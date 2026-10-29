"""dashc --debug (el depurador, docs/DEPURADOR_LOOP.md): un NOP al principio de cada línea y el HUNK_DEBUG con
ficheros, globales, campos, funciones, variables y el sitio de cada línea; dashc --debug-info lo enseña."""
import os
import re
import struct
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DASHC = os.path.join(ROOT, "dashc", "dashc")

PROGRAM = """struct Punto
    x: Int = 0
    nombre: String = ""
    hijos: [Punto] = nil
end

var total: Int = 0
var nombres: {String: Int} = {}

func doble(n: Int) -> Int
    return n * 2
end

func suma(a: Int, b: Int) -> Int
    c = a + b
    return doble(c)
end

Main
    p = Punto(3, "a", nil)
    n = suma(p.x, 4)
    k = 5
    total = n + k
    Print "suma: #{n}"
end
"""


def code_hunk(exe):
    """The bytes of the first code hunk of an Amiga executable"""
    with open(exe, "rb") as f:
        d = f.read()
    first, last = struct.unpack(">II", d[12:20])
    at = 20 + 4 * (last - first + 1)
    assert struct.unpack(">I", d[at:at + 4])[0] & 0x3FFFFFFF == 0x3E9
    n = struct.unpack(">I", d[at + 4:at + 8])[0]
    return d[at + 8:at + 8 + 4 * n]


@unittest.skipUnless(os.path.exists(DASHC), "falta dashc/dashc (make -C dashc)")
class TestDebug(unittest.TestCase):
    def build(self, tmp, *flags):
        src = os.path.join(tmp, "p.dash")
        with open(src, "w") as f:
            f.write(PROGRAM)
        exe = os.path.join(tmp, "p" + "".join(flags).replace("-", ""))
        r = subprocess.run([DASHC, *flags, src, "-o", exe], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return exe

    def test_info(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = self.build(tmp, "--debug")
            r = subprocess.run([DASHC, "--debug-info", exe], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            t = r.stdout
            self.assertTrue(t.startswith("DASH-DEBUG 1\nF 0 "), t)
            self.assertIn("G total Int 0 0\n", t)
            self.assertIn("G nombres {String:Int} 4 0\n", t)
            self.assertIn("S Punto x Int 0\nS Punto nombre String 4\nS Punto hijos [Punto] 8\n", t)
            funcs = {m[1]: (int(m[0]), int(m[2]), int(m[3])) for m in re.findall(r"^P (\d+) (\S+) (\d+) (\d+) 0 \d+$", t, re.M)}
            # each function in its place (doble is not copied into suma)
            self.assertEqual(set(funcs), {"Main", "suma", "doble"})
            # its variables in the frame (on a5), parameters from 8(a5); k is not made a constant
            suma = funcs["suma"][0]
            self.assertIn(f"V {suma} a Int 8 14\n", t)
            self.assertIn(f"V {suma} b Int 12 14\n", t)
            self.assertIn(f"V {suma} c Int -4 15\n", t)
            self.assertIn(f"V {funcs['Main'][0]} k Int ", t)
            # a NOP at the place of every line, inside its function
            code = code_hunk(exe)
            lines = [(int(a), int(c)) for a, c in re.findall(r"^L (\d+) 0 (\d+)$", t, re.M)]
            self.assertEqual(sorted(c for _, c in lines), [11, 15, 16, 20, 21, 22, 23, 24])
            for off, line in lines:
                self.assertEqual(code[off:off + 2], b"\x4e\x71", line)
                self.assertTrue(any(s <= off < e for _, s, e in funcs.values()), line)

    def test_without_debug(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = self.build(tmp)
            r = subprocess.run([DASHC, "--debug-info", exe], capture_output=True, text=True)
            self.assertEqual(r.returncode, 1)
            self.assertIn("compílalo con --debug", r.stderr)


if __name__ == "__main__":
    unittest.main()
