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

extern const char *src_name;   /* el fichero de los errores de ahora (fatal_at) */
/* los ficheros del programa: el principal y los importados (en los errores al ejecutar, por número) */
extern struct SrcFiles { const char **v; int n, cap; } src_files;
extern int lex_file;            /* el número del fichero que se está leyendo (Token.file) */
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
    P_SHL, P_SHR, P_ARROW, P_DOTDOT, P_LB, P_RB, P_DOT, P_LBRACE, P_RBRACE,
    /* un texto con #{...}: trozos de texto y de código alternos */
    T_ISTR,
    T_FLOAT   /* val: los bits del float (IEEE de 32 bits) */
};

typedef struct {
    int kind, line, col, file;
    long val;      /* T_INT */
    double dval;   /* T_FLOAT: el valor entero (un Double lo quiere con todas sus cifras) */
    char *text;    /* T_ID; T_STR ya en Latin-1 y sin escapes */
    int len;
    /* T_ISTR: piece[0] texto, piece[1] código, piece[2] texto...; plen: largo de cada texto */
    char **piece;
    int *plen, npieces;
} Token;

Token *lex(const char *src);
extern const char **lex_priv;  /* los nombres privados del módulo que se lee (rename_private) */
extern int lex_npriv;
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
    E_DICT,     /* {k: v, ...}: args son clave, valor, clave, valor... */
    E_FLOAT,    /* val: los bits del float */
    E_FUNCREF,  /* name: una función como valor (Func), su dirección */
    E_NN,       /* a, comprobando que no es nil (lo pone gen68k.c en las llamadas a métodos) */
    S_ASSIGN, S_VAR, S_IF, S_WHILE, S_FOR, S_RETURN, S_BREAK, S_CONTINUE, S_PRINT, S_EXPR,
    S_STORE,    /* a = b con a un a[i] o un p.campo */
    S_FOREACH,  /* for name in a */
    S_WINDOW,   /* Ventana.open (val 1) o .close (val 0): name es la ventana */
    S_EVLOOP,   /* EventLoop: body son los S_ON */
    S_ON,       /* On ...: val el evento (ON_*); a, la tecla o el intervalo; body */
    S_STOP      /* Stop: acaba el EventLoop */
};

/* Tipos: los básicos; un struct es TY_STRUCT + su número; una lista suma TY_ARR por cada nivel
   (Array sin más es TY_ARR + TY_VOID: lo que guarda se deduce, o Int). TY_NAMED + n: un nombre de tipo aún sin resolver
   (type_names[n]), que gen68k.c cambia por su struct. */
enum { TY_VOID, TY_INT, TY_BOOL, TY_STR, TY_CHAR, TY_NIL, TY_FLOAT, TY_DOUBLE, TY_FIXED };
/* un Double es, en dashc, una caja: un texto con sus 8 bytes en hexadecimal (runtime/api.c, dl_d_*); su
   variable, campo o elemento es dueño de ella como de un texto */
#define IS_STRLIKE(t) ((t) == TY_STR || (t) == TY_DOUBLE)
long float_bits(double d);   /* lexer.c: los bits del float de 32 bits más cercano */
#define TY_STRUCT 16
#define TY_DICT 0x4000   /* + n: dict_types.v[n] */
#define TY_NAMED 0x8000
#define TY_ARR 0x10000
#define IS_STRUCT(t) ((t) >= TY_STRUCT && (t) < TY_DICT)
#define IS_DICT(t) ((t) >= TY_DICT && (t) < TY_NAMED)
#define IS_ARR(t) ((t) >= TY_ARR)
#define IS_OBJ(t) (IS_STRUCT(t) || IS_DICT(t) || IS_ARR(t))
/* los diccionarios {K: V}: la clave (TY_STR o TY_INT) y el valor de cada uno */
typedef struct { int key, val; } DictType;
extern struct DictTypes { DictType *v; int n, cap; } dict_types;
int dict_type(int key, int val);
extern struct TypeNames { char **v; int n, cap; } type_names;

typedef struct Node Node;
typedef struct { Node **v; int n, cap; } NodeList;

struct Node {
    int kind, line, col, file;
    int op;          /* E_BIN, E_CMP: el token del operador */
    long val;        /* E_INT, E_BOOL */
    double dval;     /* E_FLOAT */
    char *name;      /* E_VAR, E_CALL, S_ASSIGN, S_VAR, S_FOR */
    char *str;       /* E_STR */
    int len;
    int type;        /* S_VAR: tipo declarado; E_LIST: lo que guarda, si lo dice su destino ([Double]) */
    Node *a, *b, *c; /* operandos; S_IF: a = condición; S_FOR: desde, hasta, paso */
    NodeList args;   /* E_CALL */
    NodeList body;   /* S_IF (rama sí), S_WHILE, S_FOR */
    NodeList els;    /* S_IF (rama no; un elif es un S_IF dentro) */
};

