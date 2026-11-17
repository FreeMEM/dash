/* El ensamblador en línea de Dash (docs/ASM_DISEÑO.md): los bloques asm ... end.
   asm_extract los saca del fuente antes del léxico (como compiler/asm68k.py) y deja en su sitio llamadas internas
   (__dash_asm y __dash_asm_out); asm_assemble pasa el cuerpo de un bloque a bytes de 68000/68020, con la sintaxis
   de Motorola (Devpac, ASM-One, vasm). */
#include <ctype.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "dashc.h"

struct AsmBlocks asm_blocks;

/* ======================= el preprocesado: asm ... end ======================= */

static int a_lower(int c) { return c >= 'A' && c <= 'Z' ? c + 32 : c; }

static int ieq(const char *a, const char *b, size_t n)   /* a (n letras) es b, sin mirar mayúsculas */
{
    size_t i;
    if (strlen(b) != n) return 0;
    for (i = 0; i < n; i++)
        if (a_lower((unsigned char)a[i]) != b[i]) return 0;
    return 1;
}

static int is_id0(int c) { return isalpha(c) || c == '_' || c == '.'; }
static int is_idc(int c) { return isalnum(c) || c == '_'; }

/* un registro: 0-7 d0-d7, 8-15 a0-a7 (sp es a7); -1 si no lo es */
static int reg_num(const char *s, size_t n)
{
    if (n == 2 && (a_lower(s[0]) == 'd' || a_lower(s[0]) == 'a') && s[1] >= '0' && s[1] <= '7')
        return (a_lower(s[0]) == 'a' ? 8 : 0) + s[1] - '0';
    if (ieq(s, "sp", n)) return 15;
    return -1;
}

static const char *reg_name(int r)
{
    static const char *n[] = {"d0", "d1", "d2", "d3", "d4", "d5", "d6", "d7",
                              "a0", "a1", "a2", "a3", "a4", "a5", "a6", "a7"};
    return n[r & 15];
}

static void trim(const char **b, const char **e)
{
    while (*b < *e && isspace((unsigned char)**b)) (*b)++;
    while (*e > *b && isspace((unsigned char)(*e)[-1])) (*e)--;
}

/* un registro de la cabecera (in, out, uses), comprobado */
static int head_reg(const char *b, const char *e, int line)
{
    int r;
    trim(&b, &e);
    r = reg_num(b, (size_t)(e - b));
    if (r < 0) fatal_at(line, 1, "asm: registro no válido: %.*s", (int)(e - b), b);
    if (r == 13) fatal_at(line, 1, "asm: el registro a5 no se puede usar en un bloque asm");
    if (r == 15) fatal_at(line, 1, "asm: el registro a7 (sp) no se puede usar en un bloque asm");
    return r;
}

/* la siguiente coma de nivel superior desde b (o e) */
static const char *top_comma(const char *b, const char *e)
{
    int depth = 0;
    char q = 0;
    for (; b < e; b++) {
        if (q) {
            if (*b == q) q = 0;
        } else if (*b == '"' || *b == '\'') {
            q = *b;
        } else if (*b == '(' || *b == '[' || *b == '{') {
            depth++;
        } else if (*b == ')' || *b == ']' || *b == '}') {
            depth--;
        } else if (*b == ',' && depth == 0) {
            return b;
        }
    }
    return e;
}

/* la cabecera de un bloque: in r = expr, ...  out var = r, ...  uses r, r-r/r */
static void parse_head(const char *h, const char *he, int line, AsmBlock *bk, Buf *call, Buf *outs)
{
    const char *kw[3] = {NULL, NULL, NULL}, *kwe[3];
    const char *p = h;
    int depth = 0, k;
    char q = 0;
    /* dónde empieza cada palabra clave (de nivel superior) */
    while (p < he) {
        if (q) {
            if (*p == '\\' && p + 1 < he) p++;
            else if (*p == q) q = 0;
            p++;
            continue;
        }
        if (*p == '"') { q = *p; p++; continue; }
        if (*p == '(' || *p == '[' || *p == '{') depth++;
        if (*p == ')' || *p == ']' || *p == '}') depth--;
        if (depth == 0 && isalpha((unsigned char)*p) && (p == h || !is_idc((unsigned char)p[-1]))) {
            const char *s = p;
            while (p < he && is_idc((unsigned char)*p)) p++;
            k = (size_t)(p - s) == 2 && !memcmp(s, "in", 2) ? 0 :
                (size_t)(p - s) == 3 && !memcmp(s, "out", 3) ? 1 :
                (size_t)(p - s) == 4 && !memcmp(s, "uses", 4) ? 2 : -1;
            if (k >= 0) {
                if (kw[k]) fatal_at(line, 1, "asm: '%s' está dos veces en la línea de asm", k == 0 ? "in" : k == 1 ? "out" : "uses");
                kw[k] = p;
            } else if (!kw[0] && !kw[1] && !kw[2]) {
                fatal_at(line, 1, "asm: se esperaba in, out o uses y hay '%.*s'", (int)(p - s), s);
            }
            continue;
        }
        if (!kw[0] && !kw[1] && !kw[2] && !isspace((unsigned char)*p))
            fatal_at(line, 1, "asm: se esperaba in, out o uses");
        p++;
    }
    /* dónde acaba cada parte: en la siguiente palabra clave */
    for (k = 0; k < 3; k++) {
        int j;
        if (!kw[k]) continue;
        kwe[k] = he;
        for (j = 0; j < 3; j++)
            if (kw[j] && kw[j] > kw[k] && kw[j] - (j == 0 ? 2 : j == 1 ? 3 : 4) < kwe[k])
                kwe[k] = kw[j] - (j == 0 ? 2 : j == 1 ? 3 : 4);
    }
    /* in r = expr */
    if (kw[0]) {
        const char *b = kw[0], *e;
        for (; b < kwe[0]; b = e + 1) {
            const char *eq, *x, *xe;
            int r, i;
            e = top_comma(b, kwe[0]);
            for (eq = b; eq < e && !(*eq == '=' && eq[1] != '='); eq++) ;
            if (eq >= e) fatal_at(line, 1, "asm: en in va registro = valor");
            r = head_reg(b, eq, line);
            for (i = 0; i < bk->nin; i++)
                if (bk->in_reg[i] == r) fatal_at(line, 1, "asm: el registro %s está dos veces en in", reg_name(r));
            if (bk->nin == 16) fatal_at(line, 1, "asm: demasiadas entradas");
            bk->in_reg[bk->nin++] = (signed char)r;
            x = eq + 1;
            xe = e;
            trim(&x, &xe);
            if (x == xe) fatal_at(line, 1, "asm: falta el valor de %s", reg_name(r));
            buf_bytes(call, ", ", 2);
            buf_bytes(call, x, (size_t)(xe - x));
            if (e >= kwe[0]) break;
        }
    }
    /* out var = r */
    if (kw[1]) {
        const char *b = kw[1], *e;
        for (; b < kwe[1]; b = e + 1) {
            const char *eq, *v, *ve;
            int r, i;
            char num[48];
            e = top_comma(b, kwe[1]);
            for (eq = b; eq < e && *eq != '='; eq++) ;
            if (eq >= e) fatal_at(line, 1, "asm: en out va variable = registro");
            v = b;
            ve = eq;
            trim(&v, &ve);
            if (v == ve || !(isalpha((unsigned char)*v) || *v == '_')) fatal_at(line, 1, "asm: en out va variable = registro");
            for (i = 0; v + i < ve; i++)
                if (!is_idc((unsigned char)v[i])) fatal_at(line, 1, "asm: en out va variable = registro");
            r = head_reg(eq + 1, e, line);
            for (i = 0; i < bk->nout; i++)
                if (bk->out_reg[i] == r) fatal_at(line, 1, "asm: el registro %s está dos veces en out", reg_name(r));
            if (bk->nout == 16) fatal_at(line, 1, "asm: demasiadas salidas");
            buf_byte(outs, ' ');
            buf_bytes(outs, v, (size_t)(ve - v));
            snprintf(num, sizeof num, " = __dash_asm_out(%d, %d)", asm_blocks.n, bk->nout);
            buf_bytes(outs, num, strlen(num));
            bk->out_reg[bk->nout++] = (signed char)r;
            if (e >= kwe[1]) break;
        }
    }
    /* uses r, r-r/r */
    if (kw[2]) {
        const char *b = kw[2], *e;
        for (; b < kwe[2]; b = e + 1) {
            const char *dash;
            e = b;
            while (e < kwe[2] && *e != ',' && *e != '/') e++;
            dash = b;
            while (dash < e && *dash != '-') dash++;
            {
                const char *x = b, *xe = e;
                trim(&x, &xe);
                if (x == xe) fatal_at(line, 1, "asm: lista de uses vacía");
            }
            if (dash < e) {
                int r1 = head_reg(b, dash, line), r2 = head_reg(dash + 1, e, line), r;
                if (r2 < r1 || (r1 < 8) != (r2 < 8)) fatal_at(line, 1, "asm: rango de registros no válido");
                for (r = r1; r <= r2; r++) {
                    if (r == 13) fatal_at(line, 1, "asm: el registro a5 no se puede usar en un bloque asm");
                    bk->uses |= 1u << r;
                }
            } else {
                bk->uses |= 1u << head_reg(b, e, line);
            }
            if (e >= kwe[2]) break;
        }
    }
}

/* ¿la línea [b, e) es "asm" con su cabecera? Devuelve dónde empieza la cabecera (o NULL) */
static const char *asm_line(const char *b, const char *e)
{
    const char *p = b;
    while (p < e && (*p == ' ' || *p == '\t')) p++;
    if (e - p < 3 || memcmp(p, "asm", 3)) return NULL;
    p += 3;
    if (p < e && !(*p == ' ' || *p == '\t' || *p == '#' || *p == '\r')) return NULL;
    while (p < e && (*p == ' ' || *p == '\t' || *p == '\r')) p++;
    if (p == e || *p == '#') return p;
    if ((e - p >= 2 && !memcmp(p, "in", 2) && (e - p == 2 || !is_idc((unsigned char)p[2]))) ||
        (e - p >= 3 && !memcmp(p, "out", 3) && (e - p == 3 || !is_idc((unsigned char)p[3]))) ||
        (e - p >= 4 && !memcmp(p, "uses", 4) && (e - p == 4 || !is_idc((unsigned char)p[4]))))
        return p;
    return NULL;
}

