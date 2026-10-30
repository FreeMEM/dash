/* import "ventana.dashui": las ventanas MUI del editor visual (JSON) como código Dash, igual que
   compiler/dashui.py de ./dash. Por cada ventana, un struct con un campo por objeto con nombre (y window) y una
   función <Nombre>_create() que la construye con los builtins mui_ y devuelve el struct. Formato:
   docs/MUI_EDITOR.md. */
#include <ctype.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "dashc.h"

/* (las tablas de abajo dejan sin dar las listas de JVal: van a cero) */
#pragma GCC diagnostic ignored "-Wmissing-field-initializers"

/* ---- JSON ---- */
enum { J_NULL, J_BOOL, J_INT, J_STR, J_ARR, J_OBJ };

typedef struct JVal JVal;
struct JVal {
    int kind;
    long num;                                  /* J_BOOL, J_INT */
    char *str;                                 /* J_STR (UTF-8) */
    struct { JVal **v; int n, cap; } items;    /* J_ARR; J_OBJ: los valores */
    struct { char **v; int n, cap; } keys;     /* J_OBJ */
};

static const char *jp, *jfile;

static void jfail(const char *what)
{
    fatal("%s: no es un JSON válido (%s)", jfile, what);
}

static void jspace(void)
{
    while (*jp == ' ' || *jp == '\t' || *jp == '\n' || *jp == '\r') jp++;
}

static void utf8(Buf *b, unsigned cp)
{
    if (cp < 0x80) {
        buf_byte(b, (int)cp);
    } else if (cp < 0x800) {
        buf_byte(b, 0xC0 | cp >> 6);
        buf_byte(b, 0x80 | (cp & 63));
    } else {
        buf_byte(b, 0xE0 | cp >> 12);
        buf_byte(b, 0x80 | (cp >> 6 & 63));
        buf_byte(b, 0x80 | (cp & 63));
    }
}

static char *jstring(void)
{
    Buf b = {0};
    if (*jp++ != '"') jfail("se esperaba un texto");
    while (*jp != '"') {
        if (!*jp) jfail("texto sin cerrar");
        if (*jp == '\\') {
            jp++;
            switch (*jp) {
            case 'n': buf_byte(&b, '\n'); break;
            case 't': buf_byte(&b, '\t'); break;
            case 'r': buf_byte(&b, '\r'); break;
            case 'b': buf_byte(&b, 8); break;
            case 'f': buf_byte(&b, 12); break;
            case 'u': {
                unsigned cp = 0;
                int i;
                for (i = 0; i < 4; i++) {
                    char c = *++jp;
                    if (!isxdigit((unsigned char)c)) jfail("\\u sin sus cuatro cifras");
                    cp = cp * 16 + (unsigned)(isdigit((unsigned char)c) ? c - '0' : tolower((unsigned char)c) - 'a' + 10);
                }
                utf8(&b, cp);
                break;
            }
            default: buf_byte(&b, *jp);
            }
            jp++;
        } else {
            buf_byte(&b, (unsigned char)*jp++);
        }
    }
    jp++;
    buf_byte(&b, 0);
    return (char *)b.p;
}

