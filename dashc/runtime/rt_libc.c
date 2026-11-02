/* Lo poco de la librería de C que usa el runtime (dashc no enlaza libnix). Se compila con
   -fno-builtin y -fno-tree-loop-distribute-patterns: si no, gcc cambiaría estos bucles por llamadas
   a ellas mismas. */
#include <stddef.h>

/* memcpy, en ensamblador: rt_asm.s */
void *memcpy(void *d, const void *s, size_t n);

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

/* sprintf: el vsnprintf de rt_compat.c (precisión, *, ll...). El de antes solo sabía %d %i %u %x %X %c %s %% con l,
   0, - y anchura: "%.60s" salía tal cual y descolocaba los argumentos (el assert de QuickJS de Tachyon, D16) */
#include <stdarg.h>
int vsnprintf(char *out, size_t max, const char *f, va_list ap);

int vsprintf(char *out, const char *f, va_list ap)
{
    return vsnprintf(out, 0x7FFFFFFF, f, ap);
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
