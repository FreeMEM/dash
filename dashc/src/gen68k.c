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

/* códigos de condición del 68000 */
enum { CC_T = 0, CC_F, CC_HI, CC_LS, CC_CC, CC_CS, CC_NE, CC_EQ, CC_VC, CC_VS,
       CC_PL, CC_MI, CC_GE, CC_LT, CC_GT, CC_LE };

#define MAX_REGS 6   /* d2-d7 */
#define MIN_USES 3   /* menos usos no pagan guardar y recuperar el registro */

static Program *prog;
static Obj *obj;
int memcheck;

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

static void resolve_fixups(void)
{
    int i;
    relax_branches();
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
            if (d < -32768 || d > 32767) fatal("salto de más de 32 KB (aún no admitido)");
            put_word(obj->code.p + f->at, (int)d);
        }
    }
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
typedef struct { Node *n; int slot, need_reg; } Repl;
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
static int uses_keys, uses_click;   /* IDCMP de las ventanas */
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

/* ¿los códigos de condición ya comparan v con 0 para la condición cc? */
static int flags_for(Var *v, int cc)
{
    return v->kind == V_REG && flags_at == obj->code.n && flags_reg == v->reg &&
           (flags_full || cc == CC_EQ || cc == CC_NE);
}

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
    lc.entry = 0;
    lc.owned = 0;
    VEC_PUSH(locals, lc);
    use_slot(lc.slot);
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

