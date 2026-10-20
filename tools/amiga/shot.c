/* Screenshot from inside the emulated Amiga, for tools/emu_run.py --screenshot.
   shot DELAY FILE [COUNT]: waits DELAY ticks (50 per second), then saves the front
   screen as a binary PPM (P6) with its palette; with COUNT > 1 it saves COUNT
   shots, DELAY ticks apart, as FILE.0, FILE.1... Run in the background ("Run
   >NIL: shot 250 DH0:shot.ppm") before the program to capture. A FILE ending in .dsh gets, from a
   planar screen, its planes as they are: "DSH1 w h depth bytes-per-row\n", the palette (3 bytes a
   colour) and each row's planes one after the other (tools/emu_run.py planar_to_png makes the PNG):
   for 4 colours 40 KB instead of the PPM's 480, which the emulated machine writes slowly.

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

/* Pixels of a high/true colour RTG screen: Picasso96API.library p96ReadPixel (LVO -120,
   rp in a1, x in d0, y in d1), which gives 0xAARRGGBB; ReadPixel would give no colour there */
static struct Library *P96Base;

static ULONG p96_read_pixel(struct RastPort *rp, LONG x, LONG y) {
    register ULONG d0 __asm("d0") = x;
    register ULONG d1 __asm("d1") = y;
    register struct RastPort *a1 __asm("a1") = rp;
    register struct Library *a6 __asm("a6") = P96Base;
    __asm volatile ("jsr a6@(-120:W)" : "+r"(d0), "+r"(d1), "+r"(a1) : "r"(a6) : "a0", "cc", "memory");
    return d0;
}

/* The whole picture is read into memory first and written with one Write: the
   emulator's host file system is slow with many small writes. A standard (planar)
   bitmap is read plane by plane: ReadPixelLine8 left a 16-pixel grey band at some
   window positions on Kickstart 3.1. Each row of each plane is copied to Fast RAM at
   once (CopyMem) and its pixels taken from there: reading Chip RAM byte by byte for every
   pixel took seconds on an A1200. RTG bitmaps of 8 bits or less go through ReadPixel and
   the palette, deeper ones through p96ReadPixel. */
/* The planes of a planar screen as they are (FILE.dsh) */
static int save_planes(struct Screen *s, const char *name) {
    struct BitMap *bm = s->RastPort.BitMap;
    LONG w = s->Width, h = s->Height, depth = bm->Depth > 8 ? 8 : bm->Depth, n = 1L << depth, bpr = (w + 7) >> 3;
    LONG y, plane, head_len, size, i, ok = 0;
    ULONG pal[256 * 3];
    UBYTE *data, *p;
    char head[64];
    BPTR f;
    GetRGB32(s->ViewPort.ColorMap, 0, n, pal);
    sprintf(head, "DSH1 %ld %ld %ld %ld\n", (long)w, (long)h, (long)depth, (long)bpr);
    head_len = strlen(head);
    size = head_len + n * 3 + h * depth * bpr;
    if (!(data = AllocVec(size, MEMF_ANY))) return 0;
    memcpy(data, head, head_len);
    p = data + head_len;
    for (i = 0; i < n * 3; i++) *p++ = pal[i] >> 24;
    for (y = 0; y < h; y++)
        for (plane = 0; plane < depth; plane++, p += bpr)
            CopyMem(bm->Planes[plane] + y * bm->BytesPerRow, p, bpr);
    if ((f = Open((STRPTR)name, MODE_NEWFILE))) {
        ok = Write(f, data, size) == size;
        Close(f);
    }
    FreeVec(data);
    return ok;
}

static int save(struct Screen *s, const char *name) {
    struct BitMap *bm = s->RastPort.BitMap;
    LONG w = s->Width, h = s->Height, x, y, n, head_len, ok = 0, depth = bm->Depth;
    BOOL planar = (GetBitMapAttr(bm, BMA_FLAGS) & BMF_STANDARD) != 0;
    BOOL truecolor = !planar && GetBitMapAttr(bm, BMA_DEPTH) > 8 && P96Base;
    UBYTE *image, *row[8];
    ULONG pal[256 * 3];
    BPTR f;
    char head[32];
    if (depth > 8) depth = 8;
    n = 1L << depth;
    GetRGB32(s->ViewPort.ColorMap, 0, n, pal);
    sprintf(head, "P6\n%ld %ld\n255\n", (long)w, (long)h);
    head_len = strlen(head);
    image = AllocVec(head_len + w * h * 3 + 8 * bm->BytesPerRow, MEMF_ANY);
    if (!image) return 0;
    memcpy(image, head, head_len);
    for (x = 0; x < 8; x++) row[x] = image + head_len + w * h * 3 + x * bm->BytesPerRow;
    {
        UBYTE *p = image + head_len;
        for (y = 0; y < h; y++) {
            if (planar) {
                LONG plane;
                for (plane = 0; plane < depth; plane++)
                    CopyMem(bm->Planes[plane] + y * bm->BytesPerRow, row[plane], bm->BytesPerRow);
            }
            for (x = 0; x < w; x++) {
                ULONG c = 0;
                if (truecolor) {
                    ULONG argb = p96_read_pixel(&s->RastPort, x, y);
                    *p++ = argb >> 16;
                    *p++ = argb >> 8;
                    *p++ = argb;
                    continue;
                }
                if (planar) {
                    LONG plane, offset = x >> 3;
                    UBYTE mask = 0x80 >> (x & 7);
                    for (plane = 0; plane < depth; plane++)
                        if (row[plane][offset] & mask) c |= 1UL << plane;
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
    P96Base = OpenLibrary((CONST_STRPTR)"Picasso96API.library", 2);   /* RTG screens, if there is one */
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
        if (s) {
            LONG len = strlen(name);
            if (len > 4 && !strcmp(name + len - 4, ".dsh") && (GetBitMapAttr(s->RastPort.BitMap, BMA_FLAGS) & BMF_STANDARD))
                save_planes(s, name);
            else
                save(s, name);
        }
    }
    if (P96Base) CloseLibrary(P96Base);
    return 0;
}
