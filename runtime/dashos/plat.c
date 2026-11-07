/* Dash en DashOS: arranque, memoria (con los nombres de exec), salida (con los de dos) y la libc que usa el
   runtime de Dash, sobre tres funciones de plataforma: dash_plat_write, dash_plat_exit y dash_plat_pages.

   Las de plataforma hablan con el sistema por svc #0 (número en x8, argumentos en x0..x5, resultado en x0):
   - DashOS (por defecto; llamadas provisionales de su C19): escribir = 1 (256 bytes como mucho por llamada),
     salir = 2, canal_crear = 3, canal_leer = 5, cerrar = 6, memoria_crear = 7 (4 MB como mucho por objeto),
     memoria_proyectar = 8 (no encima de algo), temporizador_crear = 24 (C49, para esperar).
   - Linux (-DDASH_PLAT_LINUX), para probar en el PC con qemu-aarch64 (o qemu-aarch64_be): write = 64, exit_group = 94,
     mmap = 222, nanosleep = 101.

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

/* como _svc, y además lo que deja la llamada en x1 (canal_crear da ahí el segundo extremo) */
static long _svc2(long n, long a, long b, long c, long *x1_out)
{
    register long x8 __asm__("x8") = n;
    register long x0 __asm__("x0") = a;
    register long x1 __asm__("x1") = b;
    register long x2 __asm__("x2") = c;
    register long x3 __asm__("x3") = 0;
    register long x4 __asm__("x4") = 0;
    __asm__ volatile("svc #0" : "+r"(x0), "+r"(x1) : "r"(x8), "r"(x2), "r"(x3), "r"(x4) : "memory");
    *x1_out = x1;
    return x0;
}

#define DASH_HEAP_BASE 0x100000000UL
static unsigned long heap_next = DASH_HEAP_BASE;   /* (los PIE de DashOS van de 128 a 256 GB: no chocan) */

#ifdef DASH_PLAT_LINUX
long dash_plat_write(const void *buf, long len) { return _svc(64, 1, (long)buf, len, 0, 0, 0); }
void dash_plat_exit(int code) { for (;;) _svc(94, code, 0, 0, 0, 0, 0); }
void dash_plat_sleep(unsigned long us)
{
    long ts[2] = { (long)(us / 1000000), (long)(us % 1000000) * 1000 };
    (void)_svc2;
    _svc(101, (long)ts, 0, 0, 0, 0, 0);   /* nanosleep */
}
/* ---- las llamadas de DashOS imitadas en Linux (A7), para probar los builtins con qemu-aarch64 en un solo
   programa: canales (de dos lados, colas de 16), llaves con derechos, marca y revocador, temporizadores (vencen
   cuando se lee el canal vacío) y objetos de memoria (memfd, así dos proyecciones comparten). Procesos y grupos:
   E_TIPO. Leer un canal vacío que nada puede llenar para el programa con 20. ---- */
#define EM_KEYS 256
#define EM_OBJS 64
#define EM_COLA 16
enum { EM_LIBRE, EM_LADO, EM_MEMORIA, EM_TEMPO, EM_REVOCADOR };
struct em_llave { int obj, via; unsigned derechos; unsigned long marca; };
struct em_msg { long n, nk; unsigned long marca; unsigned char datos[256]; struct em_llave k[8]; };
struct em_obj {
    int tipo, refs, par, cab, cuantos, destino, revocado, via;
    long fd, tam;
    unsigned long vence, periodo;
    struct em_msg cola[EM_COLA];
};
static struct em_llave em_k[EM_KEYS];   /* la llave n es em_k[n]; obj 0 = libre */
static struct em_obj em_o[EM_OBJS + 1];
static struct { unsigned long at, tam; } em_proy[64];

static unsigned long em_ahora(void)
{
    long ts[2];
    _svc(113, 1, (long)ts, 0, 0, 0, 0);   /* clock_gettime(CLOCK_MONOTONIC) */
    return (unsigned long)ts[0] * 1000000UL + (unsigned long)ts[1] / 1000;
}

