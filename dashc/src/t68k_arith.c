/* Generador de 68000 de dashc (docs/AARCH64_LOOP.md, fase A3): aritmética de d0 con una constante o con un operando
   (bin_ea: d0 = d0 op v). Lo incluye gen68k.c donde iba. */
/* ---- operaciones con una constante ---- */
static void shift_d0(int left, int s)
{
    if (s <= 0) return;
    if (left && s == 1) w(0xD080);                     /* add.l d0,d0 */
    else if (s <= 8) w((left ? 0xE180 : 0xE080) | (s & 7) << 9);   /* asl/asr.l #s,d0 */
    else {
        load_imm(1, s);
        w(left ? 0xE3A0 : 0xE2A0);                     /* asl/asr.l d1,d0 */
    }
}

static int popcount(uint32_t m)
{
    int c = 0;
    for (; m; m &= m - 1) c++;
    return c;
}

/* d0 = d0 * k; src: un registro que ya tiene el valor de d0 (-1: ninguno) */
static void mul_const(long k, int src)
{
    uint32_t m = k < 0 ? 0u - (uint32_t)k : (uint32_t)k;
    int neg = k < 0, s = 0;
    if (k == 0) { w(0x7000); return; }                 /* moveq #0,d0 */
    if (cpu020 && popcount(m) > 2) {
        w(0x4C3C); w(0x0800); l((uint32_t)k);          /* muls.l #k,d0 */
        return;
    }
    if (popcount(m) == 1) {
        while ((1u << s) != m) s++;
        shift_d0(1, s);
    } else if (popcount(m) == 2) {
        /* x * (2^a + 2^b) = ((x << (a-b)) + x) << b */
        int b = 0, a;
        while (!(m & (1u << b))) b++;
        a = b + 1;
        while (!(m & (1u << a))) a++;
        if (src < 0) {
            w(0x2200);                                 /* move.l d0,d1 */
            src = 1;
        }
        shift_d0(1, a - b);
        w(0xD080 | src);                               /* add.l dsrc,d0 */
        shift_d0(1, b);
    } else if (m <= 0xFFFF) {
        /* x * m = lo*m + ((hi*m) << 16): dos mulu.w */
        w(0x2200);                                     /* move.l d0,d1 */
        w(0x4841);                                     /* swap d1 */
        w(0xC2FC); w((int)m);                          /* mulu.w #m,d1 */
        w(0x4841);                                     /* swap d1 */
        w(0x4241);                                     /* clr.w d1 */
        w(0xC0FC); w((int)m);                          /* mulu.w #m,d0 */
        w(0xD081);                                     /* add.l d1,d0 */
    } else {
        /* x * m = lo*mlo + ((hi*mlo + lo*mhi) << 16): tres mulu.w */
        int mlo = (int)(m & 0xFFFF), mhi = (int)(m >> 16);
        w(0x2200);                                     /* move.l d0,d1 */
        w(0x4841);                                     /* swap d1 */
        w(0xC2FC); w(mlo);                             /* mulu.w #mlo,d1 */
        w(0x2040);                                     /* movea.l d0,a0 */
        w(0xC0FC); w(mhi);                             /* mulu.w #mhi,d0 */
        w(0xD240);                                     /* add.w d0,d1 */
        w(0x4841);                                     /* swap d1 */
        w(0x4241);                                     /* clr.w d1 */
        w(0x2008);                                     /* move.l a0,d0 */
        w(0xC0FC); w(mlo);                             /* mulu.w #mlo,d0 */
        w(0xD081);                                     /* add.l d1,d0 */
    }
    if (neg) w(0x4480);                                /* neg.l d0 */
}

