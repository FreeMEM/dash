/* Generador de AArch64 de dashc (docs/AARCH64_LOOP.md, fase A4): operandos y operaciones con valores de Dash. Lo
   incluye gen68k.c (con -DDASH_A64) donde va t68k_ops.c, con las mismas funciones. Ver ta64_base.c. */

/* ---- codificación ---- */
static void wrote(int x) { if (x == 0) x0_dirty = 1; }

static void mov_reg(int d, int s)                      /* mov xd, xs */
{
    if (d == s) return;
    if (d == 31 || s == 31) ins(0x91000000 | (uint32_t)s << 5 | (uint32_t)d);   /* (sp: add #0) */
    else ins(0xAA0003E0 | (uint32_t)s << 16 | (uint32_t)d);
    wrote(d);
}

static void mov_imm(int d, long v)                     /* xd = v (64 bits) */
{
    uint64_t u = (uint64_t)v;
    int i, first = 1, neg = v < 0;
    uint64_t base = neg ? ~(uint64_t)0 : 0;
    for (i = 0; i < 4; i++) {
        uint32_t h = (uint32_t)(u >> (16 * i)) & 0xFFFF;
        if (h == (uint32_t)(base & 0xFFFF) && !(i == 3 && first)) continue;
        if (first) {
            if (neg) ins(0x92800000 | (uint32_t)i << 21 | (~h & 0xFFFF) << 5 | (uint32_t)d);   /* movn */
            else ins(0xD2800000 | (uint32_t)i << 21 | h << 5 | (uint32_t)d);                 /* movz */
            first = 0;
        } else {
            ins(0xF2800000 | (uint32_t)i << 21 | h << 5 | (uint32_t)d);                       /* movk */
        }
    }
    if (first) ins(neg ? 0x92800000 | (uint32_t)d : 0xD2800000 | (uint32_t)d);   /* 0 o -1 */
    wrote(d);
}

static void add_imm(int d, int n, long k)              /* xd = xn + k (cualquier k) */
{
    if (k == 0) { mov_reg(d, n); return; }
    if (k > 0 && k < 4096) ins(0x91000000 | (uint32_t)k << 10 | (uint32_t)n << 5 | (uint32_t)d);
    else if (k < 0 && k > -4096) ins(0xD1000000 | (uint32_t)-k << 10 | (uint32_t)n << 5 | (uint32_t)d);
    else {
        int t = n == XT ? XT2 : XT;
        mov_imm(t, k);
        ins(0x8B000000 | (uint32_t)t << 16 | (uint32_t)n << 5 | (uint32_t)d);   /* add xd, xn, xt (n != sp) */
        if (n == 31) a64_todo("add a sp grande");
    }
    wrote(d);
}

/* ldr/str de 64 (size 3), 32 con signo (load: ldrsw) o 32 (store) en [xn + off] */
static void mem64(int load, int t, int n, long off)
{
    if (off >= 0 && off < 32768 && !(off & 7))
        ins((load ? 0xF9400000 : 0xF9000000) | (uint32_t)(off / 8) << 10 | (uint32_t)n << 5 | (uint32_t)t);
    else if (off >= -256 && off < 256)
        ins((load ? 0xF8400000 : 0xF8000000) | ((uint32_t)off & 0x1FF) << 12 | (uint32_t)n << 5 | (uint32_t)t);
    else {
        add_imm(XT2, n, off);
        ins((load ? 0xF9400000 : 0xF9000000) | (uint32_t)XT2 << 5 | (uint32_t)t);
    }
    if (load) wrote(t);
}

static void ldrsw(int t, int n, long off)              /* xt = el LONG de [xn + off], con signo */
{
    if (off >= 0 && off < 16384 && !(off & 3)) ins(0xB9800000 | (uint32_t)(off / 4) << 10 | (uint32_t)n << 5 | (uint32_t)t);
    else ins(0xB8800000 | ((uint32_t)off & 0x1FF) << 12 | (uint32_t)n << 5 | (uint32_t)t);
    wrote(t);
}

static void ldrw(int t, int n, long off)               /* xt = el ULONG de [xn + off] */
{
    ins(0xB9400000 | (uint32_t)(off / 4) << 10 | (uint32_t)n << 5 | (uint32_t)t);
    wrote(t);
}

static void push_x(int t)                              /* str xt, [sp, #-16]! */
{
    ins(0xF81F0FE0 | (uint32_t)t);
    sp_depth += SLOT;
}

static void pop_x(int t)                               /* ldr xt, [sp], #16 */
{
    ins(0xF84107E0 | (uint32_t)t);
    sp_depth -= SLOT;
    wrote(t);
}

static void sxtw(int d) { ins(0x93407C00 | (uint32_t)d << 5 | (uint32_t)d); }   /* (no toca las banderas) */