static int em_obj_nuevo(int tipo)
{
    int i;
    for (i = 1; i <= EM_OBJS; i++)
        if (em_o[i].tipo == EM_LIBRE) {
            memset(&em_o[i], 0, sizeof em_o[i]);
            em_o[i].tipo = tipo;
            return i;
        }
    return 0;
}

static long em_llave_nueva(int obj, unsigned derechos, unsigned long marca, int via)
{
    int i;
    for (i = 1; i < EM_KEYS; i++)
        if (!em_k[i].obj) {
            em_k[i].obj = obj;
            em_k[i].derechos = derechos;
            em_k[i].marca = marca;
            em_k[i].via = via;
            em_o[obj].refs++;
            return i;
        }
    return -7;
}

static void em_soltar(int obj);

/* la llave n, si vale (y no la revocaron) */
static struct em_llave *em_llave(long n)
{
    struct em_llave *k = n > 0 && n < EM_KEYS && em_k[n].obj ? &em_k[n] : NULL;
    if (k && k->via && em_o[k->via].revocado) return NULL;
    return k;
}

static void em_soltar(int obj)
{
    struct em_obj *o = &em_o[obj];
    if (--o->refs > 0) return;
    if (o->tipo == EM_LADO) {
        int i, j;
        for (i = 0; i < o->cuantos; i++) {          /* los mensajes que nadie leerá sueltan sus llaves */
            struct em_msg *m = &o->cola[(o->cab + i) % EM_COLA];
            for (j = 0; j < m->nk; j++) em_soltar(m->k[j].obj);
        }
        o->cuantos = 0;
        /* sin llaves, el lado queda cerrado (el otro recibe E_CERRADO); los dos se sueltan cuando lo están ambos */
        if (em_o[o->par].refs == 0) em_o[o->par].tipo = o->tipo = EM_LIBRE;
    } else {
        if (o->tipo == EM_MEMORIA) _svc(57, o->fd, 0, 0, 0, 0, 0);   /* close (las proyecciones siguen) */
        o->tipo = EM_LIBRE;
    }
}

/* un lado sigue abierto mientras tenga llaves */
static int em_abierto(int obj) { return em_o[obj].tipo == EM_LADO && em_o[obj].refs > 0; }

static long em_escribir(long llave, const unsigned char *datos, long n, const unsigned *tabla, long nk)
{
    struct em_llave *k = em_llave(llave), *e;
    struct em_obj *dst;
    struct em_msg *m;
    long i, j;
    if (!k) return -2;
    if (em_o[k->obj].tipo != EM_LADO) return -6;
    if (!(k->derechos & 2)) return -3;
    if (n < 0 || n > 256 || nk < 0 || nk > 8) return -5;
    for (i = 0; i < nk; i++) {
        if (!(e = em_llave(tabla[i]))) return -2;
        if (!(e->derechos & 4)) return -3;
        if (e->obj == k->obj || e->obj == em_o[k->obj].par) return -1;
        if (em_o[e->obj].tipo == EM_TEMPO && (em_o[e->obj].destino == k->obj || em_o[e->obj].destino == em_o[k->obj].par)) return -1;
        for (j = 0; j < i; j++) if (tabla[j] == tabla[i]) return -1;
    }
    dst = &em_o[em_o[k->obj].par];
    if (!em_abierto(em_o[k->obj].par)) return -4;
    if (dst->cuantos >= EM_COLA) return -8;
    m = &dst->cola[(dst->cab + dst->cuantos++) % EM_COLA];
    m->n = n;
    m->nk = nk;
    m->marca = k->marca;
    memcpy(m->datos, datos, (size_t)n);
    for (i = 0; i < nk; i++) {                   /* las llaves salen de la tabla y van en el mensaje */
        m->k[i] = em_k[tabla[i]];
        em_k[tabla[i]].obj = 0;
    }
    return 0;
}

