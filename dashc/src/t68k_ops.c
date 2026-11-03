/* Generador de 68000 de dashc (docs/AARCH64_LOOP.md, fase A3): lo que sabe de las instrucciones del 68000. Lo
   incluye gen68k.c donde iba (un solo fichero de C: comparte sus estáticos). */
/* ¿los códigos de condición ya comparan v con 0 para la condición cc? */
static int flags_for(Var *v, int cc)
{
    return v->kind == V_REG && flags_at == obj->code.n && flags_reg == v->reg &&
           (flags_full || cc == CC_EQ || cc == CC_NE);
}

/* d0 ya no tiene lo que se sabía (lo dejó una llamada) */
static void forget_d0(void) { d0_loaded = (uint32_t)-1; }

/* ---- direcciones efectivas: una variable como operando de una instrucción ---- */
static int ea_bits(Var *v)
{
    switch (v->kind) {
    case V_REG: return v->reg;      /* dN */
    case V_LOCAL: return 0x2D;      /* d16(a5) */
    case V_STACK: return 0x2F;      /* d16(sp) */
    case V_GLOBAL: return 0x39;     /* abs.l */
    default: return 0x3C;           /* #inmediato */
    }
}

static void ea_ext(Var *v)
{
    switch (v->kind) {
    case V_LOCAL:
        w(v->off);
        break;
    case V_STACK:
        w(sp_depth + param_base + v->off - 8);
        break;
    case V_GLOBAL:
        add_reloc((uint32_t)obj->code.n, HK_DATA, NULL);
        l((uint32_t)v->off);
        break;
    case V_CONST:
        l((uint32_t)v->val);
        break;
    }
}

/* una instrucción con la variable como operando (opcode sin los 6 bits de la dirección) */
static void op_ea(int opcode, Var *v)
{
    w(opcode | ea_bits(v));
    ea_ext(v);
}

/* una instrucción con un inmediato de 32 bits y la variable como destino (addi, cmpi...) */
static void op_imm_ea(int opcode, long k, Var *v)
{
    w(opcode | ea_bits(v));
    l((uint32_t)k);
    ea_ext(v);
}

/* tst.l d0, salvo si lo último fue cargar d0 con move/moveq (ya pone N y Z, y V = C = 0) */

static void tst_d0(void)
{
    if (d0_loaded != obj->code.n) w(0x4A80);           /* tst.l d0 */
}

static void load_imm(int reg, long v)
{
    int32_t x = (int32_t)v;
    if (x >= -128 && x <= 127) {
        w(0x7000 | reg << 9 | (x & 0xFF));            /* moveq #x,dN */
    } else {
        w(0x203C | reg << 9);                          /* move.l #x,dN */
        l((uint32_t)x);
    }
    if (reg == 0) d0_loaded = (uint32_t)obj->code.n;
    else flags_set(reg, 1);
}

static void load_var(int reg, Var *v)
{
    if (v->kind == V_CONST) load_imm(reg, v->val);
    else if (reg == 0 && v->kind == V_REG && d0_stored == obj->code.n && d0_stored_reg == v->reg &&
             obj->code.n >= 2 && obj->code.p[obj->code.n - 2] == (0x20 | v->reg << 1) && obj->code.p[obj->code.n - 1] == 0)
        d0_loaded = (uint32_t)obj->code.n;             /* (lo último fue move.l d0,dN: d0 ya lo tiene, con N y Z) */
    else if (!(v->kind == V_REG && v->reg == reg)) {
        op_ea(0x2000 | reg << 9, v);                   /* move.l v,dN */
        if (reg == 0) d0_loaded = (uint32_t)obj->code.n;
        else flags_set(reg, 1);
    }
}

/* Si lo último fue move.l dX,d0 (con X de 2 a 7) y no se llega ahí desde otro sitio,
   lo quita y devuelve X: quien iba a usar d0 puede usar dX. Si no, -1. */
static int take_move_to_d0(void)
{
    uint8_t *p = obj->code.p + obj->code.n - 2;
    int x, i;
    if (d0_loaded != obj->code.n || obj->code.n < 2 || p[0] != 0x20 || (p[1] & 0xF8) != 0) return -1;
    x = p[1] & 7;
    if (x < 2) return -1;
    for (i = 0; i < labels.n; i++)                     /* una etiqueta de justo detrás */
        if (labels.v[i] == (long)obj->code.n) labels.v[i] -= 2;
    obj->code.n -= 2;
    d0_loaded = (uint32_t)-1;
    return x;
}

static void store_d0(Var *v)
{
    if (v->kind == V_REG) {
        w(0x2000 | v->reg << 9);                       /* move.l d0,dN */
        flags_set(v->reg, 1);
        d0_stored = (uint32_t)obj->code.n;
        d0_stored_reg = v->reg;
    } else if (v->kind == V_LOCAL) {
        w(0x2B40);                                     /* move.l d0,off(a5) */
        w(v->off);
    } else {
        w(0x23C0);                                     /* move.l d0,global */
        add_reloc((uint32_t)obj->code.n, HK_DATA, NULL);
        l((uint32_t)v->off);
    }
}

/* store_d0 al final de una sentencia (nadie usa d0 después): si lo último fue move.l dX,d0, va move.l dX,dN sin
   pasar por d0 (y = f(y, i) con f en línea: lo que devuelve f ya está en un registro) */
static void store_d0_stmt(Var *v)
{
    int x;
    if (v->kind == V_REG && (x = take_move_to_d0()) >= 0) {
        if (x != v->reg) w(0x2000 | v->reg << 9 | x);  /* move.l dX,dN */
        flags_set(v->reg, 1);
        d0_stored = (uint32_t)-1;
        return;
    }
    store_d0(v);
}

