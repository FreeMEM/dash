/* Generador de código 68000. Cada expresión deja su valor en d0; un operando que
   no es simple se guarda en la pila mientras se calcula el otro. Las funciones usan
   un marco con a5 (link/unlk): los parámetros en 8(a5), 12(a5)... y las variables
   en -4(a5), -8(a5)... Se llaman como en C (argumentos en la pila, de derecha a
   izquierda, resultado en d0), así que el runtime de gcc se llama igual. */
#include <string.h>

#include "dashc.h"

/* códigos de condición del 68000 */
enum { CC_T = 0, CC_F, CC_HI, CC_LS, CC_CC, CC_CS, CC_NE, CC_EQ, CC_VC, CC_VS,
       CC_PL, CC_MI, CC_GE, CC_LT, CC_GT, CC_LE };

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

static void def_label(int l) { labels.v[l] = (long)obj->code.n; }

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
typedef struct { char *name; int off, type, depth; } Local;
static struct { Local *v; int n, cap; } locals;
static int depth, nslots;

typedef struct { int brk, cont; } Loop;
static struct { Loop *v; int n, cap; } loops;

static int *func_label;   /* etiqueta de cada función */
static int *global_type;
static Func *cur;
static int ret_label;

enum { V_NONE, V_LOCAL, V_GLOBAL, V_CONST };
typedef struct { int kind, off, type; long val; } Var;

static int fold(Node *n, long *v);