static long em_leer(long llave, unsigned char *buf, long cap, unsigned *tabla, long ktam, long out[2])
{
    struct em_llave *k = em_llave(llave);
    struct em_obj *o;
    struct em_msg *m;
    long i;
    if (!k) return -2;
    o = &em_o[k->obj];
    if (o->tipo != EM_LADO) return -6;
    if (!(k->derechos & 1)) return -3;
    while (!o->cuantos) {
        /* el temporizador que avise a este lado y venza antes */
        int t = 0;
        for (i = 1; i <= EM_OBJS; i++)
            if (em_o[i].tipo == EM_TEMPO && em_o[i].destino == k->obj && (!t || em_o[i].vence < em_o[t].vence)) t = (int)i;
        if (t) {
            unsigned long ahora = em_ahora(), veces = 1;
            unsigned char aviso[8];
            if (em_o[t].vence > ahora) dash_plat_sleep(em_o[t].vence - ahora);
            ahora = em_ahora();
            if (em_o[t].periodo) {
                veces = 1 + (ahora - em_o[t].vence) / em_o[t].periodo;
                em_o[t].vence += veces * em_o[t].periodo;
            } else em_o[t].destino = 0;          /* de una vez: ya no avisa */
            for (i = 0; i < 8; i++) aviso[i] = (unsigned char)(veces >> (8 * i));
            m = &o->cola[(o->cab + o->cuantos++) % EM_COLA];
            m->n = 8;
            m->nk = 0;
            m->marca = 0;
            memcpy(m->datos, aviso, 8);
            break;
        }
        if (!em_abierto(o->par)) return -4;
        PutStr((CONST_STRPTR)"dashos (Linux): canal_leer esperaría para siempre\n");
        dash_plat_exit(20);
    }
    m = &o->cola[o->cab];
    if (m->n > cap || m->nk > ktam) return -5;
    memcpy(buf, m->datos, (size_t)m->n);
    for (i = 0; i < m->nk; i++) {
        long nueva = em_llave_nueva(m->k[i].obj, m->k[i].derechos, m->k[i].marca, m->k[i].via);
        em_o[m->k[i].obj].refs--;             /* (em_llave_nueva la contó otra vez) */
        tabla[i] = (unsigned)nueva;
    }
    out[0] = m->nk;
    out[1] = (long)m->marca;
    o->cab = (o->cab + 1) % EM_COLA;
    o->cuantos--;
    return m->n;
}

