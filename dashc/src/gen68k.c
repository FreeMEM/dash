/* Generador de código 68000. Cada expresión deja su valor en d0; un operando que
   no es simple se guarda en la pila mientras se calcula el otro. Las funciones usan
   un marco con a5 (link/unlk): los parámetros en 8(a5), 12(a5)... y las variables
   en -4(a5), -8(a5)... Se llaman como en C (argumentos en la pila, de derecha a
   izquierda, resultado en d0), así que el runtime de gcc se llama igual.

   Cada función se genera dos veces: la primera cuenta cuánto se usa cada variable
   (lo de dentro de un bucle cuenta más) y la segunda pone las más usadas en d2-d7,
   que la función guarda al entrar y recupera al salir. */
#include <ctype.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "dashc.h"


#define MIN_USES 3   /* menos usos no pagan guardar y recuperar el registro */

static Program *prog;
static Obj *obj;
int memcheck;
int profile;          /* --perfil: dl_prof_enter/leave en cada función */
int cpu020;           /* --fpu o --cpu 68020 y más: muls.l, divs.l */
/* --debug (el depurador, docs/DEPURADOR_LOOP.md): un NOP al principio de cada línea, que el depurador cambia por
   un TRAP; sin copiar funciones en línea, sin variables en registros ni como constantes; y la información para el
   depurador en debug_info (el texto del HUNK_DEBUG, que escribe hunk.c) */
int debug;
Buf debug_info;
typedef struct { int label, file, line; } DbgLine;
typedef struct { char *name; int start, end, file, line; } DbgFunc;
typedef struct { int func, type, off, line; char *name; } DbgVar;
static struct { DbgLine *v; int n, cap; } dbg_lines;
static struct { DbgFunc *v; int n, cap; } dbg_funcs;
static struct { DbgVar *v; int n, cap; } dbg_vars;
static int prof_label = -1;   /* los nombres de las funciones, para el perfil */

#include "t68k_base.c"

/* un error en un nodo: con el fichero del nodo (un módulo), no el de la última instrucción generada */
static void fatal_node(Node *n, const char *fmt, ...)
{
    char msg[1024];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(msg, sizeof msg, fmt, ap);
    va_end(ap);
    src_name = src_files.v[n->file];
    fatal_at(n->line, n->col, "%s", msg);
}

/* el nombre de C (_nombre) de una función de Dash: sin el sufijo de privada de su módulo (_x__m2 es _x) */
static char *c_symbol(const char *name)
{
    char *sym = xmalloc(strlen(name) + 2), *m;
    sym[0] = '_';
    strcpy(sym + 1, name);
    m = strstr(sym, "__m");
    if (m && isdigit((unsigned char)m[3])) {
        char *e = m + 3;
        while (isdigit((unsigned char)*e)) e++;
        if (!*e) *m = 0;
    }
    return sym;
}

/* ---- nombres: constantes, globales, variables locales y funciones ---- */
/* Una variable con nombre: un hueco (slot >= 0) o, en una función copiada en el
   sitio de la llamada, un parámetro que vale una constante (slot -1 y val). frame
   separa los nombres de cada copia de los de la función que la contiene. */
/* ranged: lo <= valor <= hi siempre. entry: lo mismo, pero solo hasta que se le asigne
   algo, y dentro de los mismos bucles (entry_loops) que cuando se creó */
typedef struct {
    char *name;
    int slot, type, depth, frame;
    long val;
    int ranged;
    long lo, hi;
    int entry, entry_loops;
    int owned;   /* un texto que es suyo: se libera al salir de su bloque */
} Local;
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
typedef struct { Node *n; int slot, need_reg, type; } Repl;   /* type: TY_INT, o TY_FLOAT (un Float sacado del bucle) */
static struct { Repl *v; int n, cap; } repls;

/* depth: la de las variables del cuerpo; sp: sp_depth dentro del cuerpo */
typedef struct { int brk, cont, depth, sp; } Loop;
static struct { Loop *v; int n, cap; } loops;
static int loop_base;   /* los bucles de antes son de fuera de la función copiada */

static int *func_label;   /* etiqueta de cada función */
static int *global_type;
static int ret_label;
static int ret_sp;    /* sp_depth en ret_label */
static int cur_ret;   /* lo que devuelve la función (o la copia) que se genera */
static int cur_line;  /* la línea de la instrucción que se genera (errores: campo de nil) */
static int cur_file;  /* y su fichero (src_files) */
static int *desc_label;   /* de cada struct: su _DashType (en el código) */
static int *win_desc_label;   /* de cada Window: su DashWinDesc (en el código) */
static long *win_off;         /* y dónde está su variable en los datos */
/* EventLoop abiertos: su salida y, dentro de sus On, la profundidad y la pila (Stop) */
typedef struct { int done, depth, sp; } EvLoop;
static struct { EvLoop *v; int n, cap; } evloops;
static int uses_keys, uses_click, uses_inactive;   /* IDCMP de las ventanas */
/* GadTools, como ./dash: gadgets (GT_GetIMsg y On Gadget), gadgets o menús (sus IDCMP) y teclas de gadgets */
static int uses_gadgets, needs_gt, gadget_keys;
static int needs_area;   /* gfx_circle_fill...: la ventana prepara el relleno de áreas al abrirse */
static int uses_mui, uses_tls;   /* la pila: 32 KB con MUI, 64 KB con AmiSSL (como ./dash) */

static int find_struct(const char *name)
{
    int i;
    for (i = 0; i < prog->structs.n; i++)
        if (!strcmp(prog->structs.v[i].name, name)) return i;
    return -1;
}

static int field_index(Struct *st, const char *name)
{
    int i;
    for (i = 0; i < st->fields.n; i++)
        if (!strcmp(st->fields.v[i].name, name)) return i;
    return -1;
}

enum { V_NONE, V_LOCAL, V_REG, V_GLOBAL, V_CONST, V_STACK };

/* Una función sin variables en el marco no hace link: lee sus parámetros con sp,
   sabiendo cuánto ha metido en la pila (sp_depth) en cada punto del código. */
static int frameless, sp_depth, param_base;
typedef struct { int kind, off, reg, type; long val; } Var;

static int fold(Node *n, long *v);
static int fold_literal;   /* fold sin las variables que valen una constante */

/* Una global del programa principal no se ve desde sus módulos: allí ese nombre es una variable
   suya (como en ./dash, dashweb D14). Las de los módulos se ven desde todos. */
static int cur_file_g;
static int global_visible(int i)
{
    return prog->globals.v[i].file != 0 || cur_file_g == 0;
}

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
        if (global_visible(i) && !strcmp(prog->globals.v[i].name, name)) {
            r.kind = V_GLOBAL;
            r.off = global_off(i);
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
        VEC_PUSH(slot_off, frame_off(++nframe));
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
            *v = slot_var(r->slot, r->type);
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
    r.type = TY_INT;
    VEC_PUSH(repls, r);
}

/* --debug: una variable o parámetro de la función que se genera, con dónde está (en el marco: su desplazamiento
   sobre a5) */
static void dbg_var(const char *name, int type, int slot, int line)
{
    DbgVar d;
    if (!debug || pass != 2 || !dbg_funcs.n || slot < 0) return;
    d.func = dbg_funcs.n - 1;
    d.name = (char *)name;
    d.type = type;
    d.off = slot_off.v[slot];
    d.line = line;
    VEC_PUSH(dbg_vars, d);
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
    lc.entry = 0;
    lc.owned = 0;
    VEC_PUSH(locals, lc);
    use_slot(lc.slot);
    dbg_var(name, type, lc.slot, cur_line);
    return slot_var(lc.slot, type);
}

static void enter_scope(void) { depth++; }

static void free_owned(int from_depth, int all_frame);

/* al salir de un bloque cayendo por el final, se liberan sus textos */
static void leave_scope(void)
{
    free_owned(depth, 0);
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

static int expr_type(Node *n);
static Local *find_local(const char *name);
static int lookup_global(const char *name);

static int find_window(const char *name);

/* Win.width, height, left, top, title, inner_left, inner_top, inner_width, inner_height: su número (0-8), o -1 */
static int window_member(Node *n)
{
    static const char *const m[] = {"width", "height", "left", "top", "title", "inner_left", "inner_top",
                                    "inner_width", "inner_height", NULL};
    int i;
    if (n->kind != E_FIELD || n->a->kind != E_VAR || find_local(n->a->name) || lookup_global(n->a->name)) return -1;
    for (i = 0; i < prog->windows.n; i++)
        if (!strcmp(prog->windows.v[i].name, n->a->name)) break;
    if (i == prog->windows.n) return -1;
    for (i = 0; m[i]; i++)
        if (!strcmp(m[i], n->name)) return i;
    return -1;
}

static int fold(Node *n, long *v)
{
    long a, b;
    if (n->kind == E_BIN && expr_type(n) == TY_FIXED) {
        /* Fixed: solo lo que es una cuenta de enteros (Fixed + Fixed, Fixed * Int, Fixed / Int); Fixed * Fixed y
           un Int con un Fixed van por el runtime o se convierten */
        int fa = expr_type(n->a) == TY_FIXED, fb = expr_type(n->b) == TY_FIXED;
        if (n->op == P_STAR ? fa && fb : n->op == P_SLASH ? !(fa && !fb) : !(fa && fb)) return 0;
    }
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
            if (global_visible(i) && !strcmp(prog->globals.v[i].name, n->name)) return 0;
        for (i = 0; i < prog->consts.n; i++)
            if (!strcmp(prog->consts.v[i].name, n->name)) return fold(prog->consts.v[i].value, v);
        return 0;
    }
    case E_FIELD:
        /* Enum.MIEMBRO */
        if (n->a->kind == E_VAR && !find_local(n->a->name)) {
            int i, j;
            for (i = 0; i < prog->enums.n; i++)
                if (!strcmp(prog->enums.v[i].name, n->a->name))
                    for (j = 0; j < prog->enums.v[i].names.n; j++)
                        if (!strcmp(prog->enums.v[i].names.v[j], n->name)) {
                            *v = prog->enums.v[i].vals.v[j];
                            return 1;
                        }
        }
        return 0;
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

/* modo de prueba, como ./dash: DASH_TEST_AUTOCLOSE=<segundos> al compilar (el programa acaba solo; tools/emu_run.py)
   y DASH_PRINT_FLUSH=1 (cada Print sale enseguida) */
static int autoclose, print_flush;

#include "t68k_ops.c"

/* un operando que se usa sin calcular nada: una constante o una variable */
/* el tipo de una expresión que se sabe al compilar */
static int fold_type(Node *n)
{
    if (n->kind == E_BOOL) return TY_BOOL;
    if (n->kind == E_VAR) return lookup(n->name).type;   /* una constante: no cuenta como uso */
    if ((n->kind == E_BIN || n->kind == E_NEG) && expr_type(n) == TY_FIXED) return TY_FIXED;
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
        if (v->kind == V_NONE) fatal_node(n, "la variable %s no existe", n->name);
        return 1;
    }
    return 0;
}

static int gen_expr(Node *n);
static void gen_branch(Node *n, int label, int when_true);
static void gen_block(NodeList *b);

static void need_value(Node *n, int ty)
{
    if (ty == TY_VOID) fatal_node(n, "%s no devuelve ningún valor", n->name ? n->name : "la expresión");
}

static void value(Node *n) { need_value(n, gen_expr(n)); }

/* mete en la pila el valor de n (un argumento) */
static void push_value(Node *n)
{
    Var v;
    if (n->kind == E_STR) {
        pea_string(n->str, n->len);
        return;
    }
    if (simple(n, &v)) {
        push_var(&v);
        return;
    }
    value(n);
    push_d0();
}

/* ---- textos: llamadas al runtime de ./dash (dl_* en runtime/api.c) ----
   Como en el C de ./dash: una variable de texto es dueña de su texto (lo libera al salir
   de su bloque, en break, continue y return); lo que sale de +, de una interpolación o de
   una función es un temporal, que se libera en bloque al empezar cada vuelta de un bucle
   y al salir de una función (marcas). */
static int made_tmp;   /* desde la última marca, algo ha dejado temporales */

/* jsr sym con nargs argumentos ya en la pila; tmp: el resultado es un temporal nuevo */
static void rt_call(const char *sym, int nargs, int tmp)
{
    jsr_sym(sym);
    pop_args(nargs);
    if (tmp) made_tmp = 1;
}

/* ---- tipos sin generar código: los de las variables, y lo que devuelve una función ---- */
typedef struct { const char *name; int type; } TBind;
static struct { TBind *v; int n, cap; } tenv;   /* variables al deducir lo que devuelve una función */
static int tenv_on, tenv_base;
static int func_ret(int idx);

static int var_type(const char *name)
{
    int i;
    if (tenv_on) {
        for (i = tenv.n - 1; i >= tenv_base; i--)
            if (!strcmp(tenv.v[i].name, name)) return tenv.v[i].type;
    } else {
        Local *lc = find_local(name);
        if (lc) return lc->type;
    }
    for (i = 0; i < prog->globals.n; i++)
        if (global_visible(i) && !strcmp(prog->globals.v[i].name, name)) return global_type[i];
    for (i = 0; i < prog->consts.n; i++)
        if (!strcmp(prog->consts.v[i].name, name)) {
            Node *v = prog->consts.v[i].value;
            return v->kind == E_BOOL ? TY_BOOL : v->kind == E_STR ? TY_STR : TY_INT;
        }
    return TY_VOID;
}

static int dict_val(int t);

static int expr_type(Node *n)
{
    int ta, tb, idx;
    switch (n->kind) {
    case E_NEG:
        ta = expr_type(n->a);
        return ta == TY_FLOAT || ta == TY_DOUBLE || ta == TY_FIXED ? ta : TY_INT;
    case E_INT: case E_BNOT:
        return TY_INT;
    case E_BOOL: case E_CMP: case E_NOT: case E_AND: case E_OR:
        return TY_BOOL;
    case E_STR: case E_INTERP:
        return TY_STR;
    case E_FLOAT:
        return TY_FLOAT;
    case E_NIL:
        return TY_NIL;
    case E_VAR:
        return var_type(n->name);
    case E_CALL:
        if (find_func(n->name, &idx)) return func_ret(idx);
        if (!strcmp(n->name, "Float")) return TY_FLOAT;
        if (!strcmp(n->name, "Double")) return TY_DOUBLE;
        if (!strcmp(n->name, "Fixed") || !strcmp(n->name, "fx_sqrt") || !strcmp(n->name, "fx_sin") ||
            !strcmp(n->name, "fx_cos")) return TY_FIXED;
        if (!strcmp(n->name, "Int")) return TY_INT;
        if ((idx = find_struct(n->name)) >= 0) return TY_STRUCT + idx;
        for (idx = 0; idx < builtin_count; idx++)
            if (!strcmp(builtin_info[idx].name, n->name)) {
                static const int ret[] = {TY_VOID, TY_INT, TY_BOOL, TY_STR, TY_ARR + TY_STR, TY_DOUBLE};
                return ret[builtin_info[idx].ret];
            }
        return TY_VOID;
    case E_NN:
        return expr_type(n->a);
    case E_BIN:
        ta = expr_type(n->a);
        tb = expr_type(n->b);
        if (n->op == P_PLUS && (ta == TY_STR || tb == TY_STR)) return TY_STR;
        if (n->op == P_PLUS && (IS_ARR(ta) || IS_ARR(tb)))   /* a + b de listas: lo que guarda la primera con tipo */
            return IS_ARR(ta) && ta != TY_ARR + TY_VOID ? ta : IS_ARR(tb) ? tb : ta;
        if ((ta == TY_DOUBLE || tb == TY_DOUBLE) &&
            (n->op == P_PLUS || n->op == P_MINUS || n->op == P_STAR || n->op == P_SLASH)) return TY_DOUBLE;
        if ((ta == TY_FLOAT || tb == TY_FLOAT) &&
            (n->op == P_PLUS || n->op == P_MINUS || n->op == P_STAR || n->op == P_SLASH)) return TY_FLOAT;
        if ((ta == TY_FIXED || tb == TY_FIXED) && (n->op == P_PLUS || n->op == P_MINUS || n->op == P_STAR ||
                                                   n->op == P_SLASH || n->op == P_PERCENT)) return TY_FIXED;
        return TY_INT;
    case E_INDEX:
        ta = expr_type(n->a);
        if (ta == TY_STR) return TY_CHAR;
        if (IS_ARR(ta)) return ta == TY_ARR + TY_VOID ? TY_INT : ta - TY_ARR;
        if (IS_DICT(ta)) return dict_val(ta);
        return TY_INT;
    case E_SLICE:
        return expr_type(n->a);
    case E_FIELD:
        if (window_member(n) >= 0) return window_member(n) == 4 ? TY_STR : TY_INT;
        ta = expr_type(n->a);
        if (IS_STRUCT(ta)) {
            Struct *st = &prog->structs.v[ta - TY_STRUCT];
            int f = field_index(st, n->name);
            return f >= 0 ? st->fields.v[f].type : TY_VOID;
        }
        return TY_INT;
    case E_DICT:
        if (!n->args.n) return dict_type(TY_STR, TY_VOID);   /* {}: lo que se meta dirá qué guarda */
        ta = expr_type(n->args.v[1]);
        return dict_type(expr_type(n->args.v[0]) == TY_INT ? TY_INT : TY_STR, ta == TY_NIL ? TY_INT : ta);
    case E_LIST:
        if (n->type) return TY_ARR + n->type;          /* (el de su destino: un campo [Double]...) */
        if (!n->args.n) return TY_ARR + TY_VOID;       /* []: lo que se meta dirá qué guarda */
        ta = expr_type(n->args.v[0]);
        return TY_ARR + (ta == TY_NIL ? TY_INT : ta);
    case E_MCALL:
        ta = expr_type(n->a);
        if (IS_ARR(ta) && !strcmp(n->name, "pop")) return ta == TY_ARR + TY_VOID ? TY_INT : ta - TY_ARR;
        if (IS_DICT(ta)) {
            if (!strcmp(n->name, "get")) return dict_val(ta);
            if (!strcmp(n->name, "has")) return TY_BOOL;
            if (!strcmp(n->name, "keys")) return TY_ARR + dict_types.v[ta - TY_DICT].key;
        }
        if (IS_STRUCT(ta) && prog->structs.v[ta - TY_STRUCT].iface) {
            IfaceMethod *m;
            int i;
            Struct *st = &prog->structs.v[ta - TY_STRUCT];
            for (i = 0, m = NULL; i < st->methods.n; i++)
                if (!strcmp(st->methods.v[i].name, n->name)) m = &st->methods.v[i];
            return m ? m->ret : TY_VOID;
        }
        if (IS_STRUCT(ta)) {
            char name[256];
            snprintf(name, sizeof name, "%s.%s", prog->structs.v[ta - TY_STRUCT].name, n->name);
            if (find_func(name, &idx)) return func_ret(idx);
        }
        if (ta == TY_INT && !strcmp(n->name, "abs")) return TY_INT;
        return TY_VOID;
    }
    return TY_INT;
}

/* el valor de un diccionario (uno que aún no sabe qué guarda, Int) */
static int dict_val(int t)
{
    int v = dict_types.v[t - TY_DICT].val;
    return v == TY_VOID ? TY_INT : v;
}

/* qué guarda una lista de elementos de tipo t: 0 números, 1 objetos, 2 textos (DashArray_own) */
static int elem_kind(int t)
{
    return IS_STRLIKE(t) ? 2 : IS_OBJ(t) ? 1 : 0;
}

/* lo que devuelve una función sin "-> Tipo": el tipo del primer return con valor, con las
   variables de su cuerpo deducidas por su primera asignación. Bool y un carácter salen Int,
   como en ./dash. */
static int *fret_state;   /* 0 sin calcular, 1 calculando (recursión), 2 hecho */

static int infer_on;   /* infer_params: walk_types mira también las llamadas */

/* Una llamada a una función con parámetros sin tipo: cada uno toma el tipo de lo que se le pasa, si no es un
   número (Int es lo que ya tiene). Como ./dash, manda la primera llamada. */
static void infer_calls(Node *e)
{
    int i, idx;
    Func *f;
    if (!e) return;
    infer_calls(e->a);
    infer_calls(e->b);
    infer_calls(e->c);
    for (i = 0; i < e->args.n; i++) infer_calls(e->args.v[i]);
    if (e->kind != E_CALL || !(f = find_func(e->name, &idx)) || e->args.n != f->params.n) return;
    for (i = 0; i < f->params.n; i++)
        if (f->params.v[i].untyped) {
            int t = expr_type(e->args.v[i]);
            if (t == TY_INT || t == TY_VOID || t == TY_NIL) continue;
            f->params.v[i].type = t == TY_BOOL || t == TY_CHAR ? TY_INT : t;
            f->params.v[i].untyped = 0;
        }
}

static int collect_set;   /* walk_types anota los campos a los que algo asigna (lend) */
static int collect_fn;    /* y de qué función es lo que recorre (-1: Main) */
static void add_set_field(int st, char *name);
static void collect_lent(Node *st);
static int is_lent(int obj, const char *name);

static void walk_types(NodeList *l, int *ret)
{
    int i;
    for (i = 0; i < l->n; i++) {
        Node *st = l->v[i];
        TBind b;
        b.name = st->name;
        if (collect_set && st->kind == S_STORE && st->b->kind == E_FIELD) {
            int ts = expr_type(st->b->a);
            add_set_field(IS_STRUCT(ts) ? ts - TY_STRUCT : -1, st->b->name);
        }
        if (collect_set) collect_lent(st);
        if (infer_on) {
            infer_calls(st->a);
            infer_calls(st->b);
            infer_calls(st->c);
        }
        switch (st->kind) {
        case S_ASSIGN:
            if (var_type(st->name) == TY_VOID) {
                b.type = expr_type(st->a);
                VEC_PUSH(tenv, b);
            }
            break;
        case S_VAR:
            b.type = st->type;
            VEC_PUSH(tenv, b);
            break;
        case S_FOR:
            b.type = TY_INT;
            VEC_PUSH(tenv, b);
            break;
        case S_FOREACH:
            b.type = expr_type(st->a);
            b.type = IS_ARR(b.type) ? b.type - TY_ARR : b.type == TY_STR ? TY_CHAR : TY_INT;
            VEC_PUSH(tenv, b);
            break;
        case S_RETURN:
            if (st->a && (*ret == TY_VOID || *ret == TY_NIL)) *ret = expr_type(st->a);
            break;
        case S_EXPR:
        case S_STORE: {
            /* r = [] y luego r.push(x) o r[i] = x: la lista guarda lo de x */
            Node *list = NULL, *v = NULL;
            int j;
            if (st->kind == S_EXPR && st->a->kind == E_MCALL && st->a->args.n &&
                (!strcmp(st->a->name, "push") || !strcmp(st->a->name, "insert"))) {
                list = st->a->a;
                v = st->a->args.v[st->a->args.n - 1];
            } else if (st->kind == S_STORE && st->b->kind == E_INDEX) {
                list = st->b->a;
                v = st->a;
            }
            if (list && list->kind == E_VAR)
                for (j = tenv.n - 1; j >= tenv_base; j--)
                    if (!strcmp(tenv.v[j].name, list->name)) {
                        if (tenv.v[j].type == TY_ARR + TY_VOID) tenv.v[j].type = TY_ARR + expr_type(v);
                        break;
                    }
            break;
        }
        }
        walk_types(&st->body, ret);
        walk_types(&st->els, ret);
    }
}

static int func_ret(int idx)
{
    Func *f = &prog->funcs.v[idx];
    int saved_on = tenv_on, saved_base = tenv_base, saved_n = tenv.n, i, r = TY_VOID, saved_file;
    /* (-> Array sin más: lo que guarda, del cuerpo) */
    if ((f->declared && f->ret != TY_ARR + TY_VOID) || fret_state[idx] == 2) return f->ret;
    if (fret_state[idx] == 1) return f->has_value ? TY_INT : TY_VOID;
    fret_state[idx] = 1;
    saved_file = cur_file_g;
    cur_file_g = f->file;                              /* (las globales que ve, las de su fichero) */
    tenv_on = 1;
    tenv_base = tenv.n;
    for (i = 0; i < f->params.n; i++) {
        TBind b;
        b.name = f->params.v[i].name;
        b.type = f->params.v[i].type;
        VEC_PUSH(tenv, b);
    }
    walk_types(&f->body, &r);
    tenv.n = saved_n;
    tenv_on = saved_on;
    tenv_base = saved_base;
    cur_file_g = saved_file;
    if (r == TY_BOOL || r == TY_CHAR || r == TY_NIL || (r == TY_VOID && f->has_value)) r = TY_INT;
    if (f->declared && !IS_ARR(r)) r = f->ret;
    f->ret = r;
    fret_state[idx] = 2;
    return r;
}

/* Los parámetros sin tipo, de las llamadas: Main y luego cada función con sus parámetros (dos vueltas: un
   parámetro que se acaba de saber puede pasar a otra función). Lo que devuelven las funciones se calcula
   después otra vez, ya con los tipos. */
static void infer_params(Program *p)
{
    int pass, i, j, r, *rets = xmalloc(sizeof(int) * (p->funcs.n + 1));
    for (i = 0; i < p->funcs.n; i++) rets[i] = p->funcs.v[i].ret;
    infer_on = 1;
    for (pass = 0; pass < 2; pass++) {
        int saved_base = tenv_base;
        tenv_on = 1;
        tenv_base = tenv.n;
        r = TY_VOID;
        walk_types(&p->main, &r);
        tenv.n = tenv_base;
        for (i = 0; i < p->funcs.n; i++) {
            Func *f = &p->funcs.v[i];
            if (f->native) continue;
            cur_file_g = f->file;
            for (j = 0; j < f->params.n; j++) {
                TBind b;
                b.name = f->params.v[j].name;
                b.type = f->params.v[j].type;
                VEC_PUSH(tenv, b);
            }
            r = TY_VOID;
            walk_types(&f->body, &r);
            tenv.n = tenv_base;
        }
        tenv_base = saved_base;
        tenv_on = 0;
    }
    infer_on = 0;
    cur_file_g = 0;
    for (i = 0; i < p->funcs.n; i++) {
        p->funcs.v[i].ret = rets[i];
        fret_state[i] = 0;
    }
    free(rets);
}

/* ¿da dbl_value(n) una caja constante (un literal o un número fijo, ya convertido al compilar)? */
static int dbl_const(Node *n)
{
    long k;
    if (n->kind == E_FLOAT || (n->kind == E_NEG && n->a->kind == E_FLOAT)) return 1;
    if (n->kind == E_CALL && !strcmp(n->name, "Double") && n->args.n == 1 && !find_func(n->name, NULL))
        return expr_type(n->args.v[0]) != TY_STR && dbl_const(n->args.v[0]);
    return expr_type(n) != TY_DOUBLE && fold(n, &k);
}

