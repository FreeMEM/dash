#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "dashc.h"

int dash_ryu_s2d(const char *s, int len, double *out);   /* runtime/ryu/dash_ryu.c */

static const char *kw_names[] = {
    "func", "end", "if", "elif", "else", "while", "for", "in", "step", "return",
    "break", "continue", "var", "const", "Main", "Print", "and", "or", "not",
    "true", "false", "nil", "struct", NULL
};

static const char *punct_names[] = {
    "(", ")", ",", ":", "=", "==", "!=", "<", "<=", ">", ">=",
    "+", "-", "*", "/", "%", "&", "|", "^", "~", "<<", ">>", "->", "..", "[", "]", ".", "{", "}",
    "un texto", "un número con decimales"
};

const char *tok_name(int kind)
{
    switch (kind) {
    case T_EOF: return "el final del fichero";
    case T_INT: return "un número";
    case T_STR: return "un texto";
    case T_ID: return "un nombre";
    }
    if (kind >= K_FUNC && kind <= K_STRUCT) return kw_names[kind - K_FUNC];
    return punct_names[kind - P_LP];
}

typedef struct { Token *v; int n, cap; } TokVec;

long float_bits(double d)
{
    union { float f; uint32_t u; } x;
    x.f = (float)d;
    return (long)(int32_t)x.u;
}

/* un fuente que no es UTF-8 válido está en Latin-1, el del Amiga (Forja, los editores del Amiga): cada byte es
   su carácter (como ./dash) */
static int lex_latin1;

int valid_utf8(const unsigned char *s)
{
    while (*s) {
        int n = *s < 0x80 ? 0 : (*s & 0xE0) == 0xC0 ? 1 : (*s & 0xF0) == 0xE0 ? 2 : (*s & 0xF8) == 0xF0 ? 3 : -1;
        if (n < 0 || (n == 1 && *s < 0xC2)) return 0;
        for (s++; n > 0; n--, s++)
            if ((*s & 0xC0) != 0x80) return 0;
    }
    return 1;
}

/* Los textos van en Latin-1, como en el Amiga: de UTF-8 se pasan los caracteres
   de U+0080 a U+00FF; los demás quedan como "?". Un #{...} corta el texto: t recibe
   los trozos (texto, código, texto...) y el token pasa a T_ISTR. */
