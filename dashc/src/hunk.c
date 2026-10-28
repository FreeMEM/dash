/* Enlazador: junta el código y los datos del programa con los hunks del runtime que usa
   (un objeto Hunk de gcc, ya enlazado con ld -r, con un hunk por función) y escribe el ejecutable. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "dashc.h"

enum {
    HUNK_UNIT = 0x3E7, HUNK_NAME = 0x3E8, HUNK_CODE = 0x3E9, HUNK_DATA = 0x3EA,
    HUNK_BSS = 0x3EB, HUNK_RELOC32 = 0x3EC, HUNK_EXT = 0x3EF, HUNK_SYMBOL = 0x3F0,
    HUNK_DEBUG = 0x3F1, HUNK_END = 0x3F2, HUNK_HEADER = 0x3F3
};

typedef struct { uint32_t off; int target; } HReloc;

typedef struct {
    int type;            /* HUNK_CODE, HUNK_DATA o HUNK_BSS */
    uint32_t memflags;   /* bits 30-31: memoria chip o fast */
    uint32_t size;       /* en bytes, múltiplo de 4 */
    uint8_t *data;       /* NULL en BSS */
    const char *secname; /* su sección (HUNK_NAME), para DASHC_MAPA */
    int align2;          /* un texto constante suelto: basta con alinearlo a 2 (split_strings) */
    struct { HReloc *v; int n, cap; } relocs;
} Hunk;

typedef struct { const char *name; int hunk; uint32_t val; int abs; } Sym;

static struct { Hunk *v; int n, cap; } hunks;
static struct { Sym *v; int n, cap; } syms;

typedef struct { int hunk; uint32_t off; char *name; } Ref;
static struct { Ref *v; int n, cap; } refs;

static const uint8_t *rp, *rend;

static uint32_t rd(void)
{
    uint32_t v;
    if (rp + 4 > rend) fatal("runtime: objeto Hunk cortado");
    v = get_long(rp);
    rp += 4;
    return v;
}

static void add_sym(const char *name, int hunk, uint32_t val, int abs)
{
    Sym s;
    s.name = name;
    s.hunk = hunk;
    s.val = val;
    s.abs = abs;
    VEC_PUSH(syms, s);
}

static Sym *find_sym(const char *name)
{
    int i;
    for (i = 0; i < syms.n; i++)
        if (!strcmp(syms.v[i].name, name)) return &syms.v[i];
    return NULL;
}

/* lee las unidades de un objeto Hunk; sus hunks se numeran a partir de hunks.n */
static void read_object(const uint8_t *p, size_t len)
{
    int base = 0, cur = -1;
    char *pending_name = NULL;
    rp = p;
    rend = p + len;
    while (rp < rend) {
        uint32_t raw = rd(), type = raw & 0x3FFFFFFF, n;
        switch (type) {
        case HUNK_UNIT:
            base = hunks.n;
            cur = -1;
            n = rd();
            rp += n * 4;
            break;
        case HUNK_NAME:
            n = rd();
            pending_name = xstrndup((const char *)rp, n * 4);
            rp += n * 4;
            break;
        case HUNK_CODE:
        case HUNK_DATA:
        case HUNK_BSS: {
            Hunk h = {0};
            n = rd() & 0x3FFFFFFF;
            h.type = (int)type;
            h.memflags = raw & 0xC0000000;
            h.size = n * 4;
            h.secname = pending_name;
            pending_name = NULL;
            if (type != HUNK_BSS) {
                h.data = xmalloc(h.size);
                if (rp + h.size > rend) fatal("runtime: objeto Hunk cortado");
                memcpy(h.data, rp, h.size);
                rp += h.size;
            }
            VEC_PUSH(hunks, h);
            cur = hunks.n - 1;
            break;
        }
        case HUNK_RELOC32:
            for (;;) {
                uint32_t i, count = rd(), target;
                if (!count) break;
                target = rd();
                for (i = 0; i < count; i++) {
                    HReloc r;
                    r.off = rd();
                    r.target = base + (int)target;
                    VEC_PUSH(hunks.v[cur].relocs, r);
                }
            }
            break;
        case HUNK_EXT:
            for (;;) {
                uint32_t word = rd(), kind = word >> 24, nl = word & 0xFFFFFF, i, count;
                char *name;
                if (!word) break;
                name = xstrndup((const char *)rp, nl * 4);
                rp += nl * 4;
                if (kind < 0x80) {
                    uint32_t val = rd();
                    if (kind == 1 || kind == 3) add_sym(name, cur, val, 0);  /* EXT_DEF, EXT_RES */
                    else if (kind == 2) add_sym(name, -1, val, 1);           /* EXT_ABS */
                    /* los demás son símbolos locales: no se exportan */
                } else if (kind == 0x81) {                                   /* EXT_REF32 */
                    count = rd();
                    for (i = 0; i < count; i++) {
                        Ref r;
                        r.hunk = cur;
                        r.off = rd();
                        r.name = name;
                        VEC_PUSH(refs, r);
                    }
                } else if (kind == 0x82) {
                    fatal("runtime: símbolo común %s (compílalo con -fno-common)", name);
                } else {
                    fatal("runtime: referencia de tipo 0x%x a %s aún no admitida", (unsigned)kind, name);
                }
            }
            break;
        case HUNK_SYMBOL:
            for (;;) {
                uint32_t nl = rd();
                if (!nl) break;
                rp += nl * 4 + 4;
            }
            break;
        case HUNK_DEBUG:
            n = rd();
            rp += n * 4;
            break;
        case HUNK_END:
            cur = -1;
            break;
        default:
            fatal("runtime: bloque Hunk 0x%x aún no admitido", (unsigned)type);
        }
    }
}