/* operaciones de Int (en w, el resultado extendido): op = 'a' add, 's' sub, '&', '|', '^', '*', '/', '%', '<' lsl, '>' asr */
static void wop(int op, int d, int n, int m)
{
    uint32_t r = (uint32_t)m << 16 | (uint32_t)n << 5 | (uint32_t)d;
    switch (op) {   /* (add, sub y and ponen las banderas, como en el 68000: el recorrido a veces las usa) */
    case 'a': ins(0x2B000000 | r); sxtw(d); x0_dirty = 0; return;   /* adds */
    case 's': ins(0x6B000000 | r); sxtw(d); x0_dirty = 0; return;   /* subs */
    case '&': ins(0x6A000000 | r); sxtw(d); x0_dirty = 0; return;   /* ands */
    case '|': ins(0x2A000000 | r); break;
    case '^': ins(0x4A000000 | r); break;
    case '*': ins(0x1B007C00 | r); break;
    case '<': ins(0x1AC02000 | r); break;
    case '>': ins(0x1AC02800 | r); break;
    case '/': case '%': {
        int ok = new_label();
        fixup(ok, 5);
        ins(0x35000000 | (uint32_t)m);                 /* cbnz wm, ok */
        call_sym("_dl_div_zero", 0);                   /* (no vuelve: "división por cero") */
        def_label(ok);
        if (op == '/') ins(0x1AC00C00 | r);            /* sdiv */
        else {
            ins(0x1AC00C00 | (uint32_t)m << 16 | (uint32_t)n << 5 | XT2);   /* sdiv w17, wn, wm */
            ins(0x1B008000 | (uint32_t)m << 16 | (uint32_t)n << 10 | XT2 << 5 | (uint32_t)d);   /* msub wd, w17, wm, wn */
        }
        break;
    }
    }
    sxtw(d);
    wrote(d);
}

static int pop_op(int op)                              /* el operador de Dash (P_*) a wop */
{
    switch (op) {
    case P_PLUS: return 'a';
    case P_MINUS: return 's';
    case P_AMP: return '&';
    case P_BAR: return '|';
    case P_CARET: return '^';
    case P_STAR: return '*';
    case P_SLASH: return '/';
    case P_PERCENT: return '%';
    case P_SHL: return '<';
    case P_SHR: return '>';
    }
    return 0;
}

/* direcciones de los datos y de símbolos de fuera (adrp + add) */
static void addr_data(int d, long off)
{
    add_reloc_t((uint32_t)obj->code.n, HK_DATA, NULL, R_PG_HI21, off);
    ins(0x90000000 | (uint32_t)d);
    add_reloc_t((uint32_t)obj->code.n, HK_DATA, NULL, R_ADD_LO12, off);
    ins(0x91000000 | (uint32_t)d << 5 | (uint32_t)d);
    wrote(d);
}

static void addr_sym(int d, const char *sym)
{
    add_reloc_t((uint32_t)obj->code.n, -1, c_name(sym), R_PG_HI21, 0);
    ins(0x90000000 | (uint32_t)d);
    add_reloc_t((uint32_t)obj->code.n, -1, c_name(sym), R_ADD_LO12, 0);
    ins(0x91000000 | (uint32_t)d << 5 | (uint32_t)d);
    wrote(d);
}

static void addr_label(int d, int label)
{
    fixup(label, 3);
    ins(0x90000000 | (uint32_t)d);
    ins(0x91000000 | (uint32_t)d << 5 | (uint32_t)d);
    wrote(d);
}

/* ---- variables: registro, marco (desde x29), global (en los datos) o constante ---- */
static void var_to(int d, Var *v)
{
    switch (v->kind) {
    case V_REG: mov_reg(d, XREG(v->reg)); break;
    case V_LOCAL: mem64(1, d, 29, v->off); break;
    case V_GLOBAL:
        add_reloc_t((uint32_t)obj->code.n, HK_DATA, NULL, R_PG_HI21, v->off);
        ins(0x90000000 | XT2);
        add_reloc_t((uint32_t)obj->code.n, HK_DATA, NULL, R_LDST64_LO12, v->off);
        ins(0xF9400000 | XT2 << 5 | (uint32_t)d);
        wrote(d);
        break;
    case V_CONST: mov_imm(d, v->val); break;
    default: a64_todo("una variable en la pila (sin marco)");
    }
}

static void x_to_var(int s, Var *v)
{
    switch (v->kind) {
    case V_REG: mov_reg(XREG(v->reg), s); break;
    case V_LOCAL: mem64(0, s, 29, v->off); break;
    case V_GLOBAL:
        add_reloc_t((uint32_t)obj->code.n, HK_DATA, NULL, R_PG_HI21, v->off);
        ins(0x90000000 | XT2);
        add_reloc_t((uint32_t)obj->code.n, HK_DATA, NULL, R_LDST64_LO12, v->off);
        ins(0xF9000000 | XT2 << 5 | (uint32_t)s);
        break;
    default: a64_todo("guardar en una constante o en la pila");
    }
}

/* ---- lo que pide el recorrido (las mismas que t68k_ops.c) ---- */
static int flags_for(Var *v, int cc) { (void)v; (void)cc; return 0; }
static void forget_d0(void) { x0_dirty = 1; }
static void tst_d0(void) { cmp_x0_zero(); }
static void test_d0(void) { cmp_x0_zero(); }
static void load_imm(int reg, long v) { mov_imm(XREG(reg), (long)(int32_t)v); }
static void load_var(int reg, Var *v) { var_to(XREG(reg), v); }
static int take_move_to_d0(void) { return -1; }
static void store_d0(Var *v) { x_to_var(0, v); }
static void store_d0_stmt(Var *v) { x_to_var(0, v); }

