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
/* Hand-written 68000 version of the multiply below (same result, bit by bit).
   ma is taken shifted left by 8, so the high 32 bits of the 56-bit product
   are already the mantissa (or need one more bit) and the low 32 bits are
   the rest to round. Exponents stay as "e << 7" in the high word of the
   operand, no shifts; d2 keeps the result sign in bit 31 and (e - 1) << 7
   in the low word, checked with one unsigned compare. Four mulu.w; only
   d2-d5 saved, no frame. Checked against fp-bit on the Amiga by
   tests/test_fastfp_amiga.dash. */
__asm__(
"   .text\n"
"   .even\n"
"   .globl ___mulsf3\n"
"___mulsf3:\n"
"   move.l 4(sp),d0\n"
"   move.l 8(sp),d1\n"
"   movem.l d2-d5,-(sp)\n"
"   move.l d0,d2\n"
"   eor.l d1,d2\n"               /* bit 31: sign of the result */
"   move.l d0,d3\n"
"   swap d3\n"
"   and.w #0x7F80,d3\n"          /* ea << 7 */
"   beq .Lm_slow\n"
"   cmp.w #0x7F80,d3\n"
"   beq .Lm_slow\n"
"   move.l d1,d4\n"
"   swap d4\n"
"   and.w #0x7F80,d4\n"          /* eb << 7 */
"   beq .Lm_slow\n"
"   cmp.w #0x7F80,d4\n"
"   beq .Lm_slow\n"
"   add.w d4,d3\n"
"   sub.w #0x4000,d3\n"
"   move.w d3,d2\n"              /* (ea + eb - 128) << 7 */
"   lsl.l #8,d0\n"
"   bset #31,d0\n"               /* ma << 8 = ah:al (16 bits each) */
"   and.l #0x7FFFFF,d1\n"
"   bset #23,d1\n"               /* mb = bh:bl (8 and 16 bits) */
"   move.b ___dash_fp020,d3\n"   /* a 68020, 030 or 040: one mulu.l (64 bits) */
"   bmi.s .Lm_000\n"             /* (the 68000 goes on with one short branch: 26 cycles) */
"   bne.s .Lm_020\n"
"   move.l 4.w,a0\n"             /* the first time: the CPU from AttnFlags of ExecBase */
"   move.w 296(a0),d3\n"
"   moveq #-1,d4\n"
"   btst #1,d3\n"                /* AFF_68020 (also set on 030, 040 and 060) */
"   beq.s .Lm_set\n"
"   btst #7,d3\n"                /* AFF_68060: no 64-bit mulu.l (68060.library emulates it, slowly) */
"   bne.s .Lm_set\n"
"   moveq #1,d4\n"
".Lm_set:\n"
"   move.b d4,___dash_fp020\n"
"   bmi.s .Lm_000\n"
".Lm_020:\n"
"   move.l d0,d5\n"
"   .word 0x4C01,0x5400\n"       /* mulu.l d1,d0:d5 (written as words: the file is 68000 code) */
"   bra .Lm_prod\n"
".Lm_000:\n"
"   move.l d0,d3\n"
"   swap d3\n"                   /* d3.w = ah */
"   move.l d1,d4\n"
"   swap d4\n"                   /* d4.w = bh */
"   move.w d0,d5\n"
"   mulu.w d1,d5\n"              /* ll = al * bl */
"   mulu.w d4,d0\n"              /* al * bh */
"   mulu.w d3,d1\n"              /* ah * bl */
"   mulu.w d4,d3\n"              /* hh = ah * bh (< 2^24) */
"   add.l d1,d0\n"               /* mid, X = its bit 32 */
"   move.l d0,d1\n"
"   swap d1\n"
"   clr.w d1\n"                  /* mid << 16 */
"   clr.w d0\n"
"   addx.w d0,d0\n"
"   swap d0\n"                   /* mid >> 16, with bit 32 */
"   add.l d1,d5\n"               /* lo = ll + (mid << 16), X = carry */
"   moveq #0,d1\n"
"   addx.l d1,d0\n"
"   add.l d3,d0\n"               /* hi = hh + (mid >> 16) + carry */
".Lm_prod:\n"                    /* hi in d0, lo in d5 */
"   btst #23,d0\n"
"   bne.s .Lm_top\n"
"   add.l d5,d5\n"               /* top bit is 54: mantissa = hi:lo << 1 */
"   addx.l d0,d0\n"
"   bra.s .Lm_round\n"
".Lm_top:\n"
"   add.w #0x80,d2\n"            /* top bit is 55: mantissa = hi, e + 1 */
".Lm_round:\n"                   /* round to nearest even; rest = d5 */
"   add.l d5,d5\n"               /* C = half bit, Z = nothing below it */
"   bcc.s .Lm_done\n"
"   bne.s .Lm_up\n"
"   btst #0,d0\n"
"   beq.s .Lm_done\n"
".Lm_up:\n"
"   addq.l #1,d0\n"
"   btst #24,d0\n"
"   beq.s .Lm_done\n"
"   lsr.l #1,d0\n"
"   add.w #0x80,d2\n"
".Lm_done:\n"
"   cmp.w #0x7E80,d2\n"          /* e outside 1..254: exact routine */
"   bhi.s .Lm_slow\n"
"   tst.l d2\n"
"   bpl.s .Lm_pos\n"
"   bset #31,d0\n"
".Lm_pos:\n"
"   swap d2\n"
"   clr.w d2\n"
"   add.l d2,d0\n"               /* (e - 1) << 23 + mantissa with its bit 23 */
"   movem.l (sp)+,d2-d5\n"
"   rts\n"
".Lm_slow:\n"
"   movem.l (sp)+,d2-d5\n"
"   jmp ___dash_fb_mulsf3\n"
"   .data\n"
"   .globl ___dash_fp020\n"
"___dash_fp020:\n"
"   .byte 0\n"                   /* 0: not looked yet; 1: 68020-68040; -1: 68000, 010 or 060 */
"   .even\n"
"   .text\n"
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
/* Hand-written 68000 version of the add below (same result, bit by bit).
   x is the operand with the larger magnitude (a0), y the other one (a1).
   Mantissas with the implicit bit at 31 and eight guard bits; the carry of
   an add comes back in with roxr. Only d2-d3 saved. The special cases call
   fp-bit's add with x and y (a - b enters as a + (-b)). Checked by
   tests/test_fastfp_amiga.dash. */
__asm__(
"   .text\n"
"   .even\n"
"   .globl ___addsf3\n"
"   .globl ___subsf3\n"
"___subsf3:\n"
"   move.l 4(sp),d0\n"
"   move.l 8(sp),d1\n"
"   bchg #31,d1\n"               /* a - b = a + (-b) */
"   bra.s .La_go\n"
"___addsf3:\n"
"   move.l 4(sp),d0\n"
"   move.l 8(sp),d1\n"
".La_go:\n"
"   movem.l d2-d3,-(sp)\n"
"   move.l d0,d2\n"
"   add.l d2,d2\n"               /* |x| << 1 */
"   move.l d1,d3\n"
"   add.l d3,d3\n"               /* |y| << 1 */
"   cmp.l d3,d2\n"
"   bcc.s .La_order\n"
"   exg d0,d1\n"                 /* now |x| >= |y| */
"   exg d2,d3\n"
".La_order:\n"
"   move.l d0,a0\n"
"   move.l d1,a1\n"
"   swap d2\n"
"   lsr.w #8,d2\n"               /* ea (>= eb) */
"   cmp.w #0xFF,d2\n"
"   beq .La_slow\n"              /* inf or NaN */
"   swap d3\n"
"   lsr.w #8,d3\n"               /* eb */
"   beq .La_slow\n"              /* zero or denormal */
"   eor.l d0,d1\n"               /* bit 31: the signs differ */
"   sub.w d2,d3\n"
"   neg.w d3\n"
"   move.w d3,d1\n"              /* d1.w = d = ea - eb */
"   move.l a1,d3\n"
"   lsl.l #8,d3\n"
"   bset #31,d3\n"               /* mb */
"   tst.w d1\n"
"   beq.s .La_aligned\n"
"   cmp.w #8,d1\n"
"   bhi.s .La_sticky\n"
"   lsr.l d1,d3\n"               /* only the zero guard bits go out */
"   bra.s .La_aligned\n"
".La_sticky:\n"
"   cmp.w #31,d1\n"
"   bhi.s .La_far\n"
"   moveq #-1,d0\n"
"   lsl.l d1,d0\n"
"   not.l d0\n"
"   and.l d3,d0\n"               /* the bits shifted out */
"   lsr.l d1,d3\n"
"   tst.l d0\n"
"   beq.s .La_aligned\n"
"   or.b #1,d3\n"                /* sticky bit */
"   bra.s .La_aligned\n"
".La_far:\n"
"   moveq #1,d3\n"
".La_aligned:\n"
"   move.l a0,d0\n"
"   lsl.l #8,d0\n"
"   bset #31,d0\n"               /* ma */
"   tst.l d1\n"
"   bmi.s .La_sub\n"
"   add.l d3,d0\n"
"   bcc.s .La_round\n"
"   roxr.l #1,d0\n"              /* carry back in at bit 31 */
"   bcc.s .La_carry\n"
"   or.b #1,d0\n"                /* keep the lost bit as sticky */
".La_carry:\n"
"   addq.w #1,d2\n"
"   bra.s .La_round\n"
".La_sub:\n"
"   sub.l d3,d0\n"
"   beq.s .La_zero\n"
"   bmi.s .La_round\n"
".La_norm:\n"
"   subq.w #1,d2\n"
"   add.l d0,d0\n"
"   bpl.s .La_norm\n"
".La_round:\n"                   /* round to nearest even; rest = low byte */
"   cmp.b #0x80,d0\n"
"   bcs.s .La_done\n"
"   bne.s .La_up\n"
"   btst #8,d0\n"
"   beq.s .La_done\n"
".La_up:\n"
"   add.l #0x100,d0\n"
"   bcc.s .La_done\n"
"   roxr.l #1,d0\n"
"   addq.w #1,d2\n"
".La_done:\n"
"   tst.w d2\n"                  /* overflow / underflow: exact routine */
"   ble.s .La_slow\n"
"   cmp.w #0xFF,d2\n"
"   bge.s .La_slow\n"
"   add.l d0,d0\n"               /* drop the implicit bit */
"   move.b d2,d0\n"              /* e in the low byte */
"   ror.l #8,d0\n"               /* e : fraction : one spare bit */
"   move.l a0,d1\n"
"   add.l d1,d1\n"               /* X = sign of x */
"   roxr.l #1,d0\n"              /* sign : e : fraction */
"   movem.l (sp)+,d2-d3\n"
"   rts\n"
".La_zero:\n"
"   moveq #0,d0\n"               /* x - x = +0 */
"   movem.l (sp)+,d2-d3\n"
"   rts\n"
".La_slow:\n"
"   movem.l (sp)+,d2-d3\n"
"   move.l a1,-(sp)\n"
"   move.l a0,-(sp)\n"
"   jsr ___dash_fb_addsf3\n"
"   addq.l #8,sp\n"
"   rts\n"
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