/* suma k a la variable, sin pasar por d0 */
static void add_imm_ea(long k, Var *v)
{
    if (k >= 1 && k <= 8) op_ea(0x5080 | (k & 7) << 9, v);          /* addq.l #k,v */
    else if (k <= -1 && k >= -8) op_ea(0x5180 | (-k & 7) << 9, v);  /* subq.l #k,v */
    else if (k) op_imm_ea(0x0680, k, v);                            /* addi.l #k,v */
    if (k && v->kind == V_REG) flags_set(v->reg, 0);
}

static uint32_t add_string(const char *s, int len)
{
    uint32_t off = (uint32_t)obj->data.n;
    buf_bytes(&obj->data, s, len);
    buf_byte(&obj->data, 0);
    if (obj->data.n & 1) buf_byte(&obj->data, 0);
    return off;
}

/* Un literal como texto de Dash fijo (escapado: nunca se libera ni se escribe en su sitio), para un campo que
   empieza con él: el campo lo apunta tal cual, sin pedir memoria ni copiarlo. En los datos, 12 bytes para la
   cabecera (_DashStrHdr) y el texto; al arrancar, _dl_str_lit pone la cabecera (lit_init_label) */
static struct { uint32_t off; const char *s; int len; } *dash_lits;
static int n_dash_lits, cap_dash_lits;
static int lit_init_label = -1;

static uint32_t dash_lit(const char *s, int len)
{
    int i;
    for (i = 0; i < n_dash_lits; i++)
        if (dash_lits[i].len == len && !memcmp(dash_lits[i].s, s, (size_t)len)) return dash_lits[i].off;
    if (n_dash_lits == cap_dash_lits) {
        cap_dash_lits = cap_dash_lits ? cap_dash_lits * 2 : 16;
        dash_lits = realloc(dash_lits, sizeof(*dash_lits) * (size_t)cap_dash_lits);
    }
    buf_long(&obj->data, 0);
    buf_long(&obj->data, 0);
    buf_long(&obj->data, 0);
    dash_lits[n_dash_lits].off = add_string(s, len);
    dash_lits[n_dash_lits].s = s;
    dash_lits[n_dash_lits].len = len;
    return dash_lits[n_dash_lits++].off;
}

/* move.l #texto (o #n),var: una variable del runtime, al arrancar */
static void set_rt_var(const char *sym, const char *str, long n)
{
    w(0x23FC);
    if (str) {
        add_reloc((uint32_t)obj->code.n, HK_DATA, NULL);
        l(add_string(str, (int)strlen(str)));
    } else
        l((uint32_t)n);
    add_reloc((uint32_t)obj->code.n, -1, sym);
    l(0);
}

static void push_d0(void)
{
    w(0x2F00);                                         /* move.l d0,-(sp) */
    sp_depth += 4;
}

static void pop_d0(void)
{
    w(0x201F);                                         /* move.l (sp)+,d0 */
    sp_depth -= 4;
}

static void pea_string(const char *str, int len)
{
    w(0x4879);                                         /* pea texto */
    add_reloc((uint32_t)obj->code.n, HK_DATA, NULL);
    l(add_string(str, len));
    sp_depth += 4;
}

static void pop_args(int n)
{
    int bytes = n * 4;
    sp_depth -= bytes;
    if (!bytes) return;
    if (bytes <= 8) w(0x508F | (bytes & 7) << 9);      /* addq.l #n,sp */
    else { w(0x4FEF); w(bytes); }                      /* lea n(sp),sp */
}

/* ---- registros de trabajo: d0 (el valor), d1 (un segundo operando), a0 y a1 (punteros) ---- */
/* (sin tocar lo que se sabe de d0 y de los códigos de condición: los mismos bytes que antes, sueltos) */
static void move_d0_d1(void) { w(0x2200); }            /* move.l d0,d1 */
static void move_d0_a0(void) { w(0x2040); }            /* movea.l d0,a0 */
static void zero_d0(void) { w(0x7000); }               /* moveq #0,d0 */
static void cmp_d1_ea(Var *v) { op_ea(0xB280, v); }    /* cmp.l v,d1 */

static void pop_a0(void)
{
    w(0x205F);                                         /* movea.l (sp)+,a0 */
    sp_depth -= 4;
}

/* d0 = el byte de a0 + d1, sin signo */
static void load_byte_a0_d1(void)
{
    w(0x7000);                                         /* moveq #0,d0 */
    w(0x1030); w(0x1800);                              /* move.b 0(a0,d1.l),d0 */
}

/* una función del runtime con a0 (y d1) de argumentos; el resultado en d0 */
static void call_a0(const char *sym)
{
    w(0x2F08);                                         /* move.l a0,-(sp) */
    jsr_sym(sym);
    w(0x588F);                                         /* addq.l #4,sp */
}

static void call_a0_d1(const char *sym)
{
    w(0x2F01); w(0x2F08);                              /* move.l d1,-(sp); move.l a0,-(sp) */
    jsr_sym(sym);
    w(0x508F);                                         /* addq.l #8,sp */
}

/* ---- textos de Dash: la cabecera (_DashStrHdr: size, len, self) delante del texto ---- */
/* ¿El texto de a0 es de Dash? (como _DASH_STR_OURS: impar no; self de la cabecera = cabecera + _DASH_STR_KEY; api.c
   comprueba al compilar que la cabecera sigue siendo { size, len, self } de 12 bytes y la clave). Si lo es, a1 = su
   cabecera; si no, a slow; nil, a nil_label */
