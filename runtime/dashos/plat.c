/* Dash en DashOS: arranque, memoria (con los nombres de exec), salida (con los de dos) y la libc que usa el
   runtime de Dash, sobre tres funciones de plataforma: dash_plat_write, dash_plat_exit y dash_plat_pages.

   Las de plataforma hablan con el sistema por svc #0 (número en x8, argumentos en x0..x5, resultado en x0):
   - DashOS (por defecto; llamadas provisionales de su C19): escribir = 1, salir = 2, memoria_crear = 7,
     memoria_proyectar = 8.
   - Linux (-DDASH_PLAT_LINUX), para probar en el PC con qemu-aarch64_be: write = 64, exit_group = 94, mmap = 222.

   La memoria de Dash empieza en 4 GB (DASH_HEAP_BASE): un puntero cortado a 32 bits cae fuera y el programa se
   para en el acto, en vez de seguir con datos de otro sitio. */
#include "dash_dashos.h"

/* ---- llamadas al sistema ---- */
static long _svc(long n, long a, long b, long c, long d, long e, long f)
{
    register long x8 __asm__("x8") = n;
    register long x0 __asm__("x0") = a;
    register long x1 __asm__("x1") = b;
    register long x2 __asm__("x2") = c;
    register long x3 __asm__("x3") = d;
    register long x4 __asm__("x4") = e;
    register long x5 __asm__("x5") = f;
    __asm__ volatile("svc #0" : "+r"(x0) : "r"(x8), "r"(x1), "r"(x2), "r"(x3), "r"(x4), "r"(x5) : "memory");
    return x0;
}

#define DASH_HEAP_BASE 0x100000000UL
static unsigned long heap_next = DASH_HEAP_BASE;

#ifdef DASH_PLAT_LINUX
long dash_plat_write(const void *buf, long len) { return _svc(64, 1, (long)buf, len, 0, 0, 0); }
void dash_plat_exit(int code) { for (;;) _svc(94, code, 0, 0, 0, 0, 0); }
void *dash_plat_pages(unsigned long bytes)
{
    /* MAP_PRIVATE | MAP_ANONYMOUS | MAP_FIXED_NOREPLACE, PROT_READ | PROT_WRITE */
    long r = _svc(222, (long)heap_next, (long)bytes, 3, 0x02 | 0x20 | 0x100000, -1, 0);
    if (r < 0 || (unsigned long)r != heap_next) return NULL;
    heap_next += bytes;
    return (void *)r;
}
#else
long dash_plat_write(const void *buf, long len) { return _svc(1, (long)buf, len, 0, 0, 0, 0); }
void dash_plat_exit(int code) { for (;;) _svc(2, code, 0, 0, 0, 0, 0); }
void *dash_plat_pages(unsigned long bytes)
{
    long key = _svc(7, (long)bytes, 0, 0, 0, 0, 0);
    if (key < 0 || _svc(8, key, (long)heap_next, 3, 0, 0, 0) < 0) return NULL;
    heap_next += bytes;
    return (void *)(heap_next - bytes);   /* (memoria_crear la da a cero) */
}
#endif

/* ---- memoria de la caja Amiga (amiga_alloc): por debajo de 4 GB, desde 1 GB. Provisional: sin devolverla (en
   DashOS la dará el exec de la caja) ---- */
#define DASH_BOX_BASE 0x40000000UL
static unsigned long box_next = DASH_BOX_BASE, box_end = DASH_BOX_BASE;

void *dash_plat_box_alloc(unsigned long bytes)
{
    unsigned long n = (bytes + 7) & ~7UL, p;
    if (box_next + n > box_end) {
        unsigned long want = (n + 0xFFFFUL) & ~0xFFFFUL;
#ifdef DASH_PLAT_LINUX
        long r = _svc(222, (long)box_end, (long)want, 3, 0x02 | 0x20 | 0x100000, -1, 0);
        if (r < 0 || (unsigned long)r != box_end) return NULL;
#else
        long key = _svc(7, (long)want, 0, 0, 0, 0, 0);
        if (key < 0 || _svc(8, key, (long)box_end, 3, 0, 0, 0) < 0) return NULL;
#endif
        if (box_next == box_end) box_next = box_end;
        box_end += want;
    }
    p = box_next;
    box_next += n;
    memset((void *)p, 0, n);
    return (void *)p;
}