/* lo que deja un temporal nuevo (no lo que ya es de alguien: un literal, una variable) */
static int is_tmp_expr(Node *e)
{
    if (expr_type(e) == TY_DOUBLE && dbl_const(e)) return 0;
    return e->kind == E_BIN || e->kind == E_INTERP || e->kind == E_SLICE || e->kind == E_CALL ||
           e->kind == E_MCALL || e->kind == E_LIST || e->kind == E_DICT;
}

/* un struct nuevo (Punto(...)) o una lista literal: nace con una referencia si se asigna */
static int is_new_obj(Node *e)
{
    return (e->kind == E_LIST && e->args.n) || (e->kind == E_CALL && !find_func(e->name, NULL) &&
                                                 find_struct(e->name) >= 0);
}

/* d0 (de tipo ty) como texto: un número o un carácter pasan a un texto temporal */
static void to_str(int ty)
{
    switch (ty) {
    case TY_INT:
        /* (uno de los 16 búferes fijos de DashString_from_int: no es un temporal que haya que soltar, así que no pide
           marca de temporales; quien lo guarda lo copia, porque no es suyo) */
        push_d0();
        rt_call("_dl_str_from_int", 1, 0);
        break;
    case TY_CHAR:
        push_d0();
        rt_call("_dl_str_from_char", 1, 1);
        break;
    case TY_FLOAT:
        push_d0();
        rt_call("_dl_str_from_float", 1, 1);
        break;
    case TY_DOUBLE:
        push_d0();
        rt_call("_dl_d_str", 1, 1);
        break;
    case TY_FIXED:
        push_d0();
        rt_call("_dl_fx_str", 1, 1);
        break;
    case TY_BOOL:
        bool_to_str();
        break;
    }
}

static void str_value(Node *n)
{
    int ty = gen_expr(n);
    need_value(n, ty);
    to_str(ty);
}

/* ---- Float: el de gcc por software (fp-bit y fastfp, como ./dash); sus bits en un LONG ---- */

/* d0, de tipo from, pasado a to: Int a Float (__floatsisf) o Float a Int (__fixsfsi, como C) */
static void coerce(int from, int to)
{
    if (from == TY_FIXED && to == TY_FLOAT) {
        push_d0();
        rt_call("_dl_fx_to_float", 1, 0);
    } else if (from == TY_FIXED && (to == TY_INT || to == TY_CHAR)) {
        push_d0();
        rt_call("_dl_fx_int", 1, 0);
    } else if (to == TY_FLOAT && (from == TY_INT || from == TY_CHAR || from == TY_BOOL)) {
        push_d0();
        rt_call("___floatsisf", 1, 0);
    } else if ((to == TY_INT || to == TY_CHAR) && from == TY_FLOAT) {
        push_d0();
        rt_call("___fixsfsi", 1, 0);
    }
}

/* el valor de n como Fixed: un literal, al compilar (Fixed(1.5) es 98304, como ./dash); un Int, << 16; un Float,
   * 65536 */
static void fix_value(Node *n)
{
    long k;
    int t;
    Node *lit = n->kind == E_NEG ? n->a : n;
    if ((lit->kind == E_FLOAT || lit->kind == E_INT) && expr_type(n) != TY_FIXED) {
        double v = lit->kind == E_FLOAT ? lit->dval : (double)(int32_t)lit->val;
        double r = v * 65536.0;
        long q = (long)(r < 0 ? r - 0.5 : r + 0.5);       /* (round de Python, salvo los .5 exactos) */
        if (n->kind == E_NEG) q = -q;
        if (q > 0x7FFFFFFFL) q = 0x7FFFFFFFL;
        if (q < -0x7FFFFFFFL - 1) q = -0x7FFFFFFFL - 1;
        load_imm(0, q);
        return;
    }
    if (expr_type(n) != TY_FIXED && expr_type(n) != TY_FLOAT && fold(n, &k)) {
        load_imm(0, (long)(int32_t)((uint32_t)k << 16));
        return;
    }
    t = gen_expr(n);
    need_value(n, t);
    if (t == TY_FIXED) return;
    if (t == TY_FLOAT) {
        push_d0();
        rt_call("_dl_fx_from_float", 1, 0);
        return;
    }
    int_to_fixed();
}

/* el valor de n como Float (un número fijo, ya convertido al compilar) */
static void float_value(Node *n)
{
    long k;
    int t;
    if (fold(n, &k)) {
        load_imm(0, float_bits((double)(int32_t)k));
        return;
    }
    t = gen_expr(n);
    need_value(n, t);
    coerce(t, TY_FLOAT);
}

/* ---- Double: una caja (un texto con sus 8 bytes en hexadecimal, runtime/api.c) ---- */
static void load_dbl_lit(double d)
{
    uint64_t b;
    char hex[17];
    memcpy(&b, &d, 8);                                 /* (los bits, en el orden de esta máquina) */
    snprintf(hex, sizeof hex, "%08lX%08lX", (unsigned long)(b >> 32), (unsigned long)(b & 0xFFFFFFFFu));
    load_str_lit(hex, 16);
}

/* d0, de tipo t, como Double (una caja temporal) */
static void to_dbl(int t)
{
    if (t == TY_DOUBLE) return;
    push_d0();
    rt_call(t == TY_FLOAT ? "_dl_d_from_float" : "_dl_d_from_int", 1, 1);
}

/* el valor de n como Double; un literal o un número fijo, con todas sus cifras, al compilar */
static void dbl_value(Node *n)
{
    long k;
    int t;
    if (n->kind == E_FLOAT) {
        load_dbl_lit(n->dval);
        return;
    }
    if (n->kind == E_NEG && n->a->kind == E_FLOAT) {
        load_dbl_lit(-n->a->dval);
        return;
    }
    if (expr_type(n) != TY_DOUBLE && fold(n, &k)) {
        load_dbl_lit((double)(int32_t)k);
        return;
    }
    t = gen_expr(n);
    need_value(n, t);
    to_dbl(t);
}

/* Los argumentos de una llamada al runtime, calculados en orden y dejados en la pila
   como los pone C (el primero arriba). str[i]: el argumento i pasa a texto (1), Float (2) o Double (3). Sitio para
   todos primero y luego cada uno a su hueco: así se calculan de izquierda a derecha. */
static void float_value(Node *n);

static void args_to_stack(Node **a, int n, const char *str)
{
    int i;
    if (n == 1) {
        if (str && str[0] == 2) float_value(a[0]);
        else if (str && str[0] == 3) dbl_value(a[0]);
        else if (str && str[0] == 4) fix_value(a[0]);
        else if (str && str[0]) str_value(a[0]);
        else value(a[0]);
        push_d0();
        return;
    }
    reserve_args(n);
    for (i = 0; i < n; i++) {
        if (str && str[i] == 2) float_value(a[i]);
        else if (str && str[i] == 3) dbl_value(a[i]);
        else if (str && str[i] == 4) fix_value(a[i]);
        else if (str && str[i]) str_value(a[i]);
        else value(a[i]);
        store_d0_arg(i);
    }
}

/* "a#{x}b": DashString_join(n, trozos), con los trozos en un array en la pila */
static void gen_interp(Node *n)
{
    int np = n->args.n, i;
    char *str = xmalloc(np + 1);
    for (i = 0; i < np; i++) str[i] = 1;
    args_to_stack(n->args.v, np, str);
    free(str);
    push_sp();                                         /* la dirección de los trozos */
    push_word(np);
    rt_call("_dl_str_join", 2, 1);
    pop_args(np);
}

/* a + b con algún texto: DashString_concat, con un número pasado a texto */
static void gen_concat(Node *n)
{
    Node *a[2], *e, join;
    static const char str[2] = {1, 1};
    int np = 0, i;
    /* a + b + c...: una sola reserva para toda la cadena (DashString_join, como ./dash), no un texto intermedio por
       cada +; solo los + que ya dan texto (1 + 2 + "x" suma antes 1 + 2) */
    for (e = n; e->kind == E_BIN && e->op == P_PLUS && expr_type(e) == TY_STR; e = e->a) np++;
    if (np >= 2) {
        memset(&join, 0, sizeof join);
        join.kind = E_INTERP;
        join.line = n->line;
        join.col = n->col;
        join.file = n->file;
        for (i = 0; i <= np; i++) VEC_PUSH(join.args, NULL);
        for (e = n, i = np; i > 0; e = e->a, i--) join.args.v[i] = e->b;
        join.args.v[0] = e;
        if (join.args.v[0]->kind == E_STR && join.args.v[0]->len == 0) {   /* "" + ...: el primero sobra */
            memmove(join.args.v, join.args.v + 1, sizeof(Node *) * np);
            join.args.n--;
        }
        gen_interp(&join);
        free(join.args.v);
        return;
    }
    a[0] = n->a;
    a[1] = n->b;
    args_to_stack(a, 2, str);
    rt_call("_dl_str_concat", 2, 1);
}

/* str_code(s, i) en línea, como _dash_str_code: un texto de Dash con su largo en la cabecera; si no, _dl_str_code */
/* el índice a d1 */
static void index_to_d1(Node *i)
{
    Var vi;
    if (simple(i, &vi)) load_var(1, &vi);
    else {
        value(i);
        move_d0_d1();
    }
}

/* Los parámetros de texto que la función no cambia: su largo, medido al entrar (plen_slot), y str_code, s[i] y
   .length solo comparan con él. Un texto no cambia y el argumento que algo podría cambiar llega copiado (lend).
   Solo en el cuerpo de la propia función (no en lo copiado en línea dentro, con otros nombres) */
static struct { const char *name; int slot, param; } plen[8];
static int n_plen, plen_depth = -1;

static int plen_slot(Node *s)
{
    int k;
    Local *lc;
    if (s->kind != E_VAR || inl_stack.n != plen_depth) return -1;
    for (k = 0; k < n_plen; k++)
        if (!strcmp(plen[k].name, s->name)) {
            lc = find_local(s->name);
            return lc && lc->slot == plen[k].param ? plen[k].slot : -1;
        }
    return -1;
}

static void str_code_inline(Node *s, Node *i)
{
    Var vs;
    int ps = plen_slot(s);
    if (ps >= 0 && simple(s, &vs)) {
        int zero = new_label(), done = new_label();
        Var vl;
        index_to_d1(i);
        use_slot(ps);
        vl = slot_var(ps, TY_INT);
        cmp_d1_ea(&vl);                                /* largo */
        branch(CC_CC, zero);                           /* (sin signo: también i < 0; y nil, con largo 0) */
        load_a0(&vs);
        load_byte_a0_d1();
        branch(CC_T, done);
        def_label(zero);
        zero_d0();
        def_label(done);
        return;
    }
    int slow = new_label(), zero = new_label(), done = new_label();
    if (simple(s, &vs) && vs.kind != V_CONST) {
        index_to_d1(i);
        load_a0(&vs);
    } else {
        value(s);
        push_d0();
        index_to_d1(i);
        pop_a0();
    }
    str_ours(slow, zero);
    cmp_d1_str_len();
    branch(CC_CC, zero);                               /* (sin signo: también i < 0) */
    load_byte_a0_d1();
    branch(CC_T, done);
    def_label(slow);
    call_a0_d1("_dl_str_code");
    branch(CC_T, done);
    def_label(zero);
    zero_d0();
    def_label(done);
}

/* s.length en línea: de la cabecera si es de Dash; si no, _dl_str_len */
static void str_len_inline(Node *s)
{
    Var vs;
    int ps = plen_slot(s);
    if (ps >= 0) {
        Var vl;
        use_slot(ps);
        vl = slot_var(ps, TY_INT);
        load_var(0, &vl);
        return;
    }
    int slow = new_label(), zero = new_label(), done = new_label();
    if (simple(s, &vs) && vs.kind != V_CONST) load_a0(&vs);
    else {
        value(s);
        move_d0_a0();
    }
    str_ours(slow, zero);
    load_str_len();
    branch(CC_T, done);
    def_label(slow);
    call_a0("_dl_str_len");
    branch(CC_T, done);
    def_label(zero);
    zero_d0();
    def_label(done);
}

/* s[i]: el byte, con signo (char en el C de ./dash) */
static int gen_str_index(Node *n)
{
    str_code_inline(n->a, n->b);
    sext_byte();
    return TY_CHAR;
}

/* s[a:b]: sin a, 0; sin b, hasta el final */
static int gen_str_slice(Node *n)
{
    Node *a[3], from, to;
    memset(&from, 0, sizeof from);
    memset(&to, 0, sizeof to);
    from.kind = to.kind = E_INT;
    from.val = 0;
    to.val = 0x7FFFFFFF;
    a[0] = n->a;
    a[1] = n->b ? n->b : &from;
    a[2] = n->c ? n->c : &to;
    args_to_stack(a, 3, NULL);
    rt_call("_dl_str_slice", 3, 1);
    return TY_STR;
}

static int gen_field(Node *n)
{
    int t = expr_type(n->a);
    if (!strcmp(n->name, "length") && t == TY_STR) {
        str_len_inline(n->a);
        return TY_INT;
    }
    if (!strcmp(n->name, "length") && (IS_ARR(t) || IS_DICT(t))) {
        args_to_stack(&n->a, 1, NULL);
        rt_call(t == TY_STR ? "_dl_str_len" : IS_DICT(t) ? "_dl_dict_length" : "_dl_arr_length", 1, 0);
        return TY_INT;
    }
    fatal_node(n, "(sin --gcc) .%s aún no está", n->name);
    return TY_VOID;
}

/* ---- listas ---- */

/* el texto de d0 como temporal, si no lo es ya (un texto que guarda una lista es suyo) */
/* un elemento para una lista de et: un Int a una lista de Float o de Double, convertido */
static void list_hint(Node *e, int t);

static void elem_value(Node *v, int et)
{
    list_hint(v, et);                                  /* ([[Double]]: la de dentro también) */
    if (et == TY_DOUBLE) dbl_value(v);
    else if (et == TY_FLOAT) float_value(v);
    else if (et == TY_FIXED) fix_value(v);
    else value(v);
}

/* una lista literal que va a un destino de tipo t ([Double]...): guarda eso, no lo de su primer elemento */
static void list_hint(Node *e, int t)
{
    if (e && e->kind == E_LIST && IS_ARR(t) && t != TY_ARR + TY_VOID && !e->type) e->type = t - TY_ARR;
}

static void str_kept(Node *e)
{
    if (is_tmp_expr(e) || e->kind == E_NIL) return;
    push_d0();
    rt_call("_dl_str_tmpcopy", 1, 1);
}

/* [a, b, c]: fresh, con una referencia para una variable (DashArray_from_new); si no, un
   temporal (DashArray_from). Los textos y objetos pasan a ser de la lista (DashArray_own). */
static void gen_list(Node *n, int fresh)
{
    int np = n->args.n, i, kind, all_const = 1, et;
    long k;
    if (!np) {
        zero_d0();
        push_d0();
        rt_call("_dl_arr_create", 1, 1);
        return;
    }
    et = expr_type(n) - TY_ARR;
    kind = elem_kind(et);
    for (i = 0; i < np; i++)
        if (!fold(n->args.v[i], &k)) all_const = 0;
    if (all_const && !kind && et != TY_FLOAT && et != TY_FIXED) {
        /* los números, en los datos */
        uint32_t off = data_align();
        for (i = 0; i < np; i++) {
            fold(n->args.v[i], &k);
            data_elem(k);
        }
        push_data(off);
        push_word(np);
        rt_call(fresh ? "_dl_arr_from_new" : "_dl_arr_from", 2, !fresh);
    } else {
        char *conv = xmalloc(np + 1);
        memset(conv, et == TY_DOUBLE ? 3 : et == TY_FLOAT ? 2 : et == TY_FIXED ? 4 : 0, np);
        args_to_stack(n->args.v, np, conv);
        free(conv);
        push_sp();
        push_word(np);
        rt_call(fresh ? "_dl_arr_from_new" : "_dl_arr_from", 2, !fresh);
        pop_args(np);
    }
    if (kind) {
        push_word(kind);
        push_d0();
        rt_call("_dl_arr_own", 2, 0);
    }
}

/* ---- structs ---- */

/* d0 no puede ser nil: si lo es, "Error: campo de nil (en fuente:línea)" y se acaba */
static void nil_check(void)
{
    if (memcheck) {
        /* --memcheck: avisa y sigue con una zona a cero, como ./dash --memcheck */
        push_d0();
        rt_call("_dl_mc_nn", 1, 0);
        return;
    }
    fail_if_nil(cur_file, cur_line);
}

/* el struct de n en d0 y a0, comprobado (self no: ya se comprobó al llamar al método) */
static Struct *struct_ptr(Node *n, const char *field, int *off, int *ftype)
{
    int t = expr_type(n), f;
    Struct *st;
    if (!IS_STRUCT(t)) return NULL;
    st = &prog->structs.v[t - TY_STRUCT];
    f = field_index(st, field);
    if (f < 0) return NULL;
    value(n);
    if (!(n->kind == E_VAR && !strcmp(n->name, "self"))) nil_check();
    move_d0_a0();
    *off = field_off(f);
    *ftype = st->fields.v[f].type;
    return st;
}

/* ¿es weak el campo de n (p.campo)? */
static int field_weak(Node *n)
{
    int t = expr_type(n->a), f;
    if (!IS_STRUCT(t)) return 0;
    f = field_index(&prog->structs.v[t - TY_STRUCT], n->name);
    return f >= 0 && prog->structs.v[t - TY_STRUCT].fields.v[f].weak;
}

static int gen_struct_field(Node *n)
{
    int off, ft;
    if (!struct_ptr(n->a, n->name, &off, &ft)) return -1;
    load_a0_off(off);
    if (memcheck && field_weak(n)) {
        /* --memcheck: un weak a un objeto ya liberado es un error (y nil), como _DASH_WEAK de ./dash */
        push_d0();
        rt_call("_dl_weak_check", 1, 0);
    }
    return ft;
}

/* p.campo = v: un número va tal cual; un texto, _dash_str_set; un objeto, _dash_obj_set */
static int gen_field_store(Node *target, Node *v)
{
    int off, ft;
    if (!IS_STRUCT(expr_type(target->a))) return 0;
    ft = expr_type(target);
    list_hint(v, ft);
    if (ft == TY_DOUBLE) dbl_value(v);                 /* (un Int o un Float, convertido) */
    else if (ft == TY_FLOAT) float_value(v);
    else if (ft == TY_FIXED) fix_value(v);
    else value(v);
    push_d0();
    if (!struct_ptr(target->a, target->name, &off, &ft))
        fatal_node(target, "%s no es un campo", target->name);
    if ((IS_STRLIKE(ft) || IS_OBJ(ft)) && !field_weak(target)) {
        push_a0_addr(off);
        rt_call(!IS_STRLIKE(ft) ? "_dl_obj_set" : is_tmp_expr(v) ? "_dl_str_set" : "_dl_str_set_copy", 2, 0);
    } else {
        pop_to_a0(off);
    }
    return 1;
}

/* Punto(a, b): los que faltan, con su valor por defecto. fresh: con una referencia para una
   variable (_dash_rc_new_obj); si no, un temporal (_dash_rc_alloc_obj). Los textos se copian
   (_dash_str_set) y los objetos ganan una referencia, como en el constructor de ./dash. */
static int gen_new(Node *n, int si, int fresh)
{
    Struct *st = &prog->structs.v[si];
    int nf = st->fields.n, i;
    Node **vals = xmalloc(sizeof(Node *) * (nf + 1)), zero;
    if (n->args.n > nf) fatal_node(n, "%s tiene %d campos y se le dan %d", st->name, nf, n->args.n);
    for (i = n->args.n; i < nf; i++)      /* solo se pueden omitir los últimos, y si tienen valor por defecto */
        if (!st->fields.v[i].init)
            fatal_node(n, "%s: falta %s (sin valor por defecto; solo se omiten los últimos campos)", st->name,
                       st->fields.v[i].name);
    memset(&zero, 0, sizeof zero);
    zero.kind = E_INT;
    char *conv = xmalloc(nf + 1);
    for (i = 0; i < nf; i++) {
        vals[i] = i < n->args.n ? n->args.v[i] : st->fields.v[i].init ? st->fields.v[i].init : &zero;
        /* un Int a un campo Float o Double: convertido */
        conv[i] = st->fields.v[i].type == TY_FLOAT ? 2 : st->fields.v[i].type == TY_DOUBLE ? 3 :
                  st->fields.v[i].type == TY_FIXED ? 4 : 0;
        list_hint(vals[i], st->fields.v[i].type);
    }
    if (nf) args_to_stack(vals, nf, conv);
    free(conv);
    push_label(desc_label[si]);                        /* el descriptor */
    push_word(struct_bytes(nf));                       /* el tamaño */
    rt_call(fresh ? "_dl_rc_new_obj" : "_dl_rc_alloc_obj", 2, !fresh);
    obj_begin();                                       /* el objeto nuevo, a mano mientras se llena */
    for (i = 0; i < nf; i++) {
        int ft = st->fields.v[i].type, off = field_off(i);
        if (ft == TY_STR && vals[i]->kind == E_STR) {
            /* un literal: el texto fijo de Dash (dash_lit), sin copia */
            obj_field_data(off, dash_lit(vals[i]->str, vals[i]->len));
        } else if (IS_STRLIKE(ft)) {
            obj_field_clear(off);
            push_sp_off(SLOT * (i + 1));               /* el valor (por encima, lo guardado de obj_begin) */
            push_obj_field_addr(off);
            /* un texto que no es un temporal nuevo (una variable, un parámetro) se copia */
            rt_call(is_tmp_expr(vals[i]) ? "_dl_str_set" : "_dl_str_set_copy", 2, 0);
        } else {
            obj_field_from_sp(off, SLOT * (i + 1));
            if (IS_OBJ(ft) && !st->fields.v[i].weak) {
                push_obj_field(off);
                rt_call("_dl_retain", 1, 0);
            }
        }
    }
    obj_end();
    pop_args(nf);
    free(vals);
    return TY_STRUCT + si;
}

/* ---- préstamos: un argumento que la función llamada podría liberar mientras lo usa ----
   (un campo, una global o un elemento de lista: la función puede cambiarlo). Un texto va como
   copia temporal y un objeto con una referencia hasta que se sueltan los temporales de quien
   llama (_dash_obj_lend). Un campo que nada en el programa cambia va tal cual (dashweb D22). */
/* (de qué struct es cada uno, como ./dash: el mismo nombre en otro struct no cuenta; -1 si no se sabe, y entonces
   vale para todos) */
typedef struct { char *name; int st; } SetField;
static struct { SetField *v; int n, cap; } set_fields;   /* campos a los que algo asigna */
static int lookup_global(const char *name);

static void add_set_field(int st, char *name)
{
    int j;
    SetField sf;
    for (j = 0; j < set_fields.n; j++)
        if (set_fields.v[j].st == st && !strcmp(set_fields.v[j].name, name)) return;
    sf.name = name;
    sf.st = st;
    VEC_PUSH(set_fields, sf);
}

static int field_is_set(int st, const char *name)
{
    int j;
    for (j = 0; j < set_fields.n; j++)
        if ((set_fields.v[j].st == st || set_fields.v[j].st < 0) && !strcmp(set_fields.v[j].name, name)) return 1;
    return 0;
}

/* d0 tiene el valor del argumento a: si hace falta, prestado */
static void lend(Node *a)
{
    int t = expr_type(a), shared;
    if (!IS_STRLIKE(t) && !IS_OBJ(t)) return;
    shared = a->kind == E_FIELD || a->kind == E_INDEX ||
             (a->kind == E_VAR && !find_local(a->name) && lookup_global(a->name));
    if (!shared) return;
    if (a->kind == E_FIELD) {
        int ts = expr_type(a->a);
        if (IS_STRUCT(ts) && !field_is_set(ts - TY_STRUCT, a->name)) return;
    }
    push_d0();
    rt_call(IS_STRLIKE(t) ? "_dl_str_tmpcopy" : "_dl_obj_lend", 1, 1);
}

/* p.metodo(args): la función "Struct.metodo" con p (comprobado) delante */
/* el método name de la interfaz t (un Struct con iface), o NULL */
static IfaceMethod *iface_method(int t, const char *name)
{
    Struct *st;
    int i;
    if (!IS_STRUCT(t) || !(st = &prog->structs.v[t - TY_STRUCT])->iface) return NULL;
    for (i = 0; i < st->methods.n; i++)
        if (!strcmp(st->methods.v[i].name, name)) return &st->methods.v[i];
    return NULL;
}

/* o.metodo(args) con o de una interfaz: el de su struct, por la tabla de métodos de su _DashType (la cabecera del
   objeto, a -4; la tabla, a 8 del tipo), como ./dash */
static int gen_iface_call(Node *n, int t)
{
    IfaceMethod *m = iface_method(t, n->name);
    int i;
    if (!m) fatal_node(n, "%s no tiene el método %s", prog->structs.v[t - TY_STRUCT].name, n->name);
    if (n->args.n != m->nparams)
        fatal_node(n, "%s pide %d argumentos y se le dan %d", n->name, m->nparams, n->args.n);
    for (i = n->args.n - 1; i >= 0; i--) push_value(n->args.v[i]);
    value(n->a);
    nil_check();
    push_d0();                                         /* self */
    call_method(m->slot);
    pop_args(n->args.n + 1);
    forget_d0();
    if (IS_STRLIKE(m->ret) || IS_OBJ(m->ret)) made_tmp = 1;   /* lo devuelto es un temporal de aquí */
    return m->ret;
}

static int gen_method(Node *n, int t)
{
    char name[256];
    Node call, nn;
    int idx = 0, r;
    if (prog->structs.v[t - TY_STRUCT].iface) return gen_iface_call(n, t);
    snprintf(name, sizeof name, "%s.%s", prog->structs.v[t - TY_STRUCT].name, n->name);
    if (!find_func(name, &idx)) fatal_node(n, "%s no tiene el método %s", prog->structs.v[t - TY_STRUCT].name, n->name);
    memset(&call, 0, sizeof call);
    memset(&nn, 0, sizeof nn);
    call.kind = E_CALL;
    call.line = n->line;
    call.col = n->col;
    call.name = prog->funcs.v[idx].name;
    nn.kind = E_NN;
    nn.line = n->line;
    nn.a = n->a;
    VEC_PUSH(call.args, &nn);
    {
        int i;
        for (i = 0; i < n->args.n; i++) VEC_PUSH(call.args, n->args.v[i]);
    }
    r = gen_expr(&call);
    free(call.args.v);
    return r;
}

/* ¿La lista es una variable local (en un registro o en el marco)? Entonces se puede leer en cualquier momento: nada
   de lo que se calcula entre medias la cambia (las globales sí podría cambiarlas una función) */
static int arr_local(Node *a, Var *va)
{
    if (a->kind != E_VAR || !find_local(a->name) || !simple(a, va)) return 0;
    return va->kind == V_REG || va->kind == V_LOCAL;
}

/* a[i] de una lista, en línea (como DashArray_get: nil o un índice fuera de rango dan 0; data en 0(a), length
   en 4(a)): lo que gcc hace con el camino por C, en vez de llamar a dl_arr_get con los argumentos en la pila */
