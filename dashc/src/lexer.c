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

/* Los textos van en Latin-1, como en el Amiga (en DashOS, en UTF-8): de UTF-8 se pasan los caracteres
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
            t->plen[t->npieces] = (int)b.n;
            t->piece[t->npieces] = buf_text(&b);
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
#ifdef DASH_A64
        /* DashOS: los textos van en UTF-8 (los de un fuente en Latin-1 se pasan) */
        if (c >= 0x80 && lex_latin1) {
            buf_byte(&b, 0xC0 | c >> 6);
            buf_byte(&b, 0x80 | (c & 0x3F));
            s++;
            continue;
        }
        if (c >= 0x80) {
            buf_byte(&b, c);
            s++;
            continue;
        }
#endif
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
    {
        char *text = buf_text(&b);
        if (t->kind == T_ISTR) {
            /* el último trozo de texto */
            t->piece = xrealloc(t->piece, sizeof(char *) * (t->npieces + 1));
            t->plen = xrealloc(t->plen, sizeof(int) * (t->npieces + 1));
            t->piece[t->npieces] = text;
            t->plen[t->npieces] = *len;
            t->npieces++;
        }
        return text;
    }
}

/* Los nombres, una sola copia de cada uno para todo el programa (con Forja, 43.000 nombres en el fuente, de unos
   pocos miles distintos): nadie los cambia ni los suelta. Van de corrido en bloques de 16 KB, sin cabecera. */
static struct { const char **v; unsigned cap, n; } names;

static const char *intern(const char *b, size_t n)
{
    static char *at, *end;
    unsigned h = 5381, i;
    size_t k;
    char *d;
    for (k = 0; k < n; k++) h = ((h << 5) + h) ^ (unsigned char)b[k];   /* (sin multiplicar) */
    if ((names.n + 1) * 2 > names.cap) {
        const char **old = names.v;
        unsigned oc = names.cap, j;
        names.cap = oc ? oc * 2 : 1024;
        names.v = xmalloc(sizeof(char *) * names.cap);
        for (j = 0; j < oc; j++)
            if (old[j]) {
                unsigned g = 5381;
                const unsigned char *q = (const unsigned char *)old[j];
                while (*q) g = ((g << 5) + g) ^ *q++;
                for (i = g & (names.cap - 1); names.v[i]; i = (i + 1) & (names.cap - 1)) {}
                names.v[i] = old[j];
            }
        xfree(old);
    }
    for (i = h & (names.cap - 1); names.v[i]; i = (i + 1) & (names.cap - 1))
        if (!strncmp(names.v[i], b, n) && !names.v[i][n]) return names.v[i];
    if ((size_t)(end - at) < n + 1) {
        size_t sz = n + 1 > 16384 ? n + 1 : 16384;
        at = xmalloc(sz);
        end = at + sz;
    }
    d = at;
    for (k = 0; k < n; k++) d[k] = b[k];              /* (sin memcpy: CopyMem de exec, caro para tan poco) */
    d[n] = 0;
    at += n + 1;
    names.v[i] = d;
    names.n++;
    return d;
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
                t[i].len = (int)strlen(n);
                t[i].text = (char *)intern(n, (size_t)t[i].len);
                xfree(n);
                break;
            }
    }
}

/* los nombres privados en unos tokens ya leídos (lo mismo que leerlos otra vez con lex_priv puesto) */
void lex_rename_private(Token *t) { rename_private(t); }

/* Cuántos tokens puede tener src, por arriba: cada nombre o número, cada signo y cada texto, sin los comentarios. Antes
   se pedía sitio para uno cada 5 caracteres: en un fuente con textos largos (los datos de Forja) eran megas de más,
   a la vez que el árbol. (Si se queda corto, lex crece.) */
static int count_tokens(const char *s)
{
    int n = 0;
    while (*s) {
        unsigned char c = (unsigned char)*s;
        if (c == ' ' || c == '\t' || c == '\r' || c == '\n') s++;
        else if (c == '#') {
            while (*s && *s != '\n') s++;
        } else if (c == '"') {
            n++;
            if (s[1] == '"' && s[2] == '"') {
                const char *e = strstr(s + 3, "\"\"\"");
                s = e ? e + 3 : s + strlen(s);
            } else {
                /* (un texto con #{...}: sus trozos de código se leen aparte, con su propio lex) */
                for (s++; *s && *s != '"' && *s != '\n'; s++)
                    if (*s == '\\' && s[1]) s++;
                if (*s == '"') s++;
            }
        } else if (isalnum(c) || c == '_' || c == '@' || c == '$') {
            n++;                                       /* (1.5 cuenta tres: mejor de más) */
            while (isalnum((unsigned char)*s) || *s == '_' || *s == '@' || *s == '$') s++;
        } else {
            n++;
            s++;
        }
    }
    return n;
}

