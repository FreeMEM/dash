#include "dash_zlib.h"

long dash_zlib_deflate(const void *src, long n, void *dst, long max, long level) {
    z_stream z;
    int r;
    if (!src || !dst || n < 0 || max < 0) return -1;
    if (level < 0) level = Z_DEFAULT_COMPRESSION;
    if (level > 9) level = 9;
    dash_zlib_stream(&z, src, n, dst, max);
    r = deflateInit2(&z, (int)level, Z_DEFLATED, -MAX_WBITS, 8, Z_DEFAULT_STRATEGY);
    if (r != Z_OK) return r == Z_MEM_ERROR ? -3 : -1;
    r = deflate(&z, Z_FINISH);
    deflateEnd(&z);
    if (r == Z_STREAM_END) return (long)z.total_out;
    if (r == Z_MEM_ERROR) return -3;
    return -2;
}
