/* Generador de AArch64 de dashc (docs/AARCH64_LOOP.md, fase A4): lo que sabe de las instrucciones de
   ARM. Lo incluye gen68k.c (con -DDASH_A64) donde va t68k_base.c, con las mismas funciones.

   Las instrucciones van siempre en little-endian (así las lee la CPU); los datos, en little-endian (lo nativo de
   DashOS) o, con --be, en big-endian (bibliotecas de la caja Amiga). Registros: d0 = x0, d1 = x1, a0 = x9,
   a1 = x10, a2 = x28; las variables en x19-x27; x16 y x17 de paso. Un Int vive en 64 bits con el signo extendido
   (las operaciones se hacen en w y se extienden). */

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
static int global_off(int i) { return 16 + 8 * i; }   /* (ver data_start) */

/* ---- el código ---- */
static uint32_t x0_dirty = 0;   /* x0 cambió después de la última comparación: un Bcc tiene que compararlo antes */

/* Las tablas que el recorrido pone "en el código" (descriptores de tipos, ventanas, ficheros) van a los datos: llevan
   punteros que se reubican al cargar (PIE), y el código no se escribe nunca. Empiezan en code_align y acaban en la
   siguiente instrucción; sus etiquetas llevan DATA_LABEL. */
#define DATA_LABEL (1L << 40)
static int in_table = 0;
static void data_start(void);
/* Una etiqueta puesta con in_table es de la tabla o de lo que viene detrás (un destructor, la función siguiente):
   queda pendiente y la sitúa lo siguiente que se escriba, un dato (l) o una instrucción (ins) */
static struct { int *v; int n, cap; } pend_labels;
static struct { long *v; int n, cap; } labels;  /* posición en el código, -1 sin poner */
static void place_pending(long at)
{
    int i;
    for (i = 0; i < pend_labels.n; i++) labels.v[pend_labels.v[i]] = at;
    pend_labels.n = 0;
}