static void str_ours(int slow, int nil_label)
{
    w(0x2008);                                         /* move.l a0,d0 */
    branch(CC_EQ, nil_label);
    w(0x0800); w(0x0000);                              /* btst #0,d0 */
    branch(CC_NE, slow);
    w(0x43E8); w(0xFFF4);                              /* lea -12(a0),a1 */
    w(0x2009);                                         /* move.l a1,d0 */
    w(0x0680); l(0xDA5C7E57);                          /* addi.l #_DASH_STR_KEY,d0 */
    w(0xB0A9); w(0x0008);                              /* cmp.l 8(a1),d0 */
    branch(CC_NE, slow);
}

/* el largo de la cabecera de a1 (str_ours): comparado con d1, o a d0 */
static void cmp_d1_str_len(void) { w(0xB2A9); w(0x0004); }   /* cmp.l 4(a1),d1 */
static void load_str_len(void) { w(0x2029); w(0x0004); }     /* move.l 4(a1),d0 */

/* v (un texto, una lista...) a a0, sin pasar por la pila */
static void load_a0(Var *vs)
{
    if (vs->kind == V_REG) w(0x2040 | vs->reg);        /* movea.l dN,a0 */
    else op_ea(0x2040, vs);                            /* movea.l v,a0 */
}

/* ---- la pila: los argumentos de las llamadas (de derecha a izquierda) y los valores de paso ---- */
/* una variable o constante a la pila (pea k.w si cabe en 16 bits) */
static void push_var(Var *v)
{
    if (v->kind == V_CONST && v->val >= -32768 && v->val <= 32767) {
        w(0x4878);                                     /* pea k.w */
        w((int)v->val);
    } else {
        op_ea(0x2F00, v);                              /* move.l v,-(sp) */
    }
    sp_depth += 4;
}

static void push_word(int k)                           /* un número de 16 bits con signo */
{
    w(0x4878); w(k);                                   /* pea k.w */
    sp_depth += 4;
}

static void push_long(uint32_t k)
{
    w(0x2F3C); l(k);                                   /* move.l #k,-(sp) */
    sp_depth += 4;
}

static void push_sp(void)                              /* la dirección de lo que está en lo alto de la pila */
{
    w(0x4857);                                         /* pea (sp) */
    sp_depth += 4;
}

static void push_sp_off(int off)                       /* lo que hay en off(sp) */
{
    w(0x2F2F); w(off);                                 /* move.l off(sp),-(sp) */
    sp_depth += 4;
}

static void push_label(int label)                      /* la dirección de una etiqueta del código */
{
    Fixup f;
    w(0x4879);                                         /* pea etiqueta */
    f.at = (uint32_t)obj->code.n;
    f.label = label;
    f.abs = 1;
    f.size = 2;
    VEC_PUSH(fixups, f);
    add_reloc(f.at, HK_CODE, NULL);
    l(0);
    sp_depth += 4;
}

/* hueco para n argumentos, que se llenan con store_d0_arg (el 0 es el de más arriba) */
static void reserve_args(int n)
{
    w(0x4FEF); w(-4 * n);                              /* lea -4n(sp),sp */
    sp_depth += 4 * n;
}

static void store_d0_arg(int i)
{
    if (i) { w(0x2F40); w(4 * i); }                    /* move.l d0,4i(sp) */
    else w(0x2E80);                                    /* move.l d0,(sp) */
}

/* v a una variable de los datos (sin pasar por d0) */
static void store_var_data(Var *v, long off)
{
    op_ea(0x23C0, v);                                  /* move.l v,abs */
    add_reloc((uint32_t)obj->code.n, HK_DATA, NULL);
    l((uint32_t)off);
}

/* ---- conversiones de d0 ---- */
static void sext_byte(void) { w(0x4880); w(0x48C0); }  /* ext.w d0; ext.l d0 */

static void int_to_fixed(void)                         /* d0 << 16 */
{
    w(0x4840);                                         /* swap d0 */
    w(0x4240);                                         /* clr.w d0 */
    d0_loaded = (uint32_t)-1;
}

static void load_str_lit(const char *str, int len)
{
    w(0x203C);                                         /* move.l #texto,d0 */
    add_reloc((uint32_t)obj->code.n, HK_DATA, NULL);
    l(add_string(str, len));
    d0_loaded = (uint32_t)obj->code.n;
}

/* d0 (Bool) al texto "true" o "false" */
static void bool_to_str(void)
{
    tst_d0();
    w(0x6708);                                         /* beq.s +8 */
    load_str_lit("true", 4);
    w(0x6006);                                         /* bra.s +6 */
    load_str_lit("false", 5);
    d0_loaded = (uint32_t)-1;
}

/* ---- structs: el puntero en a0; cada campo, una palabra larga ---- */
static int field_off(int f) { return 4 * f; }

static void load_a0_off(int off)
{
    w(0x2028); w(off);                                 /* move.l off(a0),d0 */
    d0_loaded = (uint32_t)obj->code.n;
}

/* si d0 es nil: "Error: campo de nil (en fichero:línea)", y se acaba (_dl_fail_at no vuelve) */
static void fail_if_nil(int file, int line)
{
    tst_d0();
    if (file) {
        w(0x6612);                                     /* bne.s +18 */
        w(0x4879); l((uint32_t)file << 16 | (line & 0xFFFF));   /* pea fichero << 16 | línea */
    } else {
        w(0x6610);                                     /* bne.s +16 */
        w(0x4878); w(line & 0x7FFF);                   /* pea línea.w (fichero 0) */
    }
    w(0x4879);                                         /* pea "campo de nil" */
    add_reloc((uint32_t)obj->code.n, HK_DATA, NULL);
    l(add_string("campo de nil", 12));
    jsr_sym("_dl_fail_at");
}

