#include <ctype.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <time.h>
#ifdef __amigaos__
/* (AllocMem y FreeMem: la struct Node de exec, con otro nombre; la de dashc es la del árbol) */
#define Node ExecNode
#include <proto/exec.h>
#include <exec/memory.h>
#undef Node
#endif
#include "dashc.h"

int tiempos;   /* --tiempos */
static long mem_in_use, mem_peak;   /* (--tiempos: la memoria pedida al sistema, en uso, y lo más que llegó) */

void tiempo(const char *fase)
{
    static clock_t last;
    clock_t now;
    if (!tiempos) return;
    if (!last) last = clock();
    now = clock();
    printf("%-12s %6ld ms %7ld KB (pico %ld KB)\n", fase, (long)((now - last) * 1000 / CLOCKS_PER_SEC), mem_in_use / 1024,
           mem_peak / 1024);
    last = now;
}

const char *src_name = "?";
struct SrcFiles src_files;
int lex_file;

/* La memoria de dashc. El malloc de libnix recorre en cada llamada todos sus bloques (y free también, para saber de
   cuál es): con los cientos de miles de trozos de un programa grande, en un A1200 se iba en eso casi todo el tiempo
   de compilar (y la memoria, troceada). Aquí: los trozos pequeños salen de bloques de 64 KB, de corrido, y al
   soltarlos van a una lista por tamaño (de 8 en 8 bytes) de donde sale el siguiente de ese tamaño; los grandes van
   aparte (AllocMem), en una lista para soltarlos al acabar. */
#ifdef __amigaos__
#define HDR 4                     /* el tamaño del trozo, delante (con el bit 0 si es grande) */
#define sys_alloc(n) AllocMem((n), MEMF_ANY)
#define sys_free(p, n) FreeMem((p), (n))
#else
#define HDR 8                     /* (8: los double y punteros del PC, alineados) */
#define sys_alloc(n) malloc(n)
#define sys_free(p, n) ((void)(n), free(p))
#endif
#define SMALL_MAX 512
#define CHUNK_SIZE (64 * 1024)

typedef struct Big { struct Big *next, *prev; size_t size; size_t pad; } Big;   /* (16 bytes) delante de un grande */
typedef struct Chunk { struct Chunk *next; size_t pad; } Chunk;
static void *small_free[SMALL_MAX / 8 + 1];
static uint8_t *bump, *bump_end;
static Chunk *chunks;
static Big bigs = {&bigs, &bigs, 0, 0};

#define SIZE_OF(p) (*(size_t *)((uint8_t *)(p) - HDR))

static void mem_free_all(void)
{
    while (bigs.next != &bigs) {
        Big *b = bigs.next;
        bigs.next = b->next;
        sys_free(b, b->size);
    }
    bigs.prev = &bigs;
    mem_in_use = 0;
    while (chunks) {
        Chunk *c = chunks;
        chunks = c->next;
        sys_free(c, CHUNK_SIZE);
    }
    bump = bump_end = NULL;
    memset(small_free, 0, sizeof small_free);
}

void mem_init(void) { atexit(mem_free_all); }

static void *alloc_raw(size_t n, size_t *got);

/* sin memoria: cuánto se pedía y cuánto llevaba (para saber cuánta hace falta) */
static void no_memory(size_t want)
{
#if defined(__amigaos__) && defined(DIAG_MEM)
    printf("diag: pide %lu, en uso %ld, libre %lu, mayor %lu, chip mayor %lu\n", (unsigned long)want, mem_in_use,
           (unsigned long)AvailMem(MEMF_ANY), (unsigned long)AvailMem(MEMF_ANY | MEMF_LARGEST),
           (unsigned long)AvailMem(MEMF_CHIP | MEMF_LARGEST));
#endif
    fatal("sin memoria (%lu KB más, con %ld KB pedidos)", (unsigned long)(want + 1023) / 1024, mem_in_use / 1024);
}

void *xmalloc(size_t n)
{
    size_t need;
    void *p = alloc_raw(n, &need);
    if (need <= 128) {                                 /* (sin llamar a memset para poco: un nodo son 100 bytes) */
        uint32_t *q = p;
        size_t k = need / 8;                           /* (need es múltiplo de 8) */
        while (k--) {
            q[0] = 0;
            q[1] = 0;
            q += 2;
        }
    } else {
        memset(p, 0, need);
    }
    return p;
}

