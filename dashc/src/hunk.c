/* Enlazador: junta el código y los datos del programa con los hunks del runtime que usa
   (un objeto Hunk de gcc, ya enlazado con ld -r, con un hunk por función) y escribe el ejecutable. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "dashc.h"
#include "zlib.h"

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
    int shared;          /* data apunta al runtime preparado (de solo lectura): se copia antes de cambiarla */
    const uint8_t *lazy; /* sus reubicaciones en el runtime preparado, aún sin leer (relocs_ready) */
    const uint8_t *zdata; /* sus datos comprimidos (DRT2), aún sin descomprimir (own_data) */
    uint32_t zlen;
    int lazy_n, lazy_base;
    struct { HReloc *v; int n, cap; } relocs;
} Hunk;

typedef struct { const char *name; int hunk; uint32_t val; int abs; } Sym;

static struct { Hunk *v; int n, cap; } hunks;
static struct { Sym *v; int n, cap; } syms;

typedef struct { int hunk; uint32_t off; char *name; } Ref;
static struct { Ref *v; int n, cap; } refs;

static const uint8_t *rp, *rend;
#define DRT_MAGIC 0x44525431u     /* "DRT1": el runtime preparado (prepare_runtime) */
#define DRT2_MAGIC 0x44525432u    /* "DRT2": lo mismo con los datos de cada hunk comprimidos (runtime/rt_blob.py) */
static void load_prepared(const uint8_t *p, size_t len);
static const char *obj_name = "runtime";     /* el objeto que se lee, para los errores */

/* los símbolos comunes (variables de C sin -fno-common): un BSS para cada uno que nadie define */
typedef struct { char *name; uint32_t size; } Common;
static struct { Common *v; int n, cap; } commons;

/* lo de @link: objetos Hunk y bibliotecas (.a) de gcc */
static struct { const char **v; int n, cap; } link_files;
void link_add(const char *path) { VEC_PUSH(link_files, path); }
static struct { const char **v; int n, cap; } missing;   /* lo que nadie define (bind) */

static uint32_t rd(void)
{
    uint32_t v;
    if (rp + 4 > rend) fatal("%s: objeto Hunk cortado", obj_name);
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
                if (rp + h.size > rend) fatal("%s: objeto Hunk cortado", obj_name);
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
                } else if (kind == 0x82) {                                   /* EXT_COMMON: tamaño y refs */
                    Common c;
                    c.name = name;
                    c.size = rd();
                    VEC_PUSH(commons, c);
                    count = rd();
                    for (i = 0; i < count; i++) {
                        Ref r;
                        r.hunk = cur;
                        r.off = rd();
                        r.name = name;
                        VEC_PUSH(refs, r);
                    }
                } else {
                    fatal("%s: referencia de tipo 0x%x a %s aún no admitida", obj_name, (unsigned)kind, name);
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
            fatal("%s: bloque Hunk 0x%x aún no admitido", obj_name, (unsigned)type);
        }
    }
}

/* un fichero de @link: un objeto Hunk o una biblioteca de ellos (ar, como las de gcc) */
static void read_linked(const char *path)
{
    FILE *f = fopen(path, "rb");
    uint8_t *p;
    long len;
    if (!f) fatal("@link: no puedo leer %s", path);
    fseek(f, 0, SEEK_END);
    len = ftell(f);
    fseek(f, 0, SEEK_SET);
    p = xmalloc((size_t)len + 1);
    if (fread(p, 1, (size_t)len, f) != (size_t)len) fatal("@link: no puedo leer %s", path);
    fclose(f);
    obj_name = path;
    if (len >= 8 && !memcmp(p, "!<arch>\n", 8)) {
        long off = 8;
        while (off + 60 <= len) {
            char size_txt[11];
            long size;
            const uint8_t *hdr = p + off;
            memcpy(size_txt, hdr + 48, 10);
            size_txt[10] = 0;
            size = atol(size_txt);
            off += 60;
            if (size < 0 || off + size > len) fatal("@link: %s está cortada", path);
            /* (la tabla de símbolos "/" o "__.SYMDEF" y la de nombres largos "//" no son objetos) */
            if (hdr[0] != '/' && memcmp(hdr, "__.SYMDEF", 9)) {
                if (size < 4 || get_long(p + off) != HUNK_UNIT)
                    fatal("@link: %s tiene un objeto que no es Hunk (¿compilado con el gcc de Amiga?)", path);
                read_object(p + off, (size_t)size);
            }
            off += size + (size & 1);
        }
    } else {
        if (len < 4 || get_long(p) != HUNK_UNIT) fatal("@link: %s no es un objeto Hunk (¿compilado con el gcc de Amiga?)", path);
        read_object(p, (size_t)len);
    }
    obj_name = "runtime";
}