/* el comentario # de la cabecera (fuera de textos) */
static const char *head_end(const char *p, const char *e)
{
    const char *start = p;
    char q = 0;
    for (; p < e; p++) {
        if (q) {
            if (*p == '\\' && p + 1 < e) p++;
            else if (*p == q) q = 0;
        } else if (*p == '"') {
            q = '"';
        } else if (*p == '#') {
            break;
        }
    }
    while (p > start && (p[-1] == ' ' || p[-1] == '\t' || p[-1] == '\r')) p--;
    return p;
}

/* la línea que cierra el bloque: end, solo o con un comentario # o ; detrás */
static int end_line(const char *x, const char *xe)
{
    if (xe - x < 3 || memcmp(x, "end", 3)) return 0;
    x += 3;
    if (x < xe && *x != ' ' && *x != '\t' && *x != '#' && *x != ';') return 0;
    while (x < xe && (*x == ' ' || *x == '\t')) x++;
    return x == xe || *x == '#' || *x == ';';
}

char *asm_extract(const char *src)
{
    Buf out = {0};
    const char *s = src;
    int line = 1, in_native = 0, any = 0;
    /* sin ninguna línea que empiece por "asm" no hay nada que hacer (y no se copia el fuente entero) */
    for (;;) {
        while (*s == ' ' || *s == '\t') s++;
        if (s[0] == 'a' && s[1] == 's' && s[2] == 'm') break;
        s = strchr(s, '\n');
        if (!s) return NULL;
        s++;
    }
    s = src;
    while (*s) {
        const char *e = strchr(s, '\n'), *h, *t;
        if (!e) e = s + strlen(s);
        /* las regiones """ (el C de un @native) se copian tal cual */
        if (!in_native && (h = asm_line(s, e)) != NULL) {
            AsmBlock bk;
            Buf call = {0}, outs = {0}, body = {0};
            const char *he = head_end(h, e), *b;
            char num[48];
            int hline = line, nlines = 0;
            memset(&bk, 0, sizeof bk);
            bk.file = lex_file;
            snprintf(num, sizeof num, "__dash_asm(%d", asm_blocks.n);
            buf_bytes(&call, num, strlen(num));
            parse_head(h, he, line, &bk, &call, &outs);
            buf_byte(&call, ')');
            /* el cuerpo: hasta la línea que solo tiene end */
            b = *e ? e + 1 : e;
            bk.line = line + 1;
            for (;;) {
                const char *le, *x, *xe;
                if (!*b) fatal_at(hline, 1, "asm: falta el end del bloque asm");
                le = strchr(b, '\n');
                if (!le) le = b + strlen(b);
                x = b;
                xe = le;
                trim(&x, &xe);
                nlines++;
                if (end_line(x, xe)) {
                    b = *le ? le + 1 : le;
                    break;
                }
                buf_bytes(&body, b, (size_t)(le - b));
                buf_byte(&body, '\n');
                b = *le ? le + 1 : le;
            }
            buf_byte(&body, 0);
            bk.body = (char *)body.p;
            VEC_PUSH(asm_blocks, bk);
            buf_bytes(&out, call.p, call.n);
            if (outs.n) buf_bytes(&out, outs.p, outs.n);
            xfree(call.p);
            xfree(outs.p);
            buf_byte(&out, '\n');
            while (nlines--) buf_byte(&out, '\n');
            {
                const char *c;                         /* las líneas que se han saltado */
                for (c = s; c < b; c++)
                    if (*c == '\n') line++;
            }
            s = b;
            any = 1;
            continue;
        }
        for (t = s; t + 2 < e; t++)
            if (t[0] == '"' && t[1] == '"' && t[2] == '"') {
                in_native = !in_native;
                t += 2;
            }
        buf_bytes(&out, s, (size_t)(e - s));
        if (*e) buf_byte(&out, '\n');
        s = *e ? e + 1 : e;
        line++;
    }
    buf_byte(&out, 0);
    if (!any) {
        xfree(out.p);
        return NULL;
    }
    return (char *)out.p;
}

/* ======================= el ensamblador ======================= */

typedef struct { long v; int rel, undef; } AVal;   /* rel: cuántas etiquetas (del bloque) suma; undef: un nombre aún sin saber */

typedef struct {
    char *name;
    long val;
    int rel;          /* una etiqueta (desde el principio del bloque) */
    int equ;          /* equ o = */
    int pass;         /* la pasada en la que se puso */
} ASym;

typedef struct {
    int line, col;
    char *label;      /* o NULL */
    char *op;         /* el mnemónico en minúsculas, sin tamaño; NULL si no hay */
    int size;         /* 0, 'b', 'w', 'l' o 's' */
    char **opnd;      /* los operandos, sin espacios fuera de las comillas */
    int nopnd;
    int big;          /* un salto sin tamaño que no llega con 8 bits: .w */
    int full;         /* un (d,An,Xn) del 68020 que no cabe en 8 bits: formato completo */
} ALine;

static struct { ASym *v; int n, cap; } asyms;
static struct { ALine *v; int n, cap; } alines;
static Buf ob;                    /* los bytes de la pasada */
static U32Vec *orelocs;           /* (sitio, destino) de cada long que apunta a una etiqueta del bloque */
static int apass, afinal, acpu020, achanged;
static ALine *cur;
static AsmBlock *cur_block;
static AsmConstFn aconst;

static void aerr(const char *fmt, ...)
{
    char msg[512];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(msg, sizeof msg, fmt, ap);
    va_end(ap);
    fatal_at(cur ? cur->line : cur_block->line, cur ? cur->col : 1, "asm: %s", msg);
}

static ASym *asym_find(const char *name)
{
    int i;
    for (i = 0; i < asyms.n; i++)
        if (!strcmp(asyms.v[i].name, name)) return &asyms.v[i];
    return NULL;
}

static void need020(const char *what)
{
    if (acpu020) return;
    if (cur && what == cur->op && cur->size) aerr("%s.%c necesita --cpu 68020", what, cur->size);
    aerr("%s necesita --cpu 68020", what);
}

/* ---- expresiones (con la prioridad de C) ---- */
static const char *xp;   /* por dónde va */

static AVal x_or(void);

static long x_number(void)
{
    long v = 0;
    int base = 10, any = 0;
    if (*xp == '$') { base = 16; xp++; }
    else if (*xp == '%') { base = 2; xp++; }
    else if (xp[0] == '0' && (xp[1] == 'x' || xp[1] == 'X')) { base = 16; xp += 2; }
    else if (xp[0] == '0' && (xp[1] == 'b' || xp[1] == 'B') && (xp[2] == '0' || xp[2] == '1')) { base = 2; xp += 2; }
    for (;;) {
        int c = (unsigned char)*xp, d;
        if (c >= '0' && c <= '9') d = c - '0';
        else if (base == 16 && c >= 'a' && c <= 'f') d = c - 'a' + 10;
        else if (base == 16 && c >= 'A' && c <= 'F') d = c - 'A' + 10;
        else break;
        if (d >= base) aerr("número no válido");
        v = (long)((unsigned long)v * (unsigned)base + (unsigned)d);
        xp++;
        any = 1;
    }
    if (!any || is_idc((unsigned char)*xp)) aerr("número no válido");
    return (long)(int32_t)(uint32_t)v;
}

static AVal x_prim(void)
{
    AVal r = {0, 0, 0};
    if (*xp == '(') {
        xp++;
        r = x_or();
        if (*xp != ')') aerr("falta un ')'");
        xp++;
        return r;
    }
    if (*xp == '-') { xp++; r = x_prim(); if (r.rel) aerr("una etiqueta solo se puede sumar o restar"); r.v = -r.v; return r; }
    if (*xp == '+') { xp++; return x_prim(); }
    if (*xp == '~') { xp++; r = x_prim(); if (r.rel) aerr("una etiqueta solo se puede sumar o restar"); r.v = ~r.v; return r; }
    if (isdigit((unsigned char)*xp) || *xp == '$' || *xp == '%') {
        r.v = x_number();
        return r;
    }
    if (*xp == '\'' || *xp == '"') {
        char q = *xp++;
        int n = 0;
        while (*xp && *xp != q) {
            r.v = (long)(((unsigned long)r.v << 8) | (unsigned char)*xp++);
            n++;
        }
        if (!*xp) aerr("texto sin cerrar");
        xp++;
        if (n < 1 || n > 4) aerr("un carácter entre comillas tiene de 1 a 4 letras");
        r.v = (long)(int32_t)(uint32_t)r.v;
        return r;
    }
    if (is_id0((unsigned char)*xp)) {
        const char *b = xp;
        char name[128];
        ASym *s;
        long cv;
        xp++;
        while (is_idc((unsigned char)*xp)) xp++;
        if (xp - b >= (long)sizeof name) aerr("nombre demasiado largo");
        memcpy(name, b, (size_t)(xp - b));
        name[xp - b] = 0;
        if (reg_num(b, (size_t)(xp - b)) >= 0 || ieq(b, "pc", (size_t)(xp - b)))
            aerr("un registro no va en una expresión: %s", name);
        s = asym_find(name);
        if (s) {
            r.v = s->val;
            r.rel = s->rel;
            return r;
        }
        if (aconst && aconst(name, cur_block->file, &cv)) {
            r.v = cv;
            return r;
        }
        if (afinal) aerr("nombre desconocido: %s", name);
        r.undef = 1;
        return r;
    }
    if (*xp == '*' ) aerr("'*' (la posición actual) no se admite: usa una etiqueta");
    aerr("expresión no válida");
    return r;
}

static AVal x_mul(void)
{
    AVal a = x_prim(), b;
    while (*xp == '*' || (*xp == '/' && xp[1] != '/')) {
        char o = *xp++;
        b = x_prim();
        if (a.rel || b.rel) aerr("una etiqueta solo se puede sumar o restar");
        if (o == '*') a.v = (long)(int32_t)((uint32_t)a.v * (uint32_t)b.v);
        else {
            if (!b.v) { if (afinal && !a.undef && !b.undef) aerr("división por cero"); a.v = 0; }
            else a.v = (long)((int32_t)a.v / (int32_t)b.v);
        }
        a.undef |= b.undef;
    }
    return a;
}