static void add_imm_ea(long k, Var *v)                 /* v += k */
{
    if (!k) return;
    if (v->kind == V_REG) {
        int r = XREG(v->reg);
        mov_imm(XT, k);
        wop('a', r, r, XT);
        return;
    }
    var_to(XT, v);
    mov_imm(XT2, k);
    wop('a', XT, XT, XT2);
    x_to_var(XT, v);
}

static uint32_t add_string(const char *s, int len)
{
    uint32_t off;
    data_start();
    off = (uint32_t)obj->data.n;
    buf_bytes(&obj->data, s, len);
    buf_byte(&obj->data, 0);
    if (obj->data.n & 1) buf_byte(&obj->data, 0);
    return off;
}

/* Un literal como texto de Dash fijo para un campo (ver t68k_ops.c): en los datos, 16 bytes para la cabecera
   (_DashStrHdr: size, len, self de 64 bits) y el texto; al arrancar, _dl_str_lit pone la cabecera */
static struct { uint32_t off; const char *s; int len; } *dash_lits;
static int n_dash_lits, cap_dash_lits;
static int lit_init_label = -1;
static int autoclose, print_flush;
static uint32_t dash_lit(const char *s, int len)
{
    int i;
    for (i = 0; i < n_dash_lits; i++)
        if (dash_lits[i].len == len && !memcmp(dash_lits[i].s, s, (size_t)len)) return dash_lits[i].off;
    if (n_dash_lits == cap_dash_lits) {
        cap_dash_lits = cap_dash_lits ? cap_dash_lits * 2 : 16;
        dash_lits = realloc(dash_lits, sizeof(*dash_lits) * (size_t)cap_dash_lits);
    }
    data_align();
    buf_long(&obj->data, 0); buf_long(&obj->data, 0); buf_long(&obj->data, 0); buf_long(&obj->data, 0);
    dash_lits[n_dash_lits].off = add_string(s, len);
    dash_lits[n_dash_lits].s = s;
    dash_lits[n_dash_lits].len = len;
    return dash_lits[n_dash_lits++].off;
}

/* una variable del runtime, al arrancar: un texto (puntero) o un número (un LONG) */
static void set_rt_var(const char *sym, const char *str, long n)
{
    if (str) addr_data(XT, add_string(str, (int)strlen(str)));
    else mov_imm(XT, n);
    add_reloc_t((uint32_t)obj->code.n, -1, c_name(sym), R_PG_HI21, 0);
    ins(0x90000000 | XT2);
    add_reloc_t((uint32_t)obj->code.n, -1, c_name(sym), str ? R_LDST64_LO12 : R_LDST32_LO12, 0);
    ins((str ? 0xF9000000 : 0xB9000000) | XT2 << 5 | XT);
}

static void push_d0(void) { push_x(0); }
static void pop_d0(void) { pop_x(0); }

static void pea_string(const char *str, int len)
{
    addr_data(XT, add_string(str, len));
    push_x(XT);
}

static void pop_args(int n)
{
    sp_depth -= SLOT * n;
    if (n) ins(0x91000000 | (uint32_t)(SLOT * n) << 10 | 31 << 5 | 31);   /* add sp, sp, #16n */
}

static void move_d0_d1(void) { mov_reg(1, 0); }
static void move_d0_a0(void) { mov_reg(XA0, 0); }
static void zero_d0(void) { mov_imm(0, 0); }
static void cmp_d1_ea(Var *v) { var_to(XT, v); ins(0xEB00001F | XT << 16 | 1 << 5); x0_dirty = 0; }   /* cmp x1, xt */
static void pop_a0(void) { pop_x(XA0); }
static void pop_d1(void) { pop_x(1); }
static void load_byte_a0_d1(void) { ins(0x38606800 | 1 << 16 | XA0 << 5 | 0); wrote(0); }   /* ldrb w0, [x9, x1] */

static void call_a0(const char *sym) { mov_reg(0, XA0); jsr_sym(sym); }
static void call_a0_d1(const char *sym) { mov_reg(0, XA0); jsr_sym(sym); }   /* (x1 ya es d1) */

/* ---- textos de Dash: la cabecera (_DashStrHdr: size, len, self) delante del texto, 16 bytes ---- */
static void cbz_label(int reg, int label, int nz)
{
    fixup(label, 5);
    ins((nz ? 0xB5000000 : 0xB4000000) | (uint32_t)reg);
}

static void tst_bit(int reg, int bit)                  /* tst xreg, #1 << bit */
{
    ins(0xF2400000 | (uint32_t)((64 - bit) & 63) << 16 | (uint32_t)reg << 5 | 31);
    x0_dirty = 0;
}

/* ¿el texto de a0 es de Dash? Si lo es, a1 = su cabecera; si no, a slow; nil, a nil_label */
static void str_ours(int slow, int nil_label)
{
    cbz_label(XA0, nil_label, 0);
    tst_bit(XA0, 0);
    branch(CC_NE, slow);
    add_imm(XA1, XA0, -16);
    mem64(1, XT, XA1, 8);                              /* self */
    mov_imm(XT2, 0xDA5C7E57L);                         /* _DASH_STR_KEY */
    ins(0x8B000000 | XT2 << 16 | XA1 << 5 | XT2);      /* add x17, x10, x17 */
    ins(0xEB00001F | XT2 << 16 | XT << 5);             /* cmp x16, x17 */
    x0_dirty = 0;
    branch(CC_NE, slow);
}

