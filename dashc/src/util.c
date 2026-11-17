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

int check_mode, check_errors;
jmp_buf *check_jmp;
static struct CheckErr { char *text; int file, line, col, seq; } check_seen[CHECK_MAX];
static int check_flushed;

static int check_cmp(const void *a, const void *b)
{
    const struct CheckErr *x = a, *y = b;
    if (x->file != y->file) return x->file - y->file;
    if (x->line != y->line) return x->line - y->line;
    if (x->col != y->col) return x->col - y->col;
    return x->seq - y->seq;
}

/* --check: los errores, por fichero y línea (main.c la pone con atexit) */
void check_flush(void)
{
    int i;
    if (check_flushed) return;
    check_flushed = 1;
    qsort(check_seen, check_errors, sizeof check_seen[0], check_cmp);
    for (i = 0; i < check_errors; i++) err_printf("%s", check_seen[i].text);
    fflush(DASHC_ERR);
}

/* --check: tras un error, a la instrucción siguiente (o fuera, con 1, si no hay dónde seguir) */
static void check_next(void)
{
    if (check_jmp) longjmp(*check_jmp, 1);
    exit(1);
}

void check_quiet(void)
{
    if (!check_mode) exit(1);
    check_next();
}

void fatal(const char *fmt, ...)
{
    va_list ap;
    if (check_mode && check_errors) exit(1);   /* (--check: un fallo que viene de un error ya dicho) */
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
    char msg[1024], *m, full[1400];
    vsnprintf(msg, sizeof msg, fmt, ap);
    va_end(ap);
    /* (sin el sufijo de los nombres privados de un módulo: `_x__m2` es `_x`, rename_private) */
    for (m = msg; *m; m++) {
        char *e = m + 3;
        if (strncmp(m, "__m", 3) || !isdigit((unsigned char)*e)) continue;
        while (isdigit((unsigned char)*e)) e++;
        if (!isalnum((unsigned char)*e) && *e != '_') memmove(m, e, strlen(e) + 1);
    }
    snprintf(full, sizeof full, "%s:%d:%d: Error: %s\n", src_name, line, col, msg);
    if (check_mode) {
        /* cada error una vez (una función copiada en otra lo repite); salen ordenados al acabar (check_flush) */
        int i, file = 0;
        for (i = 0; i < check_errors; i++)
            if (!strcmp(check_seen[i].text, full)) check_next();
        for (i = 0; i < src_files.n; i++)
            if (!strcmp(src_files.v[i], src_name)) file = i;
        check_seen[check_errors].text = xstrndup(full, strlen(full));
        check_seen[check_errors].file = file;
        check_seen[check_errors].line = line;
        check_seen[check_errors].col = col;
        check_seen[check_errors].seq = check_errors;
        if (++check_errors == CHECK_MAX) {
            check_flush();
            err_printf("dash: Error: demasiados errores (%d): no se miran más\n", CHECK_MAX);
            exit(1);
        }
        check_next();
    }
    err_printf("%s", full);
    exit(1);
}
