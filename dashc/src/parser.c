/* Parser de descenso recursivo. Sigue la gramática de compiler/grammar.py en el
   subconjunto de dashc: enteros, Bool, textos, listas, structs con métodos, variables,
   globales con var, const, funciones, if/elif/else, while, for con rango y sobre listas. */
#include <stdio.h>
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
    n->file = at->file;
    return n;
}

struct TypeNames type_names;

/* Int, Bool, String, Array o el nombre de un struct (que puede venir después: TY_NAMED) */
static int parse_type(void)
{
    Token *t;
    int i;
    if (accept(P_LB)) {
        /* [T]: lista de T */
        i = parse_type();
        expect(P_RB);
        return (i == TY_ARR + TY_VOID ? TY_ARR + TY_INT : i) + TY_ARR;
    }
    t = expect(T_ID);
    if (!strcmp(t->text, "Int")) return TY_INT;
    if (!strcmp(t->text, "Bool")) return TY_BOOL;
    if (!strcmp(t->text, "String")) return TY_STR;
    if (!strcmp(t->text, "Array")) return TY_ARR + TY_VOID;   /* lo que guarda, por su uso */
    if (!strcmp(t->text, "Float") || !strcmp(t->text, "Fixed") || !strcmp(t->text, "Pointer") ||
        !strcmp(t->text, "Func") || !strcmp(t->text, "Void"))
        fatal_at(t->line, t->col, "dashc (prueba): el tipo %s aún no está", t->text);
    for (i = 0; i < type_names.n; i++)
        if (!strcmp(type_names.v[i], t->text)) return TY_NAMED + i;
    VEC_PUSH(type_names, t->text);
    return TY_NAMED + type_names.n - 1;
}

/* ---- expresiones, de menos a más precedencia ---- */
static Node *expr(void);

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
    case T_ID:
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
        expect(P_ASSIGN);
        n->a = expr();
        return n;
    case T_ID: {
        Node *target;
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
            pa.type = accept(P_COLON) ? parse_type() : TY_INT;
            VEC_PUSH(f.params, pa);
        } while (accept(P_COMMA));
        expect(P_RP);
    }
    if (accept(P_ARROW)) {
        f.ret = parse_type();
        f.declared = 1;
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
   (la raíz de Dash, con lib/amiga) y a la carpeta actual */
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
    if (!full) fatal_at(at->line, at->col, "no encuentro %s para importarlo", path);
    if (strlen(path) > 7 && !strcmp(path + strlen(path) - 7, ".dashui"))
        fatal_at(at->line, at->col, "dashc (prueba): import de .dashui aún no está");
    for (i = 0; i < src_files.n; i++)
        if (!strcmp(src_files.v[i], full)) return;     /* ya importado */
    VEC_PUSH(src_files, full);
    lex_file = src_files.n - 1;
    src_name = full;
    tk = lex(text);
    parse_into(p);
    tk = saved_tk;
    src_name = saved_name;
    lex_file = saved_file;
}

Program *parse(Token *toks)
{
    Program *p = xmalloc(sizeof(Program));
    tk = toks;
    parse_into(p);
    if (!p->has_main) fatal("falta el bloque Main");
    return p;
}

static void parse_into(Program *p)
{
    while (peek()->kind != T_EOF) {
        Token *t = next();
        if (t->kind == T_ID && !strcmp(t->text, "import") && peek()->kind == T_STR) {
            import_file(p, t, next()->text);
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
        if (t->kind == K_FUNC) {
            tk--;
            parse_func(p, NULL);
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
        } else if (t->kind == K_STRUCT) {
            Struct st = {0};
            Token *name = expect(T_ID);
            st.name = name->text;
            st.line = name->line;
            st.col = name->col;
            while (!accept(K_END)) {
                Token *f = next();
                if (f->kind == K_FUNC) {
                    /* un método: la función "Struct.nombre" con self delante */
                    tk--;
                    parse_func(p, &st);
                } else if (f->kind == T_ID) {
                    Field fd = {0};
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