static void ins(uint32_t v)
{
    if (pend_labels.n) place_pending((long)obj->code.n);
    in_table = 0;
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

/* un LONG de los datos, en el orden de bytes del programa (little-endian; big-endian con --be) */
static void dlong(uint32_t v)
{
    if (elf_be) { buf_long(&obj->data, v); return; }
    buf_byte(&obj->data, (int)(v & 0xFF)); buf_byte(&obj->data, (int)(v >> 8 & 0xFF));
    buf_byte(&obj->data, (int)(v >> 16 & 0xFF)); buf_byte(&obj->data, (int)(v >> 24));
}

/* un dato de una tabla (descriptores) */
static void l(uint32_t v)
{
    if (!in_table) { buf_long(&obj->code, v); return; }
    if (pend_labels.n) place_pending((long)obj->data.n | DATA_LABEL);
    dlong(v);
}

static void a64_todo(const char *what)
{
    fatal("dashc para DashOS: aún no está %s", what);
}

/* ---- etiquetas y saltos ---- */
/* kind: 0 b, 1 b.cond, 2 bl, 3 adr (dirección de una etiqueta: reubicación al .text o al .data), 4 puntero de 64
   bits a una etiqueta (ABS64, en una tabla de los datos), 5 cbz/cbnz */
typedef struct { uint32_t at; int label; int kind; int in_data; } Fixup;
static struct { Fixup *v; int n, cap; } fixups;

static int new_label(void)
{
    VEC_PUSH(labels, -1);
    return labels.n - 1;
}

/* Las banderas, como en el 68000 (donde mover a d0 las pone): cada camino que llega a una etiqueta las deja puestas
   (si x0 cambió tras la última comparación, se compara con 0 antes de saltar o de seguir), y así en la etiqueta valen */
static void cmp_x0_zero(void);
static void def_label(int l)
{
    if (in_table) { VEC_PUSH(pend_labels, l); return; }
    if (x0_dirty) cmp_x0_zero();       /* (el camino que sigue de largo) */
    labels.v[l] = (long)obj->code.n;
    x0_dirty = 0;
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
    r.in_data = 0;
    VEC_PUSH(obj->relocs, r);
}

/* una reubicación en una tabla de los datos */
static void add_reloc_d(uint32_t off, int hunk, int type, long addend)
{
    add_reloc_t(off, hunk, NULL, type, addend);
    obj->relocs.v[obj->relocs.n - 1].in_data = 1;
}

static void fixup(int label, int kind)
{
    Fixup f;
    f.at = (uint32_t)(in_table ? obj->data.n : obj->code.n);
    f.label = label;
    f.kind = kind;
    f.in_data = in_table;
    VEC_PUSH(fixups, f);
}

static void cmp_x0_zero(void) { ins(0xF100001F); x0_dirty = 0; }   /* cmp x0, #0 */

/* Bcc etiqueta (CC_T = b). Si x0 cambió tras la última comparación, se compara con 0 (el 68000 lo hace al mover) */
static void branch(int cc, int label)
{
    if (cc == CC_F) return;
    if (cc == CC_T) {
        if (x0_dirty) cmp_x0_zero();
        fixup(label, 0);
        ins(0x14000000);                               /* b */
        x0_dirty = 0;                                  /* (después no se llega de largo) */
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

/* Float: el recorrido pide las funciones de libgcc del 68000 (___addsf3, ___cmpsf2...), con los bits del float en
   x0 y x1; en ARM son instrucciones de la FPU (DashOS guarda sus registros por hilo desde C28). El resultado, como
   un Int: 32 bits con el signo extendido. */
static int fpu_call(const char *sym)
{
    static const struct { const char *name; uint32_t op; } ops[] = {
        {"___addsf3", 0x1E212800}, {"___subsf3", 0x1E213800}, {"___mulsf3", 0x1E210800},   /* fadd/fsub/fmul */
        {"___divsf3", 0x1E211800},                                                          /* fdiv */
        {"___cmpsf2", 0}, {"___floatsisf", 1}, {"___fixsfsi", 2}};
    int i;
    for (i = 0; i < (int)(sizeof ops / sizeof ops[0]) && strcmp(sym, ops[i].name); i++) ;
    if (i == (int)(sizeof ops / sizeof ops[0])) return 0;
    if (ops[i].op == 1) {
        ins(0x1E220000);                               /* scvtf s0, w0 */
        ins(0x1E260000);                               /* fmov w0, s0 */
    } else if (ops[i].op == 2) {
        ins(0x1E270000);                               /* fmov s0, w0 */
        ins(0x1E380000);                               /* fcvtzs w0, s0 (hacia 0, como C) */
    } else {
        ins(0x1E270000);                               /* fmov s0, w0 */
        ins(0x1E270021);                               /* fmov s1, w1 */
        if (ops[i].op) {
            ins(ops[i].op);
            ins(0x1E260000);                           /* fmov w0, s0 */
        } else {
            /* -1, 0 o 1; con un NaN, 1 (como __cmpsf2) */
            ins(0x1E212000);                           /* fcmp s0, s1 */
            ins(0x1A9F07E0);                           /* cset w0, ne */
            ins(0x5A9F5000);                           /* csinv w0, w0, wzr, pl: -1 si es menor */
        }
    }
    ins(0x93407C00);                                   /* sxtw x0, w0 */
    x0_dirty = 1;
    return 1;
}

static void call_sym(const char *sym, int nargs)
{
    load_args(nargs);
    if (fpu_call(sym)) return;
    jsr_sym(sym);
}
static void call_label(int label, int nargs) { load_args(nargs); jsr_label(label); }

static void resolve_fixups(void)
{
    int i;
    if (pend_labels.n) place_pending((long)obj->code.n);   /* (detrás de la última tabla no hay nada) */
    for (i = 0; i < fixups.n; i++) {
        Fixup *f = &fixups.v[i];
        long target = labels.v[f->label], d;
        int sec = HK_CODE;
        uint32_t v;
        if (target < 0) fatal("etiqueta sin poner (fallo de dashc)");
        if (target & DATA_LABEL) { sec = HK_DATA; target &= ~DATA_LABEL; }
        if (f->kind != 3 && f->kind != 4 && (sec != HK_CODE || f->in_data)) fatal("salto a una tabla (fallo de dashc)");
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
        case 3:   /* adrp + add a una etiqueta: a su sección más la posición */
            add_reloc_t(f->at, sec, NULL, R_PG_HI21, target);
            add_reloc_t(f->at + 4, sec, NULL, R_ADD_LO12, target);
            break;
        case 4:
            if (f->in_data) add_reloc_d(f->at, sec, R_ABS64, target);
            else add_reloc_t(f->at, sec, NULL, R_ABS64, target);
            break;
        }
        (void)v;
    }
}

/* ---- los datos: 16 bytes a 0, las globales (8 bytes cada una), las ventanas, las tablas, los textos ----
   (los 16 primeros: el runtime mira la cabecera de un texto, 16 bytes antes, para saber si es de Dash; el primero de
   los datos no puede tener detrás el principio del segmento) */
static void data_start(void)
{
    if (!obj->data.n) { buf_long(&obj->data, 0); buf_long(&obj->data, 0); buf_long(&obj->data, 0); buf_long(&obj->data, 0); }
}

static long data_word(long v)                          /* una palabra (8 bytes) de los datos; devuelve dónde está */
{
    long off;
    data_start();
    while (obj->data.n & 7) buf_byte(&obj->data, 0);
    off = (long)obj->data.n;
    if (elf_be) { dlong((uint32_t)((unsigned long)v >> 32)); dlong((uint32_t)v); }
    else { dlong((uint32_t)v); dlong((uint32_t)((unsigned long)v >> 32)); }
    return off;
}

static uint32_t data_align(void)
{
    data_start();
    while (obj->data.n & 7) buf_byte(&obj->data, 0);
    return (uint32_t)obj->data.n;
}

static void data_elem(long v) { data_word(v); }        /* un elemento de lista: un _DashP */