static AVal x_add(void)
{
    AVal a = x_mul(), b;
    while (*xp == '+' || *xp == '-') {
        char o = *xp++;
        b = x_mul();
        if (o == '+') { a.v = (long)(int32_t)((uint32_t)a.v + (uint32_t)b.v); a.rel += b.rel; }
        else { a.v = (long)(int32_t)((uint32_t)a.v - (uint32_t)b.v); a.rel -= b.rel; }
        a.undef |= b.undef;
    }
    return a;
}

static AVal x_shift(void)
{
    AVal a = x_add(), b;
    while ((xp[0] == '<' && xp[1] == '<') || (xp[0] == '>' && xp[1] == '>')) {
        char o = *xp;
        xp += 2;
        b = x_add();
        if (a.rel || b.rel) aerr("una etiqueta solo se puede sumar o restar");
        a.v = o == '<' ? (long)(int32_t)((uint32_t)a.v << (b.v & 31)) : (long)(int32_t)((uint32_t)a.v >> (b.v & 31));
        a.undef |= b.undef;
    }
    return a;
}

static AVal x_bin(int level)
{
    static const char ops[] = "|^&";
    AVal a = level == 2 ? x_shift() : x_bin(level + 1), b;
    while (*xp == ops[level]) {
        xp++;
        b = level == 2 ? x_shift() : x_bin(level + 1);
        if (a.rel || b.rel) aerr("una etiqueta solo se puede sumar o restar");
        a.v = level == 0 ? (a.v | b.v) : level == 1 ? (a.v ^ b.v) : (a.v & b.v);
        a.undef |= b.undef;
    }
    return a;
}

static AVal x_or(void) { return x_bin(0); }

/* una expresión entera (el texto acaba en e) */
static AVal expr(const char *s, const char *e)
{
    AVal r;
    char buf[256];
    if (e - s >= (long)sizeof buf) aerr("expresión demasiado larga");
    memcpy(buf, s, (size_t)(e - s));
    buf[e - s] = 0;
    if (!buf[0]) aerr("falta un valor");
    xp = buf;
    r = x_or();
    if (*xp) aerr("expresión no válida: %s", buf);
    if (r.rel < 0 || r.rel > 1) {
        /* (un nombre de más abajo aún sin saber, en una pasada que no es la última: .b-.a) */
        if (!r.undef || afinal) aerr("expresión no válida: %s", buf);
        r.rel = 0;
    }
    return r;
}

static long const_expr(const char *s)
{
    AVal r = expr(s, s + strlen(s));
    if (r.rel) aerr("aquí va un número, no una etiqueta: %s", s);
    return r.v;
}

/* ---- direcciones efectivas ---- */
enum { M_DN, M_AN, M_IND, M_POST, M_PRE, M_D16, M_IDX, M_ABSW, M_ABSL, M_PCD, M_PCIDX, M_IMM,
       M_SR, M_CCR, M_USP, M_LIST, M_PAIR };
#define B(m) (1u << (m))
#define A_ALL (B(M_DN) | B(M_AN) | B(M_IND) | B(M_POST) | B(M_PRE) | B(M_D16) | B(M_IDX) | B(M_ABSW) | B(M_ABSL) | \
               B(M_PCD) | B(M_PCIDX) | B(M_IMM))
#define A_DATA (A_ALL & ~B(M_AN))
#define A_MEM (A_DATA & ~B(M_DN))
#define A_CTRL (B(M_IND) | B(M_D16) | B(M_IDX) | B(M_ABSW) | B(M_ABSL) | B(M_PCD) | B(M_PCIDX))
#define A_ALT (A_ALL & ~(B(M_IMM) | B(M_PCD) | B(M_PCIDX)))
#define A_DALT (A_DATA & A_ALT)
#define A_MALT (A_MEM & A_ALT)
#define A_CALT (A_CTRL & A_ALT)

typedef struct {
    int mode, reg;
    AVal d;              /* desplazamiento, dirección o inmediato */
    int has_d;
    int xreg, xlong, scale;
    unsigned list;       /* M_LIST: bit 0 d0 ... bit 15 a7 */
    int r2;              /* M_PAIR: Dh:Dl -> reg Dh, r2 Dl */
    int bf, bfo_d, bfo, bfw_d, bfw;   /* {offset:width}; *_d: es un registro */
    const char *text;
} Ea;

/* "d0-d3/a0" */
static int parse_list(const char *s, unsigned *mask)
{
    unsigned m = 0;
    const char *p = s;
    int any = 0;
    while (*p) {
        const char *e = p, *dash;
        int r1, r2, r;
        while (*e && *e != '/') e++;
        for (dash = p; dash < e && *dash != '-'; dash++) ;
        r1 = reg_num(p, (size_t)(dash - p));
        if (r1 < 0) return 0;
        if (dash < e) {
            r2 = reg_num(dash + 1, (size_t)(e - dash - 1));
            if (r2 < 0 || r2 < r1) return 0;
            any = 1;
        } else {
            r2 = r1;
        }
        for (r = r1; r <= r2; r++) m |= 1u << r;
        if (*e == '/') { e++; any = 1; }
        p = e;
    }
    *mask = m;
    return any;
}

/* el índice de (d,An,Xn): "d0", "a1.w", "d2.l*4" */
static int parse_index(const char *s, const char *e, Ea *ea)
{
    const char *p = s;
    int r;
    while (p < e && *p != '.' && *p != '*') p++;
    r = reg_num(s, (size_t)(p - s));
    if (r < 0) return 0;
    ea->xreg = r;
    ea->xlong = 0;
    ea->scale = 1;
    if (p < e && *p == '.') {
        if (p + 1 < e && a_lower(p[1]) == 'l') ea->xlong = 1;
        else if (!(p + 1 < e && a_lower(p[1]) == 'w')) return 0;
        p += 2;
    }
    if (p < e && *p == '*') {
        p++;
        if (p + 1 != e || (*p != '1' && *p != '2' && *p != '4' && *p != '8')) return 0;
        ea->scale = *p - '0';
        p++;
    }
    return p == e;
}

static void parse_ea(const char *s, Ea *e)
{
    size_t n = strlen(s);
    const char *close;
    memset(e, 0, sizeof *e);
    e->text = s;
    if (!n) aerr("falta un operando");
    if (s[0] == '#') {
        e->mode = M_IMM;
        e->d = expr(s + 1, s + n);
        e->has_d = 1;
        return;
    }
    /* un campo de bits: <ea>{offset:width} */
    if (s[n - 1] == '}') {
        const char *o = strrchr(s, '{'), *c;
        static char tmp[256];
        if (!o || o == s) aerr("operando no válido: %s", s);
        c = strchr(o, ':');
        if (!c || c > s + n - 1) aerr("operando no válido: %s", s);
        e->bf = 1;
        if (reg_num(o + 1, (size_t)(c - o - 1)) >= 0 && reg_num(o + 1, (size_t)(c - o - 1)) < 8) {
            e->bfo_d = 1;
            e->bfo = reg_num(o + 1, (size_t)(c - o - 1));
        } else {
            AVal v = expr(o + 1, c);
            if (v.rel || v.v < 0 || v.v > 31) aerr("el desplazamiento de un campo de bits va de 0 a 31");
            e->bfo = (int)v.v;
        }
        if (reg_num(c + 1, (size_t)(s + n - 1 - c - 1)) >= 0 && reg_num(c + 1, (size_t)(s + n - 1 - c - 1)) < 8) {
            e->bfw_d = 1;
            e->bfw = reg_num(c + 1, (size_t)(s + n - 1 - c - 1));
        } else {
            AVal v = expr(c + 1, s + n - 1);
            if (v.rel || v.v < 1 || v.v > 32) aerr("el ancho de un campo de bits va de 1 a 32");
            e->bfw = (int)v.v & 31;
        }
        if ((size_t)(o - s) >= sizeof tmp) aerr("operando demasiado largo");
        memcpy(tmp, s, (size_t)(o - s));
        tmp[o - s] = 0;
        {
            int bf = e->bf, bfo_d = e->bfo_d, bfo = e->bfo, bfw_d = e->bfw_d, bfw = e->bfw;
            parse_ea(tmp, e);
            e->text = s;
            e->bf = bf; e->bfo_d = bfo_d; e->bfo = bfo; e->bfw_d = bfw_d; e->bfw = bfw;
        }
        return;
    }
    if ((e->reg = reg_num(s, n)) >= 0) {
        e->mode = e->reg < 8 ? M_DN : M_AN;
        e->reg &= 7;
        return;
    }
    if (ieq(s, "sr", n)) { e->mode = M_SR; return; }
    if (ieq(s, "ccr", n)) { e->mode = M_CCR; return; }
    if (ieq(s, "usp", n)) { e->mode = M_USP; return; }
    /* Dh:Dl (muls.l, divs.l) */
    {
        const char *c = strchr(s, ':');
        if (c && reg_num(s, (size_t)(c - s)) >= 0 && reg_num(c + 1, strlen(c + 1)) >= 0) {
            e->mode = M_PAIR;
            e->reg = reg_num(s, (size_t)(c - s));
            e->r2 = reg_num(c + 1, strlen(c + 1));
            if (e->reg > 7 || e->r2 > 7) aerr("operando no válido: %s", s);
            return;
        }
    }
    if ((strchr(s, '/') || strchr(s, '-')) && parse_list(s, &e->list)) {
        e->mode = M_LIST;
        return;
    }
    if (n >= 4 && s[0] == '-' && s[1] == '(' && s[n - 1] == ')' && (e->reg = reg_num(s + 2, n - 3)) >= 8) {
        e->mode = M_PRE;
        e->reg &= 7;
        return;
    }
    if (n >= 4 && s[0] == '(' && s[n - 1] == '+' && s[n - 2] == ')' && (e->reg = reg_num(s + 1, n - 3)) >= 8) {
        e->mode = M_POST;
        e->reg &= 7;
        return;
    }
    /* .w y .l de una dirección absoluta */
    if (n > 2 && s[n - 2] == '.' && (a_lower(s[n - 1]) == 'w' || a_lower(s[n - 1]) == 'l') && s[n - 3] != ')') {
        e->mode = a_lower(s[n - 1]) == 'w' ? M_ABSW : M_ABSL;
        e->d = expr(s, s + n - 2);
        e->has_d = 1;
        return;
    }
    if (n > 2 && s[n - 2] == '.' && (a_lower(s[n - 1]) == 'w' || a_lower(s[n - 1]) == 'l') && s[n - 3] == ')') {
        /* (expr).w */
        e->mode = a_lower(s[n - 1]) == 'w' ? M_ABSW : M_ABSL;
        e->d = expr(s, s + n - 2);
        e->has_d = 1;
        return;
    }
    if (s[n - 1] == ')') {
        int depth = 0;
        const char *open = NULL, *p, *parts[4], *pe[4];
        int np = 0, i, base = -1, idx = -1;
        for (close = s + n - 1, p = close; p >= s; p--) {
            if (*p == ')') depth++;
            else if (*p == '(' && --depth == 0) { open = p; break; }
        }
        if (!open) aerr("operando no válido: %s", s);
        /* las partes de dentro */
        for (p = open + 1; ; ) {
            const char *c = top_comma(p, close);
            if (np == 4) aerr("operando no válido: %s", s);
            parts[np] = p;
            pe[np++] = c;
            if (c >= close) break;
            p = c + 1;
        }
        if (open > s && open[-1] == '[') aerr("la indirección de memoria del 68020 no se admite: %s", s);
        if (*(open + 1) == '[') aerr("la indirección de memoria del 68020 no se admite: %s", s);
        /* ¿hay un registro? si no, es una expresión entre paréntesis */
        for (i = 0; i < np; i++) {
            const char *q = parts[i];
            size_t len = (size_t)(pe[i] - q);
            if (reg_num(q, len) >= 0 || ieq(q, "pc", len)) break;
            {
                Ea t;
                if (parse_index(q, pe[i], &t)) break;
            }
        }
        if (i == np) {
            e->mode = M_ABSL;
            e->d = expr(s, s + n);
            e->has_d = 1;
            return;
        }
        i = 0;
        if (open > s) {
            e->d = expr(s, open);
            e->has_d = 1;
        } else if (!(reg_num(parts[0], (size_t)(pe[0] - parts[0])) >= 0 || ieq(parts[0], "pc", (size_t)(pe[0] - parts[0])))) {
            e->d = expr(parts[0], pe[0]);
            e->has_d = 1;
            i = 1;
        }
        if (i >= np) aerr("operando no válido: %s", s);
        {
            size_t len = (size_t)(pe[i] - parts[i]);
            int r = reg_num(parts[i], len);
            if (ieq(parts[i], "pc", len)) base = 16;
            else if (r >= 8) base = r;
            else aerr("operando no válido: %s", s);
        }
        i++;
        if (i < np) {
            if (!parse_index(parts[i], pe[i], e)) aerr("operando no válido: %s", s);
            idx = 1;
            i++;
        }
        if (i != np) aerr("operando no válido: %s", s);
        if (base == 16) {
            e->mode = idx > 0 ? M_PCIDX : M_PCD;
        } else {
            e->reg = base & 7;
            e->mode = idx > 0 ? M_IDX : e->has_d ? M_D16 : M_IND;
        }
        if (e->scale != 1 && e->scale) need020("el índice con escala");
        return;
    }
    e->mode = M_ABSL;
    e->d = expr(s, s + n);
    e->has_d = 1;
}