static JVal *jvalue(void)
{
    JVal *v = xmalloc(sizeof(JVal));
    jspace();
    if (*jp == '{') {
        v->kind = J_OBJ;
        jp++;
        jspace();
        if (*jp == '}') {
            jp++;
            return v;
        }
        for (;;) {
            char *k;
            jspace();
            k = jstring();
            jspace();
            if (*jp++ != ':') jfail("falta ':'");
            VEC_PUSH(v->keys, k);
            VEC_PUSH(v->items, jvalue());
            jspace();
            if (*jp == ',') { jp++; continue; }
            if (*jp++ != '}') jfail("falta '}'");
            return v;
        }
    }
    if (*jp == '[') {
        v->kind = J_ARR;
        jp++;
        jspace();
        if (*jp == ']') {
            jp++;
            return v;
        }
        for (;;) {
            VEC_PUSH(v->items, jvalue());
            jspace();
            if (*jp == ',') { jp++; continue; }
            if (*jp++ != ']') jfail("falta ']'");
            return v;
        }
    }
    if (*jp == '"') {
        v->kind = J_STR;
        v->str = jstring();
        return v;
    }
    if (*jp == '-' || isdigit((unsigned char)*jp)) {
        char *end;
        double d = strtod(jp, &end);
        v->kind = J_INT;
        v->num = (long)d;
        if (d != (double)v->num) v->kind = J_NULL;   /* (un número con decimales: no es un entero) */
        jp = end;
        return v;
    }
    if (!strncmp(jp, "true", 4) || !strncmp(jp, "false", 5)) {
        v->kind = J_BOOL;
        v->num = *jp == 't';
        jp += v->num ? 4 : 5;
        return v;
    }
    if (!strncmp(jp, "null", 4)) {
        jp += 4;
        return v;
    }
    jfail("valor desconocido");
    return NULL;
}

static JVal *jget(JVal *o, const char *key)
{
    int i;
    if (!o || o->kind != J_OBJ) return NULL;
    for (i = 0; i < o->keys.n; i++)
        if (!strcmp(o->keys.v[i], key)) return o->items.v[i];
    return NULL;
}

static int jtrue(JVal *v)
{
    return v && ((v->kind == J_BOOL && v->num) || (v->kind == J_INT && v->num) || (v->kind == J_STR && v->str[0]) ||
                 v->kind == J_ARR || v->kind == J_OBJ);
}

/* ---- el código Dash ---- */
static const char *where;

static void uifail(const char *fmt, ...)
{
    char msg[600];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(msg, sizeof msg, fmt, ap);
    va_end(ap);
    fatal("%s: %s", where, msg);
}

static void out(Buf *b, const char *fmt, ...)
{
    char tmp[2048];
    va_list ap;
    int n;
    va_start(ap, fmt);
    n = vsnprintf(tmp, sizeof tmp, fmt, ap);
    va_end(ap);
    buf_bytes(b, tmp, (size_t)(n < (int)sizeof tmp ? n : (int)sizeof tmp - 1));
}

static long jint(JVal *v, const char *what)
{
    if (!v || v->kind != J_INT) uifail("%s tiene que ser un número entero", what);
    return v->num;
}

/* [r, g, b], cada uno de 0 a 255 ("background", "color": el tema oscuro de Forja), como "r, g, b" */
static const char *jrgb(JVal *v, const char *what)
{
    static char buf[40];
    int i;
    if (!v || v->kind != J_ARR || v->items.n != 3) uifail("%s es [r, g, b], cada uno de 0 a 255", what);
    for (i = 0; i < 3; i++)
        if (v->items.v[i]->kind != J_INT || v->items.v[i]->num < 0 || v->items.v[i]->num > 255)
            uifail("%s es [r, g, b], cada uno de 0 a 255", what);
    snprintf(buf, sizeof buf, "%ld, %ld, %ld", v->items.v[0]->num, v->items.v[1]->num, v->items.v[2]->num);
    return buf;
}

/* las palabras del lenguaje (las del editor, media/model.js), menos las de los On */
static void check_name(const char *name, const char *what)
{
    static const char *const words[] = {
        "func", "end", "if", "elif", "else", "while", "for", "in", "step", "return", "break", "continue", "var",
        "const", "Main", "Print", "and", "or", "not", "true", "false", "nil", "struct", "enum", "import", "Window",
        "EventLoop", "Stop", "Wait", "fn", "interface", "weak", NULL
    };
    const char *s = name;
    int i;
    if (!name || !(isalpha((unsigned char)*s) || *s == '_'))
        uifail("nombre de %s malo: %s (letras sin acentos, cifras y _, sin empezar por cifra)", what, name ? name : "nada");
    for (; *s; s++)
        if (!isalnum((unsigned char)*s) && *s != '_')
            uifail("nombre de %s malo: %s (letras sin acentos, cifras y _, sin empezar por cifra)", what, name);
    for (i = 0; words[i]; i++)
        if (!strcmp(words[i], name)) uifail("el nombre de %s %s es una palabra del lenguaje", what, name);
}

