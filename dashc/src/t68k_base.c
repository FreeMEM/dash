/* Generador de 68000 de dashc (docs/AARCH64_LOOP.md, fase A3): lo que sabe de las instrucciones del 68000. Lo
   incluye gen68k.c donde iba (un solo fichero de C: comparte sus estáticos). */
/* una función sin variables en el marco puede no hacer link (lee sus parámetros con sp) */
#define CAN_FRAMELESS 1

/* los registros para variables: d2-d7 (d0 y d1 son de trabajo) */
#define FIRST_REG 2
#define MAX_REGS 6

/* ---- los datos: las globales (una palabra larga cada una, desde el principio), las ventanas, las tablas ---- */
static int global_off(int i) { return 4 * i; }

static long data_word(long v)                          /* una palabra de los datos; devuelve dónde está */
{
    long off = (long)obj->data.n;
    buf_long(&obj->data, (uint32_t)v);
    return off;
}

static uint32_t data_align(void)                       /* alineado para una tabla de elementos de lista */
{
    if (obj->data.n & 3) buf_word(&obj->data, 0);
    return (uint32_t)obj->data.n;
}

static void data_elem(long v) { buf_long(&obj->data, (uint32_t)v); }   /* un elemento de una lista de los datos */

/* el hueco n de las variables del marco, desde a5 */
static int frame_off(int n) { return -4 * n; }

/* códigos de condición del 68000 */
enum { CC_T = 0, CC_F, CC_HI, CC_LS, CC_CC, CC_CS, CC_NE, CC_EQ, CC_VC, CC_VS,
       CC_PL, CC_MI, CC_GE, CC_LT, CC_GT, CC_LE };

/* ---- etiquetas y saltos ---- */
static struct { long *v; int n, cap; } labels;  /* posición en el código, -1 sin poner */
/* at: dónde va el desplazamiento (o la dirección, si abs); size: 2 = Bcc.w, 1 = Bcc.s
   (at ya es la instrucción siguiente), 0 = quitado */
typedef struct { uint32_t at; int label : 29; unsigned abs : 1, size : 2; } Fixup;   /* (8 bytes: hay decenas de miles) */
static struct { Fixup *v; int n, cap; } fixups;

/* Las etiquetas por su posición (lpos) y cuántos saltos van a cada una (lab_refs): def_label_at miraba en cada
   etiqueta todas las del programa, y todos los saltos (en un programa grande, millones de vueltas en un A1200).
   Cada posición puesta lleva su lista de etiquetas (lab_next/lab_prev); todo cambio de labels.v pasa por label_put
   mientras se genera (cut_code e insert_code, al final, las cambian aparte: lpos_ok = 0 y se rehace si hace falta). */
static struct { long *key; int *head; int cap, used; } lpos;
static struct { int *next, *prev, *refs; int cap; } lab_x;
static int lpos_ok = 1;

static int lpos_slot(long pos, int add)            /* el hueco de pos en la tabla (-1 si no está y no se añade) */
{
    unsigned h;
    if (add && (lpos.used + 1) * 4 > lpos.cap * 3) {   /* (hasta 3/4 llena: decenas de miles de posiciones) */
        /* más grande: se rehace con las posiciones que tienen alguna etiqueta */
        long *ok = lpos.key;
        int *oh = lpos.head, oc = lpos.cap, i;
        lpos.cap = lpos.cap ? lpos.cap * 2 : 1024;
        lpos.key = xmalloc(sizeof(long) * lpos.cap);
        lpos.head = xmalloc(sizeof(int) * lpos.cap);
        for (i = 0; i < lpos.cap; i++) lpos.key[i] = -1;
        lpos.used = 0;
        for (i = 0; i < oc; i++)
            if (ok[i] >= 0 && oh[i] >= 0) {
                int k = lpos_slot(ok[i], 1);
                lpos.head[k] = oh[i];
            }
        xfree(ok);
        xfree(oh);
    }
    if (!lpos.cap) return -1;
    h = ((unsigned)pos >> 1 ^ (unsigned)pos >> 9) & (unsigned)(lpos.cap - 1);   /* (sin multiplicar) */
    while (lpos.key[h] >= 0) {
        if (lpos.key[h] == pos) return (int)h;
        h = (h + 1) & (unsigned)(lpos.cap - 1);
    }
    if (!add) return -1;
    lpos.key[h] = pos;
    lpos.head[h] = -1;
    lpos.used++;
    return (int)h;
}