static int gen_arr_index(Node *n)
{
    int t = expr_type(n->a);
    Var va;
    if (arr_local(n->a, &va)) {
        /* la lista es una variable local: el índice primero y la lista directa a a0, sin pasar por la pila */
        value(n->b);
        load_a0(&va);
    } else {
        value(n->a);
        push_d0();
        value(n->b);
        pop_a0();
    }
    arr_get();
    return t == TY_ARR + TY_VOID ? TY_INT : t - TY_ARR;
}

static int gen_arr_slice(Node *n)
{
    Node *a[3], from, to;
    memset(&from, 0, sizeof from);
    memset(&to, 0, sizeof to);
    from.kind = to.kind = E_INT;
    to.val = 0x7FFFFFFF;
    a[0] = n->a;
    a[1] = n->b ? n->b : &from;
    a[2] = n->c ? n->c : &to;
    args_to_stack(a, 3, NULL);
    rt_call("_dl_arr_slice", 3, 1);
    return expr_type(n->a);
}

/* Una lista que aún no sabe qué guarda ([]) lo aprende con lo primero que se le mete */
static int learn_elem(Node *list, Node *v)
{
    int t = expr_type(list), et = expr_type(v);
    if (t == TY_ARR + TY_VOID && list->kind == E_VAR) {
        Local *lc = find_local(list->name);
        if (lc && et != TY_NIL && et != TY_VOID) lc->type = TY_ARR + et;
        return et;
    }
    return t - TY_ARR;
}

/* lista.metodo(args): push, insert, pop, remove, clear */
static int gen_list_method(Node *n)
{
    int t = expr_type(n->a), et, kind;
    Node *a[3];
    if (!strcmp(n->name, "push") || !strcmp(n->name, "insert")) {
        int na = !strcmp(n->name, "push") ? 1 : 2;
        if (n->args.n != na) fatal_node(n, "%s pide %d argumentos", n->name, na);
        et = learn_elem(n->a, n->args.v[na - 1]);
        kind = elem_kind(et);
        a[0] = n->a;
        a[1] = n->args.v[0];
        if (na == 2) a[2] = n->args.v[1];
        if (kind == 2) {
            /* el último, como temporal */
            int i;
            reserve_args(na + 1);
            for (i = 0; i <= na; i++) {
                if (i == na) elem_value(a[i], et);
                else value(a[i]);
                if (i == na) str_kept(a[i]);
                store_d0_arg(i);
            }
        } else {
            char conv[3] = {0, 0, 0};
            conv[na] = et == TY_FLOAT ? 2 : et == TY_FIXED ? 4 : 0;
            list_hint(a[na], et);
            args_to_stack(a, na + 1, conv);
        }
        {
            /* (el nombre se guarda en la reubicación: tiene que ser fijo) */
            static const char *const push_sym[] = {"_dl_arr_push", "_dl_arr_push_obj", "_dl_arr_push_str"};
            static const char *const insert_sym[] = {"_dl_arr_insert", "_dl_arr_insert_obj", "_dl_arr_insert_str"};
            rt_call((na == 1 ? push_sym : insert_sym)[kind], na + 1, 0);
        }
        return TY_VOID;
    }
    if (!strcmp(n->name, "sort")) {
        /* l.sort(f): f(a, b) -> Bool (a va antes que b) o -> Int (negativo si a va antes), como ./dash */
        Node *f = n->args.n == 1 ? n->args.v[0] : NULL;
        int fi, boolean = 0;
        Func *fn;
        if (!f) fatal_node(n, "sort pide 1 argumento (la función que compara)");
        if (f->kind == E_FUNCREF && (fn = find_func(f->name, &fi)) != NULL)
            boolean = fn->boolret || (fn->declared && fn->ret == TY_BOOL);
        load_imm(0, boolean);
        push_d0();
        a[0] = n->a;
        a[1] = f;
        args_to_stack(a, 2, NULL);
        rt_call("_dl_arr_sort", 3, 0);
        return TY_VOID;
    }
    if (!strcmp(n->name, "pop")) {
        et = t == TY_ARR + TY_VOID ? TY_INT : t - TY_ARR;
        kind = elem_kind(et);
        args_to_stack(&n->a, 1, NULL);
        rt_call(kind == 2 ? "_dl_arr_pop_str" : kind == 1 ? "_dl_arr_pop_obj" : "_dl_arr_pop", 1, kind != 0);
        return et;
    }
    if (!strcmp(n->name, "remove")) {
        a[0] = n->a;
        if (n->args.n != 1) fatal_node(n, "remove pide 1 argumento");
        a[1] = n->args.v[0];
        args_to_stack(a, 2, NULL);
        rt_call("_dl_arr_remove", 2, 0);
        return TY_VOID;
    }
    if (!strcmp(n->name, "clear")) {
        args_to_stack(&n->a, 1, NULL);
        rt_call("_dl_arr_clear", 1, 0);
        return TY_VOID;
    }
    fatal_node(n, "(sin --gcc) .%s aún no está", n->name);
    return TY_VOID;
}

/* ---- diccionarios ---- */
static int expr_type(Node *n);

/* {k: v, ...}: DashDict_from(kind, n, claves, valores) (o fromi con claves Int); {} es DashDict_new(0) */
static int gen_dict(Node *n)
{
    int t = expr_type(n), np = n->args.n / 2, i, kind, ikeys;
    Node **keys, **vals;
    if (!np) {
        zero_d0();
        push_d0();
        rt_call("_dl_dict_new", 1, 1);
        return t;
    }
    kind = elem_kind(dict_val(t));
    ikeys = dict_types.v[t - TY_DICT].key == TY_INT;
    keys = xmalloc(sizeof(Node *) * np);
    vals = xmalloc(sizeof(Node *) * np);
    for (i = 0; i < np; i++) {
        keys[i] = n->args.v[2 * i];
        vals[i] = n->args.v[2 * i + 1];
    }
    /* los valores y luego las claves, cada lista en su array de la pila */
    args_to_stack(vals, np, NULL);
    if (np == 1) {
        /* (con uno solo, args_to_stack lo mete con push: igual vale como array) */
    }
    args_to_stack(keys, np, NULL);
    push_sp_addr(SLOT * np);                           /* los valores */
    push_sp_addr(4);                                   /* las claves: justo encima */
    push_word(np);
    push_word(kind);
    rt_call(ikeys ? "_dl_dict_fromi" : "_dl_dict_from", 4, 1);
    pop_args(2 * np);
    free(keys);
    free(vals);
    return t;
}

static int dict_ikeys(int t) { return dict_types.v[t - TY_DICT].key == TY_INT; }

/* una clave literal de un diccionario de textos: su hash (el _dash_dict_hash del runtime), en la pila antes que los
   argumentos (va el último): dl_dict_*_h no lo calcula en cada llamada */
static int push_key_hash(int t, Node *k)
{
    uint32_t h = 5381;
    int i;
    if (dict_ikeys(t) || k->kind != E_STR || (int)strlen(k->str) != k->len) return 0;
    for (i = 0; i < k->len; i++) h = (h << 5) + h + (unsigned char)k->str[i];
    push_long(h);
    return 1;
}

/* d[k] */
/* for k in d.keys() por la tabla (gen_keys_loop): d[k] dentro es el valor de la misma casilla, sin buscar la
   clave. Solo si d es una variable que el cuerpo no pasa a nada (ni llamadas ni métodos: nada le puede meter
   claves, que moverían la tabla) y k no se reasigna */
typedef struct { const char *d, *k; int d_local, k_slot, depth, dict_slot, idx_slot; } KLoop;
static struct { KLoop *v; int n, cap; } kloops;

static int dict_passed(Node *e, const char *d)
{
    int i;
    if (!e) return 0;
    if (e->kind == E_CALL || e->kind == E_MCALL || e->kind == S_ASSIGN || e->kind == S_STORE || e->kind == S_RETURN ||
        e->kind == E_LIST || e->kind == E_DICT) {
        /* d como argumento, receptor de un método (salvo leer), valor asignado o devuelto */
        if (e->kind == E_MCALL && e->a && e->a->kind == E_VAR && !strcmp(e->a->name, d) &&
            strcmp(e->name, "has") && strcmp(e->name, "get") && strcmp(e->name, "keys") && strcmp(e->name, "length"))
            return 1;
        for (i = 0; i < e->args.n; i++)
            if (e->args.v[i]->kind == E_VAR && !strcmp(e->args.v[i]->name, d)) return 1;
        if ((e->kind == S_ASSIGN || e->kind == S_RETURN) && e->a && e->a->kind == E_VAR && !strcmp(e->a->name, d))
            return 1;
        if (e->kind == S_STORE && e->a && e->a->kind == E_VAR && !strcmp(e->a->name, d)) return 1;
    }
    if (dict_passed(e->a, d) || dict_passed(e->b, d) || dict_passed(e->c, d)) return 1;
    for (i = 0; i < e->args.n; i++)
        if (dict_passed(e->args.v[i], d)) return 1;
    for (i = 0; i < e->body.n; i++)
        if (dict_passed(e->body.v[i], d)) return 1;
    for (i = 0; i < e->els.n; i++)
        if (dict_passed(e->els.v[i], d)) return 1;
    return 0;
}

/* ¿d[k] de un for k in d.keys() que se está recorriendo? Su KLoop, o NULL */
static KLoop *kloop_of(Node *d, Node *k)
{
    int i;
    Local *ld, *lk;
    if (d->kind != E_VAR || k->kind != E_VAR) return NULL;
    for (i = kloops.n - 1; i >= 0; i--) {
        KLoop *kl = &kloops.v[i];
        if (kl->depth != inl_stack.n || strcmp(kl->d, d->name) || strcmp(kl->k, k->name)) continue;
        ld = find_local(d->name);
        lk = find_local(k->name);
        if (!ld || ld->slot != kl->d_local || !lk || lk->slot != kl->k_slot) return NULL;
        return kl;
    }
    return NULL;
}

static int gen_dict_get(Node *n)
{
    Node *a[2];
    int t = expr_type(n->a);
    KLoop *kl = kloop_of(n->a, n->b);
    int slow = -1, done = -1;
    if (kl && !dict_ikeys(t)) {
        /* solo si la casilla aún guarda k (i < cap y keys[i] == k): el cuerpo puede cambiar el diccionario por
           otro nombre (un alias, un campo, una global) y moverlo o quitarle claves; si no, la búsqueda */
        Var vd, vi, vk;
        slow = new_label();
        done = new_label();
        use_slot(kl->dict_slot);
        vd = slot_var(kl->dict_slot, t);
        load_a0(&vd);
        use_slot(kl->idx_slot);
        vi = slot_var(kl->idx_slot, TY_INT);
        load_var(0, &vi);
        dict_slot(slow);
        use_slot(kl->k_slot);
        vk = slot_var(kl->k_slot, TY_STR);
        move_ea_d1(&vk);
        dict_slot_key(slow);
        dict_slot_val();
        branch(CC_T, done);
        def_label(slow);
    }
    a[0] = n->a;
    a[1] = n->b;
    if (push_key_hash(t, n->b)) {
        args_to_stack(a, 2, NULL);
        rt_call("_dl_dict_get_h", 3, 0);
        if (done >= 0) def_label(done);
        return dict_val(t);
    }
    args_to_stack(a, 2, NULL);
    rt_call(dict_ikeys(t) ? "_dl_dict_geti" : "_dl_dict_get", 2, 0);
    if (done >= 0) def_label(done);
    return dict_val(t);
}

/* Un diccionario que aún no sabe qué guarda ({}) lo aprende con lo primero que se le mete */
static int learn_val(Node *d, Node *k, Node *v)
{
    int t = expr_type(d), vt = expr_type(v);
    if (dict_types.v[t - TY_DICT].val == TY_VOID && d->kind == E_VAR) {
        Local *lc = find_local(d->name);
        if (lc && vt != TY_NIL && vt != TY_VOID)
            lc->type = dict_type(expr_type(k) == TY_INT ? TY_INT : TY_STR, vt);
        return vt;
    }
    return dict_val(t);
}

/* d[k] = v: un texto va como temporal (_str_kept de ./dash), un objeto gana una referencia */
static void gen_dict_set(Node *target, Node *v)
{
    int t = expr_type(target->a), vt = learn_val(target->a, target->b, v), kind = elem_kind(vt), i, ik;
    static const char *const sym[2][3] = {{"_dl_dict_set", "_dl_dict_set_obj", "_dl_dict_set_str"},
                                          {"_dl_dict_seti", "_dl_dict_set_obji", "_dl_dict_set_stri"}};
    Node *a[3];
    t = expr_type(target->a);
    ik = dict_ikeys(t);
    a[0] = target->a;
    a[1] = target->b;
    a[2] = v;
    reserve_args(3);
    for (i = 0; i < 3; i++) {
        if (i == 2) elem_value(a[i], vt);
        else value(a[i]);
        if (i == 2 && kind == 2) str_kept(v);
        store_d0_arg(i);
    }
    rt_call(sym[ik][kind], 3, 0);
}

/* d.has(k), d.remove(k), d.get(k, defecto), d.keys(), d.clear() */
static int gen_dict_method(Node *n)
{
    int t = expr_type(n->a), ik = dict_ikeys(t);
    Node *a[3];
    int na = n->args.n;
    a[0] = n->a;
    if (na >= 1) a[1] = n->args.v[0];
    if (na >= 2) a[2] = n->args.v[1];
    if (!strcmp(n->name, "has") && na == 1 && push_key_hash(t, a[1])) {
        args_to_stack(a, 2, NULL);
        rt_call("_dl_dict_has_h", 3, 0);
        return TY_BOOL;
    }
    if (!strcmp(n->name, "get") && na == 2 && push_key_hash(t, a[1])) {
        args_to_stack(a, 3, NULL);
        rt_call("_dl_dict_get_or_h", 4, 0);
        return dict_val(t);
    }
    if (!strcmp(n->name, "has") && na == 1) {
        args_to_stack(a, 2, NULL);
        rt_call(ik ? "_dl_dict_hasi" : "_dl_dict_has", 2, 0);
        return TY_BOOL;
    }
    if (!strcmp(n->name, "remove") && na == 1) {
        args_to_stack(a, 2, NULL);
        rt_call(ik ? "_dl_dict_removei" : "_dl_dict_remove", 2, 0);
        return TY_VOID;
    }
    if (!strcmp(n->name, "get") && na == 2) {
        args_to_stack(a, 3, NULL);
        rt_call(ik ? "_dl_dict_get_ori" : "_dl_dict_get_or", 3, 0);
        return dict_val(t);
    }
    if (!strcmp(n->name, "keys") && na == 0) {
        args_to_stack(a, 1, NULL);
        rt_call("_dl_dict_keys", 1, 1);
        return TY_ARR + dict_types.v[t - TY_DICT].key;
    }
    if (!strcmp(n->name, "clear") && na == 0) {
        args_to_stack(a, 1, NULL);
        rt_call("_dl_dict_clear", 1, 0);
        return TY_VOID;
    }
    fatal_node(n, "un diccionario no tiene .%s con %d argumentos", n->name, na);
    return TY_VOID;
}

/* a[i] = v */
static void gen_arr_store(Node *target, Node *v)
{
    int et = learn_elem(target->a, v), kind = elem_kind(et), i;
    Node *a[3];
    Var va, vi;
    a[0] = target->a;
    a[1] = target->b;
    a[2] = v;
    if (kind == 0 && arr_local(a[0], &va)) {
        /* la lista es una variable local: el índice a d1 (simple, o por la pila si no), el valor a d0 y la lista a a0 */
        if (simple(a[1], &vi) && (vi.kind == V_CONST || vi.type == TY_INT || vi.type == TY_CHAR)) {
            elem_value(a[2], et);
            load_var(1, &vi);                          /* move.l i,d1 */
        } else {
            value(a[1]);
            push_d0();
            elem_value(a[2], et);
            pop_d1();
        }
        load_a0(&va);
        arr_put();
        return;
    }
    if (kind == 0) {
        /* una lista de valores (no textos ni objetos, que llevan cuenta de referencias): en línea, como
           DashArray_set (nil o un índice fuera de rango no hacen nada) */
        reserve2();
        value(a[0]);
        store_d0_arg(0);
        value(a[1]);
        store_d0_arg(1);
        elem_value(a[2], et);
        pop_a0();
        pop_d1();
        arr_put();
        return;
    }
    reserve_args(3);
    for (i = 0; i < 3; i++) {
        if (i == 2) elem_value(a[i], et);
        else value(a[i]);
        if (i == 2 && kind == 2) str_kept(v);
        store_d0_arg(i);
    }
    rt_call(kind == 2 ? "_dl_arr_set_str" : kind == 1 ? "_dl_arr_set_obj" : "_dl_arr_set", 3, 0);
}

/* Libera los textos de las variables de la función o copia actual con profundidad
   >= from_depth (all_frame: todas las de la función o copia) */
static void free_owned(int from_depth, int all_frame)
{
    int i;
    for (i = locals.n - 1; i >= 0; i--) {
        Local *lc = &locals.v[i];
        Var v;
        if (!lc->owned || lc->frame != cur_frame || (!all_frame && lc->depth < from_depth)) continue;
        use_slot(lc->slot);
        v = slot_var(lc->slot, lc->type);
        push_ea(&v);
        rt_call(lc->owned == 2 ? "_dl_release" : "_dl_str_free", 1, 0);
    }
}

static int has_owned(int from_depth, int all_frame)
{
    int i;
    for (i = 0; i < locals.n; i++)
        if (locals.v[i].owned && locals.v[i].frame == cur_frame && (all_frame || locals.v[i].depth >= from_depth))
            return 1;
    return 0;
}

/* ---- marcas de temporales: en la pila mientras dura el bucle o la función ----
   En la primera pasada se ponen todas y se apunta si hacía falta cada una (si algo dejó
   temporales); en la segunda solo van las que hacían falta. */
typedef struct { int idx, on, saved, sp; } MarkScope;
static struct { int *v; int n, cap; } mark_need;
static int mark_seq;

static MarkScope mark_begin(void)
{
    MarkScope m;
    m.idx = mark_seq++;
    if (pass == 1) {
        if (m.idx >= mark_need.n) VEC_PUSH(mark_need, 0);
        mark_need.v[m.idx] = 0;
    }
    m.on = pass == 1 || (m.idx < mark_need.n && mark_need.v[m.idx]);
    m.saved = made_tmp;
    made_tmp = 0;
    if (m.on) {
        jsr_sym("_dl_tmp_mark");
        push_d0();
    }
    m.sp = sp_depth;
    return m;
}

static void mark_release(MarkScope *m)
{
    int skip;
    if (!m->on) return;
    skip = new_label();
    tmp_newer(sp_depth - m->sp, skip);
    push_sp_off(sp_depth - m->sp);                     /* la marca */
    rt_call("_dl_tmp_release", 1, 0);
    def_label(skip);
}

/* al acabar: fuera los temporales y la marca */
static void mark_end(MarkScope *m)
{
    if (pass == 1) mark_need.v[m->idx] = made_tmp;
    made_tmp = m->saved;
    if (!m->on) return;
    mark_release(m);
    pop_args(1);
}

#include "t68k_arith.c"

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
    if (n->kind == E_BIN && (n->op == P_PLUS || n->op == P_MINUS) && expr_type(n) == TY_INT) {
        /* x + k, x - k y k + x: el rango de x, movido (si sigue dentro de 32 bits) */
        long k, a, b;
        long long l2, h2;
        if (fold(n->b, &k) && var_range(n->a, &a, &b)) {
            if (n->op == P_MINUS) k = -k;
        } else if (n->op == P_PLUS && fold(n->a, &k) && var_range(n->b, &a, &b)) {
        } else return 0;
        l2 = (long long)a + k;
        h2 = (long long)b + k;
        if (l2 < INT32_MIN || h2 > INT32_MAX || b == INT32_MAX) return 0;
        *lo = (long)l2;
        *hi = (long)h2;
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

#include "t68k_opt.c"

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
        if (n->op == P_AMP) and_ea(&v);
        else or_ea(&v);
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
        if (bin_pop(n->op)) return;
        move_d0_d1();
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
    int cc = cmp_cc(n->op), ta = expr_type(n->a), tb = expr_type(n->b);

    /* x == nil: el puntero */
    if (ta == TY_NIL || tb == TY_NIL) {
        if (ta == TY_NIL && tb == TY_NIL) {
            load_imm(0, 0);
        } else {
            value(ta == TY_NIL ? n->b : n->a);
            tst_d0();
        }
        return cc;
    }
    /* Fixed con un Int: el Int, Fixed(lado); dos Fixed se comparan como enteros */
    if ((ta == TY_FIXED) != (tb == TY_FIXED) && ta != TY_FLOAT && tb != TY_FLOAT && ta != TY_DOUBLE &&
        tb != TY_DOUBLE) {
        Node c = *n, wrap;
        int r;
        memset(&wrap, 0, sizeof wrap);
        wrap.kind = E_CALL;
        wrap.name = "Fixed";
        wrap.line = n->line;
        wrap.col = n->col;
        wrap.file = n->file;
        VEC_PUSH(wrap.args, ta == TY_FIXED ? n->b : n->a);
        if (ta == TY_FIXED) c.b = &wrap;
        else c.a = &wrap;
        r = gen_compare(&c);
        free(wrap.args.v);
        return r;
    }
    /* Double: dl_d_cmp da -1, 0, 1 o 2 (nan: solo != es cierto, como en C) */
    if (ta == TY_DOUBLE || tb == TY_DOUBLE) {
        Node *a[2];
        static const char conv[2] = {3, 3};
        a[0] = n->a;
        a[1] = n->b;
        args_to_stack(a, 2, conv);
        rt_call("_dl_d_cmp", 2, 0);
        if (n->op == P_EQ || n->op == P_NE) {
            tst_d0();
            return cc;
        }
        dbl_cmp_order(n->op == P_GT || n->op == P_GE);   /* <, <=, >, >=: 2 (nan) tiene que dar falso */
        return cc;
    }
    /* Float: __cmpsf2 da -1, 0 o 1 */
    if (ta == TY_FLOAT || tb == TY_FLOAT) {
        Node *a[2];
        static const char conv[2] = {2, 2};
        a[0] = n->a;
        a[1] = n->b;
        args_to_stack(a, 2, conv);
        rt_call("___cmpsf2", 2, 0);
        tst_d0();
        return cc;
    }
    /* un texto == o != un literal: letra a letra en línea (hasta 8; de uno más largo, las dos primeras y el resto
       con dl_str_cmp), sin llamar a nada si ya difiere la primera: _se_hereda de Tachyon son 20 seguidas. nil no es
       igual a ningún literal. (Hasta 24 sacaba siempre el fallo de memoria de D16 en Tachyon) */
    if (ta == TY_STR && tb == TY_STR && (n->op == P_EQ || n->op == P_NE) &&
        ((n->b->kind == E_STR && n->a->kind != E_STR) || (n->a->kind == E_STR && n->b->kind != E_STR))) {
        Node *lit = n->b->kind == E_STR ? n->b : n->a, *s = lit == n->b ? n->a : n->b;
        int i, ok, done, len = lit->len, inl = len <= 8 ? len : 2;
        if ((int)strlen(lit->str) == len) {
            value(s);
            tst_d0();
            ok = new_label();
            done = new_label();
            branch(CC_NE, ok);
            set_ne();                                  /* nil: distinto */
            branch(CC_T, done);
            def_label(ok);
            move_d0_a0();
            for (i = 0; i < inl; i++) {
                cmp_byte_next((unsigned char)lit->str[i]);
                branch(CC_NE, done);
            }
            if (inl == len) {
                tst_byte_a0();                         /* el final */
            } else {
                pea_string(lit->str + inl, len - inl);
                push_a0();
                rt_call("_dl_str_cmp", 2, 0);
                test_d0();
            }
            def_label(done);
            return cc;
        }
    }
    /* textos: el signo de strcmp (nil va antes que cualquier texto) */
    if (ta == TY_STR && tb == TY_STR) {
        Node *a[2];
        a[0] = n->a;
        a[1] = n->b;
        args_to_stack(a, 2, NULL);
        rt_call("_dl_str_cmp", 2, 0);
        tst_d0();
        return cc;
    }
    /* un carácter con un texto de uno: el código del carácter, con signo como char */
    if ((ta == TY_CHAR && n->b->kind == E_STR && n->b->len == 1) ||
        (tb == TY_CHAR && n->a->kind == E_STR && n->a->len == 1)) {
        Node c = *n, lit;
        Node *s = ta == TY_CHAR ? n->b : n->a;
        memset(&lit, 0, sizeof lit);
        lit.kind = E_INT;
        lit.val = (signed char)s->str[0];
        if (ta == TY_CHAR) c.b = &lit;
        else c.a = &lit;
        return gen_compare(&c);
    }

    /* x % 2^s == 0: basta con mirar los bits bajos, sea cual sea el signo */
    if ((cc == CC_EQ || cc == CC_NE) && fold(n->b, &k) && k == 0 && n->a->kind == E_BIN &&
        n->a->op == P_PERCENT && fold(n->a->b, &k) && pow2(k)) {
        uint32_t mask = (k < 0 ? 0u - (uint32_t)k : (uint32_t)k) - 1;
        if (n->a->a->kind == E_VAR && simple(n->a->a, &va) && va.kind != V_CONST) {
            if (mask == 1 && va.kind == V_REG) {
                test_bit0(va.reg);
                return cc;
            }
            if (mask <= 127) {
                load_imm(0, (long)mask);
                and_ea(&va);
                return cc;
            }
            load_var(0, &va);
        } else {
            value(n->a->a);
        }
        and_imm(mask);
        return cc;
    }
    if (simple(n->b, &vb)) {
        if (vb.kind == V_CONST && n->a->kind == E_VAR && simple(n->a, &va) && va.kind != V_CONST) {
            if (vb.val == 0) {
                if (!flags_for(&va, cc)) tst_ea(&va);
            } else if (va.kind == V_REG && vb.val >= -128 && vb.val <= 127) {
                load_imm(0, vb.val);
                cmp_reg_ea(va.reg, NULL);              /* dA con d0 */
            } else {
                cmp_imm_ea(vb.val, &va);
            }
            return cc;
        }
        if (vb.kind != V_CONST && n->a->kind == E_VAR && simple(n->a, &va) && va.kind == V_REG) {
            cmp_reg_ea(va.reg, &vb);                   /* dA con b */
            return cc;
        }
        value(n->a);
        if (vb.kind == V_CONST && vb.val == 0) tst_d0();
        else cmp_reg_ea(0, &vb);                       /* d0 con b */
        return cc;
    }
    if (simple(n->a, &va)) {
        /* b - a: la condición al revés */
        value(n->b);
        cmp_reg_ea(0, &va);                            /* d0 con a */
        return swap_cc(cc);
    }
    value(n->a);
    push_d0();
    value(n->b);
    move_d0_d1();
    pop_d0();
    cmp_d0_d1();
    return cc;
}