static void cmp_d1_str_len(void) { ldrw(XT, XA1, 4); ins(0xEB00001F | XT << 16 | 1 << 5); x0_dirty = 0; }
static void load_str_len(void) { ldrw(0, XA1, 4); }
static void load_a0(Var *vs) { var_to(XA0, vs); }

/* ---- la pila ---- */
static void push_var(Var *v) { var_to(XT, v); push_x(XT); }
static void push_ea(Var *v) { var_to(XT, v); push_x(XT); }
static void push_word(int k) { mov_imm(XT, k); push_x(XT); }
static void push_long(uint32_t k) { mov_imm(XT, (long)k); push_x(XT); }
static __attribute__((unused)) void push_sp(void) { mov_reg(XT, 31); push_x(XT); }
static void push_sp_off(int off) { mem64(1, XT, 31, off); push_x(XT); }
static void push_label(int label) { addr_label(XT, label); push_x(XT); }
static void push_data(uint32_t off) { addr_data(XT, off); push_x(XT); }
static __attribute__((unused)) void push_sp_addr(int off) { add_imm(XT, 31, off); push_x(XT); }
static void push_a0_addr(int off) { add_imm(XT, XA0, off); push_x(XT); }
static void push_a0(void) { push_x(XA0); }
static void pop_to_a0(int off) { pop_x(XT); mem64(0, XT, XA0, off); }

static void push_data_long(long off)
{
    Var g;
    g.kind = V_GLOBAL;
    g.off = (int)off;
    var_to(XT, &g);
    push_x(XT);
}

static void reserve_args(int n)
{
    ins(0xD1000000 | (uint32_t)(SLOT * n) << 10 | 31 << 5 | 31);   /* sub sp, sp, #16n */
    sp_depth += SLOT * n;
}
static void reserve2(void) { reserve_args(2); }
static void store_d0_arg(int i) { mem64(0, 0, 31, SLOT * i); }
static void store_arg_imm(int i, long k) { mov_imm(XT, k); mem64(0, XT, 31, SLOT * i); }

static void store_var_data(Var *v, long off)
{
    Var g;
    g.kind = V_GLOBAL;
    g.off = (int)off;
    var_to(XT, v);
    x_to_var(XT, &g);
}

/* ---- conversiones de d0 ---- */
static void sext_byte(void) { ins(0x93401C00); wrote(0); }   /* sxtb x0, w0 */

static void int_to_fixed(void)                         /* d0 << 16 */
{
    ins(0x53000000 | 16 << 16 | 15 << 10);             /* lsl w0, w0, #16 */
    sxtw(0);
    wrote(0);
}

static void load_str_lit(const char *str, int len) { addr_data(0, add_string(str, len)); }

static void bool_to_str(void)                          /* d0 (Bool) al texto "true" o "false" */
{
    cmp_x0_zero();
    addr_data(XT, add_string("true", 4));
    addr_data(XT2, add_string("false", 5));
    ins(0x9A800000 | XT << 16 | 0 << 12 | XT2 << 5 | 0);   /* csel x0, x17, x16, eq: con 0, "false" */
    wrote(0);
}

/* ---- structs: cada campo, 8 bytes; la cabecera (_Dash_RefHeader) delante, con el tipo en -8 ---- */
static int field_off(int f) { return 8 * f; }
static int struct_bytes(int nfields) { return 8 * nfields; }
static void load_a0_off(int off) { mem64(1, 0, XA0, off); }

static void fail_if_nil(int file, int line)
{
    int ok = new_label();
    cbz_label(0, ok, 1);
    addr_data(0, add_string("campo de nil", 12));
    mov_imm(1, (long)((uint32_t)file << 16 | (line & 0xFFFF)));
    jsr_sym("_dl_fail_at");
    def_label(ok);
}

/* ¿Se hizo algún temporal desde la marca de off(sp)? Si no, salta a skip. Usa a0 y d1 */
static void tmp_newer(int off, int skip)
{
    addr_sym(XA0, "_dl_tmp_serial_p");
    mem64(1, XA0, XA0, 0);
    ldrw(1, XA0, 0);
    mem64(1, XT, 31, off);
    ins(0xEB00001F | XT << 16 | 1 << 5);               /* cmp x1, x16 */
    x0_dirty = 0;
    branch(CC_LS, skip);
}

static void pea_window(int wi) { addr_data(XT, win_off[wi]); push_x(XT); }

/* d0 = (lo de lo alto de la pila) op d0 */
static int bin_pop(int op)
{
    int o = pop_op(op);
    if (op != P_PLUS && op != P_AMP && op != P_BAR && op != P_MINUS && op != P_STAR) return 0;
    pop_x(XT);
    wop(o, 0, XT, 0);
    return 1;
}

static void call_d0(int nargs) { mov_reg(XT, 0); load_args(nargs); ins(0xD63F0000 | XT << 5); x0_dirty = 1; }

