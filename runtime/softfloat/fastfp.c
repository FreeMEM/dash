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

#if defined(__mc68000__) && !defined(DASH_FASTFP_C_ONLY)
/* Hand-written 68000 version of the multiply below (same algorithm and
   rounding): four mulu.w, addx for the carry, only d2-d5 saved, no frame.
   Checked against fp-bit on the Amiga by tests/test_fastfp_amiga.dash. */
__asm__(
"   .text\n"
"   .even\n"
"   .globl ___mulsf3\n"
"___mulsf3:\n"
"   move.l 4(sp),d0\n"
"   move.l 8(sp),d1\n"
"   movem.l d2-d5,-(sp)\n"
"   move.l d0,d2\n"
"   swap d2\n"
"   lsr.w #7,d2\n"
"   and.w #0xFF,d2\n"            /* ea */
"   beq .Lm_slow\n"
"   cmp.w #0xFF,d2\n"
"   beq .Lm_slow\n"
"   move.l d1,d3\n"
"   swap d3\n"
"   lsr.w #7,d3\n"
"   and.w #0xFF,d3\n"            /* eb */
"   beq .Lm_slow\n"
"   cmp.w #0xFF,d3\n"
"   beq .Lm_slow\n"
"   add.w d3,d2\n"
"   sub.w #127,d2\n"             /* e = ea + eb - 127 */
"   and.l #0x7FFFFF,d0\n"
"   bset #23,d0\n"               /* ma = ah:al */
"   and.l #0x7FFFFF,d1\n"
"   bset #23,d1\n"               /* mb = bh:bl */
"   move.l d0,d3\n"
"   swap d3\n"                   /* d3.w = ah */
"   move.l d1,d4\n"
"   swap d4\n"                   /* d4.w = bh */
"   move.w d0,d5\n"
"   mulu.w d1,d5\n"              /* ll = al * bl */
"   mulu.w d4,d0\n"              /* al * bh */
"   mulu.w d3,d1\n"              /* ah * bl */
"   mulu.w d4,d3\n"              /* hh = ah * bh */
"   add.l d1,d0\n"               /* mid (< 2^25) */
"   move.l d0,d1\n"
"   swap d1\n"
"   clr.w d1\n"                  /* mid << 16 */
"   clr.w d0\n"
"   swap d0\n"                   /* mid >> 16 */
"   add.l d1,d5\n"               /* lo = ll + (mid << 16), X = carry */
"   moveq #0,d1\n"
"   addx.l d1,d0\n"
"   add.l d3,d0\n"               /* hi = hh + (mid >> 16) + carry; product = d0:d5 */
"   btst #15,d0\n"
"   beq.s .Lm_b46\n"
"   addq.w #1,d2\n"              /* bit 47 set: mantissa = bits 47..24 */
"   lsl.l #8,d0\n"
"   move.l d5,d1\n"
"   rol.l #8,d1\n"
"   move.b d1,d0\n"
"   and.l #0xFFFFFF,d5\n"        /* rest */
"   move.l #0x800000,d4\n"       /* half */
"   bra.s .Lm_round\n"
".Lm_b46:\n"                     /* bit 46 is the top: mantissa = bits 46..23 */
"   lsl.l #8,d0\n"
"   move.l d5,d1\n"
"   rol.l #8,d1\n"
"   move.b d1,d0\n"
"   add.l d0,d0\n"
"   btst #23,d5\n"
"   beq.s .Lm_b23\n"
"   addq.l #1,d0\n"
".Lm_b23:\n"
"   and.l #0x7FFFFF,d5\n"
"   move.l #0x400000,d4\n"
".Lm_round:\n"                   /* round to nearest even */
"   cmp.l d4,d5\n"
"   bhi.s .Lm_up\n"
"   bne.s .Lm_done\n"
"   btst #0,d0\n"
"   beq.s .Lm_done\n"
".Lm_up:\n"
"   addq.l #1,d0\n"
"   btst #24,d0\n"
"   beq.s .Lm_done\n"
"   lsr.l #1,d0\n"
"   addq.w #1,d2\n"
".Lm_done:\n"
"   tst.w d2\n"                  /* overflow / underflow: exact routine */
"   ble.s .Lm_slow\n"
"   cmp.w #0xFF,d2\n"
"   bge.s .Lm_slow\n"
"   and.l #0x7FFFFF,d0\n"
"   moveq #0,d1\n"
"   move.w d2,d1\n"
"   swap d1\n"
"   lsl.l #7,d1\n"               /* e << 23 */
"   or.l d1,d0\n"
"   move.l 20(sp),d1\n"
"   move.l 24(sp),d3\n"
"   eor.l d3,d1\n"
"   and.l #0x80000000,d1\n"
"   or.l d1,d0\n"
"   movem.l (sp)+,d2-d5\n"
"   rts\n"
".Lm_slow:\n"
"   movem.l (sp)+,d2-d5\n"
"   jmp ___dash_fb_mulsf3\n"
);
#else
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

#endif

#if defined(__mc68000__) && !defined(DASH_FASTFP_C_ONLY)
/* Hand-written 68000 version of the add below (same algorithm and rounding).
   x is the operand with the larger magnitude; a0 keeps it for the sign, a1
   the exact fp-bit routine for the special cases (add or sub, with the
   arguments still on the stack). Checked by tests/test_fastfp_amiga.dash. */