/* un texto como literal de Dash */
static void dash_string(Buf *b, const char *t)
{
    buf_byte(b, '"');
    for (; *t; t++) {
        unsigned char c = (unsigned char)*t;
        if (c == '\\') out(b, "\\\\");
        else if (c == '"') out(b, "\\\"");
        else if (c == '\n') out(b, "\\n");
        else if (c < 32 || c == 127) out(b, "\\%03o", c);   /* \33 (ESC) de los códigos de texto de MUI */
        else buf_byte(b, c);
        if (c == '#' && t[1] == '{') uifail("un texto con '#{' no vale (se leería como interpolación)");
    }
    buf_byte(b, '"');
}

static void value(Buf *b, JVal *v)
{
    if (!v || v->kind == J_NULL) uifail("valor no admitido");
    if (v->kind == J_BOOL) out(b, v->num ? "true" : "false");
    else if (v->kind == J_INT) out(b, "%ld", v->num);
    else if (v->kind == J_STR) dash_string(b, v->str);
    else uifail("valor no admitido");
}

/* qué texto lleva "tr": número (dashweb D71) */
static const char *main_text(const char *kind)
{
    static const char *const t[][2] = {
        {"text", "text"}, {"label", "text"}, {"button", "label"}, {"string", "text"}, {"cycle", "options"},
        {"combo", "text"}, {"frame", "title"}, {"tabs", "titles"}, {"window", "title"}, {"menu", "title"},
        {"item", "label"}, {NULL, NULL}
    };
    int i;
    for (i = 0; t[i][0]; i++)
        if (!strcmp(t[i][0], kind)) return t[i][1];
    return NULL;
}

/* el número de catálogo del campo field, o -1 */
static long tr_id(JVal *node, const char *kind, const char *field)
{
    JVal *tr = jget(node, "tr"), *f;
    if (!tr) return -1;
    if (tr->kind == J_INT) {
        const char *m = main_text(kind);
        if (!m) uifail("un %s no tiene texto para \"tr\"", kind);
        return !strcmp(m, field) ? tr->num : -1;
    }
    if (tr->kind != J_OBJ) uifail("\"tr\" tiene que ser un número o {\"campo\": número}");
    f = jget(tr, field);
    return f ? jint(f, "\"tr\"") : -1;
}

/* una propiedad como Dash: un texto con número de catálogo va con tr() */
static void text(Buf *b, JVal *node, const char *kind, const char *field, JVal *def)
{
    JVal *v = jget(node, field);
    long id = tr_id(node, kind, field);
    if (!v) v = def;
    if (id >= 0 && v->kind == J_STR) {
        out(b, "tr(%ld, ", id);
        value(b, v);
        out(b, ")");
    } else {
        value(b, v);
    }
}

typedef struct { const char *type, *builtin, *props[3]; JVal defs[3]; int group; } Kind;