static void lpos_unlink(int l)
{
    if (labels.v[l] < 0) return;
    if (lab_x.prev[l] >= 0) lab_x.next[lab_x.prev[l]] = lab_x.next[l];
    else {
        int k = lpos_slot(labels.v[l], 0);
        if (k >= 0) lpos.head[k] = lab_x.next[l];  /* (no está si lpos_trim la dejó fuera: nadie la busca ya) */
    }
    if (lab_x.next[l] >= 0) lab_x.prev[lab_x.next[l]] = lab_x.prev[l];
}

static void lpos_link(int l)
{
    int k;
    if (labels.v[l] < 0) return;
    k = lpos_slot(labels.v[l], 1);
    lab_x.prev[l] = -1;
    lab_x.next[l] = lpos.head[k];
    if (lab_x.next[l] >= 0) lab_x.prev[lab_x.next[l]] = l;
    lpos.head[k] = l;
}

static void lpos_rebuild(void)
{
    int i;
    for (i = 0; i < lpos.cap; i++) lpos.key[i] = -1;
    lpos.used = 0;
    for (i = 0; i < labels.n; i++) lpos_link(i);
    lpos_ok = 1;
}

static void label_put(int l, long v)               /* labels.v[l] = v */
{
    if (!lpos_ok) {
        labels.v[l] = v;
        return;
    }
    lpos_unlink(l);
    labels.v[l] = v;
    lpos_link(l);
}

static int lpos_first(long pos)                    /* la primera etiqueta en pos, o -1 */
{
    int k;
    if (!lpos_ok) lpos_rebuild();
    k = lpos_slot(pos, 0);
    return k < 0 ? -1 : lpos.head[k];
}

/* Al empezar una función (gen_one): mientras se genera solo se buscan etiquetas junto al final del código (lo que
   miran def_label_at y take_move_to_d0: n - 4, n + 4...). La tabla se rehace solo con las que están cerca del final
   (desde from): con un programa grande tenía decenas de miles de posiciones. Al acabar, cut_code e insert_code la
   rehacen entera (lpos_ok = 0). */
static void lpos_trim(long from)
{
    int keep[256], nk = 0, i, l;
    long pos;
    if (!lpos_ok || lpos.used < 2048) return;
    for (pos = from < 0 ? 0 : from; pos <= (long)obj->code.n + 8; pos++)
        for (l = lpos_first(pos); l >= 0 && nk < 256; l = lab_x.next[l]) keep[nk++] = l;
    if (nk == 256) return;                             /* (no pasa: muchas a la vez; mejor no tocar nada) */
    xfree(lpos.key);
    xfree(lpos.head);
    memset(&lpos, 0, sizeof lpos);
    for (i = nk - 1; i >= 0; i--) lpos_link(keep[i]);   /* (al revés: lpos_link pone delante; así, en su orden) */
}

static void lpos_move(long from, long to)          /* las etiquetas de from, a to */
{
    int l;
    while ((l = lpos_first(from)) >= 0) label_put(l, to);
}

static int new_label(void)
{
    VEC_PUSH(labels, -1);
    if (labels.n > lab_x.cap) {
        lab_x.cap = labels.cap;
        lab_x.next = xrealloc(lab_x.next, sizeof(int) * lab_x.cap);
        lab_x.prev = xrealloc(lab_x.prev, sizeof(int) * lab_x.cap);
        lab_x.refs = xrealloc(lab_x.refs, sizeof(int) * lab_x.cap);
    }
    lab_x.refs[labels.n - 1] = 0;
    return labels.n - 1;
}

