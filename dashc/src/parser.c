/* Parser de descenso recursivo. Sigue la gramática de compiler/grammar.py en el
   subconjunto de dashc: enteros, Bool, textos, listas, structs con métodos, variables,
   globales con var, const, funciones, if/elif/else, while, for con rango y sobre listas. */
#include <stdio.h>
#include <string.h>
#include <time.h>

#include "dashc.h"

static Token *tk;
static Func *cur_func;

static Token *peek(void) { return tk; }
static Token *next(void) { return tk++; }

static int accept(int kind)
{
    if (tk->kind == kind) {
        tk++;
        return 1;
    }
    return 0;
}

static Token *expect(int kind)
{
    if (tk->kind != kind)
        fatal_at(tk->line, tk->col, "se esperaba \"%s\" y hay \"%s\"", tok_name(kind), tok_name(tk->kind));
    return tk++;
}

static Node *node(int kind, Token *at)
{
    Node *n = xmalloc(sizeof(Node));
    n->kind = kind;
    n->line = at->line;
    n->col = at->col;
    n->file = at->file;
    return n;
}

/* var x: Tipo sin valor: 0 un número, nil lo demás (como ./dash) */
static Node *zero_value(Token *at, int type)
{
    Node *n = node(E_INT, at);
    if (type != TY_INT && type != TY_BOOL && type != TY_CHAR && type != TY_FLOAT && type != TY_FIXED) n->kind = E_NIL;
    else if (type == TY_BOOL) n->kind = E_BOOL;
    return n;
}

struct TypeNames type_names;
struct DictTypes dict_types;

int dict_type(int key, int val)
{
    DictType d;
    int i;
    for (i = 0; i < dict_types.n; i++)
        if (dict_types.v[i].key == key && dict_types.v[i].val == val) return TY_DICT + i;
    d.key = key;
    d.val = val;
    VEC_PUSH(dict_types, d);
    return TY_DICT + dict_types.n - 1;
}

/* Int, Bool, String, Array o el nombre de un struct (que puede venir después: TY_NAMED) */
static int parse_type(void)
{
    Token *t;
    int i;
    if (accept(P_LBRACE)) {
        /* {String: T} o {Int: T} */
        Token *at = peek();
        int key = parse_type(), val;
        if (key != TY_STR && key != TY_INT) fatal_at(at->line, at->col, "la clave de un diccionario es String o Int");
        expect(P_COLON);
        val = parse_type();
        expect(P_RBRACE);
        return dict_type(key, val);
    }
    if (accept(P_LB)) {
        /* [T]: lista de T */
        i = parse_type();
        expect(P_RB);
        return (i == TY_ARR + TY_VOID ? TY_ARR + TY_INT : i) + TY_ARR;
    }
    t = expect(T_ID);
    if (!strcmp(t->text, "Ptr") && peek()->kind == T_ID) {
        /* Ptr X: un puntero a una @amiga struct o a un escalar; con su nombre, que gen68k.c resuelve */
        Token *x = next();
        char *name = xmalloc(strlen(x->text) + 5);
        sprintf(name, "Ptr %s", x->text);
        for (i = 0; i < type_names.n; i++)
            if (!strcmp(type_names.v[i], name)) return TY_NAMED + i;
        VEC_PUSH(type_names, name);
        return TY_NAMED + type_names.n - 1;
    }
    if (!strcmp(t->text, "Int")) return TY_INT;
    if (!strcmp(t->text, "Bool")) return TY_BOOL;
    if (!strcmp(t->text, "String")) return TY_STR;
    if (!strcmp(t->text, "Array")) return TY_ARR + TY_VOID;   /* lo que guarda, por su uso */
    if (!strcmp(t->text, "Pointer")) return TY_INT;          /* una dirección: un número de 32 bits */
    if (!strcmp(t->text, "Float")) return TY_FLOAT;
    if (!strcmp(t->text, "Double")) return TY_DOUBLE;
    if (!strcmp(t->text, "Func")) return TY_INT;          /* una función como valor: su dirección */
    if (!strcmp(t->text, "Fixed")) return TY_FIXED;      /* coma fija 16.16 en un LONG */
    if (!strcmp(t->text, "Void")) return TY_VOID;          /* -> Void: no devuelve nada */
    if (0)
        fatal_at(t->line, t->col, "(sin --gcc) el tipo %s aún no está", t->text);
    for (i = 0; i < type_names.n; i++)
        if (!strcmp(type_names.v[i], t->text)) return TY_NAMED + i;
    VEC_PUSH(type_names, t->text);
    return TY_NAMED + type_names.n - 1;
}

/* ---- expresiones, de menos a más precedencia ---- */
static Node *expr(void);
static Node *lambda(Token *t);
static void block(NodeList *out, int stop1, int stop2, int stop3);

static Node *interp(Token *t);

static void args_until(NodeList *out, int close)
{
    if (accept(close)) return;
    do VEC_PUSH(*out, expr()); while (accept(P_COMMA));
    expect(close);
}