static char *lex_string(const char **ps, int line, int col, int *len, Token *t)
{
    const char *s = *ps + 1;
    Buf b = {0};
    for (;;) {
        unsigned char c = (unsigned char)*s;
        if (!c || c == '\n') fatal_at(line, col, "texto sin cerrar");
        if (c == '"') break;
        if (c == '#' && s[1] == '{') {
            const char *e = s + 2;
            int depth = 1;
            /* hasta la } que cierra (puede haber textos y llaves dentro) */
            while (*e && *e != '\n') {
                if (*e == '\\' && e[1]) {
                    e += 2;                            /* \" dentro de #{...}: unas comillas */
                    continue;
                }
                if (*e == '"') {
                    e++;
                    while (*e && *e != '"' && *e != '\n') e += *e == '\\' && e[1] ? 2 : 1;
                } else if (*e == '{') {
                    depth++;
                } else if (*e == '}' && --depth == 0) {
                    break;
                }
                if (*e) e++;
            }
            if (*e != '}') {
                /* "#{" sin cerrar: texto, como en ./dash */
                buf_byte(&b, '#');
                s++;
                continue;
            }
            t->piece = xrealloc(t->piece, sizeof(char *) * (t->npieces + 2));
            t->plen = xrealloc(t->plen, sizeof(int) * (t->npieces + 2));
            buf_byte(&b, 0);
            t->piece[t->npieces] = (char *)b.p;
            t->plen[t->npieces] = (int)b.n - 1;
            {
                /* el código, con \" y \\ ya como " y \ */
                char *code = xstrndup(s + 2, e - (s + 2)), *r = code, *w2 = code;
                while (*r) {
                    if (*r == '\\' && (r[1] == '"' || r[1] == '\\')) r++;
                    *w2++ = *r++;
                }
                *w2 = 0;
                t->piece[t->npieces + 1] = code;
            }
            t->plen[t->npieces + 1] = 0;
            t->npieces += 2;
            memset(&b, 0, sizeof b);
            t->kind = T_ISTR;
            s = e + 1;
            continue;
        }
        if (c == '\\') {
            s++;
            switch (*s) {
            case 'n': buf_byte(&b, '\n'); break;
            case 't': buf_byte(&b, '\t'); break;
            case 'r': buf_byte(&b, '\r'); break;
            case '\\': buf_byte(&b, '\\'); break;
            case '"': buf_byte(&b, '"'); break;
            case '\'': buf_byte(&b, '\''); break;
            case 'a': buf_byte(&b, 7); break;
            case 'b': buf_byte(&b, 8); break;
            case 'e': buf_byte(&b, 27); break;
            case 'f': buf_byte(&b, 12); break;
            case 'v': buf_byte(&b, 11); break;
            case 'x': {
                /* \x1b: hexadecimal, como en C (el texto va tal cual al C de ./dash) */
                int v = 0, k = 0;
                while (k < 2 && isxdigit((unsigned char)s[1])) {
                    s++;
                    v = v * 16 + (isdigit((unsigned char)*s) ? *s - '0' : (tolower((unsigned char)*s) - 'a' + 10));
                    k++;
                }
                if (!k) fatal_at(line, col, "\\x sin cifras");
                buf_byte(&b, v);
                break;
            }
            default:
                if (*s >= '0' && *s <= '7') {
                    /* \33, \0: octal, hasta tres cifras */
                    int v = *s - '0', k = 1;
                    while (k < 3 && s[1] >= '0' && s[1] <= '7') {
                        s++;
                        v = v * 8 + (*s - '0');
                        k++;
                    }
                    buf_byte(&b, v & 255);
                    break;
                }
                fatal_at(line, col, "escape \\%c no admitido", *s);
            }
            s++;
            continue;
        }
        if (c < 0x80 || lex_latin1) {
            buf_byte(&b, c);
            s++;
        } else if ((c & 0xE0) == 0xC0 && ((unsigned char)s[1] & 0xC0) == 0x80) {
            int cp = (c & 0x1F) << 6 | ((unsigned char)s[1] & 0x3F);
            buf_byte(&b, cp < 0x100 ? cp : '?');
            s += 2;
        } else {
            /* secuencias de 3 o 4 bytes: fuera de Latin-1 */
            buf_byte(&b, '?');
            s++;
            while (((unsigned char)*s & 0xC0) == 0x80) s++;
        }
    }
    *ps = s + 1;
    *len = (int)b.n;
    buf_byte(&b, 0);
    if (t->kind == T_ISTR) {
        /* el último trozo de texto */
        t->piece = xrealloc(t->piece, sizeof(char *) * (t->npieces + 1));
        t->plen = xrealloc(t->plen, sizeof(int) * (t->npieces + 1));
        t->piece[t->npieces] = (char *)b.p;
        t->plen[t->npieces] = *len;
        t->npieces++;
    }
    return (char *)b.p;
}

/* los nombres privados (`_x`) de un módulo: se leen con su sufijo (`_x__m2`), para que dos módulos y el
   programa puedan tener cada uno el suyo (como ./dash) */
const char **lex_priv;
int lex_npriv;
static void rename_private(Token *t)
{
    int i, j;
    char buf[32];
    if (!lex_npriv) return;
    snprintf(buf, sizeof buf, "__m%d", lex_file);
    for (i = 0; t[i].kind != T_EOF; i++) {
        if (t[i].kind != T_ID || t[i].text[0] != '_' || (i && t[i - 1].kind == P_DOT)) continue;
        for (j = 0; j < lex_npriv; j++)
            if (!strcmp(lex_priv[j], t[i].text)) {
                char *n = xmalloc(strlen(t[i].text) + strlen(buf) + 1);
                strcpy(n, t[i].text);
                strcat(n, buf);
                t[i].text = n;
                t[i].len = (int)strlen(n);
                break;
            }
    }
}

