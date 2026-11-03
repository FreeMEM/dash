/* Generador de AArch64 big-endian de dashc (docs/AARCH64_LOOP.md, fase A4): lo que sabe de las instrucciones de
   ARM. Lo incluye gen68k.c (con -DDASH_A64) donde va t68k_base.c, con las mismas funciones.

   Las instrucciones van siempre en little-endian (también en big-endian: así las lee la CPU); los datos, en
   big-endian. Registros: d0 = x0, d1 = x1, a0 = x9, a1 = x10, a2 = x28; las variables en x19-x27; x16 y x17 de
   paso. Un Int vive en 64 bits con el signo extendido (las operaciones se hacen en w y se extienden). */

/* reubicaciones de ELF que usa el generador */
enum { R_ABS64 = 257, R_PG_HI21 = 275, R_ADD_LO12 = 277, R_JUMP26 = 282, R_CALL26 = 283, R_LDST32_LO12 = 285,
       R_LDST64_LO12 = 286 };

#define SLOT 16              /* lo que ocupa cada cosa de la pila (sp siempre alineado a 16) */
#define CAN_FRAMELESS 0      /* siempre con marco: los parámetros llegan en registros y se guardan en él */
#define FIRST_REG 2          /* las variables en registros: 2..10 son x19..x27 */
#define MAX_REGS 9
#define XREG(r) ((r) < 2 ? (r) : 17 + (r))   /* d0 = x0, d1 = x1, el registro r de una variable = x(17 + r) */
#define XA0 9
#define XA1 10
#define XA2 28
#define XT 16                /* de paso */
#define XT2 17

/* los códigos de condición del recorrido (los del 68000) */
enum { CC_T = 0, CC_F, CC_HI, CC_LS, CC_CC, CC_CS, CC_NE, CC_EQ, CC_VC, CC_VS,
       CC_PL, CC_MI, CC_GE, CC_LT, CC_GT, CC_LE };
/* ... y los de ARM (después de cmp a, b: el acarreo de ARM es el contrario del préstamo del 68000) */
static const int arm_cc[16] = { 14, 15, 8, 9, 2, 3, 1, 0, 7, 6, 5, 4, 10, 11, 12, 13 };

static int frame_off(int n) { return -8 * n; }       /* (se corrige con los parámetros: ver param_off) */
static int global_off(int i) { return 8 * i; }

/* ---- el código ---- */
static uint32_t x0_dirty = 0;   /* x0 cambió después de la última comparación: un Bcc tiene que compararlo antes */

static void ins(uint32_t v)
{
    buf_byte(&obj->code, (int)(v & 0xFF));
    buf_byte(&obj->code, (int)(v >> 8 & 0xFF));
    buf_byte(&obj->code, (int)(v >> 16 & 0xFF));
    buf_byte(&obj->code, (int)(v >> 24));
}

static uint32_t ins_at(uint32_t at)
{
    uint8_t *p = obj->code.p + at;
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}

static void ins_put(uint32_t at, uint32_t v)
{
    uint8_t *p = obj->code.p + at;
    p[0] = (uint8_t)v; p[1] = (uint8_t)(v >> 8); p[2] = (uint8_t)(v >> 16); p[3] = (uint8_t)(v >> 24);
}

/* un dato dentro del código (descriptores): big-endian */
static void l(uint32_t v) { buf_long(&obj->code, v); }

static void a64_todo(const char *what)
{
    fatal("dashc para DashOS: aún no está %s", what);
}

/* ---- etiquetas y saltos ---- */
static struct { long *v; int n, cap; } labels;  /* posición en el código, -1 sin poner */
/* kind: 0 b, 1 b.cond, 2 bl, 3 adr (dirección de una etiqueta: reubicación al .text), 4 puntero de 64 bits a una
   etiqueta (ABS64 al .text), 5 cbz/cbnz */
typedef struct { uint32_t at; int label; int kind; } Fixup;
static struct { Fixup *v; int n, cap; } fixups;

static int new_label(void)
{
    VEC_PUSH(labels, -1);
    return labels.n - 1;
}

static void def_label(int l)
{
    labels.v[l] = (long)obj->code.n;
    x0_dirty = 1;                      /* se puede llegar de otro sitio: sin saber qué comparó */
}
static void def_label_fwd(int l) { def_label(l); }

static void flags_set(int reg, int full) { (void)reg; (void)full; }   /* (ARM no compara al mover) */

