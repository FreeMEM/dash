/* Para tests/test_fixdf_fpu.dash: double a entero de 64 bits y sin signo (se compila a libfixdf.a con -m68020 -m68881,
   como el C de Tachyon). Lo vio Tachyon: 1709164800000.0 daba 2^32 de más. */
static const double v[] = { 1709164800000.0, -1709164800000.0, 0, 0, 0, 8589934591.5 };
long fixdf_alto(long i) { long long x = (long long)v[i]; return (long)(x >> 32); }
long fixdf_bajo(long i) { long long x = (long long)v[i]; return (long)x; }