long dash_os_call(long n, long a, long b, long c, long d, long e, long out[2])
{
    struct em_llave *k;
    long r, i;
    (void)d; (void)e;
    out[0] = out[1] = 0;
    switch (n) {
    case 3: {                                     /* canal_crear */
        int x = em_obj_nuevo(EM_LADO), y = x ? em_obj_nuevo(EM_LADO) : 0;
        if (!y) { if (x) em_o[x].tipo = EM_LIBRE; return -7; }
        em_o[x].par = y;
        em_o[y].par = x;
        r = em_llave_nueva(x, 7, 0, 0);
        out[0] = em_llave_nueva(y, 7, 0, 0);
        return r;
    }
    case 4: return em_escribir(a, (const unsigned char *)b, c, (const unsigned *)d, e);
    case 5: return em_leer(a, (unsigned char *)b, c, (unsigned *)d, e, out);
    case 6:                                       /* cerrar */
        if (!(a > 0 && a < EM_KEYS && em_k[a].obj)) return -2;
        r = em_k[a].obj;
        em_k[a].obj = 0;
        if (em_o[r].tipo == EM_TEMPO) em_o[r].destino = 0;
        em_soltar((int)r);
        return 0;
    case 7: {                                     /* memoria_crear */
        int o;
        if (a <= 0 || a > 0x400000) return -5;
        if (!(o = em_obj_nuevo(EM_MEMORIA))) return -7;
        em_o[o].fd = _svc(279, (long)"dash", 0, 0, 0, 0, 0);   /* memfd_create */
        em_o[o].tam = (a + 4095) & ~4095L;
        if (em_o[o].fd < 0 || _svc(46, em_o[o].fd, em_o[o].tam, 0, 0, 0, 0) < 0) { em_o[o].tipo = EM_LIBRE; return -7; }
        return em_llave_nueva(o, 7, 0, 0);
    }
    case 8:                                       /* memoria_proyectar */
        if (!(k = em_llave(a))) return -2;
        if (em_o[k->obj].tipo != EM_MEMORIA) return -6;
        if ((c & 2 && !(k->derechos & 2)) || !(k->derechos & 1)) return -3;
        /* MAP_SHARED | MAP_FIXED_NOREPLACE */
        r = _svc(222, b, em_o[k->obj].tam, c & 2 ? 3 : 1, 0x01 | 0x100000, em_o[k->obj].fd, 0);
        if (r != b) return -1;
        for (i = 0; i < 64; i++)
            if (!em_proy[i].tam) { em_proy[i].at = (unsigned long)b; em_proy[i].tam = (unsigned long)em_o[k->obj].tam; break; }
        return 0;
    case 21:                                      /* memoria_quitar */
        for (i = 0; i < 64; i++)
            if (em_proy[i].tam && em_proy[i].at == (unsigned long)a) {
                _svc(215, a, (long)em_proy[i].tam, 0, 0, 0, 0);   /* munmap */
                em_proy[i].tam = 0;
                return 0;
            }
        return -1;
    case 15:                                      /* llave_duplicar */
        if (!(k = em_llave(a))) return -2;
        if (k->marca && c && (unsigned long)c != k->marca) return -3;
        return em_llave_nueva(k->obj, k->derechos & (unsigned)b, c ? (unsigned long)c : k->marca, k->via);
    case 16: {                                    /* llave_revocable */
        int v;
        if (!(k = em_llave(a))) return -2;
        if (!(v = em_obj_nuevo(EM_REVOCADOR))) return -7;
        r = em_llave_nueva(k->obj, k->derechos, k->marca, v);
        out[0] = em_llave_nueva(v, 7, 0, 0);
        return r;
    }
    case 17:                                      /* revocar */
        if (!(k = em_llave(a))) return -2;
        if (em_o[k->obj].tipo != EM_REVOCADOR) return -6;
        em_o[k->obj].revocado = 1;
        for (i = 1; i <= EM_OBJS; i++)            /* un temporizador creado por una llave revocada se para */
            if (em_o[i].tipo == EM_TEMPO && em_o[i].via == k->obj) em_o[i].destino = 0;
        return 0;
    case 24: {                                    /* temporizador_crear */
        int t;
        if (!(k = em_llave(a))) return -2;
        if (em_o[k->obj].tipo != EM_LADO) return -6;
        if (!(k->derechos & 2)) return -3;
        if (b < 0 || c < 0 || b > 86400000000L || c > 86400000000L) return -1;
        if (!(t = em_obj_nuevo(EM_TEMPO))) return -7;
        em_o[t].destino = em_o[k->obj].par;       /* avisa al otro lado */
        em_o[t].via = k->via;
        em_o[t].vence = em_ahora() + (unsigned long)(b < 10000 ? 10000 : b);
        em_o[t].periodo = c ? (unsigned long)(c < 10000 ? 10000 : c) : 0;
        return em_llave_nueva(t, 7, 0, 0);
    }
    default:
        return -6;                                /* procesos y grupos: no en Linux */
    }
}

void *dash_plat_pages(unsigned long bytes)
{
    /* MAP_PRIVATE | MAP_ANONYMOUS | MAP_FIXED_NOREPLACE, PROT_READ | PROT_WRITE */
    long r = _svc(222, (long)heap_next, (long)bytes, 3, 0x02 | 0x20 | 0x100000, -1, 0);
    if (r < 0 || (unsigned long)r != heap_next) return NULL;
    heap_next += bytes;
    return (void *)r;
}
#else
/* escribir toma como mucho 256 bytes por llamada (DashOS C35) y dice cuántos tomó: se repite con el resto */
long dash_plat_write(const void *buf, long len)
{
    long done = 0, r;
    while (done < len) {
        r = _svc(1, (long)buf + done, len - done, 0, 0, 0, 0);
        if (r <= 0) return done ? done : r;
        done += r;
    }
    return done;
}
void dash_plat_exit(int code) { for (;;) _svc(2, code, 0, 0, 0, 0, 0); }