static Node *atom(void)
{
    Token *t = next();
    Node *n;
    switch (t->kind) {
    case T_INT:
        n = node(E_INT, t);
        n->val = t->val;
        return n;
    case T_STR:
        n = node(E_STR, t);
        n->str = t->text;
        n->len = t->len;
        return n;
    case T_ISTR:
        return interp(t);
    case T_FLOAT:
        n = node(E_FLOAT, t);
        n->val = t->val;
        n->dval = t->dval;
        return n;
    case K_TRUE:
    case K_FALSE:
        n = node(E_BOOL, t);
        n->val = t->kind == K_TRUE;
        return n;
    case K_NIL:
        return node(E_NIL, t);
    case P_LB:
        n = node(E_LIST, t);
        args_until(&n->args, P_RB);
        return n;
    case P_LBRACE:
        /* {clave: valor, ...} */
        n = node(E_DICT, t);
        if (!accept(P_RBRACE)) {
            do {
                VEC_PUSH(n->args, expr());
                expect(P_COLON);
                VEC_PUSH(n->args, expr());
            } while (accept(P_COMMA));
            expect(P_RBRACE);
        }
        return n;
    case T_ID:
        if (!strcmp(t->text, "fn") && peek()->kind == P_LP) return lambda(t);
        if ((!strcmp(t->text, "build_date") || !strcmp(t->text, "build_time")) && peek()->kind == P_LP &&
            tk[1].kind == P_RP) {
            /* el momento de compilar: un texto ya hecho ("2026-10-28", "20:45:10") */
            time_t now = time(NULL);
            struct tm *tm = localtime(&now);
            char buf[16];
            next();
            next();
            strftime(buf, sizeof buf, t->text[6] == 'd' ? "%Y-%m-%d" : "%H:%M:%S", tm);
            n = node(E_STR, t);
            n->str = xstrndup(buf, strlen(buf));
            n->len = (int)strlen(buf);
            return n;
        }
        if (!strcmp(t->text, "Ptr") && peek()->kind == T_ID && tk[1].kind == P_LP) {
            /* Ptr X(dirección): una @amiga struct (A6) */
            n = node(E_ACAST, t);
            n->name = next()->text;
            expect(P_LP);
            n->a = expr();
            expect(P_RP);
            return n;
        }
        if (accept(P_LP)) {
            n = node(E_CALL, t);
            n->name = t->text;
            args_until(&n->args, P_RP);
            return n;
        }
        n = node(E_VAR, t);
        n->name = t->text;
        return n;
    case P_LP:
        n = expr();
        expect(P_RP);
        return n;
    }
    fatal_at(t->line, t->col, "se esperaba una expresión y hay \"%s\"", tok_name(t->kind));
    return NULL;
}

/* fn(a, b) -> expresión: una función sin nombre (__fn_N) con "return expresión"; el valor es su dirección.
   Va a la lista del programa al acabar lo de arriba que se está leyendo (la función de dentro sigue en uso). */
static struct { Func *v; int n, cap; } lambdas;
static int nlambdas;

static Node *lambda(Token *t)
{
    Func f = {0};
    Node *n, *r;
    char name[32];
    expect(P_LP);
    if (!accept(P_RP)) {
        do {
            Param pa;
            pa.name = expect(T_ID)->text;
            pa.untyped = !accept(P_COLON);
            pa.type = pa.untyped ? TY_INT : parse_type();
            VEC_PUSH(f.params, pa);
        } while (accept(P_COMMA));
        expect(P_RP);
    }
    snprintf(name, sizeof name, "__fn_%d", nlambdas++);
    f.name = xstrndup(name, strlen(name));
    f.line = t->line;
    f.col = t->col;
    f.file = t->file;
    if (accept(P_ARROW)) {
        f.has_value = 1;
        r = node(S_RETURN, t);
        r->a = expr();
        f.boolret = r->a->kind == E_CMP || r->a->kind == E_AND || r->a->kind == E_OR || r->a->kind == E_NOT ||
                    r->a->kind == E_BOOL;
        VEC_PUSH(f.body, r);
    } else {
        /* fn(x) en su línea, el cuerpo debajo y end */
        Func *saved = cur_func;
        cur_func = &f;
        block(&f.body, K_END, K_END, K_END);
        cur_func = saved;
        expect(K_END);
    }
    VEC_PUSH(lambdas, f);
    n = node(E_VAR, t);
    n->name = f.name;
    return n;
}

/* a[i], a[i:j], a.campo, a.metodo(...) */
static Node *primary(void)
{
    Node *n = atom();
    for (;;) {
        Token *t = peek();
        if (accept(P_LB)) {
            Node *m;
            Node *i = peek()->kind == P_COLON ? NULL : expr();
            if (accept(P_COLON)) {
                m = node(E_SLICE, t);
                m->b = i;
                m->c = peek()->kind == P_RB ? NULL : expr();
            } else {
                m = node(E_INDEX, t);
                m->b = i;
            }
            expect(P_RB);
            m->a = n;
            n = m;
        } else if (accept(P_DOT)) {
            Token *name = expect(T_ID);
            Node *m = node(accept(P_LP) ? E_MCALL : E_FIELD, name);
            m->name = name->text;
            m->a = n;
            if (m->kind == E_MCALL) args_until(&m->args, P_RP);
            n = m;
        } else {
            return n;
        }
    }
}