static Kind kinds[] = {
    {"text", "mui_text", {"text"}, {{J_STR, 0, ""}}, 0},
    {"label", "mui_label", {"text"}, {{J_STR, 0, ""}}, 0},
    {"button", "mui_button", {"label"}, {{J_STR, 0, ""}}, 0},
    {"string", "mui_string", {"text", "max"}, {{J_STR, 0, ""}, {J_INT, 80, NULL}}, 0},
    {"checkbox", "mui_checkbox", {"checked"}, {{J_BOOL, 0, NULL}}, 0},
    {"cycle", "mui_cycle", {"options"}, {{J_STR, 0, ""}}, 0},
    {"slider", "mui_slider", {"min", "max", "value"}, {{J_INT, 0, NULL}, {J_INT, 100, NULL}, {J_INT, 0, NULL}}, 0},
    {"gauge", "mui_gauge", {"max"}, {{J_INT, 100, NULL}}, 0},
    {"list", "mui_list", {NULL}, {{0}}, 0},
    {"canvas", "mui_canvas", {"min_width", "min_height"}, {{J_INT, 64, NULL}, {J_INT, 32, NULL}}, 0},
    {"scrollbar", "mui_scrollbar", {"vertical"}, {{J_BOOL, 1, NULL}}, 0},
    {"image", "mui_image", {"file"}, {{J_STR, 0, ""}}, 0},
    {"image_button", "mui_image_button", {"file"}, {{J_STR, 0, ""}}, 0},
    {"image_toggle", "mui_image_toggle", {"file", "group", "checked"},
     {{J_STR, 0, ""}, {J_INT, 0, NULL}, {J_BOOL, 0, NULL}}, 0},
    {"combo", "mui_combo", {"text", "options"}, {{J_STR, 0, ""}, {J_STR, 0, ""}}, 0},
    {"space", "mui_space", {NULL}, {{0}}, 0},
    {"balance", "mui_balance", {NULL}, {{0}}, 0},
    {"vgroup", "mui_vgroup_begin", {NULL}, {{0}}, 1},
    {"hgroup", "mui_hgroup_begin", {NULL}, {{0}}, 1},
    {"frame", "mui_frame_begin", {"title", "horizontal"}, {{J_STR, 0, ""}, {J_BOOL, 0, NULL}}, 1},
    {"columns", "mui_columns_begin", {"columns"}, {{J_INT, 2, NULL}}, 1},
    {"tabs", "mui_register_begin", {"titles"}, {{J_STR, 0, ""}}, 1},
    {"scroll", "mui_scroll_begin", {NULL}, {{0}}, 1},
    {NULL, NULL, {NULL}, {{0}}, 0}
};

static const char *const events[][2] = {
    {"event", "mui_on_press"}, {"change", "mui_on_change"}, {"ack", "mui_on_ack"}, {"double", "mui_on_double"},
    {NULL, NULL}
};

typedef struct {
    Buf lines, after;
    struct { const char **v; int n, cap; } fields, ctx;
    int autos;
} Win;

/* el nombre de la variable de un objeto: _ui_nombre (un campo del struct), _uiN si hace falta y no tiene */
static const char *var_for(Win *w, JVal *node, int needs)
{
    JVal *n = jget(node, "name");
    static char buf[300];
    int i;
    if (n && n->kind == J_STR && n->str[0]) {
        if (!strcmp(n->str, "window")) uifail("el nombre de objeto 'window' es el de la ventana");
        check_name(n->str, "objeto");
        for (i = 0; i < w->fields.n; i++)
            if (!strcmp(w->fields.v[i], n->str)) uifail("el nombre de objeto %s está dos veces", n->str);
        VEC_PUSH(w->fields, n->str);
        snprintf(buf, sizeof buf, "_ui_%s", n->str);
        return buf;
    }
    if (needs) {
        snprintf(buf, sizeof buf, "_ui%d", ++w->autos);
        return buf;
    }
    return "";
}

static void indent(Buf *b, int depth)
{
    int i;
    for (i = 0; i < depth; i++) out(b, "    ");
}