/* un salto más (fixups) a su etiqueta */
#define FIXUP_PUSH(f) do { lab_x.refs[(f).label]++; VEC_PUSH(fixups, f); } while (0)

/* undo (gen68k.c): las etiquetas y los saltos de después de una marca se van */
static void labels_undo(int labels_n, int fixups_n)
{
    int i;
    for (i = fixups_n; i < fixups.n; i++) lab_x.refs[fixups.v[i].label]--;
    if (lpos_ok)
        for (i = labels_n; i < labels.n; i++) lpos_unlink(i);
}

static uint32_t last_branch = (uint32_t)-1;   /* dónde empieza el último Bcc.w */
static uint32_t dead_at = (uint32_t)-1;       /* después de un bra: hasta la próxima etiqueta no se llega */
static uint32_t d0_loaded = (uint32_t)-1;     /* dónde acaba el último move/moveq a d0 */
static uint32_t d0_stored = (uint32_t)-1;     /* dónde acaba el último move.l d0,dN (store_d0) */
static int d0_stored_reg;
/* Los códigos de condición dicen cómo es dN (flags_reg) comparado con 0 si la última
   instrucción, que acaba en flags_at, lo cambió: para todo si flags_full (V = 0) o
   solo para == y != (una suma puede poner V) */
static uint32_t flags_at = (uint32_t)-1;
static int flags_reg, flags_full;

static void def_label_at(int l, int keep);
static void def_label(int l) { def_label_at(l, 0); }

/* una etiqueta a la que no se salta hacia atrás: si aún no se ha saltado a ella, solo
   se llega desde la instrucción de antes y d0 y los códigos de condición siguen valiendo */
static void def_label_fwd(int l) { def_label_at(l, 1); }

static void def_label_at(int l, int keep)
{
    /* un salto a la instrucción de justo después sobra */
    if (last_branch + 4 == obj->code.n && fixups.n && fixups.v[fixups.n - 1].label == l &&
        fixups.v[fixups.n - 1].at == last_branch + 2 && !fixups.v[fixups.n - 1].abs) {
        obj->code.n -= 4;
        lab_x.refs[fixups.v[fixups.n - 1].label]--;
        fixups.n--;
        lpos_move((long)obj->code.n + 4, (long)obj->code.n);
        last_branch = (uint32_t)-1;
    }
    /* bcc l; bra m; l: es b(no cc) m */
    if (fixups.n >= 2) {
        Fixup *a = &fixups.v[fixups.n - 2], *b = &fixups.v[fixups.n - 1];
        uint32_t n = (uint32_t)obj->code.n;
        if (!a->abs && !b->abs && a->label == l && a->at + 6 == n && b->at + 2 == n) {
            uint8_t *pa = obj->code.p + a->at - 2, *pb = obj->code.p + b->at - 2;
            int opa = pa[0] << 8 | pa[1], opb = pb[0] << 8 | pb[1], at_bra = lpos_first((long)n - 4) >= 0;
            if (opb == 0x6000 && (opa & 0xF0FF) == 0x6000 && (opa & 0x0F00) >= 0x0200 && !at_bra) {
                put_word(pa, opa ^ 0x0100);
                lab_x.refs[a->label]--;
                a->label = b->label;
                obj->code.n -= 4;
                fixups.n--;
                last_branch = a->at - 2;
            }
        }
    }
    label_put(l, (long)obj->code.n);
    dead_at = (uint32_t)-1;
    if (keep && lab_x.refs[l]) keep = 0;
    if (!keep) {
        d0_loaded = (uint32_t)-1;                      /* se puede llegar de otro sitio */
        d0_stored = (uint32_t)-1;
        flags_at = (uint32_t)-1;
    }
}

static void w(int v) { buf_word(&obj->code, v); }