/* "a#{x}b": los trozos de código se analizan aparte, como expresiones */
static Node *interp(Token *t)
{
    Node *n = node(E_INTERP, t);
    int i;
    for (i = 0; i < t->npieces; i++) {
        if (i % 2 == 0) {
            if (t->plen[i]) {
                Node *s = node(E_STR, t);
                s->str = t->piece[i];
                s->len = t->plen[i];
                VEC_PUSH(n->args, s);
            }
        } else {
            Token *saved = tk, *sub = lex(t->piece[i]), *p;
            for (p = sub; ; p++) {
                p->line += t->line - 1;
                if (p->line == t->line) p->col += t->col;
                if (p->kind == T_EOF) break;
            }
            tk = sub;
            VEC_PUSH(n->args, expr());
            if (peek()->kind != T_EOF) fatal_at(peek()->line, peek()->col, "sobra algo dentro de #{...}");
            tk = saved;
        }
    }
    return n;
}

static Node *unary(void)
{
    Token *t = peek();
    if (accept(P_MINUS) || accept(P_TILDE)) {
        Node *n = node(t->kind == P_MINUS ? E_NEG : E_BNOT, t);
        n->a = unary();
        return n;
    }
    return primary();
}

static Node *binary(Node *a, Token *op, Node *b)
{
    Node *n = node(E_BIN, op);
    n->op = op->kind;
    n->a = a;
    n->b = b;
    return n;
}

/* un nivel de operadores binarios asociativos por la izquierda */
#define LEVEL(fn, sub, ...) \
    static Node *fn(void) \
    { \
        static const int ops[] = { __VA_ARGS__, -1 }; \
        Node *n = sub(); \
        for (;;) { \
            int i, found = 0; \
            for (i = 0; ops[i] >= 0; i++) \
                if (peek()->kind == ops[i]) found = 1; \
            if (!found) return n; \
            Token *op = next(); \
            n = binary(n, op, sub()); \
        } \
    }

LEVEL(mul_expr, unary, P_STAR, P_SLASH, P_PERCENT)
LEVEL(add_expr, mul_expr, P_PLUS, P_MINUS)
LEVEL(shift_expr, add_expr, P_SHL, P_SHR)
LEVEL(band_expr, shift_expr, P_AMP)
LEVEL(bxor_expr, band_expr, P_CARET)
LEVEL(bor_expr, bxor_expr, P_BAR)

static int is_cmp(int k)
{
    return k == P_EQ || k == P_NE || k == P_LT || k == P_LE || k == P_GT || k == P_GE;
}

/* un valor que se puede escribir dos veces: una variable, un literal, un campo, un elemento */
static int chain_safe(Node *n)
{
    switch (n->kind) {
    case E_VAR: case E_INT: case E_STR: case E_BOOL: case E_NIL: case E_FLOAT:
        return 1;
    case E_FIELD: case E_NEG:
        return chain_safe(n->a);
    case E_INDEX:
        return chain_safe(n->a) && chain_safe(n->b);
    }
    return 0;
}

/* tk en "(": ¿hay un ".." dentro, fuera de otros paréntesis? (x in (a..b)) */
static int range_ahead(void)
{
    Token *t;
    int depth = 0;
    for (t = tk; t->kind != T_EOF; t++) {
        if (t->kind == P_LP || t->kind == P_LB || t->kind == P_LBRACE) depth++;
        else if (t->kind == P_RP || t->kind == P_RB || t->kind == P_RBRACE) {
            if (--depth == 0) return 0;
        } else if (t->kind == P_DOTDOT && depth == 1) return 1;
    }
    return 0;
}

static Node *cmp_node(Token *at, Node *a, int op, Node *b)
{
    Node *n = node(E_CMP, at);
    n->op = op;
    n->a = a;
    n->b = b;
    return n;
}

static Node *logic(int kind, Token *at, Node *a, Node *b)
{
    Node *n = node(kind, at);
    n->a = a;
    n->b = b;
    return n;
}

/* x in (a..b step s), x in lista, x in texto, x in diccionario (lo pidió David Martínez) */
static Node *in_expr(Node *x, Token *t)
{
    Node *n = node(E_IN, t);
    n->a = x;
    if (peek()->kind == P_LP && range_ahead()) {
        next();
        n->kind = E_INRANGE;
        VEC_PUSH(n->args, expr());
        expect(P_DOTDOT);
        VEC_PUSH(n->args, expr());
        if (accept(K_STEP)) {
            VEC_PUSH(n->args, expr());
        } else {
            Node *z = node(E_INT, t);
            z->val = 0;
            VEC_PUSH(n->args, z);
            /* (1..10) fijo y x una variable: 1 <= x and x <= 10 (gen68k.c, tras mirar los tipos) */
            if (chain_safe(x))
                n->c = logic(E_AND, t, cmp_node(t, x, P_GE, n->args.v[0]), cmp_node(t, x, P_LE, n->args.v[1]));
        }
        expect(P_RP);
        return n;
    }
    n->b = bor_expr();
    if (n->b->kind == E_LIST && chain_safe(x)) {
        /* x in [1, 5, 9]: x == 1 or x == 5 or x == 9 */
        Node *r = NULL;
        int i;
        if (!n->b->args.n) {
            r = node(E_BOOL, t);
            r->val = 0;
            return r;
        }
        for (i = 0; i < n->b->args.n; i++) {
            Node *eq = cmp_node(t, x, P_EQ, n->b->args.v[i]);
            r = r ? logic(E_OR, t, r, eq) : eq;
        }
        return r;
    }
    return n;
}

