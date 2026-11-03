/* Generador de 68000 de dashc (docs/AARCH64_LOOP.md, fase A3): lo que sabe de las instrucciones del 68000. Lo
   incluye gen68k.c donde iba (un solo fichero de C: comparte sus estáticos). */
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
static void call_d0(void)
{
    w(0x2040);                                         /* movea.l d0,a0 */
    w(0x4E90);                                         /* jsr (a0) */
}

static void call_method(int slot)
{
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