static Var lookup(const char *name)
{
    Var r = {V_NONE, 0, TY_INT, 0};
    int i;
    for (i = locals.n - 1; i >= 0; i--)
        if (!strcmp(locals.v[i].name, name)) {
            r.kind = V_LOCAL;
            r.off = locals.v[i].off;
            r.type = locals.v[i].type;
            return r;
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

static int declare(const char *name, int type)
{
    Local lc;
    lc.name = (char *)name;
    lc.off = -4 * ++nslots;
    lc.type = type;
    lc.depth = depth;
    VEC_PUSH(locals, lc);
    return lc.off;
}

static void enter_scope(void) { depth++; }

static void leave_scope(void)
{
    depth--;
    while (locals.n && locals.v[locals.n - 1].depth > depth) locals.n--;
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
        int i;
        for (i = locals.n - 1; i >= 0; i--)
            if (!strcmp(locals.v[i].name, n->name)) return 0;
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
        *v = arith(n->op, (int32_t)a, (int32_t)b, n);
        return 1;
    }
    return 0;
}

/* ---- carga y guardado ---- */
static void load_imm(int reg, long v)
{
    int32_t x = (int32_t)v;
    if (x >= -128 && x <= 127) {
        w(0x7000 | reg << 9 | (x & 0xFF));            /* moveq #x,dN */
    } else {
        w(0x203C | reg << 9);                          /* move.l #x,dN */
        l((uint32_t)x);
    }
}

static void load_var(int reg, Var *v)
{
    if (v->kind == V_LOCAL) {
        w(0x202D | reg << 9);                          /* move.l off(a5),dN */
        w(v->off);
    } else if (v->kind == V_GLOBAL) {
        w(0x2039 | reg << 9);                          /* move.l global,dN */
        add_reloc((uint32_t)obj->code.n, HK_DATA, NULL);
        l((uint32_t)v->off);
    } else {
        load_imm(reg, v->val);
    }
}

static void store_d0(Var *v)
{
    if (v->kind == V_LOCAL) {
        w(0x2B40);                                     /* move.l d0,off(a5) */
        w(v->off);
    } else {
        w(0x23C0);                                     /* move.l d0,global */
        add_reloc((uint32_t)obj->code.n, HK_DATA, NULL);
        l((uint32_t)v->off);
    }
}

static void push_d0(void) { w(0x2F00); }               /* move.l d0,-(sp) */

static void pop_args(int n)
{
    int bytes = n * 4;
    if (!bytes) return;
    if (bytes <= 8) w(0x508F | (bytes & 7) << 9);      /* addq.l #n,sp */
    else { w(0x4FEF); w(bytes); }                      /* lea n(sp),sp */
}

/* un operando que se carga en un registro sin tocar otros */
static int simple(Node *n, Var *v, long *k)
{
    if (fold(n, k)) {
        v->kind = V_CONST;
        v->val = *k;
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

static void need_value(Node *n, int ty)
{
    if (ty == TY_VOID) fatal_at(n->line, n->col, "%s no devuelve ningún valor", n->name ? n->name : "la expresión");
    if (ty == TY_STR) fatal_at(n->line, n->col, "dashc (prueba): los textos solo pueden ir en Print");
}

/* deja a en d0 y b en d1 */
static void gen_pair(Node *a, Node *b)
{
    Var v;
    long k;
    if (simple(b, &v, &k)) {
        need_value(a, gen_expr(a));
        load_var(1, &v);
    } else {
        need_value(a, gen_expr(a));
        push_d0();
        need_value(b, gen_expr(b));
        w(0x2200);                                     /* move.l d0,d1 */
        w(0x201F);                                     /* move.l (sp)+,d0 */
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

/* compara a con b: deja los códigos de condición de a - b */
static void gen_compare(Node *n)
{
    Var v;
    long k;
    if (fold(n->b, &k)) {
        need_value(n->a, gen_expr(n->a));
        if (k == 0) w(0x4A80);                         /* tst.l d0 */
        else { w(0xB0BC); l((uint32_t)k); }            /* cmp.l #k,d0 */
        return;
    }
    if (n->b->kind == E_VAR && simple(n->b, &v, &k) && v.kind == V_LOCAL) {
        need_value(n->a, gen_expr(n->a));
        w(0xB0AD);                                     /* cmp.l off(a5),d0 */
        w(v.off);
        return;
    }
    gen_pair(n->a, n->b);
    w(0xB081);                                         /* cmp.l d1,d0 */
}

static uint32_t add_string(const char *s, int len)
{
    uint32_t off = (uint32_t)obj->data.n;
    buf_bytes(&obj->data, s, len);
    buf_byte(&obj->data, 0);
    if (obj->data.n & 1) buf_byte(&obj->data, 0);
    return off;
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
        if (n->args.n != 1) fatal_at(n->line, n->col, "bench_sink pide 1 argumento");
        need_value(n->args.v[0], gen_expr(n->args.v[0]));
        if (sink_off < 0) {
            sink_off = (long)obj->data.n;
            buf_long(&obj->data, 0);
        }
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
            w(0x4879);                                 /* pea texto */
            add_reloc((uint32_t)obj->code.n, HK_DATA, NULL);
            l(add_string(a->str, a->len));
        } else {
            need_value(a, gen_expr(a));
            push_d0();
        }
    }
    jsr_sym(builtins[b].sym);
    pop_args(n->args.n);
    return builtins[b].ret;
}

static int gen_call(Node *n)
{
    int i, idx;
    Func *f = find_func(n->name, &idx);
    if (!f) return gen_builtin(n);
    if (n->args.n != f->params.n)
        fatal_at(n->line, n->col, "%s pide %d argumentos y se le dan %d", n->name, f->params.n, n->args.n);
    for (i = n->args.n - 1; i >= 0; i--) {
        need_value(n->args.v[i], gen_expr(n->args.v[i]));
        push_d0();
    }
    jsr_label(func_label[idx]);
    pop_args(n->args.n);
    return f->ret;
}

static int gen_expr(Node *n)
{
    long k;
    Var v;
    int ty;

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
        need_value(n->a, gen_expr(n->a));
        w(0x4480);                                     /* neg.l d0 */
        return TY_INT;
    case E_BNOT:
        need_value(n->a, gen_expr(n->a));
        w(0x4680);                                     /* not.l d0 */
        return TY_INT;
    case E_CMP:
        gen_compare(n);
        w(0x50C0 | cmp_cc(n->op) << 8);                /* scc d0 */
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
        /* suma y resta de una constante pequeña: addq/subq */
        if ((n->op == P_PLUS || n->op == P_MINUS) && fold(n->b, &k)) {
            need_value(n->a, gen_expr(n->a));
            if (n->op == P_MINUS) k = -k;
            if (k >= 1 && k <= 8) w(0x5080 | (k & 7) << 9);          /* addq.l #k,d0 */
            else if (k <= -1 && k >= -8) w(0x5180 | (-k & 7) << 9);  /* subq.l #k,d0 */
            else if (k) { w(0xD0BC); l((uint32_t)k); }                /* add.l #k,d0 */
            return TY_INT;
        }
        gen_pair(n->a, n->b);
        switch (n->op) {
        case P_PLUS: w(0xD081); break;                 /* add.l d1,d0 */
        case P_MINUS: w(0x9081); break;                /* sub.l d1,d0 */
        case P_AMP: w(0xC081); break;                  /* and.l d1,d0 */
        case P_BAR: w(0x8081); break;                  /* or.l d1,d0 */
        case P_CARET: w(0xB380); break;                /* eor.l d1,d0 */
        case P_SHL: w(0xE3A0); break;                  /* asl.l d1,d0 */
        case P_SHR: w(0xE2A0); break;                  /* asr.l d1,d0 */
        case P_STAR: jsr_sym("__dash_mul"); break;     /* d0 * d1 en el runtime */
        case P_SLASH: jsr_sym("__dash_div"); break;
        case P_PERCENT: jsr_sym("__dash_mod"); break;
        }
        return TY_INT;
    }
    (void)ty;
    fatal_at(n->line, n->col, "expresión no admitida");
    return TY_VOID;
}

/* salta a label si n es verdadero (when_true) o falso */
static void gen_branch(Node *n, int label, int when_true)
{
    long k;
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
        int cc = cmp_cc(n->op);
        gen_compare(n);
        branch(when_true ? cc : cc ^ 1, label);        /* cc ^ 1: la condición contraria */
        return;
    }
    }
    if (fold(n, &k)) {
        if ((k != 0) == when_true) branch(CC_T, label);
        return;
    }
    need_value(n, gen_expr(n));
    w(0x4A80);                                         /* tst.l d0 */
    branch(when_true ? CC_NE : CC_EQ, label);
}