/* Esperar sin gastar CPU (DashOS C49): un canal nuevo, un temporizador de una vez que avisa por él, y leer. La
   resolución es la del tic de DashOS, 10 ms. Si el kernel no tiene temporizadores, se espera girando sobre el
   contador del sistema. */
void dash_plat_sleep(unsigned long us)
{
    long a, b, t;
    unsigned char aviso[8];
    if (us == 0) return;
    a = _svc2(3, 0, 0, 0, &b);                       /* canal_crear: (a, b) */
    t = a > 0 ? _svc(24, b, (long)us, 0, 0, 0, 0) : -1;   /* temporizador_crear(b, us, una vez) */
    if (t > 0) {
        _svc(5, a, (long)aviso, sizeof aviso, 0, 0, 0);   /* canal_leer: llega a los us */
        _svc(6, t, 0, 0, 0, 0, 0);
    } else {
        unsigned long f, c0, c;
        __asm__ volatile("mrs %0, cntfrq_el0" : "=r"(f));
        __asm__ volatile("isb; mrs %0, cntvct_el0" : "=r"(c0));
        do __asm__ volatile("isb; mrs %0, cntvct_el0" : "=r"(c)); while ((c - c0) < us * (f / 1000000));
    }
    if (a > 0) {
        _svc(6, a, 0, 0, 0, 0, 0);
        _svc(6, b, 0, 0, 0, 0, 0);
    }
}

/* memoria_crear da como mucho 4 MB por objeto (C35): un trozo mayor son varios objetos proyectados seguidos desde
   at. Devuelve cuántos bytes quedaron proyectados (bytes si todo fue bien); memoria_crear la da a cero */
#define DASH_MAP_MAX 0x400000UL
static unsigned long dashos_map(unsigned long at, unsigned long bytes)
{
    unsigned long done = 0, n;
    long key;
    while (done < bytes) {
        n = bytes - done > DASH_MAP_MAX ? DASH_MAP_MAX : bytes - done;
        key = _svc(7, (long)n, 0, 0, 0, 0, 0);
        if (key < 0 || _svc(8, key, (long)(at + done), 3, 0, 0, 0) < 0) break;
        done += n;
    }
    return done;
}

long dash_os_call(long n, long a, long b, long c, long d, long e, long out[2])
{
    register long x8 __asm__("x8") = n;
    register long x0 __asm__("x0") = a;
    register long x1 __asm__("x1") = b;
    register long x2 __asm__("x2") = c;
    register long x3 __asm__("x3") = d;
    register long x4 __asm__("x4") = e;
    __asm__ volatile("svc #0" : "+r"(x0), "+r"(x1), "+r"(x2) : "r"(x8), "r"(x3), "r"(x4) : "memory");
    out[0] = x1;
    out[1] = x2;
    return x0;
}