Token *lex(const char *src)
{
    TokVec toks = {0};
    const char *s, *line_start;
    int line = 1;

    if (!strncmp(src, "\xEF\xBB\xBF", 3)) src += 3;   /* la marca de UTF-8 de los editores de Windows */
    lex_latin1 = !valid_utf8((const unsigned char *)src);
    s = line_start = src;
    /* sitio para los tokens de una vez, sin copiarlos al crecer: cuántos puede haber como mucho (count_tokens) */
    toks.cap = count_tokens(src) + 16;
    toks.v = xmalloc(sizeof(Token) * toks.cap);

    for (;;) {
        Token *t;
        /* (el token se escribe en su sitio, ya a 0: copiar uno entero cada vez costaba en el 68000) */
        if (toks.n == toks.cap) {
            toks.cap *= 2;
            toks.v = xrealloc(toks.v, sizeof(Token) * toks.cap);
        }
        t = &toks.v[toks.n];
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
        t->line = line;
        t->file = (unsigned short)lex_file;
        t->col = (unsigned short)(s - line_start + 1 > 65535 ? 65535 : s - line_start + 1);
        if (!*s) {
            t->kind = T_EOF;
            toks.n++;
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
                v = (base == 10 ? (v << 3) + (v << 1) : base == 16 ? v << 4 : v << 1) + d;   /* (v * base sin multiplicar) */
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
                t->kind = T_FLOAT;
                t->val = float_bits(d);
                t->dval = d;
            } else {
                t->kind = T_INT;
                t->val = (long)(int32_t)(uint32_t)v;
            }
        } else if (isalpha((unsigned char)*s) || *s == '_') {
            const char *b = s;
            int i;
            /* las palabras clave por su primera letra, en su orden (kw_first: la primera; kw_next: la siguiente con
               esa letra; 0 ninguna, si no el número + 1) */
            static unsigned char kw_len[32], kw_first[256], kw_next[32];
            while (isalnum((unsigned char)*s) || *s == '_') s++;
            t->kind = T_ID;
            if (!kw_len[0])
                for (i = 0; kw_names[i]; i++) {
                    unsigned char c = (unsigned char)kw_names[i][0];
                    kw_len[i] = (unsigned char)strlen(kw_names[i]);
                    if (!kw_first[c]) kw_first[c] = (unsigned char)(i + 1);
                    else {
                        int k = kw_first[c] - 1;
                        while (kw_next[k]) k = kw_next[k] - 1;
                        kw_next[k] = (unsigned char)(i + 1);
                    }
                }
            if (s - b <= 8)                            /* (ninguna palabra clave es más larga: "continue") */
                for (i = kw_first[(unsigned char)*b] - 1; i >= 0; i = kw_next[i] - 1)
                    if (s - b == kw_len[i] && !memcmp(b, kw_names[i], s - b)) {
                        t->kind = K_FUNC + i;
                        break;
                    }
            /* step solo es palabra clave en un for: fuera, un nombre más (un parámetro step; lo vio Fragua) */
            if (t->kind == K_STEP) t->kind = T_ID;
            if (t->kind == T_ID) {
                t->text = (char *)intern(b, s - b);
                t->len = (int)(s - b);
            }
        } else if (s[0] == '"' && s[1] == '"' && s[2] == '"') {
            /* """...""": el C de un @native, tal cual y con sus líneas */
            const char *b = s + 3, *e = strstr(b, "\"\"\"");
            if (!e) fatal_at(t->line, t->col, "falta el \"\"\" que cierra");
            t->kind = T_STR;
            t->text = xstrndup(b, e - b);
            t->len = (int)(e - b);
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
            t->kind = T_ID;
            t->text = (char *)intern(b, s - b);
            t->len = (int)(s - b);
        } else if (*s == '"') {
            t->kind = T_STR;
            t->text = lex_string(&s, t->line, t->col, &t->len, t);
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
            int i, k;
            /* (por el carácter: one_of[c] es su signo + 1; two_of[c], el primero de two que empieza por c, + 1) */
            static unsigned char one_of[256], two_of[256], ready;
            if (!ready) {
                ready = 1;
                for (i = 0; one[i]; i++)
                    if (!one_of[(unsigned char)one[i]]) one_of[(unsigned char)one[i]] = (unsigned char)(i + 1);
                for (i = 0; two[i].p; i++)
                    if (!two_of[(unsigned char)two[i].p[0]]) two_of[(unsigned char)two[i].p[0]] = (unsigned char)(i + 1);
            }
            k = -1;
            if (two_of[(unsigned char)*s])
                for (i = two_of[(unsigned char)*s] - 1; two[i].p; i++)
                    if (s[0] == two[i].p[0] && s[1] == two[i].p[1]) {
                        k = two[i].k;
                        s += 2;
                        break;
                    }
            if (k < 0 && *s && one_of[(unsigned char)*s]) {
                k = one_k[one_of[(unsigned char)*s] - 1];
                s++;
            }
            if (k < 0) fatal_at(t->line, t->col, "carácter inesperado '%c'", *s);
            t->kind = (unsigned char)k;
        }
        toks.n++;
    }
    rename_private(toks.v);
    return toks.v;
}