/* funciones del runtime: argumentos Int, o S para un texto literal */
static const struct { const char *name, *sym, *args; int ret; } builtins[] = {
    {"bench_start", "__bench_start", "", TY_VOID},
    {"Wait", "__dash_wait", "I", TY_VOID},
    {"bench_end", "__bench_end", "SI", TY_VOID},
    {NULL, NULL, NULL, 0}
};
static long sink_off = -1;

/* Un builtin de ./dash (compiler/amiga_builtins.py): su envoltorio db_nombre de la librería, con los
   argumentos que falten a 0. Si guarda lo que recibe, un texto o un objeto pasa escapado (se queda hasta
   el final), como en ./dash. */
static int gen_dash_builtin(Node *n)
{
    int b, i, np;
    char *sym;
    for (b = 0; b < builtin_count; b++)
        if (!strcmp(builtin_info[b].name, n->name)) break;
    if (b == builtin_count) fatal_node(n, "la función %s no existe", n->name);
    sym = xmalloc(strlen(n->name) + 5);
    strcpy(sym, "_db_");
    strcat(sym, n->name);
    if (!runtime_has(sym))
        fatal_node(n, "(sin --gcc) el builtin %s aún no está (ventanas y gráficos, Double...)", n->name);
    np = builtin_info[b].nparams;
    if (n->args.n > np) fatal_node(n, "%s pide %d argumentos y se le dan %d", n->name, np, n->args.n);
    if (np) {
        reserve_args(np);
        for (i = 0; i < np; i++) {
            if (i < n->args.n) {
                Node *a = n->args.v[i];
                int t;
                if (builtin_info[b].dparams >> i & 1) {
                    dbl_value(a);                      /* un parámetro Double: una caja */
                    t = TY_DOUBLE;
                } else {
                    t = gen_expr(a);
                    need_value(a, t);
                }
                if (builtin_info[b].keeps && ((t == TY_STR && a->kind != E_STR) || IS_OBJ(t))) {
                    push_d0();
                    rt_call(t == TY_STR ? "_dl_str_escape" : "_dl_obj_escape", 1, 0);
                }
            } else {
                zero_d0();                             /* el que falta */
            }
            store_d0_arg(i);
        }
    }
    switch (builtin_info[b].ret) {
    case 0: rt_call(sym, np, 0); return TY_VOID;
    case 1: rt_call(sym, np, 0); return TY_INT;
    case 2: rt_call(sym, np, 0); return TY_BOOL;
    case 3: rt_call(sym, np, 1); return TY_STR;
    case 5: rt_call(sym, np, 1); return TY_DOUBLE;
    default: rt_call(sym, np, 1); return TY_ARR + TY_STR;
    }
}

/* task_start con una función de Dash: corre en otro proceso a la vez que el programa, y la memoria del runtime
   (textos, listas, structs, Double, sus temporales) es de uno solo. Solo enteros, Bool, Float, globales de esos,
   builtins que no dan textos ni listas, @extern y otras funciones así; un texto literal, solo para Print o
   como argumento. Da por qué no (y dónde), o NULL. */
static const char *task_impure(Node *n, int lit_ok, int *visited, Node **at);

static const char *task_impure_list(NodeList *l, int lit_ok, int *visited, Node **at)
{
    int i;
    const char *r;
    for (i = 0; i < l->n; i++)
        if ((r = task_impure(l->v[i], lit_ok, visited, at))) return r;
    return NULL;
}

static const char *task_impure_func(int idx, int *visited, Node **at)
{
    Func *f = &prog->funcs.v[idx];
    int i;
    if (visited[idx]) return NULL;
    visited[idx] = 1;
    if (f->native) return f->ret == TY_STR ? "llamar a una función de C que da un texto" : NULL;
    for (i = 0; i < f->params.n; i++)
        if (f->params.v[i].type != TY_INT && f->params.v[i].type != TY_BOOL && f->params.v[i].type != TY_FLOAT)
            return "recibir un parámetro que no es Int, Bool ni Float";
    if (f->ret != TY_VOID && f->ret != TY_INT && f->ret != TY_BOOL && f->ret != TY_FLOAT)
        return "devolver algo que no es Int, Bool ni Float";
    return task_impure_list(&f->body, 0, visited, at);
}

static const char *task_impure(Node *n, int lit_ok, int *visited, Node **at)
{
    const char *r = NULL;
    int i;
    if (!n) return NULL;
    *at = n;
    switch (n->kind) {
    case E_STR:
        return lit_ok ? NULL : "usar textos";
    case E_INTERP: case E_LIST: case E_DICT: case E_INDEX: case E_SLICE: case E_FIELD: case E_MCALL:
        return "usar textos, listas, diccionarios ni structs";
    case S_STORE: case S_FOREACH:
        return "usar listas ni structs";
    case S_WINDOW: case S_EVLOOP: case S_ON: case S_STOP:
        return "usar ventanas ni eventos";
    case E_VAR:
        for (i = 0; i < prog->globals.n; i++)
            if (!strcmp(prog->globals.v[i].name, n->name)) {
                int t = global_type[i];
                if (IS_STRLIKE(t) || IS_OBJ(t) || t == TY_FIXED) return "usar un global que no es Int, Bool ni Float";
            }
        for (i = 0; i < prog->consts.n; i++)
            if (!strcmp(prog->consts.v[i].name, n->name) && prog->consts.v[i].value->kind == E_STR && !lit_ok)
                return "usar textos";
        return NULL;
    case S_VAR:
        if (n->type && n->type != TY_INT && n->type != TY_BOOL && n->type != TY_FLOAT)
            return "tener una variable que no es Int, Bool ni Float";
        break;
    case S_PRINT:
        return task_impure(n->a, 1, visited, at);
    case E_CALL: {
        int idx, b;
        Func *f = find_func(n->name, &idx);
        if (!f && find_struct(n->name) >= 0) return "crear structs";
        if (!f && lookup(n->name).kind != V_NONE) return "llamar a una función guardada en una variable";
        if (f) {
            if ((r = task_impure_func(idx, visited, at))) return r;
        } else {
            for (b = 0; builtins[b].name; b++)
                if (!strcmp(builtins[b].name, n->name)) break;
            if (!builtins[b].name) {
                if (!strcmp(n->name, "Fixed") || !strcmp(n->name, "Double") || !strcmp(n->name, "String"))
                    return "usar Fixed, Double ni textos";
            } else if (builtins[b].ret >= 3) {
                return "llamar a un builtin que da un texto, una lista o un Double";
            }
        }
        *at = n;
        return task_impure_list(&n->args, 1, visited, at);
    }
    default:
        break;
    }
    if ((r = task_impure(n->a, 0, visited, at)) || (r = task_impure(n->b, 0, visited, at)) ||
        (r = task_impure(n->c, 0, visited, at)) || (r = task_impure_list(&n->args, 0, visited, at)) ||
        (r = task_impure_list(&n->body, 0, visited, at)) || (r = task_impure_list(&n->els, 0, visited, at)))
        return r;
    return NULL;
}