Token *lex(const char *src)
{
    TokVec toks = {0};
    const char *s, *line_start;
    int line = 1;

    if (!strncmp(src, "\xEF\xBB\xBF", 3)) src += 3;   /* la marca de UTF-8 de los editores de Windows */
    lex_latin1 = !valid_utf8((const unsigned char *)src);
    s = line_start = src;

    for (;;) {
        Token t = {0};
        while (*s == ' ' || *s == '\t' || *s == '\r' || *s == '\n' || *s == '#') {
            if (*s == '#') {
                while (*s && *s != '\n') s++;
                continue;
            }
            if (*s == '\n') {
                line++;
                line_start = s + 1;
            }
            s++;
        }
        t.line = line;
        t.file = lex_file;
        t.col = (int)(s - line_start) + 1;
        if (!*s) {
            t.kind = T_EOF;
            VEC_PUSH(toks, t);
            break;
        }

        if (isdigit((unsigned char)*s) || (*s == '$' && isxdigit((unsigned char)s[1]))) {
            const char *b = s;
            unsigned long v = 0;
            int base = 10;
            if (*s == '$') { base = 16; s++; }
            else if (s[0] == '0' && (s[1] == 'x' || s[1] == 'X')) { base = 16; s += 2; }
            else if (s[0] == '0' && (s[1] == 'b' || s[1] == 'B')) { base = 2; s += 2; }
            for (;;) {
                int d;
                char c = *s;
                if (c >= '0' && c <= '9') d = c - '0';
                else if (base == 16 && c >= 'a' && c <= 'f') d = c - 'a' + 10;
                else if (base == 16 && c >= 'A' && c <= 'F') d = c - 'A' + 10;
                else break;
                if (d >= base) break;
                v = v * base + d;
                s++;
            }
            if (base == 10 && *s == '.' && isdigit((unsigned char)s[1])) {
                /* 1.5, 2.0e3: un Float */
                char *end;
                double d = strtod(b, &end), exact;
                /* (el double más cercano, con Ryu: el strtod de libnix, en el Amiga, falla a veces en la
                   última cifra; con más de 17 cifras, el de strtod) */
                if (!dash_ryu_s2d(b, (int)(end - b), &exact)) d = exact;
                s = end;
                t.kind = T_FLOAT;
                t.val = float_bits(d);
                t.dval = d;
            } else {
                t.kind = T_INT;
                t.val = (long)(int32_t)(uint32_t)v;
            }
        } else if (isalpha((unsigned char)*s) || *s == '_') {
            const char *b = s;
            int i;
            while (isalnum((unsigned char)*s) || *s == '_') s++;
            t.kind = T_ID;
            for (i = 0; kw_names[i]; i++)
                if ((size_t)(s - b) == strlen(kw_names[i]) && !memcmp(b, kw_names[i], s - b)) {
                    t.kind = K_FUNC + i;
                    break;
                }
            if (t.kind == T_ID) {
                t.text = xstrndup(b, s - b);
                t.len = (int)(s - b);
            }
        } else if (s[0] == '"' && s[1] == '"' && s[2] == '"') {
            /* """...""": el C de un @native, tal cual y con sus líneas */
            const char *b = s + 3, *e = strstr(b, "\"\"\"");
            if (!e) fatal_at(t.line, t.col, "falta el \"\"\" que cierra");
            t.kind = T_STR;
            t.text = xstrndup(b, e - b);
            t.len = (int)(e - b);
            for (s = b; s < e; s++)
                if (*s == '\n') {
                    line++;
                    line_start = s + 1;
                }
            s = e + 3;
        } else if (*s == '@' && (isalpha((unsigned char)s[1]))) {
            /* @native, @header...: un nombre con su @ */
            const char *b = s++;
            while (isalnum((unsigned char)*s) || *s == '_') s++;
            t.kind = T_ID;
            t.text = xstrndup(b, s - b);
            t.len = (int)(s - b);
        } else if (*s == '"') {
            t.kind = T_STR;
            t.text = lex_string(&s, t.line, t.col, &t.len, &t);
        } else {
            /* los signos de dos caracteres primero */
            static const struct { const char *p; int k; } two[] = {
                {"==", P_EQ}, {"!=", P_NE}, {"<=", P_LE}, {">=", P_GE}, {"<<", P_SHL},
                {">>", P_SHR}, {"->", P_ARROW}, {"..", P_DOTDOT}, {NULL, 0}
            };
            static const char one[] = "(),:=<>+-*/%&|^~[].{}";
            static const int one_k[] = {
                P_LP, P_RP, P_COMMA, P_COLON, P_ASSIGN, P_LT, P_GT, P_PLUS, P_MINUS,
                P_STAR, P_SLASH, P_PERCENT, P_AMP, P_BAR, P_CARET, P_TILDE, P_LB, P_RB, P_DOT,
                P_LBRACE, P_RBRACE
            };
            int i;
            const char *p;
            t.kind = -1;
            for (i = 0; two[i].p; i++)
                if (s[0] == two[i].p[0] && s[1] == two[i].p[1]) {
                    t.kind = two[i].k;
                    s += 2;
                    break;
                }
            if (t.kind < 0 && *s && (p = strchr(one, *s)) != NULL) {
                t.kind = one_k[p - one];
                s++;
            }
            if (t.kind < 0) fatal_at(t.line, t.col, "carácter inesperado '%c'", *s);
        }
        VEC_PUSH(toks, t);
    }
    rename_private(toks.v);
    return toks.v;
}
