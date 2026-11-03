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