static void check_ea(Ea *e, unsigned mask)
{
    if (!(mask & B(e->mode))) aerr("operando no válido: %s", e->text);
}

/* ---- salida ---- */
static void ow(int v) { buf_word(&ob, v & 0xFFFF); }
static void ol(uint32_t v) { buf_long(&ob, v); }

static void reloc_here(long target)
{
    if (!afinal) return;
    VEC_PUSH(*orelocs, (uint32_t)ob.n);
    VEC_PUSH(*orelocs, (uint32_t)target);
}

/* un valor de size bytes (1, 2, 4) en una palabra o dos */
static void out_imm(AVal *v, int size)
{
    if (size == 4) {
        if (v->rel) reloc_here(v->v);
        ol(v->rel ? 0 : (uint32_t)v->v);
        return;
    }
    if (v->rel) aerr("una etiqueta como inmediato necesita .l");
    if (afinal && !v->undef) {
        if (size == 1 && (v->v < -128 || v->v > 255)) aerr("el valor no cabe en un byte: %ld", v->v);
        if (size == 2 && (v->v < -32768 || v->v > 65535)) aerr("el valor no cabe en 16 bits: %ld", v->v);
    }
    ow(size == 1 ? (int)(v->v & 0xFF) : (int)(v->v & 0xFFFF));
}

static int ea_bits(Ea *e)
{
    switch (e->mode) {
    case M_DN: return e->reg;
    case M_AN: return 8 | e->reg;
    case M_IND: return 16 | e->reg;
    case M_POST: return 24 | e->reg;
    case M_PRE: return 32 | e->reg;
    case M_D16: return 40 | e->reg;
    case M_IDX: return 48 | e->reg;
    case M_ABSW: return 56;
    case M_ABSL: return 57;
    case M_PCD: return 58;
    case M_PCIDX: return 59;
    case M_IMM: return 60;
    }
    aerr("operando no válido: %s", e->text);
    return 0;
}

/* el formato del índice: breve (d8) o completo (68020, con desplazamiento de 16 o 32 bits) */
static void out_index(Ea *e, long d, int pcrel)
{
    int top = (e->xreg >= 8 ? 0x8000 : 0) | (e->xreg & 7) << 12 | e->xlong << 11 |
              (e->scale == 2 ? 1 : e->scale == 4 ? 2 : e->scale == 8 ? 3 : 0) << 9;
    if (!cur->full && d >= -128 && d <= 127) {
        ow(top | (int)(d & 0xFF));
        return;
    }
    if (!acpu020) {
        if (afinal) aerr("el desplazamiento no cabe en 8 bits: %ld", d);
        ow(top);
        return;
    }
    if (!cur->full) { cur->full = 1; achanged = 1; }
    if (pcrel) d -= 0;   /* (el pc es el de la palabra de extensión: el mismo) */
    if (d >= -32768 && d <= 32767) {
        ow(top | 0x0100 | 0x20);
        ow((int)(d & 0xFFFF));
    } else {
        ow(top | 0x0100 | 0x30);
        ol((uint32_t)d);
    }
}

/* las palabras de extensión de e (size: el de la operación, para un inmediato) */
static void out_ea(Ea *e, int size)
{
    long pc = (long)ob.n;
    switch (e->mode) {
    case M_D16:
        if (e->d.rel) aerr("una etiqueta como desplazamiento de An no se admite: %s", e->text);
        if (e->d.v < -32768 || e->d.v > 32767) {
            if (afinal) aerr("el desplazamiento no cabe en 16 bits: %s", e->text);
        }
        ow((int)(e->d.v & 0xFFFF));
        break;
    case M_IDX:
        if (e->d.rel) aerr("una etiqueta como desplazamiento de An no se admite: %s", e->text);
        out_index(e, e->has_d ? e->d.v : 0, 0);
        break;
    case M_ABSW:
        if (e->d.rel) aerr("una etiqueta como dirección corta no se admite: %s", e->text);
        if (afinal && (e->d.v < -32768 || e->d.v > 65535)) aerr("la dirección no cabe en 16 bits: %s", e->text);
        ow((int)(e->d.v & 0xFFFF));
        break;
    case M_ABSL:
        if (e->d.rel) reloc_here(e->d.v);
        ol(e->d.rel ? 0 : (uint32_t)e->d.v);
        break;
    case M_PCD: {
        long d = e->has_d ? (e->d.rel ? e->d.v - pc : e->d.v) : 0;
        if (afinal && !e->d.undef && (d < -32768 || d > 32767)) aerr("el desplazamiento no cabe en 16 bits: %s", e->text);
        ow((int)(d & 0xFFFF));
        break;
    }
    case M_PCIDX:
        out_index(e, e->has_d ? (e->d.rel ? e->d.v - pc : e->d.v) : 0, 1);
        break;
    case M_IMM:
        out_imm(&e->d, size);
        break;
    }
}

/* ---- las instrucciones ---- */
static const char *cc_names[] = {"t", "f", "hi", "ls", "cc", "cs", "ne", "eq", "vc", "vs", "pl", "mi", "ge", "lt",
                                 "gt", "le", "hs", "lo", NULL};

static int cond_code(const char *s)
{
    int i;
    for (i = 0; cc_names[i]; i++)
        if (!strcmp(s, cc_names[i])) return i < 16 ? i : i == 16 ? 4 : 5;
    return -1;
}

static int size_bytes(int sz) { return sz == 'b' ? 1 : sz == 'l' ? 4 : 2; }
static int size_ss(int sz) { return sz == 'b' ? 0 : sz == 'l' ? 2 : 1; }

static void sizes(const char *ok, int def)
{
    if (!cur->size) cur->size = def;
    if (!strchr(ok, cur->size)) aerr("tamaño .%c no válido en %s", cur->size, cur->op);
}

static void nops(int n)
{
    if (cur->nopnd != n) aerr("%s pide %d operando%s", cur->op, n, n == 1 ? "" : "s");
}

static void nops2(int a, int b)
{
    if (cur->nopnd != a && cur->nopnd != b) aerr("%s pide %d o %d operandos", cur->op, a, b);
}

/* el desplazamiento de un salto a una etiqueta, desde from */
static long branch_disp(const char *op, long from)
{
    AVal v = expr(op, op + strlen(op));
    if (!v.rel) {
        if (afinal) aerr("un salto va a una etiqueta del bloque: %s", op);
        return 0;
    }
    return v.undef ? 0 : v.v - from;
}

static void ins_branch(int cc)
{
    long d;
    uint32_t at = (uint32_t)ob.n;
    nops(1);
    if (cur->size && !strchr("swbl", cur->size)) aerr("tamaño .%c no válido en %s", cur->size, cur->op);
    d = branch_disp(cur->opnd[0], (long)at + 2);
    if (cur->size == 's' || cur->size == 'b') {
        if (afinal && d == 0) aerr("un salto .s no puede ir a la instrucción siguiente");
        if (afinal && (d < -128 || d > 127)) aerr("el salto .s no llega (%ld bytes)", d);
        ow(0x6000 | cc << 8 | (int)(d & 0xFF));
    } else if (cur->size == 'l') {
        need020(cur->op);
        ow(0x60FF | cc << 8);
        ol((uint32_t)d);
    } else if (cur->size == 'w' || cur->big) {
        if (afinal && (d < -32768 || d > 32767)) aerr("el salto no llega (%ld bytes)", d);
        ow(0x6000 | cc << 8);
        ow((int)(d & 0xFFFF));
    } else {
        if (d == 0 || d < -128 || d > 127) {
            cur->big = 1;
            achanged = 1;
            ow(0x6000 | cc << 8);
            ow((int)(d & 0xFFFF));
        } else {
            ow(0x6000 | cc << 8 | (int)(d & 0xFF));
        }
    }
}

