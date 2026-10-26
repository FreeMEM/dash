#ifndef DASH_ZLIB_H
#define DASH_ZLIB_H
/* Shared by Dash's entry points to zlib (Lorraine D6), one file each so a program that only inflates
   does not link deflate: raw deflate (no zlib or gzip wrapper, what a ZIP holds) from one buffer to
   another in one call. Memory for zlib's state comes from exec and goes back
   before returning. Errors are negative: -1 the data is not raw deflate or ends too soon, -2 the
   result does not fit in max, -3 not enough memory. */
#include <exec/memory.h>
#include <proto/exec.h>
#include "zlib.h"

static voidpf dash_zlib_alloc(voidpf opaque, uInt items, uInt size) {
    (void)opaque;
    return AllocVec((ULONG)items * size, MEMF_ANY);
}

static void dash_zlib_free(voidpf opaque, voidpf p) {
    (void)opaque;
    FreeVec(p);
}

static void dash_zlib_stream(z_stream *z, const void *src, long n, void *dst, long max) {
    UBYTE *p = (UBYTE *)z;
    unsigned i;
    for (i = 0; i < sizeof(*z); i++) p[i] = 0;
    z->zalloc = dash_zlib_alloc;
    z->zfree = dash_zlib_free;
    z->next_in = (z_const Bytef *)src;
    z->avail_in = (uInt)n;
    z->next_out = (Bytef *)dst;
    z->avail_out = (uInt)max;
}

#endif