__asm__(
"   .text\n"
"   .even\n"
"   .globl ___addsf3\n"
"   .globl ___subsf3\n"
"___subsf3:\n"
"   lea ___dash_fb_subsf3,a1\n"
"   move.l 4(sp),d0\n"
"   move.l 8(sp),d1\n"
"   bchg #31,d1\n"               /* a - b = a + (-b) */
"   bra.s .La_go\n"
"___addsf3:\n"
"   lea ___dash_fb_addsf3,a1\n"
"   move.l 4(sp),d0\n"
"   move.l 8(sp),d1\n"
".La_go:\n"
"   movem.l d2-d5,-(sp)\n"
"   move.l d0,d2\n"
"   add.l d2,d2\n"               /* |x| << 1 */
"   move.l d1,d3\n"
"   add.l d3,d3\n"               /* |y| << 1 */
"   cmp.l d3,d2\n"
"   bcc.s .La_order\n"
"   exg d0,d1\n"                 /* now |x| >= |y| */
"   exg d2,d3\n"
".La_order:\n"
"   swap d2\n"
"   lsr.w #8,d2\n"               /* ea (>= eb) */
"   cmp.w #0xFF,d2\n"
"   beq .La_slow\n"              /* inf or NaN */
"   swap d3\n"
"   lsr.w #8,d3\n"               /* eb */
"   beq .La_slow\n"              /* zero or denormal */
"   sub.w d2,d3\n"
"   neg.w d3\n"                  /* d = ea - eb */
"   move.l d1,d5\n"
"   and.l #0x7FFFFF,d5\n"
"   bset #23,d5\n"
"   lsl.l #6,d5\n"               /* mb: implicit bit at 29, six guard bits */
"   eor.l d0,d1\n"               /* bit 31: the signs differ */
"   move.l d0,a0\n"
"   move.l d0,d4\n"
"   and.l #0x7FFFFF,d4\n"
"   bset #23,d4\n"
"   lsl.l #6,d4\n"               /* ma */
"   tst.w d3\n"
"   beq.s .La_aligned\n"
"   cmp.w #6,d3\n"
"   bhi.s .La_sticky\n"
"   lsr.l d3,d5\n"               /* only the six zero guard bits go out */
"   bra.s .La_aligned\n"
".La_sticky:\n"
"   cmp.w #30,d3\n"
"   bhi.s .La_far\n"
"   moveq #-1,d0\n"
"   lsl.l d3,d0\n"
"   not.l d0\n"
"   and.l d5,d0\n"               /* the bits shifted out */
"   lsr.l d3,d5\n"
"   tst.l d0\n"
"   beq.s .La_aligned\n"
"   or.b #1,d5\n"                /* sticky bit */
"   bra.s .La_aligned\n"
".La_far:\n"
"   moveq #1,d5\n"
".La_aligned:\n"
"   tst.l d1\n"
"   bpl.s .La_add\n"
"   sub.l d5,d4\n"               /* m = ma - mb */
"   beq.s .La_zero\n"
"   btst #29,d4\n"
"   bne.s .La_round\n"
".La_norm:\n"
"   add.l d4,d4\n"
"   subq.w #1,d2\n"
"   btst #29,d4\n"
"   beq.s .La_norm\n"
"   bra.s .La_round\n"
".La_add:\n"
"   add.l d5,d4\n"               /* m = ma + mb */
"   btst #30,d4\n"
"   beq.s .La_round\n"
"   lsr.l #1,d4\n"
"   bcc.s .La_carry\n"
"   or.b #1,d4\n"                /* keep the lost bit as sticky */
".La_carry:\n"
"   addq.w #1,d2\n"
".La_round:\n"                   /* round to nearest even */
"   moveq #0x3F,d0\n"
"   and.w d4,d0\n"               /* rest */
"   lsr.l #6,d4\n"               /* mant */
"   cmp.w #0x20,d0\n"
"   bhi.s .La_up\n"
"   bne.s .La_done\n"
"   btst #0,d4\n"
"   beq.s .La_done\n"
".La_up:\n"
"   addq.l #1,d4\n"
"   btst #24,d4\n"
"   beq.s .La_done\n"
"   lsr.l #1,d4\n"
"   addq.w #1,d2\n"
".La_done:\n"
"   tst.w d2\n"                  /* overflow / underflow: exact routine */
"   ble.s .La_slow\n"
"   cmp.w #0xFF,d2\n"
"   bge.s .La_slow\n"
"   subq.w #1,d2\n"              /* mant has the implicit bit: (e - 1) << 23 + mant */
"   lsl.w #7,d2\n"
"   swap d2\n"
"   clr.w d2\n"
"   move.l d4,d0\n"
"   add.l d2,d0\n"
"   move.l a0,d1\n"
"   bpl.s .La_pos\n"
"   bset #31,d0\n"
".La_pos:\n"
"   movem.l (sp)+,d2-d5\n"
"   rts\n"
".La_zero:\n"
"   moveq #0,d0\n"               /* x - x = +0 */
"   movem.l (sp)+,d2-d5\n"
"   rts\n"
".La_slow:\n"
"   movem.l (sp)+,d2-d5\n"
"   jmp (a1)\n"
);
#else
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

#endif