/* al empezar cada vuelta: fuera los temporales de la anterior */
/* ¿Se hizo algún temporal desde la marca de off(sp)? Si no, salta a skip (como _dash_tmp_release: el contador de
   temporales no pasa de la marca). Usa a0 y d1 */
static void tmp_newer(int off, int skip)
{
    w(0x2079);                                         /* movea.l _dl_tmp_serial_p,a0 */
    add_reloc((uint32_t)obj->code.n, -1, "_dl_tmp_serial_p");
    l(0);
    w(0x2210);                                         /* move.l (a0),d1 */
    w(0xB2AF); w(off);                                 /* cmp.l marca(sp),d1 */
    branch(CC_LS, skip);
}

/* pea de la variable de la ventana (un puntero a ella, para dl_window_close y dl_event_next) */
static void pea_window(int wi)
{
    w(0x4879);                                         /* pea variable */
    add_reloc((uint32_t)obj->code.n, HK_DATA, NULL);
    l((uint32_t)win_off[wi]);
    sp_depth += 4;
}

static void push_data(uint32_t off)                    /* la dirección de algo de los datos */
{
    w(0x4879);                                         /* pea datos */
    add_reloc((uint32_t)obj->code.n, HK_DATA, NULL);
    l(off);
    sp_depth += 4;
}

static void push_sp_addr(int off)                      /* la dirección de off(sp) */
{
    w(0x486F); w(off);                                 /* pea off(sp) */
    sp_depth += 4;
}

static void push_a0_addr(int off)                      /* la dirección de off(a0) */
{
    w(0x4868); w(off);                                 /* pea off(a0) */
    sp_depth += 4;
}

static void pop_to_a0(int off)                         /* lo de lo alto de la pila a off(a0) */
{
    w(0x215F); w(off);                                 /* move.l (sp)+,off(a0) */
    sp_depth -= 4;
}

static void mul_d1(void);

/* d0 = (lo de lo alto de la pila) op d0, si la operación es de las que se hacen así; si no, 0 */
static int bin_pop(int op)
{
    switch (op) {
    case P_PLUS: w(0xD09F); sp_depth -= 4; return 1;            /* add.l (sp)+,d0 */
    case P_AMP: w(0xC09F); sp_depth -= 4; return 1;             /* and.l (sp)+,d0 */
    case P_BAR: w(0x809F); sp_depth -= 4; return 1;             /* or.l (sp)+,d0 */
    case P_MINUS: w(0x909F); w(0x4480); sp_depth -= 4; return 1;   /* sub.l (sp)+,d0; neg.l d0 */
    case P_STAR: w(0x221F); sp_depth -= 4; mul_d1(); return 1;     /* move.l (sp)+,d1 */
    }
    return 0;
}

/* llamadas por un puntero: a la función de d0, o al método slot del objeto de d0 (su _DashType, a -4 del objeto,
   tiene en 8 la tabla de métodos) */
static void call_d0(int nargs)
{
    (void)nargs;
    w(0x2040);                                         /* movea.l d0,a0 */
    w(0x4E90);                                         /* jsr (a0) */
}

static void call_method(int slot, int nargs)
{
    (void)nargs;
    w(0x2040);                                         /* movea.l d0,a0 */
    w(0x2068); w(-4);                                  /* movea.l -4(a0),a0: su tipo */
    w(0x2068); w(8);                                   /* movea.l 8(a0),a0: su tabla de métodos */
    w(0x2068); w(4 * slot);                            /* movea.l slot(a0),a0 */
    w(0x4E90);                                         /* jsr (a0) */
}

/* un BOOL de C (cualquier no 0) a 0 o 1 */
static void c_bool(void)
{
    w(0x4A80);                                         /* tst.l d0 */
    w(0x56C0);                                         /* sne d0 */
    w(0x4400);                                         /* neg.b d0 */
    w(0x0280); l(1);                                   /* andi.l #1,d0 */
}

/* d0 = la lista de a0 [d0], como DashArray_get: nil o un índice fuera dan 0 (data en 0(a0), length en 4(a0)) */
static void arr_get(void)
{
    w(0x2208);                                         /* move.l a0,d1 */
    w(0x6710);                                         /* beq.s cero */
    w(0xB0A8); w(4);                                   /* cmp.l 4(a0),d0 */
    w(0x640A);                                         /* bcc.s cero (sin signo: también un índice negativo) */
    w(0x2050);                                         /* movea.l (a0),a0 */
    w(0xE588);                                         /* lsl.l #2,d0 */
    w(0x2030); w(0x0800);                              /* move.l 0(a0,d0.l),d0 */
    w(0x6002);                                         /* bra.s fin */
    w(0x7000);                                         /* cero: moveq #0,d0 */
    d0_loaded = (uint32_t)-1;                          /* fin: */
}

static void pop_d1(void)
{
    w(0x221F);                                         /* move.l (sp)+,d1 */
    sp_depth -= 4;
}

/* hueco para dos valores en la pila (más corto que reserve_args(2): subq) */
static void reserve2(void)
{
    w(0x518F);                                         /* subq.l #8,sp */
    sp_depth += 8;
}

