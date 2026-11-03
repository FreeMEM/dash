/* Dash en DashOS: las conversiones de coma flotante por software que pide clang y que el fp-bit de GCC
   (runtime/softfloat) no trae, porque en libgcc están en libgcc2.c. Se escriben con las que sí trae: este fichero
   se compila sin registros de coma flotante, y cada operación con float o double es una llamada. */

unsigned int __fixunssfsi(float a)
{
    if (!(a >= 0.0f)) return 0;
    if (a >= 2147483648.0f) return (unsigned int)(int)(a - 2147483648.0f) + 0x80000000u;
    return (unsigned int)(int)a;
}

unsigned int __fixunsdfsi(double a)
{
    if (!(a >= 0.0)) return 0;
    if (a >= 2147483648.0) return (unsigned int)(int)(a - 2147483648.0) + 0x80000000u;
    return (unsigned int)(int)a;
}

/* Float a Double, bit a bit (exacto) */
double __extendsfdf2(float f)
{
    union { float f; unsigned int u; } a;
    union { unsigned long long u; double d; } b;
    unsigned int s, e, m;
    a.f = f;
    s = a.u >> 31;
    e = a.u >> 23 & 0xFF;
    m = a.u & 0x7FFFFF;
    if (e == 0xFF) b.u = (unsigned long long)s << 63 | 0x7FFULL << 52 | (unsigned long long)m << 29;
    else if (e == 0 && !m) b.u = (unsigned long long)s << 63;
    else if (e == 0) {                                 /* subnormal: se normaliza */
        int sh = 0;
        while (!(m & 0x800000)) { m <<= 1; sh++; }
        m &= 0x7FFFFF;
        b.u = (unsigned long long)s << 63 | (unsigned long long)(1023 - 126 - sh) << 52 | (unsigned long long)m << 29;
    } else b.u = (unsigned long long)s << 63 | (unsigned long long)(e - 127 + 1023) << 52 | (unsigned long long)m << 29;
    return b.d;
}
