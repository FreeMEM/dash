"""./dash --debug: a function nobody calls is generated (for its errors) and thrown away; its debug entries went with
it. They stayed, pointing at code that was not there (labels at -1 or into other code), and Forja's debugger wrote
its NOP over another function when stepping (Forja's tests/depurar.sh, error #80000004)."""
import os
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DASH = os.path.join(ROOT, "dash")
DASHC = os.path.join(ROOT, "dashc", "dashc")

PROGRAM = '''func sin_usar(a: Int) -> Int
    b = a * 2
    return b + 1
end

func usada(a: Int) -> Int
    return a + 1
end

Main
    x = usada(3)
    Print "x #{x}"
end
'''


@unittest.skipUnless(os.path.exists(DASHC), "make -C dashc")
class DebugSinUsar(unittest.TestCase):
    def test_sin_entradas_de_lo_tirado(self):
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "p.dash")
            exe = os.path.join(d, "p")
            with open(src, "w") as f:
                f.write(PROGRAM)
            r = subprocess.run([DASH, "--debug", src, "-o", exe], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            info = subprocess.run([DASHC, "--debug-info", exe], capture_output=True, text=True).stdout
            funcs = [l.split()[2] for l in info.splitlines() if l.startswith("P ")]
            self.assertIn("usada", funcs)
            self.assertNotIn("sin_usar", funcs)
            for l in info.splitlines():
                if l.startswith(("P ", "L ")):
                    self.assertNotIn(" -1 ", " " + l + " ", l)


if __name__ == "__main__":
    unittest.main()