static void need_imm(Ea *e)
{
    if (e->mode != M_IMM) aerr("operando no válido: %s (va un #inmediato)", e->text);
}

/* ori, andi, subi, addi, eori, cmpi: #imm,<ea> (y a ccr o sr) */
static void ins_imm(int base, Ea *s, Ea *d, int cmp)
{
    need_imm(s);
    if (d->mode == M_CCR || d->mode == M_SR) {
        if (base != 0x0000 && base != 0x0200 && base != 0x0A00) aerr("operando no válido: %s", d->text);
        if (d->mode == M_CCR) { if (cur->size && cur->size != 'b') aerr("tamaño .%c no válido en %s", cur->size, cur->op); }
        else if (cur->size && cur->size != 'w') aerr("tamaño .%c no válido en %s", cur->size, cur->op);
        ow(base | (d->mode == M_CCR ? 0x3C : 0x7C));
        out_imm(&s->d, d->mode == M_CCR ? 1 : 2);
        return;
    }
    sizes("bwl", 'w');
    if (cmp && (d->mode == M_PCD || d->mode == M_PCIDX)) need020("cmpi con (pc)");
    else check_ea(d, A_DALT);
    ow(base | size_ss(cur->size) << 6 | ea_bits(d));
    out_imm(&s->d, size_bytes(cur->size));
    out_ea(d, 0);
}

/* add, sub, and, or, cmp, eor y sus formas */
static void ins_arith(const char *op, Ea *s, Ea *d)
{
    int is_add = !strcmp(op, "add"), is_sub = !strcmp(op, "sub"), is_cmp = !strcmp(op, "cmp");
    int is_and = !strcmp(op, "and"), is_or = !strcmp(op, "or"), is_eor = !strcmp(op, "eor");
    int base = is_add ? 0xD000 : is_sub ? 0x9000 : is_cmp ? 0xB000 : is_and ? 0xC000 : is_or ? 0x8000 : 0xB000;
    int ibase = is_add ? 0x0600 : is_sub ? 0x0400 : is_cmp ? 0x0C00 : is_and ? 0x0200 : is_or ? 0x0000 : 0x0A00;
    if (d->mode == M_AN && (is_add || is_sub || is_cmp)) {
        /* adda, suba, cmpa */
        sizes("wl", 'w');
        ow(base | 0x00C0 | (cur->size == 'l') << 8 | d->reg << 9 | ea_bits(s));
        out_ea(s, size_bytes(cur->size));
        return;
    }
    if (s->mode == M_IMM && !(d->mode == M_DN && !is_eor)) {   /* (#n,Dn: la forma de siempre, como vasm) */
        ins_imm(ibase, s, d, is_cmp);
        return;
    }
    sizes("bwl", 'w');
    if (d->mode == M_DN && !is_eor) {
        check_ea(s, is_and || is_or ? A_DATA : A_ALL);
        if (s->mode == M_AN && cur->size == 'b') aerr("tamaño .b no válido con un registro de direcciones");
        ow(base | d->reg << 9 | size_ss(cur->size) << 6 | ea_bits(s));
        out_ea(s, size_bytes(cur->size));
        return;
    }
    if (s->mode == M_DN && !is_cmp) {
        check_ea(d, is_eor ? A_DALT : A_MALT);
        ow(base | 0x0100 | s->reg << 9 | size_ss(cur->size) << 6 | ea_bits(d));
        out_ea(d, 0);
        return;
    }
    aerr("operandos no válidos en %s", cur->op);
}

/* addx, subx, abcd, sbcd: Dy,Dx o -(Ay),-(Ax) */
static void ins_x(int base, Ea *s, Ea *d, int bcd)
{
    if (bcd) sizes("b", 'b');
    else sizes("bwl", 'w');
    if (s->mode == M_DN && d->mode == M_DN) ow(base | d->reg << 9 | (bcd ? 0 : size_ss(cur->size) << 6) | s->reg);
    else if (s->mode == M_PRE && d->mode == M_PRE) ow(base | 8 | d->reg << 9 | (bcd ? 0 : size_ss(cur->size) << 6) | s->reg);
    else aerr("operandos no válidos en %s", cur->op);
}

static void ins_shift(int type, int left)
{
    Ea a, b;
    if (cur->nopnd == 1) {
        parse_ea(cur->opnd[0], &a);
        if (a.mode == M_DN) {
            sizes("bwl", 'w');
            ow(0xE000 | 1 << 9 | left << 8 | size_ss(cur->size) << 6 | type << 3 | a.reg);
            return;
        }
        sizes("w", 'w');
        check_ea(&a, A_MALT);
        ow(0xE0C0 | type << 9 | left << 8 | ea_bits(&a));
        out_ea(&a, 0);
        return;
    }
    nops2(1, 2);
    parse_ea(cur->opnd[0], &a);
    parse_ea(cur->opnd[1], &b);
    sizes("bwl", 'w');
    if (b.mode != M_DN) aerr("operando no válido: %s", b.text);
    if (a.mode == M_DN) {
        ow(0xE000 | a.reg << 9 | left << 8 | size_ss(cur->size) << 6 | 0x20 | type << 3 | b.reg);
    } else if (a.mode == M_IMM) {
        if (a.d.rel || (afinal && (a.d.v < 1 || a.d.v > 8))) aerr("la cuenta de %s va de 1 a 8", cur->op);
        ow(0xE000 | (int)(a.d.v & 7) << 9 | left << 8 | size_ss(cur->size) << 6 | type << 3 | b.reg);
    } else {
        aerr("operando no válido: %s", a.text);
    }
}

static void ins_bit(int type)
{
    Ea s, d;
    nops(2);
    parse_ea(cur->opnd[0], &s);
    parse_ea(cur->opnd[1], &d);
    if (cur->size && cur->size != (d.mode == M_DN ? 'l' : 'b'))
        aerr("tamaño .%c no válido en %s", cur->size, cur->op);
    if (s.mode == M_DN) {
        check_ea(&d, type == 0 ? A_DATA : A_DALT);
        ow(0x0100 | s.reg << 9 | type << 6 | ea_bits(&d));
        out_ea(&d, 1);
    } else if (s.mode == M_IMM) {
        check_ea(&d, type == 0 ? (A_DATA & ~B(M_IMM)) : A_DALT);
        ow(0x0800 | type << 6 | ea_bits(&d));
        if (s.d.rel) aerr("el número de bit es un número");
        ow((int)(s.d.v & 0xFF));
        out_ea(&d, 0);
    } else {
        aerr("operando no válido: %s", s.text);
    }
}

static void ins_bitfield(int op)
{
    Ea a, b, *f;
    int reg = 0;
    need020(cur->op);
    if (cur->size) aerr("tamaño .%c no válido en %s", cur->size, cur->op);
    if (op == 1 || op == 3 || op == 5) {          /* bfextu, bfexts, bfffo: <ea>{o:w},Dn */
        nops(2);
        parse_ea(cur->opnd[0], &a);
        parse_ea(cur->opnd[1], &b);
        if (b.mode != M_DN) aerr("operando no válido: %s", b.text);
        f = &a;
        reg = b.reg;
    } else if (op == 7) {                         /* bfins Dn,<ea>{o:w} */
        nops(2);
        parse_ea(cur->opnd[0], &a);
        parse_ea(cur->opnd[1], &b);
        if (a.mode != M_DN) aerr("operando no válido: %s", a.text);
        f = &b;
        reg = a.reg;
    } else {
        nops(1);
        parse_ea(cur->opnd[0], &a);
        f = &a;
    }
    if (!f->bf) aerr("falta el campo {desplazamiento:ancho}: %s", f->text);
    check_ea(f, B(M_DN) | (op == 0 || op == 1 || op == 3 || op == 5 ? A_CTRL : A_CALT));
    ow(0xE8C0 | op << 8 | ea_bits(f));
    ow(reg << 12 | f->bfo_d << 11 | (f->bfo & 31) << 6 | f->bfw_d << 5 | (f->bfw & 31));
    out_ea(f, 0);
}

/* muls, mulu, divs, divu (y divsl, divul): .w del 68000; .l del 68020 */
static void ins_muldiv(int div, int sign, int lform)
{
    Ea s, d;
    nops(2);
    parse_ea(cur->opnd[0], &s);
    parse_ea(cur->opnd[1], &d);
    check_ea(&s, A_DATA);
    if (lform) sizes("l", 'l');
    else sizes("wl", 'w');
    if (cur->size == 'w') {
        if (d.mode != M_DN) aerr("operando no válido: %s", d.text);
        ow((div ? 0x80C0 : 0xC0C0) | sign << 8 | d.reg << 9 | ea_bits(&s));
        out_ea(&s, 2);
        return;
    }
    need020(cur->op);
    ow((div ? 0x4C40 : 0x4C00) | ea_bits(&s));
    if (d.mode == M_DN) {
        if (lform) aerr("%s.l va con Dr:Dq", cur->op);
        ow(d.reg << 12 | sign << 11 | d.reg);          /* (mul: el campo Dh no se lee; como vasm) */
    } else if (d.mode == M_PAIR) {
        /* mul: Dh:Dl; div: Dr:Dq */
        if (lform) ow(d.r2 << 12 | sign << 11 | d.reg);
        else ow(d.r2 << 12 | sign << 11 | 0x0400 | d.reg);
    } else {
        aerr("operando no válido: %s", d.text);
    }
    out_ea(&s, 4);
}

