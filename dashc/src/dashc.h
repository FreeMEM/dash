/* dashc: prueba de concepto de un compilador de Dash autosuficiente.
   De un .dash saca un ejecutable de Amiga (formato Hunk) sin compilador de C:
   genera código 68000 y lo enlaza con el runtime, ya compilado y metido en dashc. */
#ifndef DASHC_H
#define DASHC_H

#include <stddef.h>
#include <stdint.h>

/* ---- utilidades (util.c) ---- */
typedef struct {
    uint8_t *p;
    size_t n, cap;
} Buf;

void buf_byte(Buf *b, int v);
void buf_word(Buf *b, int v);
void buf_long(Buf *b, uint32_t v);
void buf_bytes(Buf *b, const void *p, size_t n);
void put_word(uint8_t *p, int v);
void put_long(uint8_t *p, uint32_t v);
uint32_t get_long(const uint8_t *p);

void *xmalloc(size_t n);
void *xrealloc(void *p, size_t n);
char *xstrndup(const char *s, size_t n);

/* lista dinámica: struct { T *v; int n, cap; } */
#define VEC_PUSH(vec, x) do { \
        if ((vec).n == (vec).cap) { \
            (vec).cap = (vec).cap ? (vec).cap * 2 : 8; \
            (vec).v = xrealloc((vec).v, (vec).cap * sizeof(*(vec).v)); \
        } \
        (vec).v[(vec).n++] = (x); \
    } while (0)

extern const char *src_name;
void fatal(const char *fmt, ...);
void fatal_at(int line, int col, const char *fmt, ...);

/* ---- léxico (lexer.c) ---- */
enum {
    T_EOF, T_INT, T_STR, T_ID,
    /* palabras clave, en el orden de kw_names */
    K_FUNC, K_END, K_IF, K_ELIF, K_ELSE, K_WHILE, K_FOR, K_IN, K_STEP, K_RETURN,
    K_BREAK, K_CONTINUE, K_VAR, K_CONST, K_MAIN, K_PRINT, K_AND, K_OR, K_NOT,
    K_TRUE, K_FALSE, K_NIL, K_STRUCT,
    /* signos */
    P_LP, P_RP, P_COMMA, P_COLON, P_ASSIGN, P_EQ, P_NE, P_LT, P_LE, P_GT, P_GE,
    P_PLUS, P_MINUS, P_STAR, P_SLASH, P_PERCENT, P_AMP, P_BAR, P_CARET, P_TILDE,
    P_SHL, P_SHR, P_ARROW, P_DOTDOT, P_LB, P_RB, P_DOT,
    /* un texto con #{...}: trozos de texto y de código alternos */
    T_ISTR
};

typedef struct {
    int kind, line, col;
    long val;      /* T_INT */
    char *text;    /* T_ID; T_STR ya en Latin-1 y sin escapes */
    int len;
    /* T_ISTR: piece[0] texto, piece[1] código, piece[2] texto...; plen: largo de cada texto */
    char **piece;
    int *plen, npieces;
} Token;

Token *lex(const char *src);
const char *tok_name(int kind);

/* ---- árbol (parser.c) ---- */
enum {
    E_INT, E_STR, E_BOOL, E_VAR, E_CALL, E_BIN, E_CMP, E_NEG, E_BNOT, E_NOT, E_AND, E_OR,
    E_NIL,      /* nil */
    E_INDEX,    /* a[b] */
    E_SLICE,    /* a[b:c]; b o c pueden faltar (NULL) */
    E_FIELD,    /* a.name */
    E_MCALL,    /* a.name(args) */
    E_LIST,     /* [args] */
    E_INTERP,   /* "...#{x}...": args son los trozos (E_STR y expresiones) */
    S_ASSIGN, S_VAR, S_IF, S_WHILE, S_FOR, S_RETURN, S_BREAK, S_CONTINUE, S_PRINT, S_EXPR,
    S_STORE,    /* a = b con a un a[i] o un p.campo */
    S_FOREACH   /* for name in a */
};

/* Tipos: los básicos; un struct es TY_STRUCT + su número; una lista suma TY_ARR por cada nivel
   (Array sin más es una lista de Int). TY_NAMED + n: un nombre de tipo aún sin resolver
   (type_names[n]), que gen68k.c cambia por su struct. */
enum { TY_VOID, TY_INT, TY_BOOL, TY_STR, TY_CHAR, TY_NIL };
#define TY_STRUCT 16
#define TY_NAMED 0x8000
#define TY_ARR 0x10000
#define IS_STRUCT(t) ((t) >= TY_STRUCT && (t) < TY_NAMED)
#define IS_ARR(t) ((t) >= TY_ARR)
#define IS_OBJ(t) (IS_STRUCT(t) || IS_ARR(t))
extern struct TypeNames { char **v; int n, cap; } type_names;

typedef struct Node Node;
typedef struct { Node **v; int n, cap; } NodeList;

struct Node {
    int kind, line, col;
    int op;          /* E_BIN, E_CMP: el token del operador */
    long val;        /* E_INT, E_BOOL */
    char *name;      /* E_VAR, E_CALL, S_ASSIGN, S_VAR, S_FOR */
    char *str;       /* E_STR */
    int len;
    int type;        /* S_VAR: tipo declarado */
    Node *a, *b, *c; /* operandos; S_IF: a = condición; S_FOR: desde, hasta, paso */
    NodeList args;   /* E_CALL */
    NodeList body;   /* S_IF (rama sí), S_WHILE, S_FOR */
    NodeList els;    /* S_IF (rama no; un elif es un S_IF dentro) */
};

typedef struct {
    char *name;
    int type;
} Param;

typedef struct {
    char *name;
    int line, col;
    struct { Param *v; int n, cap; } params;
    int ret;         /* tipo que devuelve (sin "-> Tipo", lo deduce gen68k.c) */
    int declared;    /* con "-> Tipo" */
    int has_value;   /* tiene algún "return valor" */
    NodeList body;
} Func;

typedef struct {
    char *name;
    int line, col, type;
    Node *init;
} Global;

typedef struct {
    char *name;
    int line, col;
    Node *value;
} Const;

typedef struct {
    char *name;
    int line, col, type;
    Node *init;      /* valor por defecto, o NULL */
} Field;

/* Los métodos van en funcs como "Struct.metodo", con self de primer parámetro */
typedef struct {
    char *name;
    int line, col;
    struct { Field *v; int n, cap; } fields;
} Struct;

typedef struct {
    struct { Struct *v; int n, cap; } structs;
    struct { Func *v; int n, cap; } funcs;
    struct { Global *v; int n, cap; } globals;
    struct { Const *v; int n, cap; } consts;
    NodeList main;
    int has_main;
} Program;

Program *parse(Token *toks);

/* ---- código 68000 (gen68k.c) ---- */
enum { HK_CODE = 0, HK_DATA = 1 };

typedef struct {
    uint32_t off;      /* dónde está el long que hay que reubicar */
    int hunk;          /* HK_CODE o HK_DATA, o -1 si va a un símbolo del runtime */
    const char *sym;
} Reloc;

typedef struct {
    Buf code, data;
    struct { Reloc *v; int n, cap; } relocs;
} Obj;

void gen_program(Program *prog, Obj *obj);

/* ---- enlazado y ejecutable (hunk.c) ---- */
void link_exe(Obj *obj, const uint8_t *rt, size_t rtlen, const char *out);

#endif