static Node *compare_expr(void)
{
    Node *n = bor_expr(), *last;
    int k = peek()->kind;
    if (k == K_IN || (k == K_NOT && tk[1].kind == K_IN)) {
        Token *t = next();
        if (k == K_NOT) {
            Node *m = node(E_NOT, t);
            next();
            m->a = in_expr(n, t);
            return m;
        }
        return in_expr(n, t);
    }
    if (is_cmp(k)) {
        Token *op = next();
        n = last = binary(n, op, bor_expr());
        n->kind = E_CMP;
        /* a < b <= c: a < b and b <= c, con b escrito dos veces (como en Python) */
        while (is_cmp(peek()->kind)) {
            Node *c;
            op = next();
            if (!chain_safe(last->b))
                fatal_at(op->line, op->col, "en una cadena de comparaciones (a < b < c) el valor del medio no puede "
                         "llamar a una función: guárdalo antes en una variable, o escribe x in (a..b)");
            c = binary(last->b, op, bor_expr());
            c->kind = E_CMP;
            n = logic(E_AND, op, n, c);
            last = c;
        }
    }
    return n;
}

static Node *not_expr(void)
{
    Token *t = peek();
    if (accept(K_NOT)) {
        Node *n = node(E_NOT, t);
        n->a = not_expr();
        return n;
    }
    return compare_expr();
}

static Node *and_expr(void)
{
    Node *n = not_expr();
    while (peek()->kind == K_AND) {
        Node *m = node(E_AND, next());
        m->a = n;
        m->b = not_expr();
        n = m;
    }
    return n;
}

static Node *expr(void)
{
    Node *n = and_expr();
    while (peek()->kind == K_OR) {
        Node *m = node(E_OR, next());
        m->a = n;
        m->b = and_expr();
        n = m;
    }
    return n;
}

/* ---- instrucciones ---- */
static void block(NodeList *out, int stop1, int stop2, int stop3);

static Node *stmt(void)
{
    Token *t = next();
    Node *n;
    switch (t->kind) {
    case K_IF:
    case K_ELIF:
        n = node(S_IF, t);
        n->a = expr();
        block(&n->body, K_ELIF, K_ELSE, K_END);
        if (peek()->kind == K_ELIF) {
            /* elif: un if dentro de la rama no, que se lleva el "end" */
            VEC_PUSH(n->els, stmt());
            return n;
        }
        if (accept(K_ELSE)) block(&n->els, K_END, K_END, K_END);
        expect(K_END);
        return n;
    case K_WHILE:
        n = node(S_WHILE, t);
        n->a = expr();
        block(&n->body, K_END, K_END, K_END);
        expect(K_END);
        return n;
    case K_FOR:
        n = node(S_FOR, t);
        n->name = expect(T_ID)->text;
        expect(K_IN);
        if (!accept(P_LP)) {
            /* for x in lista */
            n->kind = S_FOREACH;
            n->a = expr();
            block(&n->body, K_END, K_END, K_END);
            expect(K_END);
            return n;
        }
        n->a = expr();
        expect(P_DOTDOT);
        n->b = expr();
        if (accept(K_STEP)) n->c = expr();
        expect(P_RP);
        block(&n->body, K_END, K_END, K_END);
        expect(K_END);
        return n;
    case K_RETURN:
        n = node(S_RETURN, t);
        /* el valor, si sigue en la misma línea */
        if (peek()->line == t->line && peek()->kind != K_END) {
            n->a = expr();
            if (!cur_func) fatal_at(t->line, t->col, "return con valor fuera de una función");
            cur_func->has_value = 1;
        }
        return n;
    case K_BREAK:
        return node(S_BREAK, t);
    case K_CONTINUE:
        return node(S_CONTINUE, t);
    case K_PRINT:
        n = node(S_PRINT, t);
        n->a = expr();
        return n;
    case K_VAR:
        n = node(S_VAR, t);
        n->name = expect(T_ID)->text;
        expect(P_COLON);
        n->type = parse_type();
        n->a = accept(P_ASSIGN) ? expr() : zero_value(t, n->type);
        return n;
    case T_ID: {
        Node *target;
        if (!strcmp(t->text, "Stop") && peek()->line != t->line)
            return node(S_STOP, t);
        if (!strcmp(t->text, "EventLoop")) {
            /* EventLoop / On Close|Key ["x"|n]|Click|Timer n|Gadget|Menu|RightClick|Inactive ... end / end */
            n = node(S_EVLOOP, t);
            while (!accept(K_END)) {
                Token *on = expect(T_ID), *kind;
                Node *h;
                static const char *const names[] = {"Close", "Key", "Click", "Timer", "Gadget", "Menu", "RightClick",
                                                     "Inactive", NULL};
                int i;
                if (strcmp(on->text, "On")) fatal_at(on->line, on->col, "en un EventLoop va On ...");
                kind = expect(T_ID);
                h = node(S_ON, on);
                for (i = 0; names[i] && strcmp(names[i], kind->text); i++)
                    ;
                if (!names[i]) fatal_at(kind->line, kind->col, "On %s no existe", kind->text);
                h->val = i;
                if (i == ON_KEY && peek()->line == kind->line && (peek()->kind == T_STR || peek()->kind == T_INT))
                    h->a = atom();
                if (i == ON_TIMER) h->a = atom();
                block(&h->body, K_END, K_END, K_END);
                expect(K_END);
                VEC_PUSH(n->body, h);
            }
            return n;
        }
        if (!strcmp(t->text, "Wait") && peek()->line == t->line && peek()->kind != P_ASSIGN && peek()->kind != P_LP &&
            peek()->kind != P_DOT && peek()->kind != P_LB) {
            /* Wait segundos: la función Wait del runtime */
            n = node(S_EXPR, t);
            n->a = node(E_CALL, t);
            n->a->name = "Wait";
            VEC_PUSH(n->a->args, expr());
            return n;
        }
        tk--;
        target = primary();
        if (accept(P_ASSIGN)) {
            if (target->kind == E_VAR) {
                n = node(S_ASSIGN, t);
                n->name = t->text;
            } else if (target->kind == E_INDEX || target->kind == E_FIELD) {
                n = node(S_STORE, t);
                n->b = target;
            } else {
                fatal_at(t->line, t->col, "no se puede asignar a esto");
                return NULL;
            }
            n->a = expr();
            return n;
        }
        if (target->kind == E_CALL || target->kind == E_MCALL) {
            n = node(S_EXPR, t);
            n->a = target;
            return n;
        }
        if (target->kind == E_FIELD && target->a->kind == E_VAR &&
            (!strcmp(target->name, "open") || !strcmp(target->name, "close"))) {
            /* Ventana.open, Ventana.close */
            n = node(S_WINDOW, t);
            n->name = target->a->name;
            n->val = !strcmp(target->name, "open");
            return n;
        }
        break;
    }
    }
    fatal_at(t->line, t->col, "no se esperaba \"%s\" aquí", tok_name(t->kind));
    return NULL;
}