static void gen_node(Win *w, JVal *node, int depth)
{
    JVal *t = jget(node, "type"), *ch;
    Kind *k;
    int i, needs, nev = 0;
    char var[300];
    const char *kind;
    if (!node || node->kind != J_OBJ || !t || t->kind != J_STR) uifail("un objeto sin 'type'");
    kind = t->str;
    for (k = kinds; k->type && strcmp(k->type, kind); k++)
        ;
    if (!k->type) uifail("tipo de objeto desconocido: %s", kind);
    for (i = 0; events[i][0]; i++) nev += jget(node, events[i][0]) != NULL;
    needs = nev || jget(node, "weight") || jget(node, "disabled") || jget(node, "hidden") || jget(node, "help") ||
            jget(node, "background") || jget(node, "color") ||
            jtrue(jget(node, "context_menu")) || jtrue(jget(node, "take_tab"));
    snprintf(var, sizeof var, "%s", var_for(w, node, needs));
    indent(&w->lines, depth);
    if (var[0]) out(&w->lines, "%s = ", var);
    out(&w->lines, "%s(", k->builtin);
    for (i = 0; i < 3 && k->props[i]; i++) {
        if (i) out(&w->lines, ", ");
        text(&w->lines, node, kind, k->props[i], &k->defs[i]);
    }
    out(&w->lines, ")\n");
    for (i = 0; events[i][0]; i++)
        if (jget(node, events[i][0])) out(&w->after, "    %s(%s, %ld)\n", events[i][1], var, jint(jget(node, events[i][0]), events[i][0]));
    if (jget(node, "weight")) out(&w->after, "    mui_weight(%s, %ld)\n", var, jint(jget(node, "weight"), "weight"));
    if (jtrue(jget(node, "disabled"))) out(&w->after, "    mui_set_enabled(%s, false)\n", var);
    if (jtrue(jget(node, "hidden"))) out(&w->after, "    mui_set_visible(%s, false)\n", var);
    if (jtrue(jget(node, "help"))) {
        JVal empty = {J_STR, 0, "", {0}, {0}};
        out(&w->after, "    mui_help(%s, ", var);
        text(&w->after, node, kind, "help", &empty);
        out(&w->after, ")\n");
    }
    if (jget(node, "background")) out(&w->after, "    mui_set_background(%s, %s)\n", var, jrgb(jget(node, "background"), "\"background\""));
    if (jget(node, "color")) {
        if (strcmp(kind, "text") && strcmp(kind, "label") && strcmp(kind, "button"))
            uifail("\"color\" es de un text, label o button, no de un %s", kind);
        out(&w->after, "    mui_set_text_pen(%s, %s)\n", var, jrgb(jget(node, "color"), "\"color\""));
    }
    if (jtrue(jget(node, "take_tab"))) {
        if (strcmp(kind, "canvas")) uifail("\"take_tab\" es de un canvas, no de un %s", kind);
        out(&w->after, "    mui_canvas_take_tab(%s, true)\n", var);
    }
    if (jtrue(jget(node, "context_menu"))) {
        const char *menu = jget(node, "context_menu")->str;
        int found = 0;
        for (i = 0; i < w->ctx.n; i++) found |= !strcmp(w->ctx.v[i], menu);
        if (!found) uifail("%s tiene \"context_menu\": %s, que no es de los \"context_menus\" de la ventana", kind, menu);
        out(&w->after, "    mui_set_context_menu(%s, _ui_%s)\n", var, menu);
    }
    ch = jget(node, "children");
    if (k->group) {
        for (i = 0; ch && ch->kind == J_ARR && i < ch->items.n; i++) gen_node(w, ch->items.v[i], depth + 1);
        indent(&w->lines, depth);
        out(&w->lines, "mui_group_end()\n");
    } else if (jtrue(ch) && ch->items.n) {
        uifail("un %s no puede tener hijos", kind);
    }
}

/* un menú, una opción o un submenú: con "name", un campo de la ventana; "disabled" lo pone gris */
static void named(Win *w, JVal *node, int depth, const char *call)
{
    char var[300];
    snprintf(var, sizeof var, "%s", var_for(w, node, jtrue(jget(node, "disabled"))));
    indent(&w->lines, depth);
    if (var[0]) out(&w->lines, "%s = ", var);
    out(&w->lines, "%s\n", call);
    if (jtrue(jget(node, "disabled"))) out(&w->after, "    mui_set_enabled(%s, false)\n", var);
}

static char *as_text(JVal *node, const char *kind, const char *field)
{
    Buf b = {0};
    JVal empty = {J_STR, 0, "", {0}, {0}};
    text(&b, node, kind, field, &empty);
    buf_byte(&b, 0);
    return (char *)b.p;
}