static void flags_set(int reg, int full)
{
    flags_at = (uint32_t)obj->code.n;
    flags_reg = reg;
    flags_full = full;
}
static void l(uint32_t v) { buf_long(&obj->code, v); }


/* Las reubicaciones, como el código (buf_spill): entre función y función, las ya hechas salen aparte (rel_spill) y
   la lista no crece copiándolas todas; rel_flatten las junta al acabar. obj->relocs.v está corrido rel_base
   elementos (vale desde rel_base) y cap cuenta desde 0 */
static int rel_base;
static struct RelSeg { struct RelSeg *next; int n; } *rel_segs, *rel_segs_end;   /* (y detrás, sus n Reloc) */

static void add_reloc(uint32_t off, int hunk, const char *sym)
{
    Reloc r;
    r.off = off;
    r.hunk = hunk;
    r.sym = sym;
    if (obj->relocs.n == obj->relocs.cap) {
        int have = obj->relocs.cap - rel_base, nc = have ? have + (have < 4096 ? have : have / 2) : 8;
        Reloc *real = obj->relocs.v ? obj->relocs.v + rel_base : NULL;
        real = xrealloc(real, sizeof(Reloc) * (size_t)nc);
        obj->relocs.v = real - rel_base;
        obj->relocs.cap = rel_base + nc;
    }
    obj->relocs.v[obj->relocs.n++] = r;
}

static void rel_spill(void)
{
    int k = obj->relocs.n - rel_base;
    struct RelSeg *s;
    if (k < 2048) return;
    s = xmalloc(sizeof *s + sizeof(Reloc) * (size_t)k);
    s->n = k;
    memcpy(s + 1, obj->relocs.v + rel_base, sizeof(Reloc) * (size_t)k);
    if (rel_segs_end) rel_segs_end->next = s;
    else rel_segs = s;
    rel_segs_end = s;
    obj->relocs.v -= k;                            /* (el mismo sitio de memoria, con base k más allá) */
    obj->relocs.cap += k;
    rel_base += k;
}

static void rel_flatten(void)
{
    Reloc *all, *d;
    struct RelSeg *s;
    if (!rel_segs) return;
    all = d = xmalloc(sizeof(Reloc) * (size_t)(obj->relocs.n + 1));
    for (s = rel_segs; s; s = s->next) {
        memcpy(d, s + 1, sizeof(Reloc) * (size_t)s->n);
        d += s->n;
    }
    memcpy(d, obj->relocs.v + rel_base, sizeof(Reloc) * (size_t)(obj->relocs.n - rel_base));
    while (rel_segs) {
        s = rel_segs;
        rel_segs = s->next;
        xfree(s);
    }
    rel_segs_end = NULL;
    xfree(obj->relocs.v + rel_base);
    obj->relocs.v = all;
    obj->relocs.cap = obj->relocs.n + 1;
    rel_base = 0;
}

/* Bcc.w etiqueta (CC_T = bra) */
static void branch(int cc, int label)
{
    Fixup f;
    if (dead_at == obj->code.n) return;               /* justo detrás de otro bra: no se llega */
    last_branch = (uint32_t)obj->code.n;
    w(0x6000 | cc << 8);
    f.at = (uint32_t)obj->code.n;
    f.label = label;
    f.abs = 0;
    f.size = 2;
    FIXUP_PUSH(f);
    w(0);
    if (cc == CC_T) dead_at = (uint32_t)obj->code.n;
}

/* jsr a una etiqueta del código (dirección absoluta reubicada) */
static void jsr_label(int label)
{
    Fixup f;
    w(0x4EB9);
    f.at = (uint32_t)obj->code.n;
    f.label = label;
    f.abs = 1;
    f.size = 2;
    FIXUP_PUSH(f);
    add_reloc(f.at, HK_CODE, NULL);
    l(0);
}