static void call_method(int slot, int nargs)
{
    mov_reg(XA0, 0);
    mem64(1, XA0, XA0, -8);                            /* su tipo */
    mem64(1, XA0, XA0, 16);                            /* su tabla de métodos */
    mem64(1, XT, XA0, 8 * slot);
    load_args(nargs);
    ins(0xD63F0000 | XT << 5);                         /* blr x16 */
    x0_dirty = 1;
}

static void c_bool(void)                               /* un BOOL de C a 0 o 1 */
{
    ins(0x7100001F);                                   /* cmp w0, #0 */
    ins(0x9A9F07E0 | 0 << 12);                         /* cset x0, ne (csinc x0, xzr, xzr, eq) */
    wrote(0);
}

/* ---- listas (DashArrayLong: data en 0, length en 8) y diccionarios ---- */
#define ELEM 8
#define ARR_DATA 0
#define ARR_LEN 8
#define DICT_CAP 20                                    /* DashDict: keys 0, vals 8, count 16, cap 20, ikeys 40 */

static void arr_get(void)                              /* d0 = la lista de a0 [d0]; nil o fuera: 0 */
{
    int zero = new_label(), done = new_label();
    cbz_label(XA0, zero, 0);
    ldrsw(XT, XA0, ARR_LEN);
    ins(0xEB00001F | XT << 16 | 0 << 5);               /* cmp x0, x16 */
    x0_dirty = 0;
    branch(CC_CC, zero);
    mem64(1, XA0, XA0, 0);
    ins(0xF8607800 | 0 << 16 | XA0 << 5 | 0);          /* ldr x0, [x9, x0, lsl #3] */
    branch(CC_T, done);
    def_label(zero);
    mov_imm(0, 0);
    def_label(done);
}

static void arr_put(void)                              /* la lista de a0 [d1] = d0 */
{
    int done = new_label();
    cbz_label(XA0, done, 0);
    ldrsw(XT, XA0, ARR_LEN);
    ins(0xEB00001F | XT << 16 | 1 << 5);               /* cmp x1, x16 */
    x0_dirty = 0;
    branch(CC_CC, done);
    mem64(1, XA0, XA0, 0);
    ins(0xF8207800 | 1 << 16 | XA0 << 5 | 0);          /* str x0, [x9, x1, lsl #3] */
    def_label(done);
}

/* ---- un objeto nuevo mientras se llenan sus campos: en x28, que se guarda ---- */
static void obj_begin(void) { push_x(XA2); mov_reg(XA2, 0); }
static void obj_end(void) { mov_reg(0, XA2); pop_x(XA2); }
static void obj_field_data(int off, uint32_t data) { addr_data(XT, data); mem64(0, XT, XA2, off); }
static void obj_field_clear(int off) { mem64(0, 31 /* xzr */, XA2, off); }
static void obj_field_from_sp(int off, int spoff) { mem64(1, XT, 31, spoff); mem64(0, XT, XA2, off); }
static void push_obj_field_addr(int off) { add_imm(XT, XA2, off); push_x(XT); }
static void push_obj_field(int off) { mem64(1, XT, XA2, off); push_x(XT); }

static void move_ea_d1(Var *v) { var_to(1, v); }

/* la casilla d0 del diccionario de a0: si no es una casilla (>= cap), a slow; a1 = keys */
static void dict_slot(int slow)
{
    ldrsw(XT, XA0, DICT_CAP);
    ins(0xEB00001F | XT << 16 | 0 << 5);               /* cmp x0, x16 */
    x0_dirty = 0;
    branch(CC_CC, slow);
    mem64(1, XA1, XA0, 0);
}

static void dict_slot_key(int slow)
{
    ins(0xF8607800 | 0 << 16 | XA1 << 5 | XT);         /* ldr x16, [x10, x0, lsl #3] */
    ins(0xEB00001F | XT << 16 | 1 << 5);               /* cmp x1, x16 */
    x0_dirty = 0;
    branch(CC_NE, slow);
}

static void dict_slot_val(void)
{
    mem64(1, XA0, XA0, 8);                             /* vals */
    ins(0xF8607800 | 0 << 16 | XA0 << 5 | 0);          /* ldr x0, [x9, x0, lsl #3] */
    wrote(0);
}

/* ---- comparaciones (de 64 bits: los Int están extendidos) ---- */
static void cmp_regs(int a, int b) { ins(0xEB00001F | (uint32_t)b << 16 | (uint32_t)a << 5); x0_dirty = 0; }
static void tst_ea(Var *v) { var_to(XT, v); ins(0xF100001F | XT << 5); x0_dirty = 0; }
static void cmp_imm_ea(long k, Var *v) { var_to(XT, v); mov_imm(XT2, (long)(int32_t)k); cmp_regs(XT, XT2); }
static void cmp_d0_d1(void) { cmp_regs(0, 1); }
static void set_ne(void) { mov_imm(0, 1); cmp_x0_zero(); }
static void test_bit0(int reg) { tst_bit(XREG(reg), 0); }
static void and_ea(Var *v) { var_to(XT, v); wop('&', 0, 0, XT); }
static void or_ea(Var *v) { var_to(XT, v); wop('|', 0, 0, XT); }
static void and_imm(uint32_t k) { mov_imm(XT, (long)(int32_t)k); wop('&', 0, 0, XT); }