/* la lista de a0 [d1] = d0, como DashArray_set: nil o un índice fuera no hacen nada */
static void arr_put(void)
{
    w(0xB0FC); w(0);                                   /* cmpa.w #0,a0 */
    w(0x670E);                                         /* beq.s fin */
    w(0xB2A8); w(4);                                   /* cmp.l 4(a0),d1 */
    w(0x6408);                                         /* bcc.s fin */
    w(0x2050);                                         /* movea.l (a0),a0 */
    w(0xE589);                                         /* lsl.l #2,d1 */
    w(0x2180); w(0x1800);                              /* move.l d0,0(a0,d1.l) */
    d0_loaded = (uint32_t)-1;                          /* fin: */
}

/* ---- un objeto nuevo mientras se llenan sus campos: en a2, que se guarda (una función de Dash a la que llama C,
   una retrollamada, tiene que dejarlo como estaba; C no lo toca) ---- */
#define SLOT 4                                         /* lo que ocupa cada cosa de la pila */
static int struct_bytes(int nfields) { return 4 * nfields; }

static void obj_begin(void)                            /* el objeto de d0 */
{
    w(0x2F0A);                                         /* move.l a2,-(sp) */
    sp_depth += 4;
    w(0x2440);                                         /* movea.l d0,a2 */
}

static void obj_end(void)                              /* el objeto a d0 */
{
    w(0x200A);                                         /* move.l a2,d0 */
    w(0x245F);                                         /* movea.l (sp)+,a2 */
    sp_depth -= 4;
}

static void obj_field_data(int off, uint32_t data)     /* el campo apunta a algo de los datos */
{
    w(0x257C);                                         /* move.l #datos,off(a2) */
    add_reloc((uint32_t)obj->code.n, HK_DATA, NULL);
    l(data);
    w(off);
}

static void obj_field_clear(int off) { w(0x42AA); w(off); }   /* clr.l off(a2) */

static void obj_field_from_sp(int off, int spoff)
{
    w(0x256F); w(spoff); w(off);                       /* move.l spoff(sp),off(a2) */
}

static void push_obj_field_addr(int off)
{
    w(0x486A); w(off);                                 /* pea off(a2) */
    sp_depth += 4;
}

static void push_obj_field(int off)
{
    w(0x2F2A); w(off);                                 /* move.l off(a2),-(sp) */
    sp_depth += 4;
}

static void move_ea_d1(Var *v) { op_ea(0x2200, v); }   /* move.l v,d1 (sin tocar lo que se sabe de los códigos) */

/* ---- diccionarios (DashDict: keys en 0, vals en 4, cap en 12): la casilla d0 del de a0 ---- */
/* si d0 no es una casilla (>= cap), a slow; si no, a1 = keys y d0 = el desplazamiento de la casilla */
static void dict_slot(int slow)
{
    w(0xB0A8); w(12);                                  /* cmp.l 12(a0),d0: cap */
    branch(CC_CC, slow);
    w(0x2250);                                         /* movea.l (a0),a1: keys */
    w(0xD080); w(0xD080);                              /* add.l d0,d0 (x2) */
}

/* si la clave de la casilla no es la de d1, a slow */
static void dict_slot_key(int slow)
{
    w(0xB2B1); w(0x0800);                              /* cmp.l (0,a1,d0.l),d1 */
    branch(CC_NE, slow);
}

static void dict_slot_val(void)                        /* d0 = el valor de la casilla */
{
    w(0x2068); w(4);                                   /* movea.l 4(a0),a0: vals */
    w(0x2030); w(0x0800);                              /* move.l (0,a0,d0.l),d0 */
}

/* ---- comparaciones: dejan los códigos de condición para la condición que devuelve el recorrido (CC_*) ---- */
static void test_d0(void) { w(0x4A80); }               /* tst.l d0 (siempre: tst_d0 se lo salta si ya vale) */
static void tst_ea(Var *v) { op_ea(0x4A80, v); }       /* tst.l v */
static void cmp_imm_ea(long k, Var *v) { op_imm_ea(0x0C80, k, v); }   /* cmpi.l #k,v */
static void cmp_d0_d1(void) { w(0xB081); }             /* cmp.l d1,d0: d0 con d1 */
static void set_ne(void) { w(0x7001); }                /* moveq #1,d0: Z = 0 */
static void test_bit0(int reg) { w(0x0800 | reg); w(0); }   /* btst #0,dN: Z si es par */
static void and_ea(Var *v) { op_ea(0xC080, v); }       /* and.l v,d0 */
static void and_imm(uint32_t k) { w(0x0280); l(k); }   /* andi.l #k,d0 */

/* el registro reg con v (o con d0 si v es NULL): cmp.l v,dN */
static void cmp_reg_ea(int reg, Var *v)
{
    if (v) op_ea(0xB080 | reg << 9, v);
    else w(0xB080 | reg << 9);
}

/* textos letra a letra: el byte de a0 con c, y a0 al siguiente; y si a0 está en el final */
static void cmp_byte_next(int c) { w(0x0C18); w(c); }  /* cmpi.b #c,(a0)+ */
static void tst_byte_a0(void) { w(0x4A10); }           /* tst.b (a0) */

static void push_a0(void)
{
    w(0x2F08);                                         /* move.l a0,-(sp) */
    sp_depth += 4;
}

/* d0 = lo de dl_d_cmp (-1, 0, 1 o 2 con un nan) para <, <=, >, >=: con 2, falso. gt: es > o >= */
static void dbl_cmp_order(int gt)
{
    int no = new_label(), done = new_label();
    w(0x0C80); l(2);                                   /* cmpi.l #2,d0 */
    branch(CC_EQ, no);
    w(0x4A80);                                         /* tst.l d0 */
    branch(CC_T, done);
    def_label(no);
    /* d0 = 2: comparado con 0 da "mayor", así que < y <= quedan falsos; > y >= se fuerzan con -1 (menor) */
    if (gt) w(0x70FF);                                 /* moveq #-1,d0 */
    w(0x4A80);                                         /* tst.l d0 */
    def_label(done);
}

