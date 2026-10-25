#include <exec/types.h>
#include <intuition/screens.h>
#include <proto/exec.h>
#include <proto/intuition.h>
#include <proto/graphics.h>
struct IntuitionBase *IntuitionBase;
struct GfxBase *GfxBase;
int main(void) {
    struct Screen *s;
    long i;
    IntuitionBase = (struct IntuitionBase *)OpenLibrary("intuition.library", 37);
    GfxBase = (struct GfxBase *)OpenLibrary("graphics.library", 37);
    s = OpenScreenTags(NULL, SA_Width, 320, SA_Height, 256, SA_Depth, 5, SA_Title, (ULONG)"bench", TAG_DONE);
    if (s) {
        for (i = 1; i <= 2000; i++) {
            SetAPen(&s->RastPort, i % 32);
            Move(&s->RastPort, i % 320, 0);
            Draw(&s->RastPort, 319 - i % 320, 180);
        }
        CloseScreen(s);
    }
    CloseLibrary((struct Library *)GfxBase);
    CloseLibrary((struct Library *)IntuitionBase);
    return 0;
}