static void menu_item(Win *w, JVal *item, int depth, int top)
{
    char call[2048];
    char *label;
    JVal *sub;
    int i;
    if (!item || item->kind != J_OBJ) uifail("una opción de menú tiene que ser un objeto");
    if (jtrue(jget(item, "separator"))) {
        indent(&w->lines, depth);
        out(&w->lines, "mui_menu_separator()\n");
        return;
    }
    label = as_text(item, "item", "label");
    if (jget(item, "checked") && !jtrue(jget(item, "check")))
        uifail("la opción %s tiene \"checked\" sin \"check\": true", label);
    if ((sub = jget(item, "submenu")) != NULL) {
        if (!top) uifail("opción %s: un submenú no puede tener otro dentro", label);
        if (sub->kind != J_ARR) uifail("opción %s: \"submenu\" tiene que ser una lista de opciones", label);
        if (jget(item, "key") || jget(item, "event") || jget(item, "check"))
            uifail("opción %s: un submenú no lleva key, event ni check (sus opciones sí)", label);
        snprintf(call, sizeof call, "mui_submenu_begin(%s)", label);
        named(w, item, depth, call);
        for (i = 0; i < sub->items.n; i++) menu_item(w, sub->items.v[i], depth + 1, 0);
        indent(&w->lines, depth);
        out(&w->lines, "mui_submenu_end()\n");
        return;
    }
    {
        Buf key = {0};
        JVal *k = jget(item, "key"), *ev = jget(item, "event");
        long event = ev ? jint(ev, "el evento de un menú") : 0;
        dash_string(&key, k && k->kind == J_STR ? k->str : "");
        buf_byte(&key, 0);
        if (jtrue(jget(item, "check"))) {
            JVal *c = jget(item, "checked");
            if (c && c->kind != J_BOOL) uifail("opción %s: \"checked\" tiene que ser true o false", label);
            snprintf(call, sizeof call, "mui_menu_check(%s, %s, %ld, %s)", label, (char *)key.p, event,
                     c && c->num ? "true" : "false");
        } else {
            snprintf(call, sizeof call, "mui_menu_item(%s, %s, %ld)", label, (char *)key.p, event);
        }
        named(w, item, depth, call);
    }
}