static void push_data_long(long off)                   /* lo que hay en una variable de los datos */
{
    w(0x2F39);                                         /* move.l datos,-(sp) */
    add_reloc((uint32_t)obj->code.n, HK_DATA, NULL);
    l((uint32_t)off);
    sp_depth += 4;
}

/* d0 = la dirección de una etiqueta del código, o de un símbolo de fuera (del runtime o de @link) */
static void load_label(int label)
{
    Fixup f;
    w(0x203C);                                         /* move.l #etiqueta,d0 */
    f.at = (uint32_t)obj->code.n;
    f.label = label;
    f.abs = 1;
    f.size = 2;
    VEC_PUSH(fixups, f);
    add_reloc(f.at, HK_CODE, NULL);
    l(0);
}

static void load_sym(const char *sym)
{
    w(0x203C);                                         /* move.l #símbolo,d0 */
    add_reloc((uint32_t)obj->code.n, -1, sym);
    l(0);
}

/* ---- operaciones de un operando sobre d0 ---- */
static void neg_d0(void) { w(0x4480); }                /* neg.l d0 */
static void not_d0(void) { w(0x4680); }                /* not.l d0 */
static void float_neg(void) { w(0x0A80); l(0x80000000); }   /* eori.l #$80000000,d0: el signo de un Float */

static void abs_d0(void)
{
    tst_d0();
    w(0x6A02);                                         /* bpl.s +2 */
    w(0x4480);                                         /* neg.l d0 */
}

static void set_cc(int cc)                             /* d0 = 1 si se cumple la condición cc, 0 si no */
{
    w(0x50C0 | cc << 8);                               /* scc d0 */
    w(0x0280); l(1);                                   /* andi.l #1,d0 */
}

static void push_ea(Var *v)                            /* una variable a la pila (move.l, también una constante) */
{
    op_ea(0x2F00, v);                                  /* move.l v,-(sp) */
    sp_depth += 4;
}

static void store_arg_imm(int i, long k)               /* un número al argumento i (reserve_args) */
{
    w(0x2F7C);                                         /* move.l #k,d16(sp) */
    l((uint32_t)k);
    w(4 * i);
}

/* ---- v op= algo sin pasar por d0: op = 0 add, 1 sub, 2 and, 3 or ---- */
/* dN op= s (o, si s es NULL, op= dX) */
static void op_to_reg(int op, int reg, Var *s, int x)
{
    static const int to_reg[] = {0xD080, 0x9080, 0xC080, 0x8080};   /* op.l ea,dN */
    if (s) op_ea(to_reg[op] | reg << 9, s);
    else w(to_reg[op] | reg << 9 | x);
    flags_set(reg, op >= 2);                           /* and y or ponen V = 0 */
}

static void op_reg_to(int op, int x, Var *v)           /* v op= dX */
{
    static const int to_mem[] = {0xD180, 0x9180, 0xC180, 0x8180};   /* op.l dN,ea */
    op_ea(to_mem[op] | x << 9, v);
}

/* v op= k con op = P_AMP, P_BAR, P_CARET (v cualquiera) o P_SHL, P_SHR (v en un registro, k de 1 a 8) */
static void op_imm_into(int op, long k, Var *v)
{
    switch (op) {
    case P_AMP: op_imm_ea(0x0280, k, v); break;                /* andi.l #k,v */
    case P_BAR: op_imm_ea(0x0080, k, v); break;                /* ori.l #k,v */
    case P_CARET: op_imm_ea(0x0A80, k, v); break;              /* eori.l #k,v */
    case P_SHL: w(0xE180 | (k & 7) << 9 | v->reg); break;      /* asl.l #k,dN */
    case P_SHR: w(0xE080 | (k & 7) << 9 | v->reg); break;      /* asr.l #k,dN */
    }
    if (v->kind == V_REG) flags_set(v->reg, op != P_SHL);      /* asl puede poner V */
}

/* v (en un registro) /= 2^sh, redondeando hacia cero como divmod_pow2 */
static void reg_div_pow2(Var *v, int sh)
{
    uint32_t mask = (1u << sh) - 1;
    if (!flags_for(v, CC_PL)) w(0x4A80 | v->reg);      /* tst.l dN */
    if (mask <= 8) {
        w(0x6A02);                                     /* bpl.s +2 */
        w(0x5080 | (mask & 7) << 9 | v->reg);          /* addq.l #mask,dN */
    } else {
        w(0x6A06);                                     /* bpl.s +6 */
        w(0x0680 | v->reg); l(mask);                   /* addi.l #mask,dN */
    }
    w(0xE080 | (sh & 7) << 9 | v->reg);                /* asr.l #s,dN */
    flags_set(v->reg, 1);
}

/* ---- cómo son las listas y los diccionarios por dentro (el runtime de ./dash en el 68000) ---- */
#define ELEM 4                                         /* bytes de un elemento de lista */
#define ARR_DATA 0                                     /* DashArrayLong: data, length */
#define ARR_LEN 4
#define DICT_CAP 12                                    /* DashDict: keys 0, vals 4, count 8, cap 12, ikeys 24 */

