/* Parser de descenso recursivo. Sigue la gramática de compiler/grammar.py en el
   subconjunto de la prueba: enteros, Bool, textos literales en Print, variables,
   globales con var, const, funciones, if/elif/else, while, for con rango. */
#include <string.h>

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
    return n;
}

static int parse_type(void)
{
    Token *t = expect(T_ID);
    if (!strcmp(t->text, "Int")) return TY_INT;
    if (!strcmp(t->text, "Bool")) return TY_BOOL;
    fatal_at(t->line, t->col, "dashc (prueba): el tipo %s aún no está (solo Int y Bool)", t->text);
    return TY_VOID;
}

/* ---- expresiones, de menos a más precedencia ---- */
static Node *expr(void);

static Node *primary(void)
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
    case K_TRUE:
    case K_FALSE:
        n = node(E_BOOL, t);
        n->val = t->kind == K_TRUE;
        return n;
    case T_ID:
        if (accept(P_LP)) {
            n = node(E_CALL, t);
            n->name = t->text;
            if (!accept(P_RP)) {
                do VEC_PUSH(n->args, expr()); while (accept(P_COMMA));
                expect(P_RP);
            }
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

static Node *compare_expr(void)
{
    Node *n = bor_expr();
    int k = peek()->kind;
    if (k == P_EQ || k == P_NE || k == P_LT || k == P_LE || k == P_GT || k == P_GE) {
        Token *op = next();
        n = binary(n, op, bor_expr());
        n->kind = E_CMP;
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
        expect(P_LP);
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
            if (cur_func->ret == TY_VOID) cur_func->ret = TY_INT;
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
        expect(P_ASSIGN);
        n->a = expr();
        return n;
    case T_ID:
        if (accept(P_ASSIGN)) {
            n = node(S_ASSIGN, t);
            n->name = t->text;
            n->a = expr();
            return n;
        }
        if (peek()->kind == P_LP) {
            tk--;
            n = node(S_EXPR, t);
            n->a = primary();
            return n;
        }
        break;
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

Program *parse(Token *toks)
{
    Program *p = xmalloc(sizeof(Program));
    tk = toks;
    while (peek()->kind != T_EOF) {
        Token *t = next();
        if (t->kind == K_FUNC) {
            Func f = {0};
            Token *name = expect(T_ID);
            f.name = name->text;
            f.line = name->line;
            f.col = name->col;
            expect(P_LP);
            if (!accept(P_RP)) {
                do {
                    Param pa;
                    pa.name = expect(T_ID)->text;
                    pa.type = accept(P_COLON) ? parse_type() : TY_INT;
                    VEC_PUSH(f.params, pa);
                } while (accept(P_COMMA));
                expect(P_RP);
            }
            if (accept(P_ARROW)) f.ret = parse_type();
            VEC_PUSH(p->funcs, f);
            cur_func = &p->funcs.v[p->funcs.n - 1];
            block(&cur_func->body, K_END, K_END, K_END);
            cur_func = NULL;
            expect(K_END);
        } else if (t->kind == K_VAR) {
            Global g = {0};
            Token *name = expect(T_ID);
            g.name = name->text;
            g.line = name->line;
            g.col = name->col;
            expect(P_COLON);
            g.type = parse_type();
            expect(P_ASSIGN);
            g.init = expr();
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
        } else if (t->kind == K_MAIN) {
            if (p->has_main) fatal_at(t->line, t->col, "hay dos Main");
            p->has_main = 1;
            block(&p->main, K_END, K_END, K_END);
            expect(K_END);
        } else {
            fatal_at(t->line, t->col, "no se esperaba \"%s\" aquí", tok_name(t->kind));
        }
    }
    if (!p->has_main) fatal("falta el bloque Main");
    return p;
}