/* d0 = d0 / k o d0 % k, con k = ±2^s, redondeando hacia cero como en C */
static void divmod_pow2(int op, long k, int s)
{
    uint32_t mask = (1u << s) - 1;
    if (op == P_SLASH) {
        tst_d0();
        if (mask <= 8) {
            w(0x6A02);                                 /* bpl.s +2 */
            w(0x5080 | (mask & 7) << 9);               /* addq.l #mask,d0 */
        } else {
            w(0x6A06);                                 /* bpl.s +6 */
            w(0xD0BC); l(mask);                        /* add.l #mask,d0 */
        }
        shift_d0(0, s);
        if (k < 0) w(0x4480);                          /* neg.l d0 */
    } else {
        /* el resto lleva el signo del dividendo: -(-x & mask) si x < 0 */
        tst_d0();
        w(0x6B08);                                     /* bmi.s +8 */
        w(0x0280); l(mask);                            /* andi.l #mask,d0 */
        w(0x600A);                                     /* bra.s +10 */
        w(0x4480);                                     /* neg.l d0 */
        w(0x0280); l(mask);                            /* andi.l #mask,d0 */
        w(0x4480);                                     /* neg.l d0 */
    }
}

/* d0 = d0 / k o d0 % k, con 1 < k <= 65535: un divu.w si el dividendo es >= 0 y el
   cociente cabe en 16 bits (como el camino rápido del runtime, sin la llamada).
   El camino rápido es el del salto: un salto tomado cuesta menos que uno no tomado
   y un bra. */
static void divmod_const(int op, long k)
{
    int load = k <= 127 ? 2 : 6;                       /* moveq o move.l #k,d1 */
    w(0xB0BC); l(((uint32_t)k << 16) - 1);             /* cmp.l #(k << 16) - 1,d0 */
    w(0x6300 | (load + 10));                           /* bls.s rápido (sin signo: un negativo es enorme) */
    load_imm(1, k);
    jsr_sym(op == P_SLASH ? "__dash_divk" : "__dash_modk");   /* sin volver a probar el divu.w */
    w(0x4A80);                                         /* tst.l d0, como deja el swap del otro camino */
    w(op == P_SLASH ? 0x600A : 0x6008);                /* bra.s fin */
    w(0x80FC); w((int)k);                              /* rápido: divu.w #k,d0, resto:cociente */
    if (op == P_SLASH) { w(0x4840); w(0x4240); w(0x4840); }   /* swap; clr.w; swap: el cociente */
    else { w(0x4240); w(0x4840); }                     /* clr.w; swap: el resto */
    d0_loaded = (uint32_t)obj->code.n;                 /* los códigos dicen cómo es d0 */
}

/* d0 = d0 / d1 o d0 % d1: divu.w si 1 <= d1 <= 32767 y la parte alta de d0 es menor
   que d1 (eso ya dice que d0 >= 0 y que el cociente cabe en 16 bits); si no, el runtime */
static void divmod_d1(int op)
{
    int x = op == P_SLASH ? 6 : 4;                     /* lo que saca el cociente o el resto */
    if (cpu020) {
        w(0x4C41);                                     /* divs.l d1,d0 / divsl.l d1,d1:d0 */
        if (op == P_SLASH) w(0x0800);
        else { w(0x0801); w(0x2001); }                 /* el resto, a d0: move.l d1,d0 */
        d0_loaded = (uint32_t)obj->code.n;
        return;
    }
    w(0xB2BC); l(0x7FFF);                              /* cmp.l #$7FFF,d1 */
    w(0x6200 | (18 + x));                              /* bhi.s lento (también los negativos) */
    w(0x4A41);                                         /* tst.w d1 */
    w(0x6700 | (14 + x));                              /* beq.s lento */
    w(0x4840); w(0xB041);                              /* swap d0; cmp.w d1,d0 */
    w(0x6400 | (6 + x));                               /* bcc.s lento_swap */
    w(0x4840); w(0x80C1);                              /* swap d0; divu.w d1,d0 */
    if (op == P_SLASH) { w(0x4840); w(0x4240); w(0x4840); }   /* swap; clr.w; swap: el cociente */
    else { w(0x4240); w(0x4840); }                     /* clr.w; swap: el resto */
    w(0x600A);                                         /* bra.s fin */
    w(0x4840);                                         /* lento_swap: swap d0 */
    jsr_sym(op == P_SLASH ? "__dash_div" : "__dash_mod");   /* lento */
    w(0x4A80);                                         /* tst.l d0 */
    d0_loaded = (uint32_t)obj->code.n;
}