static void a0_deref(void) { w(0x2050); }              /* movea.l (a0),a0 */
static void load_a0_raw(int off)                       /* d0 = off(a0) (sin tocar lo que se sabe de d0) */
{
    if (off) { w(0x2028); w(off); }                    /* move.l off(a0),d0 */
    else w(0x2010);                                    /* move.l (a0),d0 */
}

static void load_elem(void)                            /* d0 = el elemento d0 de los datos de a0 */
{
    w(0xD080); w(0xD080);                              /* add.l d0,d0 (x2): bytes */
    w(0x2030); w(0x0800);                              /* move.l (0,a0,d0.l),d0 */
}

static void load_char(void)                            /* d0 = el byte d0 de a0, con signo (un char de C) */
{
    w(0x1030); w(0x0800);                              /* move.b (0,a0,d0.l),d0 */
    w(0x4880); w(0x48C0);                              /* ext.w d0; ext.l d0 */
}

static void cmp_reg_a0(int reg, int off) { w(0xB0A8 | reg << 9); w(off); }   /* cmp.l off(a0),dN */
static void dict_test_ikeys(void) { w(0x4A68); w(24); }                       /* tst.w 24(a0): ikeys */

/* d0 -= k o v; dN += v */
static void sub_imm(long k)
{
    if (k >= 1 && k <= 8) w(0x5180 | (k & 7) << 9);   /* subq.l #k,d0 */
    else { w(0x0480); l((uint32_t)k); }                /* subi.l #k,d0 */
}
static void sub_ea(Var *v) { op_ea(0x9080, v); }       /* sub.l v,d0 */
static void add_to_reg(int reg, Var *v) { op_ea(0xD080 | reg << 9, v); }   /* add.l v,dN */

/* dbra dN,etiqueta */
static void dbra(int reg, int label)
{
    Fixup f;
    w(0x51C8 | reg);
    f.at = (uint32_t)obj->code.n;
    f.label = label;
    f.abs = 0;
    f.size = 2;
    VEC_PUSH(fixups, f);
    w(0);
}


/* fin de una vuelta de un bucle con contador (vc, de vueltas - 1): si quedan, a top. big: puede pasar de 65536 */
static void loop_count(Var *vc, int top, int big)
{
    if (vc->kind == V_REG) {
        dbra(vc->reg, top);
        if (big) {
            w(0x0480 | vc->reg); l(0x10000);           /* subi.l #$10000,dN: la parte alta del contador */
            branch(CC_CC, top);
        }
    } else {
        op_ea(0x5380, vc);                             /* subq.l #1,contador */
        branch(CC_CC, top);
    }
}

/* d0 con un número; small: con moveq a d1 si cabe en 8 bits (más corto) */
static void cmp_d0_k(long k, int small)
{
    if (small && k >= -128 && k <= 127) {
        w(0x7200 | (k & 0xFF));                        /* moveq #k,d1 */
        w(0xB081);                                     /* cmp.l d1,d0 */
    } else {
        w(0xB0BC); l((uint32_t)k);                     /* cmp.l #k,d0 */
    }
}

static void test_bit_d0(int bit) { w(0x0800); w(bit); }   /* btst #bit,d0: Z si está a 0 */
static void debug_nop(void) { w(0x4E71); }             /* nop: donde --debug pone un TRAP */

/* deja bytes de la pila antes de un salto (break, Stop, return): el código de después no lo ve (sin sp_depth) */
static void skip_stack(int bytes) { w(0x4FEF); w(bytes); }   /* lea bytes(sp),sp */

/* ---- funciones: marco con a5 (link/unlk) salvo frameless; las variables en registros (used: bit n = dN) se
   guardan al entrar y se recuperan al salir; los parámetros, en la pila desde 8(a5) ---- */
static uint32_t fn_frame_at;                           /* dónde va el tamaño del marco (link), que se sabe al final */

static int fn_param_base(int nregs) { return 4 + 4 * nregs; }   /* dirección de vuelta y registros guardados */
static int param_off(int i) { return 8 + 4 * i; }      /* el parámetro i, desde a5 */

static int regs_count(int used, int *last)
{
    int r, n = 0;
    for (r = 0; r < 8; r++)
        if (used & 1 << r) { n++; *last = r; }
    return n;
}

static void fn_prologue(int frameless, int used)
{
    int r, last = 0, n = regs_count(used, &last), mask = 0;
    for (r = 0; r < 8; r++)
        if (used & 1 << r) mask |= 0x8000 >> r;        /* movem -(sp): d0 es el bit 15 */
    if (!frameless) {
        w(0x4E55);                                     /* link a5,#-marco */
        fn_frame_at = (uint32_t)obj->code.n;
        w(0);
    }
    if (n == 1) w(0x2F00 | last);                      /* move.l dN,-(sp) */
    else if (n) { w(0x48E7); w(mask); }                /* movem.l regs,-(sp) */
}

/* el parámetro i a su registro (sin marco: desde sp, por encima de lo guardado) */
static void load_param(int reg, int i, int frameless)
{
    if (frameless) {
        w(0x202F | reg << 9);                          /* move.l d16(sp),dN */
        w(param_base + 4 * i);
    } else {
        w(0x202D | reg << 9);                          /* move.l 8+4i(a5),dN */
        w(8 + 4 * i);
    }
}

static void fn_epilogue(int frameless, int used, int nframe)
{
    int last = 0, n = regs_count(used, &last);
    if (n == 1) w(0x201F | last << 9);                 /* move.l (sp)+,dN */
    else if (n) { w(0x4CDF); w(used); }                /* movem.l (sp)+,regs: d0 es el bit 0 */
    if (!frameless) {
        w(0x4E5D);                                     /* unlk a5 */
        if (nframe * 4 > 32767) fatal("demasiadas variables en una función");
        put_word(obj->code.p + fn_frame_at, -4 * nframe);
    }
    w(0x4E75);                                         /* rts */
}

