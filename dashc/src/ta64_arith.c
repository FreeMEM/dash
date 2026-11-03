/* Generador de AArch64 de dashc (docs/AARCH64_LOOP.md, fase A4): aritmética de d0 (x0). ARM multiplica y divide
   en una instrucción: no hacen falta los atajos del 68000. Lo incluye gen68k.c donde va t68k_arith.c. */

static int popcount(uint32_t m)
{
    int n = 0;
    while (m) { n += m & 1; m >>= 1; }
    return n;
}

/* d0 = d0 * k; src: un registro que ya tiene el valor de d0 (-1: ninguno) */
static void mul_const(long k, int src)
{
    int s = src >= 0 ? XREG(src) : 0;
    mov_imm(XT, (long)(int32_t)k);
    wop('*', 0, s, XT);
}

static __attribute__((unused)) void divmod_pow2(int op, long k, int s)        /* d0 = d0 / k o d0 % k, con k = ±2^s */
{
    (void)s;
    mov_imm(XT, (long)(int32_t)k);
    wop(op == P_SLASH ? '/' : '%', 0, 0, XT);
}

static void square_d0(void) { wop('*', 0, 0, 0); }

/* d0 = d0 op v */
static void bin_ea(int op, Var *v)
{
    int o = pop_op(op);
    if (!o) fatal("operador sin generar (dashc para DashOS)");
    var_to(XT, v);
    wop(o, 0, 0, XT);
}
