/* Generador de 68000 de dashc (docs/AARCH64_LOOP.md, fase A3): lo que sabe de las instrucciones del 68000. Lo
   incluye gen68k.c donde iba (un solo fichero de C: comparte sus estáticos). */
/* códigos de condición del 68000 */
enum { CC_T = 0, CC_F, CC_HI, CC_LS, CC_CC, CC_CS, CC_NE, CC_EQ, CC_VC, CC_VS,
       CC_PL, CC_MI, CC_GE, CC_LT, CC_GT, CC_LE };

/* ---- etiquetas y saltos ---- */
static struct { long *v; int n, cap; } labels;  /* posición en el código, -1 sin poner */
/* at: dónde va el desplazamiento (o la dirección, si abs); size: 2 = Bcc.w, 1 = Bcc.s
   (at ya es la instrucción siguiente), 0 = quitado */
typedef struct { uint32_t at; int label; int abs; int size; } Fixup;
static struct { Fixup *v; int n, cap; } fixups;

static int new_label(void)
{
    VEC_PUSH(labels, -1);
    return labels.n - 1;
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
        int i;
        obj->code.n -= 4;
        fixups.n--;
        for (i = 0; i < labels.n; i++)
            if (labels.v[i] == (long)obj->code.n + 4) labels.v[i] = (long)obj->code.n;
        last_branch = (uint32_t)-1;
    }
    /* bcc l; bra m; l: es b(no cc) m */
    if (fixups.n >= 2) {
        Fixup *a = &fixups.v[fixups.n - 2], *b = &fixups.v[fixups.n - 1];
        uint32_t n = (uint32_t)obj->code.n;
        if (!a->abs && !b->abs && a->label == l && a->at + 6 == n && b->at + 2 == n) {
            uint8_t *pa = obj->code.p + a->at - 2, *pb = obj->code.p + b->at - 2;
            int opa = pa[0] << 8 | pa[1], opb = pb[0] << 8 | pb[1], i, at_bra = 0;
            for (i = 0; i < labels.n; i++)
                if (labels.v[i] == (long)n - 4) at_bra = 1;
            if (opb == 0x6000 && (opa & 0xF0FF) == 0x6000 && (opa & 0x0F00) >= 0x0200 && !at_bra) {
                put_word(pa, opa ^ 0x0100);
                a->label = b->label;
                obj->code.n -= 4;
                fixups.n--;
                last_branch = a->at - 2;
            }
        }
    }
    labels.v[l] = (long)obj->code.n;
    dead_at = (uint32_t)-1;
    if (keep) {
        int i;
        for (i = 0; i < fixups.n; i++)
            if (fixups.v[i].label == l) keep = 0;
    }
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


static void add_reloc(uint32_t off, int hunk, const char *sym)
{
    Reloc r;
    r.off = off;
    r.hunk = hunk;
    r.sym = sym;
    VEC_PUSH(obj->relocs, r);
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
    VEC_PUSH(fixups, f);
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
    VEC_PUSH(fixups, f);
    add_reloc(f.at, HK_CODE, NULL);
    l(0);
}


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
   siguiente se quita (en Bcc.s un desplazamiento 0 significaría Bcc.w). */
static void relax_branches(void)
{
    int changed = 1, i;
    while (changed) {
        changed = 0;
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
    }
}

/* mete n bytes a 0 en pos (lo de pos en adelante se mueve: etiquetas, saltos y reubicaciones) */
static void insert_code(uint32_t pos, int n)
{
    int i;
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