void *dash_plat_pages(unsigned long bytes)
{
    unsigned long at = heap_next, got = dashos_map(at, bytes);
    heap_next += got;                     /* (lo proyectado no se vuelve a proyectar, aunque falte el resto) */
    return got == bytes ? (void *)at : NULL;
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
        unsigned long got = dashos_map(box_end, want);
        if (got != want) { box_next = box_end += got; return NULL; }
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

/* ---- búferes de Dash (buffer_alloc y memory_map, A7): entre 1,5 y 2 GB. Un programa guarda un búfer en un Int,
   que en DashOS es de 32 bits (LONG): aquí su dirección cabe. 0x6000_0000..0x7000_0000 para buffer_alloc (lista
   de libres sin juntar: los búferes suelen ser pocos y grandes); 0x7000_0000..0x7800_0000, 32 huecos de 4 MB
   para memory_map (los reparte el runtime). Por encima, la pila de los ejecutables ET_EXEC (hasta 2 GB). ---- */
#define DASH_BUF_BASE 0x60000000UL
#define DASH_BUF_END 0x70000000UL
typedef struct BufH { unsigned long size; struct BufH *next; } BufH;
static unsigned long buf_next = DASH_BUF_BASE, buf_end = DASH_BUF_BASE;
static BufH *buf_free;

void *dash_plat_buffer_alloc(unsigned long bytes)
{
    unsigned long n = (bytes + 15) & ~15UL;
    BufH **pp, *h;
    if (!n) n = 16;
    if (bytes > DASH_BUF_END - DASH_BUF_BASE) return NULL;
    for (pp = &buf_free; (h = *pp) && h->size < n; pp = &h->next) ;
    if (h) {
        *pp = h->next;
        memset(h + 1, 0, h->size);
        return h + 1;
    }
    if (buf_next + sizeof(BufH) + n > buf_end) {
        unsigned long want = (buf_next + sizeof(BufH) + n - buf_end + 0xFFFFUL) & ~0xFFFFUL;
        if (buf_end + want > DASH_BUF_END) return NULL;
#ifdef DASH_PLAT_LINUX
        long r = _svc(222, (long)buf_end, (long)want, 3, 0x02 | 0x20 | 0x100000, -1, 0);
        if (r < 0 || (unsigned long)r != buf_end) return NULL;
        buf_end += want;
#else
        unsigned long got = dashos_map(buf_end, want);
        buf_end += got;
        if (got != want) return NULL;
#endif
    }
    h = (BufH *)buf_next;                 /* (recién proyectado: a cero) */
    h->size = n;
    buf_next += sizeof(BufH) + n;
    return h + 1;
}

void dash_plat_buffer_free(void *p)
{
    BufH *h;
    if (!p) return;
    h = (BufH *)p - 1;
    h->next = buf_free;
    buf_free = h;
}

/* ---- arranque ----
   Un programa PIE (./dash --dashos --pie: ET_DYN estático, sin enlazador dinámico) se reubica a sí mismo antes de nada:
   aplica las R_AARCH64_RELATIVE de su .dynamic con la dirección donde lo cargaron. Esta función no puede usar
   punteros guardados (aún no valen): solo direcciones relativas al código (símbolos ocultos). Sin PIE no hay
   _DYNAMIC y no hace nada. */
extern const unsigned long _DYNAMIC[] __attribute__((weak, visibility("hidden")));
extern const char __ehdr_start[] __attribute__((visibility("hidden")));
void _dash_relocate(void) __attribute__((used));
void _dash_relocate(void)
{
    unsigned long base = (unsigned long)__ehdr_start, rela = 0, size = 0, i;
    const unsigned long *d = _DYNAMIC;
    if (!d) return;
    for (; d[0]; d += 2) {
        if (d[0] == 7) rela = d[1];                   /* DT_RELA */
        else if (d[0] == 8) size = d[1];              /* DT_RELASZ */
    }
    for (i = 0; i < size / 24; i++) {
        const unsigned long *r = (const unsigned long *)(base + rela) + 3 * i;
        if ((r[1] & 0xFFFFFFFF) == 1027)              /* R_AARCH64_RELATIVE */
            *(unsigned long *)(base + r[0]) = base + r[2];
    }
}

/* El camino por C entra por _start (y llama a main); el código de dashc, por _dash_entry, que sigue en su
   _dashc_start (no tiene main) */
int main() __attribute__((weak));
void _dash_atexit_run(void);
__asm__(".text\n.global _start\n.type _start, %function\n_start:\n"
        "    mov x29, #0\n    mov x30, #0\n    bl _dash_relocate\n    bl _dash_start_c\n    b .\n"
        ".global _dash_entry\n.type _dash_entry, %function\n.weak _dashc_start\n_dash_entry:\n"
        "    mov x29, #0\n    mov x30, #0\n    bl _dash_relocate\n    b _dashc_start\n");
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
/* dos: esperar tics de 1/50 s (A7) */
void Delay(LONG ticks) { if (ticks > 0) dash_plat_sleep((unsigned long)ticks * 20000UL); }

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
