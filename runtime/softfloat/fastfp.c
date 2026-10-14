/*
 * Fast single-precision multiply and add for 68000 (Dash Float).
 *
 * The common case (normal numbers, normal result) is done here with 16x16
 * multiplies (mulu.w) and shifts; zeros, denormals, infinities, NaNs and
 * results that overflow or underflow go to the generic fp-bit routines
 * (renamed to __dash_fb_*), so every result is the IEEE one, rounded to
 * nearest even. tools/fastfp_check.py compares this file bit by bit with
 * the host FPU over millions of random operands.
 */

#ifndef DASH_MULSF3
#define DASH_MULSF3 __mulsf3
#define DASH_ADDSF3 __addsf3
#define DASH_SUBSF3 __subsf3
#define DASH_FB_MULSF3 __dash_fb_mulsf3
#define DASH_FB_ADDSF3 __dash_fb_addsf3
#endif

typedef unsigned int u32;      /* 32 bits on the Amiga and on the host check */
typedef int s32;
typedef unsigned short u16;
typedef union { float f; u32 u; } fu;

float DASH_FB_MULSF3(float a, float b);
float DASH_FB_ADDSF3(float a, float b);

/* a 16x16 -> 32 multiply: one mulu.w (GCC alone calls __mulsi3 for some) */
static inline u32 mul16(u16 a, u16 b)
{
#if defined(__mc68000__)
    u32 r = a;
    __asm__ ("mulu.w %1,%0" : "+d"(r) : "dmi"(b) : "cc");
    return r;
#else
    return (u32)a * (u32)b;
#endif
}

float DASH_MULSF3(float a, float b)
{
    fu x, y, r;
    u32 ea, eb, ma, mb, ll, mid, lo, hi, mant, rest, half;
    s32 e;
    x.f = a;
    y.f = b;
    ea = (x.u >> 23) & 0xFF;
    eb = (y.u >> 23) & 0xFF;
    if (ea == 0 || eb == 0 || ea == 0xFF || eb == 0xFF)
        return DASH_FB_MULSF3(a, b);
    ma = (x.u & 0x7FFFFF) | 0x800000;
    mb = (y.u & 0x7FFFFF) | 0x800000;
    /* 24 x 24 = 48-bit product as hi:lo, from 16-bit halves */
    ll = mul16((u16)ma, (u16)mb);
    mid = mul16((u16)ma, (u16)(mb >> 16)) + mul16((u16)(ma >> 16), (u16)mb);
    lo = ll + (mid << 16);
    hi = mul16((u16)(ma >> 16), (u16)(mb >> 16)) + (mid >> 16) + (lo < ll);
    e = (s32)ea + (s32)eb - 127;
    if (hi & 0x8000) {               /* bit 47 set: mantissa is bits 47..24 */
        mant = (hi << 8) | (lo >> 24);
        rest = lo & 0xFFFFFF;
        half = 0x800000;
        e++;
    } else {                         /* bit 46 is the top: bits 46..23 */
        mant = (hi << 9) | (lo >> 23);
        rest = lo & 0x7FFFFF;
        half = 0x400000;
    }
    if (rest > half || (rest == half && (mant & 1))) {
        mant++;
        if (mant == 0x1000000) {
            mant >>= 1;
            e++;
        }
    }
    if (e <= 0 || e >= 0xFF)         /* overflow or underflow: exact handling */
        return DASH_FB_MULSF3(a, b);
    r.u = ((x.u ^ y.u) & 0x80000000UL) | ((u32)e << 23) | (mant & 0x7FFFFF);
    return r.f;
}

float DASH_ADDSF3(float a, float b)
{
    fu x, y, r;
    u32 ea, eb, ma, mb, m, d, mant, rest;
    s32 e;
    x.f = a;
    y.f = b;
    ea = (x.u >> 23) & 0xFF;
    eb = (y.u >> 23) & 0xFF;
    if (ea == 0 || eb == 0 || ea == 0xFF || eb == 0xFF)
        return DASH_FB_ADDSF3(a, b);
    if ((x.u & 0x7FFFFFFF) < (y.u & 0x7FFFFFFF)) {   /* |x| >= |y| */
        fu t = x; x = y; y = t;
        d = ea; ea = eb; eb = d;
    }
    /* implicit bit at 29, six guard bits below the mantissa */
    ma = ((x.u & 0x7FFFFF) | 0x800000) << 6;
    mb = ((y.u & 0x7FFFFF) | 0x800000) << 6;
    d = ea - eb;
    if (d > 30)
        mb = 1;                                    /* only sticky */
    else if (d)
        mb = (mb >> d) | ((mb & ((1UL << d) - 1)) != 0);
    e = (s32)ea;
    if ((x.u ^ y.u) & 0x80000000UL) {
        m = ma - mb;
        if (m == 0) {
            r.u = 0;                               /* x - x = +0 */
            return r.f;
        }
        while (!(m & 0x20000000UL)) {
            m <<= 1;
            e--;
        }
    } else {
        m = ma + mb;
        if (m & 0x40000000UL) {
            m = (m >> 1) | (m & 1);
            e++;
        }
    }
    mant = m >> 6;
    rest = m & 0x3F;
    if (rest > 0x20 || (rest == 0x20 && (mant & 1))) {
        mant++;
        if (mant == 0x1000000) {
            mant >>= 1;
            e++;
        }
    }
    if (e <= 0 || e >= 0xFF)
        return DASH_FB_ADDSF3(a, b);
    r.u = (x.u & 0x80000000UL) | ((u32)e << 23) | (mant & 0x7FFFFF);
    return r.f;
}

float DASH_SUBSF3(float a, float b)
{
    fu y;
    y.f = b;
    y.u ^= 0x80000000UL;
    return DASH_ADDSF3(a, y.f);
}
