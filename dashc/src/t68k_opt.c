/* Generador de 68000 de dashc (docs/AARCH64_LOOP.md, fase A3): optimizaciones propias del 68000 que el recorrido
   común pide por su nombre (devuelven 0 si no se aplican; otro procesador puede no tener ninguna). Usan funciones del
   recorrido (value, simple, var_range...): lo incluye gen68k.c donde iba. */

/* con rangos conocidos: sin comprobar si cabe en 16 bits */
static int gen_ranged(Node *n)
{
    long k, alo, ahi, blo, bhi;
    Var v;
    int op = n->op;
    if (!var_range(n->a, &alo, &ahi)) return 0;
    if ((op == P_SLASH || op == P_PERCENT) && alo >= 0 && fold(n->b, &k) && k > 1 && k <= 65535) {
        int s = pow2(k);
        if (!s && ahi >= (long)((uint32_t)k << 16)) return 0;   /* el cociente no cabe */
        value(n->a);
        if (s && op == P_SLASH) shift_d0(0, s);
        else if (s) { w(0x0280); l((uint32_t)k - 1); }  /* andi.l #k-1,d0 */
        else {
            w(0x80FC); w((int)k);                      /* divu.w #k,d0 */
            if (op == P_SLASH) { w(0x4840); w(0x4240); w(0x4840); }   /* swap; clr.w; swap */
            else { w(0x4240); w(0x4840); }             /* clr.w; swap */
        }
        d0_loaded = (uint32_t)obj->code.n;             /* los códigos dicen cómo es d0 */
        return 1;
    }
    if ((op == P_SLASH || op == P_PERCENT) && alo >= 0 && ahi <= 0xFFFF && !fold(n->b, &k) && loop_weight > 1) {
        /* dividendo de 16 bits: el cociente cabe; solo hace falta 1 <= divisor <= 65535 */
        int x = op == P_SLASH ? 6 : 4, r = 1;
        value(n->a);
        if (simple(n->b, &v)) {
            if (v.kind == V_REG) r = v.reg;            /* el divisor ya está en un registro */
            else load_var(1, &v);
        } else {
            push_d0();
            value(n->b);
            w(0x2200);                                 /* move.l d0,d1 */
            pop_d0();
        }
        if (!var_range(n->b, &blo, &bhi)) blo = -1, bhi = INT32_MAX;
        if (blo >= 1 && bhi <= 0xFFFF) {
            w(0x80C0 | r);                             /* divu.w dr,d0 */
            if (op == P_SLASH) { w(0x4840); w(0x4240); w(0x4840); }
            else { w(0x4240); w(0x4840); }
            d0_loaded = (uint32_t)obj->code.n;
            return 1;
        }
        w(0xB0BC | r << 9); l(0xFFFF);                 /* cmp.l #$FFFF,dr */
        if (blo >= 1) {
            w(0x6200 | (4 + x));                       /* bhi.s lento; el divisor no es 0 */
        } else {
            w(0x6200 | (8 + x));                       /* bhi.s lento (también los negativos) */
            w(0x4A40 | r);                             /* tst.w dr */
            w(0x6700 | (4 + x));                       /* beq.s lento */
        }
        w(0x80C0 | r);                                 /* divu.w dr,d0 */
        if (op == P_SLASH) { w(0x4840); w(0x4240); w(0x4840); }
        else { w(0x4240); w(0x4840); }
        w(r == 1 ? 0x6008 : 0x600A);                   /* bra.s fin */
        if (r != 1) w(0x2200 | r);                     /* lento: move.l dr,d1 */
        jsr_sym(op == P_SLASH ? "__dash_div" : "__dash_mod");
        w(0x4A80);                                     /* tst.l d0: así los dos caminos dejan los códigos */
        d0_loaded = (uint32_t)obj->code.n;
        return 1;
    }
    if (op == P_STAR && alo >= -32768 && ahi <= 32767 && var_range(n->b, &blo, &bhi) &&
        blo >= -32768 && bhi <= 32767 && !fold(n->a, &k) && !fold(n->b, &k)) {
        value(n->a);
        simple(n->b, &v);
        if (v.kind != V_REG) {
            load_var(1, &v);
            v.kind = V_REG;
            v.reg = 1;
        }
        w(0xC1C0 | v.reg);                             /* muls.w dN,d0 */
        return 1;
    }
    return 0;
}
