"""The inline assembler gives the same bytes by both paths: ./dash (dashc/src/asm68k.c) and ./dash --gcc
(compiler/asm68k.py and binutils' as). One block with the FPU, the rest of the 68020 and some 68000, built both
ways; the bytes between two markers must be equal. Needs dashc and the Amiga gcc (skipped without them)."""
import os
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GCC = "/opt/amiga/bin/m68k-amigaos-gcc"

LINES = """\
fmove.x fp0,fp1
fmove.l d0,fp2
fmove.s d1,fp3
fmove.w (a0),fp0
fmove.d (a0)+,fp1
fmove.l #3,fp0
fmove.s #1.5,fp0
fmove.d #-2.25,fp1
fmove.x #0.5,fp2
fmove.l fp0,d0
fmove.d fp2,-(sp)
fmove.l d0,fpcr
fmove.l fpsr,d1
fmovem.x fp2-fp7,-(sp)
fmovem.x (sp)+,fp2-fp7
fmovem.l fpcr/fpsr,-(sp)
fmovem.l (sp)+,fpcr/fpsr
fadd.x fp0,fp1
fsub.s (a0),fp2
fmul.d 8(a0),fp3
fdiv.w #3,fp0
fsqrt.x fp0
fsin.x fp0
fcos.x fp1,fp2
fsincos.x fp0,fp1:fp2
fintrz.x fp0,fp1
fcmp.l #10,fp0
ftst.x fp0
fmovecr.x #$32,fp0
fnop
fsave -(sp)
frestore (sp)+
fseq d0
ftrapne.w #5
.a:
fbeq .a
fblt.l .a
fdbne d0,.a
move.l ([4,a0],8),d0
move.l ([16,a0,d0.w*2],-4),d1
move.l ([100000,a1],d2.w,70000),d3
cas.l d0,d1,(a0)
cas2.w d4:d5,d6:d7,(d0):(a2)
cmp2.w 4(a1),a2
chk2.b (a0),d1
pack -(a0),-(a1),#0
unpk d2,d3,#$3030
trapgt.l #70000
bkpt #3
movec a0,vbr
move.w (a0)+,-(a1)
movem.l d2-d7/a2-a6,-(sp)
btst #6,$bfe001
divsl.l d1,d2:d0
bfextu d0{4:8},d1""".splitlines()


def build(gcc: bool, d: str) -> bytes:
    src = os.path.join(d, "p.dash")
    body = "\n".join(("    " + l) if l.endswith(":") else ("        " + l) for l in LINES)
    with open(src, "w") as f:
        f.write("Main\n    asm uses d0-d7/a0-a4/a6\n        bra.w .fin\n        dc.l $DEADBEEF\n" + body +
                "\n        dc.l $CAFEBABE\n    .fin:\n    end\nend\n")
    out = os.path.join(d, "g" if gcc else "d")
    r = subprocess.run([os.path.join(ROOT, "dash"), *(["--gcc"] if gcc else []), "--fpu", src, "-o", out],
                       capture_output=True, text=True, cwd=d)
    if r.returncode:
        raise AssertionError(r.stdout + r.stderr)
    with open(out, "rb") as f:
        data = f.read()
    a = data.index(b"\xde\xad\xbe\xef") + 4
    return data[a:data.index(b"\xca\xfe\xba\xbe", a)]


@unittest.skipUnless(os.path.exists(GCC) and os.path.exists(os.path.join(ROOT, "dashc", "dashc")),
                     "sin el gcc de Amiga o sin dashc")
class SameBytes(unittest.TestCase):
    def test_both_paths(self):
        with tempfile.TemporaryDirectory() as d:
            direct, viac = build(False, d), build(True, d)
        self.assertEqual(direct.hex(), viac.hex())


if __name__ == "__main__":
    unittest.main()