/* (sin poner a 0; got: lo que cabe de verdad) */
static void *alloc_raw(size_t n, size_t *got)
{
    size_t need = (n + 7) & ~(size_t)7;
    uint8_t *p;
    if (!need) need = 8;
    if (need <= SMALL_MAX) {
        void **fl = &small_free[need / 8];
        if (*fl) {
            p = *fl;
            *fl = *(void **)p;
        } else {
            if ((size_t)(bump_end - bump) < need + HDR) {
                Chunk *c = sys_alloc(CHUNK_SIZE);
                if (!c) no_memory(CHUNK_SIZE);
                mem_in_use += CHUNK_SIZE;
                if (mem_in_use > mem_peak) mem_peak = mem_in_use;
                c->next = chunks;
                chunks = c;
                bump = (uint8_t *)(c + 1);
                bump_end = (uint8_t *)c + CHUNK_SIZE;
            }
            p = bump + HDR;
            bump += need + HDR;
            SIZE_OF(p) = need;
        }
    } else {
        size_t total = sizeof(Big) + HDR + need;
        Big *b;
        if (total < need) no_memory(need);
        b = sys_alloc(total);
        if (!b) no_memory(total);
        mem_in_use += (long)total;
        if (mem_in_use > mem_peak) mem_peak = mem_in_use;
        b->size = total;
        b->next = bigs.next;
        b->prev = &bigs;
        bigs.next->prev = b;
        bigs.next = b;
        p = (uint8_t *)(b + 1) + HDR;
        SIZE_OF(p) = need | 1;
    }
    *got = need;
    return p;
}

void xfree(void *p)
{
    size_t s;
    if (!p) return;
    s = SIZE_OF(p);
    if (s & 1) {
        Big *b = (Big *)((uint8_t *)p - HDR) - 1;
        b->prev->next = b->next;
        b->next->prev = b->prev;
        mem_in_use -= (long)b->size;
        sys_free(b, b->size);
    } else {
        void **fl = &small_free[s / 8];
        *(void **)p = *fl;
        *fl = p;
    }
}

void *xrealloc(void *p, size_t n)
{
    size_t cap, got;
    void *q;
    if (!p) return xmalloc(n);
    cap = SIZE_OF(p) & ~(size_t)1;
    if (n <= cap) return p;
    q = alloc_raw(n, &got);
    memcpy(q, p, cap);
    memset((uint8_t *)q + cap, 0, got - cap);
    xfree(p);
    return q;
}

size_t xcap(const void *p) { return p ? SIZE_OF(p) & ~(size_t)1 : 0; }

/* Los nodos del árbol (y sus NodeExt), de corrido en bloques de 32 KB: sin la cabecera ni el redondeo a 8 de cada
   trozo (nunca se sueltan uno a uno; node_free_all, todos al acabar de generar) */
static struct NodeBlock { struct NodeBlock *next; } *node_blocks;

static uint8_t *arena_at, *arena_end;

void *node_arena(size_t size)
{
    uint8_t *at = arena_at, *end = arena_end;
    /* (de 4 en 4 bytes, también en el 68000, donde el struct va de 2 en 2: un long que no empieza en múltiplo de 4
       va más lento en un 68020) */
    size_t sz = (size + 3) & ~(size_t)3;
    void *n;
#if !defined(__amigaos__)
    sz = (size + 7) & ~(size_t)7;                  /* (los double y punteros del PC, alineados) */
#endif
    if ((size_t)(end - at) < sz) {
        struct NodeBlock *b = xmalloc(32 * 1024);
        b->next = node_blocks;
        node_blocks = b;
        at = (uint8_t *)(b + 1);
#if !defined(__amigaos__)
        at = (uint8_t *)b + 8;
#endif
        end = (uint8_t *)b + 32 * 1024;
    }
    n = at;                                        /* (ya a 0: xmalloc) */
    arena_at = at + sz;
    arena_end = end;
    return n;
}

void node_free_all(void)
{
    arena_at = arena_end = NULL;
    while (node_blocks) {
        struct NodeBlock *b = node_blocks;
        node_blocks = b->next;
        xfree(b);
    }
}

Node *node_alloc(void)
{
    Node *n = node_arena(sizeof(Node));
    n->x = &node_no_ext;
    return n;
}

/* (sin memcpy: el de libnix llama a CopyMem de exec, caro para unos pocos bytes) */
static void copy_small(void *dst, const void *src, size_t n)
{
    uint8_t *d = dst;
    const uint8_t *s = src;
    if (n > 64) {
        memcpy(d, s, n);
        return;
    }
    while (n--) *d++ = *s++;
}

char *xstrndup(const char *s, size_t n)
{
    size_t got;
    char *d = alloc_raw(n + 1, &got);
    copy_small(d, s, n);
    while (n < got) d[n++] = 0;
    return d;
}

/* lo de b como texto (con su 0 detrás), en un trozo de su tamaño: un Buf empieza con 256 bytes, y los miles de
   textos de un programa grande se quedaban con ellos (b queda vacío) */