/* ¿define el runtime este símbolo? (lee sus nombres una vez y lo deja todo como estaba) */
int runtime_has(const char *sym)
{
    static struct { char **v; int n, cap; } names;
    static int loaded;
    int i;
    if (!loaded) {
        loaded = 1;
        read_object(rt_blob, rt_blob_len);
        for (i = 0; i < syms.n; i++) VEC_PUSH(names, (char *)syms.v[i].name);
        hunks.n = 0;
        syms.n = 0;
        refs.n = 0;
    }
    for (i = 0; i < names.n; i++)
        if (!strcmp(names.v[i], sym)) return 1;
    return 0;
}

/* apunta en el long de (hunk, off) la dirección del símbolo */
static void bind(int hunk, uint32_t off, const char *name)
{
    Sym *s = find_sym(name);
    uint8_t *p = hunks.v[hunk].data + off;
    if (!s) fatal("el runtime no tiene %s", name);
    put_long(p, get_long(p) + s->val);
    if (!s->abs) {
        HReloc r;
        r.off = off;
        r.target = s->hunk;
        VEC_PUSH(hunks.v[hunk].relocs, r);
    }
}

static void wl(FILE *f, uint32_t v)
{
    uint8_t b[4];
    put_long(b, v);
    fwrite(b, 1, 4, f);
}

static Hunk own_hunk(int type, Buf *b)
{
    Hunk h = {0};
    while (b->n & 3) buf_byte(b, 0);
    if (!b->n) buf_long(b, 0);
    h.type = type;
    h.size = (uint32_t)b->n;
    h.data = b->p;
    return h;
}

/* Desde los hunks de la pila, marca en keep los que alcanzan sus reubicaciones (atando antes los
   símbolos de cada uno); lo que apunta un hunk débil no cuenta */
static void reach(int *keep, int *stack, int sp, const int *weak)
{
    int j;
    while (sp) {
        int cur = stack[--sp];
        Hunk *h = &hunks.v[cur];
        for (j = 0; j < refs.n; j++)
            if (refs.v[j].hunk == cur) {
                bind(cur, refs.v[j].off, refs.v[j].name);
                refs.v[j].hunk = -1;               /* ya está */
            }
        if (weak[cur]) continue;
        for (j = 0; j < h->relocs.n; j++)
            if (!keep[h->relocs.v[j].target]) {
                keep[h->relocs.v[j].target] = 1;
                stack[sp++] = h->relocs.v[j].target;
            }
    }
}

/* la ventana y el RastPort de dibujo actuales: los usan casi todos los runtimes de ventanas y gráficos
   (que sus limpiezas los toquen no dice que el programa use esos runtimes) */
static int shared_data(int d)
{
    int k;
    for (k = 0; k < syms.n; k++)
        if (syms.v[k].hunk == d && (!strcmp(syms.v[k].name, "__dash_win") || !strcmp(syms.v[k].name, "__dash_rp")))
            return 1;
    return 0;
}

/* ¿usa el hunk t datos o BSS que van en el programa y no son del arranque? (sus reubicaciones y sus
   símbolos aún sin atar) */