static void ins_move(void)
{
    Ea s, d;
    nops(2);
    parse_ea(cur->opnd[0], &s);
    parse_ea(cur->opnd[1], &d);
    if (d.mode == M_CCR || d.mode == M_SR) {
        if (cur->size && cur->size != 'w') aerr("tamaño .%c no válido en %s", cur->size, cur->op);
        check_ea(&s, A_DATA);
        ow((d.mode == M_CCR ? 0x44C0 : 0x46C0) | ea_bits(&s));
        out_ea(&s, 2);
        return;
    }
    if (s.mode == M_SR || s.mode == M_CCR) {
        if (cur->size && cur->size != 'w') aerr("tamaño .%c no válido en %s", cur->size, cur->op);
        if (s.mode == M_CCR) need020("move ccr");
        check_ea(&d, A_DALT);
        ow((s.mode == M_SR ? 0x40C0 : 0x42C0) | ea_bits(&d));
        out_ea(&d, 0);
        return;
    }
    if (s.mode == M_USP || d.mode == M_USP) {
        if (cur->size && cur->size != 'l') aerr("tamaño .%c no válido en %s", cur->size, cur->op);
        if (s.mode == M_USP && d.mode == M_AN) ow(0x4E68 | d.reg);
        else if (d.mode == M_USP && s.mode == M_AN) ow(0x4E60 | s.reg);
        else aerr("operandos no válidos en move");
        return;
    }
    if (d.mode == M_AN) {
        sizes("wl", 'w');
    } else {
        sizes("bwl", 'w');
        check_ea(&d, A_DALT);
        if (s.mode == M_AN && cur->size == 'b') aerr("tamaño .b no válido con un registro de direcciones");
    }
    check_ea(&s, A_ALL);
    {
        int db = ea_bits(&d);
        int sz = cur->size == 'b' ? 1 : cur->size == 'l' ? 2 : 3;
        ow(sz << 12 | (db & 7) << 9 | (db >> 3) << 6 | ea_bits(&s));
    }
    out_ea(&s, size_bytes(cur->size));
    out_ea(&d, 0);
}

static void ins_movem(void)
{
    Ea a, b;
    unsigned mask;
    int tomem;
    nops(2);
    parse_ea(cur->opnd[0], &a);
    parse_ea(cur->opnd[1], &b);
    sizes("wl", 'w');
    if (a.mode == M_DN || a.mode == M_AN || a.mode == M_LIST) {
        tomem = 1;
        mask = a.mode == M_LIST ? a.list : 1u << (a.reg + (a.mode == M_AN ? 8 : 0));
        check_ea(&b, A_CALT | B(M_PRE));
    } else if (b.mode == M_DN || b.mode == M_AN || b.mode == M_LIST) {
        tomem = 0;
        mask = b.mode == M_LIST ? b.list : 1u << (b.reg + (b.mode == M_AN ? 8 : 0));
        check_ea(&a, A_CTRL | B(M_POST));
    } else {
        aerr("movem pide una lista de registros");
        return;
    }
    if (tomem && b.mode == M_PRE) {
        unsigned r = 0;
        int i;
        for (i = 0; i < 16; i++)
            if (mask & 1u << i) r |= 1u << (15 - i);
        mask = r;
    }
    ow((tomem ? 0x4880 : 0x4C80) | (cur->size == 'l') << 6 | ea_bits(tomem ? &b : &a));
    ow((int)mask);
    out_ea(tomem ? &b : &a, 0);
}

static void ins_movep(void)
{
    Ea s, d;
    nops(2);
    parse_ea(cur->opnd[0], &s);
    parse_ea(cur->opnd[1], &d);
    sizes("wl", 'w');
    if (s.mode == M_DN && (d.mode == M_D16 || d.mode == M_IND)) {
        ow(0x0188 | (cur->size == 'l') << 6 | s.reg << 9 | d.reg);
        ow(d.mode == M_D16 ? (int)(d.d.v & 0xFFFF) : 0);
    } else if (d.mode == M_DN && (s.mode == M_D16 || s.mode == M_IND)) {
        ow(0x0108 | (cur->size == 'l') << 6 | d.reg << 9 | s.reg);
        ow(s.mode == M_D16 ? (int)(s.d.v & 0xFFFF) : 0);
    } else {
        aerr("operandos no válidos en movep");
    }
}

/* una instrucción de un operando sobre <ea> (clr, neg, not, tst...) */
static void ins_unary(int base, const char *sz, int def, unsigned mask)
{
    Ea a;
    nops(1);
    parse_ea(cur->opnd[0], &a);
    sizes(sz, def);
    check_ea(&a, mask);
    if (a.mode == M_AN && cur->size == 'b') aerr("tamaño .b no válido con un registro de direcciones");
    ow(base | (strlen(sz) > 1 ? size_ss(cur->size) << 6 : 0) | ea_bits(&a));
    out_ea(&a, size_bytes(cur->size));
}

static Ea op1, op2;

static void ins_ctrl(int base)   /* jmp, jsr, pea */
{
    nops(1);
    parse_ea(cur->opnd[0], &op1);
    if (!strcmp(cur->op, "pea")) sizes("l", 'l');
    else if (cur->size) aerr("tamaño .%c no válido en %s", cur->size, cur->op);
    check_ea(&op1, A_CTRL);
    ow(base | ea_bits(&op1));
    out_ea(&op1, 0);
}