/* las llamadas, con cuántos argumentos dejó el recorrido en la pila (el 68000 los deja allí: no hace falta) */
static void jsr_sym(const char *sym);
static void call_sym(const char *sym, int nargs) { (void)nargs; jsr_sym(sym); }
static void call_label(int label, int nargs) { (void)nargs; jsr_label(label); }

/* jsr a una función del runtime */
static void jsr_sym(const char *sym)
{
    w(0x4EB9);
    add_reloc((uint32_t)obj->code.n, -1, sym);
    l(0);
}

/* quita n bytes del código en pos y mueve lo que haya detrás */
static void cut_code(uint32_t pos, int n)
{
    int i;
    lpos_ok = 0;
    memmove(obj->code.p + pos, obj->code.p + pos + n, obj->code.n - pos - n);
    obj->code.n -= n;
    for (i = 0; i < labels.n; i++)
        if (labels.v[i] > (long)pos) labels.v[i] -= n;
    for (i = 0; i < fixups.n; i++)
        if (fixups.v[i].at > pos) fixups.v[i].at -= n;
    for (i = 0; i < obj->relocs.n; i++)
        if (obj->relocs.v[i].off > pos) obj->relocs.v[i].off -= n;
}

/* Como el ensamblador: un Bcc.w que llega con 8 bits pasa a Bcc.s (2 bytes menos, y
   sin tomar el salto cuesta 8 ciclos en vez de 12). Encoger solo acerca los destinos,
   así que se repite hasta que no cambia nada. Un salto que acaba yendo a la instrucción
   siguiente se quita (en Bcc.s un desplazamiento 0 significaría Bcc.w).
   relax_one: una vuelta, quitando cada trozo en el momento (cut_code mueve todo lo de detrás: con un programa grande,
   miles de veces el código entero); es la que vale si los saltos no están en orden. relax_branches hace lo mismo
   apuntando los trozos que se quitan y quitándolos todos juntos al acabar la vuelta: una posición de antes de la
   vuelta x está ahora en x menos lo quitado antes de x (cut_before). */
static int relax_one(void)
{
    int changed = 0, i;
    for (i = 0; i < fixups.n; i++) {
        Fixup *f = &fixups.v[i];
        uint8_t *p;
        long target, d;
        if (f->abs || !f->size) continue;
        p = obj->code.p + f->at - 2;
        if ((p[0] & 0xF0) != 0x60 || p[0] == 0x61) continue;   /* Bcc y bra; no dbra */
        target = labels.v[f->label];
        if (target < 0) continue;
        d = target - (long)f->at;
        if (f->size == 2) {
            if (target > (long)f->at) d -= 2;      /* sin la extensión, el destino se acerca */
            if (d < -128 || d > 127) continue;
            if (d == 0) {
                f->size = 0;
                cut_code(f->at - 2, 4);
            } else {
                p[1] = (uint8_t)(d & 0xFF);
                f->size = 1;
                cut_code(f->at, 2);
            }
            changed = 1;
        } else if (d == 0) {
            f->size = 0;
            cut_code(f->at - 2, 2);
            changed = 1;
        }
    }
    return changed;
}

/* los trozos quitados en esta vuelta (en posiciones de antes de la vuelta, en orden) y lo quitado hasta cada uno */
static struct { uint32_t *pos; long *sum; int n, cap; } cuts;

static long cut_before(long x)                         /* lo quitado antes de x (trozos en pos < x) */
{
    int lo = 0, hi = cuts.n;
    while (lo < hi) {
        int mid = (lo + hi) / 2;
        if ((long)cuts.pos[mid] < x) lo = mid + 1;
        else hi = mid;
    }
    return lo ? cuts.sum[lo - 1] : 0;
}