void dash_plat_box_free(void *p, unsigned long bytes) { (void)p; (void)bytes; }

/* ---- arranque (el del camino por C; el código de dashc entra por _dashc_start y no tiene main) ---- */
int main() __attribute__((weak));
void _dash_atexit_run(void);
__asm__(".text\n.global _start\n.type _start, %function\n_start:\n"
        "    mov x29, #0\n    mov x30, #0\n    bl _dash_start_c\n    b .\n");
void _dash_start_c(void) __attribute__((noreturn, used));
void _dash_start_c(void) { exit(main()); }

static char out_buf[512];
static int out_n;

LONG Flush(BPTR fh)
{
    (void)fh;
    if (out_n) dash_plat_write(out_buf, out_n);
    out_n = 0;
    return 1;
}

void exit(int code)
{
    _dash_atexit_run();
    Flush(1);
    dash_plat_exit(code);
}

/* ---- memoria ----
   Bloques con una cabecera de 16 bytes (su tamaño útil y, en los de un pool, el pool). Los de hasta 4 KB van por
   clases de 16 bytes con una lista de libres cada una; los grandes, a una lista de libres por tamaño (el primero
   que cabe). Se sacan de trozos de 1 MB (o del tamaño del bloque) que da dash_plat_pages; no se devuelven. */
typedef struct Blk { unsigned long size; struct Pool *pool; } Blk;   /* 16 bytes */
typedef struct Free { struct Free *next; } Free;
typedef struct Big { Blk h; struct Big *next; } Big;
#define CLASSES 256
#define CHUNK (1UL << 20)
static Free *small_free[CLASSES + 1];
static Big *big_free;
static unsigned char *chunk_p, *chunk_end;

static void *raw(unsigned long n)   /* n múltiplo de 16 */
{
    unsigned char *p;
    if ((unsigned long)(chunk_end - chunk_p) < n) {
        unsigned long want = n > CHUNK ? (n + 4095) & ~4095UL : CHUNK;
        unsigned char *c = dash_plat_pages(want);
        if (!c) return NULL;
        if (c != chunk_end) chunk_p = c;   /* (si sigue al anterior, se aprovecha lo que quedaba) */
        chunk_end = c + want;
    }
    p = chunk_p;
    chunk_p += n;
    return p;
}

static void *blk_alloc(unsigned long size, int clear)
{
    unsigned long n = (size + 15) & ~15UL;
    Blk *b;
    if (!n) n = 16;
    if (n <= 16UL * CLASSES) {
        Free **l = &small_free[n >> 4];
        if (*l) {
            b = (Blk *)*l - 1;
            *l = (*l)->next;
        } else if (!(b = raw(n + sizeof(Blk))))
            return NULL;
    } else {
        Big **pp, *g;
        for (pp = &big_free; (g = *pp) && g->h.size < n; pp = &g->next) ;
        if (g) {
            *pp = g->next;
            b = &g->h;
            n = b->size;
        } else if (!(b = raw(n + sizeof(Blk))))
            return NULL;
    }
    b->size = n;
    b->pool = NULL;
    if (clear) memset(b + 1, 0, n);
    return b + 1;
}

static void blk_free(void *p)
{
    Blk *b;
    if (!p) return;
    b = (Blk *)p - 1;
    if (b->size <= 16UL * CLASSES) {
        Free *f = p;
        f->next = small_free[b->size >> 4];
        small_free[b->size >> 4] = f;
    } else {
        Big *g = (Big *)b;
        g->next = big_free;
        big_free = g;
    }
}

/* un pool: la lista de sus bloques, para soltarlos todos con DeletePool */
typedef struct PNode { struct PNode *prev, *next; } PNode;   /* delante de cada bloque del pool */
typedef struct Pool { PNode head; ULONG flags; } Pool;

