"""El rodeo del JIT de Emu68 1.1.0-beta.1 (lo contaron David Martínez y BordanBordan): tras cada muls.l/mulu.l de
32 bits, un move.l del registro en sí mismo, porque Emu68 deja el producto de 64 bits en el registro de ARM y su
lsr.l Dn,Dm desplazaba esos 64 bits ((a * b) >> n salía mal; Tachyon se colgaba creando el contexto de QuickJS).
Por C, el as de compiler/emu68 (gcc -B, solo con 68020 o más); directo, dashc (dashc/src/t68k_arith.c). El asm en
línea (#APP) y el 68000 quedan igual. El caso mínimo que falla en Emu68 de verdad está en el docstring de
compiler/emu68/as y en docs/VERSIONES.md; Emu68 no corre en FS-UAE, así que aquí se mira el código."""
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AS = os.path.join(ROOT, "compiler", "emu68", "as")
GCC = "/opt/amiga/bin/m68k-amigaos-gcc"
OBJDUMP = "/opt/amiga/bin/m68k-amigaos-objdump"
DASHC = os.path.join(ROOT, "dashc", "dashc")
sys.path.insert(0, ROOT)
from compiler.cflags import cpu_flags, opt_flags  # noqa: E402

C = "unsigned f(unsigned a, unsigned b, int n) { return (a * b) >> n; }\n" \
    "long long g(int a, int b) { return (long long)a * b; }\n"


def filtro(texto):
    return subprocess.run([sys.executable, AS, "--filtro"], input=texto, capture_output=True, text=True,
                          check=True).stdout


class Filtro(unittest.TestCase):
    def test_tras_cada_mul_de_32_bits(self):
        r = filtro("\tmuls.l d1,d0\n\tmulu.l #5,d4\nx:\tmulsl %d1,%d7 | c\n")
        self.assertEqual(r, "\tmuls.l d1,d0\n\tmove.l d0,d0\n\tmulu.l #5,d4\n\tmove.l d4,d4\n"
                            "x:\tmulsl %d1,%d7 | c\n\tmove.l %d7,%d7\n")

    def test_la_de_64_bits_y_el_asm_en_linea_igual(self):
        t = "\tmuls.l d1,d2:d3\n#APP\n\tmuls.l d2,d3\n#NO_APP\n\tmuls.w d1,d0\n"
        self.assertEqual(filtro(t), t)


@unittest.skipUnless(os.path.exists(GCC), "sin el gcc del Amiga")
class PorC(unittest.TestCase):
    def codigo(self, flags):
        with tempfile.TemporaryDirectory() as d:
            c = os.path.join(d, "m.c")
            o = os.path.join(d, "m.o")
            with open(c, "w") as f:
                f.write(C)
            subprocess.run([GCC, "-noixemul", *opt_flags(), *flags, "-c", c, "-o", o], check=True)
            return subprocess.run([OBJDUMP, "-d", "-m68020", o], capture_output=True, text=True).stdout

    def test_68020(self):
        d = self.codigo(cpu_flags(None, True))
        lineas = [l.split("\t")[-1].strip() for l in d.splitlines() if "\t" in l]
        i = next(k for k, l in enumerate(lineas) if l.startswith("mulsl") and ":" not in l and "," in l
                 and l.count(",") == 1)
        r = lineas[i].split(",")[-1]
        self.assertEqual(lineas[i + 1], f"movel {r},{r}")
        self.assertIn("lsrl", d)

    def test_68000_sin_as_propio(self):
        self.assertEqual([f for f in cpu_flags(None, False) if f.startswith("-B")], [])


@unittest.skipUnless(os.path.exists(DASHC), "sin dashc")
class Directo(unittest.TestCase):
    def hunk(self, *opciones):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "m.dash")
            o = os.path.join(d, "m")
            with open(p, "w") as f:
                f.write("Main\n    a = arg_count() + 3\n    b = a * a\n    c = a * 1234567\n    Print b + c * a\nend\n")
            subprocess.run([os.path.join(ROOT, "dash"), p, "-o", o, *opciones], check=True, capture_output=True)
            return open(o, "rb").read()

    def test_68020(self):
        h = self.hunk("--fpu")
        self.assertIn(b"\x4c\x00\x08\x00\x20\x00", h)          # muls.l d0,d0; move.l d0,d0
        self.assertIn(b"\x4c\x3c\x08\x00\x00\x12\xd6\x87\x20\x00", h)   # muls.l #1234567,d0; move.l d0,d0

    def test_68000(self):
        self.assertNotIn(b"\x4c\x3c\x08\x00", self.hunk())


if __name__ == "__main__":
    unittest.main()