static int instruction(void)
{
    const char *op = cur->op;
    size_t n = strlen(op);
    int cc;
    if (!strcmp(op, "move")) { ins_move(); return 1; }
    if (!strcmp(op, "movea")) {
        nops(2);
        parse_ea(cur->opnd[1], &op2);
        if (op2.mode != M_AN) aerr("operando no válido: %s", op2.text);
        ins_move();
        return 1;
    }
    if (!strcmp(op, "moveq")) {
        nops(2);
        parse_ea(cur->opnd[0], &op1);
        parse_ea(cur->opnd[1], &op2);
        if (cur->size && cur->size != 'l') aerr("tamaño .%c no válido en moveq", cur->size);
        need_imm(&op1);
        if (op2.mode != M_DN) aerr("operando no válido: %s", op2.text);
        if (op1.d.rel || (afinal && (op1.d.v < -128 || op1.d.v > 127))) aerr("moveq va de -128 a 127");
        ow(0x7000 | op2.reg << 9 | (int)(op1.d.v & 0xFF));
        return 1;
    }
    if (!strcmp(op, "movem")) { ins_movem(); return 1; }
    if (!strcmp(op, "movep")) { ins_movep(); return 1; }
    if (!strcmp(op, "add") || !strcmp(op, "sub") || !strcmp(op, "cmp") || !strcmp(op, "and") ||
        !strcmp(op, "or") || !strcmp(op, "eor")) {
        nops(2);
        parse_ea(cur->opnd[0], &op1);
        parse_ea(cur->opnd[1], &op2);
        ins_arith(op, &op1, &op2);
        return 1;
    }
    if (!strcmp(op, "adda") || !strcmp(op, "suba") || !strcmp(op, "cmpa")) {
        nops(2);
        parse_ea(cur->opnd[0], &op1);
        parse_ea(cur->opnd[1], &op2);
        if (op2.mode != M_AN) aerr("operando no válido: %s", op2.text);
        check_ea(&op1, A_ALL);
        ins_arith(op[0] == 'a' ? "add" : op[0] == 's' ? "sub" : "cmp", &op1, &op2);
        return 1;
    }
    if (!strcmp(op, "addi") || !strcmp(op, "subi") || !strcmp(op, "cmpi") || !strcmp(op, "andi") ||
        !strcmp(op, "ori") || !strcmp(op, "eori")) {
        static const char *nm[] = {"ori", "andi", "subi", "addi", "", "eori", "cmpi"};
        int i;
        nops(2);
        parse_ea(cur->opnd[0], &op1);
        parse_ea(cur->opnd[1], &op2);
        for (i = 0; i < 7; i++)
            if (!strcmp(op, nm[i])) break;
        ins_imm(i << 9, &op1, &op2, i == 6);
        return 1;
    }
    if (!strcmp(op, "addq") || !strcmp(op, "subq")) {
        nops(2);
        parse_ea(cur->opnd[0], &op1);
        parse_ea(cur->opnd[1], &op2);
        need_imm(&op1);
        sizes("bwl", 'w');
        check_ea(&op2, A_ALT);
        if (op2.mode == M_AN && cur->size == 'b') aerr("tamaño .b no válido con un registro de direcciones");
        if (op1.d.rel || (afinal && (op1.d.v < 1 || op1.d.v > 8))) aerr("%s va de 1 a 8", op);
        ow((op[0] == 'a' ? 0x5000 : 0x5100) | (int)(op1.d.v & 7) << 9 | size_ss(cur->size) << 6 | ea_bits(&op2));
        out_ea(&op2, 0);
        return 1;
    }
    if (!strcmp(op, "addx") || !strcmp(op, "subx") || !strcmp(op, "abcd") || !strcmp(op, "sbcd")) {
        nops(2);
        parse_ea(cur->opnd[0], &op1);
        parse_ea(cur->opnd[1], &op2);
        ins_x(!strcmp(op, "addx") ? 0xD100 : !strcmp(op, "subx") ? 0x9100 : !strcmp(op, "abcd") ? 0xC100 : 0x8100,
              &op1, &op2, op[1] == 'b');
        return 1;
    }
    if (!strcmp(op, "cmpm")) {
        nops(2);
        parse_ea(cur->opnd[0], &op1);
        parse_ea(cur->opnd[1], &op2);
        sizes("bwl", 'w');
        if (op1.mode != M_POST || op2.mode != M_POST) aerr("cmpm va con (Ay)+,(Ax)+");
        ow(0xB108 | op2.reg << 9 | size_ss(cur->size) << 6 | op1.reg);
        return 1;
    }
    if (!strcmp(op, "muls") || !strcmp(op, "mulu")) { ins_muldiv(0, op[3] == 's', 0); return 1; }
    if (!strcmp(op, "divs") || !strcmp(op, "divu")) { ins_muldiv(1, op[3] == 's', 0); return 1; }
    if (!strcmp(op, "divsl") || !strcmp(op, "divul")) { ins_muldiv(1, op[3] == 's' || op[2] == 's', 1); return 1; }
    if (n == 3 && (op[2] == 'l' || op[2] == 'r') && (!strncmp(op, "as", 2) || !strncmp(op, "ls", 2) || !strncmp(op, "ro", 2))) {
        ins_shift(op[0] == 'a' ? 0 : op[0] == 'l' ? 1 : 3, op[2] == 'l');
        return 1;
    }
    if (n == 4 && !strncmp(op, "rox", 3) && (op[3] == 'l' || op[3] == 'r')) {
        ins_shift(2, op[3] == 'l');
        return 1;
    }
    if (!strcmp(op, "btst")) { ins_bit(0); return 1; }
    if (!strcmp(op, "bchg")) { ins_bit(1); return 1; }
    if (!strcmp(op, "bclr")) { ins_bit(2); return 1; }
    if (!strcmp(op, "bset")) { ins_bit(3); return 1; }
    {
        static const char *bfn[] = {"bftst", "bfextu", "bfchg", "bfexts", "bfclr", "bfffo", "bfset", "bfins", NULL};
        int i;
        for (i = 0; bfn[i]; i++)
            if (!strcmp(op, bfn[i])) { ins_bitfield(i); return 1; }
    }
    if (!strcmp(op, "clr")) { ins_unary(0x4200, "bwl", 'w', A_DALT); return 1; }
    if (!strcmp(op, "neg")) { ins_unary(0x4400, "bwl", 'w', A_DALT); return 1; }
    if (!strcmp(op, "negx")) { ins_unary(0x4000, "bwl", 'w', A_DALT); return 1; }
    if (!strcmp(op, "not")) { ins_unary(0x4600, "bwl", 'w', A_DALT); return 1; }
    if (!strcmp(op, "tst")) {
        nops(1);
        parse_ea(cur->opnd[0], &op1);
        if (op1.mode == M_AN || op1.mode == M_IMM || op1.mode == M_PCD || op1.mode == M_PCIDX) need020("tst con ese operando");
        ins_unary(0x4A00, "bwl", 'w', A_ALL);
        return 1;
    }
    if (!strcmp(op, "nbcd")) { ins_unary(0x4800, "b", 'b', A_DALT); return 1; }
    if (!strcmp(op, "tas")) { ins_unary(0x4AC0, "b", 'b', A_DALT); return 1; }
    if (op[0] == 's' && (cc = cond_code(op + 1)) >= 0) { ins_unary(0x50C0 | cc << 8, "b", 'b', A_DALT); return 1; }
    if (!strcmp(op, "lea")) {
        nops(2);
        parse_ea(cur->opnd[0], &op1);
        parse_ea(cur->opnd[1], &op2);
        sizes("l", 'l');
        check_ea(&op1, A_CTRL);
        if (op2.mode != M_AN) aerr("operando no válido: %s", op2.text);
        ow(0x41C0 | op2.reg << 9 | ea_bits(&op1));
        out_ea(&op1, 0);
        return 1;
    }
    if (!strcmp(op, "pea")) { ins_ctrl(0x4840); return 1; }
    if (!strcmp(op, "jmp")) { ins_ctrl(0x4EC0); return 1; }
    if (!strcmp(op, "jsr")) { ins_ctrl(0x4E80); return 1; }
    if (!strcmp(op, "chk")) {
        nops(2);
        parse_ea(cur->opnd[0], &op1);
        parse_ea(cur->opnd[1], &op2);
        sizes("wl", 'w');
        if (cur->size == 'l') need020("chk.l");
        check_ea(&op1, A_DATA);
        if (op2.mode != M_DN) aerr("operando no válido: %s", op2.text);
        ow((cur->size == 'l' ? 0x4100 : 0x4180) | op2.reg << 9 | ea_bits(&op1));
        out_ea(&op1, size_bytes(cur->size));
        return 1;
    }
    if (!strcmp(op, "ext") || !strcmp(op, "extb")) {
        nops(1);
        parse_ea(cur->opnd[0], &op1);
        if (op1.mode != M_DN) aerr("operando no válido: %s", op1.text);
        if (op[3] == 'b') {
            sizes("l", 'l');
            need020("extb");
            ow(0x49C0 | op1.reg);
        } else {
            sizes("wl", 'w');
            ow((cur->size == 'l' ? 0x48C0 : 0x4880) | op1.reg);
        }
        return 1;
    }
    if (!strcmp(op, "swap")) {
        nops(1);
        parse_ea(cur->opnd[0], &op1);
        sizes("w", 'w');
        if (op1.mode != M_DN) aerr("operando no válido: %s", op1.text);
        ow(0x4840 | op1.reg);
        return 1;
    }
    if (!strcmp(op, "exg")) {
        nops(2);
        parse_ea(cur->opnd[0], &op1);
        parse_ea(cur->opnd[1], &op2);
        sizes("l", 'l');
        if (op1.mode == M_DN && op2.mode == M_DN) ow(0xC140 | op1.reg << 9 | op2.reg);
        else if (op1.mode == M_AN && op2.mode == M_AN) ow(0xC148 | op1.reg << 9 | op2.reg);
        else if (op1.mode == M_DN && op2.mode == M_AN) ow(0xC188 | op1.reg << 9 | op2.reg);
        else if (op1.mode == M_AN && op2.mode == M_DN) ow(0xC188 | op2.reg << 9 | op1.reg);
        else aerr("operandos no válidos en exg");
        return 1;
    }
    if (!strcmp(op, "link")) {
        nops(2);
        parse_ea(cur->opnd[0], &op1);
        parse_ea(cur->opnd[1], &op2);
        sizes("wl", 'w');
        if (op1.mode != M_AN) aerr("operando no válido: %s", op1.text);
        need_imm(&op2);
        if (cur->size == 'l') {
            need020("link.l");
            ow(0x4808 | op1.reg);
            out_imm(&op2.d, 4);
        } else {
            if (afinal && (op2.d.v < -32768 || op2.d.v > 32767)) aerr("el valor no cabe en 16 bits: %ld", op2.d.v);
            ow(0x4E50 | op1.reg);
            out_imm(&op2.d, 2);
        }
        return 1;
    }
    if (!strcmp(op, "unlk")) {
        nops(1);
        parse_ea(cur->opnd[0], &op1);
        if (cur->size) aerr("tamaño .%c no válido en unlk", cur->size);
        if (op1.mode != M_AN) aerr("operando no válido: %s", op1.text);
        ow(0x4E58 | op1.reg);
        return 1;
    }
    if (!strcmp(op, "trap") || !strcmp(op, "stop") || !strcmp(op, "rtd")) {
        nops(1);
        parse_ea(cur->opnd[0], &op1);
        if (cur->size) aerr("tamaño .%c no válido en %s", cur->size, op);
        need_imm(&op1);
        if (op[0] == 't') {
            if (op1.d.rel || (afinal && (op1.d.v < 0 || op1.d.v > 15))) aerr("trap va de 0 a 15");
            ow(0x4E40 | (int)(op1.d.v & 15));
        } else {
            if (op[0] == 'r') need020("rtd");
            ow(op[0] == 's' ? 0x4E72 : 0x4E74);
            out_imm(&op1.d, 2);
        }
        return 1;
    }
    {
        static const struct { const char *n; int code; } solo[] = {
            {"nop", 0x4E71}, {"rts", 0x4E75}, {"rte", 0x4E73}, {"rtr", 0x4E77}, {"reset", 0x4E70},
            {"trapv", 0x4E76}, {"illegal", 0x4AFC}, {NULL, 0}
        };
        int i;
        for (i = 0; solo[i].n; i++)
            if (!strcmp(op, solo[i].n)) {
                if (cur->nopnd) aerr("%s pide 0 operandos", op);
                if (cur->size) aerr("tamaño .%c no válido en %s", cur->size, op);
                ow(solo[i].code);
                return 1;
            }
    }
    if (!strcmp(op, "bra")) { ins_branch(0); return 1; }
    if (!strcmp(op, "bsr")) { ins_branch(1); return 1; }
    if (op[0] == 'b' && (cc = cond_code(op + 1)) >= 2) { ins_branch(cc); return 1; }
    if (op[0] == 'd' && op[1] == 'b' && ((cc = cond_code(op + 2)) >= 0 || !strcmp(op, "dbra"))) {
        long d;
        if (!strcmp(op, "dbra")) cc = 1;
        nops(2);
        parse_ea(cur->opnd[0], &op1);
        if (cur->size && cur->size != 'w') aerr("tamaño .%c no válido en %s", cur->size, op);
        if (op1.mode != M_DN) aerr("operando no válido: %s", op1.text);
        d = branch_disp(cur->opnd[1], (long)ob.n + 2);
        if (afinal && (d < -32768 || d > 32767)) aerr("el salto no llega (%ld bytes)", d);
        ow(0x50C8 | cc << 8 | op1.reg);
        ow((int)(d & 0xFFFF));
        return 1;
    }
    return 0;
}

/* ---- las directivas ---- */
static void align2(void)
{
    if (ob.n & 1) buf_byte(&ob, 0);
}