static void gen_window(Buf *o, JVal *win)
{
    Win w;
    JVal *name = jget(win, "name"), *ctx = jget(win, "context_menus"), *menus = jget(win, "menus"), *root, *v;
    int i, j;
    char *title;
    memset(&w, 0, sizeof w);
    check_name(name && name->kind == J_STR ? name->str : NULL, "ventana");
    if (ctx && ctx->kind != J_ARR) uifail("\"context_menus\" tiene que ser una lista de menús");
    for (i = 0; ctx && i < ctx->items.n; i++) {
        JVal *m = ctx->items.v[i], *mn = jget(m, "name");
        if (!mn || mn->kind != J_STR || !mn->str[0])
            uifail("un menú de contexto necesita \"name\" (los objetos lo dan como \"context_menu\")");
        VEC_PUSH(w.ctx, mn->str);
    }
    {
        JVal def = {J_STR, 0, name->str, {0}, {0}};
        Buf t = {0};
        text(&t, win, "window", "title", &def);
        buf_byte(&t, 0);
        title = (char *)t.p;
    }
    out(&w.lines, "    _window = mui_window_begin(%s, %ld)\n", title, (v = jget(win, "id")) ? jint(v, "id") : 0L);
    for (i = 0; menus && menus->kind == J_ARR && i < menus->items.n; i++) {
        JVal *m = menus->items.v[i], *items = jget(m, "items");
        char call[2048];
        snprintf(call, sizeof call, "mui_menu_begin(%s)", as_text(m, "menu", "title"));
        named(&w, m, 2, call);
        for (j = 0; items && items->kind == J_ARR && j < items->items.n; j++) menu_item(&w, items->items.v[j], 3, 1);
        out(&w.lines, "        mui_menu_end()\n");
    }
    root = jget(win, "root");
    if (jtrue(root)) {
        JVal *rt = jget(root, "type");
        /* el grupo de la ventana ya es vertical: un vgroup raíz va directo dentro */
        if (rt && rt->kind == J_STR && !strcmp(rt->str, "vgroup") && !jtrue(jget(root, "name")) &&
            !jget(root, "weight") && !jget(root, "disabled") && !jget(root, "hidden") && !jget(root, "help") &&
            !jget(root, "background")) {
            JVal *ch = jget(root, "children");
            for (i = 0; ch && ch->kind == J_ARR && i < ch->items.n; i++) gen_node(&w, ch->items.v[i], 2);
        } else {
            gen_node(&w, root, 2);
        }
    }
    out(&w.lines, "    mui_window_end()\n");
    for (i = 0; ctx && i < ctx->items.n; i++) {
        JVal *m = ctx->items.v[i], *items = jget(m, "items");
        char call[2048];
        snprintf(call, sizeof call, "mui_context_menu_begin(%s)", as_text(m, "menu", "title"));
        named(&w, m, 1, call);
        for (j = 0; items && items->kind == J_ARR && j < items->items.n; j++) menu_item(&w, items->items.v[j], 2, 1);
        out(&w.lines, "    mui_menu_end()\n");
    }
    if ((v = jget(win, "close")) != NULL) out(&w.after, "    mui_on_close(_window, %ld)\n", jint(v, "close"));
    if ((v = jget(win, "background")) != NULL)   /* (el de su grupo raíz) */
        out(&w.after, "    mui_set_background(_window, %s)\n", jrgb(v, "\"background\""));
    if ((v = jget(win, "size")) != NULL) {
        if (v->kind != J_ARR || v->items.n != 2 || v->items.v[0]->kind != J_INT || v->items.v[1]->kind != J_INT)
            uifail("\"size\" es [ancho, alto] en tanto por ciento");
        out(&w.after, "    mui_window_size(_window, %ld, %ld)\n", v->items.v[0]->num, v->items.v[1]->num);
    }
    out(o, "struct %s\n    window: Int\n", name->str);
    for (i = 0; i < w.fields.n; i++) out(o, "    %s: Int\n", w.fields.v[i]);
    out(o, "end\n\nfunc %s_create() -> %s\n", name->str, name->str);
    buf_bytes(o, w.lines.p, w.lines.n);
    buf_bytes(o, w.after.p, w.after.n);
    out(o, "    return %s(_window", name->str);
    for (i = 0; i < w.fields.n; i++) out(o, ", _ui_%s", w.fields.v[i]);
    out(o, ")\nend\n\n");
}

/* el código Dash de las ventanas de un .dashui (el texto JSON) */
char *dashui_generate(const char *json, const char *filename)
{
    JVal *data, *ver, *wins;
    Buf o = {0};
    int i, j;
    char w[600];
    jp = json;
    jfile = filename;
    data = jvalue();
    ver = jget(data, "dashui");
    if (!ver || ver->kind != J_INT || ver->num != 1)
        fatal("%s: no es un .dashui de la versión 1 (\"dashui\": 1)", filename);
    out(&o, "# Hecho de %s (ventanas MUI, docs/MUI_EDITOR.md)\n\n", filename);
    wins = jget(data, "windows");
    for (i = 0; wins && wins->kind == J_ARR && i < wins->items.n; i++) {
        JVal *win = wins->items.v[i], *n = jget(win, "name");
        snprintf(w, sizeof w, "%s: ventana %d", filename, i + 1);
        where = w;
        if (!win || win->kind != J_OBJ) uifail("no es un objeto");
        for (j = 0; j < i; j++) {
            JVal *m = jget(wins->items.v[j], "name");
            if (n && m && n->kind == J_STR && m->kind == J_STR && !strcmp(n->str, m->str))
                uifail("el nombre de ventana %s está dos veces", n->str);
        }
        gen_window(&o, win);
    }
    buf_byte(&o, 0);
    return (char *)o.p;
}