char *buf_text(Buf *b)
{
    char *t = xstrndup(b->p ? (const char *)b->p : "", b->n);
    xfree(b->p);
    b->p = NULL;
    b->n = b->cap = 0;
    return t;
}

static void grow(Buf *b, size_t extra)
{
    if (b->n - b->base + extra > b->cap) {
        uint8_t *real = b->p ? b->p + b->base : NULL;
        /* (al doble; desde 64 KB, la mitad más, como VEC_PUSH) */
        b->cap = b->cap ? b->cap + (b->cap < 65536 ? b->cap : b->cap / 2) : 256;
        while (b->cap < b->n - b->base + extra) b->cap *= 2;
        real = xrealloc(real, b->cap);
        b->p = real - b->base;
    }
}

struct BufSeg { struct BufSeg *next; size_t n; };   /* y detrás, sus n bytes */
#define SPILL_MIN (32 * 1024)

void buf_spill(Buf *b, size_t keep)
{
    struct BufSeg *s;
    size_t k;
    if (b->n - b->base < SPILL_MIN + keep) return;
    k = b->n - b->base - keep;
    s = xmalloc(sizeof *s + k);
    s->n = k;
    memcpy(s + 1, b->p + b->base, k);
    memmove(b->p + b->base, b->p + b->base + k, keep);
    if (b->segs_end) b->segs_end->next = s;
    else b->segs = s;
    b->segs_end = s;
    b->p -= k;                                     /* (el mismo sitio de memoria, con base k más allá) */
    b->base += k;
}

void buf_flatten(Buf *b)
{
    uint8_t *all, *d;
    struct BufSeg *s;
    if (!b->segs) return;
    all = d = xmalloc(b->n + 1);
    for (s = b->segs; s; s = s->next) {
        memcpy(d, s + 1, s->n);
        d += s->n;
    }
    memcpy(d, b->p + b->base, b->n - b->base);
    while (b->segs) {
        s = b->segs;
        b->segs = s->next;
        xfree(s);
    }
    b->segs_end = NULL;
    xfree(b->p + b->base);
    b->p = all;
    b->base = 0;
    b->cap = b->n + 1;
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
    copy_small(b->p + b->n, p, n);
    b->n += n;
}

/* el 68000 es big-endian */
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

/* Índice de nombres (dashc.h, NameIdx): para no comparar con strcmp un nombre con todas las funciones, globales,
   símbolos del runtime... en cada búsqueda (en un A1200, la mayor parte del tiempo de compilar un programa grande).
   Cada cubo encadena sus elementos en orden: el primero que encaja es el mismo que daba la búsqueda de antes. */
unsigned name_hash(const char *s)
{
    /* los 8 primeros caracteres, el largo y los 3 últimos (sin multiplicar: en el 68000 es una llamada) */
    const unsigned char *p = (const unsigned char *)s;
    unsigned h = 5381;
    while (*p && p - (const unsigned char *)s < 8) h = ((h << 5) + h) ^ *p++;
    if (*p) {
        while (*p) p++;
        h = ((h << 5) + h) ^ (unsigned)(p - (const unsigned char *)s);
        h = ((h << 5) + h) ^ p[-1];
        h = ((h << 5) + h) ^ p[-2];
        h = ((h << 5) + h) ^ p[-3];
    }
    return h ^ (h >> 11);
}

void nidx_sync(NameIdx *x, const void *base, size_t stride, size_t off, int n)
{
    int i;
    if (base != x->base || n < x->n) x->n = 0;          /* otra lista (o más corta): de nuevo */
    if (n * 2 > x->nb) {                                /* más cubos, y todo de nuevo */
        int nb = 64;
        while (nb < n * 2) nb *= 2;
        xfree(x->head);
        xfree(x->tail);
        x->head = xmalloc(sizeof(int) * nb);
        x->tail = xmalloc(sizeof(int) * nb);
        x->nb = nb;
        x->n = 0;
    }
    if (n > x->cap) {
        x->cap = n * 2;
        x->next = xrealloc(x->next, sizeof(int) * x->cap);
    }
    if (!x->n)
        for (i = 0; i < x->nb; i++) x->head[i] = -1;
    x->base = base;
    if (x->n == n) return;                              /* (lo normal: nada nuevo) */
    base = (const char *)base + (size_t)x->n * stride;
    for (i = x->n; i < n; i++, base = (const char *)base + stride) {
        const char *name = *(const char *const *)((const char *)base + off);   /* (base avanza: sin multiplicar) */
        unsigned b = name_hash(name) & (unsigned)(x->nb - 1);
        x->next[i] = -1;
        if (x->head[b] < 0) x->head[b] = i;
        else x->next[x->tail[b]] = i;
        x->tail[b] = i;
    }
    x->n = n;
}