static int datas(void)
{
    const char *op = cur->op;
    int i;
    if (!strcmp(op, "dc")) {
        int sz = cur->size ? cur->size : 'w';
        if (!strchr("bwl", sz)) aerr("tamaño .%c no válido en dc", sz);
        if (!cur->nopnd) aerr("dc pide al menos un valor");
        for (i = 0; i < cur->nopnd; i++) {
            const char *o = cur->opnd[i];
            size_t n = strlen(o);
            if (sz == 'b' && n >= 2 && (o[0] == '"' || o[0] == '\'') && o[n - 1] == o[0] && n != 3) {
                size_t k;
                for (k = 1; k + 1 < n; k++) buf_byte(&ob, (unsigned char)o[k]);
                continue;
            }
            {
                AVal v = expr(o, o + n);
                if (sz == 'l') {
                    if (v.rel) reloc_here(v.v);
                    ol(v.rel ? 0 : (uint32_t)v.v);
                } else {
                    if (v.rel) aerr("una etiqueta en dc va con dc.l");
                    if (afinal && sz == 'b' && (v.v < -128 || v.v > 255)) aerr("el valor no cabe en un byte: %ld", v.v);
                    if (afinal && sz == 'w' && (v.v < -32768 || v.v > 65535)) aerr("el valor no cabe en 16 bits: %ld", v.v);
                    if (sz == 'b') buf_byte(&ob, (int)(v.v & 0xFF));
                    else ow((int)v.v);
                }
            }
        }
        return 1;
    }
    if (!strcmp(op, "ds")) {
        int sz = cur->size ? cur->size : 'w';
        long k;
        if (!strchr("bwl", sz)) aerr("tamaño .%c no válido en ds", sz);
        nops(1);
        k = const_expr(cur->opnd[0]);
        if (k < 0 || k > 0x1000000) aerr("ds: tamaño no válido");
        for (k *= size_bytes(sz); k > 0; k--) buf_byte(&ob, 0);
        return 1;
    }
    if (!strcmp(op, "even")) {
        if (cur->nopnd) aerr("even pide 0 operandos");
        align2();
        return 1;
    }
    if (!strcmp(op, "incbin")) {
        const char *o;
        size_t n;
        char path[1024];
        long from = 0, count = -1, len;
        FILE *f;
        if (cur->nopnd < 1 || cur->nopnd > 3) aerr("incbin pide de 1 a 3 operandos");
        o = cur->opnd[0];
        n = strlen(o);
        if (n < 2 || (o[0] != '"' && o[0] != '\'') || o[n - 1] != o[0]) aerr("incbin va con el nombre del fichero entre comillas");
        if (cur->nopnd > 1) from = const_expr(cur->opnd[1]);
        if (cur->nopnd > 2) count = const_expr(cur->opnd[2]);
        {
            const char *src = src_files.v[cur_block->file], *slash = strrchr(src, '/');
            if (o[1] == '/' || !slash) snprintf(path, sizeof path, "%.*s", (int)(n - 2), o + 1);
            else snprintf(path, sizeof path, "%.*s%.*s", (int)(slash - src + 1), src, (int)(n - 2), o + 1);
#ifdef __amigaos__
            if (!slash && (slash = strrchr(src, ':')) != NULL && !strchr(o, ':'))
                snprintf(path, sizeof path, "%.*s%.*s", (int)(slash - src + 1), src, (int)(n - 2), o + 1);
#endif
        }
        f = fopen(path, "rb");
        if (!f) aerr("no se puede leer %s", path);
        fseek(f, 0, SEEK_END);
        len = ftell(f);
        if (from < 0 || from > len) { fclose(f); aerr("incbin: desde fuera del fichero"); }
        if (count < 0 || from + count > len) {
            if (count >= 0) { fclose(f); aerr("incbin: el fichero tiene %ld bytes", len); }
            count = len - from;
        }
        fseek(f, from, SEEK_SET);
        {
            size_t at = ob.n;
            for (n = 0; n < (size_t)count; n++) buf_byte(&ob, 0);
            if (fread(ob.p + at, 1, (size_t)count, f) != (size_t)count) { fclose(f); aerr("no se puede leer %s", path); }
        }
        fclose(f);
        return 1;
    }
    return 0;
}

/* ---- las líneas ---- */
static char *strip_spaces(const char *b, const char *e)
{
    char *r = xmalloc((size_t)(e - b) + 1), *w = r;
    char q = 0;
    for (; b < e; b++) {
        if (q) {
            if (*b == q) q = 0;
        } else if (*b == '"' || *b == '\'') {
            q = *b;
        } else if (*b == ' ' || *b == '\t') {
            continue;
        }
        *w++ = *b;
    }
    *w = 0;
    return r;
}

static void parse_lines(AsmBlock *bk)
{
    const char *s = bk->body;
    int line = bk->line;
    alines.n = 0;
    while (*s) {
        const char *e = strchr(s, '\n'), *p, *ce;
        ALine al;
        char q = 0;
        if (!e) e = s + strlen(s);
        memset(&al, 0, sizeof al);
        al.line = line;
        /* el comentario: ; fuera de comillas, o * al principio */
        for (ce = s; ce < e; ce++) {
            if (q) {
                if (*ce == q) q = 0;
            } else if (*ce == '"' || *ce == '\'') {
                q = *ce;
            } else if (*ce == ';') {
                break;
            }
        }
        while (ce > s && isspace((unsigned char)ce[-1])) ce--;
        p = s;
        while (p < ce && (*p == ' ' || *p == '\t')) p++;
        al.col = (int)(p - s) + 1;
        cur = &al;
        if (p < ce && *p == '*') p = ce;
        if (p < ce) {
            const char *w = p, *we;
            /* una etiqueta: nombre: o, en la columna 1, un nombre */
            if (is_id0((unsigned char)*w)) {
                we = w + 1;
                while (we < ce && is_idc((unsigned char)*we)) we++;
                if (we < ce && *we == ':') {
                    al.label = xstrndup(w, (size_t)(we - w));
                    p = we + 1;
                } else if (w == s) {
                    al.label = xstrndup(w, (size_t)(we - w));
                    p = we;
                }
            }
            while (p < ce && isspace((unsigned char)*p)) p++;
            if (p < ce) {
                const char *m = p, *me;
                while (p < ce && (is_idc((unsigned char)*p) || *p == '.')) p++;
                me = p;
                if (m == me && *p == '=' && al.label) {
                    /* NOMBRE = valor (en la columna 1) */
                    al.op = xstrndup("equ", 3);
                } else {
                    /* NOMBRE equ valor, NOMBRE = valor sin etiqueta */
                    const char *r = p;
                    while (r < ce && isspace((unsigned char)*r)) r++;
                    if (!al.label && m < me && is_id0((unsigned char)*m) && r < ce &&
                        ((*r == '=' && r[1] != '=') || (ce - r >= 3 && ieq(r, "equ", 3) && (ce - r == 3 || isspace((unsigned char)r[3]))))) {
                        al.label = xstrndup(m, (size_t)(me - m));
                        al.op = xstrndup("equ", 3);
                        p = r + (*r == '=' ? 1 : 3);
                    } else if (al.label && ce - m >= 3 && ieq(m, "equ", 3) && me - m == 3) {
                        al.op = xstrndup("equ", 3);
                    } else {
                        const char *dot = me;
                        size_t k;
                        if (m == me) aerr("instrucción no válida");
                        for (dot = m; dot < me && *dot != '.'; dot++) ;
                        al.op = xstrndup(m, (size_t)(dot - m));
                        for (k = 0; al.op[k]; k++) al.op[k] = (char)a_lower((unsigned char)al.op[k]);
                        if (dot < me) {
                            if (me - dot != 2) aerr("tamaño no válido: %.*s", (int)(me - m), m);
                            al.size = a_lower((unsigned char)dot[1]);
                            if (!strchr("bwls", al.size)) aerr("tamaño .%c no válido en %s", dot[1], al.op);
                        }
                    }
                }
                if (*p == '=' && al.op && !strcmp(al.op, "equ") && p < ce && p[1] != '=') p++;
                while (p < ce && isspace((unsigned char)*p)) p++;
                /* los operandos */
                while (p < ce) {
                    const char *c = top_comma(p, ce);
                    const char *x = p, *xe = c;
                    trim(&x, &xe);
                    if (x == xe) aerr("falta un operando");
                    al.opnd = xrealloc(al.opnd, sizeof(char *) * (size_t)(al.nopnd + 1));
                    al.opnd[al.nopnd++] = strip_spaces(x, xe);
                    if (c >= ce) break;
                    p = c + 1;
                    if (p >= ce) aerr("falta un operando");
                }
            }
        }
        if (al.label || al.op) VEC_PUSH(alines, al);
        cur = NULL;
        s = *e ? e + 1 : e;
        line++;
    }
}

/* ¿qué es la instrucción? para alinear lo que va delante */
static int wants_even(ALine *al)
{
    if (!al->op) return 0;
    if (!strcmp(al->op, "equ") || !strcmp(al->op, "even") || !strcmp(al->op, "incbin")) return 0;
    if ((!strcmp(al->op, "dc") || !strcmp(al->op, "ds")) && al->size == 'b') return 0;
    return 1;
}

static void define(ALine *al, long val, int rel)
{
    ASym *s = asym_find(al->label);
    if (s && s->pass == apass) aerr("%s ya está definido", al->label);
    if (!s) {
        ASym ns;
        memset(&ns, 0, sizeof ns);
        ns.name = al->label;
        VEC_PUSH(asyms, ns);
        s = &asyms.v[asyms.n - 1];
    } else if (s->val != val || s->rel != rel) {
        achanged = 1;
    }
    s->val = val;
    s->rel = rel;
    s->equ = !rel;
    s->pass = apass;
}

static void one_pass(void)
{
    int i;
    ob.n = 0;
    achanged = 0;
    for (i = 0; i < alines.n; i++) {
        ALine *al = &alines.v[i];
        cur = al;
        if (al->op && !strcmp(al->op, "equ")) {
            AVal v;
            if (!al->label) aerr("equ sin nombre");
            if (al->nopnd != 1) aerr("equ pide 1 operando");
            if (reg_num(al->label, strlen(al->label)) >= 0) aerr("%s es un registro", al->label);
            v = expr(al->opnd[0], al->opnd[0] + strlen(al->opnd[0]));
            define(al, v.v, v.rel);
            if (v.rel) asyms.v[asyms.n - 1].equ = 0;
            continue;
        }
        if (wants_even(al)) align2();
        else if (!al->op) {
            /* una etiqueta sola: la alinea lo que venga después (al final del bloque, el código de Dash) */
            int j = i + 1;
            while (j < alines.n && (!alines.v[j].op || !strcmp(alines.v[j].op, "equ"))) j++;
            if (j == alines.n || wants_even(&alines.v[j])) align2();
        }
        if (al->label) {
            if (reg_num(al->label, strlen(al->label)) >= 0 || ieq(al->label, "pc", strlen(al->label)))
                aerr("%s es un registro", al->label);
            define(al, (long)ob.n, 1);
        }
        if (!al->op) continue;
        if (datas()) continue;
        if (!instruction()) aerr("instrucción desconocida: %s", al->op);
    }
    cur = NULL;
    align2();
}

void asm_assemble(AsmBlock *bk, Buf *code, int cpu, AsmConstFn cfn, U32Vec *relocs)
{
    int i;
    cur_block = bk;
    acpu020 = cpu;
    aconst = cfn;
    orelocs = relocs;
    relocs->n = 0;
    asyms.n = 0;
    src_name = src_files.v[bk->file];
    parse_lines(bk);
    afinal = 0;
    for (i = 1, apass = 1; ; i++, apass++) {
        one_pass();
        if (!achanged && i > 1) break;
        if (i > 40) {
            cur = NULL;
            aerr("las etiquetas no se estabilizan");
        }
    }
    apass++;
    afinal = 1;
    one_pass();
    buf_bytes(code, ob.p, ob.n);
}