static void cmp_reg_ea(int reg, Var *v)
{
    if (v) { var_to(XT, v); cmp_regs(XREG(reg), XT); }
    else cmp_regs(XREG(reg), 0);
}

static void cmp_byte_next(int c)                       /* el byte de a0 con c, y a0 al siguiente */
{
    ins(0x38400400 | 1 << 12 | XA0 << 5 | XT);         /* ldrb w16, [x9], #1 */
    ins(0x7100001F | (uint32_t)(c & 0xFF) << 10 | XT << 5);   /* cmp w16, #c */
    x0_dirty = 0;
}

static void tst_byte_a0(void)
{
    ins(0x39400000 | XA0 << 5 | XT);                   /* ldrb w16, [x9] */
    ins(0x7100001F | XT << 5);                         /* cmp w16, #0 */
    x0_dirty = 0;
}

static void dbl_cmp_order(int gt)
{
    int no = new_label(), done = new_label();
    ins(0xF100081F);                                   /* cmp x0, #2 */
    x0_dirty = 0;
    branch(CC_EQ, no);
    cmp_x0_zero();
    branch(CC_T, done);
    def_label(no);
    if (gt) mov_imm(0, -1);
    cmp_x0_zero();
    def_label(done);
    x0_dirty = 0;
}

static void load_label(int label) { addr_label(0, label); }
static void load_sym(const char *sym) { addr_sym(0, sym); }

static void neg_d0(void) { wop('s', 0, 31, 0); }       /* (wzr - w0) */
static void not_d0(void) { ins(0x2A2003E0); sxtw(0); wrote(0); } /* mvn w0, w0 */
static void float_neg(void) { ins(0x52010000); sxtw(0); wrote(0); }   /* eor w0, w0, #0x80000000 */

static void abs_d0(void)
{
    ins(0x7100001F);                                   /* cmp w0, #0 */
    ins(0x5A800400 | 0 << 16 | 5 << 12 | 0);           /* cneg w0, w0, mi (csneg w0, w0, w0, pl) */
    sxtw(0);
    wrote(0);
}

static void set_cc(int cc)                             /* d0 = 1 si se cumple cc */
{
    ins(0x9A9F07E0 | (uint32_t)(arm_cc[cc] ^ 1) << 12);   /* cset x0, cc */
    wrote(0);
}

/* ---- v op= algo: op = 0 add, 1 sub, 2 and, 3 or ---- */
static const int op4[4] = {'a', 's', '&', '|'};

static void op_to_reg(int op, int reg, Var *s, int x)
{
    int r = XREG(reg);
    if (s) { var_to(XT, s); wop(op4[op], r, r, XT); }
    else wop(op4[op], r, r, XREG(x));
}

static void op_reg_to(int op, int x, Var *v)
{
    var_to(XT, v);
    wop(op4[op], XT, XT, XREG(x));
    x_to_var(XT, v);
}

static void op_imm_into(int op, long k, Var *v)
{
    int o = pop_op(op);
    var_to(XT, v);
    mov_imm(XT2, k);
    wop(o, XT, XT, XT2);
    x_to_var(XT, v);
}

static void reg_div_pow2(Var *v, int sh)               /* v (en un registro) /= 2^sh, hacia cero */
{
    int r = XREG(v->reg);
    mov_imm(XT, 1L << sh);
    wop('/', r, r, XT);
}

static void a0_deref(void) { mem64(1, XA0, XA0, 0); }

static void ptr_add(long k, Var *v)                    /* un puntero += k (en 64 bits) */
{
    if (v->kind == V_REG) { add_imm(XREG(v->reg), XREG(v->reg), k); return; }
    var_to(XT, v);
    add_imm(XT, XT, k);
    x_to_var(XT, v);
}
static void load_a0_raw(int off)                       /* (el largo de una lista es un LONG; lo demás, punteros) */
{
    if (off == ARR_LEN) ldrsw(0, XA0, off);
    else mem64(1, 0, XA0, off);
}
static void load_elem(void) { ins(0xF8607800 | 0 << 16 | XA0 << 5 | 0); wrote(0); }   /* ldr x0, [x9, x0, lsl #3] */
static void load_char(void) { ins(0x38A06800 | 0 << 16 | XA0 << 5 | 0); wrote(0); }   /* ldrsb x0, [x9, x0] */
static void cmp_reg_a0(int reg, int off) { ldrsw(XT, XA0, off); cmp_regs(XREG(reg), XT); }

static void dict_test_ikeys(void)
{
    ins(0x79C00000 | (40 / 2) << 10 | XA0 << 5 | XT);  /* ldrsh w16, [x9, #40] */
    ins(0x7100001F | XT << 5);
    x0_dirty = 0;
}

static void sub_imm(long k) { mov_imm(XT, k); wop('s', 0, 0, XT); }
static void sub_ea(Var *v) { var_to(XT, v); wop('s', 0, 0, XT); }
static void add_to_reg(int reg, Var *v) { int r = XREG(reg); var_to(XT, v); wop('a', r, r, XT); }

static __attribute__((unused)) void dbra(int reg, int label) { (void)reg; (void)label; a64_todo("dbra"); }