static void cut_note(uint32_t pos, int n)
{
    if (cuts.n == cuts.cap) {
        cuts.cap = cuts.cap ? cuts.cap * 2 : 256;
        cuts.pos = xrealloc(cuts.pos, sizeof(uint32_t) * cuts.cap);
        cuts.sum = xrealloc(cuts.sum, sizeof(long) * cuts.cap);
    }
    cuts.pos[cuts.n] = pos;
    cuts.sum[cuts.n] = (cuts.n ? cuts.sum[cuts.n - 1] : 0) + n;
    cuts.n++;
}

/* al acabar de generar (gen_program): las etiquetas y los saltos ya no hacen falta; su memoria, para enlazar */
static void labels_free(void)
{
    xfree(fixups.v);
    xfree(labels.v);
    xfree(lab_x.next);
    xfree(lab_x.prev);
    xfree(lab_x.refs);
    xfree(lpos.key);
    xfree(lpos.head);
    xfree(cuts.pos);
    xfree(cuts.sum);
    memset(&fixups, 0, sizeof fixups);
    memset(&labels, 0, sizeof labels);
    memset(&lab_x, 0, sizeof lab_x);
    memset(&lpos, 0, sizeof lpos);
    memset(&cuts, 0, sizeof cuts);
}

static void relax_branches(void)
{
    int changed = 1, i;
    for (i = 1; i < fixups.n; i++)
        if (fixups.v[i].at <= fixups.v[i - 1].at) break;
    if (i < fixups.n) {                                /* (no están en orden: de uno en uno) */
        while (relax_one()) ;
        return;
    }
    while (changed) {
        long total;
        changed = 0;
        cuts.n = 0;
        for (i = 0; i < fixups.n; i++) {
            Fixup *f = &fixups.v[i];
            uint8_t *p;
            long target, d, at;
            if (f->abs || !f->size) continue;
            p = obj->code.p + f->at - 2;               /* (el código aún sin mover en esta vuelta) */
            if ((p[0] & 0xF0) != 0x60 || p[0] == 0x61) continue;   /* Bcc y bra; no dbra */
            target = labels.v[f->label];
            if (target < 0) continue;
            target -= cut_before(target);
            at = (long)f->at - (cuts.n ? cuts.sum[cuts.n - 1] : 0);   /* (todo lo quitado está antes) */
            d = target - at;
            if (f->size == 2) {
                if (target > at) d -= 2;               /* sin la extensión, el destino se acerca */
                if (d < -128 || d > 127) continue;
                if (d == 0) {
                    f->size = 0;
                    cut_note(f->at - 2, 4);
                } else {
                    p[1] = (uint8_t)(d & 0xFF);
                    f->size = 1;
                    cut_note(f->at, 2);
                }
                changed = 1;
            } else if (d == 0) {
                f->size = 0;
                cut_note(f->at - 2, 2);
                changed = 1;
            }
        }
        if (!cuts.n) break;
        lpos_ok = 0;
        /* el código sin los trozos, y cada posición a su sitio */
        {
            uint32_t from = 0, to = 0;
            int k;
            for (k = 0; k <= cuts.n; k++) {
                uint32_t end = k < cuts.n ? cuts.pos[k] : (uint32_t)obj->code.n;
                if (to != from) memmove(obj->code.p + to, obj->code.p + from, end - from);
                to += end - from;
                if (k < cuts.n) from = end + (uint32_t)(cuts.sum[k] - (k ? cuts.sum[k - 1] : 0));
            }
            total = cuts.sum[cuts.n - 1];
            obj->code.n -= total;
        }
        for (i = 0; i < labels.n; i++)
            if (labels.v[i] > 0) labels.v[i] -= cut_before(labels.v[i]);
        for (i = 0; i < fixups.n; i++) fixups.v[i].at -= (uint32_t)cut_before(fixups.v[i].at);
        for (i = 0; i < obj->relocs.n; i++) obj->relocs.v[i].off -= (uint32_t)cut_before(obj->relocs.v[i].off);
    }
}

