/* Screenshot from inside the emulated Amiga, for tools/emu_run.py --screenshot.
   shot DELAY FILE [COUNT]: waits DELAY ticks (50 per second), then saves the front
   screen as a binary PPM (P6) with its palette; with COUNT > 1 it saves COUNT
   shots, DELAY ticks apart, as FILE.0, FILE.1... Run in the background ("Run
   >NIL: shot 250 DH0:shot.ppm") before the program to capture.

   Build: m68k-amigaos-gcc -O2 -noixemul -o shot tools/amiga/shot.c */
#include <exec/types.h>
#include <intuition/intuitionbase.h>
#include <graphics/gfx.h>
#include <proto/exec.h>
#include <proto/dos.h>
#include <proto/graphics.h>
#include <proto/intuition.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern struct IntuitionBase *IntuitionBase;
extern struct GfxBase *GfxBase;

/* The whole picture is read into memory first and written with one Write: the
   emulator's host file system is slow with many small writes. A standard (planar)
   bitmap is read plane by plane: ReadPixelLine8 left a 16-pixel grey band at some
   window positions on Kickstart 3.1. Other bitmaps (RTG) go through ReadPixel. */
static int save(struct Screen *s, const char *name) {
    struct BitMap *bm = s->RastPort.BitMap;
    LONG w = s->Width, h = s->Height, x, y, n, head_len, ok = 0, depth = bm->Depth;
    BOOL planar = (GetBitMapAttr(bm, BMA_FLAGS) & BMF_STANDARD) != 0;
    UBYTE *image;
    ULONG pal[256 * 3];
    BPTR f;
    char head[32];
    if (depth > 8) depth = 8;
    n = 1L << depth;
    GetRGB32(s->ViewPort.ColorMap, 0, n, pal);
    sprintf(head, "P6\n%ld %ld\n255\n", (long)w, (long)h);
    head_len = strlen(head);
    image = AllocVec(head_len + w * h * 3, MEMF_ANY);
    if (!image) return 0;
    memcpy(image, head, head_len);
    {
        UBYTE *p = image + head_len;
        for (y = 0; y < h; y++) {
            for (x = 0; x < w; x++) {
                ULONG c = 0;
                if (planar) {
                    LONG plane, offset = y * bm->BytesPerRow + (x >> 3);
                    UBYTE mask = 0x80 >> (x & 7);
                    for (plane = 0; plane < depth; plane++)
                        if (bm->Planes[plane][offset] & mask) c |= 1UL << plane;
                } else {
                    c = ReadPixel(&s->RastPort, x, y);
                }
                if (c >= (ULONG)n) c = 0;
                *p++ = pal[c * 3] >> 24;
                *p++ = pal[c * 3 + 1] >> 24;
                *p++ = pal[c * 3 + 2] >> 24;
            }
        }
    }
    if ((f = Open((STRPTR)name, MODE_NEWFILE))) {
        ok = Write(f, image, head_len + w * h * 3) == head_len + w * h * 3;
        Close(f);
    }
    FreeVec(image);
    return ok;
}

int main(int argc, char **argv) {
    LONG delay, count, i;
    char name[256];
    if (argc < 3) { PutStr("usage: shot DELAY FILE [COUNT]\n"); return 10; }
    delay = atol(argv[1]);
    count = argc > 3 ? atol(argv[3]) : 1;
    for (i = 0; i < count; i++) {
        struct Screen *s;
        ULONG lock;
        Delay(delay);
        if (count > 1) sprintf(name, "%s.%ld", argv[2], (long)i);
        else sprintf(name, "%s", argv[2]);
        lock = LockIBase(0);
        s = IntuitionBase->FirstScreen;
        UnlockIBase(lock);
        if (s) save(s, name);
    }
    return 0;
}
