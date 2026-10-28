/* Lo poco de la librería de C que usa el runtime (dashc no enlaza libnix). Se compila con
   -fno-builtin y -fno-tree-loop-distribute-patterns: si no, gcc cambiaría estos bucles por llamadas
   a ellas mismas. */
#include <stddef.h>

void *memcpy(void *d, const void *s, size_t n)
{
    unsigned char *p = d;
    const unsigned char *q = s;
    /* de 4 en 4 si los dos están en dirección par (el 68000 lee longs en direcciones pares) */
    if (!(((unsigned long)p | (unsigned long)q) & 1)) {
        while (n >= 4) {
            *(unsigned long *)p = *(const unsigned long *)q;
            p += 4;
            q += 4;
            n -= 4;
        }
    }
    while (n--) *p++ = *q++;
    return d;
}

void *memmove(void *d, const void *s, size_t n)
{
    unsigned char *p = d;
    const unsigned char *q = s;
    if (p <= q || p >= q + n) return memcpy(d, s, n);
    p += n;
    q += n;
    while (n--) *--p = *--q;
    return d;
}

void *memset(void *d, int c, size_t n)
{
    unsigned char *p = d;
    while (n--) *p++ = (unsigned char)c;
    return d;
}

size_t strlen(const char *s)
{
    const char *p = s;
    while (*p) p++;
    return (size_t)(p - s);
}

int strcmp(const char *a, const char *b)
{
    const unsigned char *p = (const unsigned char *)a, *q = (const unsigned char *)b;
    while (*p && *p == *q) {
        p++;
        q++;
    }
    return *p - *q;
}
