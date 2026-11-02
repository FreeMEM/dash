/* stb_image for Dash's image_decode: JPEG, PNG, GIF and BMP from memory, without stdio, SIMD, HDR or float.
   Its memory comes from exec (AllocVec, with the size in front for realloc): it may run in another process.
   Errors do not abort: stbi_load_from_memory gives NULL. */
#include <exec/memory.h>
#include <proto/exec.h>
#include <stddef.h>

static void *dash_stbi_malloc(size_t n)
{
    ULONG *p = (ULONG *)AllocVec(n + 4, MEMF_ANY);
    if (!p) return NULL;
    p[0] = (ULONG)n;
    return p + 1;
}

static void dash_stbi_free(void *p)
{
    if (p) FreeVec((ULONG *)p - 1);
}

static void *dash_stbi_realloc(void *p, size_t n)
{
    void *q = dash_stbi_malloc(n);
    size_t old = p ? ((ULONG *)p)[-1] : 0;
    if (!q) return NULL;
    if (p) {
        CopyMem(p, q, old < n ? old : n);
        dash_stbi_free(p);
    }
    return q;
}

#define STBI_MALLOC(sz) dash_stbi_malloc(sz)
#define STBI_REALLOC(p, sz) dash_stbi_realloc(p, sz)
#define STBI_FREE(p) dash_stbi_free(p)
#define STB_IMAGE_IMPLEMENTATION
#define STBI_NO_STDIO
#define STBI_NO_SIMD
#define STBI_NO_HDR
#define STBI_NO_LINEAR
#define STBI_ONLY_JPEG
#define STBI_ONLY_PNG
#define STBI_ONLY_GIF
#define STBI_ONLY_BMP
#define STBI_ASSERT(x)
#define STBI_NO_THREAD_LOCALS   /* (its error message without thread-local storage: no emutls from libgcc) */
#include "stb_image.h"
