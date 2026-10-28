/* Generador de código 68000. Cada expresión deja su valor en d0; un operando que
   no es simple se guarda en la pila mientras se calcula el otro. Las funciones usan
   un marco con a5 (link/unlk): los parámetros en 8(a5), 12(a5)... y las variables
   en -4(a5), -8(a5)... Se llaman como en C (argumentos en la pila, de derecha a
   izquierda, resultado en d0), así que el runtime de gcc se llama igual.

   Cada función se genera dos veces: la primera cuenta cuánto se usa cada variable
   (lo de dentro de un bucle cuenta más) y la segunda pone las más usadas en d2-d7,
   que la función guarda al entrar y recupera al salir. */
#include <stdlib.h>
#include <string.h>

#include "dashc.h"

/* códigos de condición del 68000 */
enum { CC_T = 0, CC_F, CC_HI, CC_LS, CC_CC, CC_CS, CC_NE, CC_EQ, CC_VC, CC_VS,
       CC_PL, CC_MI, CC_GE, CC_LT, CC_GT, CC_LE };

#define MAX_REGS 6   /* d2-d7 */
#define MIN_USES 3   /* menos usos no pagan guardar y recuperar el registro */

static Program *prog;
static Obj *obj;

/* ---- etiquetas y saltos ---- */
static struct { long *v; int n, cap; } labels;  /* posición en el código, -1 sin poner */
typedef struct { uint32_t at; int label; int abs; } Fixup;
static struct { Fixup *v; int n, cap; } fixups;

static int new_label(void)
{
    VEC_PUSH(labels, -1);
    return labels.n - 1;
}

static uint32_t last_branch = (uint32_t)-1;   /* dónde empieza el último Bcc.w */
static uint32_t d0_loaded = (uint32_t)-1;     /* dónde acaba el último move/moveq a d0 */

static void def_label(int l)
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
    labels.v[l] = (long)obj->code.n;
    d0_loaded = (uint32_t)-1;                          /* se puede llegar de otro sitio */
}

static void w(int v) { buf_word(&obj->code, v); }
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
    last_branch = (uint32_t)obj->code.n;
    w(0x6000 | cc << 8);
    f.at = (uint32_t)obj->code.n;
    f.label = label;
    f.abs = 0;
    VEC_PUSH(fixups, f);
    w(0);
}

