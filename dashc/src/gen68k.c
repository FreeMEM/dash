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
static uint32_t dead_at = (uint32_t)-1;       /* después de un bra: hasta la próxima etiqueta no se llega */
static uint32_t d0_loaded = (uint32_t)-1;     /* dónde acaba el último move/moveq a d0 */
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
typedef struct { char *name; int slot, type, depth, frame; long val; int ranged; long lo, hi; } Local;
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
static int pass;     /* 1: contando usos; 2: con los registros ya repartidos */
static struct { int *v; int n, cap; } inl_stack;   /* funciones que se están generando o copiando */

/* Expresiones que se leen de un hueco en vez de calcularse: i * k en un for (el hueco
   suma paso * k en cada vuelta) y las constantes grandes de la condición de un bucle
   (need_reg: solo si el hueco tiene registro; si no, se usa la constante). */
typedef struct { Node *n; int slot, need_reg; } Repl;
static struct { Repl *v; int n, cap; } repls;

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

/* ¿los códigos de condición ya comparan v con 0 para la condición cc? */
static int flags_for(Var *v, int cc)
{
    return v->kind == V_REG && flags_at == obj->code.n && flags_reg == v->reg &&
           (flags_full || cc == CC_EQ || cc == CC_NE);
}

static int fold(Node *n, long *v);
static int fold_literal;   /* fold sin las variables que valen una constante */

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

/* Un hueco nuevo; en la segunda pasada los huecos salen en el mismo orden. Uno
   opcional (opt) solo se usa si le toca registro: nunca ocupa sitio en el marco. */
static int new_slot_opt(int param_off, int opt)
{
    int slot = slot_uses.n;
    VEC_PUSH(slot_uses, 0);
    VEC_PUSH(slot_start, ++event);
    VEC_PUSH(slot_end, event);
    if (slot >= slot_reg.n) VEC_PUSH(slot_reg, -1);
    if (param_off) {
        VEC_PUSH(slot_off, param_off);
    } else if (slot_reg.v[slot] >= 0 || opt) {
        VEC_PUSH(slot_off, 0);
    } else {
        VEC_PUSH(slot_off, -4 * ++nframe);
    }
    return slot;
}

static int new_slot(int param_off) { return new_slot_opt(param_off, 0); }

/* n se lee de un hueco (ver Repl) */
static int repl_var(Node *n, Var *v)
{
    int i;
    for (i = repls.n - 1; i >= 0; i--)
        if (repls.v[i].n == n) {
            Repl *r = &repls.v[i];
            if (r->need_reg && pass == 2 && slot_reg.v[r->slot] < 0) return 0;
            use_slot(r->slot);
            *v = slot_var(r->slot, TY_INT);
            return 1;
        }
    return 0;
}

static int is_repl(Node *n)
{
    int i;
    for (i = 0; i < repls.n; i++)
        if (repls.v[i].n == n) return 1;
    return 0;
}

static void add_repl(Node *n, int slot, int need_reg)
{
    Repl r;
    r.n = n;
    r.slot = slot;
    r.need_reg = need_reg;
    VEC_PUSH(repls, r);
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
    lc.ranged = 0;
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
            if (lc->slot >= 0 || fold_literal) return 0;
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
    else flags_set(reg, 1);
}

static void load_var(int reg, Var *v)
{
    if (v->kind == V_CONST) load_imm(reg, v->val);
    else if (!(v->kind == V_REG && v->reg == reg)) {
        op_ea(0x2000 | reg << 9, v);                   /* move.l v,dN */
        if (reg == 0) d0_loaded = (uint32_t)obj->code.n;
        else flags_set(reg, 1);
    }
}

/* Si lo último fue move.l dX,d0 (con X de 2 a 7) y no se llega ahí desde otro sitio,
   lo quita y devuelve X: quien iba a usar d0 puede usar dX. Si no, -1. */
static int take_move_to_d0(void)
{
    uint8_t *p = obj->code.p + obj->code.n - 2;
    int x, i;
    if (d0_loaded != obj->code.n || obj->code.n < 2 || p[0] != 0x20 || (p[1] & 0xF8) != 0) return -1;
    x = p[1] & 7;
    if (x < 2) return -1;
    for (i = 0; i < labels.n; i++)                     /* una etiqueta de justo detrás */
        if (labels.v[i] == (long)obj->code.n) labels.v[i] -= 2;
    obj->code.n -= 2;
    d0_loaded = (uint32_t)-1;
    return x;
}