/* mete n bytes a 0 en pos (lo de pos en adelante se mueve: etiquetas, saltos y reubicaciones) */
static void insert_code(uint32_t pos, int n)
{
    int i;
    lpos_ok = 0;
    for (i = 0; i < n; i++) buf_byte(&obj->code, 0);
    memmove(obj->code.p + pos + n, obj->code.p + pos, obj->code.n - pos - n);
    memset(obj->code.p + pos, 0, n);
    for (i = 0; i < labels.n; i++)
        if (labels.v[i] >= (long)pos) labels.v[i] += n;
    for (i = 0; i < fixups.n; i++)
        if (fixups.v[i].at >= pos) fixups.v[i].at += n;
    for (i = 0; i < obj->relocs.n; i++)
        if (obj->relocs.v[i].off >= pos) obj->relocs.v[i].off += n;
}

/* Lo contrario de relax_branches, para lo que no llega (una función de más de 32 KB, Main con mucho copiado en
   línea): un Bcc.s que se quedó lejos pasa a .w, y un .w que no llega a 32 KB, a un jmp absoluto reubicado (bra:
   jmp; Bcc: la condición contraria .s por encima de un jmp; dbra: por encima de un bra.s y un jmp). Crecer aleja
   destinos, así que se repite hasta que todo llega. */
static void grow_branches(void)
{
    int changed = 1, i;
    while (changed) {
        changed = 0;
        for (i = 0; i < fixups.n; i++) {
            Fixup *f = &fixups.v[i];
            uint8_t *p;
            long target, d;
            uint32_t at = f->at;
            if (f->abs || !f->size) continue;
            target = labels.v[f->label];
            if (target < 0) continue;
            d = target - (long)at;
            p = obj->code.p + at - 2;
            if (f->size == 1) {
                if (d >= -128 && d <= 127) continue;
                p[1] = 0;                                  /* Bcc.s -> Bcc.w */
                insert_code(at, 2);
                f = &fixups.v[i];
                f->at = at;              /* (insert_code movió también este salto: su desplazamiento va justo aquí) */
                f->size = 2;
                changed = 1;
                continue;
            }
            if (d >= -32768 && d <= 32767) continue;
            if (p[0] == 0x60) {                            /* bra.w -> jmp abs.l */
                insert_code(at + 2, 2);
                p = obj->code.p + at - 2;
                p[0] = 0x4E; p[1] = 0xF9;
            } else if ((p[0] & 0xF0) == 0x60) {            /* Bcc.w -> B!cc.s +6; jmp abs.l */
                insert_code(at + 2, 4);
                p = obj->code.p + at - 2;
                p[0] = (uint8_t)(p[0] ^ 1);
                p[1] = 6;
                p[2] = 0x4E; p[3] = 0xF9;
                f->at = at += 2;
            } else {                                       /* dbra dn,+4; bra.s +6; jmp abs.l */
                insert_code(at + 2, 8);
                p = obj->code.p + at;
                p[0] = 0; p[1] = 4;
                p[2] = 0x60; p[3] = 6;
                p[4] = 0x4E; p[5] = 0xF9;
                f->at = at += 6;
            }
            f->abs = 1;
            add_reloc(f->at, HK_CODE, NULL);
            changed = 1;
        }
    }
}

static void resolve_fixups(void)
{
    int i;
    relax_branches();
    grow_branches();
    for (i = 0; i < fixups.n; i++) {
        Fixup *f = &fixups.v[i];
        long target = labels.v[f->label];
        if (!f->size) continue;
        if (target < 0) fatal("etiqueta sin poner (fallo de dashc)");
        if (f->abs) {
            put_long(obj->code.p + f->at, (uint32_t)target);
        } else if (f->size == 1) {
            obj->code.p[f->at - 1] = (uint8_t)((target - (long)f->at) & 0xFF);
        } else {
            long d = target - (long)f->at;
            if (d < -32768 || d > 32767) fatal("salto de más de 32 KB (fallo de dashc: grow_branches)");
            put_word(obj->code.p + f->at, (int)d);
        }
    }
}