static int touches_own_data(int t, const int *keep, const int *core)
{
    int j, d;
    Hunk *h = &hunks.v[t];
    for (j = 0; j < h->relocs.n + refs.n; j++) {
        if (j < h->relocs.n) {
            d = h->relocs.v[j].target;
        } else {
            Sym *s;
            if (refs.v[j - h->relocs.n].hunk != t) continue;
            s = find_sym(refs.v[j - h->relocs.n].name);
            if (!s || s->abs) continue;
            d = s->hunk;
        }
        if (keep[d] && !core[d] && hunks.v[d].type != HUNK_CODE && !shared_data(d)) {
            if (getenv("DASHC_MAPA")) {
                const char *a = hunks.v[t].secname, *b = hunks.v[d].secname;
                int k;
                for (k = 0; k < syms.n; k++)
                    if (syms.v[k].hunk == d) b = syms.v[k].name;
                fprintf(stderr, "limpieza %s por %s\n", a ? a : "?", b ? b : "?");
            }
            return 1;
        }
    }
    return 0;
}

static int cmp_u32(const void *a, const void *b)
{
    uint32_t x = *(const uint32_t *)a, y = *(const uint32_t *)b;
    return x < y ? -1 : x > y;
}

/* Los textos constantes de un objeto de C (gcc de Amiga los deja en su .text, sin trocear aunque las funciones
   vayan cada una en su sección): un hunk .text sin símbolos ni reubicaciones propias se parte en un hunk por
   texto al que se llega, para que cada programa lleve solo los suyos. Cada trozo empieza tras el 0 del texto
   anterior (una referencia al medio de un texto se queda con el texto entero). Solo si todo parece texto: un
   byte de control raro dice que hay tablas binarias (zlib), y el hunk se queda entero. */
static void split_strings(int first)
{
    int i, j, k, n0 = hunks.n;
    for (i = first; i < n0; i++) {
        Hunk *h = &hunks.v[i];
        uint32_t *starts = NULL;
        int ns = 0, bad = 0;
        if (h->type != HUNK_CODE || !h->secname || strcmp(h->secname, ".text") || h->relocs.n || !h->data) continue;
        for (j = 0; j < syms.n && !bad; j++) bad = syms.v[j].hunk == i && !syms.v[j].abs;
        for (j = 0; j < (int)h->size && !bad; j++) {
            uint8_t c = h->data[j];
            bad = c > 0 && c < 32 && c != 7 && c != 8 && c != 9 && c != 10 && c != 12 && c != 13 && c != 27;
        }
        for (j = 0; j < refs.n && !bad; j++) bad = refs.v[j].hunk == i;
        /* dónde empiezan los textos a los que se llega */
        starts = xmalloc(sizeof(uint32_t));
        starts[ns++] = 0;
        for (j = first; j < n0 && !bad; j++)
            for (k = 0; k < hunks.v[j].relocs.n && !bad; k++)
                if (hunks.v[j].relocs.v[k].target == i) {
                    uint32_t o = get_long(hunks.v[j].data + hunks.v[j].relocs.v[k].off);
                    if (o >= h->size) {
                        bad = 1;
                        break;
                    }
                    while (o > 0 && h->data[o - 1] != 0) o--;
                    starts = xrealloc(starts, sizeof(uint32_t) * (ns + 1));
                    starts[ns++] = o;
                }
        if (!bad) {
            qsort(starts, ns, sizeof(uint32_t), cmp_u32);
            for (j = k = 1; j < ns; j++)
                if (starts[j] != starts[k - 1]) starts[k++] = starts[j];
            ns = k;
        }
        if (bad || ns < 2) {                           /* (con un solo texto, nada que partir) */
            free(starts);
            continue;
        }
        /* las referencias, a su trozo (el primero se queda en este hunk; los demás, hunks nuevos tras los
           que hay) */
        for (j = first; j < n0; j++)
            for (k = 0; k < hunks.v[j].relocs.n; k++)
                if (hunks.v[j].relocs.v[k].target == i) {
                    uint8_t *p = hunks.v[j].data + hunks.v[j].relocs.v[k].off;
                    uint32_t o = get_long(p);
                    int a = 0, b = ns - 1;
                    while (a < b) {                    /* el último inicio <= o */
                        int m = (a + b + 1) / 2;
                        if (starts[m] <= o) a = m;
                        else b = m - 1;
                    }
                    put_long(p, o - starts[a]);
                    if (a) hunks.v[j].relocs.v[k].target = hunks.n + a - 1;
                }
        for (j = 1; j < ns; j++) {
            Hunk piece = {0};
            uint32_t end = j + 1 < ns ? starts[j + 1] : hunks.v[i].size;
            piece.type = HUNK_CODE;
            piece.size = end - starts[j];
            piece.data = xmalloc(piece.size);
            memcpy(piece.data, hunks.v[i].data + starts[j], piece.size);
            piece.secname = ".text (un texto)";
            piece.align2 = 1;
            VEC_PUSH(hunks, piece);
        }
        hunks.v[i].size = starts[1];
        hunks.v[i].align2 = 1;
        free(starts);
    }
}