/* jsr a una etiqueta del código (dirección absoluta reubicada) */
static void jsr_label(int label)
{
    Fixup f;
    w(0x4EB9);
    f.at = (uint32_t)obj->code.n;
    f.label = label;
    f.abs = 1;
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

static void resolve_fixups(void)
{
    int i;
    for (i = 0; i < fixups.n; i++) {
        Fixup *f = &fixups.v[i];
        long target = labels.v[f->label];
        if (target < 0) fatal("etiqueta sin poner (fallo de dashc)");
        if (f->abs) {
            put_long(obj->code.p + f->at, (uint32_t)target);
        } else {
            long d = target - (long)f->at;
            if (d < -32768 || d > 32767) fatal("salto de más de 32 KB (aún no admitido)");
            put_word(obj->code.p + f->at, (int)d);
        }
    }
}

/* ---- nombres: constantes, globales, variables locales y funciones ---- */
/* Una variable con nombre: un hueco (slot >= 0) o, en una función copiada en el
   sitio de la llamada, un parámetro que vale una constante (slot -1 y val). frame
   separa los nombres de cada copia de los de la función que la contiene. */
typedef struct { char *name; int slot, type, depth, frame; long val; } Local;
static struct { Local *v; int n, cap; } locals;
static int depth, cur_frame, frame_count;

/* Cada variable local o parámetro de la función es un "hueco": en la primera pasada
   se cuentan sus usos; en la segunda, slot_reg dice en qué registro va (o -1). */
static struct { long *v; int n, cap; } slot_uses, slot_start, slot_end;
static long event;   /* posición en el código de cada uso (primera pasada) */
/* Bucles abiertos: una variable de antes del bucle que se usa dentro tiene que
   seguir viva hasta el final del bucle (la vuelta siguiente la vuelve a leer). */
typedef struct { long start; struct { int *v; int n, cap; } slots; } LoopLife;
static struct { LoopLife *v; int n, cap; } lives;
static struct { int *v; int n, cap; } slot_reg, slot_off;
static long loop_weight = 1;
static int nframe;   /* huecos en el marco */

typedef struct { int brk, cont; } Loop;
static struct { Loop *v; int n, cap; } loops;
static int loop_base;   /* los bucles de antes son de fuera de la función copiada */

static int *func_label;   /* etiqueta de cada función */
static int *global_type;
static int ret_label;

enum { V_NONE, V_LOCAL, V_REG, V_GLOBAL, V_CONST, V_STACK };

/* Una función sin variables en el marco no hace link: lee sus parámetros con sp,
   sabiendo cuánto ha metido en la pila (sp_depth) en cada punto del código. */
static int frameless, sp_depth, param_base;
typedef struct { int kind, off, reg, type; long val; } Var;

static int fold(Node *n, long *v);

static Local *find_local(const char *name)
{
    int i;
    for (i = locals.n - 1; i >= 0; i--)
        if (locals.v[i].frame == cur_frame && !strcmp(locals.v[i].name, name)) return &locals.v[i];
    return NULL;
}

static void use_slot(int slot)
{
    int i;
    slot_uses.v[slot] += loop_weight;
    slot_end.v[slot] = ++event;
    for (i = 0; i < lives.n; i++)
        if (lives.v[i].start > slot_start.v[slot]) {
            VEC_PUSH(lives.v[i].slots, slot);          /* el bucle más externo de los de después */
            break;
        }
}

static Var slot_var(int slot, int type)
{
    Var r = {V_LOCAL, 0, 0, TY_INT, 0};
    r.type = type;
    if (slot_reg.v[slot] >= 0) {
        r.kind = V_REG;
        r.reg = slot_reg.v[slot];
    } else if (frameless) {
        r.kind = V_STACK;                              /* solo los parámetros llegan aquí */
        r.off = slot_off.v[slot];
    } else {
        r.off = slot_off.v[slot];
    }
    return r;
}

static Var lookup(const char *name)
{
    Var r = {V_NONE, 0, 0, TY_INT, 0};
    Local *lc = find_local(name);
    int i;
    if (lc && lc->slot < 0) {
        r.kind = V_CONST;
        r.val = lc->val;
        r.type = lc->type;
        return r;
    }
    if (lc) {
        use_slot(lc->slot);
        return slot_var(lc->slot, lc->type);
    }
    for (i = 0; i < prog->globals.n; i++)
        if (!strcmp(prog->globals.v[i].name, name)) {
            r.kind = V_GLOBAL;
            r.off = i * 4;
            r.type = global_type[i];
            return r;
        }
    for (i = 0; i < prog->consts.n; i++)
        if (!strcmp(prog->consts.v[i].name, name)) {
            Const *c = &prog->consts.v[i];
            r.kind = V_CONST;
            if (!fold(c->value, &r.val)) fatal_at(c->line, c->col, "la constante %s no es un número fijo", c->name);
            r.type = c->value->kind == E_BOOL ? TY_BOOL : TY_INT;
            return r;
        }
    return r;
}

/* un hueco nuevo; en la segunda pasada los huecos salen en el mismo orden */
static int new_slot(int param_off)
{
    int slot = slot_uses.n;
    VEC_PUSH(slot_uses, 0);
    VEC_PUSH(slot_start, ++event);
    VEC_PUSH(slot_end, event);
    if (slot >= slot_reg.n) VEC_PUSH(slot_reg, -1);
    if (param_off) {
        VEC_PUSH(slot_off, param_off);
    } else if (slot_reg.v[slot] >= 0) {
        VEC_PUSH(slot_off, 0);
    } else {
        VEC_PUSH(slot_off, -4 * ++nframe);
    }
    return slot;
}

static Var declare(const char *name, int type)
{
    Local lc;
    lc.name = (char *)name;
    lc.slot = new_slot(0);
    lc.type = type;
    lc.depth = depth;
    lc.frame = cur_frame;
    lc.val = 0;
    VEC_PUSH(locals, lc);
    use_slot(lc.slot);
    return slot_var(lc.slot, type);
}

static void enter_scope(void) { depth++; }

static void leave_scope(void)
{
    depth--;
    while (locals.n && locals.v[locals.n - 1].depth > depth) locals.n--;
}

static void enter_loop(void)
{
    LoopLife lf;
    if (loop_weight < (1L << 20)) loop_weight *= 8;
    lf.start = ++event;
    lf.slots.v = NULL;
    lf.slots.n = lf.slots.cap = 0;
    VEC_PUSH(lives, lf);
}

static void leave_loop(void)
{
    LoopLife *lf = &lives.v[--lives.n];
    long end = ++event;
    int i;
    if (loop_weight > 1) loop_weight /= 8;
    for (i = 0; i < lf->slots.n; i++)
        if (slot_end.v[lf->slots.v[i]] < end) slot_end.v[lf->slots.v[i]] = end;
    free(lf->slots.v);
}

static Func *find_func(const char *name, int *idx)
{
    int i;
    for (i = 0; i < prog->funcs.n; i++)
        if (!strcmp(prog->funcs.v[i].name, name)) {
            if (idx) *idx = i;
            return &prog->funcs.v[i];
        }
    return NULL;
}

/* ---- valores conocidos al compilar ---- */
static int32_t arith(int op, int32_t a, int32_t b, Node *at)
{
    switch (op) {
    case P_PLUS: return (int32_t)((uint32_t)a + (uint32_t)b);
    case P_MINUS: return (int32_t)((uint32_t)a - (uint32_t)b);
    case P_STAR: return (int32_t)((uint32_t)a * (uint32_t)b);
    case P_SLASH:
    case P_PERCENT:
        if (!b) fatal_at(at->line, at->col, "división por cero");
        if (a == INT32_MIN && b == -1) return op == P_SLASH ? a : 0;
        return op == P_SLASH ? a / b : a % b;
    case P_AMP: return a & b;
    case P_BAR: return a | b;
    case P_CARET: return a ^ b;
    case P_SHL: return (int32_t)((uint32_t)a << (b & 31));
    case P_SHR: return a >> (b & 31);
    }
    return 0;
}

static int fold(Node *n, long *v)
{
    long a, b;
    switch (n->kind) {
    case E_INT:
    case E_BOOL:
        *v = n->val;
        return 1;
    case E_VAR: {
        Local *lc = find_local(n->name);
        int i;
        if (lc) {
            if (lc->slot >= 0) return 0;
            *v = lc->val;
            return 1;
        }
        for (i = 0; i < prog->globals.n; i++)
            if (!strcmp(prog->globals.v[i].name, n->name)) return 0;
        for (i = 0; i < prog->consts.n; i++)
            if (!strcmp(prog->consts.v[i].name, n->name)) return fold(prog->consts.v[i].value, v);
        return 0;
    }
    case E_NEG:
        if (!fold(n->a, &a)) return 0;
        *v = (int32_t)(0u - (uint32_t)a);
        return 1;
    case E_BNOT:
        if (!fold(n->a, &a)) return 0;
        *v = ~(int32_t)a;
        return 1;
    case E_BIN:
        if (!fold(n->a, &a) || !fold(n->b, &b)) return 0;
        if ((n->op == P_SLASH || n->op == P_PERCENT) && b == 0) return 0;   /* error al ejecutar */
        *v = arith(n->op, (int32_t)a, (int32_t)b, n);
        return 1;
    }
    return 0;
}

/* k = ±2^s con s >= 1: devuelve s; si no, 0 */
static int pow2(long k)
{
    uint32_t m = k < 0 ? 0u - (uint32_t)k : (uint32_t)k;
    int s = 0;
    if (m < 2 || (m & (m - 1))) return 0;
    while (m > 1) { m >>= 1; s++; }
    return s;
}

/* ---- direcciones efectivas: una variable como operando de una instrucción ---- */
static int ea_bits(Var *v)
{
    switch (v->kind) {
    case V_REG: return v->reg;      /* dN */
    case V_LOCAL: return 0x2D;      /* d16(a5) */
    case V_STACK: return 0x2F;      /* d16(sp) */
    case V_GLOBAL: return 0x39;     /* abs.l */
    default: return 0x3C;           /* #inmediato */
    }
}

static void ea_ext(Var *v)
{
    switch (v->kind) {
    case V_LOCAL:
        w(v->off);
        break;
    case V_STACK:
        w(sp_depth + param_base + v->off - 8);
        break;
    case V_GLOBAL:
        add_reloc((uint32_t)obj->code.n, HK_DATA, NULL);
        l((uint32_t)v->off);
        break;
    case V_CONST:
        l((uint32_t)v->val);
        break;
    }
}

/* una instrucción con la variable como operando (opcode sin los 6 bits de la dirección) */
static void op_ea(int opcode, Var *v)
{
    w(opcode | ea_bits(v));
    ea_ext(v);
}

/* una instrucción con un inmediato de 32 bits y la variable como destino (addi, cmpi...) */
static void op_imm_ea(int opcode, long k, Var *v)
{
    w(opcode | ea_bits(v));
    l((uint32_t)k);
    ea_ext(v);
}

/* tst.l d0, salvo si lo último fue cargar d0 con move/moveq (ya pone N y Z, y V = C = 0) */

static void tst_d0(void)
{
    if (d0_loaded != obj->code.n) w(0x4A80);           /* tst.l d0 */
}

static void load_imm(int reg, long v)
{
    int32_t x = (int32_t)v;
    if (x >= -128 && x <= 127) {
        w(0x7000 | reg << 9 | (x & 0xFF));            /* moveq #x,dN */
    } else {
        w(0x203C | reg << 9);                          /* move.l #x,dN */
        l((uint32_t)x);
    }
    if (reg == 0) d0_loaded = (uint32_t)obj->code.n;
}

static void load_var(int reg, Var *v)
{
    if (v->kind == V_CONST) load_imm(reg, v->val);
    else if (!(v->kind == V_REG && v->reg == reg)) {
        op_ea(0x2000 | reg << 9, v);                   /* move.l v,dN */
        if (reg == 0) d0_loaded = (uint32_t)obj->code.n;
    }
}

static void store_d0(Var *v)
{
    if (v->kind == V_REG) {
        w(0x2000 | v->reg << 9);                       /* move.l d0,dN */
    } else if (v->kind == V_LOCAL) {
        w(0x2B40);                                     /* move.l d0,off(a5) */
        w(v->off);
    } else {
        w(0x23C0);                                     /* move.l d0,global */
        add_reloc((uint32_t)obj->code.n, HK_DATA, NULL);
        l((uint32_t)v->off);
    }
}

/* suma k a la variable, sin pasar por d0 */
static void add_imm_ea(long k, Var *v)
{
    if (k >= 1 && k <= 8) op_ea(0x5080 | (k & 7) << 9, v);          /* addq.l #k,v */
    else if (k <= -1 && k >= -8) op_ea(0x5180 | (-k & 7) << 9, v);  /* subq.l #k,v */
    else if (k) op_imm_ea(0x0680, k, v);                            /* addi.l #k,v */
}

static uint32_t add_string(const char *s, int len)
{
    uint32_t off = (uint32_t)obj->data.n;
    buf_bytes(&obj->data, s, len);
    buf_byte(&obj->data, 0);
    if (obj->data.n & 1) buf_byte(&obj->data, 0);
    return off;
}

static void push_d0(void)
{
    w(0x2F00);                                         /* move.l d0,-(sp) */
    sp_depth += 4;
}

static void pop_d0(void)
{
    w(0x201F);                                         /* move.l (sp)+,d0 */
    sp_depth -= 4;
}

static void pea_string(const char *str, int len)
{
    w(0x4879);                                         /* pea texto */
    add_reloc((uint32_t)obj->code.n, HK_DATA, NULL);
    l(add_string(str, len));
    sp_depth += 4;
}

static void pop_args(int n)
{
    int bytes = n * 4;
    sp_depth -= bytes;
    if (!bytes) return;
    if (bytes <= 8) w(0x508F | (bytes & 7) << 9);      /* addq.l #n,sp */
    else { w(0x4FEF); w(bytes); }                      /* lea n(sp),sp */
}

/* un operando que se usa sin calcular nada: una constante o una variable */
static int simple(Node *n, Var *v)
{
    long k;
    if (fold(n, &k)) {
        v->kind = V_CONST;
        v->val = k;
        v->type = n->kind == E_BOOL ? TY_BOOL : TY_INT;
        return 1;
    }
    if (n->kind == E_VAR) {
        *v = lookup(n->name);
        if (v->kind == V_NONE) fatal_at(n->line, n->col, "la variable %s no existe", n->name);
        return 1;
    }
    return 0;
}

static int gen_expr(Node *n);
static void gen_branch(Node *n, int label, int when_true);
static void gen_block(NodeList *b);

static void need_value(Node *n, int ty)
{
    if (ty == TY_VOID) fatal_at(n->line, n->col, "%s no devuelve ningún valor", n->name ? n->name : "la expresión");
    if (ty == TY_STR) fatal_at(n->line, n->col, "dashc (prueba): los textos solo pueden ir en Print");
}

static void value(Node *n) { need_value(n, gen_expr(n)); }

/* mete en la pila el valor de n (un argumento) */
static void push_value(Node *n)
{
    Var v;
    if (n->kind != E_STR && simple(n, &v)) {
        if (v.kind == V_CONST && v.val >= -32768 && v.val <= 32767) {
            w(0x4878);                                 /* pea k.w */
            w((int)v.val);
        } else {
            op_ea(0x2F00, &v);                         /* move.l v,-(sp) */
        }
        sp_depth += 4;
        return;
    }
    value(n);
    push_d0();
}

/* ---- operaciones con una constante ---- */
static void shift_d0(int left, int s)
{
    if (s <= 0) return;
    if (left && s == 1) w(0xD080);                     /* add.l d0,d0 */
    else if (s <= 8) w((left ? 0xE180 : 0xE080) | (s & 7) << 9);   /* asl/asr.l #s,d0 */
    else {
        load_imm(1, s);
        w(left ? 0xE3A0 : 0xE2A0);                     /* asl/asr.l d1,d0 */
    }
}

static int popcount(uint32_t m)
{
    int c = 0;
    for (; m; m &= m - 1) c++;
    return c;
}

/* d0 = d0 * k */
static void mul_const(long k)
{
    uint32_t m = k < 0 ? 0u - (uint32_t)k : (uint32_t)k;
    int neg = k < 0, s = 0;
    if (k == 0) { w(0x7000); return; }                 /* moveq #0,d0 */
    if (popcount(m) == 1) {
        while ((1u << s) != m) s++;
        shift_d0(1, s);
    } else if (popcount(m) == 2) {
        /* x * (2^a + 2^b) = ((x << (a-b)) + x) << b */
        int b = 0, a;
        while (!(m & (1u << b))) b++;
        a = b + 1;
        while (!(m & (1u << a))) a++;
        w(0x2200);                                     /* move.l d0,d1 */
        shift_d0(1, a - b);
        w(0xD081);                                     /* add.l d1,d0 */
        shift_d0(1, b);
    } else if (m <= 0xFFFF) {
        /* x * m = lo*m + ((hi*m) << 16): dos mulu.w */
        w(0x2200);                                     /* move.l d0,d1 */
        w(0x4841);                                     /* swap d1 */
        w(0xC2FC); w((int)m);                          /* mulu.w #m,d1 */
        w(0x4841);                                     /* swap d1 */
        w(0x4241);                                     /* clr.w d1 */
        w(0xC0FC); w((int)m);                          /* mulu.w #m,d0 */
        w(0xD081);                                     /* add.l d1,d0 */
    } else {
        /* x * m = lo*mlo + ((hi*mlo + lo*mhi) << 16): tres mulu.w */
        int mlo = (int)(m & 0xFFFF), mhi = (int)(m >> 16);
        w(0x2200);                                     /* move.l d0,d1 */
        w(0x4841);                                     /* swap d1 */
        w(0xC2FC); w(mlo);                             /* mulu.w #mlo,d1 */
        w(0x2040);                                     /* movea.l d0,a0 */
        w(0xC0FC); w(mhi);                             /* mulu.w #mhi,d0 */
        w(0xD240);                                     /* add.w d0,d1 */
        w(0x4841);                                     /* swap d1 */
        w(0x4241);                                     /* clr.w d1 */
        w(0x2008);                                     /* move.l a0,d0 */
        w(0xC0FC); w(mlo);                             /* mulu.w #mlo,d0 */
        w(0xD081);                                     /* add.l d1,d0 */
    }
    if (neg) w(0x4480);                                /* neg.l d0 */
}

/* d0 = d0 / k o d0 % k, con k = ±2^s, redondeando hacia cero como en C */
static void divmod_pow2(int op, long k, int s)
{
    uint32_t mask = (1u << s) - 1;
    if (op == P_SLASH) {
        tst_d0();
        if (mask <= 8) {
            w(0x6A02);                                 /* bpl.s +2 */
            w(0x5080 | (mask & 7) << 9);               /* addq.l #mask,d0 */
        } else {
            w(0x6A06);                                 /* bpl.s +6 */
            w(0xD0BC); l(mask);                        /* add.l #mask,d0 */
        }
        shift_d0(0, s);
        if (k < 0) w(0x4480);                          /* neg.l d0 */
    } else {
        /* el resto lleva el signo del dividendo: -(-x & mask) si x < 0 */
        tst_d0();
        w(0x6B08);                                     /* bmi.s +8 */
        w(0x0280); l(mask);                            /* andi.l #mask,d0 */
        w(0x600A);                                     /* bra.s +10 */
        w(0x4480);                                     /* neg.l d0 */
        w(0x0280); l(mask);                            /* andi.l #mask,d0 */
        w(0x4480);                                     /* neg.l d0 */
    }
}

/* d0 = d0 op v */
static void bin_ea(int op, Var *v)
{
    long k = v->val;
    int s;
    if (v->kind == V_CONST) {
        switch (op) {
        case P_PLUS:
        case P_MINUS:
            if (op == P_MINUS) k = -k;
            if (k >= 1 && k <= 8) w(0x5080 | (k & 7) << 9);          /* addq.l #k,d0 */
            else if (k <= -1 && k >= -8) w(0x5180 | (-k & 7) << 9);  /* subq.l #k,d0 */
            else if (k) { w(0xD0BC); l((uint32_t)k); }                /* add.l #k,d0 */
            return;
        case P_STAR:
            mul_const(k);
            return;
        case P_SLASH:
        case P_PERCENT:
            if (k == 1 || k == -1) {
                if (op == P_PERCENT) w(0x7000);        /* moveq #0,d0 */
                else if (k == -1) w(0x4480);           /* neg.l d0 */
                return;
            }
            if ((s = pow2(k)) != 0) {
                divmod_pow2(op, k, s);
                return;
            }
            break;
        case P_SHL:
        case P_SHR:
            if (k >= 0 && k <= 31) {
                shift_d0(op == P_SHL, (int)k);
                return;
            }
            break;
        }
    }
    switch (op) {
    case P_PLUS: op_ea(0xD080, v); return;             /* add.l v,d0 */
    case P_MINUS: op_ea(0x9080, v); return;            /* sub.l v,d0 */
    case P_AMP: op_ea(0xC080, v); return;              /* and.l v,d0 */
    case P_BAR: op_ea(0x8080, v); return;              /* or.l v,d0 */
    case P_CARET:
        if (v->kind == V_REG) { w(0xB180 | v->reg << 9); return; }  /* eor.l dN,d0 */
        break;
    }
    load_var(1, v);
    switch (op) {
    case P_CARET: w(0xB380); break;                    /* eor.l d1,d0 */
    case P_SHL: w(0xE3A0); break;                      /* asl.l d1,d0 */
    case P_SHR: w(0xE2A0); break;                      /* asr.l d1,d0 */
    case P_STAR: jsr_sym("__dash_mul"); break;         /* d0 * d1 en el runtime */
    case P_SLASH: jsr_sym("__dash_div"); break;
    case P_PERCENT: jsr_sym("__dash_mod"); break;
    }
}

static int commutative(int op)
{
    return op == P_PLUS || op == P_STAR || op == P_AMP || op == P_BAR || op == P_CARET;
}

static void gen_binary(Node *n)
{
    Var v;
    long k;
    if (commutative(n->op) && fold(n->a, &k) && !fold(n->b, &k)) {
        simple(n->a, &v);                              /* 3 * x es x * 3 */
        value(n->b);
        bin_ea(n->op, &v);
    } else if (simple(n->b, &v)) {
        value(n->a);
        bin_ea(n->op, &v);
    } else if (commutative(n->op) && simple(n->a, &v)) {
        value(n->b);
        bin_ea(n->op, &v);
    } else {
        Var d1 = {V_REG, 0, 1, TY_INT, 0};
        value(n->a);
        push_d0();
        value(n->b);
        w(0x2200);                                     /* move.l d0,d1 */
        pop_d0();
        bin_ea(n->op, &d1);
    }
}

static int cmp_cc(int op)
{
    switch (op) {
    case P_EQ: return CC_EQ;
    case P_NE: return CC_NE;
    case P_LT: return CC_LT;
    case P_LE: return CC_LE;
    case P_GT: return CC_GT;
    default: return CC_GE;
    }
}

/* la condición con los operandos al revés: a < b es b > a */
static int swap_cc(int cc)
{
    switch (cc) {
    case CC_LT: return CC_GT;
    case CC_GT: return CC_LT;
    case CC_LE: return CC_GE;
    case CC_GE: return CC_LE;
    }
    return cc;
}

/* Compara a con b y deja los códigos de condición. Devuelve el código de
   condición que hay que mirar para la comparación de n. */
static int gen_compare(Node *n)
{
    Var va, vb;
    long k;
    int cc = cmp_cc(n->op);

    /* x % 2^s == 0: basta con mirar los bits bajos, sea cual sea el signo */
    if ((cc == CC_EQ || cc == CC_NE) && fold(n->b, &k) && k == 0 && n->a->kind == E_BIN &&
        n->a->op == P_PERCENT && fold(n->a->b, &k) && pow2(k)) {
        value(n->a->a);
        w(0x0280); l((k < 0 ? 0u - (uint32_t)k : (uint32_t)k) - 1);   /* andi.l #mask,d0 */
        return cc;
    }
    if (simple(n->b, &vb)) {
        if (vb.kind == V_CONST && n->a->kind == E_VAR && simple(n->a, &va) && va.kind != V_CONST) {
            if (vb.val == 0) op_ea(0x4A80, &va);       /* tst.l a */
            else op_imm_ea(0x0C80, vb.val, &va);       /* cmpi.l #k,a */
            return cc;
        }
        if (vb.kind != V_CONST && n->a->kind == E_VAR && simple(n->a, &va) && va.kind == V_REG) {
            op_ea(0xB080 | va.reg << 9, &vb);          /* cmp.l b,dA */
            return cc;
        }
        value(n->a);
        if (vb.kind == V_CONST && vb.val == 0) tst_d0();
        else op_ea(0xB080, &vb);                       /* cmp.l b,d0 */
        return cc;
    }
    if (simple(n->a, &va)) {
        /* b - a: la condición al revés */
        value(n->b);
        op_ea(0xB080, &va);                            /* cmp.l a,d0 */
        return swap_cc(cc);
    }
    value(n->a);
    push_d0();
    value(n->b);
    w(0x2200);                                         /* move.l d0,d1 */
    pop_d0();
    w(0xB081);                                         /* cmp.l d1,d0 */
    return cc;
}


/* funciones del runtime: argumentos Int, o S para un texto literal */
static const struct { const char *name, *sym, *args; int ret; } builtins[] = {
    {"bench_start", "__bench_start", "", TY_VOID},
    {"bench_end", "__bench_end", "SI", TY_VOID},
    {NULL, NULL, NULL, 0}
};
static long sink_off = -1;

static int gen_builtin(Node *n)
{
    int i, b;
    if (!strcmp(n->name, "bench_sink")) {
        /* guarda el valor donde no se pueda quitar: un move.l, como el volatile de bench_lib.dash */
        Var v;
        Var src;
        if (n->args.n != 1) fatal_at(n->line, n->col, "bench_sink pide 1 argumento");
        if (sink_off < 0) {
            sink_off = (long)obj->data.n;
            buf_long(&obj->data, 0);
        }
        if (n->args.v[0]->kind == E_VAR && simple(n->args.v[0], &src) && src.kind != V_CONST) {
            op_ea(0x23C0, &src);                       /* move.l v,sumidero */
            add_reloc((uint32_t)obj->code.n, HK_DATA, NULL);
            l((uint32_t)sink_off);
            return TY_VOID;
        }
        value(n->args.v[0]);
        v.kind = V_GLOBAL;
        v.off = (int)sink_off;
        store_d0(&v);
        return TY_VOID;
    }
    for (b = 0; builtins[b].name; b++)
        if (!strcmp(builtins[b].name, n->name)) break;
    if (!builtins[b].name) fatal_at(n->line, n->col, "la función %s no existe", n->name);
    if (n->args.n != (int)strlen(builtins[b].args))
        fatal_at(n->line, n->col, "%s pide %d argumentos y se le dan %d", n->name, (int)strlen(builtins[b].args), n->args.n);
    for (i = n->args.n - 1; i >= 0; i--) {
        Node *a = n->args.v[i];
        if (builtins[b].args[i] == 'S') {
            if (a->kind != E_STR) fatal_at(a->line, a->col, "dashc (prueba): aquí va un texto literal");
            pea_string(a->str, a->len);
        } else {
            push_value(a);
        }
    }
    jsr_sym(builtins[b].sym);
    pop_args(n->args.n);
    return builtins[b].ret;
}

/* ---- funciones copiadas en el sitio de la llamada ----
   Como gcc con las funciones static: se copia una función pequeña, o la que solo
   se llama desde un sitio, si no es recursiva. Cada argumento se calcula una vez,
   en un hueco nuevo; una constante o una variable que la función no cambia se usa
   tal cual. */
#define INLINE_SIZE 25   /* nodos del árbol */
#define INLINE_DEPTH 4

static int *call_sites, *body_size, *needed;
static unsigned char **param_set;   /* la función asigna a ese parámetro */
static struct { int *v; int n, cap; } inl_stack;   /* funciones que se están generando o copiando */

static int can_inline(int idx)
{
    int i;
    if (inl_stack.n >= INLINE_DEPTH) return 0;
    for (i = 0; i < inl_stack.n; i++)
        if (inl_stack.v[i] == idx) return 0;
    return body_size[idx] <= INLINE_SIZE || call_sites[idx] == 1;
}

static int gen_inline(Node *n, Func *f, int idx)
{
    int i, saved_frame = cur_frame, saved_ret = ret_label, saved_base = loop_base, frame = ++frame_count;
    Local *binds = xmalloc(sizeof(Local) * (n->args.n + 1));

    enter_scope();
    for (i = n->args.n - 1; i >= 0; i--) {
        Node *a = n->args.v[i];
        Local *b = &binds[i], *src;
        long k;
        b->name = f->params.v[i].name;
        b->type = f->params.v[i].type;
        b->depth = depth;
        b->frame = frame;
        b->slot = -1;
        b->val = 0;
        if (!param_set[idx][i] && fold(a, &k)) {
            b->val = k;
            continue;
        }
        if (!param_set[idx][i] && a->kind == E_VAR && (src = find_local(a->name)) != NULL) {
            b->slot = src->slot;
            b->val = src->val;
            if (src->slot >= 0) use_slot(src->slot);
            continue;
        }
        value(a);
        b->slot = new_slot(0);
        use_slot(b->slot);
        {
            Var t = slot_var(b->slot, b->type);
            store_d0(&t);
        }
    }
    cur_frame = frame;
    for (i = 0; i < n->args.n; i++) VEC_PUSH(locals, binds[i]);
    free(binds);
    ret_label = new_label();
    loop_base = loops.n;
    VEC_PUSH(inl_stack, idx);
    gen_block(&f->body);
    inl_stack.n--;
    def_label(ret_label);
    ret_label = saved_ret;
    loop_base = saved_base;
    cur_frame = saved_frame;
    leave_scope();
    return f->ret;
}

static int gen_call(Node *n)
{
    int i, idx;
    Func *f = find_func(n->name, &idx);
    if (!f) return gen_builtin(n);
    if (n->args.n != f->params.n)
        fatal_at(n->line, n->col, "%s pide %d argumentos y se le dan %d", n->name, f->params.n, n->args.n);
    if (can_inline(idx)) return gen_inline(n, f, idx);
    for (i = n->args.n - 1; i >= 0; i--) push_value(n->args.v[i]);
    jsr_label(func_label[idx]);
    pop_args(n->args.n);
    if (!needed[idx]) needed[idx] = 1;               /* 2: ya generada */
    return f->ret;
}

static int gen_expr(Node *n)
{
    long k;
    Var v;

    if (n->kind != E_CMP && n->kind != E_AND && n->kind != E_OR && n->kind != E_NOT && fold(n, &k)) {
        load_imm(0, k);
        return n->kind == E_BOOL ? TY_BOOL : TY_INT;
    }
    switch (n->kind) {
    case E_STR:
        return TY_STR;
    case E_VAR:
        v = lookup(n->name);
        if (v.kind == V_NONE) fatal_at(n->line, n->col, "la variable %s no existe", n->name);
        load_var(0, &v);
        return v.type;
    case E_CALL:
        return gen_call(n);
    case E_NEG:
        value(n->a);
        w(0x4480);                                     /* neg.l d0 */
        return TY_INT;
    case E_BNOT:
        value(n->a);
        w(0x4680);                                     /* not.l d0 */
        return TY_INT;
    case E_CMP:
        w(0x50C0 | gen_compare(n) << 8);               /* scc d0 */
        w(0x0280); l(1);                               /* andi.l #1,d0 */
        return TY_BOOL;
    case E_NOT:
    case E_AND:
    case E_OR: {
        int f = new_label(), done = new_label();
        gen_branch(n, f, 0);
        w(0x7001);                                     /* moveq #1,d0 */
        branch(CC_T, done);
        def_label(f);
        w(0x7000);                                     /* moveq #0,d0 */
        def_label(done);
        return TY_BOOL;
    }
    case E_BIN:
        gen_binary(n);
        return TY_INT;
    }
    fatal_at(n->line, n->col, "expresión no admitida");
    return TY_VOID;
}

/* salta a label si n es verdadero (when_true) o falso */
static void gen_branch(Node *n, int label, int when_true)
{
    long k;
    Var v;
    switch (n->kind) {
    case E_NOT:
        gen_branch(n->a, label, !when_true);
        return;
    case E_AND:
        if (when_true) {
            int skip = new_label();
            gen_branch(n->a, skip, 0);
            gen_branch(n->b, label, 1);
            def_label(skip);
        } else {
            gen_branch(n->a, label, 0);
            gen_branch(n->b, label, 0);
        }
        return;
    case E_OR:
        if (when_true) {
            gen_branch(n->a, label, 1);
            gen_branch(n->b, label, 1);
        } else {
            int skip = new_label();
            gen_branch(n->a, skip, 1);
            gen_branch(n->b, label, 0);
            def_label(skip);
        }
        return;
    case E_CMP: {
        int cc = gen_compare(n);
        branch(when_true ? cc : cc ^ 1, label);        /* cc ^ 1: la condición contraria */
        return;
    }
    }
    if (fold(n, &k)) {
        if ((k != 0) == when_true) branch(CC_T, label);
        return;
    }
    if (n->kind == E_VAR && simple(n, &v)) op_ea(0x4A80, &v);   /* tst.l v */
    else {
        value(n);
        tst_d0();
    }
    branch(when_true ? CC_NE : CC_EQ, label);
}

/* ---- instrucciones ---- */
static void gen_block(NodeList *b);

static void gen_for(Node *n)
{
    long from, to, step = 1;
    int down = 0, top = new_label(), cont = new_label(), done = new_label(), test;
    int step_known = 1, end_known;
    Var vi, vend, vstep;
    Loop lp;

    if (n->c && !fold(n->c, &step)) step_known = 0;
    if (step_known && step < 0) down = 1;
    /* sin paso, (5..1) cuenta hacia atrás si los dos extremos son fijos */
    if (!n->c && fold(n->a, &from) && fold(n->b, &to) && from > to) {
        down = 1;
        step = -1;
    }
    if (step_known && step == 0) fatal_at(n->line, n->col, "el paso del for no puede ser 0");

    enter_scope();
    value(n->a);
    vi = declare(n->name, TY_INT);
    store_d0(&vi);
    end_known = fold(n->b, &to);
    if (end_known) {
        vend.kind = V_CONST;
        vend.val = to;
    } else {
        value(n->b);
        vend = declare("", TY_INT);                    /* "": no se puede nombrar */
        store_d0(&vend);
    }
    if (!step_known) {
        value(n->c);
        vstep = declare("", TY_INT);
        store_d0(&vstep);
    }

    enter_loop();
    /* las veces que se usan en cada vuelta: comparar e incrementar */
    use_slot(locals.v[locals.n - 1 - !end_known - !step_known].slot);
    if (!end_known) use_slot(locals.v[locals.n - 1 - !step_known].slot);
    if (!step_known) use_slot(locals.v[locals.n - 1].slot);

    /* la comparación va al final: una vuelta es cuerpo, incremento y un salto */
    test = new_label();
    branch(CC_T, test);
    def_label(top);
    lp.brk = done;
    lp.cont = cont;
    VEC_PUSH(loops, lp);
    gen_block(&n->body);
    loops.n--;

    def_label(cont);
    if (!step_known) {
        if (vi.kind == V_REG) op_ea(0xD080 | vi.reg << 9, &vstep);  /* add.l paso,di */
        else {
            load_var(0, &vstep);
            op_ea(0xD180, &vi);                        /* add.l d0,i */
        }
    } else {
        add_imm_ea(step, &vi);
    }
    def_label(test);
    if (vend.kind == V_CONST) op_imm_ea(0x0C80, vend.val, &vi);     /* cmpi.l #fin,i */
    else if (vi.kind == V_REG) op_ea(0xB080 | vi.reg << 9, &vend);  /* cmp.l fin,di */
    else {
        load_var(0, &vi);
        op_ea(0xB080, &vend);                          /* cmp.l fin,d0 */
    }
    branch(down ? CC_GE : CC_LE, top);
    def_label(done);
    leave_loop();
    leave_scope();
}

/* qué es un nombre, sin contarlo como uso */
static int lookup_kind(const char *name)
{
    Local *lc = find_local(name);
    if (!lc) return V_GLOBAL;
    if (lc->slot < 0) return V_CONST;
    return slot_reg.v[lc->slot] >= 0 ? V_REG : V_LOCAL;
}

/* v = v op e: la operación directamente sobre la variable */
static int gen_update(Node *n)
{
    Node *e = n->a, *other;
    Var v;
    long k;
    int op;
    if (e->kind != E_BIN) return 0;
    op = e->op;
    if (e->a->kind == E_VAR && !strcmp(e->a->name, n->name)) other = e->b;
    else if (commutative(op) && e->b->kind == E_VAR && !strcmp(e->b->name, n->name)) other = e->a;
    else return 0;
    if (op == P_CARET || op == P_SHL || op == P_SHR) {
        /* solo con una constante; los desplazamientos, solo en un registro */
        if (!fold(other, &k)) return 0;
        if (op != P_CARET && (lookup_kind(n->name) != V_REG || k < 1 || k > 8)) return 0;
    } else if (op != P_PLUS && op != P_MINUS && op != P_AMP && op != P_BAR) {
        return 0;
    }
    v = lookup(n->name);
    if (v.kind == V_NONE || v.kind == V_CONST) return 0;
    if (fold(other, &k)) {
        switch (op) {
        case P_PLUS: add_imm_ea(k, &v); return 1;
        case P_MINUS: add_imm_ea(-k, &v); return 1;
        case P_AMP: op_imm_ea(0x0280, k, &v); return 1;            /* andi.l #k,v */
        case P_BAR: op_imm_ea(0x0080, k, &v); return 1;            /* ori.l #k,v */
        case P_CARET: op_imm_ea(0x0A80, k, &v); return 1;          /* eori.l #k,v */
        case P_SHL: w(0xE180 | (k & 7) << 9 | v.reg); return 1;    /* asl.l #k,dN */
        case P_SHR: w(0xE080 | (k & 7) << 9 | v.reg); return 1;    /* asr.l #k,dN */
        }
    }
    value(other);
    if (v.kind == V_REG) {
        static const int to_reg[] = {0xD080, 0x9080, 0xC080, 0x8080};   /* add/sub/and/or.l d0,dN */
        w(to_reg[op == P_PLUS ? 0 : op == P_MINUS ? 1 : op == P_AMP ? 2 : 3] | v.reg << 9);
    } else {
        static const int to_mem[] = {0xD180, 0x9180, 0xC180, 0x8180};   /* add/sub/and/or.l d0,v */
        op_ea(to_mem[op == P_PLUS ? 0 : op == P_MINUS ? 1 : op == P_AMP ? 2 : 3], &v);
    }
    return 1;
}

static void gen_stmt(Node *n)
{
    Var v;
    long k;
    int ty;
    switch (n->kind) {
    case S_PRINT:
        if (n->a->kind == E_STR) {
            pea_string(n->a->str, n->a->len);
            jsr_sym("__dash_print_str");
        } else {
            ty = gen_expr(n->a);
            need_value(n->a, ty);
            push_d0();
            jsr_sym(ty == TY_BOOL ? "__dash_print_bool" : "__dash_print_int");
        }
        pop_args(1);
        return;
    case S_ASSIGN:
    case S_VAR:
        if (n->kind == S_ASSIGN && gen_update(n)) return;
        if (n->kind == S_ASSIGN && fold(n->a, &k)) {
            v = lookup(n->name);
            if (v.kind == V_NONE) v = declare(n->name, n->a->kind == E_BOOL ? TY_BOOL : TY_INT);
            if (v.kind == V_CONST) fatal_at(n->line, n->col, "%s es una constante", n->name);
            if (v.kind == V_REG) {
                load_imm(v.reg, k);                    /* moveq #k,dN */
            } else {
                load_imm(0, k);
                store_d0(&v);
            }
            return;
        }
        ty = gen_expr(n->a);
        need_value(n->a, ty);
        v = lookup(n->name);
        if (n->kind == S_VAR || v.kind == V_NONE) {
            /* la primera asignación declara (en el bloque actual) */
            v = declare(n->name, n->kind == S_VAR ? n->type : ty);
        } else if (v.kind == V_CONST) {
            fatal_at(n->line, n->col, "%s es una constante", n->name);
        }
        store_d0(&v);
        return;
    case S_EXPR:
        gen_expr(n->a);
        return;
    case S_IF: {
        int f = new_label(), done = new_label();
        gen_branch(n->a, f, 0);
        enter_scope();
        gen_block(&n->body);
        leave_scope();
        if (n->els.n) branch(CC_T, done);
        def_label(f);
        enter_scope();
        gen_block(&n->els);
        leave_scope();
        def_label(done);
        return;
    }
    case S_WHILE: {
        Loop lp;
        int top = new_label(), test = new_label(), done = new_label();
        enter_loop();
        branch(CC_T, test);                            /* la condición va al final */
        def_label(top);
        lp.brk = done;
        lp.cont = test;
        VEC_PUSH(loops, lp);
        enter_scope();
        gen_block(&n->body);
        leave_scope();
        loops.n--;
        def_label(test);
        gen_branch(n->a, top, 1);
        def_label(done);
        leave_loop();
        return;
    }
    case S_FOR:
        gen_for(n);
        return;
    case S_BREAK:
    case S_CONTINUE:
        if (loops.n <= loop_base) fatal_at(n->line, n->col, "%s fuera de un bucle", n->kind == S_BREAK ? "break" : "continue");
        branch(CC_T, n->kind == S_BREAK ? loops.v[loops.n - 1].brk : loops.v[loops.n - 1].cont);
        return;
    case S_RETURN:
        if (n->a) value(n->a);
        branch(CC_T, ret_label);
        return;
    }
    fatal_at(n->line, n->col, "instrucción no admitida");
}

static void gen_block(NodeList *b)
{
    int i;
    for (i = 0; i < b->n; i++) gen_stmt(b->v[i]);
}

/* una pasada sobre la función: link a5,#-marco; guarda registros ... recupera; unlk a5; rts */
static void gen_function_pass(int label, Func *f, NodeList *body)
{
    uint32_t frame_at = 0;
    int i, nregs = 0, mask_push = 0, mask_pop = 0, last = 0;

    locals.n = 0;
    depth = 0;
    nframe = 0;
    loop_weight = 1;
    slot_uses.n = 0;
    slot_start.n = 0;
    slot_end.n = 0;
    event = 0;
    slot_off.n = 0;
    cur_frame = 0;
    loops.n = 0;
    loop_base = 0;
    ret_label = new_label();

    for (i = 0; i < slot_reg.n; i++)
        if (slot_reg.v[i] >= 0) {
            nregs++;
            last = slot_reg.v[i];
            mask_push |= 0x8000 >> slot_reg.v[i];      /* movem -(sp): d0 es el bit 15 */
            mask_pop |= 1 << slot_reg.v[i];            /* movem (sp)+: d0 es el bit 0 */
        }

    sp_depth = 0;
    param_base = 4 + 4 * nregs;                        /* dirección de vuelta y registros guardados */
    def_label(label);
    if (!frameless) {
        w(0x4E55);                                     /* link a5,#-marco */
        frame_at = (uint32_t)obj->code.n;
        w(0);
    }
    if (nregs == 1) w(0x2F00 | last);                  /* move.l dN,-(sp) */
    else if (nregs) { w(0x48E7); w(mask_push); }       /* movem.l regs,-(sp) */

    if (f)
        for (i = 0; i < f->params.n; i++) {
            Local lc;
            lc.name = f->params.v[i].name;
            lc.slot = new_slot(8 + 4 * i);
            lc.type = f->params.v[i].type;
            lc.depth = 0;
            lc.frame = 0;
            lc.val = 0;
            VEC_PUSH(locals, lc);
            if (slot_reg.v[lc.slot] >= 0) {
                if (frameless) {
                    w(0x202F | slot_reg.v[lc.slot] << 9);   /* move.l d16(sp),dN */
                    w(param_base + 4 * i);
                } else {
                    w(0x202D | slot_reg.v[lc.slot] << 9);   /* move.l 8+4i(a5),dN */
                    w(8 + 4 * i);
                }
            }
        }
    gen_block(body);
    def_label(ret_label);
    if (sp_depth) fatal("la pila no cuadra (fallo de dashc)");
    if (nregs == 1) w(0x201F | last << 9);             /* move.l (sp)+,dN */
    else if (nregs) { w(0x4CDF); w(mask_pop); }        /* movem.l (sp)+,regs */
    if (!frameless) {
        w(0x4E5D);                                     /* unlk a5 */
        if (nframe * 4 > 32767) fatal("demasiadas variables en una función");
        put_word(obj->code.p + frame_at, -4 * nframe);
    }
    w(0x4E75);                                         /* rts */
}

/* lo generado hasta un punto, para deshacer lo que venga después */
typedef struct { size_t code_n, data_n; int relocs_n, fixups_n, labels_n; long sink; } Mark;

static Mark mark(void)
{
    Mark m;
    m.code_n = obj->code.n;
    m.data_n = obj->data.n;
    m.relocs_n = obj->relocs.n;
    m.fixups_n = fixups.n;
    m.labels_n = labels.n;
    m.sink = sink_off;
    return m;
}

static void undo(Mark *m)
{
    obj->code.n = m->code_n;
    obj->data.n = m->data_n;
    obj->relocs.n = m->relocs_n;
    fixups.n = m->fixups_n;
    labels.n = m->labels_n;
    sink_off = m->sink;
}

static void gen_function(int label, Func *f, NodeList *body)
{
    Mark m = mark();
    int i, r;

    /* primera pasada: todo en el marco, contando usos */
    slot_reg.n = 0;
    frameless = 0;
    gen_function_pass(label, f, body);

    /* se deshace y se eligen los huecos más usados para d2-d7 */
    undo(&m);
    /* de más a menos usado: al primer registro libre durante toda su vida, desde que
       se asigna hasta su último uso (dos variables que no viven a la vez lo comparten) */
    for (i = 0; i < slot_reg.n; i++) slot_reg.v[i] = -1;
    for (;;) {
        int best = -1, j;
        for (i = 0; i < slot_uses.n; i++)
            if (slot_reg.v[i] == -1 && slot_uses.v[i] >= MIN_USES && (best < 0 || slot_uses.v[i] > slot_uses.v[best]))
                best = i;
        if (best < 0) break;
        slot_reg.v[best] = -2;                         /* visto: si no hay registro, al marco */
        for (r = 2; r < 2 + MAX_REGS; r++) {
            for (j = 0; j < slot_uses.n; j++)
                if (slot_reg.v[j] == r && slot_start.v[j] < slot_end.v[best] && slot_start.v[best] < slot_end.v[j])
                    break;
            if (j == slot_uses.n) {
                slot_reg.v[best] = r;
                break;
            }
        }
    }
    /* sin marco si todas las variables (no los parámetros) van en registros */
    frameless = 1;
    for (i = 0; i < slot_reg.n; i++) {
        if (slot_reg.v[i] < 0) slot_reg.v[i] = -1;
        if (slot_reg.v[i] < 0 && slot_off.v[i] < 0) frameless = 0;
    }
    gen_function_pass(label, f, body);
}

/* tamaño del árbol, y de paso cuántas veces se llama a cada función */
static int tree_size(Node *n);

static int list_size(NodeList *l)
{
    int i, s = 0;
    for (i = 0; i < l->n; i++) s += tree_size(l->v[i]);
    return s;
}

static int tree_size(Node *n)
{
    int idx;
    if (!n) return 0;
    if (n->kind == E_CALL && find_func(n->name, &idx)) call_sites[idx]++;
    return 1 + tree_size(n->a) + tree_size(n->b) + tree_size(n->c) +
           list_size(&n->args) + list_size(&n->body) + list_size(&n->els);
}

/* ¿se asigna a name en el árbol? */
static int assigns(Node *n, const char *name);

static int list_assigns(NodeList *l, const char *name)
{
    int i;
    for (i = 0; i < l->n; i++)
        if (assigns(l->v[i], name)) return 1;
    return 0;
}

static int assigns(Node *n, const char *name)
{
    if (!n) return 0;
    if ((n->kind == S_ASSIGN || n->kind == S_VAR || n->kind == S_FOR) && !strcmp(n->name, name)) return 1;
    return list_assigns(&n->body, name) || list_assigns(&n->els, name);
}

static void gen_one(int idx, int label, Func *f, NodeList *body)
{
    VEC_PUSH(inl_stack, idx);
    gen_function(label, f, body);
    inl_stack.n--;
}

void gen_program(Program *p, Obj *o)
{
    int i, main_label, fail, again;
    prog = p;
    obj = o;

    call_sites = xmalloc(sizeof(int) * (p->funcs.n + 1));
    body_size = xmalloc(sizeof(int) * (p->funcs.n + 1));
    needed = xmalloc(sizeof(int) * (p->funcs.n + 1));
    param_set = xmalloc(sizeof(*param_set) * (p->funcs.n + 1));
    list_size(&p->main);
    for (i = 0; i < p->funcs.n; i++) {
        Func *f = &p->funcs.v[i];
        int j;
        body_size[i] = list_size(&f->body);
        param_set[i] = xmalloc(f->params.n + 1);
        for (j = 0; j < f->params.n; j++) param_set[i][j] = (unsigned char)list_assigns(&f->body, f->params.v[j].name);
    }

    func_label = xmalloc(sizeof(int) * (p->funcs.n + 1));
    for (i = 0; i < p->funcs.n; i++) {
        int j;
        for (j = 0; j < i; j++)
            if (!strcmp(p->funcs.v[i].name, p->funcs.v[j].name))
                fatal_at(p->funcs.v[i].line, p->funcs.v[i].col, "la función %s ya existe", p->funcs.v[i].name);
        func_label[i] = new_label();
    }

    /* globales: sus valores iniciales van en el hunk de datos */
    global_type = xmalloc(sizeof(int) * (p->globals.n + 1));
    for (i = 0; i < p->globals.n; i++) {
        long v;
        Global *g = &p->globals.v[i];
        if (!fold(g->init, &v))
            fatal_at(g->line, g->col, "dashc (prueba): el valor inicial de %s tiene que ser un número fijo", g->name);
        global_type[i] = g->type;
        buf_long(&o->data, (uint32_t)v);
    }

    /* arranque: guarda registros, abre lo necesario, ejecuta Main y sale */
    main_label = new_label();
    fail = new_label();
    w(0x48E7); w(0x3F3E);                              /* movem.l d2-d7/a2-a6,-(sp) */
    jsr_sym("__dash_init");
    w(0x4A80);                                         /* tst.l d0 */
    branch(CC_NE, fail);
    jsr_label(main_label);
    jsr_sym("__dash_exit");
    w(0x7000);                                         /* moveq #0,d0 */
    def_label(fail);
    w(0x4CDF); w(0x7CFC);                              /* movem.l (sp)+,d2-d7/a2-a6 */
    w(0x4E75);                                         /* rts */

    /* Main y las funciones a las que se llama de verdad (no copiadas) */
    gen_one(-1, main_label, NULL, &p->main);
    do {
        again = 0;
        for (i = 0; i < p->funcs.n; i++)
            if (needed[i] == 1) {
                needed[i] = 2;
                gen_one(i, func_label[i], &p->funcs.v[i], &p->funcs.v[i].body);
                again = 1;
            }
    } while (again);
    /* las demás no van en el ejecutable, pero se generan y se tiran para dar sus errores */
    for (i = 0; i < p->funcs.n; i++)
        if (!needed[i]) {
            Mark m = mark();
            int *saved = xmalloc(sizeof(int) * (p->funcs.n + 1));
            memcpy(saved, needed, sizeof(int) * p->funcs.n);
            gen_one(i, func_label[i], &p->funcs.v[i], &p->funcs.v[i].body);
            undo(&m);
            labels.v[func_label[i]] = -1;
            memcpy(needed, saved, sizeof(int) * p->funcs.n);
            free(saved);
        }
    resolve_fixups();
}