/* fin de una vuelta con contador (vc, de vueltas - 1): si quedan, a top */
static void loop_count(Var *vc, int top, int big)
{
    (void)big;
    if (vc->kind == V_REG) {
        int r = XREG(vc->reg);
        ins(0x71000400 | (uint32_t)r << 5 | (uint32_t)r);   /* subs w, w, #1 */
        sxtw(r);
        x0_dirty = 0;
        branch(CC_GE, top);
    } else {
        var_to(XT, vc);
        ins(0x71000400 | XT << 5 | XT);                     /* subs w16, w16, #1 */
        sxtw(XT);
        x_to_var(XT, vc);
        x0_dirty = 0;
        branch(CC_GE, top);
    }
}

static void cmp_d0_k(long k, int small) { (void)small; mov_imm(XT, k); cmp_regs(0, XT); }
static void test_bit_d0(int bit) { tst_bit(0, bit); }

/* Ctrl-C en los bucles: en DashOS no (no hay señales de exec) */
static void brk_check(void) { }
static void debug_nop(void) { ins(0xD503201F); }
static void skip_stack(int bytes) { add_imm(31, 31, bytes); }

/* ---- funciones: marco con x29; los parámetros llegan en x0..x7 y se guardan en el marco ---- */
static int fn_nparams;
static uint32_t fn_frame_at;
static int fn_param_base(int nregs) { (void)nregs; return 0; }

static int param_off(int i)
{
    if (i >= 8) a64_todo("una función con más de 8 parámetros");
    if (i + 1 > fn_nparams) fn_nparams = i + 1;
    mem64(0, i, 29, -8 * (i + 1));                     /* el parámetro, a su hueco */
    return -8 * (i + 1);
}

static void fn_prologue(int frameless, int used)
{
    int r, prev = -1;
    (void)frameless;
    fn_nparams = 0;
    ins(0xA9BF7BFD);                                   /* stp x29, x30, [sp, #-16]! */
    ins(0x910003FD);                                   /* mov x29, sp */
    fn_frame_at = (uint32_t)obj->code.n;
    ins(0xD1000000 | 31 << 5 | 31);                    /* sub sp, sp, #marco (se pone al final) */
    for (r = 0; r < 16; r++)
        if (used & 1 << r) {
            if (prev < 0) prev = XREG(r);
            else {
                ins(0xA9BF0000 | (uint32_t)XREG(r) << 10 | 31 << 5 | (uint32_t)prev);   /* stp */
                prev = -1;
            }
        }
    if (prev >= 0) ins(0xA9BF0000 | 31 << 10 | 31 << 5 | (uint32_t)prev);   /* stp xN, xzr */
}

static void load_param(int reg, int i, int frameless) { (void)frameless; mem64(1, XREG(reg), 29, -8 * (i + 1)); }

static void fn_epilogue(int frameless, int used, int nframe)
{
    int r, regs[16], n = 0, i, frame;
    (void)frameless;
    for (r = 0; r < 16; r++)
        if (used & 1 << r) regs[n++] = XREG(r);
    /* al revés que en el prólogo: los pares, desde el último */
    i = n;
    if (n & 1) {
        ins(0xA8C10000 | 31 << 10 | 31 << 5 | (uint32_t)regs[n - 1]);   /* ldp xN, xzr, [sp], #16 */
        i = n - 1;
    }
    for (; i >= 2; i -= 2)
        ins(0xA8C10000 | (uint32_t)regs[i - 1] << 10 | 31 << 5 | (uint32_t)regs[i - 2]);   /* ldp */
    ins(0x910003BF);                                   /* mov sp, x29 */
    ins(0xA8C17BFD);                                   /* ldp x29, x30, [sp], #16 */
    ins(0xD65F03C0);                                   /* ret */
    x0_dirty = 0;
    frame = (8 * (fn_nparams + nframe) + 15) & ~15;
    if (frame > 4095) fatal("demasiadas variables en una función (dashc para DashOS)");
    ins_put(fn_frame_at, ins_at(fn_frame_at) | (uint32_t)frame << 10);
}

static void clear_global(long off)
{
    Var g;
    g.kind = V_GLOBAL;
    g.off = (int)off;
    x_to_var(31 /* xzr */, &g);
}

/* ---- las tablas que el recorrido pone "en el código" (descriptores...): en ARM, en los datos (ver in_table);
   punteros de 8 bytes, alineados ---- */
static void code_align(void)
{
    x0_dirty = 0;                                      /* (antes, el final de una función: no se llega de largo) */
    in_table = 1;
    data_start();
    while (obj->data.n & 7) buf_byte(&obj->data, 0);   /* (de byte en byte: los textos dejan los datos en cualquier largo) */
}
static void code_long(uint32_t v) { l(v); }

static void code_ptr(int label)
{
    code_align();
    if (label >= 0) fixup(label, 4);
    l(0); l(0);
}

static void code_data_ptr(uint32_t off)
{
    code_align();
    add_reloc_d((uint32_t)obj->data.n, HK_DATA, R_ABS64, off);
    l(0); l(0);
}