/* move.l #texto (o #n),var: una variable del runtime, al arrancar */
static void set_rt_var(const char *sym, const char *str, long n)
{
    w(0x23FC);
    if (str) {
        add_reloc((uint32_t)obj->code.n, HK_DATA, NULL);
        l(add_string(str, (int)strlen(str)));
    } else
        l((uint32_t)n);
    add_reloc((uint32_t)obj->code.n, -1, sym);
    l(0);
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

static void load_str_lit(const char *str, int len)
{
    w(0x203C);                                         /* move.l #texto,d0 */
    add_reloc((uint32_t)obj->code.n, HK_DATA, NULL);
    l(add_string(str, len));
    d0_loaded = (uint32_t)obj->code.n;
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

static void walk_types(NodeList *l, int *ret)
{
    int i;
    for (i = 0; i < l->n; i++) {
        Node *st = l->v[i];
        TBind b;
        b.name = st->name;
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
        push_d0();
        rt_call("_dl_str_from_int", 1, 1);
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
        tst_d0();
        w(0x6708);                                     /* beq.s +8 */
        load_str_lit("true", 4);
        w(0x6006);                                     /* bra.s +6 */
        load_str_lit("false", 5);
        d0_loaded = (uint32_t)-1;
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
    w(0x4840);                                         /* swap d0 */
    w(0x4240);                                         /* clr.w d0: << 16 */
    d0_loaded = (uint32_t)-1;
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
    w(0x4FEF); w(-4 * n);                              /* lea -4n(sp),sp */
    sp_depth += 4 * n;
    for (i = 0; i < n; i++) {
        if (str && str[i] == 2) float_value(a[i]);
        else if (str && str[i] == 3) dbl_value(a[i]);
        else if (str && str[i] == 4) fix_value(a[i]);
        else if (str && str[i]) str_value(a[i]);
        else value(a[i]);
        if (i) { w(0x2F40); w(4 * i); }                /* move.l d0,4i(sp) */
        else w(0x2E80);                                /* move.l d0,(sp) */
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
    w(0x4857);                                         /* pea (sp): la dirección de los trozos */
    sp_depth += 4;
    w(0x4878); w(np);                                  /* pea n.w */
    sp_depth += 4;
    rt_call("_dl_str_join", 2, 1);
    pop_args(np);
}

/* a + b con algún texto: DashString_concat, con un número pasado a texto */
static void gen_concat(Node *n)
{
    Node *a[2];
    static const char str[2] = {1, 1};
    a[0] = n->a;
    a[1] = n->b;
    args_to_stack(a, 2, str);
    rt_call("_dl_str_concat", 2, 1);
}

/* s[i]: el byte, con signo (char en el C de ./dash) */
static int gen_str_index(Node *n)
{
    Node *a[2];
    a[0] = n->a;
    a[1] = n->b;
    args_to_stack(a, 2, NULL);
    rt_call("_dl_str_code", 2, 0);
    w(0x4880); w(0x48C0);                              /* ext.w d0; ext.l d0 */
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
    if (!strcmp(n->name, "length") && (t == TY_STR || IS_ARR(t) || IS_DICT(t))) {
        args_to_stack(&n->a, 1, NULL);
        rt_call(t == TY_STR ? "_dl_str_len" : IS_DICT(t) ? "_dl_dict_length" : "_dl_arr_length", 1, 0);
        return TY_INT;
    }
    fatal_node(n, "dashc (prueba): .%s aún no está", n->name);
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
        w(0x7000);                                     /* moveq #0,d0 */
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
        uint32_t off;
        if (obj->data.n & 3) buf_word(&obj->data, 0);
        off = (uint32_t)obj->data.n;
        for (i = 0; i < np; i++) {
            fold(n->args.v[i], &k);
            buf_long(&obj->data, (uint32_t)k);
        }
        w(0x4879);                                     /* pea datos */
        add_reloc((uint32_t)obj->code.n, HK_DATA, NULL);
        l(off);
        sp_depth += 4;
        w(0x4878); w(np);                              /* pea n.w */
        sp_depth += 4;
        rt_call(fresh ? "_dl_arr_from_new" : "_dl_arr_from", 2, !fresh);
    } else {
        char *conv = xmalloc(np + 1);
        memset(conv, et == TY_DOUBLE ? 3 : et == TY_FLOAT ? 2 : et == TY_FIXED ? 4 : 0, np);
        args_to_stack(n->args.v, np, conv);
        free(conv);
        w(0x4857);                                     /* pea (sp) */
        sp_depth += 4;
        w(0x4878); w(np);                              /* pea n.w */
        sp_depth += 4;
        rt_call(fresh ? "_dl_arr_from_new" : "_dl_arr_from", 2, !fresh);
        pop_args(np);
    }
    if (kind) {
        w(0x4878); w(kind);                            /* pea kind.w */
        sp_depth += 4;
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
    tst_d0();
    if (cur_file) {
        w(0x6612);                                     /* bne.s +18 */
        w(0x4879); l((uint32_t)cur_file << 16 | (cur_line & 0xFFFF));   /* pea fichero << 16 | línea */
    } else {
        w(0x6610);                                     /* bne.s +16 */
        w(0x4878); w(cur_line & 0x7FFF);               /* pea línea.w (fichero 0) */
    }
    w(0x4879);                                         /* pea "campo de nil" */
    add_reloc((uint32_t)obj->code.n, HK_DATA, NULL);
    l(add_string("campo de nil", 12));
    jsr_sym("_dl_fail_at");                            /* no vuelve */
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
    w(0x2040);                                         /* movea.l d0,a0 */
    *off = 4 * f;
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
    w(0x2028); w(off);                                 /* move.l off(a0),d0 */
    d0_loaded = (uint32_t)obj->code.n;
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
        w(0x4868); w(off);                             /* pea off(a0) */
        sp_depth += 4;
        rt_call(!IS_STRLIKE(ft) ? "_dl_obj_set" : is_tmp_expr(v) ? "_dl_str_set" : "_dl_str_set_copy", 2, 0);
    } else {
        w(0x215F); w(off);                             /* move.l (sp)+,off(a0) */
        sp_depth -= 4;
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
    {
        Fixup f;
        w(0x4879);                                     /* pea descriptor */
        f.at = (uint32_t)obj->code.n;
        f.label = desc_label[si];
        f.abs = 1;
        f.size = 2;
        VEC_PUSH(fixups, f);
        add_reloc(f.at, HK_CODE, NULL);
        l(0);
        sp_depth += 4;
    }
    w(0x4878); w(4 * nf);                              /* pea tamaño.w */
    sp_depth += 4;
    rt_call(fresh ? "_dl_rc_new_obj" : "_dl_rc_alloc_obj", 2, !fresh);
    w(0x2440);                                         /* movea.l d0,a2 (C no toca a2) */
    for (i = 0; i < nf; i++) {
        int ft = st->fields.v[i].type, off = 4 * i;
        if (IS_STRLIKE(ft)) {
            w(0x42AA); w(off);                         /* clr.l off(a2) */
            w(0x2F2F); w(4 * i);                       /* move.l v(sp),-(sp) */
            sp_depth += 4;
            w(0x486A); w(off);                         /* pea off(a2) */
            sp_depth += 4;
            /* un texto que no es un temporal nuevo (una variable, un parámetro) se copia */
            rt_call(is_tmp_expr(vals[i]) ? "_dl_str_set" : "_dl_str_set_copy", 2, 0);
        } else {
            w(0x256F); w(4 * i); w(off);               /* move.l v(sp),off(a2) */
            if (IS_OBJ(ft) && !st->fields.v[i].weak) {
                w(0x2F2A); w(off);                     /* move.l off(a2),-(sp) */
                sp_depth += 4;
                rt_call("_dl_retain", 1, 0);
            }
        }
    }
    w(0x200A);                                         /* move.l a2,d0 */
    pop_args(nf);
    free(vals);
    return TY_STRUCT + si;
}

/* ---- préstamos: un argumento que la función llamada podría liberar mientras lo usa ----
   (un campo, una global o un elemento de lista: la función puede cambiarlo). Un texto va como
   copia temporal y un objeto con una referencia hasta que se sueltan los temporales de quien
   llama (_dash_obj_lend). Un campo que nada en el programa cambia va tal cual (dashweb D22). */
static struct { char **v; int n, cap; } set_fields;   /* campos a los que algo asigna */
static int lookup_global(const char *name);

static void find_set_fields(NodeList *l)
{
    int i, j;
    for (i = 0; i < l->n; i++) {
        Node *n = l->v[i];
        if (n->kind == S_STORE && n->b->kind == E_FIELD) {
            for (j = 0; j < set_fields.n && strcmp(set_fields.v[j], n->b->name); j++)
                ;
            if (j == set_fields.n) VEC_PUSH(set_fields, n->b->name);
        }
        find_set_fields(&n->body);
        find_set_fields(&n->els);
    }
}

static int field_is_set(const char *name)
{
    int j;
    for (j = 0; j < set_fields.n; j++)
        if (!strcmp(set_fields.v[j], name)) return 1;
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
    if (a->kind == E_FIELD && IS_STRUCT(expr_type(a->a)) && !field_is_set(a->name)) return;
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
    w(0x2040);                                         /* movea.l d0,a0 */
    w(0x2068); w(-4);                                  /* movea.l -4(a0),a0: su tipo */
    w(0x2068); w(8);                                   /* movea.l 8(a0),a0: su tabla de métodos */
    w(0x2068); w(4 * m->slot);                         /* movea.l slot(a0),a0 */
    w(0x4E90);                                         /* jsr (a0) */
    pop_args(n->args.n + 1);
    d0_loaded = (uint32_t)-1;
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

/* a[i] de una lista */
static int gen_arr_index(Node *n)
{
    Node *a[2];
    int t = expr_type(n->a);
    a[0] = n->a;
    a[1] = n->b;
    args_to_stack(a, 2, NULL);
    rt_call("_dl_arr_get", 2, 0);
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
            w(0x4FEF); w(-4 * (na + 1));               /* lea -4n(sp),sp */
            sp_depth += 4 * (na + 1);
            for (i = 0; i <= na; i++) {
                if (i == na) elem_value(a[i], et);
                else value(a[i]);
                if (i == na) str_kept(a[i]);
                if (i) { w(0x2F40); w(4 * i); }
                else w(0x2E80);
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
    fatal_node(n, "dashc (prueba): .%s aún no está", n->name);
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
        w(0x7000);                                     /* moveq #0,d0 */
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
    w(0x486F); w(4 * np);                              /* pea valores(sp) */
    sp_depth += 4;
    w(0x486F); w(4);                                   /* pea claves(sp): justo encima */
    sp_depth += 4;
    w(0x4878); w(np);                                  /* pea n.w */
    sp_depth += 4;
    w(0x4878); w(kind);                                /* pea kind.w */
    sp_depth += 4;
    rt_call(ikeys ? "_dl_dict_fromi" : "_dl_dict_from", 4, 1);
    pop_args(2 * np);
    free(keys);
    free(vals);
    return t;
}

static int dict_ikeys(int t) { return dict_types.v[t - TY_DICT].key == TY_INT; }

/* d[k] */
static int gen_dict_get(Node *n)
{
    Node *a[2];
    int t = expr_type(n->a);
    a[0] = n->a;
    a[1] = n->b;
    args_to_stack(a, 2, NULL);
    rt_call(dict_ikeys(t) ? "_dl_dict_geti" : "_dl_dict_get", 2, 0);
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
    w(0x4FEF); w(-12);                                 /* lea -12(sp),sp */
    sp_depth += 12;
    for (i = 0; i < 3; i++) {
        if (i == 2) elem_value(a[i], vt);
        else value(a[i]);
        if (i == 2 && kind == 2) str_kept(v);
        if (i) { w(0x2F40); w(4 * i); }
        else w(0x2E80);
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
    a[0] = target->a;
    a[1] = target->b;
    a[2] = v;
    w(0x4FEF); w(-12);                                 /* lea -12(sp),sp */
    sp_depth += 12;
    for (i = 0; i < 3; i++) {
        if (i == 2) elem_value(a[i], et);
        else value(a[i]);
        if (i == 2 && kind == 2) str_kept(v);
        if (i) { w(0x2F40); w(4 * i); }
        else w(0x2E80);
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
        op_ea(0x2F00, &v);                             /* move.l v,-(sp) */
        sp_depth += 4;
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

/* al empezar cada vuelta: fuera los temporales de la anterior */
static void mark_release(MarkScope *m)
{
    if (!m->on) return;
    w(0x2F2F); w(sp_depth - m->sp);                    /* move.l marca(sp),-(sp) */
    sp_depth += 4;
    rt_call("_dl_tmp_release", 1, 0);
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
    w(0x6300 | (load + 10));                           /* bls.s rápido (sin signo: un negativo es enorme) */
    load_imm(1, k);
    jsr_sym(op == P_SLASH ? "__dash_divk" : "__dash_modk");   /* sin volver a probar el divu.w */
    w(0x4A80);                                         /* tst.l d0, como deja el swap del otro camino */
    w(op == P_SLASH ? 0x600A : 0x6008);                /* bra.s fin */
    w(0x80FC); w((int)k);                              /* rápido: divu.w #k,d0, resto:cociente */
    if (op == P_SLASH) { w(0x4840); w(0x4240); w(0x4840); }   /* swap; clr.w; swap: el cociente */
    else { w(0x4240); w(0x4840); }                     /* clr.w; swap: el resto */
    d0_loaded = (uint32_t)obj->code.n;                 /* los códigos dicen cómo es d0 */
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
    w(0x600A);                                         /* bra.s fin */
    w(0x4840);                                         /* lento_swap: swap d0 */
    jsr_sym(op == P_SLASH ? "__dash_div" : "__dash_mod");   /* lento */
    w(0x4A80);                                         /* tst.l d0 */
    d0_loaded = (uint32_t)obj->code.n;
}

/* d0 = d0 * d1: muls.w si los dos caben en 16 bits con signo; si no, el runtime */
static void mul_d1(void)
{
    w(0x3040); w(0xB088); w(0x6606);                   /* movea.w d0,a0; cmp.l a0,d0; bne.s lento */
    w(0x3041); w(0xB288); w(0x670A);                   /* movea.w d1,a0; cmp.l a0,d1; beq.s rápido */
    jsr_sym("__dash_mul");                             /* lento */
    w(0x4A80);                                         /* tst.l d0 */
    w(0x6002);                                         /* bra.s fin */
    w(0xC1C1);                                         /* rápido: muls.w d1,d0 */
    d0_loaded = (uint32_t)obj->code.n;
}

/* d0 = d0 * d0 */
static void square_d0(void)
{
    w(0x3040); w(0xB088); w(0x670C);                   /* movea.w d0,a0; cmp.l a0,d0; beq.s rápido */
    w(0x2200);                                         /* move.l d0,d1 */
    jsr_sym("__dash_mul");
    w(0x4A80);                                         /* tst.l d0 */
    w(0x6002);                                         /* bra.s fin */
    w(0xC1C0);                                         /* rápido: muls.w d0,d0 */
    d0_loaded = (uint32_t)obj->code.n;
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
        int x = op == P_SLASH ? 6 : 4, r = 1;
        value(n->a);
        if (simple(n->b, &v)) {
            if (v.kind == V_REG) r = v.reg;            /* el divisor ya está en un registro */
            else load_var(1, &v);
        } else {
            push_d0();
            value(n->b);
            w(0x2200);                                 /* move.l d0,d1 */
            pop_d0();
        }
        if (!var_range(n->b, &blo, &bhi)) blo = -1, bhi = INT32_MAX;
        if (blo >= 1 && bhi <= 0xFFFF) {
            w(0x80C0 | r);                             /* divu.w dr,d0 */
            if (op == P_SLASH) { w(0x4840); w(0x4240); w(0x4840); }
            else { w(0x4240); w(0x4840); }
            d0_loaded = (uint32_t)obj->code.n;
            return 1;
        }
        w(0xB0BC | r << 9); l(0xFFFF);                 /* cmp.l #$FFFF,dr */
        if (blo >= 1) {
            w(0x6200 | (4 + x));                       /* bhi.s lento; el divisor no es 0 */
        } else {
            w(0x6200 | (8 + x));                       /* bhi.s lento (también los negativos) */
            w(0x4A40 | r);                             /* tst.w dr */
            w(0x6700 | (4 + x));                       /* beq.s lento */
        }
        w(0x80C0 | r);                                 /* divu.w dr,d0 */
        if (op == P_SLASH) { w(0x4840); w(0x4240); w(0x4840); }
        else { w(0x4240); w(0x4840); }
        w(r == 1 ? 0x6008 : 0x600A);                   /* bra.s fin */
        if (r != 1) w(0x2200 | r);                     /* lento: move.l dr,d1 */
        jsr_sym(op == P_SLASH ? "__dash_div" : "__dash_mod");
        w(0x4A80);                                     /* tst.l d0: así los dos caminos dejan los códigos */
        d0_loaded = (uint32_t)obj->code.n;
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
        /* <, <=, >, >=: 2 tiene que dar falso */
        w(0x0C80); l(2);                               /* cmpi.l #2,d0 */
        {
            int no = new_label(), done = new_label();
            branch(CC_EQ, no);
            w(0x4A80);                                 /* tst.l d0 */
            branch(CC_T, done);
            def_label(no);
            /* d0 = 2: comparado con 0 da "mayor", así que < y <= quedan falsos; > y >= se fuerzan con -1
               (menor) */
            if (n->op == P_GT || n->op == P_GE) w(0x70FF);   /* moveq #-1,d0 */
            w(0x4A80);                                 /* tst.l d0 */
            def_label(done);
        }
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
        fatal_node(n, "dashc (prueba): el builtin %s aún no está (ventanas y gráficos, Double...)", n->name);
    np = builtin_info[b].nparams;
    if (n->args.n > np) fatal_node(n, "%s pide %d argumentos y se le dan %d", n->name, np, n->args.n);
    if (np) {
        w(0x4FEF); w(-4 * np);                         /* lea -4n(sp),sp */
        sp_depth += 4 * np;
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
                w(0x7000);                             /* moveq #0,d0: el que falta */
            }
            if (i) { w(0x2F40); w(4 * i); }            /* move.l d0,4i(sp) */
            else w(0x2E80);                            /* move.l d0,(sp) */
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

static int gen_builtin(Node *n)
{
    int i, b;
    if (!strcmp(n->name, "bench_sink")) {
        /* guarda el valor donde no se pueda quitar: un move.l, como el volatile de bench_lib.dash */
        Var v;
        Var src;
        if (n->args.n != 1) fatal_node(n, "bench_sink pide 1 argumento");
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
            if (a->kind != E_STR) fatal_node(a, "dashc (prueba): aquí va un texto literal");
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
                op_ea(0x2F00, &t);                     /* move.l p,-(sp) */
                sp_depth += 4;
                rt_call(IS_STRLIKE(b->type) ? "_dl_str_dup" : "_dl_retain_r", 1, 0);
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
        w(0x2040);                                     /* movea.l d0,a0 */
        w(0x4E90);                                     /* jsr (a0) */
        pop_args(n->args.n);
        d0_loaded = (uint32_t)-1;
        return TY_INT;
    }
    if (!f) return gen_builtin(n);
    if (n->args.n != f->params.n)
        fatal_node(n, "%s pide %d argumentos y se le dan %d", n->name, f->params.n, n->args.n);
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
        return TY_INT;
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
            Fixup f;
            load_imm(0, wm);
            push_d0();
            w(0x4879);                                 /* pea descriptor */
            f.at = (uint32_t)obj->code.n;
            f.label = win_desc_label[wi];
            f.abs = 1;
            f.size = 2;
            VEC_PUSH(fixups, f);
            add_reloc(f.at, HK_CODE, NULL);
            l(0);
            sp_depth += 4;
            w(0x2F39);                                 /* move.l ventana,-(sp) */
            add_reloc((uint32_t)obj->code.n, HK_DATA, NULL);
            l((uint32_t)win_off[wi]);
            sp_depth += 4;
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
            tst_d0();
            w(0x6A02);                                 /* bpl.s +2 */
            w(0x4480);                                 /* neg.l d0 */
            return TY_INT;
        }
        fatal_node(n, "dashc (prueba): .%s() aún no está", n->name);
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
                Fixup f;
                w(0x203C);                             /* move.l #función,d0 */
                f.at = (uint32_t)obj->code.n;
                f.label = func_label[idx];
                f.abs = 1;
                f.size = 2;
                VEC_PUSH(fixups, f);
                add_reloc(f.at, HK_CODE, NULL);
                l(0);
                if (!needed[idx]) needed[idx] = 1;
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
            w(0x0A80); l(0x80000000);                  /* eori.l #$80000000,d0: el signo */
            return TY_FLOAT;
        }
        value(n->a);
        w(0x4480);                                     /* neg.l d0 */
        return expr_type(n->a) == TY_FIXED ? TY_FIXED : TY_INT;
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
    f.size = 2;
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
        int pass_n, neg = new_label();
        def_label(test);
        if (!step_known) {
            /* el paso se sabe al ejecutar: su signo dice el sentido, como en ./dash */
            op_ea(0x4A80, &vstep);                     /* tst.l paso */
            branch(CC_MI, neg);
        }
        for (pass_n = 0; pass_n < (step_known ? 1 : 2); pass_n++) {
            if (pass_n) def_label(neg);
            if (vend.kind == V_CONST) op_imm_ea(0x0C80, vend.val, &vi);     /* cmpi.l #fin,i */
            else if (vi.kind == V_REG) op_ea(0xB080 | vi.reg << 9, &vend);  /* cmp.l fin,di */
            else {
                load_var(0, &vi);
                op_ea(0xB080, &vend);                  /* cmp.l fin,d0 */
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
    if (vc.kind == V_REG) {
        dbra(vc.reg, top);
        w(0x0480 | vc.reg); l(0x10000);                /* subi.l #$10000,dN: más de 65536 vueltas */
        branch(CC_CC, top);
    }
    def_label(done);
    leave_loop();
    mark_end(&ms);
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
        op_ea(0x2F00, &v);                             /* move.l s,-(sp) */
        sp_depth += 4;
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
    if (e->kind == E_NIL) load_imm(0, 0);
    else if (ty == TY_DOUBLE) dbl_value(e);            /* (una caja; un número, convertido) */
    else str_value(e);
    push_d0();
    if (fresh) {
        w(0x4878); w(0);                               /* pea 0.w: sin texto antes */
        sp_depth += 4;
    } else {
        v = lookup(n->name);
        op_ea(0x2F00, &v);                             /* move.l s,-(sp) */
        sp_depth += 4;
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
        v.off = i * 4;
        v.type = global_type[i];
        if (g->init->kind == E_NIL) continue;
        if (IS_STRLIKE(global_type[i])) {
            if (global_type[i] == TY_DOUBLE) dbl_value(g->init);
            else str_value(g->init);
            push_d0();
            w(0x4878); w(0);                           /* pea 0.w */
            sp_depth += 4;
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
        w(0x4878); w(0);                               /* pea 0.w */
        sp_depth += 4;
    } else {
        v = lookup(n->name);
        op_ea(0x2F00, &v);                             /* move.l v,-(sp) */
        sp_depth += 4;
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
        w(0xB081);                                     /* cmp.l d1,d0 */
        branch(CC_GE, done);
    }
    if (src_slot >= 0) {
        use_slot(src_slot);
        vs = slot_var(src_slot, TY_STR);
    }
    load_var(0, &vs);
    tst_d0();
    branch(CC_EQ, done);                               /* nil: ninguno */
    w(0x2040);                                         /* movea.l d0,a0 */
    load_var(0, &vi);
    w(0x1030); w(0x0800);                              /* move.b (0,a0,d0.l),d0 */
    w(0x4880); w(0x48C0);                              /* ext.w d0; ext.l d0 (un char de C) */
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

static void gen_foreach(Node *n)
{
    int t = expr_type(n->a), et, top = new_label(), test = new_label(), cont = new_label(), done = new_label();
    int arr_slot, idx_slot;
    MarkScope ms;
    Loop lp;
    Var va, vi, vx;
    if (t == TY_STR) {
        gen_foreach_str(n);
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
    if (va.kind == V_REG) w(0x2040 | va.reg);          /* movea.l dN,a0 */
    else op_ea(0x2040, &va);                           /* movea.l lista,a0 */
    w(0x2050);                                         /* movea.l (a0),a0: los datos */
    use_slot(idx_slot);
    vi = slot_var(idx_slot, TY_INT);
    load_var(0, &vi);
    w(0xD080); w(0xD080);                              /* add.l d0,d0 (x2): bytes */
    w(0x2030); w(0x0800);                              /* move.l (0,a0,d0.l),d0 */
    if (IS_OBJ(et)) {
        /* un objeto, con una referencia durante la vuelta: el cuerpo podría sacarlo de la lista */
        push_d0();
        rt_call("_dl_retain_r", 1, 0);
    }
    vx = declare(n->name, et);
    if (IS_OBJ(et)) locals.v[locals.n - 1].owned = 2;
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
    w(0x2040);                                         /* movea.l d0,a0 */
    use_slot(idx_slot);
    if (vi.kind == V_REG) {
        w(0xB0A8 | vi.reg << 9); w(4);                 /* cmp.l 4(a0),dI */
    } else {
        load_var(1, &vi);
        w(0xB2A8); w(4);                               /* cmp.l 4(a0),d1 */
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

/* pea de la variable de la ventana (un puntero a ella, para dl_window_close y dl_event_next) */
static void pea_window(int wi)
{
    w(0x4879);                                         /* pea variable */
    add_reloc((uint32_t)obj->code.n, HK_DATA, NULL);
    l((uint32_t)win_off[wi]);
    sp_depth += 4;
}

static void gen_window_op(Node *n)
{
    int wi = find_window(n->name);
    if (wi < 0) fatal_node(n, "la ventana %s no existe", n->name);
    if (n->val) {
        Fixup f;
        pea_window(wi);                                /* dl_window_open(descriptor, &variable) */
        w(0x4879);                                     /* pea descriptor */
        f.at = (uint32_t)obj->code.n;
        f.label = win_desc_label[wi];
        f.abs = 1;
        f.size = 2;
        VEC_PUSH(fixups, f);
        add_reloc(f.at, HK_CODE, NULL);
        l(0);
        sp_depth += 4;
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
        args_to_stack(a, 1, NULL);
        w(0x2F00);                                     /* (move.l d0,-(sp): el intervalo, ya en la pila) */
        obj->code.n -= 2;
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
        static const long cls[] = {0x200 /* CLOSEWINDOW */, 0x400 /* RAWKEY */, 0x8 /* MOUSEBUTTONS */, -1, 0x40, 0x100};
        int next = new_label(), skip = new_label();
        /* la clase está en d0 hasta aquí: cada On la compara y, si no es la suya, salta al siguiente */
        if (cls[h->val] >= -128 && cls[h->val] <= 127) {
            w(0x7200 | (cls[h->val] & 0xFF));          /* moveq #clase,d1 */
            w(0xB081);                                 /* cmp.l d1,d0 */
        } else {
            w(0xB0BC); l((uint32_t)cls[h->val]);       /* cmp.l #clase,d0 */
        }
        branch(CC_NE, next);
        w(0x2F00);                                     /* move.l d0,-(sp): la clase, para el On siguiente */
        sp_depth += 4;
        if (h->val == ON_KEY) {
            /* las teclas al soltarse no cuentan; On Key "a" mira el texto de la tecla, On Key 69 su código */
            jsr_sym("_dl_event_code");
            w(0x0800); w(7);                           /* btst #7,d0: IECODE_UP_PREFIX */
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
                    w(0xB0BC); l((uint32_t)code);      /* cmp.l #código,d0 */
                    branch(CC_NE, skip);
                }
            }
        } else if (h->val == ON_CLICK) {
            jsr_sym("_dl_event_code");
            w(0xB0BC); l(0x68);                        /* cmp.l #SELECTDOWN,d0 */
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
    if (memcheck) {
        /* el sitio de la instrucción, para los avisos (_DASH_MC_WHERE de ./dash) */
        char where[600];
        snprintf(where, sizeof where, "%s:%d", src_files.v[n->file], n->line);
        w(0x23FC);                                     /* move.l #"fuente:línea",_dash_mc_where */
        add_reloc((uint32_t)obj->code.n, HK_DATA, NULL);
        l(add_string(where, (int)strlen(where)));
        add_reloc((uint32_t)obj->code.n, -1, "__dash_mc_where");
        l(0);
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
                w(0x2E80);                             /* move.l d0,(sp) */
                ty = TY_STR;
            }
            jsr_sym(ty == TY_BOOL ? "__dash_print_bool" : ty == TY_STR || ty == TY_NIL ? "__dash_print_str" :
                    ty == TY_CHAR ? "__dash_print_char" : "__dash_print_int");
        }
        pop_args(1);
        return;
    case S_ASSIGN:
    case S_VAR:
        {
            Local *lc = find_local(n->name);
            if (lc) lc->entry = 0;                     /* el rango de entrada ya no vale */
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
        MarkScope ms;
        int top, test, done, base = repls.n, slots = slot_uses.n;
        if (gen_counted_while(n)) return;
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
            if (sp_depth != ev->sp) { w(0x4FEF); w(sp_depth - ev->sp); }
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
        fatal_node(n, "dashc (prueba): esta asignación aún no está");
        return;
    case S_BREAK:
    case S_CONTINUE:
        if (loops.n <= loop_base) fatal_node(n, "%s fuera de un bucle", n->kind == S_BREAK ? "break" : "continue");
        {
            Loop *lp = &loops.v[loops.n - 1];
            free_owned(lp->depth, 0);
            if (sp_depth != lp->sp) { w(0x4FEF); w(sp_depth - lp->sp); }
            branch(CC_T, n->kind == S_BREAK ? lp->brk : lp->cont);
        }
        return;
    case S_RETURN: {
        int owned = has_owned(0, 1);
        if (n->a && ret_branch >= 0) {
            if (owned) {
                value(n->a);
                push_d0();
                free_owned(0, 1);
                pop_d0();
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
        if (sp_depth != ret_sp) { w(0x4FEF); w(sp_depth - ret_sp); }   /* lea: fuera las marcas de los bucles */
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

static void gen_function_pass(int label, Func *f, NodeList *body)
{
    uint32_t frame_at = 0;
    int i, nregs = 0, mask_push = 0, mask_pop = 0, last = 0;
    MarkScope fm;

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
            lc.entry = 0;
            lc.owned = 0;
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
    mark_seq = 0;
    made_tmp = 0;
    cur_ret = f ? f->ret : TY_VOID;
    if (f) {
        /* un parámetro de texto que el cuerpo cambia: una copia suya, como en ./dash */
        int idx = (int)(f - prog->funcs.v);
        for (i = 0; i < f->params.n; i++)
            if ((IS_STRLIKE(f->params.v[i].type) || IS_OBJ(f->params.v[i].type)) && param_set[idx][i]) {
                /* (una lista o un struct: una referencia suya) */
                int str = IS_STRLIKE(f->params.v[i].type);
                Var v = lookup(f->params.v[i].name);
                op_ea(0x2F00, &v);                     /* move.l p,-(sp) */
                sp_depth += 4;
                rt_call(str ? "_dl_str_dup" : "_dl_retain_r", 1, 0);
                store_d0(&v);
                locals.v[i].owned = str ? 1 : 2;
            }
        fm = mark_begin();
    } else {
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
                g.off = i * 4;
                g.type = global_type[i];
                op_ea(0x2F00, &g);                     /* move.l g,-(sp) */
                sp_depth += 4;
                rt_call(IS_STRLIKE(global_type[i]) ? "_dl_str_free" : "_dl_release", 1, 0);
                w(0x42B9);                             /* clr.l g */
                add_reloc((uint32_t)obj->code.n, HK_DATA, NULL);
                l((uint32_t)g.off);
            }
        jsr_sym("_dl_tmp_release_all");
    }
    if (f && IS_OBJ(cur_ret)) w(0x7000);               /* moveq #0,d0: sin return, nil */
    def_label(ret_label);
    if (f) {
        if (pass == 1) mark_need.v[fm.idx] = made_tmp;
        if (fm.on) {
            /* fuera los temporales de la función, menos el texto que devuelve */
            push_d0();
            w(0x2F2F); w(4);                           /* move.l 4(sp),-(sp): la marca */
            sp_depth += 4;
            rt_call(IS_STRLIKE(cur_ret) ? "_dl_tmp_release_keep" : "_dl_tmp_release_ret", 2, 0);
            pop_args(1);
        }
        if (IS_OBJ(cur_ret)) {
            push_d0();
            rt_call("_dl_obj_float", 1, 0);
        }
    }
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
    mark_need.n = 0;
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
        if (n->kind == S_ON && n->val == ON_CLICK) uses_click = 1;
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
        static const char *const fl[] = {"closegadget", "dragbar", "depthgadget", "sizegadget", "borderless", "activate"};
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
                for (f = 0; f < 6 && strcmp(fl[f], v->name); f++)
                    ;
                if (f < 6) flags = k ? flags | 1L << f : flags & ~(1L << f);
            }
        }
        def_label(win_desc_label[i]);
        add_reloc((uint32_t)obj->code.n, HK_DATA, NULL);
        l(add_string(title, (int)strlen(title)));
        l((uint32_t)left);
        l((uint32_t)top);
        l((uint32_t)width);
        l((uint32_t)height);
        l((uint32_t)flags);
        l(0x200 | (uses_keys ? 0x400 : 0) | (uses_click ? 0x8 : 0) |   /* CLOSEWINDOW, RAWKEY, MOUSEBUTTONS */
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
            w(0x2F0A);                                 /* move.l a2,-(sp) */
            w(0x246F); w(8);                           /* movea.l 8(sp),a2 */
            for (i = 0; i < st->fields.n; i++) {
                int ft = st->fields.v[i].type;
                if ((!IS_STRLIKE(ft) && !IS_OBJ(ft)) || st->fields.v[i].weak) continue;
                w(0x2F2A); w(4 * i);                   /* move.l campo(a2),-(sp) */
                jsr_sym(IS_STRLIKE(ft) ? "_dl_str_free" : "_dl_release_child");
                w(0x588F);                             /* addq.l #4,sp */
            }
            w(0x245F);                                 /* movea.l (sp)+,a2 */
            w(0x4E75);                                 /* rts */
        }
        def_label(desc_label[si]);
        if (destroy >= 0) {
            Fixup f;
            f.at = (uint32_t)obj->code.n;
            f.label = destroy;
            f.abs = 1;
            f.size = 2;
            VEC_PUSH(fixups, f);
            add_reloc(f.at, HK_CODE, NULL);
        }
        l(0);
        l((uint32_t)(4 * st->fields.n));
        if (st->ifaces.n) {
            /* la tabla de métodos de sus interfaces: justo detrás */
            Fixup f;
            int tab = new_label(), j, k;
            f.at = (uint32_t)obj->code.n;
            f.label = tab;
            f.abs = 1;
            f.size = 2;
            VEC_PUSH(fixups, f);
            add_reloc(f.at, HK_CODE, NULL);
            l(0);
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
                    f.at = (uint32_t)obj->code.n;
                    f.label = func_label[fi];
                    VEC_PUSH(fixups, f);
                    add_reloc(f.at, HK_CODE, NULL);
                }
                l(0);
            }
        } else {
            l(0);
        }
    }
}

void gen_program(Program *p, Obj *o)
{
    int i, main_label, again, files_label;
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
        buf_long(&o->data, (uint32_t)v);
    }
    /* los campos a los que algo asigna (préstamos) */
    find_set_fields(&p->main);
    for (i = 0; i < p->funcs.n; i++) find_set_fields(&p->funcs.v[i].body);

    /* las ventanas: su variable, tras las globales */
    win_off = xmalloc(sizeof(long) * (p->windows.n + 1));
    win_desc_label = xmalloc(sizeof(int) * (p->windows.n + 1));
    for (i = 0; i < p->windows.n; i++) {
        win_off[i] = (long)o->data.n;
        buf_long(&o->data, 0);
        win_desc_label[i] = new_label();
    }
    find_uses(&p->main);
    for (i = 0; i < p->funcs.n; i++) find_uses(&p->funcs.v[i].body);

    /* lo que devuelve cada función */
    fret_state = xmalloc(sizeof(int) * (p->funcs.n + 1));
    memset(fret_state, 0, sizeof(int) * (p->funcs.n + 1));
    infer_params(p);
    for (i = 0; i < p->funcs.n; i++) func_ret(i);

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
    {
        /* la pila que pide (16 KB, como ./dash; 32 KB con MUI, 64 KB con AmiSSL; más con @stack): _dash_start
           cambia a una así si la del shell es menor */
        long stack = uses_tls ? 65536 : uses_mui ? 32768 : 16384;
        if (p->stack_min > stack) stack = p->stack_min;
        w(0x2F3C); l((uint32_t)stack);                 /* move.l #pila,-(sp) */
    }
    {
        int k;
        for (k = 0; k < 2; k++) {
            Fixup f;
            w(0x4879);                                 /* pea ficheros (sus nombres, para los errores); pea main */
            f.at = (uint32_t)obj->code.n;
            f.label = k ? main_label : files_label;
            f.abs = 1;
            f.size = 2;
            VEC_PUSH(fixups, f);
            add_reloc(f.at, HK_CODE, NULL);
            l(0);
        }
    }
    w(0x4EF9);                                         /* jmp _dash_start */
    add_reloc((uint32_t)obj->code.n, -1, "__dash_start");
    l(0);

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
    for (i = 0; i < src_files.n && i < 63; i++) {
        add_reloc((uint32_t)obj->code.n, HK_DATA, NULL);
        l(add_string(src_files.v[i], (int)strlen(src_files.v[i])));
    }
    l(0);
    resolve_fixups();
}
