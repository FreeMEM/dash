#include "dash_zlib.h"

long dash_zlib_inflate(const void *src, long n, void *dst, long max) {
    z_stream z;
    int r;
    if (!src || !dst || n < 0 || max < 0) return -1;
    dash_zlib_stream(&z, src, n, dst, max);
    r = inflateInit2(&z, -MAX_WBITS);
    if (r != Z_OK) return r == Z_MEM_ERROR ? -3 : -1;
    r = inflate(&z, Z_FINISH);
    inflateEnd(&z);
    if (r == Z_STREAM_END) return (long)z.total_out;
    if (r == Z_MEM_ERROR) return -3;
    /* stopped with the output full: it does not fit (it may also be cut short, but more room tells) */
    if ((r == Z_BUF_ERROR || r == Z_OK) && z.avail_out == 0) return -2;
    return -1;
}