/* el destructor de un struct: el runtime lo llama con el objeto en x0 */
static void destroy_begin(void)
{
    ins(0xA9BE7BFD);                                   /* stp x29, x30, [sp, #-32]! */
    ins(0x910003FD);                                   /* mov x29, sp */
    ins(0xF9000BFC);                                   /* str x28, [sp, #16] */
    ins(0xAA0003FC);                                   /* mov x28, x0 */
}

static void destroy_field(int off, const char *sym) { mem64(1, 0, XA2, off); jsr_sym(sym); }

static void destroy_end(void)
{
    ins(0xF9400BFC);                                   /* ldr x28, [sp, #16] */
    ins(0xA8C27BFD);                                   /* ldp x29, x30, [sp], #32 */
    ins(0xD65F03C0);                                   /* ret */
    x0_dirty = 0;
}

/* ---- el arranque: _dash_start(main, ficheros, pila) del runtime ---- */
static int start_args;
static void start_arg_long(uint32_t v) { mov_imm(XT, (long)v); ins(0xF81F0FE0 | XT); start_args++; }
static void start_arg_label(int label) { addr_label(XT, label); ins(0xF81F0FE0 | XT); start_args++; }

static void jmp_sym(const char *sym)
{
    load_args(start_args);
    add_reloc_t((uint32_t)obj->code.n, -1, c_name(sym), R_JUMP26, 0);
    ins(0x14000000);                                   /* b sym */
    x0_dirty = 0;
}

/* la cabecera de los literales de los campos (dash_lit), al arrancar */
static void lit_init_begin(void) { ins(0xA9BF7BFD); ins(0x910003FD); }   /* stp x29, x30; mov x29, sp */
static void lit_init_one(uint32_t off) { addr_data(0, off); jsr_sym("_dl_str_lit"); }
static void lit_init_end(void) { ins(0xA8C17BFD); ins(0xD65F03C0); x0_dirty = 0; }    /* ldp x29, x30; ret */

/* la dirección de un array de n cosas que el recorrido dejó en la pila desde off(sp), cada una en 16 bytes: se
   juntan ahí mismo como las espera el C (lng: LONG de 4 bytes; si no, de 8) y se mete su dirección */
static void push_array(int off, int n, int lng)
{
    int i;
    for (i = lng ? 0 : 1; i < n; i++) {
        mem64(1, XT, 31, off + SLOT * i);
        if (lng) ins(0xB9000000 | (uint32_t)((off + 4 * i) / 4) << 10 | 31 << 5 | XT);   /* str w16, [sp, #off+4i] */
        else mem64(0, XT, 31, off + 8 * i);
    }
    add_imm(XT, 31, off);
    push_x(XT);
}

/* ---- @amiga struct (A6): campos de 1, 2 y 4 bytes en x9 + off (sin ldp ni exclusivos: van a 2 bytes) ---- */
static void zext_d0(void) { ins(0x2A0003E0); wrote(0); }   /* mov w0, w0: con ceros arriba */

static void amiga_check32(void)                        /* una dirección de 4 GB o más no cabe en un campo de 32 bits */
{
    int ok = new_label();
    ins(0xD360FC10);                                   /* lsr x16, x0, #32 */
    cbz_label(XT, ok, 0);
    jsr_sym("_dl_a32_fail");
    def_label(ok);
}

static void amem(uint32_t op, int t, int off)          /* op: la forma sin escalar (ldur...), con [x9 + off] */
{
    int base = XA0;
    if (off < -256 || off > 255) { add_imm(XT, XA0, off); base = XT; off = 0; }
    ins(op | ((uint32_t)off & 0x1FF) << 12 | (uint32_t)base << 5 | (uint32_t)t);
}

/* La memoria del Amiga es big-endian: en un programa little-endian, Word y Long se leen y escriben dando la vuelta a
   sus bytes (rev, rev16) */
static void amiga_load(int off, int size, int sgn)
{
    if (!elf_be && size > 1) {
        amem(size == 4 ? 0xB8400000 : 0x78400000, 0, off);            /* ldur w0 / ldurh w0 */
        ins(size == 4 ? 0x5AC00800 : 0x5AC00400);                     /* rev w0, w0 / rev16 w0, w0 */
        if (sgn) ins(size == 4 ? 0x93407C00 : 0x93403C00);            /* sxtw x0, w0 / sxth x0, w0 */
    }
    else if (size == 4) amem(sgn ? 0xB8800000 : 0xB8400000, 0, off);   /* ldursw x0 / ldur w0 */
    else if (size == 2) amem(sgn ? 0x78800000 : 0x78400000, 0, off);   /* ldursh x0 / ldurh w0 */
    else amem(sgn ? 0x38800000 : 0x38400000, 0, off);                 /* ldursb x0 / ldurb w0 */
    wrote(0);
}

static void amiga_store(int off, int size)
{
    int t = 0;
    if (!elf_be && size > 1) {
        ins((size == 4 ? 0x5AC00800 : 0x5AC00400) | XT2);              /* rev w17, w0 / rev16 w17, w0 */
        t = XT2;
    }
    amem(size == 4 ? 0xB8000000 : size == 2 ? 0x78000000 : 0x38000000, t, off);   /* stur w / sturh / sturb */
}

static void amiga_addr(int off) { add_imm(0, XA0, off); }