static void block(NodeList *out, int stop1, int stop2, int stop3)
{
    for (;;) {
        int k = peek()->kind;
        if (k == stop1 || k == stop2 || k == stop3) return;
        if (k == T_EOF) fatal_at(peek()->line, peek()->col, "falta \"end\"");
        VEC_PUSH(*out, stmt());
    }
}

/* func nombre(params) -> Tipo ... end; en un struct st, el método lleva self delante */
int parse_module_ok;

static void parse_func(Program *p, Struct *st)
{
    Func f = {0};
    Token *name;
    expect(K_FUNC);
    name = expect(T_ID);
    f.name = name->text;
    f.line = name->line;
    f.col = name->col;
    f.file = name->file;
    if (st) {
        Param self;
        int i;
        size_t len = strlen(st->name) + strlen(name->text) + 2;
        f.name = xmalloc(len);
        strcpy(f.name, st->name);
        strcat(f.name, ".");
        strcat(f.name, name->text);
        self.name = "self";
        self.untyped = 0;
        self.type = -1;
        for (i = 0; i < type_names.n; i++)
            if (!strcmp(type_names.v[i], st->name)) self.type = TY_NAMED + i;
        if (self.type < 0) {
            VEC_PUSH(type_names, st->name);
            self.type = TY_NAMED + type_names.n - 1;
        }
        VEC_PUSH(f.params, self);
    }
    expect(P_LP);
    if (!accept(P_RP)) {
        do {
            Param pa;
            pa.name = expect(T_ID)->text;
            pa.untyped = !accept(P_COLON);
            pa.type = pa.untyped ? TY_INT : parse_type();
            VEC_PUSH(f.params, pa);
        } while (accept(P_COMMA));
        expect(P_RP);
    }
    if (accept(P_ARROW)) {
        f.ret = parse_type();
        f.declared = 1;
    }
    if (peek()->kind == T_STR && peek()[1].kind == K_END) {
        /* el C de un @native: no hay cuerpo de Dash */
        next();
        next();
        f.declared = 1;
        VEC_PUSH(p->funcs, f);
        return;
    }
    VEC_PUSH(p->funcs, f);
    cur_func = &p->funcs.v[p->funcs.n - 1];
    block(&cur_func->body, K_END, K_END, K_END);
    cur_func = NULL;
    expect(K_END);
}

/* "a/b/../c" -> "a/c", sin "./" */
static char *normalize(const char *path)
{
    char *out = xmalloc(strlen(path) + 1), *seg[256];
    char *copy = xstrndup(path, strlen(path)), *tok;
    int n = 0, i, abs = path[0] == '/';
    for (tok = strtok(copy, "/"); tok; tok = strtok(NULL, "/")) {
        if (!strcmp(tok, ".")) continue;
        if (!strcmp(tok, "..") && n > 0 && strcmp(seg[n - 1], "..")) n--;
        else if (n < 256) seg[n++] = tok;
    }
    out[0] = 0;
    if (abs) strcat(out, "/");
    for (i = 0; i < n; i++) {
        if (i) strcat(out, "/");
        strcat(out, seg[i]);
    }
    return out;
}

