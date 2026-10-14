#!/usr/bin/env python3
"""Check runtime/softfloat/fastfp.c bit by bit against the host FPU.

Builds fastfp.c for the host (the fp-bit fallbacks become the host's own
float operations) and compares multiply, add and subtract over random
operands: any bits, close exponents (cancellation), extreme exponents
(overflow/underflow paths) and mixed signs. Exit code 1 on any mismatch.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HARNESS = r'''
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#define DASH_MULSF3 fast_mul
#define DASH_ADDSF3 fast_add
#define DASH_SUBSF3 fast_sub
#define DASH_FB_MULSF3 host_mul
#define DASH_FB_ADDSF3 host_add
float host_mul(float a, float b) { volatile float r = a * b; return r; }
float host_add(float a, float b) { volatile float r = a + b; return r; }
#include "FASTFP"
static uint32_t s = 12345;
static uint32_t rnd(void) { s ^= s << 13; s ^= s >> 17; s ^= s << 5; return s; }
static float f(uint32_t u) { float x; memcpy(&x, &u, 4); return x; }
static uint32_t u(float x) { uint32_t v; memcpy(&v, &x, 4); return v; }
int main(void) {
    long bad = 0, n;
    for (n = 0; n < 3000000; n++) {
        uint32_t ua = rnd(), ub = rnd();
        int kind = n % 4;
        if (kind == 1) ub = (ub & 0x807FFFFF) | (ua & 0x7F800000);            /* same exponent */
        if (kind == 2) ub = (ub & 0x807FFFFF) | ((ua + ((rnd() & 7) << 23)) & 0x7F800000);  /* close */
        if (kind == 3) { ua = (ua & 0x80FFFFFF) | ((rnd() & 1) ? 0x7E000000 : 0x01000000); }  /* extremes */
        float a = f(ua), b = f(ub);
        if (a != a || b != b) continue;
        volatile float hm = a * b, ha = a + b, hs = a - b;
        float m = fast_mul(a, b), ad = fast_add(a, b), sb = fast_sub(a, b);
        if (u(m) != u(hm) && !(m != m && hm != hm)) { if (bad++ < 5) printf("mul %08x %08x: %08x host %08x\n", ua, ub, u(m), u(hm)); }
        if (u(ad) != u(ha) && !(ad != ad && ha != ha)) { if (bad++ < 5) printf("add %08x %08x: %08x host %08x\n", ua, ub, u(ad), u(ha)); }
        if (u(sb) != u(hs) && !(sb != sb && hs != hs)) { if (bad++ < 5) printf("sub %08x %08x: %08x host %08x\n", ua, ub, u(sb), u(hs)); }
    }
    printf("%ld differences in %ld cases x 3 operations\n", bad, n);
    return bad != 0;
}
'''

def main():
    src = (HARNESS.replace('"FASTFP"', '"' + str(ROOT / "runtime" / "softfloat" / "fastfp.c") + '"'))
    with tempfile.TemporaryDirectory() as tmp:
        c = Path(tmp) / "check.c"
        exe = Path(tmp) / "check"
        c.write_text(src)
        build = subprocess.run(["gcc", "-O2", "-msse2", "-mfpmath=sse", "-o", str(exe), str(c)],
                               capture_output=True, text=True)
        if build.returncode:
            print(build.stderr)
            return 2
        run = subprocess.run([str(exe)], capture_output=True, text=True)
        print(run.stdout, end="")
        return run.returncode

if __name__ == "__main__":
    sys.exit(main())