APTR CreatePool(ULONG flags, ULONG puddle, ULONG threshold)
{
    Pool *p = blk_alloc(sizeof(Pool), 1);
    (void)puddle;
    (void)threshold;
    if (!p) return NULL;
    p->head.prev = p->head.next = &p->head;
    p->flags = flags;
    return p;
}

APTR AllocPooled(APTR pool, ULONG size)
{
    Pool *p = pool;
    PNode *n = blk_alloc(sizeof(PNode) + size, (p->flags & MEMF_CLEAR) != 0);
    if (!n) return NULL;
    n->next = p->head.next;
    n->prev = &p->head;
    p->head.next->prev = n;
    p->head.next = n;
    return n + 1;
}

void FreePooled(APTR pool, APTR mem, ULONG size)
{
    PNode *n = (PNode *)mem - 1;
    (void)pool;
    (void)size;
    n->prev->next = n->next;
    n->next->prev = n->prev;
    blk_free(n);
}

void DeletePool(APTR pool)
{
    Pool *p = pool;
    PNode *n, *next;
    if (!p) return;
    for (n = p->head.next; n != &p->head; n = next) {
        next = n->next;
        blk_free(n);
    }
    blk_free(p);
}

APTR AllocMem(ULONG size, ULONG flags) { return blk_alloc(size, (flags & MEMF_CLEAR) != 0); }
void FreeMem(APTR mem, ULONG size) { (void)size; blk_free(mem); }
APTR AllocVec(ULONG size, ULONG flags) { return blk_alloc(size, (flags & MEMF_CLEAR) != 0); }
void FreeVec(APTR mem) { blk_free(mem); }
void CopyMem(const void *src, void *dst, ULONG size) { memmove(dst, src, size); }

/* las de la libc, para las bibliotecas del runtime (Ryu, zlib) */
int errno;
void *malloc(size_t n) { return blk_alloc(n, 0); }
void *calloc(size_t n, size_t size) { return blk_alloc(n * size, 1); }
void free(void *p) { blk_free(p); }
void *realloc(void *p, size_t n)
{
    void *q;
    if (!p) return malloc(n);
    if (n <= ((Blk *)p - 1)->size) return p;
    if ((q = malloc(n))) {
        memcpy(q, p, ((Blk *)p - 1)->size);
        free(p);
    }
    return q;
}

/* ---- salida ---- */
APTR DOSBase = (APTR)1, IntuitionBase = (APTR)1;   /* (no son NULL: el runtime pregunta si hay dos.library) */
BPTR Output(void) { return 1; }

LONG Write(BPTR fh, const void *buf, LONG len)
{
    const char *s = buf;
    LONG i;
    (void)fh;
    for (i = 0; i < len; i++) {
        if (out_n == (int)sizeof out_buf) Flush(1);
        out_buf[out_n++] = s[i];
#ifdef DASH_PLAT_LINUX
        if (s[i] == '\n') Flush(1);                    /* (en las pruebas: lo escrito se ve aunque el programa caiga) */
#endif
    }
    return len;
}

static void put(const char *s, long n) { Write(1, s, (LONG)n); }