typedef struct {
    char *name;
    int type;
    int untyped;     /* sin ": Tipo": el de lo que se le pasa en la primera llamada (Int si es un número) */
} Param;

typedef struct {
    char *name;
    int line, col, file;
    struct { Param *v; int n, cap; } params;
    int ret;         /* tipo que devuelve (sin "-> Tipo", lo deduce gen68k.c) */
    int declared;    /* con "-> Tipo" */
    int has_value;   /* tiene algún "return valor" */
    int native;      /* 1, @native: su C va en la librería de dashc (solo los de lib/amiga); 2, @extern: de @link */
    int boolret;     /* una lambda "fn(a, b) -> a < b": da un Bool (sort: si a va antes que b) */
    NodeList body;
} Func;

typedef struct {
    char *name;
    int line, col, type, file;   /* file: las del programa (0) no se ven desde sus módulos */
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
    int weak;        /* weak padre: Nodo: apunta sin sostener (sin referencia) */
} Field;

/* Un método de una interfaz: su posición en la tabla de métodos de los structs (slot, única en el programa) */
typedef struct {
    char *name;
    int ret, nparams, slot;
} IfaceMethod;

/* Los métodos van en funcs como "Struct.metodo", con self de primer parámetro. Una interfaz es un Struct sin
   campos con iface y sus métodos; un struct dice las que cumple en ifaces. */
typedef struct {
    char *name;
    int line, col;
    struct { Field *v; int n, cap; } fields;
    int iface;
    struct { IfaceMethod *v; int n, cap; } methods;   /* (de una interfaz) */
    struct { char **v; int n, cap; } ifaces;          /* (de un struct: los nombres de sus interfaces) */
} Struct;

typedef struct {
    char *name;
    struct { char **v; int n, cap; } names;
    struct { long *v; int n, cap; } vals;
} Enum;

enum { ON_CLOSE, ON_KEY, ON_CLICK, ON_TIMER, ON_GADGET, ON_MENU };

/* Window Nombre ... end: sus propiedades (title, width...), cada una con su valor */
typedef struct {
    char *name;
    int line, col;
    NodeList props;   /* E_* con name = la propiedad */
} WindowDef;

typedef struct {
    struct { WindowDef *v; int n, cap; } windows;
    struct { Enum *v; int n, cap; } enums;
    struct { Struct *v; int n, cap; } structs;
    struct { Func *v; int n, cap; } funcs;
    struct { Global *v; int n, cap; } globals;
    struct { Const *v; int n, cap; } consts;
    NodeList main;
    int has_main;
    char *version;   /* @version: lo que va tras "$VER: " */
    char *catalog, *catalog_lang;   /* @catalog "X.catalog" versión "idioma propio" */
    long catalog_version;
    char *wb_output;  /* @workbench_output "NIL:": desde el Workbench, en vez de la consola */
    int wb_output_main;
    long stack_min;  /* @stack N: al menos esa pila */
    int nslots;      /* los métodos de interfaz del programa (tamaño de la tabla de métodos de un struct) */
} Program;

Program *parse(Token *toks);
char *dashui_generate(const char *json, const char *filename);   /* dashui.c: un .dashui como Dash */
char *read_text(const char *path);   /* main.c: el fichero entero, o NULL */
int runtime_has(const char *sym);    /* hunk.c: ¿define el runtime este símbolo? */
extern const uint8_t *rt_blob;       /* main.c: el runtime que se va a enlazar */
extern size_t rt_blob_len;

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
extern int memcheck;   /* --memcheck: como ./dash --memcheck */

/* builtins (build/builtins_tab.c): ret 0 nada, 1 Int, 2 Bool, 3 String, 4 [String]; keeps: guarda lo
   que recibe (un texto o un objeto pasa escapado) */
/* ret: 0 nada, 1 Int, 2 Bool, 3 String, 4 [String], 5 Double; dparams: los parámetros Double (bits) */
typedef struct { const char *name; unsigned char nparams, ret, keeps, dparams; } BuiltinInfo;
extern const BuiltinInfo builtin_info[];
extern const int builtin_count;
typedef struct { const char *name; int code; } KeyName;
extern const KeyName key_names[];

/* ---- enlazado y ejecutable (hunk.c) ---- */
void link_exe(Obj *obj, const uint8_t *rt, size_t rtlen, const char *out);
void link_add(const char *path);     /* @link: un objeto o una biblioteca más que enlazar */

#endif