/* import "x.dash": como ./dash, relativo al fichero que importa y si no, a sus carpetas de más arriba
   (la raíz de Dash, con lib/amiga), a la carpeta actual y a la de Dash (dash_home) */
static void parse_into(Program *p);

static void import_file(Program *p, Token *at, const char *path)
{
    const char *from = src_files.v[at->file];
    char dir[1024], *full = NULL, *text;
    int i, up;
    Token *saved_tk = tk;
    const char *saved_name = src_name;
    int saved_file = lex_file;
    const char *slash = strrchr(from, '/');
    snprintf(dir, sizeof dir, "%.*s", slash ? (int)(slash - from) : 0, from);
    for (up = 0; up < 10 && !full; up++) {
        char cand[2048], *norm;
        snprintf(cand, sizeof cand, "%s%s%s", dir, dir[0] ? "/" : "", path);
        norm = normalize(cand);
        if ((text = read_text(norm)) != NULL) full = norm;
        if (!dir[0] || !strcmp(dir, "/")) break;
        if (!full) {
            /* la carpeta de arriba */
            char *s = strrchr(dir, '/');
            if (s) *s = 0;
            else if (strcmp(dir, "..") && strncmp(dir, "../", 3)) dir[0] = 0;
            else strncat(dir, "/..", sizeof dir - strlen(dir) - 1);
        }
    }
    if (!full && (text = read_text(path)) != NULL) full = normalize(path);
    if (!full && dash_home[0]) {
        /* la carpeta de Dash: import "lib/json.dash" desde un programa de cualquier sitio */
        char cand[2048], *norm;
        size_t k = strlen(dash_home);
        snprintf(cand, sizeof cand, "%s%s%s", dash_home, dash_home[k - 1] == ':' || dash_home[k - 1] == '/' ? "" : "/",
                 path);
        norm = dash_home[k - 1] == ':' ? xstrndup(cand, strlen(cand)) : normalize(cand);
        if ((text = read_text(norm)) != NULL) full = norm;
    }
    if (!full) fatal_at(at->line, at->col, "no encuentro %s para importarlo", path);
    for (i = 0; i < src_files.n; i++)
        if (!strcmp(src_files.v[i], full)) return;     /* ya importado */
    /* un .dashui (ventanas del editor de MUI): su código Dash, como un módulo más */
    if (strlen(path) > 7 && !strcmp(path + strlen(path) - 7, ".dashui")) text = dashui_generate(text, full);
    VEC_PUSH(src_files, full);
    lex_file = src_files.n - 1;
    src_name = full;
    {
        /* sus nombres privados: lo que declara con `_` delante (func, const, var, struct, enum...) */
        const char **saved_priv = lex_priv;
        int saved_npriv = lex_npriv, n = 0;
        lex_npriv = 0;
        tk = lex(text);
        lex_priv = NULL;
        for (i = 1; tk[i - 1].kind != T_EOF && tk[i].kind != T_EOF; i++) {
            Token *d = &tk[i - 1];
            if (tk[i].kind == T_ID && tk[i].text[0] == '_' &&
                (d->kind == K_FUNC || d->kind == K_CONST || d->kind == K_VAR || d->kind == K_STRUCT ||
                 (d->kind == T_ID && (!strcmp(d->text, "enum") || !strcmp(d->text, "interface"))))) {
                lex_priv = xrealloc(lex_priv, (n + 1) * sizeof *lex_priv);
                lex_priv[n++] = tk[i].text;
            }
        }
        lex_npriv = n;
        if (n) tk = lex(text);
        parse_into(p);
        while (lambdas.n) VEC_PUSH(p->funcs, lambdas.v[--lambdas.n]);
        lex_priv = saved_priv;
        lex_npriv = saved_npriv;
    }
    tk = saved_tk;
    src_name = saved_name;
    lex_file = saved_file;
}

Program *parse(Token *toks)
{
    Program *p = xmalloc(sizeof(Program));
    tk = toks;
    parse_into(p);
    while (lambdas.n) VEC_PUSH(p->funcs, lambdas.v[--lambdas.n]);
    if (!p->has_main && !parse_module_ok) fatal("falta el bloque Main");
    return p;
}