/* ---- instrucciones ---- */
static void gen_block(NodeList *b);


static void gen_for(Node *n)
{
    long from, to, step = 1;
    int down = 0, top = new_label(), cont = new_label(), done = new_label();
    int ivar, end_slot, step_slot = 0, step_known = 1;
    Var vi;
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
    need_value(n->a, gen_expr(n->a));
    ivar = declare(n->name, TY_INT);
    w(0x2B40); w(ivar);                                /* move.l d0,i */
    need_value(n->b, gen_expr(n->b));
    end_slot = declare("", TY_INT);                    /* "": no se puede nombrar */
    w(0x2B40); w(end_slot);
    if (!step_known) {
        need_value(n->c, gen_expr(n->c));
        step_slot = declare("", TY_INT);
        w(0x2B40); w(step_slot);
    }

    def_label(top);
    w(0x202D); w(ivar);                                /* move.l i,d0 */
    w(0xB0AD); w(end_slot);                            /* cmp.l fin,d0 */
    branch(down ? CC_LT : CC_GT, done);

    lp.brk = done;
    lp.cont = cont;
    VEC_PUSH(loops, lp);
    gen_block(&n->body);
    loops.n--;

    def_label(cont);
    if (!step_known) {
        w(0x202D); w(step_slot);                       /* move.l paso,d0 */
        w(0xD1AD); w(ivar);                            /* add.l d0,i */
    } else if (step >= 1 && step <= 8) {
        w(0x50AD | (step & 7) << 9); w(ivar);          /* addq.l #paso,i */
    } else if (step <= -1 && step >= -8) {
        w(0x51AD | (-step & 7) << 9); w(ivar);         /* subq.l #paso,i */
    } else {
        w(0x06AD); l((uint32_t)step); w(ivar);         /* addi.l #paso,i */
    }
    branch(CC_T, top);
    def_label(done);
    leave_scope();
    vi.kind = V_NONE;
    (void)vi;
}

static void gen_stmt(Node *n)
{
    Var v;
    int ty;
    switch (n->kind) {
    case S_PRINT:
        if (n->a->kind == E_STR) {
            w(0x4879);                                 /* pea texto */
            add_reloc((uint32_t)obj->code.n, HK_DATA, NULL);
            l(add_string(n->a->str, n->a->len));
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
        ty = gen_expr(n->a);
        need_value(n->a, ty);
        v = lookup(n->name);
        if (n->kind == S_VAR || v.kind == V_NONE) {
            /* la primera asignación declara (en el bloque actual) */
            v.kind = V_LOCAL;
            v.off = declare(n->name, n->kind == S_VAR ? n->type : ty);
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
        int top = new_label(), done = new_label();
        def_label(top);
        gen_branch(n->a, done, 0);
        lp.brk = done;
        lp.cont = top;
        VEC_PUSH(loops, lp);
        enter_scope();
        gen_block(&n->body);
        leave_scope();
        loops.n--;
        branch(CC_T, top);
        def_label(done);
        return;
    }
    case S_FOR:
        gen_for(n);
        return;
    case S_BREAK:
    case S_CONTINUE:
        if (!loops.n) fatal_at(n->line, n->col, "%s fuera de un bucle", n->kind == S_BREAK ? "break" : "continue");
        branch(CC_T, n->kind == S_BREAK ? loops.v[loops.n - 1].brk : loops.v[loops.n - 1].cont);
        return;
    case S_RETURN:
        if (n->a) need_value(n->a, gen_expr(n->a));
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

/* una función: link a5,#-marco ... unlk a5; rts */
static void gen_function(int label, Func *f, NodeList *body)
{
    uint32_t frame_at;
    int i;
    cur = f;
    locals.n = 0;
    depth = 0;
    nslots = 0;
    ret_label = new_label();
    def_label(label);
    w(0x4E55);                                         /* link a5,#-marco */
    frame_at = (uint32_t)obj->code.n;
    w(0);
    if (f)
        for (i = 0; i < f->params.n; i++) {
            Local lc;
            lc.name = f->params.v[i].name;
            lc.off = 8 + 4 * i;
            lc.type = f->params.v[i].type;
            lc.depth = 0;
            VEC_PUSH(locals, lc);
        }
    gen_block(body);
    def_label(ret_label);
    w(0x4E5D);                                         /* unlk a5 */
    w(0x4E75);                                         /* rts */
    if (nslots * 4 > 32767) fatal("demasiadas variables en una función");
    put_word(obj->code.p + frame_at, -4 * nslots);
}

void gen_program(Program *p, Obj *o)
{
    int i, main_label, fail;
    prog = p;
    obj = o;

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

    gen_function(main_label, NULL, &p->main);
    for (i = 0; i < p->funcs.n; i++) gen_function(func_label[i], &p->funcs.v[i], &p->funcs.v[i].body);
    resolve_fixups();
}