static int gen_builtin(Node *n)
{
    int i, b;
    if (!strcmp(n->name, "bench_sink")) {
        /* guarda el valor donde no se pueda quitar: un move.l, como el volatile de bench_lib.dash */
        Var v;
        Var src;
        if (n->args.n != 1) fatal_node(n, "bench_sink pide 1 argumento");
        if (sink_off < 0) {
            sink_off = data_word(0);
        }
        if (n->args.v[0]->kind == E_VAR && simple(n->args.v[0], &src) && src.kind != V_CONST) {
            store_var_data(&src, sink_off);            /* al sumidero */
            return TY_VOID;
        }
        value(n->args.v[0]);
        v.kind = V_GLOBAL;
        v.off = (int)sink_off;
        store_d0(&v);
        return TY_VOID;
    }
    if ((!strcmp(n->name, "task_start") || !strcmp(n->name, "task_start_with")) && n->args.n >= 1 &&
        n->args.v[0]->kind == E_FUNCREF) {
        int idx;
        Func *f = find_func(n->args.v[0]->name, &idx);
        if (f && !f->native) {
            int *visited = xmalloc(sizeof(int) * (prog->funcs.n + 1));
            Node *at = n->args.v[0];
            const char *why;
            memset(visited, 0, sizeof(int) * (prog->funcs.n + 1));
            if (f->params.n != 1) fatal_node(n, "task_start: %s tiene que recibir un Int", f->name);
            if ((why = task_impure_func(idx, visited, &at)))
                fatal_node(at, "task_start: %s corre a la vez que el programa y no puede %s", f->name, why);
            free(visited);
        }
    }
    if (!strcmp(n->name, "str_code") && n->args.n == 2 && expr_type(n->args.v[0]) == TY_STR) {
        str_code_inline(n->args.v[0], n->args.v[1]);
        return TY_INT;
    }
    for (b = 0; builtins[b].name; b++)
        if (!strcmp(builtins[b].name, n->name)) break;
    if (!builtins[b].name && !strcmp(n->name, "Fixed") && n->args.n == 1) {
        fix_value(n->args.v[0]);
        return TY_FIXED;
    }
    if (!builtins[b].name && n->args.n == 1 &&
        (!strcmp(n->name, "fx_sqrt") || !strcmp(n->name, "fx_sin") || !strcmp(n->name, "fx_cos"))) {
        static const char conv[1] = {4};
        args_to_stack(n->args.v, 1, conv);
        rt_call(!strcmp(n->name, "fx_sqrt") ? "_dl_fx_sqrt" : !strcmp(n->name, "fx_sin") ? "_dl_fx_sin" : "_dl_fx_cos",
                1, 0);
        return TY_FIXED;
    }
    if (!builtins[b].name && !strcmp(n->name, "Double") && n->args.n == 1) {
        /* Double(x): de un texto, como str_to_double; lo demás, convertido */
        if (expr_type(n->args.v[0]) == TY_STR) {
            args_to_stack(n->args.v, 1, NULL);
            rt_call("_dl_d_from_str", 1, 1);
        } else {
            dbl_value(n->args.v[0]);
        }
        return TY_DOUBLE;
    }
    if (!builtins[b].name && (!strcmp(n->name, "Int") || !strcmp(n->name, "Float")) && n->args.n == 1 &&
        expr_type(n->args.v[0]) == TY_DOUBLE) {
        args_to_stack(n->args.v, 1, NULL);
        rt_call(n->name[0] == 'I' ? "_dl_d_to_int" : "_dl_d_to_float", 1, 0);
        return n->name[0] == 'I' ? TY_INT : TY_FLOAT;
    }
    if (!builtins[b].name && (!strcmp(n->name, "Int") || !strcmp(n->name, "Float")) && n->args.n == 1) {
        int t = expr_type(n->args.v[0]), to = n->name[0] == 'I' ? TY_INT : TY_FLOAT;
        if (t == TY_STR && to == TY_INT) {
            /* Int("12"): str_to_int en base 10 */
            Node *a[2], ten;
            memset(&ten, 0, sizeof ten);
            ten.kind = E_INT;
            ten.val = 10;
            a[0] = n->args.v[0];
            a[1] = &ten;
            args_to_stack(a, 2, NULL);
            rt_call("_db_str_to_int", 2, 0);
            return TY_INT;
        }
        value(n->args.v[0]);
        coerce(t, to);
        return to;
    }
    if (!builtins[b].name) return gen_dash_builtin(n);
    if (n->args.n != (int)strlen(builtins[b].args))
        fatal_node(n, "%s pide %d argumentos y se le dan %d", n->name, (int)strlen(builtins[b].args), n->args.n);
    for (i = n->args.n - 1; i >= 0; i--) {
        Node *a = n->args.v[i];
        if (builtins[b].args[i] == 'S') {
            if (a->kind != E_STR) fatal_node(a, "(sin --gcc) aquí va un texto literal");
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
    static int sin_copiar = -1;
    if (debug) return 0;                               /* --debug: cada función en su sitio */
    if (sin_copiar < 0) sin_copiar = getenv("DASHC_SIN_COPIAR") != NULL;   /* (para buscar fallos: sin copiar en línea) */
    if (sin_copiar) return 0;
    {
        /* DASHC_NO_COPIAR=f,g: esas no (para buscar cuál da un fallo) */
        const char *no = getenv("DASHC_NO_COPIAR"), *nm = no ? c_symbol(prog->funcs.v[idx].name) + 1 : "";
        size_t ln = strlen(nm);
        while (no && *no) {
            const char *c = strchr(no, ',');
            size_t k = c ? (size_t)(c - no) : strlen(no);
            if (k == ln && !strncmp(no, nm, k)) return 0;
            no = c ? c + 1 : NULL;
        }
    }
    if (inl_stack.n + sub_stack.n >= INLINE_DEPTH || prog->funcs.v[idx].native) return 0;
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

/* Float, Double y Fixed: un Int que va a ellos se convierte */
static int num_kind(int t)
{
    return t == TY_FLOAT || t == TY_DOUBLE || t == TY_FIXED;
}

/* ¿llama e a name (una variable Func)? el nombre de una llamada no es un nodo que se pueda sustituir */
static int calls_name(Node *n, const char *name)
{
    int i;
    if (!n) return 0;
    if (n->kind == E_CALL && !strcmp(n->name, name)) return 1;
    for (i = 0; i < n->args.n; i++)
        if (calls_name(n->args.v[i], name)) return 1;
    return calls_name(n->a, name) || calls_name(n->b, name) || calls_name(n->c, name);
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
    /* un campo puede dar "campo de nil", que dice la línea de la función: así no se pone */
    if (e->kind == E_FIELD || e->kind == E_MCALL) return 0;
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
    for (i = 0; i < f->params.n; i++)
        if (calls_name(e, f->params.v[i].name)) return NULL;   /* f(v) con f un parámetro Func */
    /* un número que pasaría a Float, Double o Fixed (en el parámetro o en lo que devuelve): sin sustituir */
    if (num_kind(f->ret) && expr_type(e) != f->ret) return NULL;
    for (i = 0; i < call->args.n; i++)
        if (num_kind(f->params.v[i].type) && expr_type(call->args.v[i]) != f->params.v[i].type) return NULL;
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
    int saved_branch = ret_branch, saved_when = ret_when, saved_cur_ret = cur_ret, saved_ret_sp = ret_sp;
    int saved_file_g = cur_file_g, saved_file = cur_file, saved_line = cur_line;
    const char *saved_src = src_name;
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
        b->entry = 0;
        b->owned = 0;
        if (!param_set[idx][i] && b->type != TY_DOUBLE && (b->type != TY_FIXED || expr_type(a) != TY_FLOAT) &&
            fold(a, &k)) {
            if (b->type == TY_FIXED && expr_type(a) != TY_FIXED) k = (long)(int32_t)((uint32_t)k << 16);
            b->val = b->type == TY_FLOAT ? float_bits((double)(int32_t)k) : k;
            continue;
        }
        if (!param_set[idx][i] && a->kind == E_VAR && (src = find_local(a->name)) != NULL &&
            (b->type != TY_FLOAT || src->type == TY_FLOAT) && (b->type != TY_DOUBLE || src->type == TY_DOUBLE) &&
            (b->type != TY_FIXED || src->type == TY_FIXED)) {
            b->slot = src->slot;
            b->val = src->val;
            b->ranged = src->ranged;
            b->lo = src->lo;
            b->hi = src->hi;
            b->entry = src->entry;
            b->entry_loops = src->entry_loops;
            if (src->slot >= 0) use_slot(src->slot);
            continue;
        }
        {
            Var t, sv;
            int simple_arg = a->kind == E_VAR && simple(a, &sv) && sv.kind != V_CONST && find_local(a->name) &&
                             (b->type != TY_FLOAT || expr_type(a) == TY_FLOAT) &&
                             (b->type != TY_DOUBLE || expr_type(a) == TY_DOUBLE) &&
                             (b->type != TY_FIXED || expr_type(a) == TY_FIXED);
            if (!simple_arg) {
                if (b->type == TY_FLOAT) float_value(a);
                else if (b->type == TY_FIXED) fix_value(a);
                else if (b->type == TY_DOUBLE && expr_type(a) != TY_DOUBLE) dbl_value(a);
                else {
                    value(a);
                    lend(a);
                }
            }
            b->slot = new_slot(0);
            use_slot(b->slot);
            t = slot_var(b->slot, b->type);
            if (var_range(a, &b->lo, &b->hi)) {
                b->entry = 1;                          /* la copia empieza con el rango del argumento */
                b->entry_loops = loops.n;
            }
            if (simple_arg && t.kind == V_REG) load_var(t.reg, &sv);   /* move.l x,dN */
            else {
                if (simple_arg) load_var(0, &sv);
                store_d0(&t);
            }
            if ((IS_STRLIKE(b->type) || IS_OBJ(b->type)) && param_set[idx][i]) {
                /* un parámetro de texto que la función cambia: una copia suya (un objeto: una referencia) */
                push_ea(&t);
                rt_call(IS_STRLIKE(b->type) ? "_dl_str_dup" : "_dl_hold_r", 1, 0);
                store_d0(&t);
                b->owned = IS_STRLIKE(b->type) ? 1 : 2;
            }
        }
    }
    cur_frame = frame;
    for (i = 0; i < n->args.n; i++) VEC_PUSH(locals, binds[i]);
    free(binds);
    ret_label = new_label();
    ret_branch = branch_to;
    ret_when = when_true;
    cur_ret = f->ret;
    ret_sp = sp_depth;
    loop_base = loops.n;
    VEC_PUSH(inl_stack, idx);
    gen_block(&f->body);
    inl_stack.n--;
    free_owned(0, 1);                                  /* cayendo por el final */
    def_label_fwd(ret_label);                          /* si solo se llega cayendo, d0 sigue valiendo */
    ret_label = saved_ret;
    ret_branch = saved_branch;
    ret_when = saved_when;
    cur_ret = saved_cur_ret;
    /* (lo copiado es de su fichero: lo que sigue en la instrucción que llama, otra vez del suyo, con sus globales) */
    cur_file_g = saved_file_g;
    cur_file = saved_file;
    cur_line = saved_line;
    src_name = saved_src;
    ret_sp = saved_ret_sp;
    loop_base = saved_base;
    cur_frame = saved_frame;
    depth--;                                           /* sin leave_scope: sus textos ya se liberaron */
    while (locals.n && locals.v[locals.n - 1].depth > depth) locals.n--;
    return f->ret;
}

static int gen_call(Node *n)
{
    int i, idx;
    Func *f = find_func(n->name, &idx);
    if (!f && (idx = find_struct(n->name)) >= 0) return gen_new(n, idx, 0);
    if (!f && lookup(n->name).kind != V_NONE) {
        /* g(4) con g una variable Func: la función a la que apunta, como una de C (Int) */
        Var v;
        for (i = n->args.n - 1; i >= 0; i--) push_value(n->args.v[i]);
        v = lookup(n->name);
        load_var(0, &v);
        call_d0();
        pop_args(n->args.n);
        forget_d0();
        return TY_INT;
    }
    if (!f) return gen_builtin(n);
    if (n->args.n != f->params.n)
        fatal_node(n, "%s pide %d argumentos y se le dan %d", n->name, f->params.n, n->args.n);
    if (f->native == 2) {
        /* @extern: la función de C de lo de @link, como una del runtime (los argumentos en la pila, de
           derecha a izquierda; lo devuelto en d0); un texto que devuelve se copia a un temporal de Dash */
        char *sym = c_symbol(f->name);
        for (i = n->args.n - 1; i >= 0; i--) push_value(n->args.v[i]);
        rt_call(sym, n->args.n, 0);
        if (f->ret == TY_STR) {
            push_d0();
            rt_call("_dl_str_tmpcopy_c", 1, 1);
        } else if (f->ret == TY_BOOL) {
            c_bool();
        }
        forget_d0();
        return f->ret;
    }
    if (f->native) {
        /* el envoltorio dn_nombre de la librería (runtime/gen_lib.py) */
        char *sym = xmalloc(strlen(f->name) + 5);
        strcpy(sym, "_dn_");
        strcat(sym, f->name);
        if (!runtime_has(sym))
            fatal_at(f->line, f->col, "@native %s: Dash 2.0 no admite C en los programas (solo el de lib/amiga)", f->name);
        for (i = n->args.n - 1; i >= 0; i--) push_value(n->args.v[i]);
        rt_call(sym, n->args.n, 0);
        return f->ret == TY_VOID ? TY_VOID : f->ret;
    }
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
    for (i = n->args.n - 1; i >= 0; i--) {
        Node *a = n->args.v[i], *in = a->kind == E_NN ? a->a : a;   /* (self de un método: comprobado) */
        if (f->params.v[i].type == TY_FLOAT && expr_type(a) != TY_FLOAT) {
            float_value(a);                            /* un Int a un parámetro Float */
            push_d0();
        } else if (f->params.v[i].type == TY_DOUBLE && expr_type(a) != TY_DOUBLE) {
            dbl_value(a);                              /* un Int o un Float a un parámetro Double */
            push_d0();
        } else if (f->params.v[i].type == TY_FIXED && expr_type(a) != TY_FIXED) {
            fix_value(a);                              /* un Int o un literal a un parámetro Fixed */
            push_d0();
        } else if (in->kind == E_FIELD || in->kind == E_INDEX || (in->kind == E_VAR && !find_local(in->name))) {
            value(a);
            lend(in);
            push_d0();
        } else {
            push_value(a);
        }
    }
    jsr_label(func_label[idx]);
    pop_args(n->args.n);
    if (!needed[idx]) needed[idx] = 1;               /* 2: ya generada */
    if (IS_STRLIKE(f->ret) || IS_OBJ(f->ret)) made_tmp = 1;   /* lo devuelto es un temporal de aquí */
    return f->ret;
}

static int gen_expr(Node *n)
{
    long k;
    Var v;

    if (repl_var(n, &v)) {
        load_var(0, &v);
        return v.type;
    }
    if (n->kind != E_CMP && n->kind != E_AND && n->kind != E_OR && n->kind != E_NOT && fold(n, &k)) {
        load_imm(0, k);
        return fold_type(n);
    }
    switch (n->kind) {
    case E_STR:
        load_str_lit(n->str, n->len);
        return TY_STR;
    case E_NIL:
        load_imm(0, 0);
        return TY_NIL;
    case E_FLOAT:
        load_imm(0, n->val);
        return TY_FLOAT;
    case E_INTERP:
        gen_interp(n);
        return TY_STR;
    case E_INDEX:
        if (expr_type(n->a) == TY_STR) return gen_str_index(n);
        if (IS_ARR(expr_type(n->a))) return gen_arr_index(n);
        if (IS_DICT(expr_type(n->a))) return gen_dict_get(n);
        fatal_node(n, "aquí no se puede usar [ ]");
        return TY_VOID;
    case E_SLICE:
        if (expr_type(n->a) == TY_STR) return gen_str_slice(n);
        if (IS_ARR(expr_type(n->a))) return gen_arr_slice(n);
        fatal_node(n, "aquí no se puede usar [ : ]");
        return TY_VOID;
    case E_FIELD: {
        int t, wm = window_member(n);
        if (wm >= 0) {
            /* Win.width...: de la ventana abierta (puede haber cambiado) o de su definición, como ./dash */
            int wi = find_window(n->a->name);
            load_imm(0, wm);
            push_d0();
            push_label(win_desc_label[wi]);            /* el descriptor */
            push_data_long(win_off[wi]);               /* la ventana */
            rt_call("_dl_win_member", 3, 0);
            return wm == 4 ? TY_STR : TY_INT;
        }
        t = gen_struct_field(n);
        if (t >= 0) return t;
        return gen_field(n);
    }
    case E_NN: {
        int t = gen_expr(n->a);
        int saved = cur_line;
        cur_line = n->line;
        nil_check();
        cur_line = saved;
        return t;
    }
    case E_LIST:
        gen_list(n, 0);
        return expr_type(n);
    case E_DICT:
        return gen_dict(n);
    case E_MCALL:
        if (IS_ARR(expr_type(n->a))) return gen_list_method(n);
        if (IS_STRUCT(expr_type(n->a))) return gen_method(n, expr_type(n->a));
        if (IS_DICT(expr_type(n->a))) return gen_dict_method(n);
        if (expr_type(n->a) == TY_INT && !strcmp(n->name, "abs") && !n->args.n) {
            /* x.abs(): el abs() de C, como ./dash */
            need_value(n->a, gen_expr(n->a));
            abs_d0();
            return TY_INT;
        }
        fatal_node(n, "(sin --gcc) .%s() aún no está", n->name);
        return TY_VOID;
    case E_VAR:
        v = lookup(n->name);
        if (v.kind == V_NONE) {
            fatal_node(n, "la variable %s no existe", n->name);
        }
        load_var(0, &v);
        return v.type;
    case E_FUNCREF: {
            int idx;
            Func *fn = find_func(n->name, &idx);
            if (fn && !fn->native) {
                /* una función como valor (mui_canvas_on_draw(lienzo, pinta)...): su dirección; la llaman
                   como a una de C, que es como van las de dashc */
                load_label(func_label[idx]);
                if (!needed[idx]) needed[idx] = 1;
                return TY_INT;
            }
            if (fn && fn->native == 2) {
                /* una de @extern: la dirección de su símbolo de C (un puntero a función para otro C, o la función
                   de un task_start) */
                char *sym = c_symbol(fn->name);
                load_sym(sym);
                return TY_INT;
            }
            fatal_node(n, "%s: una función de @native no puede ir como valor", n->name);
            return TY_VOID;
        }
    case E_CALL:
        return gen_call(n);
    case E_NEG:
        if (expr_type(n->a) == TY_DOUBLE) {
            args_to_stack(&n->a, 1, NULL);
            rt_call("_dl_d_neg", 1, 1);
            return TY_DOUBLE;
        }
        if (expr_type(n->a) == TY_FLOAT) {
            value(n->a);
            float_neg();
            return TY_FLOAT;
        }
        value(n->a);
        neg_d0();
        return expr_type(n->a) == TY_FIXED ? TY_FIXED : TY_INT;
    case E_BNOT:
        value(n->a);
        not_d0();
        return TY_INT;
    case E_CMP:
        set_cc(gen_compare(n));
        return TY_BOOL;
    case E_NOT:
    case E_AND:
    case E_OR: {
        int f = new_label(), done = new_label();
        gen_branch(n, f, 0);
        set_ne();                                      /* 1 */
        branch(CC_T, done);
        def_label(f);
        zero_d0();
        def_label(done);
        return TY_BOOL;
    }
    case E_BIN:
        if (n->op == P_PLUS && (expr_type(n->a) == TY_STR || expr_type(n->b) == TY_STR)) {
            gen_concat(n);
            return TY_STR;
        }
        if (n->op == P_PLUS && IS_ARR(expr_type(n))) {
            /* a + b de listas: una nueva con las dos (DashArray_concat) */
            Node *a[2];
            a[0] = n->a;
            a[1] = n->b;
            args_to_stack(a, 2, NULL);
            rt_call("_dl_arr_concat", 2, 1);
            return expr_type(n);
        }
        if (expr_type(n) == TY_DOUBLE) {
            /* a op b con algún Double: dl_d_op(a, b, op), una caja nueva */
            Node *a[2];
            static const char conv[2] = {3, 3};
            load_imm(0, n->op == P_PLUS ? 0 : n->op == P_MINUS ? 1 : n->op == P_STAR ? 2 : 3);
            push_d0();
            a[0] = n->a;
            a[1] = n->b;
            args_to_stack(a, 2, conv);
            rt_call("_dl_d_op", 3, 1);
            return TY_DOUBLE;
        }
        if (expr_type(n) == TY_FLOAT) {
            /* a op b con algún Float: __addsf3, __subsf3, __mulsf3, __divsf3 */
            Node *a[2];
            static const char conv[2] = {2, 2};
            a[0] = n->a;
            a[1] = n->b;
            args_to_stack(a, 2, conv);
            rt_call(n->op == P_PLUS ? "___addsf3" : n->op == P_MINUS ? "___subsf3" :
                    n->op == P_STAR ? "___mulsf3" : "___divsf3", 2, 0);
            return TY_FLOAT;
        }
        if (expr_type(n) == TY_FIXED) {
            /* Fixed, como ./dash: Fixed * Fixed y Fixed / Fixed, el runtime (64 bits); * y / por un Int, la
               cuenta de enteros; + - y %, los dos como Fixed */
            int fa = expr_type(n->a) == TY_FIXED, fb = expr_type(n->b) == TY_FIXED;
            if ((n->op == P_STAR && fa && fb) || (n->op == P_SLASH && !(fa && !fb))) {
                Node *a[2];
                static const char conv[2] = {4, 4};
                a[0] = n->a;
                a[1] = n->b;
                args_to_stack(a, 2, conv);
                rt_call(n->op == P_STAR ? "_dl_fx_mul" : "_dl_fx_div", 2, 0);
                return TY_FIXED;
            }
            if (n->op == P_STAR || n->op == P_SLASH) {
                gen_binary(n);                         /* (Fixed * Int, Int * Fixed, Fixed / Int) */
                return TY_FIXED;
            }
            if (fa && fb) {
                gen_binary(n);
                return TY_FIXED;
            }
            {
                /* + - % con un Int: ese lado, Fixed(lado) */
                Node c = *n, wrap;
                memset(&wrap, 0, sizeof wrap);
                wrap.kind = E_CALL;
                wrap.name = "Fixed";
                wrap.line = n->line;
                wrap.col = n->col;
                wrap.file = n->file;
                VEC_PUSH(wrap.args, fa ? n->b : n->a);
                if (fa) c.b = &wrap;
                else c.a = &wrap;
                gen_binary(&c);
                free(wrap.args.v);
                return TY_FIXED;
            }
        }
        if (expr_type(n->a) == TY_FLOAT || expr_type(n->b) == TY_FLOAT ||
            expr_type(n->a) == TY_DOUBLE || expr_type(n->b) == TY_DOUBLE)
            fatal_node(n, "este operador no es para Float ni Double");
        gen_binary(n);
        return TY_INT;
    }
    fatal_node(n, "expresión no admitida");
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
        if (!flags_for(&v, CC_NE)) tst_ea(&v);
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

#define MAX_INV 6

/* ¿e no cambia en el cuerpo de un for? Literales, constantes y variables locales que el cuerpo no asigna (ni la
   del for), y +, -, *, / y el signo de ellas. Las globales no: una función que llama el cuerpo podría cambiarlas */
static int loop_inv(Node *e, NodeList *body, const char *ivar)
{
    Local *lc;
    switch (e->kind) {
    case E_FLOAT: case E_INT: return 1;
    case E_NEG: return loop_inv(e->a, body, ivar);
    case E_VAR:
        lc = find_local(e->name);
        return lc && strcmp(e->name, ivar) && !list_assigns(body, e->name);
    case E_BIN:
        return (e->op == P_PLUS || e->op == P_MINUS || e->op == P_STAR || e->op == P_SLASH) &&
               loop_inv(e->a, body, ivar) && loop_inv(e->b, body, ivar);
    default: return 0;
    }
}

/* Las operaciones de Float del cuerpo que no cambian en él (las más grandes): se calculan una vez antes del bucle
   (gcc lo hace igual por el camino por C). Sin efectos ni errores (dividir por cero da infinito), así que da igual
   que el cuerpo no llegue a ejecutarlas */
static void find_float_inv(Node *n, NodeList *body, const char *ivar, Node **inv, int *ninv)
{
    int i;
    if (!n || *ninv >= MAX_INV) return;
    if (n->kind == E_BIN && (n->op == P_PLUS || n->op == P_MINUS || n->op == P_STAR || n->op == P_SLASH) &&
        expr_type(n) == TY_FLOAT && loop_inv(n, body, ivar) && !(n->a->kind == E_FLOAT && n->b->kind == E_FLOAT)) {
        inv[(*ninv)++] = n;
        return;
    }
    find_float_inv(n->a, body, ivar, inv, ninv);
    find_float_inv(n->b, body, ivar, inv, ninv);
    find_float_inv(n->c, body, ivar, inv, ninv);
    for (i = 0; i < n->args.n; i++) find_float_inv(n->args.v[i], body, ivar, inv, ninv);
    for (i = 0; i < n->body.n; i++) find_float_inv(n->body.v[i], body, ivar, inv, ninv);
    for (i = 0; i < n->els.n; i++) find_float_inv(n->els.v[i], body, ivar, inv, ninv);
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
    Node *inv[MAX_INV];
    int ninv = 0, inv_slot[MAX_INV];
    Var vi, vend, vstep, vc, sr_v[MAX_SR];
    Loop lp;
    MarkScope ms;

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
    if (step_known && step == 0) fatal_node(n, "el paso del for no puede ser 0");

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

    ms = mark_begin();
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
    /* los Float que no cambian en el cuerpo, en huecos (antes de reservar los del contador) */
    for (i = 0; i < n->body.n; i++) find_float_inv(n->body.v[i], &n->body, n->name, inv, &ninv);
    for (j = 0; j < ninv; j++) {
        Var vv;
        float_value(inv[j]);
        vv = declare_slot("", TY_FLOAT, &inv_slot[j]);
        store_d0(&vv);
        add_repl(inv[j], inv_slot[j], 0);
        repls.v[repls.n - 1].type = TY_FLOAT;
    }

    if (counted) {
        if (count >= 0) {
            vc = declare_slot("", TY_INT, &cnt_slot);
            set_imm(&vc, count - 1);
        } else {
            /* vueltas - 1 = fin - inicio (o al revés); ninguna si es negativo */
            value(n->b);
            if (from_known) {
                if (from) sub_imm(from);
                else tst_d0();
            } else {
                sub_ea(&vi);
            }
            branch(down ? CC_GT : CC_LT, done);
            if (down) neg_d0();
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
    for (j = 0; j < ninv; j++) use_slot(inv_slot[j]);

    /* sin contador, la comparación va al final: una vuelta es cuerpo, incremento y un salto */
    if (!counted) {
        test = new_label();
        branch(CC_T, test);
    }
    def_label(top);
    mark_release(&ms);
    lp.brk = done;
    lp.cont = cont;
    enter_scope();
    lp.depth = depth;
    lp.sp = sp_depth;
    VEC_PUSH(loops, lp);
    gen_block(&n->body);
    loops.n--;
    leave_scope();

    def_label(cont);
    if (use_i) {
        if (!step_known) {
            if (vi.kind == V_REG) add_to_reg(vi.reg, &vstep);
            else {
                load_var(0, &vstep);
                op_reg_to(0, 0, &vi);                  /* i += d0 */
            }
        } else {
            add_imm_ea(step, &vi);
        }
    }
    for (j = 0; j < nsr; j++) add_imm_ea((long)(int32_t)((uint32_t)step * (uint32_t)sr_k[j]), &sr_v[j]);
    if (counted) {
        loop_count(&vc, top, count < 0 || count > 65536);
    } else {
        int pass_n, neg = new_label();
        def_label(test);
        if (!step_known) {
            /* el paso se sabe al ejecutar: su signo dice el sentido, como en ./dash */
            tst_ea(&vstep);
            branch(CC_MI, neg);
        }
        for (pass_n = 0; pass_n < (step_known ? 1 : 2); pass_n++) {
            if (pass_n) def_label(neg);
            if (vend.kind == V_CONST) cmp_imm_ea(vend.val, &vi);
            else if (vi.kind == V_REG) cmp_reg_ea(vi.reg, &vend);
            else {
                load_var(0, &vi);
                cmp_reg_ea(0, &vend);
            }
            branch(pass_n || down ? CC_GE : CC_LE, top);
            if (!step_known && !pass_n) branch(CC_T, done);
        }
    }
    def_label(done);
    repls.n = repl_base;
    leave_loop();
    leave_scope();
    mark_end(&ms);
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
    Var s;
    if (t && simple(t, &s) && s.kind != V_CONST) {
        if (v->kind == V_REG) {
            op_to_reg(op, v->reg, &s, -1);
            return;
        }
        if (s.kind == V_REG) { op_reg_to(op, s.reg, v); return; }
        load_var(0, &s);
    } else if (t) {
        int x;
        value(t);
        if ((x = take_move_to_d0()) >= 0) {             /* el valor está en dX: sin pasar por d0 */
            if (v->kind == V_REG) op_to_reg(op, v->reg, NULL, x);
            else op_reg_to(op, x, v);
            return;
        }
    }
    if (v->kind == V_REG) op_to_reg(op, v->reg, NULL, 0);
    else op_reg_to(op, 0, v);
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
        v = lookup(n->name);
        reg_div_pow2(&v, sh);
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
        op_imm_into(op, k, &v);
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
        if (global_visible(i) && !strcmp(prog->globals.v[i].name, name)) return 1;
    for (i = 0; i < prog->consts.n; i++)
        if (!strcmp(prog->consts.v[i].name, name)) return 1;
    return 0;
}

/* ¿se sabe que la condición c se cumple al llegar al bucle? (v op k, con el rango de v) */
static int true_at_entry(Node *c)
{
    Node *vn;
    Local *lc;
    long k, lo, hi;
    int op;
    if (c->kind != E_CMP) return 0;
    op = c->op;
    if (fold(c->b, &k) && c->a->kind == E_VAR) vn = c->a;
    else if (fold(c->a, &k) && c->b->kind == E_VAR) {
        vn = c->b;
        op = op == P_LT ? P_GT : op == P_GT ? P_LT : op == P_LE ? P_GE : op == P_GE ? P_LE : op;
    } else return 0;
    if (!var_range(vn, &lo, &hi)) {
        if (!(lc = find_local(vn->name)) || lc->slot < 0 || !lc->entry || lc->entry_loops != loops.n) return 0;
        lo = lc->lo;
        hi = lc->hi;
    }
    switch (op) {
    case P_NE: return lo > k || hi < k;
    case P_EQ: return lo == k && hi == k;
    case P_LT: return hi < k;
    case P_LE: return hi <= k;
    case P_GT: return lo > k;
    case P_GE: return lo >= k;
    }
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
    MarkScope ms;
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
    ms = mark_begin();
    /* vueltas - 1: fin - v (- 1 con <) o v - fin (- 1 con >); ninguna si no llega */
    value(end);
    simple(vn, &vv);
    sub_ea(&vv);                                       /* fin - v */
    switch (op) {
    case P_LT: branch(CC_LE, done); sub_imm(1); break;
    case P_LE: branch(CC_LT, done); break;
    case P_GT: branch(CC_GE, done); neg_d0(); sub_imm(1); break;
    default: branch(CC_GT, done); neg_d0(); break;
    }
    vc = slot_var(slot, TY_INT);
    store_d0(&vc);
    use_slot(slot);
    enter_loop();
    use_slot(slot);
    /* si en la segunda pasada el hueco se queda sin registro, el bucle va con su condición (S_WHILE), que lee
       el fin en cada vuelta: tiene que seguir vivo en todo el bucle (si no, su registro lo toma otra variable) */
    if (pass == 1 && end->kind == E_VAR) {
        Local *le = find_local(end->name);
        if (le && le->slot >= 0) use_slot(le->slot);
    }
    def_label(top);
    mark_release(&ms);
    lp.brk = done;
    lp.cont = -1;                                      /* no hay continue */
    enter_scope();
    lp.depth = depth;
    lp.sp = sp_depth;
    VEC_PUSH(loops, lp);
    gen_block(&n->body);
    leave_scope();
    loops.n--;
    use_slot(slot);
    if (vc.kind == V_REG) loop_count(&vc, top, 1);
    def_label(done);
    leave_loop();
    mark_end(&ms);
    return 1;
}

/* r = a + b o r = a - b de enteros, con r en un registro y a y b simples (ninguno lee r): se calcula en el registro
   de r, sin pasar por d0 (como gcc). 0: no es el caso */
static int assign_in_reg(Node *n)
{
    Node *e = n->a;
    Var v, va, vb;
    long k;
    if (e->kind != E_BIN || (e->op != P_PLUS && e->op != P_MINUS) || expr_type(e) != TY_INT) return 0;
    v = lookup(n->name);
    if (v.kind != V_NONE && (v.kind != V_REG || v.type != TY_INT)) return 0;
    if (refs(e->b, n->name) || refs(e->a, n->name)) return 0;
    if (!simple(e->a, &va) || !simple(e->b, &vb)) return 0;
    if (va.kind != V_CONST && va.type != TY_INT && va.type != TY_CHAR) return 0;
    if (vb.kind != V_CONST && vb.type != TY_INT && vb.type != TY_CHAR) return 0;
    if (v.kind == V_NONE) {                            /* la primera asignación declara */
        v = declare(n->name, TY_INT);
        if (v.kind != V_REG) {                         /* sin registro: como siempre */
            value(e);
            store_d0(&v);
            return 1;
        }
    }
    load_var(v.reg, &va);                              /* move.l a,dN */
    if (vb.kind == V_CONST) {
        k = e->op == P_PLUS ? vb.val : -vb.val;
        add_imm_ea(k, &v);
        if (!k) flags_set(v.reg, 1);
    } else {
        op_to_reg(e->op == P_PLUS ? 0 : 1, v.reg, &vb, -1);   /* dN += b o -= b */
    }
    return 1;
}

/* La pista de una parte de una unión: el largo de un literal; -2 un número, carácter o Bool pasado a texto (un
   texto de C: strlen, sin mirar cabecera); -1 lo demás */
static int join_hint(Node *p)
{
    int ty;
    if (p->kind == E_STR && p->len < 32768) return p->len;
    ty = expr_type(p);
    if (ty == TY_INT || ty == TY_CHAR || ty == TY_BOOL) return -2;
    return -1;
}

/* s = a + b + ... o s = "...#{x}..." (hasta 6 partes): dl_str_set_join_r escribe en el texto de s si cabe, sin
   el temporal de la unión ni su copia (como _dash_str_set_join del camino por C). 0: no es el caso */
static int str_set_join(Node *n, Node *e, int fresh)
{
    Node *parts[6], *x;
    char str[6];
    int np = 0, i;
    Var v;
    if (e->kind == E_INTERP) {
        if (e->args.n < 1 || e->args.n > 6) return 0;
        for (i = 0; i < e->args.n; i++) parts[i] = e->args.v[i];
        np = e->args.n;
    } else if (e->kind == E_BIN && e->op == P_PLUS && expr_type(e) == TY_STR) {
        for (x = e; x->kind == E_BIN && x->op == P_PLUS && expr_type(x) == TY_STR; x = x->a) {
            if (np >= 5) return 0;
            np++;
        }
        parts[0] = x;
        for (x = e, i = np; i > 0; x = x->a, i--) parts[i] = x->b;
        np++;
    } else return 0;
    if (np == 2 && parts[0]->kind == E_STR && parts[0]->len < 32768 && expr_type(parts[1]) == TY_INT) {
        /* literal + número: dl_str_cat_li_r(var, literal, largo, n) */
        value(parts[1]);
        push_d0();
        push_word(parts[0]->len);                      /* el largo */
        load_str_lit(parts[0]->str, parts[0]->len);
        push_d0();
        if (fresh) {
            push_word(0);                                  /* sin texto antes */
        } else {
            v = lookup(n->name);
            push_ea(&v);
        }
        rt_call("_dl_str_cat_li_r", 4, 0);
        goto guardar;
    }
    for (i = 0; i < np; i++) str[i] = 1;
    args_to_stack(parts, np, str);                     /* las partes, en la pila */
    if (np == 2) {
        /* dos partes: dl_str_cat2_r(var, pista a, pista b, a, b), con las partes ya en la pila */
        for (i = 1; i >= 0; i--) {
            push_word(join_hint(parts[i]));            /* su pista */
        }
        if (fresh) {
            push_word(0);
        } else {
            v = lookup(n->name);
            push_ea(&v);
        }
        rt_call("_dl_str_cat2_r", 5, 0);
        goto guardar;
    }
    reserve_args(np);                                  /* las pistas */
    for (i = 0; i < np; i++) store_arg_imm(i, join_hint(parts[i]));
    push_sp();                                         /* las pistas */
    push_sp_addr(SLOT * (np + 1));                     /* las partes */
    push_word(np);
    if (fresh) {
        push_word(0);                                  /* sin texto antes */
    } else {
        v = lookup(n->name);
        push_ea(&v);
    }
    rt_call("_dl_str_set_join_r", 4, 0);
    pop_args(2 * np);
guardar:
    if (fresh) {
        v = declare(n->name, TY_STR);
        locals.v[locals.n - 1].owned = 1;
    }
    store_d0(&v);
    return 1;
}

/* s = valor para una variable de texto: la variable es dueña de su texto; s = s + x añade
   en su sitio (_dash_str_append); una variable nueva empieza sin texto */
static void gen_str_assign(Node *n, int ty)
{
    Node *e = n->a;
    Local *lc = find_local(n->name);
    int fresh = n->kind == S_VAR || (!lc && !lookup_global(n->name));
    Var v;
    if (lc && lc->slot < 0) fatal_node(n, "%s es una constante", n->name);
    if (ty == TY_STR && !fresh && e->kind == E_BIN && e->op == P_PLUS && e->a->kind == E_VAR && !strcmp(e->a->name, n->name) &&
        !refs(e->b, n->name)) {
        str_value(e->b);
        push_d0();
        v = lookup(n->name);
        push_ea(&v);
        rt_call("_dl_str_append_r", 2, 0);
        store_d0(&v);
        return;
    }
    if (fresh && e->kind == E_NIL) {
        v = declare(n->name, ty);
        locals.v[locals.n - 1].owned = 1;
        set_imm(&v, 0);
        return;
    }
    if (ty == TY_STR && str_set_join(n, e, fresh)) return;
    if (ty == TY_STR && e->kind != E_NIL && (lc || fresh) && is_lent(0, n->name)) {
        /* toma prestado el texto (un literal, o de una lista o diccionario de un parámetro): ni copia ni free */
        value(e);
        v = fresh ? declare(n->name, ty) : lookup(n->name);
        store_d0(&v);
        return;
    }
    if (e->kind == E_NIL) load_imm(0, 0);
    else if (ty == TY_DOUBLE) dbl_value(e);            /* (una caja; un número, convertido) */
    else str_value(e);
    push_d0();
    if (fresh) {
        push_word(0);                                  /* sin texto antes */
    } else {
        v = lookup(n->name);
        push_ea(&v);
    }
    rt_call(is_tmp_expr(e) ? "_dl_str_assign" : "_dl_str_assign_copy", 2, 0);
    if (fresh) {
        v = declare(n->name, ty);
        locals.v[locals.n - 1].owned = 1;
    }
    store_d0(&v);
}

/* Al empezar Main, las globales de texto toman su valor (una copia suya, como en ./dash) */
static void gen_global_inits(void)
{
    int i;
    for (i = 0; i < prog->globals.n; i++) {
        Global *g = &prog->globals.v[i];
        Var v;
        long k;
        v.kind = V_GLOBAL;
        v.off = global_off(i);
        v.type = global_type[i];
        if (g->init->kind == E_NIL) continue;
        if (IS_STRLIKE(global_type[i])) {
            if (global_type[i] == TY_DOUBLE) dbl_value(g->init);
            else str_value(g->init);
            push_d0();
            push_word(0);
            rt_call(is_tmp_expr(g->init) ? "_dl_str_assign" : "_dl_str_assign_copy", 2, 0);
        } else if (IS_OBJ(global_type[i])) {
            if (g->init->kind == E_LIST && g->init->args.n) gen_list(g->init, 1);
            else if (is_new_obj(g->init)) gen_new(g->init, find_struct(g->init->name), 1);
            else value(g->init);
            if (!is_new_obj(g->init)) {
                push_d0();
                rt_call("_dl_retain_r", 1, 0);         /* la global se queda con una referencia */
            }
        } else if (!fold(g->init, &k)) {
            value(g->init);
        } else {
            continue;                                  /* (ya en los datos) */
        }
        store_d0(&v);
    }
}

/* v = valor para una lista o un struct: cuenta de referencias (_dash_obj_set). Una lista
   literal nace con su referencia (DashArray_from_new) y la variable se la queda. */
static void gen_obj_assign(Node *n, int tt)
{
    Node *e = n->a;
    Local *lc = find_local(n->name);
    int fresh = n->kind == S_VAR || (!lc && !lookup_global(n->name)), lit = is_new_obj(e);
    Var v;
    if (lc && lc->slot < 0) fatal_node(n, "%s es una constante", n->name);
    if ((e->kind == E_FIELD || e->kind == E_INDEX) && (lc || fresh) && is_lent(1, n->name)) {
        /* toma prestado el objeto (de un campo o elemento de lo que sostiene otro): sin referencia propia */
        value(e);
        v = fresh ? declare(n->name, tt) : lookup(n->name);
        store_d0(&v);
        return;
    }
    list_hint(e, tt);
    if (e->kind == E_LIST) gen_list(e, 1);
    else if (lit) gen_new(e, find_struct(e->name), 1);
    else value(e);
    if (fresh && (lit || e->kind == E_NIL)) {
        v = declare(n->name, tt);
        locals.v[locals.n - 1].owned = 2;
        store_d0(&v);
        return;
    }
    push_d0();
    if (fresh) {
        push_word(0);
    } else {
        v = lookup(n->name);
        push_ea(&v);
    }
    rt_call(lit ? "_dl_obj_assign_new" : "_dl_obj_assign", 2, 0);
    if (fresh) {
        v = declare(n->name, tt);
        locals.v[locals.n - 1].owned = 2;
    }
    store_d0(&v);
}

/* for x in lista: la lista sujeta (_dash_hold) mientras dura el bucle; x es el elemento
   (prestado: no es suyo) */
/* for c in texto: cada carácter (Char) hasta el 0, como ./dash; el texto de una variable se lee en cada vuelta
   y, si el cuerpo la cambia, cuenta el largo del principio. Otro texto, una copia suya. */
static void gen_foreach_str(Node *n)
{
    int top = new_label(), cont = new_label(), done = new_label(), src_slot = -1, idx_slot, len_slot = -1;
    int assigned = n->a->kind == E_VAR && list_assigns(&n->body, n->a->name);
    MarkScope ms;
    Loop lp;
    Var vs, vi, vl, vx;
    ms = mark_begin();
    enter_scope();
    if (n->a->kind == E_VAR) {
        vs = lookup(n->a->name);
    } else {
        value(n->a);
        push_d0();
        rt_call("_dl_str_dup", 1, 0);
        vs = declare_slot("", TY_STR, &src_slot);
        locals.v[locals.n - 1].owned = 1;              /* al acabar, _dl_str_free */
        store_d0(&vs);
    }
    vi = declare_slot("", TY_INT, &idx_slot);
    set_imm(&vi, 0);
    if (assigned) {
        load_var(0, &vs);
        push_d0();
        rt_call("_dl_str_len", 1, 0);
        vl = declare_slot("", TY_INT, &len_slot);
        store_d0(&vl);
    }
    enter_loop();
    if (src_slot >= 0) use_slot(src_slot);
    use_slot(idx_slot);
    if (len_slot >= 0) use_slot(len_slot);
    def_label(top);
    mark_release(&ms);
    lp.brk = done;
    lp.cont = cont;
    enter_scope();
    lp.depth = depth;
    lp.sp = sp_depth;
    VEC_PUSH(loops, lp);
    use_slot(idx_slot);
    vi = slot_var(idx_slot, TY_INT);
    if (assigned) {
        use_slot(len_slot);
        vl = slot_var(len_slot, TY_INT);
        load_var(1, &vl);
        load_var(0, &vi);
        cmp_d0_d1();
        branch(CC_GE, done);
    }
    if (src_slot >= 0) {
        use_slot(src_slot);
        vs = slot_var(src_slot, TY_STR);
    }
    load_var(0, &vs);
    tst_d0();
    branch(CC_EQ, done);                               /* nil: ninguno */
    move_d0_a0();
    load_var(0, &vi);
    load_char();
    if (!assigned) branch(CC_EQ, done);                /* el 0 del final */
    vx = declare(n->name, TY_CHAR);
    store_d0(&vx);
    gen_block(&n->body);
    loops.n--;
    leave_scope();
    def_label(cont);
    use_slot(idx_slot);
    add_imm_ea(1, &vi);
    branch(CC_T, top);
    def_label(done);
    leave_loop();
    leave_scope();                                     /* la copia del texto */
    mark_end(&ms);
}

/* ---- for x in lista sin una referencia por vuelta (como ./dash, _loop_keeps_elements) ----
   El bucle sostiene la lista: un elemento solo se va si algo lo saca de una lista (pop, remove, clear, l[i] = y).
   Una función "conserva" si nunca lo hace, ni ella ni lo que llama (en su cuerpo una lista y un diccionario no se
   distinguen: cualquier x[i] = y, pop, remove o clear cuenta). Se calcula una vez (punto fijo). */
static char *keeps_fn;   /* por función: 1 conserva */

/* ¿pasa e una función de Dash como argumento (una retrollamada que el builtin puede llamar)? */
static int passes_func(Node *e)
{
    int i;
    for (i = 0; i < e->args.n; i++)
        if (e->args.v[i]->kind == E_FUNCREF) return 1;
    return 0;
}

static int call_keeps(Node *e)
{
    int idx, b;
    if (find_func(e->name, &idx)) return keeps_fn[idx];
    if (find_struct(e->name) >= 0) return 1;           /* un constructor: un objeto nuevo */
    if (passes_func(e)) return 0;
    if (!strncmp(e->name, "mui_", 4) || !strncmp(e->name, "ra_", 3)) return 0;   /* pueden llamar a Dash */
    if (!strcmp(e->name, "Int") || !strcmp(e->name, "Float") || !strcmp(e->name, "Double") ||
        !strcmp(e->name, "Fixed")) return 1;
    for (b = 0; b < builtin_count; b++)
        if (!strcmp(builtin_info[b].name, e->name)) return 1;
    return 0;                                          /* una Func, o algo que no se sabe */
}

/* ¿un método de ese nombre que no conserva? (sin tipos: todos los "Struct.name") */
static int method_keeps(const char *name)
{
    int i;
    size_t ln = strlen(name);
    for (i = 0; i < prog->funcs.n; i++) {
        const char *fn = prog->funcs.v[i].name, *dot = strchr(fn, '.');
        if (dot && strlen(dot + 1) == ln && !strcmp(dot + 1, name) && !keeps_fn[i]) return 0;
    }
    return 1;
}

static int node_keeps(Node *e, int any_index);

static int list_keeps(NodeList *l, int any_index)
{
    int i;
    for (i = 0; i < l->n; i++)
        if (!node_keeps(l->v[i], any_index)) return 0;
    return 1;
}

/* any_index: x[i] = y cuenta aunque x sea un diccionario (en el cuerpo de otra función no se sabe) */
static int node_keeps(Node *e, int any_index)
{
    if (!e) return 1;
    switch (e->kind) {
    case S_EVLOOP: case S_WINDOW: case S_ON: case S_STOP:
        return 0;
    case S_STORE:
        if (e->b->kind == E_INDEX && (any_index || !IS_DICT(expr_type(e->b->a)))) return 0;
        break;
    case E_MCALL:
        if (!strcmp(e->name, "pop") || !strcmp(e->name, "remove") || !strcmp(e->name, "clear")) {
            if (any_index || !IS_DICT(expr_type(e->a))) return 0;
        } else if (!method_keeps(e->name)) {
            return 0;
        }
        break;
    case E_CALL:
        if (!call_keeps(e)) return 0;
        break;
    }
    return node_keeps(e->a, any_index) && node_keeps(e->b, any_index) && node_keeps(e->c, any_index) &&
           list_keeps(&e->args, any_index) && list_keeps(&e->body, any_index) && list_keeps(&e->els, any_index);
}

static void compute_keeps(void)
{
    int i, changed = 1;
    keeps_fn = xmalloc(prog->funcs.n + 1);
    for (i = 0; i < prog->funcs.n; i++) keeps_fn[i] = !prog->funcs.v[i].native;
    while (changed) {
        changed = 0;
        for (i = 0; i < prog->funcs.n; i++)
            if (keeps_fn[i] && !list_keeps(&prog->funcs.v[i].body, 1)) {
                keeps_fn[i] = 0;
                changed = 1;
            }
    }
}

/* ---- variables que toman prestado su valor, sin copia ni referencia propia (como ./dash: D66 los textos, Lorraine
   D44 los objetos) ----
   Una función "no libera" si nada de lo que hace, ni lo que llama, puede liberar algo que ya existía: ningún x[i] = y,
   pop, remove ni clear; ningún campo que no sea un número asignado (de los objetos: tampoco un texto); ninguna global
   ni parámetro que no sea un número reasignado; ni ventanas, ni EventLoop; solo builtins sin retrollamadas,
   constructores y funciones como ella. En una así:
   - un texto que solo recibe literales y elementos de una lista o diccionario de textos que cuelga de un parámetro
     (d[k], l[i], d.get(k, literal o parámetro)) apunta al texto, sin copiarlo (y sin liberarlo al salir);
   - un struct, lista o diccionario que solo recibe campos o elementos de un parámetro, global u otra variable así, y
     que no sale de la función (return, a otra variable, campo, lista, literal, constructor o builtin), también. */
typedef struct { char *name, *root; int kind; } LentAssign;   /* kind: 0 otro, 1 literal, 2 texto prestable, 3 objeto */
typedef struct { char **v; int n, cap; } NameVec;
typedef struct {
    struct { LentAssign *v; int n, cap; } as;
    NameVec others, escaped, lstr, lobj;
    int frees;   /* 1: puede liberar un texto u objeto (campo, parámetro o global); 2: un objeto */
} LentInfo;
static LentInfo *lent_info;
static char *nofree_txt, *nofree_obj;

static int name_in(NameVec *v, const char *name)
{
    int i;
    for (i = 0; i < v->n; i++)
        if (!strcmp(v->v[i], name)) return 1;
    return 0;
}

static void name_add(NameVec *v, char *name)
{
    if (!name_in(v, name)) VEC_PUSH(*v, name);
}

static int harmless(int t, int objs)
{
    return t == TY_INT || t == TY_BOOL || t == TY_CHAR || t == TY_FIXED || t == TY_FLOAT ||
           (objs && (t == TY_STR || t == TY_DOUBLE));
}

/* el campo name del struct st (-1: de todos los structs con un campo así) guarda algo que no se libera */
static int field_harmless(int st, const char *name, int objs)
{
    int i, j;
    for (i = 0; i < prog->structs.n; i++) {
        Struct *s = &prog->structs.v[i];
        if (st >= 0 && i != st) continue;
        for (j = 0; j < s->fields.n; j++)
            if (!strcmp(s->fields.v[j].name, name) && !harmless(s->fields.v[j].type, objs)) return 0;
    }
    return 1;
}

static int in_tenv(const char *name)
{
    int i;
    for (i = tenv.n - 1; i >= tenv_base; i--)
        if (!strcmp(tenv.v[i].name, name)) return 1;
    return 0;
}

/* la variable de la que cuelga e (a.b.c, l[i].x...), o NULL */
static char *lent_root(Node *e, int index_too)
{
    while (e->kind == E_FIELD || (index_too && e->kind == E_INDEX)) e = e->a;
    return e->kind == E_VAR ? e->name : NULL;
}

static int lent_str_value(Func *f, Node *v)
{
    int tc;
    char *r;
    Node *c;
    if (v->kind == E_INDEX) {
        c = v->a;
    } else if (v->kind == E_MCALL && !strcmp(v->name, "get") && v->args.n == 2) {
        Node *d = v->args.v[1];
        int pi;
        c = v->a;
        if (!(d->kind == E_STR || (d->kind == E_VAR && (pi = param_index(f, d->name)) >= 0 &&
                                   f->params.v[pi].type == TY_STR))) return 0;
        if (!IS_DICT(expr_type(c))) return 0;
    } else {
        return 0;
    }
    tc = expr_type(c);
    if (!((IS_DICT(tc) && dict_types.v[tc - TY_DICT].val == TY_STR) || tc == TY_ARR + TY_STR)) return 0;
    r = lent_root(c, 0);
    return r && param_index(f, r) >= 0;
}

static void lent_escape(LentInfo *li, Node *e)
{
    if (e && e->kind == E_VAR) name_add(&li->escaped, e->name);
}

/* los objetos que salen dentro de una expresión: a una lista o diccionario literal, a push/insert, a un builtin o
   constructor */
static void lent_escapes_expr(LentInfo *li, Node *e)
{
    int i;
    if (!e) return;
    if (e->kind == E_LIST) for (i = 0; i < e->args.n; i++) lent_escape(li, e->args.v[i]);
    if (e->kind == E_DICT) for (i = 1; i < e->args.n; i += 2) lent_escape(li, e->args.v[i]);
    if (e->kind == E_MCALL && (!strcmp(e->name, "push") || !strcmp(e->name, "insert")))
        for (i = 0; i < e->args.n; i++) lent_escape(li, e->args.v[i]);
    if (e->kind == E_CALL && !find_func(e->name, NULL))
        for (i = 0; i < e->args.n; i++) lent_escape(li, e->args.v[i]);
    lent_escapes_expr(li, e->a);
    lent_escapes_expr(li, e->b);
    lent_escapes_expr(li, e->c);
    for (i = 0; i < e->args.n; i++) lent_escapes_expr(li, e->args.v[i]);
}

static void lent_begin(void)
{
    lent_info = xmalloc(sizeof(LentInfo) * (prog->funcs.n + 1));
    memset(lent_info, 0, sizeof(LentInfo) * (prog->funcs.n + 1));
}

/* walk_types (collect_set) con los tipos de las variables a mano: lo de cada sentencia de la función collect_fn */
static void collect_lent(Node *st)
{
    LentInfo *li;
    Func *f;
    if (collect_fn < 0) return;
    li = &lent_info[collect_fn];
    f = &prog->funcs.v[collect_fn];
    switch (st->kind) {
    case S_STORE:
        if (st->b->kind == E_FIELD) {
            int ts = expr_type(st->b->a), s = IS_STRUCT(ts) ? ts - TY_STRUCT : -1;
            if (!field_harmless(s, st->b->name, 0)) li->frees |= 1;
            if (!field_harmless(s, st->b->name, 1)) li->frees |= 2;
        }
        lent_escape(li, st->a);
        break;
    case S_ASSIGN: {
        int pi = param_index(f, st->name);
        LentAssign la;
        if (pi >= 0) {
            if (!harmless(f->params.v[pi].type, 0)) li->frees |= 1;
            if (!harmless(f->params.v[pi].type, 1)) li->frees |= 2;
            break;
        }
        if (!in_tenv(st->name) && var_type(st->name) != TY_VOID) {   /* una global */
            li->frees |= 1;
            if (!harmless(var_type(st->name), 1)) li->frees |= 2;
            break;
        }
        la.name = st->name;
        la.root = NULL;
        la.kind = 0;
        if (st->a->kind == E_STR) la.kind = 1;
        else if (lent_str_value(f, st->a)) la.kind = 2;
        else if ((st->a->kind == E_FIELD || st->a->kind == E_INDEX) && IS_OBJ(expr_type(st->a)) &&
                 (la.root = lent_root(st->a, 1))) la.kind = 3;
        VEC_PUSH(li->as, la);
        lent_escape(li, st->a);
        break;
    }
    case S_VAR: case S_FOREACH: case S_FOR:
        name_add(&li->others, st->name);
        break;
    case S_RETURN:
        lent_escape(li, st->a);
        break;
    }
    lent_escapes_expr(li, st->a);
    if (st->kind != S_ASSIGN && st->kind != S_VAR) lent_escapes_expr(li, st->b);
}

static int call_nofree(Node *e, char *nf)
{
    int idx, b;
    if (find_func(e->name, &idx)) return nf[idx];
    if (find_struct(e->name) >= 0) return 1;
    if (passes_func(e)) return 0;
    if (!strncmp(e->name, "mui_", 4) || !strncmp(e->name, "ra_", 3)) return 0;
    if (!strcmp(e->name, "Int") || !strcmp(e->name, "Float") || !strcmp(e->name, "Double") ||
        !strcmp(e->name, "Fixed")) return 1;
    for (b = 0; b < builtin_count; b++)
        if (!strcmp(builtin_info[b].name, e->name)) return 1;
    return 0;
}

static int node_nofree(Node *e, char *nf);

static int list_nofree(NodeList *l, char *nf)
{
    int i;
    for (i = 0; i < l->n; i++)
        if (!node_nofree(l->v[i], nf)) return 0;
    return 1;
}

static int node_nofree(Node *e, char *nf)
{
    if (!e) return 1;
    switch (e->kind) {
    case S_EVLOOP: case S_WINDOW: case S_ON: case S_STOP:
        return 0;
    case S_STORE:
        if (e->b->kind == E_INDEX) return 0;
        break;
    case E_MCALL: {
        int i;
        size_t ln = strlen(e->name);
        if (!strcmp(e->name, "pop") || !strcmp(e->name, "remove") || !strcmp(e->name, "clear")) return 0;
        for (i = 0; i < prog->funcs.n; i++) {
            const char *dot = strchr(prog->funcs.v[i].name, '.');
            if (dot && strlen(dot + 1) == ln && !strcmp(dot + 1, e->name) && !nf[i]) return 0;
        }
        break;
    }
    case E_CALL:
        if (!call_nofree(e, nf)) return 0;
        break;
    }
    return node_nofree(e->a, nf) && node_nofree(e->b, nf) && node_nofree(e->c, nf) && list_nofree(&e->args, nf) &&
           list_nofree(&e->body, nf) && list_nofree(&e->els, nf);
}

static void nofree_fixpoint(char *nf, int bit)
{
    int i, changed = 1;
    for (i = 0; i < prog->funcs.n; i++) nf[i] = !prog->funcs.v[i].native && !(lent_info[i].frees & bit);
    while (changed) {
        changed = 0;
        for (i = 0; i < prog->funcs.n; i++)
            if (nf[i] && !list_nofree(&prog->funcs.v[i].body, nf)) {
                nf[i] = 0;
                changed = 1;
            }
    }
}

static void lent_end(void)
{
    int i, j, k, changed;
    nofree_txt = xmalloc(prog->funcs.n + 1);
    nofree_obj = xmalloc(prog->funcs.n + 1);
    nofree_fixpoint(nofree_txt, 1);
    nofree_fixpoint(nofree_obj, 2);
    for (i = 0; i < prog->funcs.n; i++) {
        LentInfo *li = &lent_info[i];
        Func *f = &prog->funcs.v[i];
        for (j = 0; j < li->as.n; j++) {
            char *name = li->as.v[j].name;
            int all_str = 1, any_str = 0, all_obj = 1;
            if (name_in(&li->lstr, name) || name_in(&li->lobj, name) || name_in(&li->others, name)) continue;
            for (k = 0; k < li->as.n; k++)
                if (!strcmp(li->as.v[k].name, name)) {
                    int kd = li->as.v[k].kind;
                    if (kd != 1 && kd != 2) all_str = 0;
                    if (kd == 2) any_str = 1;
                    if (kd != 3) all_obj = 0;
                }
            if (nofree_txt[i] && all_str && any_str && !name_in(&li->escaped, name)) VEC_PUSH(li->lstr, name);
            if (nofree_obj[i] && all_obj && !name_in(&li->escaped, name)) VEC_PUSH(li->lobj, name);
        }
        /* lo que cuelga de una variable con referencia propia puede irse cuando esa cambia */
        cur_file_g = f->file;
        for (changed = 1; changed; ) {
            changed = 0;
            for (j = 0; j < li->lobj.n; j++)
                for (k = 0; k < li->as.n; k++) {
                    char *r = li->as.v[k].root;
                    if (strcmp(li->as.v[k].name, li->lobj.v[j])) continue;
                    if (param_index(f, r) < 0 && !lookup_global(r) && !name_in(&li->lobj, r)) {
                        li->lobj.v[j] = li->lobj.v[--li->lobj.n];
                        changed = 1;
                        break;
                    }
                }
        }
    }
    cur_file_g = 0;
}

/* ¿name toma prestado su valor en la función que se genera ahora (obj: un objeto; si no, un texto)? */
static int is_lent(int obj, const char *name)
{
    int idx;
    if (!lent_info || !inl_stack.n) return 0;
    idx = inl_stack.v[inl_stack.n - 1];
    if (idx < 0 || idx >= prog->funcs.n) return 0;
    return name_in(obj ? &lent_info[idx].lobj : &lent_info[idx].lstr, name);
}

/* for x in lista: ¿puede el cuerpo sacar x de una lista? (si no, x va sin referencia propia) */
static int loop_keeps_elements(Node *n)
{
    if (!keeps_fn) compute_keeps();
    if (list_assigns(&n->body, n->name)) return 0;
    return list_keeps(&n->body, 0);
}

/* ---- for k in d.keys() por la tabla de d, sin hacer la lista de claves (como ./dash, _keys_in_place) ----
   d es una variable local o un parámetro (un diccionario de textos) y el cuerpo no puede quitar ninguna clave: no
   asigna d ni d[...], no llama a pop, remove ni clear, y solo llama a builtins sin retrollamadas, constructores y
   funciones que nunca sacan nada de una lista o diccionario (keeps_fn). k toma prestada cada clave; d se sostiene
   durante el bucle y su tabla se lee en cada vuelta. */
static int keys_body_ok(Node *e, const char *d)
{
    int i;
    if (!e) return 1;
    switch (e->kind) {
    case S_EVLOOP: case S_WINDOW: case S_ON: case S_STOP:
        return 0;
    case S_ASSIGN:
        if (!strcmp(e->name, d)) return 0;
        break;
    case S_STORE:
        if (e->b->kind == E_INDEX && e->b->a->kind == E_VAR && !strcmp(e->b->a->name, d)) return 0;
        break;
    case E_MCALL:
        if (!strcmp(e->name, "pop") || !strcmp(e->name, "remove") || !strcmp(e->name, "clear")) return 0;
        if (!method_keeps(e->name)) return 0;
        break;
    case E_CALL:
        if (!call_keeps(e)) return 0;
        break;
    }
    if (!keys_body_ok(e->a, d) || !keys_body_ok(e->b, d) || !keys_body_ok(e->c, d)) return 0;
    for (i = 0; i < e->args.n; i++)
        if (!keys_body_ok(e->args.v[i], d)) return 0;
    for (i = 0; i < e->body.n; i++)
        if (!keys_body_ok(e->body.v[i], d)) return 0;
    for (i = 0; i < e->els.n; i++)
        if (!keys_body_ok(e->els.v[i], d)) return 0;
    return 1;
}

static int keys_in_place(Node *n)
{
    Node *it = n->a;
    int t, i;
    if (it->kind != E_MCALL || strcmp(it->name, "keys") || it->args.n || it->a->kind != E_VAR) return 0;
    t = expr_type(it->a);
    if (!IS_DICT(t) || dict_ikeys(t) || !find_local(it->a->name)) return 0;
    if (!keeps_fn) compute_keeps();
    if (list_assigns(&n->body, n->name)) return 0;     /* (k = ...: k no puede tomar prestada la clave) */
    for (i = 0; i < n->body.n; i++)
        if (!keys_body_ok(n->body.v[i], it->a->name)) return 0;
    return 1;
}

static void gen_keys_loop(Node *n)
{
    int top = new_label(), test = new_label(), cont = new_label(), done = new_label(), d_slot, idx_slot;
    MarkScope ms;
    Loop lp;
    Var vd, vi, vx;
    int t = expr_type(n->a->a);
    ms = mark_begin();
    enter_scope();
    value(n->a->a);
    vd = declare_slot("", t, &d_slot);
    locals.v[locals.n - 1].owned = 2;                  /* al acabar, _dash_release */
    store_d0(&vd);
    push_d0();
    rt_call("_dl_hold", 1, 0);
    vi = declare_slot("", TY_INT, &idx_slot);
    set_imm(&vi, 0);
    enter_loop();
    use_slot(d_slot);
    use_slot(idx_slot);
    branch(CC_T, test);
    def_label(top);
    mark_release(&ms);
    lp.brk = done;
    lp.cont = cont;
    enter_scope();
    lp.depth = depth;
    lp.sp = sp_depth;
    VEC_PUSH(loops, lp);
    /* k = d->keys[i]; sin clave, la siguiente */
    use_slot(d_slot);
    vd = slot_var(d_slot, t);
    load_a0(&vd);
    a0_deref();                                       /* keys */
    use_slot(idx_slot);
    vi = slot_var(idx_slot, TY_INT);
    load_var(0, &vi);
    load_elem();
    branch(CC_EQ, cont);
    vx = declare(n->name, TY_STR);
    store_d0(&vx);
    {
        /* d[k] del cuerpo: de la casilla (kloop_of) */
        Local *ld = n->a->a->kind == E_VAR ? find_local(n->a->a->name) : NULL;
        int pushed = 0;
        if (ld && !debug && !list_assigns(&n->body, n->name)) {
            int i, passed = 0;
            for (i = 0; i < n->body.n && !passed; i++) passed = dict_passed(n->body.v[i], n->a->a->name);
            if (!passed) {
                KLoop kl;
                kl.d = n->a->a->name;
                kl.k = n->name;
                kl.d_local = ld->slot;
                kl.k_slot = locals.v[locals.n - 1].slot;
                kl.depth = inl_stack.n;
                kl.dict_slot = d_slot;
                kl.idx_slot = idx_slot;
                VEC_PUSH(kloops, kl);
                pushed = 1;
            }
        }
        gen_block(&n->body);
        if (pushed) kloops.n--;
    }
    loops.n--;
    leave_scope();
    def_label(cont);
    use_slot(idx_slot);
    add_imm_ea(1, &vi);
    def_label(test);
    /* ¿d, de claves de texto, e i < cap? */
    use_slot(d_slot);
    load_var(0, &vd);
    branch(CC_EQ, done);
    move_d0_a0();
    dict_test_ikeys();
    branch(CC_NE, done);
    use_slot(idx_slot);
    if (vi.kind == V_REG) {
        cmp_reg_a0(vi.reg, DICT_CAP);
    } else {
        load_var(1, &vi);
        cmp_reg_a0(1, DICT_CAP);
    }
    branch(CC_LT, top);
    def_label(done);
    leave_loop();
    leave_scope();                                     /* _dash_release de d */
    mark_end(&ms);
}

/* ¿Nada en el cuerpo de un for puede cambiar listas? Sin llamadas (funciones, builtins, métodos ni constructores),
   sin escribir campos ni elementos (S_STORE), sin asignar globales ni EventLoop. Entonces la lista del for (que se
   sostiene) no cambia: sus datos y su largo se leen una vez (gen_foreach) */
static int body_frozen(Node *e)
{
    int i;
    if (!e) return 1;
    switch (e->kind) {
    case E_CALL: case E_MCALL: case E_FUNCREF: case E_LIST: case E_DICT:
    case S_STORE: case S_EVLOOP: case S_WINDOW: case S_ON: case S_STOP:
        return 0;
    case S_ASSIGN:
        if (lookup_global(e->name) && !find_local(e->name)) return 0;
        break;
    default:
        break;
    }
    if (!body_frozen(e->a) || !body_frozen(e->b) || !body_frozen(e->c)) return 0;
    for (i = 0; i < e->args.n; i++)
        if (!body_frozen(e->args.v[i])) return 0;
    for (i = 0; i < e->body.n; i++)
        if (!body_frozen(e->body.v[i])) return 0;
    for (i = 0; i < e->els.n; i++)
        if (!body_frozen(e->els.v[i])) return 0;
    return 1;
}

/* for x in lista con el cuerpo sin nada que cambie listas (body_frozen) y sin referencia ni copia por vuelta: un
   puntero a los datos que avanza y las vueltas que quedan, leídos una vez (como gcc con el C de ./dash) */
static void gen_foreach_frozen(Node *n, int t, int et, int arr_slot, MarkScope *ms)
{
    int top = new_label(), cont = new_label(), done = new_label(), ptr_slot, cnt_slot;
    Var va, vp, vc, vx;
    Loop lp;
    use_slot(arr_slot);
    va = slot_var(arr_slot, t);
    load_var(0, &va);
    branch(CC_EQ, done);                               /* (una lista nil no tiene elementos) */
    move_d0_a0();
    load_a0_raw(ARR_LEN);                              /* el largo */
    branch(CC_LE, done);
    vc = declare_slot("", TY_INT, &cnt_slot);
    store_d0(&vc);
    load_a0_raw(ARR_DATA);                             /* los datos */
    vp = declare_slot("", TY_INT, &ptr_slot);
    store_d0(&vp);
    enter_loop();
    use_slot(arr_slot);
    use_slot(ptr_slot);
    use_slot(cnt_slot);
    def_label(top);
    mark_release(ms);
    lp.brk = done;
    lp.cont = cont;
    enter_scope();
    lp.depth = depth;
    lp.sp = sp_depth;
    VEC_PUSH(loops, lp);
    use_slot(ptr_slot);
    vp = slot_var(ptr_slot, TY_INT);
    load_a0(&vp);
    load_a0_raw(0);                                    /* el elemento */
    add_imm_ea(ELEM, &vp);                             /* el puntero, al siguiente */
    vx = declare(n->name, et);
    store_d0(&vx);
    gen_block(&n->body);
    loops.n--;
    leave_scope();
    def_label(cont);
    use_slot(cnt_slot);
    vc = slot_var(cnt_slot, TY_INT);
    add_imm_ea(-1, &vc);                               /* subq.l #1,vueltas */
    branch(CC_NE, top);
    def_label(done);
    leave_loop();
    leave_scope();                                     /* _dash_release de la lista */
    mark_end(ms);
}

static void gen_foreach(Node *n)
{
    int t = expr_type(n->a), et, top = new_label(), test = new_label(), cont = new_label(), done = new_label();
    int arr_slot, idx_slot, keep;
    MarkScope ms;
    Loop lp;
    Var va, vi, vx;
    if (t == TY_STR) {
        gen_foreach_str(n);
        return;
    }
    if (keys_in_place(n)) {
        gen_keys_loop(n);
        return;
    }
    if (!IS_ARR(t)) fatal_node(n, "for ... in pide una lista");
    et = t == TY_ARR + TY_VOID ? TY_INT : t - TY_ARR;
    ms = mark_begin();
    enter_scope();
    value(n->a);
    va = declare_slot("", t, &arr_slot);
    locals.v[locals.n - 1].owned = 2;                  /* al acabar, _dash_release */
    store_d0(&va);
    push_d0();
    rt_call("_dl_hold", 1, 0);
    keep = (IS_OBJ(et) && !loop_keeps_elements(n)) || (IS_STRLIKE(et) && list_assigns(&n->body, n->name));
    if (!keep && !debug) {
        int frozen = 1, i;
        for (i = 0; i < n->body.n && frozen; i++) frozen = body_frozen(n->body.v[i]);
        if (frozen) {
            gen_foreach_frozen(n, t, et, arr_slot, &ms);
            return;
        }
    }
    vi = declare_slot("", TY_INT, &idx_slot);
    set_imm(&vi, 0);
    enter_loop();
    use_slot(arr_slot);
    use_slot(idx_slot);
    branch(CC_T, test);
    def_label(top);
    mark_release(&ms);
    lp.brk = done;
    lp.cont = cont;
    enter_scope();
    lp.depth = depth;
    lp.sp = sp_depth;
    VEC_PUSH(loops, lp);
    /* x = data[i] */
    use_slot(arr_slot);
    va = slot_var(arr_slot, t);
    load_a0(&va);
    a0_deref();                                       /* los datos */
    use_slot(idx_slot);
    vi = slot_var(idx_slot, TY_INT);
    load_var(0, &vi);
    load_elem();
    keep = IS_OBJ(et) && !loop_keeps_elements(n);
    if (keep) {
        /* un objeto, con una referencia durante la vuelta: el cuerpo podría sacarlo de la lista */
        push_d0();
        rt_call("_dl_retain_r", 1, 0);
    } else if (IS_STRLIKE(et) && list_assigns(&n->body, n->name)) {
        /* un texto que el cuerpo cambia (x = str_trim(x)): una copia suya, como ./dash; si no, la asignación
           liberaba el de la lista (y la lista, otra vez al acabar) */
        push_d0();
        rt_call("_dl_str_dup", 1, 0);
        keep = 1;
    }
    vx = declare(n->name, et);
    if (keep) locals.v[locals.n - 1].owned = IS_OBJ(et) ? 2 : 1;
    store_d0(&vx);
    gen_block(&n->body);
    loops.n--;
    leave_scope();
    def_label(cont);
    use_slot(idx_slot);
    add_imm_ea(1, &vi);
    def_label(test);
    /* ¿i < length? (una lista nil no tiene elementos) */
    use_slot(arr_slot);
    load_var(0, &va);
    branch(CC_EQ, done);
    move_d0_a0();
    use_slot(idx_slot);
    if (vi.kind == V_REG) {
        cmp_reg_a0(vi.reg, ARR_LEN);
    } else {
        load_var(1, &vi);
        cmp_reg_a0(1, ARR_LEN);
    }
    branch(CC_LT, top);
    def_label(done);
    leave_loop();
    leave_scope();                                     /* _dash_release de la lista */
    mark_end(&ms);
}

/* ---- ventanas ---- */
static int find_window(const char *name)
{
    int i;
    for (i = 0; i < prog->windows.n; i++)
        if (!strcmp(prog->windows.v[i].name, name)) return i;
    return -1;
}

static void gen_window_op(Node *n)
{
    int wi = find_window(n->name);
    if (wi < 0) fatal_node(n, "la ventana %s no existe", n->name);
    if (n->val) {
        pea_window(wi);                                /* dl_window_open(descriptor, &variable) */
        push_label(win_desc_label[wi]);                /* el descriptor */
        rt_call("_dl_window_open", 2, 0);
        if (needs_area) {
            /* _dash_init_area(_dash_rp, ancho, alto), como ./dash */
            jsr_sym("_dl_init_area");
        }
    } else {
        pea_window(wi);
        rt_call("_dl_window_close", 1, 0);
    }
}

/* la ventana del EventLoop: la última abierta antes en el código (como ./dash, context.current_window) */
static int cur_window = -1;

/* EventLoop: cada mensaje (dl_event_next) con su marca de temporales; según su clase, los On */
static void gen_evloop(Node *n)
{
    int top = new_label(), done = new_label(), i, wi = cur_window, timer = -1;
    MarkScope ms;
    Loop lp;
    if (wi < 0) fatal_node(n, "EventLoop sin ventana abierta antes");
    for (i = 0; i < n->body.n; i++)
        if (n->body.v[i]->val == ON_TIMER) timer = i;
    if (uses_gadgets) {
        /* los mensajes con GT_GetIMsg, y el del gadget apuntado (gadget_id) */
        load_imm(0, gadget_keys);
        push_d0();
        rt_call("_dl_event_gt_on", 1, 0);
    }
    ms = mark_begin();
    enter_loop();
    def_label(top);
    mark_release(&ms);
    if (timer >= 0) {
        Node *a[1];
        a[0] = n->body.v[timer]->a;
        args_to_stack(a, 1, NULL);                     /* el intervalo, en la pila */
        pea_window(wi);
        rt_call("_dl_event_next_timer", 2, 0);
    } else {
        pea_window(wi);
        rt_call("_dl_event_next", 1, 0);
    }
    tst_d0();
    branch(CC_EQ, done);                               /* la ventana se cerró */
    {
        EvLoop ev;
        ev.done = done;
        ev.depth = depth + 1;                          /* la de los cuerpos de los On */
        ev.sp = sp_depth;                              /* sin la clase */
        VEC_PUSH(evloops, ev);
    }
    for (i = 0; i < n->body.n; i++) {
        Node *h = n->body.v[i];
        static const long cls[] = {0x200 /* CLOSEWINDOW */, 0x400 /* RAWKEY */, 0x8 /* MOUSEBUTTONS */, -1, 0x40, 0x100,
                                   0x8 /* MOUSEBUTTONS */, 0x80000 /* INACTIVEWINDOW */};
        int next = new_label(), skip = new_label();
        /* la clase está en d0 hasta aquí: cada On la compara y, si no es la suya, salta al siguiente */
        cmp_d0_k(cls[h->val], 1);
        branch(CC_NE, next);
        push_d0();                                     /* la clase, para el On siguiente */
        if (h->val == ON_KEY) {
            /* las teclas al soltarse no cuentan; On Key "a" mira el texto de la tecla, On Key 69 su código */
            jsr_sym("_dl_event_code");
            test_bit_d0(7);                            /* IECODE_UP_PREFIX */
            branch(CC_NE, skip);
            if (h->a) {
                long code = -1;
                if (h->a->kind == E_INT) code = h->a->val;
                else if (h->a->len == 1) {
                    load_imm(0, (unsigned char)h->a->str[0]);
                    push_d0();
                    rt_call("_dl_key_char", 1, 0);
                    tst_d0();
                    branch(CC_EQ, skip);
                } else {
                    int k;
                    for (k = 0; key_names[k].name; k++) {
                        const char *a = key_names[k].name, *b = h->a->str;
                        while (*a && toupper((unsigned char)*a) == toupper((unsigned char)*b)) a++, b++;
                        if (!*a && !*b) code = key_names[k].code;
                    }
                    if (code < 0) fatal_at(h->a->line, h->a->col, "la tecla %s no existe", h->a->str);
                }
                if (code >= 0) {
                    jsr_sym("_dl_event_code");
                    cmp_d0_k(code, 0);
                    branch(CC_NE, skip);
                }
            }
        } else if (h->val == ON_CLICK || h->val == ON_RIGHTCLICK) {
            jsr_sym("_dl_event_code");
            cmp_d0_k(h->val == ON_CLICK ? 0x68 : 0x69, 0);   /* SELECTDOWN (MENUDOWN) */
            branch(CC_NE, skip);
        }
        {
            /* el cuerpo: un bloque; un break o continue suelto acaba este mensaje (como en el switch
               de ./dash); Stop sale del EventLoop */
            int mtop = new_label();
            if (h->val == ON_MENU) {
                /* una vez por cada opción elegida (menu_id dice cuál) */
                jsr_sym("_dl_menu_begin");
                def_label(mtop);
                jsr_sym("_dl_menu_next");
                tst_d0();
                branch(CC_EQ, skip);
            }
            enter_scope();
            lp.brk = skip;
            lp.cont = h->val == ON_MENU ? mtop : skip;
            lp.depth = depth;
            lp.sp = sp_depth;
            VEC_PUSH(loops, lp);
            gen_block(&h->body);
            loops.n--;
            leave_scope();
            if (h->val == ON_MENU) branch(CC_T, mtop);
        }
        def_label(skip);
        pop_d0();                                      /* la clase otra vez */
        def_label(next);
    }
    branch(CC_T, top);
    evloops.n--;
    def_label(done);
    leave_loop();
    mark_end(&ms);
    /* al acabar, la ventana se cierra */
    pea_window(wi);
    rt_call("_dl_window_close", 1, 0);
}

static int forced_type = -1;   /* el tipo de una función de una línea puesta como expresión */

static void gen_stmt(Node *n)
{
    Var v;
    long k;
    int ty, forced = forced_type;
    forced_type = -1;
    cur_line = n->line;
    cur_file = n->file;
    cur_file_g = n->file;
    src_name = src_files.v[n->file];                   /* para los errores al compilar */
    if (debug) {
        /* el sitio de la línea: un NOP que el depurador cambia por un TRAP */
        if (pass == 2) {
            DbgLine d;
            d.label = new_label();
            def_label(d.label);
            d.file = n->file;
            d.line = n->line;
            VEC_PUSH(dbg_lines, d);
        }
        debug_nop();
    }
    if (memcheck) {
        /* el sitio de la instrucción, para los avisos (_DASH_MC_WHERE de ./dash) */
        char where[600];
        snprintf(where, sizeof where, "%s:%d", src_files.v[n->file], n->line);
        set_rt_var("__dash_mc_where", where, 0);
    }
    switch (n->kind) {
    case S_PRINT:
        if (n->a->kind == E_STR) {
            pea_string(n->a->str, n->a->len);
            jsr_sym("__dash_print_str");
        } else {
            ty = gen_expr(n->a);
            need_value(n->a, ty);
            push_d0();
            if (ty == TY_FLOAT || ty == TY_DOUBLE || ty == TY_FIXED) {
                to_str(ty);                            /* un Float, como texto (DashString_from_float) */
                store_d0_arg(0);
                ty = TY_STR;
            }
            jsr_sym(ty == TY_BOOL ? "__dash_print_bool" : ty == TY_STR || ty == TY_NIL ? "__dash_print_str" :
                    ty == TY_CHAR ? "__dash_print_char" : "__dash_print_int");
        }
        pop_args(1);
        if (print_flush) rt_call("_dl_print_flush", 0, 0);
        return;
    case S_ASSIGN:
    case S_VAR:
        {
            Local *lc = find_local(n->name);
            if (lc) lc->entry = 0;                     /* el rango de entrada ya no vale */
            /* x = nil de una variable nueva: no dice qué guarda (lo que se le asigne después se perdía), como ./dash */
            if (n->kind == S_ASSIGN && n->a->kind == E_NIL && !lc && lookup_kind(n->name) == V_GLOBAL &&
                !lookup_global(n->name))
                fatal_node(n, "'%s = nil' no dice qué guarda %s: decláralo con su tipo (var %s: Tipo = nil)",
                           n->name, n->name, n->name);
        }
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
        {
            int tt = n->kind == S_VAR ? n->type : var_type(n->name);
            if (tt == TY_VOID) tt = expr_type(n->a);   /* una variable nueva */
            else if (n->kind == S_ASSIGN && tt == TY_STR && n->a->kind != E_NIL) {
                /* (como ./dash: un número en una variable que guarda un texto es un error, no un texto) */
                int et = expr_type(n->a);
                if (et == TY_INT || et == TY_BOOL || et == TY_FLOAT || et == TY_FIXED)
                    fatal_node(n, "no se puede guardar un %s en %s, que guarda un String",
                               et == TY_BOOL ? "Bool" : et == TY_FLOAT ? "Float" : et == TY_FIXED ? "Fixed" : "Int", n->name);
            }
            if (IS_STRLIKE(tt)) {
                gen_str_assign(n, tt);
                return;
            }
            if (IS_OBJ(tt)) {
                gen_obj_assign(n, tt);
                return;
            }
            if (tt == TY_FLOAT || tt == TY_FIXED) {
                /* un Float o un Fixed: el valor convertido, sin las cuentas de enteros en su sitio */
                Local *lc = find_local(n->name);
                int fresh = n->kind == S_VAR || (!lc && !lookup_global(n->name));
                if (tt == TY_FIXED) fix_value(n->a);
                else float_value(n->a);
                v = fresh ? declare(n->name, tt) : lookup(n->name);
                if (v.kind == V_CONST) fatal_node(n, "%s es una constante", n->name);
                store_d0(&v);
                return;
            }
        }
        if (n->kind == S_ASSIGN && gen_update(n)) return;
        if (!debug && fold(n->a, &k) && lookup_kind(n->name) == V_GLOBAL && !lookup_global(n->name) &&
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
            lc.entry = 0;
            lc.owned = 0;
            VEC_PUSH(locals, lc);
            return;
        }
        if (n->kind == S_ASSIGN && fold(n->a, &k)) {
            v = lookup(n->name);
            if (v.kind == V_NONE) v = declare(n->name, forced >= 0 ? forced : fold_type(n->a));
            if (v.kind == V_CONST) fatal_node(n, "%s es una constante", n->name);
            if (v.kind == V_REG) {
                load_imm(v.reg, k);                    /* moveq #k,dN */
            } else {
                load_imm(0, k);
                store_d0(&v);
            }
            return;
        }
        if (n->kind == S_ASSIGN && forced < 0 && assign_in_reg(n)) return;
        ty = gen_expr(n->a);
        need_value(n->a, ty);
        if (forced >= 0) ty = forced;
        v = lookup(n->name);
        if (n->kind == S_VAR || v.kind == V_NONE) {
            /* la primera asignación declara (en el bloque actual) */
            v = declare(n->name, n->kind == S_VAR ? n->type : ty);
        } else if (v.kind == V_CONST) {
            fatal_node(n, "%s es una constante", n->name);
        }
        store_d0_stmt(&v);
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
        MarkScope ms;
        int top, test, done, base = repls.n, slots = slot_uses.n;
        if (!autoclose && gen_counted_while(n)) return;
        top = new_label();
        test = new_label();
        done = new_label();
        /* si gen_counted_while no ha podido en la segunda pasada, no se suben constantes:
           los huecos tienen que salir en el mismo orden que en la primera */
        if (slot_uses.n == slots) hoist_consts(n->a);
        ms = mark_begin();
        enter_loop();
        /* La condición va al final. Si es barata, también al entrar (en vez de saltar
           al final): así al final solo se llega desde el cuerpo y su última instrucción
           puede servir de comparación. */
        if (has_call(n->a)) branch(CC_T, test);
        else if (!true_at_entry(n->a)) gen_branch(n->a, done, 0);   /* si se sabe que se cumple, nada */
        def_label(top);
        mark_release(&ms);
        if (autoclose) rt_call("_dl_ac_loop", 0, 0);
        lp.brk = done;
        lp.cont = test;
        enter_scope();
        lp.depth = depth;
        lp.sp = sp_depth;
        VEC_PUSH(loops, lp);
        gen_block(&n->body);
        leave_scope();
        loops.n--;
        def_label_fwd(test);
        gen_branch(n->a, top, 1);
        def_label(done);
        repls.n = base;
        leave_loop();
        mark_end(&ms);
        return;
    }
    case S_FOR:
        gen_for(n);
        return;
    case S_FOREACH:
        gen_foreach(n);
        return;
    case S_WINDOW:
        gen_window_op(n);
        if (n->val) cur_window = find_window(n->name);
        return;
    case S_EVLOOP:
        gen_evloop(n);
        return;
    case S_STOP:
        if (!evloops.n) fatal_node(n, "Stop fuera de un EventLoop");
        {
            /* como un break del EventLoop: lo de los bucles de dentro se suelta */
            EvLoop *ev = &evloops.v[evloops.n - 1];
            free_owned(ev->depth, 0);
            if (sp_depth != ev->sp) skip_stack(sp_depth - ev->sp);
            branch(CC_T, ev->done);
        }
        return;
    case S_STORE:
        if (n->b->kind == E_INDEX && IS_ARR(expr_type(n->b->a))) {
            gen_arr_store(n->b, n->a);
            return;
        }
        if (n->b->kind == E_FIELD && gen_field_store(n->b, n->a)) return;
        if (n->b->kind == E_INDEX && IS_DICT(expr_type(n->b->a))) {
            gen_dict_set(n->b, n->a);
            return;
        }
        fatal_node(n, "(sin --gcc) esta asignación aún no está");
        return;
    case S_BREAK:
    case S_CONTINUE:
        if (loops.n <= loop_base) fatal_node(n, "%s fuera de un bucle", n->kind == S_BREAK ? "break" : "continue");
        {
            Loop *lp = &loops.v[loops.n - 1];
            free_owned(lp->depth, 0);
            if (sp_depth != lp->sp) skip_stack(sp_depth - lp->sp);
            branch(CC_T, n->kind == S_BREAK ? lp->brk : lp->cont);
        }
        return;
    case S_RETURN: {
        int owned = has_owned(0, 1);
        if (n->a && ret_branch >= 0) {
            if (owned || sp_depth != ret_sp) {
                value(n->a);
                if (owned) {
                    push_d0();
                    free_owned(0, 1);
                    pop_d0();
                }
                /* dentro de un bucle (sus marcas en la pila: un for de otra función copiada en una condición), fuera
                   antes de saltar */
                if (sp_depth != ret_sp) {
                    skip_stack(sp_depth - ret_sp);
                    tst_d0();
                    branch(ret_when ? CC_NE : CC_EQ, ret_branch);
                    branch(CC_T, ret_label);           /* (ya sin las marcas: no otra vez abajo) */
                    return;
                }
                tst_d0();
                branch(ret_when ? CC_NE : CC_EQ, ret_branch);
            } else {
                gen_branch(n->a, ret_branch, ret_when);
            }
        } else if (n->a && cur_ret == TY_FIXED) {
            fix_value(n->a);                           /* return 1 en una -> Fixed: 1.0 */
            if (owned) {
                push_d0();
                free_owned(0, 1);
                pop_d0();
            }
        } else if (n->a && cur_ret == TY_DOUBLE) {
            /* un Double: su caja (un número, convertido); la de otro, como temporal de quien llama */
            dbl_value(n->a);
            if (!is_tmp_expr(n->a)) {
                push_d0();
                rt_call("_dl_str_ret", 1, 1);
            }
            if (owned) {
                push_d0();
                free_owned(0, 1);
                pop_d0();
            }
        } else if (n->a) {
            ty = gen_expr(n->a);
            need_value(n->a, ty);
            coerce(ty, cur_ret);
            if (cur_ret == TY_STR) {
                to_str(ty);
                /* un texto que ya es de alguien sale como temporal de quien llama */
                if (!is_tmp_expr(n->a)) {
                    push_d0();
                    rt_call("_dl_str_ret", 1, 1);
                }
            }
            if (IS_OBJ(cur_ret)) {
                /* una referencia mientras se liberan las variables; luego flota (_dash_obj_float):
                   en una función, después de soltar sus temporales (en ret_label) */
                push_d0();
                rt_call("_dl_retain_r", 1, 0);
            }
            if (owned) {
                push_d0();
                free_owned(0, 1);
                pop_d0();
            }
            if (IS_OBJ(cur_ret) && cur_frame) {
                push_d0();
                rt_call("_dl_obj_float", 1, 1);
            }
        } else if (owned) {
            free_owned(0, 1);
        }
        if (sp_depth != ret_sp) skip_stack(sp_depth - ret_sp);   /* fuera las marcas de los bucles */
        branch(CC_T, ret_label);
        return;
    }
    }
    fatal_node(n, "instrucción no admitida");
}

static void gen_block(NodeList *b)
{
    int i;
    for (i = 0; i < b->n; i++) gen_stmt(b->v[i]);
}

/* una pasada sobre la función: link a5,#-marco; guarda registros ... recupera; unlk a5; rts */
static void gen_global_inits(void);

/* ¿Usa el cuerpo str_code(name, ...), name[i] o name.length? */
static int len_uses_node(Node *e, const char *name)
{
    int i;
    if (!e) return 0;
    if (e->kind == E_CALL && !strcmp(e->name, "str_code") && e->args.n == 2 && e->args.v[0]->kind == E_VAR &&
        !strcmp(e->args.v[0]->name, name)) return 1;
    if ((e->kind == E_INDEX || (e->kind == E_FIELD && !strcmp(e->name, "length"))) && e->a && e->a->kind == E_VAR &&
        !strcmp(e->a->name, name)) return 1;
    if (len_uses_node(e->a, name) || len_uses_node(e->b, name) || len_uses_node(e->c, name)) return 1;
    for (i = 0; i < e->args.n; i++)
        if (len_uses_node(e->args.v[i], name)) return 1;
    for (i = 0; i < e->body.n; i++)
        if (len_uses_node(e->body.v[i], name)) return 1;
    for (i = 0; i < e->els.n; i++)
        if (len_uses_node(e->els.v[i], name)) return 1;
    return 0;
}

static int len_uses(NodeList *body, const char *name)
{
    int i;
    for (i = 0; i < body->n; i++)
        if (len_uses_node(body->v[i], name)) return 1;
    return 0;
}

static void gen_function_pass(int label, Func *f, NodeList *body)
{
    int i, nregs = 0, used = 0;
    MarkScope fm;

    n_plen = 0;
    plen_depth = -1;
    locals.n = 0;
    depth = 0;
    nframe = 0;
    cur_file_g = f ? f->file : 0;
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
        if (slot_reg.v[i] >= 0 && !(used & 1 << slot_reg.v[i])) {
            nregs++;
            used |= 1 << slot_reg.v[i];
        }

    sp_depth = 0;
    param_base = fn_param_base(nregs);
    def_label(label);
    if (debug && pass == 2) {
        DbgFunc d;
        d.name = f ? f->name : "Main";
        d.start = label;
        d.end = -1;
        d.file = f ? f->file : 0;
        d.line = f ? f->line : 0;
        VEC_PUSH(dbg_funcs, d);
    }
    fn_prologue(frameless, used);

    if (f)
        for (i = 0; i < f->params.n; i++) {
            Local lc;
            lc.name = f->params.v[i].name;
            lc.slot = new_slot(param_off(i));
            lc.type = f->params.v[i].type;
            lc.depth = 0;
            lc.frame = 0;
            lc.val = 0;
            lc.ranged = 0;
            lc.entry = 0;
            lc.owned = 0;
            VEC_PUSH(locals, lc);
            dbg_var(lc.name, lc.type, lc.slot, f->line);
            if (slot_reg.v[lc.slot] >= 0) load_param(slot_reg.v[lc.slot], i, frameless);
        }
    mark_seq = 0;
    made_tmp = 0;
    cur_ret = f ? f->ret : TY_VOID;
    if (f) {
        /* un parámetro de texto que el cuerpo cambia: una copia suya, como en ./dash */
        int idx = (int)(f - prog->funcs.v);
        for (i = 0; i < f->params.n; i++)
            if ((IS_STRLIKE(f->params.v[i].type) || IS_OBJ(f->params.v[i].type)) && param_set[idx][i]) {
                /* (una lista o un struct: una referencia suya; un temporal de quien llama sigue siéndolo, si no al
                   soltarla al salir se liberaba mientras quien llamó aún lo usa) */
                int str = IS_STRLIKE(f->params.v[i].type);
                Var v = lookup(f->params.v[i].name);
                push_ea(&v);
                rt_call(str ? "_dl_str_dup" : "_dl_hold_r", 1, 0);
                store_d0(&v);
                locals.v[i].owned = str ? 1 : 2;
            }
        n_plen = 0;
        plen_depth = -1;
        /* (solo si la función no puede liberar textos ni objetos, ni ella ni lo que llama: si no, el texto del
           parámetro podría liberarse, o su memoria ser de otro, mientras corre; Tachyon colgaba así) */
        if (!debug && nofree_txt && nofree_txt[idx] && nofree_obj[idx])
            for (i = 0; i < f->params.n && n_plen < 8; i++)
                if (f->params.v[i].type == TY_STR && !param_set[idx][i] && len_uses(body, f->params.v[i].name)) {
                    Node pv;
                    Var vl;
                    memset(&pv, 0, sizeof pv);
                    pv.kind = E_VAR;
                    pv.name = f->params.v[i].name;
                    str_len_inline(&pv);                   /* (aún sin plen: lo mide) */
                    plen[n_plen].name = pv.name;
                    plen[n_plen].param = locals.v[i].slot;
                    vl = declare_slot("", TY_INT, &plen[n_plen].slot);
                    store_d0(&vl);
                    n_plen++;
                }
        plen_depth = inl_stack.n;
        if (profile) {
            push_word(idx + 1);                        /* su número */
            rt_call("_dl_prof_enter", 1, 0);
        }
        fm = mark_begin();
    } else {
        if (profile) {
            push_word(prog->funcs.n + 1);              /* cuántas */
            push_label(prof_label);                    /* sus nombres */
            rt_call("_dl_prof_start", 2, 0);
        }
        gen_global_inits();
    }
    ret_sp = sp_depth;
    gen_block(body);
    if (f) free_owned(0, 1);                           /* cayendo por el final */
    if (!f && memcheck) {
        /* --memcheck: al acabar Main se suelta todo, para que el resumen cuente solo lo perdido */
        free_owned(0, 1);
        for (i = 0; i < prog->globals.n; i++)
            if (IS_STRLIKE(global_type[i]) || IS_OBJ(global_type[i])) {
                Var g;
                g.kind = V_GLOBAL;
                g.off = global_off(i);
                g.type = global_type[i];
                push_ea(&g);
                rt_call(IS_STRLIKE(global_type[i]) ? "_dl_str_free" : "_dl_release", 1, 0);
                clear_global(g.off);
            }
        jsr_sym("_dl_tmp_release_all");
    }
    if (f && IS_OBJ(cur_ret)) zero_d0();               /* sin return, nil */
    def_label(ret_label);
    if (f) {
        if (pass == 1) mark_need.v[fm.idx] = made_tmp;
        if (fm.on) {
            /* fuera los temporales de la función, menos el texto que devuelve */
            int skip = new_label();
            if (!IS_STRLIKE(cur_ret)) tmp_newer(0, skip);   /* (d0, lo que devuelve, no se toca) */
            push_d0();
            push_sp_off(4);                            /* la marca */
            rt_call(IS_STRLIKE(cur_ret) ? "_dl_tmp_release_keep" : "_dl_tmp_release_ret", 2, 0);
            def_label(skip);
            pop_args(1);
        }
        if (IS_OBJ(cur_ret)) {
            push_d0();
            rt_call("_dl_obj_float", 1, 0);
        }
        if (profile) {
            push_d0();
            jsr_sym("_dl_prof_leave");
            pop_d0();
        }
    } else if (profile) {
        jsr_sym("_dl_prof_report");
    }
    if (sp_depth) fatal("la pila no cuadra (fallo de dashc)");
    fn_epilogue(frameless, used, nframe);
    if (debug && pass == 2) {
        dbg_funcs.v[dbg_funcs.n - 1].end = new_label();
        def_label(dbg_funcs.v[dbg_funcs.n - 1].end);
    }
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
    while (n_dash_lits && dash_lits[n_dash_lits - 1].off >= m->data_n) n_dash_lits--;   /* (sus datos ya no están) */
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
    mark_need.n = 0;
    frameless = 0;
    pass = 1;
    gen_function_pass(label, f, body);

    /* se deshace y se eligen los huecos más usados para d2-d7 */
    undo(&m);
    /* de más a menos usado: al primer registro libre durante toda su vida, desde que
       se asigna hasta su último uso (dos variables que no viven a la vez lo comparten) */
    for (i = 0; i < slot_reg.n; i++) slot_reg.v[i] = -1;
    while (!debug) {                                   /* (--debug: todas en el marco, donde las lee el depurador) */
        int best = -1, j;
        for (i = 0; i < slot_uses.n; i++)
            if (slot_reg.v[i] == -1 && slot_uses.v[i] >= MIN_USES && (best < 0 || slot_uses.v[i] > slot_uses.v[best]))
                best = i;
        if (best < 0) break;
        slot_reg.v[best] = -2;                         /* visto: si no hay registro, al marco */
        for (r = FIRST_REG; r < FIRST_REG + MAX_REGS; r++) {
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
    if (debug) frameless = 0;
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

/* ¿usa el programa teclas o clics? (las ventanas piden esos mensajes: IDCMP) */
static void find_uses_expr(Node *n)
{
    int i;
    if (!n) return;
    if (n->kind == E_CALL && !strncmp(n->name, "key_", 4)) uses_keys = 1;
    if (n->kind == E_CALL && !find_func(n->name, NULL)) {
        static const char *gad[] = {"button_", "checkbox_", "slider_", "textfield_", "listview_", "gadget_",
                                    "cycle_", "radio_", "integer_", "palette_", "number_", NULL};
        for (i = 0; gad[i]; i++)
            if (!strncmp(n->name, gad[i], strlen(gad[i]))) uses_gadgets = needs_gt = 1;
        if (!strncmp(n->name, "gt_", 3) || !strncmp(n->name, "menu_", 5)) needs_gt = 1;
        if (!strncmp(n->name, "mui_", 4)) uses_mui = 1;
        if (!strncmp(n->name, "tls_", 4) || !strncmp(n->name, "https_", 6)) uses_tls = 1;
        if (!strcmp(n->name, "gfx_ellipse_fill") || !strcmp(n->name, "gfx_circle_fill") ||
            !strncmp(n->name, "gfx_poly_", 9))
            needs_area = 1;
        /* button_create(..., "_Vale"): la tecla del gadget */
        if ((!strcmp(n->name, "button_create") || !strcmp(n->name, "checkbox_create")))
            for (i = 0; i < n->args.n; i++)
                if (n->args.v[i]->kind == E_STR && memchr(n->args.v[i]->str, '_', n->args.v[i]->len))
                    gadget_keys = uses_keys = 1;
    }
    find_uses_expr(n->a);
    find_uses_expr(n->b);
    find_uses_expr(n->c);
    for (i = 0; i < n->args.n; i++) find_uses_expr(n->args.v[i]);
}

static void find_uses(NodeList *l)
{
    int i;
    for (i = 0; i < l->n; i++) {
        Node *n = l->v[i];
        if (n->kind == S_ON && n->val == ON_KEY) uses_keys = 1;
        if (n->kind == S_ON && (n->val == ON_CLICK || n->val == ON_RIGHTCLICK)) uses_click = 1;
        if (n->kind == S_ON && n->val == ON_INACTIVE) uses_inactive = 1;
        if (n->kind == S_ON && n->val == ON_GADGET) uses_gadgets = needs_gt = 1;
        if (n->kind == S_ON && n->val == ON_MENU) needs_gt = 1;
        find_uses_expr(n->a);
        find_uses_expr(n->b);
        find_uses(&n->body);
        find_uses(&n->els);
    }
}

/* De cada ventana, su DashWinDesc (runtime/api.c), con las propiedades y los valores por defecto de ./dash */
static void gen_window_descs(void)
{
    int i, j;
    for (i = 0; i < prog->windows.n; i++) {
        WindowDef *wd = &prog->windows.v[i];
        long left = 50, top = 50, width = 0, height = 0, flags = 1 | 2 | 4 | 32, k;
        const char *title = "";
        static const char *const fl[] = {"closegadget", "dragbar", "depthgadget", "sizegadget", "borderless", "activate",
                                         "rmbtrap"};
        for (j = 0; j < wd->props.n; j++) {
            Node *v = wd->props.v[j];
            int f;
            if (!strcmp(v->name, "title")) {
                if (v->kind != E_STR) fatal_at(v->line, v->col, "title es un texto");
                title = v->str;
                continue;
            }
            if (!fold(v, &k)) fatal_at(v->line, v->col, "%s tiene que ser un valor fijo", v->name);
            if (!strcmp(v->name, "left")) left = k;
            else if (!strcmp(v->name, "top")) top = k;
            else if (!strcmp(v->name, "width")) width = k;
            else if (!strcmp(v->name, "height")) height = k;
            else {
                for (f = 0; f < 7 && strcmp(fl[f], v->name); f++)
                    ;
                if (f < 7) flags = k ? flags | 1L << f : flags & ~(1L << f);
            }
        }
        def_label(win_desc_label[i]);                  /* DashWinDesc */
        code_data_ptr(add_string(title, (int)strlen(title)));
        code_long((uint32_t)left);
        code_long((uint32_t)top);
        code_long((uint32_t)width);
        code_long((uint32_t)height);
        code_long((uint32_t)flags);
        code_long(0x200 | (uses_keys ? 0x400 : 0) | (uses_click ? 0x8 : 0) |   /* CLOSEWINDOW, RAWKEY, MOUSEBUTTONS */
                  (uses_inactive ? 0x80000 : 0) |                             /* INACTIVEWINDOW */
                  (needs_gt ? 0x174 : 0));   /* GADGETUP, GADGETDOWN, MOUSEMOVE, MENUPICK, REFRESHWINDOW */
    }
}

/* TY_NAMED (un nombre de tipo que el analizador aún no conocía) -> su struct */
static int resolve_type(int t, int line, int col)
{
    int d = 0;
    while (t >= TY_ARR) {
        t -= TY_ARR;
        d++;
    }
    if (t >= TY_NAMED) {
        int si = find_struct(type_names.v[t - TY_NAMED]), i;
        for (i = 0; si < 0 && i < prog->enums.n; i++)
            if (!strcmp(prog->enums.v[i].name, type_names.v[t - TY_NAMED])) return TY_INT + d * TY_ARR;   /* un enum es Int */
        if (si < 0) fatal_at(line, col, "el tipo %s no existe", type_names.v[t - TY_NAMED]);
        t = TY_STRUCT + si;
    }
    return t + d * TY_ARR;
}

/* el cuerpo que se resuelve (Main o una función, con sus parámetros): sus variables tapan a las funciones */
static NodeList *resolving_body;
static Func *resolving_func;
static int list_assigns(NodeList *l, const char *name);

static int is_local_name(const char *name)
{
    int i;
    for (i = 0; resolving_func && i < resolving_func->params.n; i++)
        if (!strcmp(resolving_func->params.v[i].name, name)) return 1;
    return resolving_body && list_assigns(resolving_body, name);
}

/* Una constante que no es un número fijo (un texto, un Float): su valor en cada sitio donde se usa */
static void subst_consts(Node **pe)
{
    Node *e = *pe;
    int i;
    long k;
    if (!e) return;
    if (e->kind == E_VAR) {
        for (i = 0; i < prog->globals.n; i++)
            if (!strcmp(prog->globals.v[i].name, e->name)) return;
        if (find_func(e->name, NULL) && !is_local_name(e->name)) {
            e->kind = E_FUNCREF;                       /* una función como valor */
            return;
        }
        for (i = 0; i < prog->consts.n; i++)
            if (!strcmp(prog->consts.v[i].name, e->name)) {
                Node *v = prog->consts.v[i].value;
                if (v->kind == E_FLOAT || !fold(v, &k)) {
                    subst_consts(&prog->consts.v[i].value);
                    *pe = prog->consts.v[i].value;
                }
                return;
            }
        return;
    }
    subst_consts(&e->a);
    subst_consts(&e->b);
    subst_consts(&e->c);
    for (i = 0; i < e->args.n; i++) subst_consts(&e->args.v[i]);
}

static void resolve_list(NodeList *l)
{
    int i;
    for (i = 0; i < l->n; i++) {
        Node *n = l->v[i];
        subst_consts(&n->a);
        subst_consts(&n->b);
        subst_consts(&n->c);
        for (int j = 0; j < n->args.n; j++) subst_consts(&n->args.v[j]);
        if (n->kind == S_VAR) n->type = resolve_type(n->type, n->line, n->col);
        resolve_list(&n->body);
        resolve_list(&n->els);
    }
}

/* De cada struct, su _DashType { destroy, tamaño, métodos } y su destroy: libera los textos y
   suelta los objetos de sus campos (_dash_release_child, como el de ./dash). Van en el código. */
static void gen_struct_types(void)
{
    int si, i;
    for (si = 0; si < prog->structs.n; si++) {
        Struct *st = &prog->structs.v[si];
        int destroy = -1;
        for (i = 0; i < st->fields.n; i++)
            if ((IS_STRLIKE(st->fields.v[i].type) || IS_OBJ(st->fields.v[i].type)) && !st->fields.v[i].weak)
                destroy = new_label();
        if (destroy >= 0) {
            def_label(destroy);
            destroy_begin();
            for (i = 0; i < st->fields.n; i++) {
                int ft = st->fields.v[i].type;
                if ((!IS_STRLIKE(ft) && !IS_OBJ(ft)) || st->fields.v[i].weak) continue;
                destroy_field(field_off(i), IS_STRLIKE(ft) ? "_dl_str_free" : "_dl_release_child");
            }
            destroy_end();
        }
        def_label(desc_label[si]);
        code_ptr(destroy);                             /* _DashType: destroy, size, methods */
        code_long((uint32_t)struct_bytes(st->fields.n));
        if (st->ifaces.n) {
            /* la tabla de métodos de sus interfaces: justo detrás */
            int tab = new_label(), j, k;
            code_ptr(tab);
            def_label(tab);
            for (k = 0; k < prog->nslots; k++) {
                /* el método de este slot: de una de sus interfaces, con su "Struct.metodo" */
                const char *mname = NULL;
                int fi = -1;
                for (j = 0; j < st->ifaces.n && !mname; j++) {
                    int ii = find_struct(st->ifaces.v[j]), q;
                    if (ii < 0 || !prog->structs.v[ii].iface)
                        fatal_at(st->line, st->col, "%s no es una interfaz", st->ifaces.v[j]);
                    for (q = 0; q < prog->structs.v[ii].methods.n; q++)
                        if (prog->structs.v[ii].methods.v[q].slot == k) mname = prog->structs.v[ii].methods.v[q].name;
                }
                if (mname) {
                    char full[256];
                    snprintf(full, sizeof full, "%s.%s", st->name, mname);
                    if (!find_func(full, &fi))
                        fatal_at(st->line, st->col, "%s no tiene el método %s de su interfaz", st->name, mname);
                }
                code_ptr(mname ? func_label[fi] : -1);
            }
        } else {
            code_ptr(-1);
        }
    }
}

/* ---- --debug: el texto del HUNK_DEBUG (docs/DEPURADOR_LOOP.md) ---- */

static void dbg_printf(const char *fmt, ...)
{
    char tmp[2200];
    va_list ap;
    int n;
    va_start(ap, fmt);
    n = vsnprintf(tmp, sizeof tmp, fmt, ap);
    va_end(ap);
    buf_bytes(&debug_info, tmp, (size_t)(n < (int)sizeof tmp ? n : (int)sizeof tmp - 1));
}

/* un tipo como en Dash, sin espacios: Int, String, Punto, [Int], {String:Int} */
static void dbg_type(int t)
{
    if (IS_ARR(t)) {
        dbg_printf("[");
        dbg_type(t - TY_ARR);
        dbg_printf("]");
    } else if (IS_DICT(t)) {
        dbg_printf("{");
        dbg_type(dict_types.v[t - TY_DICT].key);
        dbg_printf(":");
        dbg_type(dict_types.v[t - TY_DICT].val);
        dbg_printf("}");
    } else if (IS_STRUCT(t)) {
        dbg_printf("%s", prog->structs.v[t - TY_STRUCT].name);
    } else {
        static const char *const names[] = {"Void", "Int", "Bool", "String", "Char", "Nil", "Float", "Double", "Fixed"};
        dbg_printf("%s", t >= 0 && t <= TY_FIXED ? names[t] : "Int");
    }
}

/* Una cosa por línea: F ficheros, G globales (desplazamiento en el hunk de datos), S campos de los structs
   (desplazamiento desde el puntero al objeto), P funciones (dónde empiezan y acaban en el hunk de código), V sus
   variables y parámetros (desplazamiento sobre a5, línea donde se declaran) y L el NOP de cada línea. */
static void debug_text(Program *p)
{
    int i, j;
    debug_info.n = 0;
    dbg_printf("DASH-DEBUG 1\n");
    for (i = 0; i < src_files.n; i++) dbg_printf("F %d %s\n", i, src_files.v[i]);
    for (i = 0; i < p->globals.n; i++) {
        dbg_printf("G %s ", p->globals.v[i].name);
        dbg_type(global_type[i]);
        dbg_printf(" %d %d\n", i * 4, p->globals.v[i].file);
    }
    for (i = 0; i < p->structs.n; i++) {
        Struct *st = &p->structs.v[i];
        if (st->iface) continue;
        for (j = 0; j < st->fields.n; j++) {
            dbg_printf("S %s %s ", st->name, st->fields.v[j].name);
            dbg_type(resolve_type(st->fields.v[j].type, st->fields.v[j].line, st->fields.v[j].col));
            dbg_printf(" %d\n", 4 * j);
        }
    }
    for (i = 0; i < dbg_funcs.n; i++) {
        DbgFunc *d = &dbg_funcs.v[i];
        dbg_printf("P %d %s %ld %ld %d %d\n", i, d->name, labels.v[d->start], labels.v[d->end], d->file, d->line);
    }
    for (i = 0; i < dbg_vars.n; i++) {
        DbgVar *d = &dbg_vars.v[i];
        dbg_printf("V %d %s ", d->func, d->name);
        dbg_type(d->type);
        dbg_printf(" %d %d\n", d->off, d->line);
    }
    for (i = 0; i < dbg_lines.n; i++)
        dbg_printf("L %ld %d %d\n", labels.v[dbg_lines.v[i].label], dbg_lines.v[i].file, dbg_lines.v[i].line);
}

void gen_program(Program *p, Obj *o)
{
    int i, main_label, again, files_label;
    prog = p;
    obj = o;
    {
        const char *e = getenv("DASH_TEST_AUTOCLOSE");
        autoclose = e ? atoi(e) : 0;
        if (autoclose < 0) autoclose = 0;
        e = getenv("DASH_PRINT_FLUSH");
        print_flush = e && *e && strcmp(e, "0");
    }

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

    /* los nombres de tipos, a sus structs (también lo que guarda cada diccionario) */
    for (i = 0; i < dict_types.n; i++) dict_types.v[i].val = resolve_type(dict_types.v[i].val, 0, 0);
    desc_label = xmalloc(sizeof(int) * (p->structs.n + 1));
    for (i = 0; i < p->structs.n; i++) {
        int j;
        Struct *st = &p->structs.v[i];
        for (j = 0; j < i; j++)
            if (!strcmp(p->structs.v[j].name, st->name)) fatal_at(st->line, st->col, "el struct %s ya existe", st->name);
        for (j = 0; j < st->fields.n; j++)
            st->fields.v[j].type = resolve_type(st->fields.v[j].type, st->fields.v[j].line, st->fields.v[j].col);
        desc_label[i] = new_label();
    }
    for (i = 0; i < p->globals.n; i++) {
        p->globals.v[i].type = resolve_type(p->globals.v[i].type, p->globals.v[i].line, p->globals.v[i].col);
        subst_consts(&p->globals.v[i].init);
    }
    for (i = 0; i < p->funcs.n; i++) {
        Func *f = &p->funcs.v[i];
        int j;
        for (j = 0; j < f->params.n; j++) f->params.v[j].type = resolve_type(f->params.v[j].type, f->line, f->col);
        f->ret = resolve_type(f->ret, f->line, f->col);
        resolving_func = f;
        resolving_body = &f->body;
        resolve_list(&f->body);
    }
    resolving_func = NULL;
    resolving_body = &p->main;
    resolve_list(&p->main);
    resolving_body = NULL;

    /* globales: sus valores iniciales van en el hunk de datos (los textos, al empezar Main) */
    global_type = xmalloc(sizeof(int) * (p->globals.n + 1));
    for (i = 0; i < p->globals.n; i++) {
        long v = 0;
        Global *g = &p->globals.v[i];
        global_type[i] = g->type;
        /* un número fijo va en los datos; lo demás, al empezar Main (gen_global_inits) */
        if (!IS_STRLIKE(g->type) && !IS_OBJ(g->type)) fold(g->init, &v);
        data_word(v);                                  /* (en global_off(i)) */
    }

    /* las ventanas: su variable, tras las globales */
    win_off = xmalloc(sizeof(long) * (p->windows.n + 1));
    win_desc_label = xmalloc(sizeof(int) * (p->windows.n + 1));
    for (i = 0; i < p->windows.n; i++) {
        win_off[i] = data_word(0);
        win_desc_label[i] = new_label();
    }
    find_uses(&p->main);
    for (i = 0; i < p->funcs.n; i++) find_uses(&p->funcs.v[i].body);

    /* lo que devuelve cada función */
    fret_state = xmalloc(sizeof(int) * (p->funcs.n + 1));
    memset(fret_state, 0, sizeof(int) * (p->funcs.n + 1));
    infer_params(p);
    for (i = 0; i < p->funcs.n; i++) func_ret(i);
    /* los campos a los que algo asigna (préstamos), con los tipos de las variables ya sabidos */
    collect_set = 1;
    tenv_on = 1;
    tenv_base = tenv.n;
    lent_begin();
    {
        int r = TY_VOID;
        collect_fn = -1;
        walk_types(&p->main, &r);
    }
    tenv.n = tenv_base;
    for (i = 0; i < p->funcs.n; i++) {
        Func *f = &p->funcs.v[i];
        int j, r = TY_VOID;
        if (f->native) continue;
        collect_fn = i;
        cur_file_g = f->file;
        for (j = 0; j < f->params.n; j++) {
            TBind b;
            b.name = f->params.v[j].name;
            b.type = f->params.v[j].type;
            VEC_PUSH(tenv, b);
        }
        walk_types(&f->body, &r);
        tenv.n = tenv_base;
    }
    cur_file_g = 0;
    tenv_on = 0;
    collect_set = 0;
    lent_end();
    if (profile) prof_label = new_label();

    /* arranque: _dash_start (rt_math.s) guarda registros, abre lo necesario, ejecuta Main y sale */
    main_label = new_label();
    /* (a0 y d0 traen la línea de órdenes: no se tocan) */
    files_label = new_label();
    /* @catalog (su nombre, versión e idioma propio) y @workbench_output, en las variables del runtime (antes
       de los globales, que pueden llamar a tr) */
    if (p->catalog) {
        set_rt_var("__dash_catalog_name", p->catalog, 0);
        set_rt_var("__dash_catalog_version", NULL, p->catalog_version);
        if (p->catalog_lang) set_rt_var("__dash_catalog_builtin", p->catalog_lang, 0);
    }
    if (p->wb_output) set_rt_var("__dash_stdiowin", p->wb_output, 0);
    if (p->version) set_rt_var("__dash_version", p->version, 0);   /* program_version() */
    if (autoclose) set_rt_var("__dash_ac_secs", NULL, autoclose);
    {
        /* los literales de los campos como textos de Dash (dash_lit): su cabecera, antes que nada */
        lit_init_label = new_label();
        jsr_label(lit_init_label);
    }
    {
        /* la pila que pide (16 KB, como ./dash; 32 KB con MUI, 64 KB con AmiSSL; más con @stack): _dash_start
           cambia a una así si la del shell es menor */
        long stack = uses_tls ? 65536 : uses_mui ? 32768 : 16384;
        if (p->stack_min > stack) stack = p->stack_min;
        start_arg_long((uint32_t)stack);               /* la pila */
    }
    {
        int k;
        for (k = 0; k < 2; k++) start_arg_label(k ? main_label : files_label);   /* los ficheros (para los errores), main */
    }
    jmp_sym("__dash_start");

    /* los métodos de las interfaces van en las tablas de métodos: se generan aunque nadie los llame directo */
    for (i = 0; i < p->structs.n; i++) {
        int j, fi;
        Struct *st = &p->structs.v[i];
        for (j = 0; j < p->funcs.n; j++) {
            size_t len = strlen(st->name);
            if (st->ifaces.n && !strncmp(p->funcs.v[j].name, st->name, len) && p->funcs.v[j].name[len] == '.' &&
                !needed[j]) {
                fi = j;
                needed[fi] = 1;
            }
        }
    }
    /* las @export van siempre: las llama el C de @link */
    for (i = 0; i < p->funcs.n; i++)
        if (p->funcs.v[i].exported && !needed[i]) needed[i] = 1;
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
        if (!needed[i] && !p->funcs.v[i].native) {
            Mark m = mark();
            int *saved = xmalloc(sizeof(int) * (p->funcs.n + 1));
            memcpy(saved, needed, sizeof(int) * p->funcs.n);
            gen_one(i, func_label[i], &p->funcs.v[i], &p->funcs.v[i].body);
            undo(&m);
            labels.v[func_label[i]] = -1;
            memcpy(needed, saved, sizeof(int) * p->funcs.n);
            free(saved);
        }
    gen_struct_types();
    gen_window_descs();
    {
        int i;
        def_label(lit_init_label);
        lit_init_begin();
        for (i = 0; i < n_dash_lits; i++) lit_init_one(dash_lits[i].off);
        lit_init_end();
    }
    if (p->version) {
        /* @version: "$VER: versión (d.m.aaaa)", como ./dash (lo lee la orden Version) */
        char ver[512];
        time_t now = time(NULL);
        struct tm *tm = localtime(&now);
        snprintf(ver, sizeof ver, "$VER: %s (%d.%d.%d)", p->version, tm->tm_mday, tm->tm_mon + 1, tm->tm_year + 1900);
        add_string(ver, (int)strlen(ver));
    }
    /* los nombres de los ficheros (_dash_srcfiles de ./dash), terminados en 0 */
    def_label(files_label);
    for (i = 0; i < src_files.n && i < 63; i++) code_data_ptr(add_string(src_files.v[i], (int)strlen(src_files.v[i])));
    code_long(0);
    if (profile) {
        /* --perfil: el nombre de cada función (0 es Main) */
        def_label(prof_label);
        code_data_ptr(add_string("Main", 4));
        for (i = 0; i < p->funcs.n; i++) code_data_ptr(add_string(p->funcs.v[i].name, (int)strlen(p->funcs.v[i].name)));
    }
    resolve_fixups();
    if (debug) debug_text(p);
    /* las @export, con su nombre de C, para hunk.c */
    for (i = 0; i < p->funcs.n; i++)
        if (p->funcs.v[i].exported) {
            Export e;
            e.name = c_symbol(p->funcs.v[i].name);
            e.off = (uint32_t)labels.v[func_label[i]];
            VEC_PUSH(obj->exports, e);
        }
}

/* ---- dashc --cabecera: los structs del programa para el C de @link ---- */

/* el tipo de C de un campo, tal como lo guarda dashc (4 bytes cada uno) */
static void c_field_type(FILE *f, int t)
{
    if (IS_STRUCT(t)) fprintf(f, "struct _Dash_%s *", prog->structs.v[t - TY_STRUCT].name);
    else if (IS_ARR(t)) fprintf(f, "DashArray *");
    else if (IS_DICT(t)) fprintf(f, "DashDict *");
    else if (t == TY_STR) fprintf(f, "STRPTR ");
    else if (t == TY_DOUBLE) fprintf(f, "STRPTR /* Double: su caja */ ");
    else if (t == TY_FLOAT) fprintf(f, "ULONG /* Float: sus bits */ ");
    else if (t == TY_BOOL) fprintf(f, "LONG /* Bool: 0 o 1 */ ");
    else fprintf(f, "LONG ");
}

void write_c_header(Program *p, FILE *f)
{
    int i, j;
    prog = p;
    fprintf(f, "/* Los structs de Dash del programa tal como los coloca dashc (dashc --cabecera), y lo del runtime que\n"
               "   puede usar el C de @link. El puntero a un objeto apunta a su primer campo; cada campo, 4 bytes. Un\n"
               "   texto que una función de C devuelve a Dash (@extern -> String) lo copia dashc: puede ser suyo. */\n"
               "#ifndef DASH_TIPOS_H\n#define DASH_TIPOS_H\n#include <exec/types.h>\n\n"
               "typedef struct DashArray DashArray;\ntypedef struct DashDict DashDict;\n\n"
               "/* textos: una copia de Dash (se libera con dl_str_free), su largo */\n"
               "STRPTR dl_str_dup(STRPTR s);\nvoid dl_str_free(STRPTR s);\nLONG dl_str_len(STRPTR s);\n"
               "/* objetos (structs, listas, diccionarios): sostenerlos y soltarlos */\n"
               "void dl_retain(void *o);\nvoid dl_release(void *o);\n"
               "/* listas: largo y elemento i (un número, o el puntero de un texto u objeto) */\n"
               "LONG dl_arr_length(DashArray *a);\nLONG dl_arr_get(DashArray *a, LONG i);\n"
               "/* diccionarios de texto: largo y valor */\n"
               "LONG dl_dict_length(DashDict *d);\nLONG dl_dict_get(DashDict *d, STRPTR k);\n"
               "/* un temporal de Dash (se libera solo); olvidar el largo guardado de un texto de C que se libera */\n"
               "STRPTR dl_str_temp(STRPTR s);\nvoid dl_str_forget(STRPTR s);\n"
               "/* los builtins, como db_nombre(LONG...) (db_time_ms()...) */\n\n"
               "/* los nombres del C de ./dash (Dash 1.x), para el C que venía de @native o @c */\n"
               "#define _dash_str_dup(s, temp) ((temp) ? dl_str_temp((STRPTR)(s)) : dl_str_dup((STRPTR)(s)))\n"
               "#define _dash_str_len(s) dl_str_len((STRPTR)(s))\n#define _dash_str_forget(s) dl_str_forget((STRPTR)(s))\n"
               "#define _dash_retain(o) dl_retain((void *)(o))\n#define _dash_release(o) dl_release((void *)(o))\n"
               "#define DashArray_length(a) dl_arr_length((DashArray *)(a))\n"
               "#define DashArray_get(a, i) dl_arr_get((DashArray *)(a), (i))\n"
               "#define _dash_time_ms() db_time_ms()\nLONG db_time_ms(void);\n\n");
    fprintf(f, "typedef DashArray DashArrayLong;\n\n/* las constantes enteras del programa */\n");
    for (i = 0; i < p->consts.n; i++) {
        long k;
        if (fold(p->consts.v[i].value, &k)) fprintf(f, "#define %s %ldL\n", p->consts.v[i].name, k);
    }
    fprintf(f, "\n");
    for (i = 0; i < p->structs.n; i++)
        if (!p->structs.v[i].iface) fprintf(f, "struct _Dash_%s;\n", p->structs.v[i].name);
    for (i = 0; i < p->structs.n; i++) {
        Struct *st = &p->structs.v[i];
        if (st->iface) continue;
        fprintf(f, "\ntypedef struct _Dash_%s {\n", st->name);
        for (j = 0; j < st->fields.n; j++) {
            Field *fd = &st->fields.v[j];
            fprintf(f, "    ");
            c_field_type(f, resolve_type(fd->type, fd->line, fd->col));
            fprintf(f, "%s;%s\n", fd->name, fd->weak ? "   /* weak */" : "");
        }
        if (!st->fields.n) fprintf(f, "    LONG _vacio;\n");
        fprintf(f, "} _Dash_%s;\n", st->name);
    }
    /* las funciones @export: las que el C llama por su nombre */
    for (i = 0; i < p->funcs.n; i++) {
        Func *fn = &p->funcs.v[i];
        if (!fn->exported) continue;
        fprintf(f, "%s", i ? "" : "\n");
        if (fn->ret == TY_VOID) fprintf(f, "\nvoid ");
        else {
            fprintf(f, "\n");
            c_field_type(f, resolve_type(fn->ret, fn->line, fn->col));
        }
        fprintf(f, "%s(", c_symbol(fn->name) + 1);
        for (j = 0; j < fn->params.n; j++) {
            fprintf(f, "%s", j ? ", " : "");
            c_field_type(f, resolve_type(fn->params.v[j].type, fn->line, fn->col));
            fprintf(f, "%s", fn->params.v[j].name);
        }
        fprintf(f, "%s);", fn->params.n ? "" : "void");
    }
    fprintf(f, "\n\n#endif\n");
}
