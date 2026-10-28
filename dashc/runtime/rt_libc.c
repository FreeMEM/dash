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

char *strcpy(char *d, const char *s)
{
    char *p = d;
    while ((*p++ = *s++) != 0)
        ;
    return d;
}

char *strncpy(char *d, const char *s, size_t n)
{
    char *p = d;
    while (n && (*p = *s) != 0) {
        p++;
        s++;
        n--;
    }
    while (n--) *p++ = 0;
    return d;
}

char *strcat(char *d, const char *s)
{
    strcpy(d + strlen(d), s);
    return d;
}

int strncmp(const char *a, const char *b, size_t n)
{
    const unsigned char *p = (const unsigned char *)a, *q = (const unsigned char *)b;
    while (n && *p && *p == *q) {
        p++;
        q++;
        n--;
    }
    return n ? *p - *q : 0;
}

char *strstr(const char *h, const char *n)
{
    size_t len = strlen(n);
    if (!len) return (char *)h;
    for (; *h; h++)
        if (*h == *n && !strncmp(h, n, len)) return (char *)h;
    return 0;
}

/* lo usan las funciones de texto en línea de libnix (strsup.h): copia n bytes de s a d */
void __bcopz(const void *s, void *d, size_t n)
{
    memmove(d, s, n);
}

/* sprintf con lo que usa el runtime: %d %i %u %x %X %c %s %%, con l, 0, - y anchura (int = 32 bits) */
#include <stdarg.h>

static char *put_num(char *o, unsigned long v, int base, int upper, int neg, int width, int zero, int left)
{
    char tmp[12];
    int n = 0, len;
    const char *dig = upper ? "0123456789ABCDEF" : "0123456789abcdef";
    do {
        tmp[n++] = dig[v % base];
        v /= base;
    } while (v);
    len = n + neg;
    if (!left && !zero)
        for (; width > len; width--) *o++ = ' ';
    if (neg) *o++ = '-';
    if (!left && zero)
        for (; width > len; width--) *o++ = '0';
    while (n) *o++ = tmp[--n];
    if (left)
        for (; width > len; width--) *o++ = ' ';
    return o;
}

int vsprintf(char *out, const char *f, va_list ap)
{
    char *o = out;
    for (; *f; f++) {
        int width = 0, zero = 0, left = 0;
        if (*f != '%') {
            *o++ = *f;
            continue;
        }
        f++;
        if (*f == '-') { left = 1; f++; }
        if (*f == '0') { zero = 1; f++; }
        while (*f >= '0' && *f <= '9') width = width * 10 + *f++ - '0';
        if (*f == 'l') f++;
        switch (*f) {
        case 'd': case 'i': {
            long v = va_arg(ap, long);
            o = put_num(o, v < 0 ? 0ul - (unsigned long)v : (unsigned long)v, 10, 0, v < 0, width, zero, left);
            break;
        }
        case 'u': o = put_num(o, va_arg(ap, unsigned long), 10, 0, 0, width, zero, left); break;
        case 'x': o = put_num(o, va_arg(ap, unsigned long), 16, 0, 0, width, zero, left); break;
        case 'X': o = put_num(o, va_arg(ap, unsigned long), 16, 1, 0, width, zero, left); break;
        case 'c': *o++ = (char)va_arg(ap, int); break;
        case 's': {
            const char *s = va_arg(ap, const char *);
            int len = (int)strlen(s ? s : "");
            if (!left) for (; width > len; width--) *o++ = ' ';
            while (s && *s) *o++ = *s++;
            if (left) for (; width > len; width--) *o++ = ' ';
            break;
        }
        case '%': *o++ = '%'; break;
        default: *o++ = *f; break;
        }
    }
    *o = 0;
    return (int)(o - out);
}

int sprintf(char *out, const char *f, ...)
{
    va_list ap;
    int n;
    va_start(ap, f);
    n = vsprintf(out, f, ap);
    va_end(ap);
    return n;
}