/* Solo va lo que se usa: desde el código y los datos del programa, los hunks del runtime a los que
   llega alguna reubicación (el runtime va compilado con -ffunction-sections: un hunk por función).
   Los que van se juntan en un hunk de código, uno de datos y uno de BSS. */
void link_exe(Obj *obj, const uint8_t *rt, size_t rtlen, const char *out)
{
    FILE *f;
    int i, j, k, nout;
    int *keep, *outh, *stack, *weak, *core, more, sp = 0;
    uint32_t *base, outsize[3] = {0, 0, 0};
    static const int outtype[3] = {HUNK_CODE, HUNK_DATA, HUNK_BSS};
    struct { HReloc *v; int n, cap; } outrel[3] = {{0}};

    VEC_PUSH(hunks, own_hunk(HUNK_CODE, &obj->code));   /* HK_CODE = 0 */
    VEC_PUSH(hunks, own_hunk(HUNK_DATA, &obj->data));   /* HK_DATA = 1 */
    read_object(rt, rtlen);
    if (!getenv("DASHC_SIN_TROCEAR")) split_strings(2);

    /* los símbolos, solo los de los hunks a los que se llega (el runtime trae funciones que usan cosas
       que ningún programa enlaza todavía) */
    for (i = 0; i < obj->relocs.n; i++) {
        Reloc *r = &obj->relocs.v[i];
        if (r->sym) {
            bind(HK_CODE, r->off, r->sym);
        } else {
            HReloc h;
            h.off = r->off;
            h.target = r->hunk;
            VEC_PUSH(hunks.v[HK_CODE].relocs, h);
        }
    }

    /* lo que se alcanza desde el programa */
    keep = xmalloc(sizeof(int) * hunks.n);
    stack = xmalloc(sizeof(int) * hunks.n);
    memset(keep, 0, sizeof(int) * hunks.n);
    /* hunks débiles: los de un símbolo _dash_weak_* (un puntero a una función de limpieza); lo que
       apuntan no cuenta como usado */
    weak = xmalloc(sizeof(int) * hunks.n);
    memset(weak, 0, sizeof(int) * hunks.n);
    for (i = 0; i < syms.n; i++)
        if (syms.v[i].hunk >= 0 && !strncmp(syms.v[i].name, "__dash_weak_", 12)) weak[syms.v[i].hunk] = 1;
    keep[0] = keep[1] = 1;
    stack[sp++] = 0;
    stack[sp++] = 1;
    reach(keep, stack, sp, weak);

    /* La función de un puntero débil (la limpieza de un runtime) va si toca datos que el programa usa y
       que no son de todos (los del arranque: las bases de las librerías, _dash_win...): la de los
       temporizadores si hay temporizadores, la de los gadgets si hay gadgets. Hasta que no entre ninguna
       más (una que entra puede usar datos de otra). */
    core = xmalloc(sizeof(int) * hunks.n);
    memset(core, 0, sizeof(int) * hunks.n);
    {
        Sym *st = find_sym("__dash_start");
        if (st && !st->abs) {
            core[st->hunk] = 1;
            stack[0] = st->hunk;
            reach(core, stack, 1, weak);
        }
    }
    for (more = !getenv("DASHC_SIN_LIMPIEZAS"); more; ) {
        more = 0;
        for (i = 0; i < hunks.n; i++) {
            Hunk *h = &hunks.v[i];
            if (!keep[i] || !weak[i]) continue;
            for (j = 0; j < h->relocs.n; j++) {
                int t = h->relocs.v[j].target;
                if (!keep[t] && touches_own_data(t, keep, core)) {
                    keep[t] = 1;
                    stack[0] = t;
                    reach(keep, stack, 1, weak);
                    more = 1;
                }
            }
        }
    }

    /* un puntero débil a algo que no va: 0, sin reubicación */
    for (i = 0; i < hunks.n; i++)
        if (keep[i] && weak[i]) {
            Hunk *h = &hunks.v[i];
            for (j = 0; j < h->relocs.n; j++)
                if (!keep[h->relocs.v[j].target]) {
                    put_long(h->data + h->relocs.v[j].off, 0);
                    h->relocs.v[j--] = h->relocs.v[--h->relocs.n];
                }
        }

    /* dónde va cada uno en el hunk de su tipo (0 código, 1 datos, 2 BSS) */
    base = xmalloc(sizeof(uint32_t) * hunks.n);
    outh = xmalloc(sizeof(int) * hunks.n);
    for (i = 0; i < hunks.n; i++) {
        Hunk *h = &hunks.v[i];
        if (!keep[i]) continue;
        if (h->memflags) fatal("runtime: un hunk con memoria chip o fast aún no se admite");
        outh[i] = h->type == HUNK_CODE ? 0 : h->type == HUNK_DATA ? 1 : 2;
        base[i] = outsize[outh[i]];
        outsize[outh[i]] += h->align2 ? (h->size + 1) & ~1u : (h->size + 3) & ~3u;
    }
    for (k = 0; k < 3; k++) outsize[k] = (outsize[k] + 3) & ~3u;
    /* las reubicaciones, a su sitio en los hunks juntados */
    for (i = 0; i < hunks.n; i++) {
        Hunk *h = &hunks.v[i];
        if (!keep[i]) continue;
        for (j = 0; j < h->relocs.n; j++) {
            HReloc r;
            int t = h->relocs.v[j].target;
            uint8_t *p = h->data + h->relocs.v[j].off;
            put_long(p, get_long(p) + base[t]);
            r.off = base[i] + h->relocs.v[j].off;
            r.target = outh[t];
            VEC_PUSH(outrel[outh[i]], r);
        }
    }
    nout = outsize[2] ? 3 : 2;
    if (getenv("DASHC_MAPA"))
        for (i = 2; i < hunks.n; i++)
            if (keep[i]) {
                const char *name = hunks.v[i].secname ? hunks.v[i].secname : "?";
                for (j = 0; j < syms.n; j++)
                    if (syms.v[j].hunk == i) name = syms.v[j].name;
                fprintf(stderr, "%6u %c %s\n", (unsigned)hunks.v[i].size, "CDB"[hunks.v[i].type - HUNK_CODE], name);
            }

    f = fopen(out, "wb");
    if (!f) fatal("no se puede escribir %s", out);
    wl(f, HUNK_HEADER);
    wl(f, 0);                            /* sin librerías residentes */
    wl(f, (uint32_t)nout);
    wl(f, 0);
    wl(f, (uint32_t)nout - 1);
    for (k = 0; k < nout; k++) wl(f, outsize[k] / 4);
    for (k = 0; k < nout; k++) {
        static const uint8_t zero[4];
        wl(f, (uint32_t)outtype[k]);
        wl(f, outsize[k] / 4);
        if (k < 2) {
            uint32_t done = 0;
            for (i = 0; i < hunks.n; i++) {
                Hunk *h = &hunks.v[i];
                uint32_t padded;
                if (!keep[i] || outh[i] != k) continue;
                padded = h->align2 ? (h->size + 1) & ~1u : (h->size + 3) & ~3u;
                fwrite(h->data, 1, h->size, f);
                fwrite(zero, 1, padded - h->size, f);
                done += padded;
            }
            fwrite(zero, 1, outsize[k] - done, f);
        }
        if (outrel[k].n) {
            /* agrupadas por el hunk al que apuntan */
            wl(f, HUNK_RELOC32);
            for (j = 0; j < nout; j++) {
                int count = 0, m;
                for (m = 0; m < outrel[k].n; m++) count += outrel[k].v[m].target == j;
                if (!count) continue;
                wl(f, (uint32_t)count);
                wl(f, (uint32_t)j);
                for (m = 0; m < outrel[k].n; m++)
                    if (outrel[k].v[m].target == j) wl(f, outrel[k].v[m].off);
            }
            wl(f, 0);
        }
        wl(f, HUNK_END);
    }
    if (fclose(f)) fatal("no se puede escribir %s", out);
}