/* ¿define el runtime este símbolo? (lee sus nombres una vez y lo deja todo como estaba) */
int runtime_has(const char *sym)
{
    static struct { char **v; int n, cap; } names;
    static int loaded;
    int i;
    if (!loaded) {
        loaded = 1;
        if (rt_blob_len >= 4 && (get_long(rt_blob) == DRT_MAGIC || get_long(rt_blob) == DRT2_MAGIC))
            load_prepared(rt_blob, rt_blob_len);
        else read_object(rt_blob, rt_blob_len);
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
static uint8_t *own_data(int i);
static void relocs_ready(int i);

static void bind(int hunk, uint32_t off, const char *name)
{
    Sym *s = find_sym(name);
    uint8_t *p;
    if (!s) {
        int i;
        if (!link_files.n) fatal("el runtime no tiene %s", name);
        /* (se apuntan todos los que faltan y se dicen juntos al final) */
        for (i = 0; i < missing.n; i++)
            if (!strcmp(missing.v[i], name)) return;
        VEC_PUSH(missing, name);
        return;
    }
    p = own_data(hunk) + off;
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
static int *why;
static const char *hunk_name(int i)
{
    const char *name = hunks.v[i].secname ? hunks.v[i].secname : "?";
    int j;
    for (j = 0; j < syms.n; j++)                     /* el símbolo del principio, si lo hay */
        if (syms.v[j].hunk == i && (name == hunks.v[i].secname || !syms.v[j].val)) name = syms.v[j].name;
    return name;
}                                  /* DASHC_MAPA: quién trajo cada hunk */
static void reach(int *keep, int *stack, int sp, const int *weak)
{
    int j;
    while (sp) {
        int cur = stack[--sp];
        Hunk *h;
        relocs_ready(cur);
        h = &hunks.v[cur];
        for (j = 0; j < refs.n; j++)
            if (refs.v[j].hunk == cur) {
                bind(cur, refs.v[j].off, refs.v[j].name);
                refs.v[j].hunk = -1;               /* ya está */
            }
        if (weak[cur]) continue;
        for (j = 0; j < h->relocs.n; j++)
            if (!keep[h->relocs.v[j].target]) {
                keep[h->relocs.v[j].target] = 1;
                if (why) why[h->relocs.v[j].target] = cur;
                stack[sp++] = h->relocs.v[j].target;
            }
    }
}

/* la ventana y el RastPort de dibujo actuales: los usan casi todos los runtimes de ventanas y gráficos
   (que sus limpiezas los toquen no dice que el programa use esos runtimes) */
static int win_hunk = -2, rp_hunk = -2;
static int shared_data(int d)
{
    if (win_hunk == -2) {
        Sym *w = find_sym("__dash_win"), *r = find_sym("__dash_rp");
        win_hunk = w && !w->abs ? w->hunk : -1;
        rp_hunk = r && !r->abs ? r->hunk : -1;
    }
    return d == win_hunk || d == rp_hunk;
}

/* ¿usa el hunk t datos o BSS que van en el programa y no son del arranque? (sus reubicaciones y sus
   símbolos aún sin atar) */
static int touches_own_data(int t, const int *keep, const int *core)
{
    int j, d;
    Hunk *h;
    relocs_ready(t);
    h = &hunks.v[t];
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
                err_printf("limpieza %s por %s\n", a ? a : "?", b ? b : "?");
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

/* ---- el runtime preparado (dashc --preparar, al construir dashc) ----
   Leer el objeto Hunk del runtime (2.200 hunks), trocear sus textos y atar sus nombres costaba 5 s en cada
   compilación en un A1200: se hace una vez y se guarda así (en longs, big-endian):
     "DRT1", nhunks, nsyms, nrefs, nrelocs, tamaño de los nombres, tamaño de los datos
     por hunk: tipo, tamaño, align2, nombre de sección (o ~0), sitio de sus datos (o ~0 en BSS), 1.ª reubicación, cuántas
     reubicaciones: sitio, hunk
     símbolos: nombre, hunk (o ~0 si es absoluto), valor
     referencias sin atar (a lo que el runtime no tiene: las ata lo de @link, o es un error si se llega): hunk, sitio, nombre
     los nombres (terminados en 0) y los datos */

static uint32_t strtab_add(Buf *st, const char *s)
{
    static struct { const char **v; int n, cap; } seen;
    static struct { uint32_t *v; int n, cap; } at;
    uint32_t off;
    int i;
    if (!s) return ~0u;
    for (i = 0; i < seen.n; i++)
        if (!strcmp(seen.v[i], s)) return at.v[i];      /* (los repetidos, una vez) */
    off = (uint32_t)st->n;
    buf_bytes(st, s, strlen(s) + 1);
    VEC_PUSH(seen, s);
    VEC_PUSH(at, off);
    return off;
}

void prepare_runtime(const uint8_t *rt, size_t len, const char *out)
{
    Buf hb = {0}, rb = {0}, sb = {0}, fb = {0}, st = {0}, db = {0}, head = {0};
    int i, j, nrel = 0, nref = 0;
    FILE *f;
    read_object(rt, len);
    split_strings(0);
    for (j = 0; j < refs.n; j++)
        if (find_sym(refs.v[j].name)) {
            bind(refs.v[j].hunk, refs.v[j].off, refs.v[j].name);
            refs.v[j].hunk = -1;
        }
    for (i = 0; i < hunks.n; i++) {
        Hunk *h = &hunks.v[i];
        buf_long(&hb, (uint32_t)h->type);
        buf_long(&hb, h->size);
        buf_long(&hb, (uint32_t)h->align2 | h->memflags);
        {
            /* (el nombre de sección solo sirve para DASHC_MAPA: si un símbolo nombra el hunk, sobra) */
            int named = 0;
            for (j = 0; j < syms.n && !named; j++) named = syms.v[j].hunk == i && !syms.v[j].abs;
            buf_long(&hb, named ? ~0u : strtab_add(&st, h->secname));
        }
        if (h->data) {
            buf_long(&hb, (uint32_t)db.n);
            buf_bytes(&db, h->data, h->size);
        } else {
            buf_long(&hb, ~0u);
        }
        buf_long(&hb, (uint32_t)nrel);
        buf_long(&hb, (uint32_t)h->relocs.n);
        for (j = 0; j < h->relocs.n; j++) {
            buf_long(&rb, h->relocs.v[j].off);
            buf_long(&rb, (uint32_t)h->relocs.v[j].target);
        }
        nrel += h->relocs.n;
    }
    for (i = 0; i < syms.n; i++) {
        buf_long(&sb, strtab_add(&st, syms.v[i].name));
        buf_long(&sb, syms.v[i].abs ? ~0u : (uint32_t)syms.v[i].hunk);
        buf_long(&sb, syms.v[i].val);
    }
    for (j = 0; j < refs.n; j++)
        if (refs.v[j].hunk >= 0) {
            buf_long(&fb, (uint32_t)refs.v[j].hunk);
            buf_long(&fb, refs.v[j].off);
            buf_long(&fb, strtab_add(&st, refs.v[j].name));
            nref++;
        }
    while (st.n & 3) buf_byte(&st, 0);
    buf_long(&head, DRT_MAGIC);
    buf_long(&head, (uint32_t)hunks.n);
    buf_long(&head, (uint32_t)syms.n);
    buf_long(&head, (uint32_t)nref);
    buf_long(&head, (uint32_t)nrel);
    buf_long(&head, (uint32_t)st.n);
    buf_long(&head, (uint32_t)db.n);
    if (!(f = fopen(out, "wb"))) fatal("no se puede escribir %s", out);
    fwrite(head.p, 1, head.n, f);
    fwrite(hb.p, 1, hb.n, f);
    fwrite(rb.p, 1, rb.n, f);
    fwrite(sb.p, 1, sb.n, f);
    if (fb.n) fwrite(fb.p, 1, fb.n, f);
    fwrite(st.p, 1, st.n, f);
    fwrite(db.p, 1, db.n, f);
    if (fclose(f)) fatal("no se puede escribir %s", out);
}

/* carga el runtime preparado tras los hunks que ya hay; los datos se quedan en el blob hasta que se cambian */
static void load_prepared(const uint8_t *p, size_t len)
{
    uint32_t nh, ns, nr, nrel, stl, i;
    const uint8_t *hp, *rp0, *sp0, *fp, *strs, *data, *zl;
    int base = hunks.n;
    if (len < 28) fatal("runtime preparado cortado");
    nh = get_long(p + 4);
    ns = get_long(p + 8);
    nr = get_long(p + 12);
    nrel = get_long(p + 16);
    stl = get_long(p + 20);
    hp = p + 28;
    rp0 = hp + nh * 28;
    sp0 = rp0 + nrel * 8;
    fp = sp0 + ns * 12;
    zl = get_long(p) == DRT2_MAGIC ? fp + nr * 12 : NULL;    /* DRT2: el tamaño comprimido de cada hunk */
    strs = fp + nr * 12 + (zl ? nh * 4 : 0);
    data = strs + stl;
    if (data + get_long(p + 24) > p + len) fatal("runtime preparado cortado");
    /* (sitio para todos de una vez: sin copiar las listas cada vez que crecen) */
    if (hunks.cap < hunks.n + (int)nh) {
        hunks.cap = hunks.n + (int)nh + 8;
        hunks.v = xrealloc(hunks.v, sizeof(Hunk) * hunks.cap);
    }
    if (syms.cap < syms.n + (int)ns) {
        syms.cap = syms.n + (int)ns + 64;
        syms.v = xrealloc(syms.v, sizeof(Sym) * syms.cap);
    }
    for (i = 0; i < nh; i++, hp += 28) {
        Hunk h = {0};
        uint32_t flags = get_long(hp + 8), name = get_long(hp + 12), d = get_long(hp + 16);
        uint32_t r0 = get_long(hp + 20), rn = get_long(hp + 24);
        h.type = (int)get_long(hp);
        h.size = get_long(hp + 4);
        h.align2 = flags & 1;
        h.memflags = flags & 0xC0000000u;
        h.secname = name == ~0u ? NULL : (const char *)strs + name;
        if (d != ~0u && zl && get_long(zl + i * 4)) {
            h.zdata = data + d;
            h.zlen = get_long(zl + i * 4);
        } else if (d != ~0u) {
            h.data = (uint8_t *)(data + d);
            h.shared = 1;
        }
        if (rn) {
            /* (se leen solo las de los hunks que se miran: casi todos se quedan fuera) */
            h.lazy = rp0 + r0 * 8;
            h.lazy_n = (int)rn;
            h.lazy_base = base;
        }
        VEC_PUSH(hunks, h);
    }
    for (i = 0; i < ns; i++, sp0 += 12) {
        uint32_t hk = get_long(sp0 + 4);
        add_sym((const char *)strs + get_long(sp0), hk == ~0u ? -1 : base + (int)hk, get_long(sp0 + 8), hk == ~0u);
    }
    for (i = 0; i < nr; i++, fp += 12) {
        Ref r;
        r.hunk = base + (int)get_long(fp);
        r.off = get_long(fp + 4);
        r.name = (char *)strs + get_long(fp + 8);
        VEC_PUSH(refs, r);
    }
}

/* las reubicaciones del hunk i, leídas del runtime preparado si aún no lo estaban */
static void relocs_ready(int i)
{
    Hunk *h = &hunks.v[i];
    int j;
    if (!h->lazy) return;
    h->relocs.v = xmalloc(sizeof(HReloc) * h->lazy_n);
    h->relocs.n = h->relocs.cap = h->lazy_n;
    for (j = 0; j < h->lazy_n; j++) {
        h->relocs.v[j].off = get_long(h->lazy + j * 8);
        h->relocs.v[j].target = h->lazy_base + (int)get_long(h->lazy + j * 8 + 4);
    }
    h->lazy = NULL;
}

/* los datos del hunk i, propios (copiados del runtime preparado si hacía falta) para cambiarlos */
static uint8_t *own_data(int i)
{
    Hunk *h = &hunks.v[i];
    if (h->zdata) {
        /* DRT2: sus datos, descomprimidos ahora (deflate crudo) */
        z_stream z;
        memset(&z, 0, sizeof z);
        h->data = xmalloc(h->size);
        z.next_in = (Bytef *)h->zdata;
        z.avail_in = h->zlen;
        z.next_out = h->data;
        z.avail_out = h->size;
        if (inflateInit2(&z, -MAX_WBITS) != Z_OK || inflate(&z, Z_FINISH) != Z_STREAM_END || z.total_out != h->size)
            fatal("el runtime de dentro está estropeado");
        inflateEnd(&z);
        h->zdata = NULL;
        h->shared = 0;
    }
    if (h->shared) {
        uint8_t *d = xmalloc(h->size);
        memcpy(d, h->data, h->size);
        h->data = d;
        h->shared = 0;
    }
    return h->data;
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
    if (rtlen >= 4 && (get_long(rt) == DRT_MAGIC || get_long(rt) == DRT2_MAGIC)) {
        load_prepared(rt, rtlen);
    } else {
        read_object(rt, rtlen);
        if (!getenv("DASHC_SIN_TROCEAR")) split_strings(2);
    }
    tiempo("runtime");
    for (i = 0; i < link_files.n; i++) read_linked(link_files.v[i]);
    /* las funciones @export del programa, por su nombre de C (si ni el runtime ni lo de @link lo tienen ya) */
    for (i = 0; i < obj->exports.n; i++)
        if (!find_sym(obj->exports.v[i].name)) add_sym(obj->exports.v[i].name, HK_CODE, obj->exports.v[i].off, 0);
    /* un común que nadie define: un BSS suyo */
    for (i = 0; i < commons.n; i++)
        if (!find_sym(commons.v[i].name)) {
            Hunk h = {0};
            h.type = HUNK_BSS;
            h.size = (commons.v[i].size + 3) & ~3u;
            h.secname = commons.v[i].name;
            VEC_PUSH(hunks, h);
            add_sym(commons.v[i].name, hunks.n - 1, 0, 0);
        }

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
    if (getenv("DASHC_MAPA")) {
        why = xmalloc(sizeof(int) * hunks.n);
        for (i = 0; i < hunks.n; i++) why[i] = -1;
    }
    keep[0] = keep[1] = 1;
    stack[sp++] = 0;
    stack[sp++] = 1;
    reach(keep, stack, sp, weak);
    tiempo("alcanzar");

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

    if (missing.n) {
        err_printf("dash: Error: nadie define (ni el runtime ni lo de @link):");
        for (i = 0; i < missing.n; i++) err_printf(" %s", missing.v[i][0] == '_' ? missing.v[i] + 1 : missing.v[i]);
        err_printf("\n");
        exit(1);
    }

    /* un puntero débil a algo que no va: 0, sin reubicación */
    for (i = 0; i < hunks.n; i++)
        if (keep[i] && weak[i]) {
            Hunk *h;
            relocs_ready(i);
            h = &hunks.v[i];
            for (j = 0; j < h->relocs.n; j++)
                if (!keep[h->relocs.v[j].target]) {
                    put_long(own_data(i) + h->relocs.v[j].off, 0);
                    h->relocs.v[j--] = h->relocs.v[--h->relocs.n];
                }
        }

    tiempo("limpiezas");
    /* dónde va cada uno en el hunk de su tipo (0 código, 1 datos, 2 BSS) */
    base = xmalloc(sizeof(uint32_t) * hunks.n);
    outh = xmalloc(sizeof(int) * hunks.n);
    for (i = 0; i < hunks.n; i++) {
        Hunk *h = &hunks.v[i];
        if (!keep[i]) continue;
        if (h->memflags) fatal("%s: un hunk con memoria chip o fast aún no se admite", h->secname ? h->secname : "?");
        outh[i] = h->type == HUNK_CODE ? 0 : h->type == HUNK_DATA ? 1 : 2;
        base[i] = outsize[outh[i]];
        outsize[outh[i]] += h->align2 ? (h->size + 1) & ~1u : (h->size + 3) & ~3u;
    }
    for (k = 0; k < 3; k++) outsize[k] = (outsize[k] + 3) & ~3u;
    /* las reubicaciones, a su sitio en los hunks juntados */
    for (i = 0; i < hunks.n; i++) {
        Hunk *h;
        if (!keep[i]) continue;
        relocs_ready(i);
        h = &hunks.v[i];
        for (j = 0; j < h->relocs.n; j++) {
            HReloc r;
            int t = h->relocs.v[j].target;
            uint8_t *p = own_data(i) + h->relocs.v[j].off;
            put_long(p, get_long(p) + base[t]);
            r.off = base[i] + h->relocs.v[j].off;
            r.target = outh[t];
            VEC_PUSH(outrel[outh[i]], r);
        }
    }
    nout = outsize[2] ? 3 : 2;
    if (why)
        /* el tamaño, el tipo, el nombre y quién lo trajo (el programa, otro hunk o, si nada, una limpieza) */
        for (i = 2; i < hunks.n; i++)
            if (keep[i]) {
                int by = why[i];
                err_printf("%6u %c %06x %s", (unsigned)hunks.v[i].size, "CDB"[hunks.v[i].type - HUNK_CODE],
                           (unsigned)base[i], hunk_name(i));
                err_printf(" <- %s\n", by < 0 ? "(limpieza)" : by < 2 ? "(programa)" : hunk_name(by));
            }

    if (debug_info.n) {
        /* --debug: dónde quedó _dash_quit (el depurador acaba el programa por ahí) */
        Sym *q = find_sym("__dash_quit");
        if (q && !q->abs && keep[q->hunk] && outh[q->hunk] == 0) {
            char line[40];
            snprintf(line, sizeof line, "Q %u\n", (unsigned)(base[q->hunk] + q->val));
            buf_bytes(&debug_info, line, strlen(line));
        }
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
                if (h->zdata) own_data(i);
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
        if (k == 0 && debug_info.n) {
            /* --debug: el texto para el depurador (gen68k.c, debug_text); LoadSeg no lo carga */
            static const uint8_t zero[4];
            uint32_t n = ((uint32_t)debug_info.n + 3) / 4;
            wl(f, HUNK_DEBUG);
            wl(f, n);
            fwrite(debug_info.p, 1, debug_info.n, f);
            fwrite(zero, 1, n * 4 - debug_info.n, f);
        }
        wl(f, HUNK_END);
    }
    if (fclose(f)) fatal("no se puede escribir %s", out);
}
