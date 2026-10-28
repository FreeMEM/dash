#include <ctype.h>
#include <string.h>

#include "dashc.h"

static const char *kw_names[] = {
    "func", "end", "if", "elif", "else", "while", "for", "in", "step", "return",
    "break", "continue", "var", "const", "Main", "Print", "and", "or", "not",
    "true", "false", NULL
};

static const char *punct_names[] = {
    "(", ")", ",", ":", "=", "==", "!=", "<", "<=", ">", ">=",
    "+", "-", "*", "/", "%", "&", "|", "^", "~", "<<", ">>", "->", ".."
};

const char *tok_name(int kind)
{
    switch (kind) {
    case T_EOF: return "el final del fichero";
    case T_INT: return "un número";
    case T_STR: return "un texto";
    case T_ID: return "un nombre";
    }
    if (kind >= K_FUNC && kind <= K_FALSE) return kw_names[kind - K_FUNC];
    return punct_names[kind - P_LP];
}

typedef struct { Token *v; int n, cap; } TokVec;

/* Los textos van en Latin-1, como en el Amiga: de UTF-8 se pasan los caracteres
   de U+0080 a U+00FF; los demás quedan como "?". */
static char *lex_string(const char **ps, int line, int col, int *len)
{
    const char *s = *ps + 1;
    Buf b = {0};
    for (;;) {
        unsigned char c = (unsigned char)*s;
        if (!c || c == '\n') fatal_at(line, col, "texto sin cerrar");
        if (c == '"') break;
        if (c == '#' && s[1] == '{')
            fatal_at(line, col, "dashc (prueba): la interpolación #{...} aún no está");
        if (c == '\\') {
            s++;
            switch (*s) {
            case 'n': buf_byte(&b, '\n'); break;
            case 't': buf_byte(&b, '\t'); break;
            case 'r': buf_byte(&b, '\r'); break;
            case '\\': buf_byte(&b, '\\'); break;
            case '"': buf_byte(&b, '"'); break;
            default: fatal_at(line, col, "escape \\%c no admitido", *s);
            }
            s++;
            continue;
        }
        if (c < 0x80) {
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
    return (char *)b.p;
}

Token *lex(const char *src)
{
    TokVec toks = {0};
    const char *s = src, *line_start = src;
    int line = 1;

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
        t.col = (int)(s - line_start) + 1;
        if (!*s) {
            t.kind = T_EOF;
            VEC_PUSH(toks, t);
            break;
        }

        if (isdigit((unsigned char)*s) || (*s == '$' && isxdigit((unsigned char)s[1]))) {
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
            if (*s == '.' && isdigit((unsigned char)s[1]))
                fatal_at(t.line, t.col, "dashc (prueba): Float aún no está");
            t.kind = T_INT;
            t.val = (long)(int32_t)(uint32_t)v;
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
        } else if (*s == '"') {
            t.kind = T_STR;
            t.text = lex_string(&s, t.line, t.col, &t.len);
        } else {
            /* los signos de dos caracteres primero */
            static const struct { const char *p; int k; } two[] = {
                {"==", P_EQ}, {"!=", P_NE}, {"<=", P_LE}, {">=", P_GE}, {"<<", P_SHL},
                {">>", P_SHR}, {"->", P_ARROW}, {"..", P_DOTDOT}, {NULL, 0}
            };
            static const char one[] = "(),:=<>+-*/%&|^~";
            static const int one_k[] = {
                P_LP, P_RP, P_COMMA, P_COLON, P_ASSIGN, P_LT, P_GT, P_PLUS, P_MINUS,
                P_STAR, P_SLASH, P_PERCENT, P_AMP, P_BAR, P_CARET, P_TILDE
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
    return toks.v;
}
