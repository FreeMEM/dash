#include <ctype.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <time.h>
#include "dashc.h"

int tiempos;   /* --tiempos */

void tiempo(const char *fase)
{
    static clock_t last;
    clock_t now;
    if (!tiempos) return;
    if (!last) last = clock();
    now = clock();
    printf("%-12s %6ld ms\n", fase, (long)((now - last) * 1000 / CLOCKS_PER_SEC));
    last = now;
}

const char *src_name = "?";
struct SrcFiles src_files;
int lex_file;

void *xmalloc(size_t n)
{
    void *p = calloc(1, n ? n : 1);
    if (!p) fatal("sin memoria");
    return p;
}

void *xrealloc(void *p, size_t n)
{
    p = realloc(p, n ? n : 1);
    if (!p) fatal("sin memoria");
    return p;
}

char *xstrndup(const char *s, size_t n)
{
    char *d = xmalloc(n + 1);
    memcpy(d, s, n);
    d[n] = 0;
    return d;
}

static void grow(Buf *b, size_t extra)
{
    if (b->n + extra > b->cap) {
        b->cap = b->cap ? b->cap * 2 : 256;
        while (b->cap < b->n + extra) b->cap *= 2;
        b->p = xrealloc(b->p, b->cap);
    }
}

void buf_byte(Buf *b, int v)
{
    grow(b, 1);
    b->p[b->n++] = (uint8_t)v;
}

void buf_word(Buf *b, int v)
{
    grow(b, 2);
    put_word(b->p + b->n, v);
    b->n += 2;
}

void buf_long(Buf *b, uint32_t v)
{
    grow(b, 4);
    put_long(b->p + b->n, v);
    b->n += 4;
}

void buf_bytes(Buf *b, const void *p, size_t n)
{
    grow(b, n);
    memcpy(b->p + b->n, p, n);
    b->n += n;
}

/* el 68000 es big-endian */
void put_word(uint8_t *p, int v)
{
    p[0] = (uint8_t)(v >> 8);
    p[1] = (uint8_t)v;
}

void put_long(uint8_t *p, uint32_t v)
{
    p[0] = (uint8_t)(v >> 24);
    p[1] = (uint8_t)(v >> 16);
    p[2] = (uint8_t)(v >> 8);
    p[3] = (uint8_t)v;
}

uint32_t get_long(const uint8_t *p)
{
    return (uint32_t)p[0] << 24 | (uint32_t)p[1] << 16 | (uint32_t)p[2] << 8 | p[3];
}

void fatal(const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    fprintf(stderr, "dashc: Error: ");
    vfprintf(stderr, fmt, ap);
    fprintf(stderr, "\n");
    va_end(ap);
    exit(1);
}

void fatal_at(int line, int col, const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    char msg[1024], *m;
    fprintf(stderr, "%s:%d:%d: Error: ", src_name, line, col);
    vsnprintf(msg, sizeof msg, fmt, ap);
    /* (sin el sufijo de los nombres privados de un módulo: `_x__m2` es `_x`, rename_private) */
    for (m = msg; *m; m++) {
        char *e = m + 3;
        if (strncmp(m, "__m", 3) || !isdigit((unsigned char)*e)) continue;
        while (isdigit((unsigned char)*e)) e++;
        if (!isalnum((unsigned char)*e) && *e != '_') memmove(m, e, strlen(e) + 1);
    }
    fprintf(stderr, "%s\n", msg);
    va_end(ap);
    exit(1);
}
