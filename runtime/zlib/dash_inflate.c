#include "dash_zlib.h"

static long dash_zlib_inflate_w(const void *src, long n, void *dst, long max, int wbits) {
    z_stream z;
    int r;
    if (!src || !dst || n < 0 || max < 0) return -1;
    dash_zlib_stream(&z, src, n, dst, max);
    r = inflateInit2(&z, wbits);
    if (r != Z_OK) return r == Z_MEM_ERROR ? -3 : -1;
    r = inflate(&z, Z_FINISH);
    inflateEnd(&z);
    if (r == Z_STREAM_END) return (long)z.total_out;
    if (r == Z_MEM_ERROR) return -3;
    /* stopped with the output full: it does not fit (it may also be cut short, but more room tells) */
    if ((r == Z_BUF_ERROR || r == Z_OK) && z.avail_out == 0) return -2;
    return -1;
}

long dash_zlib_inflate(const void *src, long n, void *dst, long max) {
    return dash_zlib_inflate_w(src, n, dst, max, -MAX_WBITS);
}

/* gzip (RFC 1952: its header skipped, its trailer not checked), zlib (RFC 1950, with its adler32) or raw
   deflate, told by the first bytes: what an HTTP "Content-Encoding: gzip" or "deflate" body may be (Dash 2.0,
   what Tachyon did with @native) */
long dash_zlib_inflate_auto(const void *src, long n, void *dst, long max) {
    const unsigned char *p = (const unsigned char *)src;
    long i, r;
    if (!src || !dst || n < 0 || max < 0) return -1;
    if (n >= 18 && p[0] == 0x1f && p[1] == 0x8b && p[2] == 8) {
        unsigned char fl = p[3];
        i = 10;
        if (fl & 4) i += 2 + (p[10] | (p[11] << 8));                /* FEXTRA */
        if (fl & 8) { while (i < n && p[i]) i++; i++; }              /* FNAME */
        if (fl & 16) { while (i < n && p[i]) i++; i++; }             /* FCOMMENT */
        if (fl & 2) i += 2;                                          /* FHCRC */
        if (i >= n) return -1;
        return dash_zlib_inflate_w(p + i, n - i, dst, max, -MAX_WBITS);
    }
    if (n >= 2 && (p[0] & 0x0F) == 8 && (p[0] >> 4) <= 7 && ((p[0] << 8) | p[1]) % 31 == 0) {
        r = dash_zlib_inflate_w(src, n, dst, max, MAX_WBITS);
        if (r != -1) return r;           /* (-1: it was not zlib after all, though it looked like it: raw) */
    }
    return dash_zlib_inflate_w(src, n, dst, max, -MAX_WBITS);
}
