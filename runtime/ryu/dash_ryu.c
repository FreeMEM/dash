/* Dash's entry points to Ryu (Lorraine D1, D3): a double to its shortest decimal (d2s.c) and a decimal of up
   to 17 significant digits to the nearest double (s2d.c). Both in one file so they share the table. */
#if defined(__mc68000__) && !defined(RYU_32_BIT_PLATFORM)
#define RYU_32_BIT_PLATFORM
#endif
#include "ryu/d2s.c"
#include "ryu/s2d.c"

/* d (finite and not zero; the sign is ignored) = *mant * 10^*exp, with the fewest digits in *mant and, of
   those, the nearest to d (from Tachyon's third_party/ryu/d2d.c) */
void dash_ryu_d2d(double d, uint64_t *mant, int32_t *exp)
{
    const uint64_t bits = double_to_bits(d);
    const uint64_t ieeeMantissa = bits & ((1ull << DOUBLE_MANTISSA_BITS) - 1);
    const uint32_t ieeeExponent = (uint32_t) ((bits >> DOUBLE_MANTISSA_BITS) & ((1u << DOUBLE_EXPONENT_BITS) - 1));
    floating_decimal_64 v;
    if (d2d_small_int(ieeeMantissa, ieeeExponent, &v)) {
        for (;;) {
            const uint64_t q = div10(v.mantissa);
            const uint32_t r = ((uint32_t) v.mantissa) - 10 * ((uint32_t) q);
            if (r != 0)
                break;
            v.mantissa = q;
            ++v.exponent;
        }
    } else {
        v = d2d(ieeeMantissa, ieeeExponent);
    }
    *mant = v.mantissa;
    *exp = v.exponent;
}

/* The double of the decimal in s[0..len-1] ([-]digits[.digits][e[+-]digits], up to 17 significant digits):
   0 and *out set, or not 0 */
int dash_ryu_s2d(const char *s, int len, double *out)
{
    return s2d_n(s, len, out) == SUCCESS ? 0 : 1;
}