static void add_reloc_t(uint32_t off, int hunk, const char *sym, int type, long addend)
{
    Reloc r;
    r.off = off;
    r.hunk = hunk;
    r.sym = sym;
    r.type = type;
    r.addend = addend;
    VEC_PUSH(obj->relocs, r);
}

static void fixup(int label, int kind)
{
    Fixup f;
    f.at = (uint32_t)obj->code.n;
    f.label = label;
    f.kind = kind;
    VEC_PUSH(fixups, f);
}

static void cmp_x0_zero(void) { ins(0xF100001F); x0_dirty = 0; }   /* cmp x0, #0 */

/* Bcc etiqueta (CC_T = b). Si x0 cambió tras la última comparación, se compara con 0 (el 68000 lo hace al mover) */
static void branch(int cc, int label)
{
    if (cc == CC_F) return;
    if (cc == CC_T) {
        fixup(label, 0);
        ins(0x14000000);                               /* b */
        return;
    }
    if (x0_dirty) cmp_x0_zero();
    fixup(label, 1);
    ins(0x54000000 | arm_cc[cc]);                      /* b.cond */
}

/* ---- llamadas: los argumentos que dejó el recorrido en la pila (el 0, arriba) a x0..x7 ---- */
static void load_args(int nargs)
{
    int i;
    if (nargs > 8) a64_todo("una llamada con más de 8 argumentos");
    for (i = 0; i < nargs; i++)
        ins(0xF9400000 | (uint32_t)(i * 16 / 8) << 10 | 31 << 5 | (uint32_t)i);   /* ldr xi, [sp, #16i] */
}

static void jsr_label(int label)
{
    fixup(label, 2);
    ins(0x94000000);                                   /* bl */
    x0_dirty = 1;
}

/* el nombre de C: los del recorrido llevan un _ delante (el del 68000) */
static const char *c_name(const char *sym) { return sym[0] == '_' ? sym + 1 : sym; }

static void jsr_sym(const char *sym)
{
    add_reloc_t((uint32_t)obj->code.n, -1, c_name(sym), R_CALL26, 0);
    ins(0x94000000);                                   /* bl sym */
    x0_dirty = 1;
}

static void call_sym(const char *sym, int nargs) { load_args(nargs); jsr_sym(sym); }
static void call_label(int label, int nargs) { load_args(nargs); jsr_label(label); }

static void resolve_fixups(void)
{
    int i;
    for (i = 0; i < fixups.n; i++) {
        Fixup *f = &fixups.v[i];
        long target = labels.v[f->label], d;
        uint32_t v;
        if (target < 0) fatal("etiqueta sin poner (fallo de dashc)");
        d = (target - (long)f->at) / 4;
        switch (f->kind) {
        case 0: case 2:
            if (d < -(1L << 25) || d >= (1L << 25)) fatal("salto de más de 128 MB");
            ins_put(f->at, ins_at(f->at) | ((uint32_t)d & 0x3FFFFFF));
            break;
        case 1: case 5:
            if (d < -(1L << 18) || d >= (1L << 18)) fatal("salto condicional de más de 1 MB (aún no)");
            ins_put(f->at, ins_at(f->at) | ((uint32_t)d & 0x7FFFF) << 5);
            break;
        case 3:   /* adrp + add a una etiqueta del código: al .text más la posición */
            add_reloc_t(f->at, HK_CODE, NULL, R_PG_HI21, target);
            add_reloc_t(f->at + 4, HK_CODE, NULL, R_ADD_LO12, target);
            break;
        case 4:
            add_reloc_t(f->at, HK_CODE, NULL, R_ABS64, target);
            break;
        }
        (void)v;
    }
}

/* ---- los datos: las globales (8 bytes cada una, desde el principio), las ventanas, las tablas ---- */
static long data_word(long v)                          /* una palabra (8 bytes) de los datos; devuelve dónde está */
{
    long off;
    while (obj->data.n & 7) buf_byte(&obj->data, 0);
    off = (long)obj->data.n;
    buf_long(&obj->data, (uint32_t)((unsigned long)v >> 32));
    buf_long(&obj->data, (uint32_t)v);
    return off;
}

static uint32_t data_align(void)
{
    while (obj->data.n & 7) buf_byte(&obj->data, 0);
    return (uint32_t)obj->data.n;
}

static void data_elem(long v) { data_word(v); }        /* un elemento de lista: un _DashP */