/* d0 = d0 * d1: muls.w si los dos caben en 16 bits con signo; si no, el runtime */
static void mul_d1(void)
{
    if (cpu020) {
        w(0x4C01); w(0x0800);                          /* muls.l d1,d0 */
        d0_loaded = (uint32_t)obj->code.n;
        return;
    }
    w(0x3040); w(0xB088); w(0x6606);                   /* movea.w d0,a0; cmp.l a0,d0; bne.s lento */
    w(0x3041); w(0xB288); w(0x670A);                   /* movea.w d1,a0; cmp.l a0,d1; beq.s rápido */
    jsr_sym("__dash_mul");                             /* lento */
    w(0x4A80);                                         /* tst.l d0 */
    w(0x6002);                                         /* bra.s fin */
    w(0xC1C1);                                         /* rápido: muls.w d1,d0 */
    d0_loaded = (uint32_t)obj->code.n;
}

/* d0 = d0 * d0 */
static void square_d0(void)
{
    if (cpu020) {
        w(0x4C00); w(0x0800);                          /* muls.l d0,d0 */
        d0_loaded = (uint32_t)obj->code.n;
        return;
    }
    w(0x3040); w(0xB088); w(0x670C);                   /* movea.w d0,a0; cmp.l a0,d0; beq.s rápido */
    w(0x2200);                                         /* move.l d0,d1 */
    jsr_sym("__dash_mul");
    w(0x4A80);                                         /* tst.l d0 */
    w(0x6002);                                         /* bra.s fin */
    w(0xC1C0);                                         /* rápido: muls.w d0,d0 */
    d0_loaded = (uint32_t)obj->code.n;
}

/* d0 = d0 op v */
static void bin_ea(int op, Var *v)
{
    long k = v->val;
    int s;
    if (v->kind == V_CONST) {
        switch (op) {
        case P_PLUS:
        case P_MINUS:
            if (op == P_MINUS) k = -k;
            if (k >= 1 && k <= 8) w(0x5080 | (k & 7) << 9);          /* addq.l #k,d0 */
            else if (k <= -1 && k >= -8) w(0x5180 | (-k & 7) << 9);  /* subq.l #k,d0 */
            else if (k) { w(0xD0BC); l((uint32_t)k); }                /* add.l #k,d0 */
            return;
        case P_STAR:
            mul_const(k, -1);
            return;
        case P_SLASH:
        case P_PERCENT:
            if (k == 1 || k == -1) {
                if (op == P_PERCENT) w(0x7000);        /* moveq #0,d0 */
                else if (k == -1) w(0x4480);           /* neg.l d0 */
                return;
            }
            if ((s = pow2(k)) != 0) {
                divmod_pow2(op, k, s);
                return;
            }
            if (k > 1 && k <= 65535) {
                divmod_const(op, k);
                return;
            }
            break;
        case P_SHL:
        case P_SHR:
            if (k >= 0 && k <= 31) {
                shift_d0(op == P_SHL, (int)k);
                return;
            }
            break;
        }
    }
    switch (op) {
    case P_PLUS: op_ea(0xD080, v); return;             /* add.l v,d0 */
    case P_MINUS: op_ea(0x9080, v); return;            /* sub.l v,d0 */
    case P_AMP: op_ea(0xC080, v); return;              /* and.l v,d0 */
    case P_BAR: op_ea(0x8080, v); return;              /* or.l v,d0 */
    case P_CARET:
        if (v->kind == V_REG) { w(0xB180 | v->reg << 9); return; }  /* eor.l dN,d0 */
        break;
    }
    load_var(1, v);
    switch (op) {
    case P_CARET: w(0xB380); break;                    /* eor.l d1,d0 */
    case P_SHL: w(0xE3A0); break;                      /* asl.l d1,d0 */
    case P_SHR: w(0xE2A0); break;                      /* asr.l d1,d0 */
    case P_STAR: mul_d1(); break;
    case P_SLASH:
    case P_PERCENT:
        /* en un bucle, el camino rápido aquí (no con un divisor fijo, que ya se sabe que no cabe en 16 bits) */
        if (cpu020 || (loop_weight > 1 && v->kind != V_CONST)) divmod_d1(op);
        else jsr_sym(op == P_SLASH ? "__dash_div" : "__dash_mod");
        break;
    }
}
