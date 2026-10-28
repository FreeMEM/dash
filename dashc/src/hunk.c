/* Enlazador: junta el código y los datos del programa con los hunks del runtime
   (un objeto Hunk de gcc, ya enlazado con ld -r) y escribe el ejecutable. */
#include <stdio.h>
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

void link_exe(Obj *obj, const uint8_t *rt, size_t rtlen, const char *out)
{
    FILE *f;
    int i, j;

    VEC_PUSH(hunks, own_hunk(HUNK_CODE, &obj->code));   /* HK_CODE = 0 */
    VEC_PUSH(hunks, own_hunk(HUNK_DATA, &obj->data));   /* HK_DATA = 1 */
    read_object(rt, rtlen);

    for (i = 0; i < refs.n; i++) bind(refs.v[i].hunk, refs.v[i].off, refs.v[i].name);
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

    f = fopen(out, "wb");
    if (!f) fatal("no se puede escribir %s", out);
    wl(f, HUNK_HEADER);
    wl(f, 0);                            /* sin librerías residentes */
    wl(f, (uint32_t)hunks.n);
    wl(f, 0);
    wl(f, (uint32_t)hunks.n - 1);
    for (i = 0; i < hunks.n; i++) wl(f, hunks.v[i].size / 4 | hunks.v[i].memflags);
    for (i = 0; i < hunks.n; i++) {
        Hunk *h = &hunks.v[i];
        wl(f, (uint32_t)h->type);
        wl(f, h->size / 4);
        if (h->data) fwrite(h->data, 1, h->size, f);
        if (h->relocs.n) {
            /* agrupadas por el hunk al que apuntan */
            wl(f, HUNK_RELOC32);
            for (j = 0; j < hunks.n; j++) {
                int k, count = 0;
                for (k = 0; k < h->relocs.n; k++) count += h->relocs.v[k].target == j;
                if (!count) continue;
                wl(f, (uint32_t)count);
                wl(f, (uint32_t)j);
                for (k = 0; k < h->relocs.n; k++)
                    if (h->relocs.v[k].target == j) wl(f, h->relocs.v[k].off);
            }
            wl(f, 0);
        }
        wl(f, HUNK_END);
    }
    if (fclose(f)) fatal("no se puede escribir %s", out);
}