static void clear_global(long off)                     /* una global a 0 */
{
    w(0x42B9);                                         /* clr.l g */
    add_reloc((uint32_t)obj->code.n, HK_DATA, NULL);
    l((uint32_t)off);
}

/* ---- datos dentro del código (descriptores _DashType, tablas de métodos) ---- */
static void code_align(void) { }                       /* (palabras largas: el código ya va a 2 bytes) */
static void code_long(uint32_t v) { l(v); }

static void code_ptr(int label)                        /* la dirección de una etiqueta (-1: NULL) */
{
    if (label >= 0) {
        Fixup f;
        f.at = (uint32_t)obj->code.n;
        f.label = label;
        f.abs = 1;
        f.size = 2;
        VEC_PUSH(fixups, f);
        add_reloc(f.at, HK_CODE, NULL);
    }
    l(0);
}

/* el destructor de un struct (como lo llama el runtime: el objeto, de argumento): suelta sus campos con dueño */
static void destroy_begin(void)
{
    w(0x2F0A);                                         /* move.l a2,-(sp) */
    w(0x246F); w(8);                                   /* movea.l 8(sp),a2: el objeto */
}

static void destroy_field(int off, const char *sym)
{
    w(0x2F2A); w(off);                                 /* move.l campo(a2),-(sp) */
    jsr_sym(sym);
    w(0x588F);                                         /* addq.l #4,sp */
}

static void destroy_end(void)
{
    w(0x245F);                                         /* movea.l (sp)+,a2 */
    w(0x4E75);                                         /* rts */
}

static void code_data_ptr(uint32_t off)                /* la dirección de algo de los datos */
{
    add_reloc((uint32_t)obj->code.n, HK_DATA, NULL);
    l(off);
}

/* ---- el arranque: _dash_start(main, ficheros, pila) del runtime, con los argumentos en la pila ---- */
static void start_arg_long(uint32_t v) { w(0x2F3C); l(v); }   /* move.l #v,-(sp) (sin sp_depth: no vuelve) */

static void start_arg_label(int label)
{
    Fixup f;
    w(0x4879);                                         /* pea etiqueta */
    f.at = (uint32_t)obj->code.n;
    f.label = label;
    f.abs = 1;
    f.size = 2;
    VEC_PUSH(fixups, f);
    add_reloc(f.at, HK_CODE, NULL);
    l(0);
}

static void jmp_sym(const char *sym)
{
    w(0x4EF9);                                         /* jmp símbolo */
    add_reloc((uint32_t)obj->code.n, -1, sym);
    l(0);
}

/* la cabecera de los literales de los campos (dash_lit), al arrancar; d0 y a0 llevan la línea de órdenes */
static void lit_init_begin(void) { w(0x48E7); w(0x8080); }   /* movem.l d0/a0,-(sp) */

static void lit_init_one(uint32_t off)
{
    w(0x4879);                                         /* pea texto */
    add_reloc((uint32_t)obj->code.n, HK_DATA, NULL);
    l(off);
    jsr_sym("_dl_str_lit");
    w(0x588F);                                         /* addq.l #4,sp */
}

static void lit_init_end(void)
{
    w(0x4CDF); w(0x0101);                              /* movem.l (sp)+,d0/a0 */
    w(0x4E75);                                         /* rts */
}

static void or_ea(Var *v) { op_ea(0x8080, v); }        /* or.l v,d0 */

static void ptr_add(long k, Var *v) { add_imm_ea(k, v); }   /* un puntero += k (en el 68000, como un Int) */

/* la dirección de un array de n cosas que el recorrido dejó en la pila desde off(sp) (lng: de LONG; si no, de
   punteros): en el 68000 cada una ocupa ya 4 bytes */
static void push_array(int off, int n, int lng)
{
    (void)n;
    (void)lng;
    if (off) push_sp_addr(off);
    else push_sp();
}

/* ---- @amiga struct (A6): campos de 1, 2 y 4 bytes en a0 + off ---- */
static void zext_d0(void) { }                          /* (una dirección de 32 bits: en el 68000 ya lo es) */
static void amiga_check32(void) { }                    /* (en DashOS: que quepa en 32 bits) */

static void amiga_load(int off, int size, int sgn)
{
    if (size == 4) { w(0x2028); w(off); }             /* move.l off(a0),d0 */
    else if (size == 2) {
        if (!sgn) w(0x7000);                           /* moveq #0,d0 */
        w(0x3028); w(off);                             /* move.w off(a0),d0 */
        if (sgn) w(0x48C0);                            /* ext.l d0 */
    } else {
        if (!sgn) w(0x7000);
        w(0x1028); w(off);                             /* move.b off(a0),d0 */
        if (sgn) { w(0x4880); w(0x48C0); }             /* ext.w d0; ext.l d0 */
    }
    d0_loaded = (uint32_t)-1;
}

static void amiga_store(int off, int size)
{
    w(size == 4 ? 0x2140 : size == 2 ? 0x3140 : 0x1140); w(off);   /* move.l/w/b d0,off(a0) */
}

static void amiga_addr(int off)                        /* d0 = a0 + off */
{
    w(0x41E8); w(off);                                 /* lea off(a0),a0 */
    w(0x2008);                                         /* move.l a0,d0 */
    d0_loaded = (uint32_t)-1;
}