static void parse_into(Program *p)
{
    while (peek()->kind != T_EOF) {
        Token *t;
        /* las lambdas de lo anterior, ya como funciones */
        while (lambdas.n) VEC_PUSH(p->funcs, lambdas.v[--lambdas.n]);
        t = next();
        if (t->kind == T_ID && !strcmp(t->text, "import") && peek()->kind == T_STR) {
            import_file(p, t, next()->text);
            continue;
        }
        if (t->kind == T_ID && !strcmp(t->text, "Window") && peek()->kind == T_ID) {
            /* Window Nombre / propiedad valor ... / end */
            WindowDef wd = {0};
            Token *name = next();
            wd.name = name->text;
            wd.line = name->line;
            wd.col = name->col;
            while (!accept(K_END)) {
                Token *pn = expect(T_ID);
                Node *v = expr();
                v->name = pn->text;
                VEC_PUSH(wd.props, v);
            }
            VEC_PUSH(p->windows, wd);
            continue;
        }
        if (t->kind == T_ID && !strcmp(t->text, "enum") && peek()->kind == T_ID) {
            /* enum Nombre A, B = 5, C ... end: cada uno vale el anterior + 1 (el primero, 0) */
            Enum e = {0};
            long v = 0;
            e.name = next()->text;
            while (!accept(K_END)) {
                Token *m = expect(T_ID);
                if (accept(P_ASSIGN)) {
                    int neg = accept(P_MINUS);
                    v = expect(T_INT)->val;
                    if (neg) v = -v;
                }
                VEC_PUSH(e.names, m->text);
                VEC_PUSH(e.vals, v);
                v++;
                accept(P_COMMA);
            }
            VEC_PUSH(p->enums, e);
            continue;
        }
        if (t->kind == T_ID && !strcmp(t->text, "@native")) {
            /* @native func f(...) -> T """C""" end: solo vale si su C va en la librería (lib/amiga) */
            Func *f;
            parse_func(p, NULL);
            f = &p->funcs.v[p->funcs.n - 1];
            f->native = 1;
            continue;
        }
        if (t->kind == T_ID && !strcmp(t->text, "@stack")) {
            long n = expect(T_INT)->val;
            if (n > p->stack_min) p->stack_min = n;
            continue;
        }
        if (t->kind == T_ID && !strcmp(t->text, "@version")) {
            p->version = expect(T_STR)->text;
            continue;
        }
        if (t->kind == T_ID && !strcmp(t->text, "@catalog")) {
            /* @catalog "X.catalog" versión ["idioma de sus textos"]: el que abre el primer tr */
            p->catalog = expect(T_STR)->text;
            p->catalog_version = expect(T_INT)->val;
            if (peek()->kind == T_STR) p->catalog_lang = next()->text;
            continue;
        }
        if (t->kind == T_ID && !strcmp(t->text, "@workbench_output")) {
            /* el del programa gana al de un módulo */
            Token *v = expect(T_STR);
            if (t->file == 0 || !p->wb_output_main) p->wb_output = v->text;
            if (t->file == 0) p->wb_output_main = 1;
            continue;
        }
        if (t->kind == T_ID && !strcmp(t->text, "@link")) {
            /* @link "x.o" o "libx.a": relativo al fichero que lo dice */
            Token *v = expect(T_STR);
            const char *from = src_files.v[t->file], *slash = strrchr(from, '/');
            char *path = xmalloc(strlen(from) + strlen(v->text) + 2);
            if (v->text[0] == '/' || !slash) strcpy(path, v->text);
            else sprintf(path, "%.*s/%s", (int)(slash - from), from, v->text);
            link_add(path);
            continue;
        }
        if (t->kind == T_ID && !strcmp(t->text, "@extern")) {
            /* @extern("lo que sea") func f(a: Int, s: String, n: Nodo) -> Int: una función de C de lo de @link */
            Func f = {0};
            Token *name;
            if (accept(P_LP)) {
                expect(T_STR);
                expect(P_RP);
            }
            expect(K_FUNC);
            name = expect(T_ID);
            f.name = name->text;
            f.line = name->line;
            f.col = name->col;
            f.file = name->file;
            expect(P_LP);
            if (!accept(P_RP)) {
                do {
                    Param pa;
                    pa.name = expect(T_ID)->text;
                    pa.untyped = !accept(P_COLON);
                    pa.type = pa.untyped ? TY_INT : parse_type();
                    /* (un struct: su puntero, prestado mientras dura la llamada) */
                    if (pa.type != TY_INT && pa.type != TY_BOOL && pa.type != TY_STR &&
                        (pa.type < TY_NAMED || pa.type >= TY_ARR))
                        fatal_at(name->line, name->col, "@extern %s: sus parámetros son Int, Bool, String o un struct", f.name);
                    VEC_PUSH(f.params, pa);
                } while (accept(P_COMMA));
                expect(P_RP);
            }
            f.ret = TY_VOID;
            if (accept(P_ARROW)) f.ret = parse_type();
            /* (un struct: uno que el C toma de Dash, prestado: se sostiene al guardarlo, como el de una función) */
            if (f.ret != TY_VOID && f.ret != TY_INT && f.ret != TY_BOOL && f.ret != TY_STR &&
                (f.ret < TY_NAMED || f.ret >= TY_ARR))
                fatal_at(name->line, name->col, "@extern %s: devuelve Int, Bool, String, un struct o nada", f.name);
            f.declared = 1;
            f.native = 2;
            VEC_PUSH(p->funcs, f);
            continue;
        }
        if (t->kind == T_ID && !strcmp(t->text, "@export")) {
            /* @export func f(...): una función de Dash que el C de @link llama por su nombre */
            int n0 = p->funcs.n;
            if (peek()->kind != K_FUNC) fatal_at(t->line, t->col, "@export va delante de una func");
            parse_func(p, NULL);
            if (p->funcs.n > n0) p->funcs.v[p->funcs.n - 1].exported = 1;
            continue;
        }
        if (0)
            fatal_at(t->line, t->col, "(sin --gcc) %s aún no está", t->text);
        if (t->kind == T_ID && !strcmp(t->text, "@amiga")) {
            /* @amiga struct Nombre / campo: Tipo ... / end (A6) */
            AStruct as = {0};
            Token *name;
            if (next()->kind != K_STRUCT) fatal_at(t->line, t->col, "@amiga va delante de un struct");
            name = expect(T_ID);
            as.name = name->text;
            as.line = name->line;
            as.col = name->col;
            while (!accept(K_END)) {
                AField f = {0};
                Token *fn = expect(T_ID), *ty;
                f.name = fn->text;
                f.line = fn->line;
                f.col = fn->col;
                expect(P_COLON);
                ty = expect(T_ID);
                if (!strcmp(ty->text, "Ptr")) {
                    Token *x = expect(T_ID);
                    f.ftype = xmalloc(strlen(x->text) + 5);
                    sprintf(f.ftype, "Ptr %s", x->text);
                } else if (accept(P_LB)) {
                    Token *n = expect(T_INT);
                    expect(P_RB);
                    f.ftype = xmalloc(strlen(ty->text) + 24);
                    sprintf(f.ftype, "%s[%ld]", ty->text, n->val);
                } else {
                    f.ftype = ty->text;
                }
                VEC_PUSH(as.fields, f);
            }
            VEC_PUSH(p->amiga, as);
            continue;
        }
        if (t->kind == T_ID && t->text[0] == '@')
            fatal_at(t->line, t->col, "%s lleva C, y Dash 2.0 no admite C en los programas", t->text);
        if (t->kind == K_FUNC) {
            tk--;
            parse_func(p, NULL);
        } else if (t->kind == K_VAR) {
            Global g = {0};
            Token *name = expect(T_ID);
            g.name = name->text;
            g.line = name->line;
            g.col = name->col;
            g.file = name->file;
            expect(P_COLON);
            g.type = parse_type();
            g.init = accept(P_ASSIGN) ? expr() : zero_value(name, g.type);
            VEC_PUSH(p->globals, g);
        } else if (t->kind == K_CONST) {
            Const c = {0};
            Token *name = expect(T_ID);
            c.name = name->text;
            c.line = name->line;
            c.col = name->col;
            expect(P_ASSIGN);
            c.value = expr();
            VEC_PUSH(p->consts, c);
        } else if (t->kind == T_ID && !strcmp(t->text, "interface") && peek()->kind == T_ID) {
            /* interface Nombre / func metodo(params) -> Tipo / ... / end */
            Struct st = {0};
            Token *name = expect(T_ID);
            st.name = name->text;
            st.line = name->line;
            st.col = name->col;
            st.iface = 1;
            while (!accept(K_END)) {
                IfaceMethod m = {0};
                expect(K_FUNC);
                m.name = expect(T_ID)->text;
                expect(P_LP);
                if (!accept(P_RP)) {
                    do {
                        expect(T_ID);
                        if (accept(P_COLON)) parse_type();
                        m.nparams++;
                    } while (accept(P_COMMA));
                    expect(P_RP);
                }
                m.ret = accept(P_ARROW) ? parse_type() : TY_VOID;
                m.slot = p->nslots++;
                VEC_PUSH(st.methods, m);
            }
            VEC_PUSH(p->structs, st);
        } else if (t->kind == K_STRUCT) {
            Struct st = {0};
            Token *name = expect(T_ID);
            st.name = name->text;
            st.line = name->line;
            st.col = name->col;
            if (accept(P_COLON))                       /* struct Cuadro: Figura, Orden */
                do VEC_PUSH(st.ifaces, expect(T_ID)->text); while (accept(P_COMMA));
            while (!accept(K_END)) {
                Token *f = next();
                if (f->kind == K_FUNC) {
                    /* un método: la función "Struct.nombre" con self delante */
                    tk--;
                    parse_func(p, &st);
                } else if (f->kind == T_ID) {
                    Field fd = {0};
                    if (!strcmp(f->text, "weak") && peek()->kind == T_ID) {
                        fd.weak = 1;
                        f = next();
                    }
                    fd.name = f->text;
                    fd.line = f->line;
                    fd.col = f->col;
                    expect(P_COLON);
                    fd.type = parse_type();
                    if (accept(P_ASSIGN)) fd.init = expr();
                    VEC_PUSH(st.fields, fd);
                } else {
                    fatal_at(f->line, f->col, "no se esperaba \"%s\" en un struct", tok_name(f->kind));
                }
            }
            VEC_PUSH(p->structs, st);
        } else if (t->kind == K_MAIN) {
            if (p->has_main) fatal_at(t->line, t->col, "hay dos Main");
            p->has_main = 1;
            block(&p->main, K_END, K_END, K_END);
            expect(K_END);
        } else {
            fatal_at(t->line, t->col, "no se esperaba \"%s\" aquí", tok_name(t->kind));
        }
    }
}
