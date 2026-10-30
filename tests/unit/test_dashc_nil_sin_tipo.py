"""dashc: una variable nueva que nace con x = nil no dice qué guarda (lo que se le asignaba después se perdía, pieza 19
de Forja); da error, como ./dash, que pide var x: Tipo = nil. Con su tipo, o si ya existe, compila."""
import os
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DASHC = os.path.join(ROOT, "dashc", "dashc")
STRUCT = "struct Conv\n    n: Int = 0\nend\n\n"


@unittest.skipUnless(os.path.exists(DASHC), "falta dashc/dashc (make -C dashc)")
class TestNilSinTipo(unittest.TestCase):
    def build(self, src):
        with tempfile.TemporaryDirectory() as tmp:
            f = os.path.join(tmp, "p.dash")
            with open(f, "w") as fh:
                fh.write(src)
            return subprocess.run([DASHC, f, "-o", os.path.join(tmp, "p")], capture_output=True, text=True)

    def test_error(self):
        r = self.build(STRUCT + "Main\n    c = nil\n    c = Conv(5)\n    Print c.n\nend\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn("p.dash:6:5: Error: 'c = nil' no dice qué guarda c: decláralo con su tipo (var c: Tipo = nil)",
                      r.stderr)

    def test_with_type_or_existing(self):
        r = self.build(STRUCT + "var g: Conv = nil\n\nMain\n    var c: Conv = nil\n    c = nil\n    g = nil\n"
                       "    s = \"a\"\n    s = nil\n    Print \"bien\"\nend\n")
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