/* el formato de RawDoFmt que usa Dash; los argumentos vienen de next(ctx) como enteros del tamaño de un puntero */
typedef intptr_t (*NextArg)(void *ctx);
static LONG fmt_out(const char *f, NextArg next, void *ctx)
{
    LONG total = 0;
    while (*f) {
        char num[24], *s;
        int left = 0, zero = 0, width = 0, prec = -1, len, pad;
        const char *start;
        intptr_t v;
        if (*f != '%') {
            start = f;
            while (*f && *f != '%') f++;
            put(start, f - start);
            total += (LONG)(f - start);
            continue;
        }
        f++;
        if (*f == '-') { left = 1; f++; }
        if (*f == '0') { zero = 1; f++; }
        while (*f >= '0' && *f <= '9') width = width * 10 + *f++ - '0';
        if (*f == '.') {
            prec = 0;
            for (f++; *f >= '0' && *f <= '9'; f++) prec = prec * 10 + *f - '0';
        }
        if (*f == 'l') f++;
        switch (*f) {
        case 's':
            s = (char *)next(ctx);
            if (!s) s = "";
            len = (int)strlen(s);
            if (prec >= 0 && len > prec) len = prec;
            break;
        case 'c':
            num[0] = (char)next(ctx);
            s = num;
            len = 1;
            break;
        case 'd': case 'u': case 'x': case 'X': {
            ULONG u;
            int neg = 0, base = *f == 'x' || *f == 'X' ? 16 : 10;
            const char *dig = *f == 'X' ? "0123456789ABCDEF" : "0123456789abcdef";
            v = next(ctx);
            u = (ULONG)v;
            if (*f == 'd' && (LONG)u < 0) { neg = 1; u = (ULONG)-(LONG)u; }
            s = num + sizeof num;
            do { *--s = dig[u % base]; u /= base; } while (u);
            if (neg) *--s = '-';
            len = (int)(num + sizeof num - s);
            break;
        }
        case '%':
            s = "%";
            len = 1;
            break;
        case 0:
            return total;
        default:
            s = (char *)f;
            len = 1;
        }
        f++;
        pad = width > len ? width - len : 0;
        if (!left && zero && (*s == '-') && pad) { put(s, 1); s++; len--; total++; }
        if (!left) while (pad--) { put(zero ? "0" : " ", 1); total++; }
        put(s, len);
        total += len;
        if (left) while (pad-- > 0) { put(" ", 1); total++; }
    }
    return total;
}

static intptr_t next_va(void *ctx) { return va_arg(*(va_list *)ctx, intptr_t); }
static intptr_t next_arr(void *ctx) { const intptr_t **a = ctx; return *(*a)++; }

LONG Printf(CONST_STRPTR fmt, ...)
{
    va_list ap;
    LONG n;
    va_start(ap, fmt);
    n = fmt_out((const char *)fmt, next_va, &ap);
    va_end(ap);
    return n;
}

LONG VPrintf(CONST_STRPTR fmt, const intptr_t *args) { return fmt_out((const char *)fmt, next_arr, &args); }
LONG PutStr(CONST_STRPTR s) { put((const char *)s, (long)strlen((const char *)s)); return 0; }

/* ---- libc ---- */
void *memcpy(void *d, const void *s, size_t n)
{
    unsigned char *a = d;
    const unsigned char *b = s;
    while (n--) *a++ = *b++;
    return d;
}

void *memmove(void *d, const void *s, size_t n)
{
    unsigned char *a = d;
    const unsigned char *b = s;
    if (a < b) while (n--) *a++ = *b++;
    else while (n--) a[n] = b[n];
    return d;
}

void *memset(void *d, int c, size_t n)
{
    unsigned char *a = d;
    while (n--) *a++ = (unsigned char)c;
    return d;
}

int memcmp(const void *a, const void *b, size_t n)
{
    const unsigned char *x = a, *y = b;
    for (; n; n--, x++, y++)
        if (*x != *y) return *x - *y;
    return 0;
}

size_t strlen(const char *s)
{
    const char *p = s;
    while (*p) p++;
    return (size_t)(p - s);
}

int strcmp(const char *a, const char *b)
{
    while (*a && *a == *b) a++, b++;
    return (unsigned char)*a - (unsigned char)*b;
}

int strncmp(const char *a, const char *b, size_t n)
{
    for (; n; n--, a++, b++) {
        if (*a != *b) return (unsigned char)*a - (unsigned char)*b;
        if (!*a) return 0;
    }
    return 0;
}

char *strcpy(char *d, const char *s)
{
    char *r = d;
    while ((*d++ = *s++)) ;
    return r;
}

char *strchr(const char *s, int c)
{
    for (;; s++) {
        if (*s == (char)c) return (char *)s;
        if (!*s) return NULL;
    }
}
