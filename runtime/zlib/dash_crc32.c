#include "zlib.h"

unsigned long dash_zlib_crc32(const void *buf, long n, unsigned long crc) {
    if (!buf || n <= 0) return crc;
    return crc32(crc, (const Bytef *)buf, (uInt)n);
}
