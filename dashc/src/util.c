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

/* Un error o aviso de dashc (DASHC_ERR). Los textos de dashc van en UTF-8; en el Amiga, en Latin-1 (lo que no es
   UTF-8 válido, como un nombre de fichero que ya está en Latin-1, queda como está) */
static void err_out(const char *fmt, va_list ap)
{
    char msg[2048];
    vsnprintf(msg, sizeof msg, fmt, ap);
#ifdef __amigaos__
    {
        unsigned char *s = (unsigned char *)msg, *d = s;
        for (; *s; s++) {
            if ((s[0] == 0xC2 || s[0] == 0xC3) && (s[1] & 0xC0) == 0x80) {
                *d++ = (unsigned char)((s[0] & 0x03) << 6 | (s[1] & 0x3F));
                s++;
            } else {
                *d++ = *s;
            }
        }
        *d = 0;
    }
#endif
    fputs(msg, DASHC_ERR);
}

void err_printf(const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    err_out(fmt, ap);
    va_end(ap);
}

void fatal(const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    err_printf("dash: Error: ");
    err_out(fmt, ap);
    err_printf("\n");
    va_end(ap);
    exit(1);
}

void fatal_at(int line, int col, const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    char msg[1024], *m;
    err_printf("%s:%d:%d: Error: ", src_name, line, col);
    vsnprintf(msg, sizeof msg, fmt, ap);
    /* (sin el sufijo de los nombres privados de un módulo: `_x__m2` es `_x`, rename_private) */
    for (m = msg; *m; m++) {
        char *e = m + 3;
        if (strncmp(m, "__m", 3) || !isdigit((unsigned char)*e)) continue;
        while (isdigit((unsigned char)*e)) e++;
        if (!isalnum((unsigned char)*e) && *e != '_') memmove(m, e, strlen(e) + 1);
    }
    err_printf("%s\n", msg);
    va_end(ap);
    exit(1);
}