static void store_d0(Var *v)
{
    if (v->kind == V_REG) {
        w(0x2000 | v->reg << 9);                       /* move.l d0,dN */
        flags_set(v->reg, 1);
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
    if (k && v->kind == V_REG) flags_set(v->reg, 0);
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
/* el tipo de una expresión que se sabe al compilar */
static int fold_type(Node *n)
{
    if (n->kind == E_BOOL) return TY_BOOL;
    if (n->kind == E_VAR) return lookup(n->name).type;   /* una constante: no cuenta como uso */
    return TY_INT;
}

static int simple(Node *n, Var *v)
{
    long k;
    if (repl_var(n, v)) return 1;
    if (fold(n, &k)) {
        v->kind = V_CONST;
        v->val = k;
        v->type = fold_type(n);
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

/* d0 = d0 * k; src: un registro que ya tiene el valor de d0 (-1: ninguno) */
static void mul_const(long k, int src)
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
        if (src < 0) {
            w(0x2200);                                 /* move.l d0,d1 */
            src = 1;
        }
        shift_d0(1, a - b);
        w(0xD080 | src);                               /* add.l dsrc,d0 */
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

/* d0 = d0 / k o d0 % k, con 1 < k <= 65535: un divu.w si el dividendo es >= 0 y el
   cociente cabe en 16 bits (como el camino rápido del runtime, sin la llamada).
   El camino rápido es el del salto: un salto tomado cuesta menos que uno no tomado
   y un bra. */
static void divmod_const(int op, long k)
{
    int load = k <= 127 ? 2 : 6;                       /* moveq o move.l #k,d1 */
    w(0xB0BC); l(((uint32_t)k << 16) - 1);             /* cmp.l #(k << 16) - 1,d0 */
    w(0x6300 | (load + 8));                            /* bls.s rápido (sin signo: un negativo es enorme) */
    load_imm(1, k);
    jsr_sym(op == P_SLASH ? "__dash_divk" : "__dash_modk");   /* sin volver a probar el divu.w */
    w(op == P_SLASH ? 0x600A : 0x6008);                /* bra.s fin */
    w(0x80FC); w((int)k);                              /* rápido: divu.w #k,d0, resto:cociente */
    if (op == P_SLASH) { w(0x4840); w(0x4240); w(0x4840); }   /* swap; clr.w; swap: el cociente */
    else { w(0x4240); w(0x4840); }                     /* clr.w; swap: el resto */
}

/* d0 = d0 / d1 o d0 % d1: divu.w si 1 <= d1 <= 32767 y la parte alta de d0 es menor
   que d1 (eso ya dice que d0 >= 0 y que el cociente cabe en 16 bits); si no, el runtime */
static void divmod_d1(int op)
{
    int x = op == P_SLASH ? 6 : 4;                     /* lo que saca el cociente o el resto */
    w(0xB2BC); l(0x7FFF);                              /* cmp.l #$7FFF,d1 */
    w(0x6200 | (18 + x));                              /* bhi.s lento (también los negativos) */
    w(0x4A41);                                         /* tst.w d1 */
    w(0x6700 | (14 + x));                              /* beq.s lento */
    w(0x4840); w(0xB041);                              /* swap d0; cmp.w d1,d0 */
    w(0x6400 | (6 + x));                               /* bcc.s lento_swap */
    w(0x4840); w(0x80C1);                              /* swap d0; divu.w d1,d0 */
    if (op == P_SLASH) { w(0x4840); w(0x4240); w(0x4840); }   /* swap; clr.w; swap: el cociente */
    else { w(0x4240); w(0x4840); }                     /* clr.w; swap: el resto */
    w(0x6008);                                         /* bra.s fin */
    w(0x4840);                                         /* lento_swap: swap d0 */
    jsr_sym(op == P_SLASH ? "__dash_div" : "__dash_mod");   /* lento */
}

/* d0 = d0 * d1: muls.w si los dos caben en 16 bits con signo; si no, el runtime */
static void mul_d1(void)
{
    w(0x3040); w(0xB088); w(0x6606);                   /* movea.w d0,a0; cmp.l a0,d0; bne.s lento */
    w(0x3041); w(0xB288); w(0x6708);                   /* movea.w d1,a0; cmp.l a0,d1; beq.s rápido */
    jsr_sym("__dash_mul");                             /* lento */
    w(0x6002);                                         /* bra.s fin */
    w(0xC1C1);                                         /* rápido: muls.w d1,d0 */
}

/* d0 = d0 * d0 */
static void square_d0(void)
{
    w(0x3040); w(0xB088); w(0x670A);                   /* movea.w d0,a0; cmp.l a0,d0; beq.s rápido */
    w(0x2200);                                         /* move.l d0,d1 */
    jsr_sym("__dash_mul");
    w(0x6002);                                         /* bra.s fin */
    w(0xC1C0);                                         /* rápido: muls.w d0,d0 */
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
            mul_const(k, -1);
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
            if (k > 1 && k <= 65535) {
                divmod_const(op, k);
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
    case P_STAR: mul_d1(); break;
    case P_SLASH:
    case P_PERCENT:
        if (loop_weight > 1) divmod_d1(op);            /* en un bucle, el camino rápido aquí */
        else jsr_sym(op == P_SLASH ? "__dash_div" : "__dash_mod");
        break;
    }
}

static int commutative(int op)
{
    return op == P_PLUS || op == P_STAR || op == P_AMP || op == P_BAR || op == P_CARET;
}

static NodeList *cur_body(void);
static long step_of(Node *s, const char *v);

/* Una variable que solo se asigna con valores fijos o sumándole algo positivo nunca
   baja del menor de esos valores (como gcc, se da por hecho que no se desborda) */
static int monotone(NodeList *l, const char *name, long *lo)
{
    int i;
    long k;
    for (i = 0; i < l->n; i++) {
        Node *s = l->v[i];
        if ((s->kind == S_ASSIGN || s->kind == S_VAR || s->kind == S_FOR) && !strcmp(s->name, name)) {
            if (s->kind == S_FOR) return 0;
            if (fold(s->a, &k)) {
                if (k < *lo) *lo = k;
            } else if (step_of(s, name) <= 0) {
                return 0;
            }
        }
        if (!monotone(&s->body, name, lo) || !monotone(&s->els, name, lo)) return 0;
    }
    return 1;
}

/* entre qué valores está n, si se sabe */
static int var_range(Node *n, long *lo, long *hi)
{
    Local *lc;
    int idx, i;
    if (fold(n, lo)) {
        *hi = *lo;
        return 1;
    }
    if (n->kind != E_VAR || !(lc = find_local(n->name)) || lc->slot < 0) return 0;
    if (lc->ranged) {
        *lo = lc->lo;
        *hi = lc->hi;
        return 1;
    }
    /* un parámetro empieza con un valor que no se sabe */
    idx = inl_stack.v[inl_stack.n - 1];
    if (idx >= 0)
        for (i = 0; i < prog->funcs.v[idx].params.n; i++)
            if (!strcmp(prog->funcs.v[idx].params.v[i].name, n->name)) return 0;
    *lo = INT32_MAX;
    if (!monotone(cur_body(), n->name, lo) || *lo == INT32_MAX) return 0;
    *hi = INT32_MAX;
    return 1;
}

/* con rangos conocidos: sin comprobar si cabe en 16 bits */
static int gen_ranged(Node *n)
{
    long k, alo, ahi, blo, bhi;
    Var v;
    int op = n->op;
    if (!var_range(n->a, &alo, &ahi)) return 0;
    if ((op == P_SLASH || op == P_PERCENT) && alo >= 0 && fold(n->b, &k) && k > 1 && k <= 65535) {
        int s = pow2(k);
        if (!s && ahi >= (long)((uint32_t)k << 16)) return 0;   /* el cociente no cabe */
        value(n->a);
        if (s && op == P_SLASH) shift_d0(0, s);
        else if (s) { w(0x0280); l((uint32_t)k - 1); }  /* andi.l #k-1,d0 */
        else {
            w(0x80FC); w((int)k);                      /* divu.w #k,d0 */
            if (op == P_SLASH) { w(0x4840); w(0x4240); w(0x4840); }   /* swap; clr.w; swap */
            else { w(0x4240); w(0x4840); }             /* clr.w; swap */
        }
        d0_loaded = (uint32_t)obj->code.n;             /* los códigos dicen cómo es d0 */
        return 1;
    }
    if ((op == P_SLASH || op == P_PERCENT) && alo >= 0 && ahi <= 0xFFFF && !fold(n->b, &k) && loop_weight > 1) {
        /* dividendo de 16 bits: el cociente cabe; solo hace falta 1 <= divisor <= 65535 */
        int x = op == P_SLASH ? 6 : 4;
        value(n->a);
        if (simple(n->b, &v)) {
            load_var(1, &v);
        } else {
            push_d0();
            value(n->b);
            w(0x2200);                                 /* move.l d0,d1 */
            pop_d0();
        }
        if (!var_range(n->b, &blo, &bhi)) blo = -1, bhi = INT32_MAX;
        if (blo >= 1 && bhi <= 0xFFFF) {
            w(0x80C1);                                 /* divu.w d1,d0 */
            if (op == P_SLASH) { w(0x4840); w(0x4240); w(0x4840); }
            else { w(0x4240); w(0x4840); }
            d0_loaded = (uint32_t)obj->code.n;
            return 1;
        }
        w(0xB2BC); l(0xFFFF);                          /* cmp.l #$FFFF,d1 */
        if (blo >= 1) {
            w(0x6200 | (4 + x));                       /* bhi.s lento; el divisor no es 0 */
        } else {
            w(0x6200 | (8 + x));                       /* bhi.s lento (también los negativos) */
            w(0x4A41);                                 /* tst.w d1 */
            w(0x6700 | (4 + x));                       /* beq.s lento */
        }
        w(0x80C1);                                     /* divu.w d1,d0 */
        if (op == P_SLASH) { w(0x4840); w(0x4240); w(0x4840); }
        else { w(0x4240); w(0x4840); }
        w(0x6006);                                     /* bra.s fin */
        jsr_sym(op == P_SLASH ? "__dash_div" : "__dash_mod");
        return 1;
    }
    if (op == P_STAR && alo >= -32768 && ahi <= 32767 && var_range(n->b, &blo, &bhi) &&
        blo >= -32768 && bhi <= 32767 && !fold(n->a, &k) && !fold(n->b, &k)) {
        value(n->a);
        simple(n->b, &v);
        if (v.kind != V_REG) {
            load_var(1, &v);
            v.kind = V_REG;
            v.reg = 1;
        }
        w(0xC1C0 | v.reg);                             /* muls.w dN,d0 */
        return 1;
    }
    return 0;
}

static void gen_binary(Node *n)
{
    Var v;
    Node *x;
    long k;
    if (gen_ranged(n)) return;
    if (n->op == P_STAR && n->a->kind == E_VAR && n->b->kind == E_VAR && !strcmp(n->a->name, n->b->name) &&
        !fold(n->a, &k)) {
        value(n->a);                                   /* x * x */
        lookup(n->a->name);                            /* cuenta el segundo uso */
        square_d0();
    } else if ((n->op == P_AMP || n->op == P_BAR) && fold(n->b, &k) && k >= -128 && k <= 127 &&
               n->a->kind == E_VAR && simple(n->a, &v) && v.kind != V_CONST) {
        load_imm(0, k);                                /* x & 1: moveq #1,d0; and.l x,d0 */
        op_ea(n->op == P_AMP ? 0xC080 : 0x8080, &v);
    } else if (n->op == P_STAR && (fold(n->b, &k) ? (x = n->a) : fold(n->a, &k) ? (x = n->b) : NULL) &&
               x->kind == E_VAR && simple(x, &v) && v.kind == V_REG) {
        load_var(0, &v);                               /* x * k con x en un registro */
        mul_const(k, v.reg);
    } else if (commutative(n->op) && fold(n->a, &k) && !fold(n->b, &k)) {
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
        switch (n->op) {
        case P_PLUS: w(0xD09F); sp_depth -= 4; return;            /* add.l (sp)+,d0 */
        case P_AMP: w(0xC09F); sp_depth -= 4; return;             /* and.l (sp)+,d0 */
        case P_BAR: w(0x809F); sp_depth -= 4; return;             /* or.l (sp)+,d0 */
        case P_MINUS: w(0x909F); w(0x4480); sp_depth -= 4; return;   /* sub.l (sp)+,d0; neg.l d0 */
        case P_STAR: w(0x221F); sp_depth -= 4; mul_d1(); return;     /* move.l (sp)+,d1 */
        }
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
        uint32_t mask = (k < 0 ? 0u - (uint32_t)k : (uint32_t)k) - 1;
        if (n->a->a->kind == E_VAR && simple(n->a->a, &va) && va.kind != V_CONST) {
            if (mask == 1 && va.kind == V_REG) {
                w(0x0800 | va.reg); w(0);              /* btst #0,dN */
                return cc;
            }
            if (mask <= 127) {
                load_imm(0, (long)mask);
                op_ea(0xC080, &va);                    /* moveq #mask,d0; and.l x,d0 */
                return cc;
            }
            load_var(0, &va);
        } else {
            value(n->a->a);
        }
        w(0x0280); l(mask);                            /* andi.l #mask,d0 */
        return cc;
    }
    if (simple(n->b, &vb)) {
        if (vb.kind == V_CONST && n->a->kind == E_VAR && simple(n->a, &va) && va.kind != V_CONST) {
            if (vb.val == 0) {
                if (!flags_for(&va, cc)) op_ea(0x4A80, &va);   /* tst.l a */
            } else if (va.kind == V_REG && vb.val >= -128 && vb.val <= 127) {
                load_imm(0, vb.val);
                w(0xB080 | va.reg << 9);               /* moveq #k,d0; cmp.l d0,dA */
            } else {
                op_imm_ea(0x0C80, vb.val, &va);        /* cmpi.l #k,a */
            }
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

static struct { int *v; int n, cap; } sub_stack;  /* funciones de una línea puestas como expresión */

static int can_inline(int idx)
{
    int i;
    if (inl_stack.n + sub_stack.n >= INLINE_DEPTH) return 0;
    for (i = 0; i < inl_stack.n; i++)
        if (inl_stack.v[i] == idx) return 0;
    for (i = 0; i < sub_stack.n; i++)
        if (sub_stack.v[i] == idx) return 0;
    return body_size[idx] <= INLINE_SIZE || call_sites[idx] == 1;
}

/* Una función que solo es "return e" se pone como la expresión e con los argumentos en
   lugar de los parámetros: y = suma1(y) es y = y + 1. Vale si cada argumento es fijo,
   una variable, o se usa una vez y no llama a nada; y si los demás nombres de e (globales
   o constantes) no los tapa una variable del sitio de la llamada. */
static int count_refs(Node *n, const char *name)
{
    int i, c;
    if (!n) return 0;
    c = n->kind == E_VAR && !strcmp(n->name, name);
    for (i = 0; i < n->args.n; i++) c += count_refs(n->args.v[i], name);
    return c + count_refs(n->a, name) + count_refs(n->b, name) + count_refs(n->c, name);
}

static int param_index(Func *f, const char *name)
{
    int i;
    for (i = 0; i < f->params.n; i++)
        if (!strcmp(f->params.v[i].name, name)) return i;
    return -1;
}

static int subst_ok(Node *e, Func *f)
{
    int i;
    if (!e) return 1;
    if (e->kind == E_VAR && param_index(f, e->name) < 0 && find_local(e->name)) return 0;
    for (i = 0; i < e->args.n; i++)
        if (!subst_ok(e->args.v[i], f)) return 0;
    return subst_ok(e->a, f) && subst_ok(e->b, f) && subst_ok(e->c, f);
}

static Node *subst(Node *e, Func *f, NodeList *args)
{
    Node *c;
    int i;
    if (!e) return NULL;
    if (e->kind == E_VAR) {
        i = param_index(f, e->name);
        return i >= 0 ? args->v[i] : e;
    }
    c = xmalloc(sizeof *c);
    *c = *e;
    c->a = subst(e->a, f, args);
    c->b = subst(e->b, f, args);
    c->c = subst(e->c, f, args);
    if (e->args.n) {
        c->args.v = xmalloc(sizeof(Node *) * e->args.n);
        c->args.cap = e->args.n;
        for (i = 0; i < e->args.n; i++) c->args.v[i] = subst(e->args.v[i], f, args);
    }
    return c;
}

static int has_call(Node *n);

static Node *try_subst(Node *call, int *idx)
{
    Func *f;
    Node *e;
    int i;
    long k;
    if (call->kind != E_CALL || !(f = find_func(call->name, idx)) || call->args.n != f->params.n) return NULL;
    if (f->body.n != 1 || f->body.v[0]->kind != S_RETURN || !(e = f->body.v[0]->a)) return NULL;
    if (!can_inline(*idx) || !subst_ok(e, f)) return NULL;
    for (i = 0; i < call->args.n; i++) {
        Node *a = call->args.v[i];
        if (fold(a, &k) || a->kind == E_VAR) continue;
        if (count_refs(e, f->params.v[i].name) == 1 && !has_call(a)) continue;
        return NULL;
    }
    return subst(e, f, &call->args);
}

/* Una función copiada dentro de una condición (if f(x)) salta directamente a donde
   toque en cada return, sin pasar el valor por d0: ret_branch es la etiqueta a la que
   salta un return que vale ret_when (-1: los return dejan el valor en d0). */
static int ret_branch = -1, ret_when;

static int gen_inline(Node *n, Func *f, int idx, int branch_to, int when_true)
{
    int i, saved_frame = cur_frame, saved_ret = ret_label, saved_base = loop_base, frame = ++frame_count;
    int saved_branch = ret_branch, saved_when = ret_when;
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
        b->ranged = 0;
        if (!param_set[idx][i] && fold(a, &k)) {
            b->val = k;
            continue;
        }
        if (!param_set[idx][i] && a->kind == E_VAR && (src = find_local(a->name)) != NULL) {
            b->slot = src->slot;
            b->val = src->val;
            b->ranged = src->ranged;
            b->lo = src->lo;
            b->hi = src->hi;
            if (src->slot >= 0) use_slot(src->slot);
            continue;
        }
        {
            Var t, sv;
            int simple_arg = a->kind == E_VAR && simple(a, &sv) && sv.kind != V_CONST;
            if (!simple_arg) value(a);
            b->slot = new_slot(0);
            use_slot(b->slot);
            t = slot_var(b->slot, b->type);
            if (simple_arg && t.kind == V_REG) load_var(t.reg, &sv);   /* move.l x,dN */
            else {
                if (simple_arg) load_var(0, &sv);
                store_d0(&t);
            }
        }
    }
    cur_frame = frame;
    for (i = 0; i < n->args.n; i++) VEC_PUSH(locals, binds[i]);
    free(binds);
    ret_label = new_label();
    ret_branch = branch_to;
    ret_when = when_true;
    loop_base = loops.n;
    VEC_PUSH(inl_stack, idx);
    gen_block(&f->body);
    inl_stack.n--;
    def_label_fwd(ret_label);                          /* si solo se llega cayendo, d0 sigue valiendo */
    ret_label = saved_ret;
    ret_branch = saved_branch;
    ret_when = saved_when;
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
    if (can_inline(idx)) {
        Node *e = try_subst(n, &idx);
        if (e) {
            VEC_PUSH(sub_stack, idx);
            need_value(n, gen_expr(e));
            sub_stack.n--;
            return f->ret;                             /* el tipo de la función, no el de e */
        }
        return gen_inline(n, f, idx, -1, 0);
    }
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

    if (repl_var(n, &v)) {
        load_var(0, &v);
        return TY_INT;
    }
    if (n->kind != E_CMP && n->kind != E_AND && n->kind != E_OR && n->kind != E_NOT && fold(n, &k)) {
        load_imm(0, k);
        return fold_type(n);
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
    case E_CALL: {
        int idx;
        Func *f;
        Node *e = try_subst(n, &idx);
        if (e) {
            VEC_PUSH(sub_stack, idx);
            gen_branch(e, label, when_true);
            sub_stack.n--;
            return;
        }
        /* copiada en modo salto si acaba en "return valor" (así todo camino devuelve algo) */
        f = find_func(n->name, &idx);
        if (f && n->args.n == f->params.n && can_inline(idx) && f->body.n &&
            f->body.v[f->body.n - 1]->kind == S_RETURN && f->body.v[f->body.n - 1]->a) {
            gen_inline(n, f, idx, label, when_true);
            return;
        }
        break;
    }
    }
    if (fold(n, &k)) {
        if ((k != 0) == when_true) branch(CC_T, label);
        return;
    }
    if (n->kind == E_VAR && simple(n, &v)) {
        if (!flags_for(&v, CC_NE)) op_ea(0x4A80, &v);   /* tst.l v */
    }
    else {
        value(n);
        tst_d0();
    }
    branch(when_true ? CC_NE : CC_EQ, label);
}

/* ---- instrucciones ---- */
static void gen_block(NodeList *b);

static int list_assigns(NodeList *l, const char *name);
static int refs(Node *n, const char *name);
static int list_refs(NodeList *l, const char *name);

/* dbra dN,etiqueta */
static void dbra(int reg, int label)
{
    Fixup f;
    w(0x51C8 | reg);
    f.at = (uint32_t)obj->code.n;
    f.label = label;
    f.abs = 0;
    VEC_PUSH(fixups, f);
    w(0);
}

/* v = k */
static void set_imm(Var *v, long k)
{
    if (v->kind == V_REG) load_imm(v->reg, k);
    else {
        load_imm(0, k);
        store_d0(v);
    }
}

static Var declare_slot(const char *name, int type, int *slot)
{
    Var v = declare(name, type);
    *slot = locals.v[locals.n - 1].slot;
    return v;
}

/* i * k en el cuerpo de un for, con k fijo y caro de multiplicar */
typedef struct { Node *n; long k; } Mult;
#define MAX_MULTS 16
#define MAX_SR 3

/* las variables de n no cambian en el cuerpo */
static int stable(Node *n, NodeList *body)
{
    if (!n) return 1;
    if (n->kind == E_VAR && list_assigns(body, n->name)) return 0;
    return stable(n->a, body) && stable(n->b, body);
}

static void find_mults(Node *n, const char *name, NodeList *body, Mult *m, int *nm)
{
    Node *o = NULL;
    long k;
    int i;
    if (!n || *nm >= MAX_MULTS) return;
    if (n->kind == E_BIN && n->op == P_STAR) {
        if (n->a->kind == E_VAR && !strcmp(n->a->name, name)) o = n->b;
        else if (n->b->kind == E_VAR && !strcmp(n->b->name, name)) o = n->a;
        if (o && fold(o, &k) && stable(o, body) && popcount(k < 0 ? 0u - (uint32_t)k : (uint32_t)k) >= 2) {
            m[*nm].n = n;
            m[*nm].k = k;
            (*nm)++;
            return;
        }
    }
    find_mults(n->a, name, body, m, nm);
    find_mults(n->b, name, body, m, nm);
    find_mults(n->c, name, body, m, nm);
    for (i = 0; i < n->args.n; i++) find_mults(n->args.v[i], name, body, m, nm);
    for (i = 0; i < n->body.n; i++) find_mults(n->body.v[i], name, body, m, nm);
    for (i = 0; i < n->els.n; i++) find_mults(n->els.v[i], name, body, m, nm);
}

/* Un for con el número de vueltas conocido al empezar (el cuerpo no cambia i) lleva
   un contador aparte que acaba con dbra, y el índice solo existe si el cuerpo lo lee.
   i * k se lleva sumando paso * k en un hueco. Si no, se compara i con el final. */
static void gen_for(Node *n)
{
    long from = 0, to = 0, step = 1, count = -1;
    int down = 0, top = new_label(), cont = new_label(), done = new_label(), test = -1;
    int step_known = 1, from_known, end_known, counted, use_i;
    int i_slot = -1, end_slot = -1, step_slot = -1, cnt_slot = -1, repl_base = repls.n;
    int nm = 0, nsr = 0, i, j;
    Mult m[MAX_MULTS];
    long sr_k[MAX_SR];
    int sr_slot[MAX_SR];
    Var vi, vend, vstep, vc, sr_v[MAX_SR];
    Loop lp;

    if (n->c && !fold(n->c, &step)) step_known = 0;
    if (step_known && step < 0) down = 1;
    from_known = fold(n->a, &from);
    end_known = fold(n->b, &to);
    /* sin paso, (5..1) cuenta hacia atrás si los dos extremos son literales o
       constantes (no variables, aunque se sepa su valor) */
    fold_literal = 1;
    if (!n->c && fold(n->a, &from) && fold(n->b, &to) && from > to) {
        down = 1;
        step = -1;
    }
    fold_literal = 0;
    fold(n->a, &from);
    fold(n->b, &to);
    if (step_known && step == 0) fatal_at(n->line, n->col, "el paso del for no puede ser 0");

    counted = step_known && !list_assigns(&n->body, n->name);
    if (counted && from_known && end_known) {
        long long c = 0;
        if (down ? from >= to : from <= to)
            c = down ? ((long long)from - to) / -step + 1 : ((long long)to - from) / step + 1;
        if (c < 1 || c > 0xFFFFFFFFLL) counted = 0;     /* ninguna vuelta: como siempre */
        else count = (long)c;
    } else if (counted && step != 1 && step != -1) {
        counted = 0;
    }

    enter_scope();
    if (step_known) {
        for (i = 0; i < n->body.n; i++) find_mults(n->body.v[i], n->name, &n->body, m, &nm);
        for (i = 0; i < nm; i++) {
            for (j = 0; j < nsr && sr_k[j] != m[i].k; j++)
                ;
            if (j == nsr) {
                if (nsr == MAX_SR) continue;
                sr_k[nsr++] = m[i].k;
            }
            add_repl(m[i].n, -1, 0);                   /* el hueco, más abajo */
        }
    }
    use_i = !counted || !from_known || refs(n->b, n->name) || (n->c && refs(n->c, n->name)) ||
            list_refs(&n->body, n->name);

    if (use_i) {
        if (!from_known) value(n->a);
        vi = declare_slot(n->name, TY_INT, &i_slot);
        if (from_known) set_imm(&vi, from);
        else store_d0(&vi);
        if (counted && from_known && end_known) {
            /* el cuerpo no cambia i: sus valores están entre los extremos */
            Local *lc = &locals.v[locals.n - 1];
            lc->ranged = 1;
            lc->lo = from < to ? from : to;
            lc->hi = from < to ? to : from;
        }
    }
    for (j = 0; j < nsr; j++) {
        sr_v[j] = declare_slot("", TY_INT, &sr_slot[j]);   /* "": no se puede nombrar */
        if (from_known) {
            set_imm(&sr_v[j], (long)(int32_t)((uint32_t)from * (uint32_t)sr_k[j]));
        } else {
            load_var(0, &vi);
            mul_const(sr_k[j], -1);
            store_d0(&sr_v[j]);
        }
    }
    for (i = repl_base; i < repls.n; i++) {
        Mult *mm = NULL;
        for (j = 0; j < nm; j++)
            if (m[j].n == repls.v[i].n) mm = &m[j];
        for (j = 0; j < nsr; j++)
            if (sr_k[j] == mm->k) repls.v[i].slot = sr_slot[j];
    }
    for (i = repl_base; i < repls.n; i++)
        if (repls.v[i].slot < 0) repls.v[i--] = repls.v[--repls.n];   /* sin hueco (más de MAX_SR) */

    if (counted) {
        if (count >= 0) {
            vc = declare_slot("", TY_INT, &cnt_slot);
            set_imm(&vc, count - 1);
        } else {
            /* vueltas - 1 = fin - inicio (o al revés); ninguna si es negativo */
            value(n->b);
            if (from_known) {
                if (from >= 1 && from <= 8) w(0x5180 | (from & 7) << 9);   /* subq.l #inicio,d0 */
                else if (from) { w(0x0480); l((uint32_t)from); }          /* subi.l #inicio,d0 */
                else tst_d0();
            } else {
                op_ea(0x9080, &vi);                    /* sub.l i,d0 */
            }
            branch(down ? CC_GT : CC_LT, done);
            if (down) w(0x4480);                       /* neg.l d0 */
            vc = declare_slot("", TY_INT, &cnt_slot);
            store_d0(&vc);
        }
    } else {
        if (end_known) {
            vend.kind = V_CONST;
            vend.val = to;
        } else {
            value(n->b);
            vend = declare_slot("", TY_INT, &end_slot);
            store_d0(&vend);
        }
        if (!step_known) {
            value(n->c);
            vstep = declare_slot("", TY_INT, &step_slot);
            store_d0(&vstep);
        }
    }

    enter_loop();
    /* las veces que se usan en cada vuelta: comparar, contar e incrementar */
    if (i_slot >= 0) use_slot(i_slot);
    if (end_slot >= 0) use_slot(end_slot);
    if (step_slot >= 0) use_slot(step_slot);
    if (cnt_slot >= 0) use_slot(cnt_slot);
    for (j = 0; j < nsr; j++) use_slot(sr_slot[j]);

    /* sin contador, la comparación va al final: una vuelta es cuerpo, incremento y un salto */
    if (!counted) {
        test = new_label();
        branch(CC_T, test);
    }
    def_label(top);
    lp.brk = done;
    lp.cont = cont;
    VEC_PUSH(loops, lp);
    gen_block(&n->body);
    loops.n--;

    def_label(cont);
    if (use_i) {
        if (!step_known) {
            if (vi.kind == V_REG) op_ea(0xD080 | vi.reg << 9, &vstep);  /* add.l paso,di */
            else {
                load_var(0, &vstep);
                op_ea(0xD180, &vi);                    /* add.l d0,i */
            }
        } else {
            add_imm_ea(step, &vi);
        }
    }
    for (j = 0; j < nsr; j++) add_imm_ea((long)(int32_t)((uint32_t)step * (uint32_t)sr_k[j]), &sr_v[j]);
    if (counted) {
        if (vc.kind == V_REG) {
            dbra(vc.reg, top);
            if (count < 0 || count > 65536) {
                /* más de 65536 vueltas: la parte alta del contador */
                w(0x0480 | vc.reg); l(0x10000);        /* subi.l #$10000,dN */
                branch(CC_CC, top);
            }
        } else {
            op_ea(0x5380, &vc);                        /* subq.l #1,contador */
            branch(CC_CC, top);
        }
    } else {
        def_label(test);
        if (vend.kind == V_CONST) op_imm_ea(0x0C80, vend.val, &vi);     /* cmpi.l #fin,i */
        else if (vi.kind == V_REG) op_ea(0xB080 | vi.reg << 9, &vend);  /* cmp.l fin,di */
        else {
            load_var(0, &vi);
            op_ea(0xB080, &vend);                      /* cmp.l fin,d0 */
        }
        branch(down ? CC_GE : CC_LE, top);
    }
    def_label(done);
    repls.n = repl_base;
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

/* ¿lee n la variable name? (lo que se lee de un hueco no cuenta) */
static int refs(Node *n, const char *name);

static int list_refs(NodeList *l, const char *name)
{
    int i;
    for (i = 0; i < l->n; i++)
        if (refs(l->v[i], name)) return 1;
    return 0;
}

static int refs(Node *n, const char *name)
{
    if (!n || is_repl(n)) return 0;
    if ((n->kind == E_VAR || n->kind == S_FOR) && !strcmp(n->name, name)) return 1;
    return refs(n->a, name) || refs(n->b, name) || refs(n->c, name) || list_refs(&n->args, name) ||
           list_refs(&n->body, name) || list_refs(&n->els, name);
}

static int has_call(Node *n)
{
    int i;
    if (!n) return 0;
    if (n->kind == E_CALL) return 1;
    for (i = 0; i < n->args.n; i++)
        if (has_call(n->args.v[i])) return 1;
    return has_call(n->a) || has_call(n->b) || has_call(n->c);
}

/* e como suma de términos con signo; self: si sale la variable name sumando (una vez) */
#define MAX_TERMS 16
static int collect_terms(Node *e, const char *name, Node **t, int *neg, int *nt, int sign, int *self)
{
    if (e->kind == E_BIN && (e->op == P_PLUS || e->op == P_MINUS))
        return collect_terms(e->a, name, t, neg, nt, sign, self) &&
               collect_terms(e->b, name, t, neg, nt, e->op == P_MINUS ? -sign : sign, self);
    if (e->kind == E_VAR && !strcmp(e->name, name) && sign > 0 && !*self) {
        *self = 1;
        return 1;
    }
    if (*nt >= MAX_TERMS) return 0;
    t[*nt] = e;
    neg[*nt] = sign < 0;
    (*nt)++;
    return 1;
}

/* v = v op t, con op = add, sub, and u or (índice en las tablas) */
static void op_into(int op, Var *v, Node *t)
{
    static const int to_reg[] = {0xD080, 0x9080, 0xC080, 0x8080};   /* op.l ea,dN */
    static const int to_mem[] = {0xD180, 0x9180, 0xC180, 0x8180};   /* op.l dN,ea */
    Var s;
    if (t && simple(t, &s) && s.kind != V_CONST) {
        if (v->kind == V_REG) {
            op_ea(to_reg[op] | v->reg << 9, &s);
            flags_set(v->reg, op >= 2);                /* and y or ponen V = 0 */
            return;
        }
        if (s.kind == V_REG) { op_ea(to_mem[op] | s.reg << 9, v); return; }
        load_var(0, &s);
    } else if (t) {
        int x;
        value(t);
        if ((x = take_move_to_d0()) >= 0) {             /* el valor está en dX: sin pasar por d0 */
            if (v->kind == V_REG) {
                w(to_reg[op] | v->reg << 9 | x);
                flags_set(v->reg, op >= 2);
            } else {
                op_ea(to_mem[op] | x << 9, v);
            }
            return;
        }
    }
    if (v->kind == V_REG) {
        w(to_reg[op] | v->reg << 9);
        flags_set(v->reg, op >= 2);
    } else {
        op_ea(to_mem[op], v);
    }
}

/* v = v op e: la operación directamente sobre la variable. Una suma de varios
   términos (v = v + a - b...) se hace término a término. */
static int gen_update(Node *n)
{
    Node *e = n->a, *other;
    Var v;
    long k;
    int op, kind = lookup_kind(n->name);
    if (e->kind != E_BIN) return 0;
    op = e->op;
    if (op == P_PLUS || op == P_MINUS) {
        Node *t[MAX_TERMS];
        int neg[MAX_TERMS], nt = 0, self = 0, i;
        if (!collect_terms(e, n->name, t, neg, &nt, 1, &self) || !self) return 0;
        for (i = 0; i < nt; i++)
            if (refs(t[i], n->name) || (kind != V_REG && kind != V_LOCAL && has_call(t[i]))) return 0;
        v = lookup(n->name);
        if (v.kind == V_NONE || v.kind == V_CONST) return 0;
        for (i = 0; i < nt; i++) {
            if (i) v = lookup(n->name);                /* cuenta cada uso */
            if (fold(t[i], &k)) add_imm_ea(neg[i] ? (long)(int32_t)(0u - (uint32_t)k) : k, &v);
            else op_into(neg[i], &v, t[i]);
        }
        return 1;
    }
    if (e->a->kind == E_VAR && !strcmp(e->a->name, n->name)) other = e->b;
    else if (commutative(op) && e->b->kind == E_VAR && !strcmp(e->b->name, n->name)) other = e->a;
    else return 0;
    if (op == P_SLASH && kind == V_REG && fold(other, &k) && k > 1 && pow2(k) && pow2(k) <= 8) {
        /* x = x / 2^s en su registro: redondea hacia cero como divmod_pow2 */
        int sh = pow2(k);
        uint32_t mask = (1u << sh) - 1;
        v = lookup(n->name);
        if (!flags_for(&v, CC_PL)) w(0x4A80 | v.reg);  /* tst.l dN */
        if (mask <= 8) {
            w(0x6A02);                                 /* bpl.s +2 */
            w(0x5080 | (mask & 7) << 9 | v.reg);       /* addq.l #mask,dN */
        } else {
            w(0x6A06);                                 /* bpl.s +6 */
            w(0x0680 | v.reg); l(mask);                /* addi.l #mask,dN */
        }
        w(0xE080 | (sh & 7) << 9 | v.reg);             /* asr.l #s,dN */
        flags_set(v.reg, 1);
        return 1;
    }
    if (op == P_CARET || op == P_SHL || op == P_SHR) {
        /* solo con una constante; los desplazamientos, solo en un registro */
        if (!fold(other, &k)) return 0;
        if (op != P_CARET && (kind != V_REG || k < 1 || k > 8)) return 0;
    } else if (op != P_AMP && op != P_BAR) {
        return 0;
    }
    if (refs(other, n->name)) return 0;
    v = lookup(n->name);
    if (v.kind == V_NONE || v.kind == V_CONST) return 0;
    if (fold(other, &k)) {
        switch (op) {
        case P_AMP: op_imm_ea(0x0280, k, &v); break;               /* andi.l #k,v */
        case P_BAR: op_imm_ea(0x0080, k, &v); break;               /* ori.l #k,v */
        case P_CARET: op_imm_ea(0x0A80, k, &v); break;             /* eori.l #k,v */
        case P_SHL: w(0xE180 | (k & 7) << 9 | v.reg); break;       /* asl.l #k,dN */
        case P_SHR: w(0xE080 | (k & 7) << 9 | v.reg); break;       /* asr.l #k,dN */
        }
        if (v.kind == V_REG) flags_set(v.reg, op != P_SHL);        /* asl puede poner V */
        return 1;
    }
    op_into(op == P_AMP ? 2 : 3, &v, other);
    return 1;
}

/* Las constantes grandes (sin moveq) que se comparan en la condición de un bucle van
   en un registro antes de empezar, si queda alguno: cmp.l dN,dM en vez de cmpi.l. */
static void hoist_consts(Node *c)
{
    long k;
    Node *side;
    if (c->kind == E_NOT) hoist_consts(c->a);
    if (c->kind == E_AND || c->kind == E_OR) {
        hoist_consts(c->a);
        hoist_consts(c->b);
    }
    if (c->kind != E_CMP) return;
    if (fold(c->b, &k) && !fold(c->a, &k)) side = c->b;
    else if (fold(c->a, &k) && !fold(c->b, &k)) side = c->a;
    else return;
    fold(side, &k);
    if (k >= -128 && k <= 127) return;
    {
        int slot = new_slot_opt(0, 1);
        if (pass == 2 && slot_reg.v[slot] >= 0) load_imm(slot_reg.v[slot], k);
        add_repl(side, slot, 1);
    }
}

/* veces que se asigna a name en el cuerpo (un for también asigna) */
static int count_assigns(NodeList *l, const char *name)
{
    int i, c = 0;
    for (i = 0; i < l->n; i++) {
        Node *n = l->v[i];
        if ((n->kind == S_ASSIGN || n->kind == S_VAR || n->kind == S_FOR) && !strcmp(n->name, name)) c++;
        c += count_assigns(&n->body, name) + count_assigns(&n->els, name);
    }
    return c;
}

/* el cuerpo de la función que se está generando o copiando */
static NodeList *cur_body(void)
{
    int idx = inl_stack.v[inl_stack.n - 1];
    return idx < 0 ? &prog->main : &prog->funcs.v[idx].body;
}

static int lookup_global(const char *name)
{
    int i;
    for (i = 0; i < prog->globals.n; i++)
        if (!strcmp(prog->globals.v[i].name, name)) return 1;
    for (i = 0; i < prog->consts.n; i++)
        if (!strcmp(prog->consts.v[i].name, name)) return 1;
    return 0;
}

static int has_continue(NodeList *l)
{
    int i;
    for (i = 0; i < l->n; i++)
        if (l->v[i]->kind == S_CONTINUE || has_continue(&l->v[i]->body) || has_continue(&l->v[i]->els)) return 1;
    return 0;
}

/* ¿es s "v = v + d" (o v - d, d + v) con d fijo? Devuelve d (0 si no) */
static long step_of(Node *s, const char *v)
{
    Node *e = s->a;
    long d;
    if (s->kind != S_ASSIGN || strcmp(s->name, v) || e->kind != E_BIN) return 0;
    if (e->op == P_PLUS && e->a->kind == E_VAR && !strcmp(e->a->name, v) && fold(e->b, &d)) return d;
    if (e->op == P_PLUS && e->b->kind == E_VAR && !strcmp(e->b->name, v) && fold(e->a, &d)) return d;
    if (e->op == P_MINUS && e->a->kind == E_VAR && !strcmp(e->a->name, v) && fold(e->b, &d)) return -d;
    return 0;
}

static void gen_block(NodeList *b);

/* while v < fin con un solo "v = v + 1" en el cuerpo (fuera de los if) y sin continue:
   cada vuelta suma 1, así que las vueltas (fin - v) se saben al entrar y el bucle acaba
   con dbra, como un for. Igual con v > fin y v = v - 1, y con <= y >=. Solo si el
   contador tiene registro; si no, devuelve 0 sin haber generado nada. */
static int gen_counted_while(Node *n)
{
    Node *c = n->a, *vn, *end;
    Local *lc;
    long k;
    int op, up, i, inc = 0, slot, top, done;
    Var vv, vc;
    Loop lp;
    if (c->kind != E_CMP) return 0;
    op = c->op;
    /* v es el lado que cambia en el cuerpo */
    if (c->a->kind == E_VAR && !fold(c->a, &k) && count_assigns(&n->body, c->a->name) == 1) {
        vn = c->a;
        end = c->b;
    } else if (c->b->kind == E_VAR && !fold(c->b, &k)) {
        vn = c->b;
        end = c->a;
        op = op == P_LT ? P_GT : op == P_GT ? P_LT : op == P_LE ? P_GE : op == P_GE ? P_LE : op;
    } else {
        return 0;
    }
    if (op != P_LT && op != P_LE && op != P_GT && op != P_GE) return 0;
    up = op == P_LT || op == P_LE;
    if (!(lc = find_local(vn->name)) || lc->slot < 0) return 0;
    if (!fold(end, &k)) {
        Local *le;
        if (end->kind != E_VAR || !(le = find_local(end->name)) || le->slot < 0 ||
            list_assigns(&n->body, end->name) || !strcmp(end->name, vn->name)) return 0;
    }
    if (count_assigns(&n->body, vn->name) != 1 || has_continue(&n->body)) return 0;
    for (i = 0; i < n->body.n; i++)
        if (step_of(n->body.v[i], vn->name) == (up ? 1 : -1)) inc = 1;
    if (!inc) return 0;

    slot = new_slot_opt(0, 1);
    if (pass == 2 && slot_reg.v[slot] < 0) return 0;
    top = new_label();
    done = new_label();
    /* vueltas - 1: fin - v (- 1 con <) o v - fin (- 1 con >); ninguna si no llega */
    value(end);
    simple(vn, &vv);
    op_ea(0x9080, &vv);                                /* sub.l v,d0: fin - v */
    switch (op) {
    case P_LT: branch(CC_LE, done); w(0x5380); break;          /* subq.l #1,d0 */
    case P_LE: branch(CC_LT, done); break;
    case P_GT: branch(CC_GE, done); w(0x4480); w(0x5380); break;   /* neg.l d0; subq.l #1,d0 */
    default: branch(CC_GT, done); w(0x4480); break;            /* neg.l d0 */
    }
    vc = slot_var(slot, TY_INT);
    store_d0(&vc);
    use_slot(slot);
    enter_loop();
    use_slot(slot);
    def_label(top);
    lp.brk = done;
    lp.cont = -1;                                      /* no hay continue */
    VEC_PUSH(loops, lp);
    enter_scope();
    gen_block(&n->body);
    leave_scope();
    loops.n--;
    use_slot(slot);
    if (vc.kind == V_REG) {
        dbra(vc.reg, top);
        w(0x0480 | vc.reg); l(0x10000);                /* subi.l #$10000,dN: más de 65536 vueltas */
        branch(CC_CC, top);
    }
    def_label(done);
    leave_loop();
    return 1;
}

static int forced_type = -1;   /* el tipo de una función de una línea puesta como expresión */

static void gen_stmt(Node *n)
{
    Var v;
    long k;
    int ty, forced = forced_type;
    forced_type = -1;
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
        if (n->kind == S_ASSIGN && n->a->kind == E_CALL) {
            int idx;
            Node *e = try_subst(n->a, &idx), tmp;
            if (e) {
                tmp = *n;
                tmp.a = e;
                VEC_PUSH(sub_stack, idx);
                forced_type = prog->funcs.v[idx].ret;
                gen_stmt(&tmp);
                sub_stack.n--;
                return;
            }
        }
        if (n->kind == S_ASSIGN && gen_update(n)) return;
        if (fold(n->a, &k) && lookup_kind(n->name) == V_GLOBAL && !lookup_global(n->name) &&
            count_assigns(cur_body(), n->name) == 1) {
            /* una variable que solo se asigna una vez, con un valor fijo, es una constante */
            Local lc;
            lc.name = n->name;
            lc.slot = -1;
            lc.type = n->kind == S_VAR ? n->type : forced >= 0 ? forced : fold_type(n->a);
            lc.depth = depth;
            lc.frame = cur_frame;
            lc.val = k;
            lc.ranged = 0;
            VEC_PUSH(locals, lc);
            return;
        }
        if (n->kind == S_ASSIGN && fold(n->a, &k)) {
            v = lookup(n->name);
            if (v.kind == V_NONE) v = declare(n->name, forced >= 0 ? forced : fold_type(n->a));
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
        if (forced >= 0) ty = forced;
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
        int top, test, done, base = repls.n, slots = slot_uses.n;
        if (gen_counted_while(n)) return;
        top = new_label();
        test = new_label();
        done = new_label();
        /* si gen_counted_while no ha podido en la segunda pasada, no se suben constantes:
           los huecos tienen que salir en el mismo orden que en la primera */
        if (slot_uses.n == slots) hoist_consts(n->a);
        enter_loop();
        /* La condición va al final. Si es barata, también al entrar (en vez de saltar
           al final): así al final solo se llega desde el cuerpo y su última instrucción
           puede servir de comparación. */
        if (has_call(n->a)) branch(CC_T, test);
        else gen_branch(n->a, done, 0);
        def_label(top);
        lp.brk = done;
        lp.cont = test;
        VEC_PUSH(loops, lp);
        enter_scope();
        gen_block(&n->body);
        leave_scope();
        loops.n--;
        def_label_fwd(test);
        gen_branch(n->a, top, 1);
        def_label(done);
        repls.n = base;
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
        if (n->a && ret_branch >= 0) gen_branch(n->a, ret_branch, ret_when);
        else if (n->a) value(n->a);
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
    ret_branch = -1;

    /* cada registro una vez, aunque lo compartan varias variables */
    for (i = 0; i < slot_reg.n; i++)
        if (slot_reg.v[i] >= 0 && !(mask_pop & 1 << slot_reg.v[i])) {
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
            lc.ranged = 0;
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
    pass = 1;
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
    pass = 2;
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
