#include "zlib.h"

/* Adler-32, the checksum at the end of a zlib stream (git keeps its objects so): 1 to start */
unsigned long dash_zlib_adler32(const void *buf, long n, unsigned long a) {
    if (!buf || n <= 0) return a;
    return adler32(a, (const Bytef *)buf, (uInt)n);
}

unsigned long dash_zlib_crc32(const void *buf, long n, unsigned long crc) {
    if (!buf || n <= 0) return crc;
    return crc32(crc, (const Bytef *)buf, (uInt)n);
}
