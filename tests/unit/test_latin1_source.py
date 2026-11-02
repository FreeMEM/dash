"""Fuentes en Latin-1 (pieza 27 de Forja: en el Amiga los ficheros son Latin-1): un .dash o un .dashui que no es
UTF-8 válido se lee como Latin-1, cada byte su carácter, en dashc y en ./dash; los de UTF-8 (con su marca o sin ella)
siguen como antes. Los textos llegan al programa en Latin-1."""
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DASHC = os.path.join(ROOT, "dashc", "dashc")

LATIN1 = b'Main\n    Print "\xa1Hola, mundo! \xf1"\nend\n'
UTF8 = b'Main\n    Print "\xc2\xa1Hola, mundo! \xc3\xb1"\nend\n'
BOM = b'\xef\xbb\xbf' + UTF8
EXPECTED = b"\xa1Hola, mundo! \xf1\x00"

DASHUI = (b'{"dashui": 1, "windows": [{"name": "V", "title": "Ma\xf1ana", "root": {"type": "vgroup", "children": '
          b'[{"type": "text", "name": "t", "text": "\xa1Hola \\u00e9"}]}}]}\n')
UI_MAIN = b'import "v.dashui"\nMain\n    if mui_app_begin("A", "AA") != 0\n        v = V_create()\n        mui_app_end()\n    end\nend\n'


def write(tmp, name, data):
    path = os.path.join(tmp, name)
    with open(path, "wb") as f:
        f.write(data)
    return path


@unittest.skipUnless(os.path.exists(DASHC), "falta dashc/dashc (make -C dashc)")
class TestDashc(unittest.TestCase):
    def build(self, tmp, src):
        exe = src[:-5]
        r = subprocess.run([DASHC, src, "-o", exe], capture_output=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(exe, "rb") as f:
            return f.read()

    def test_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name, data in (("latin1", LATIN1), ("utf8", UTF8), ("bom", BOM)):
                self.assertIn(EXPECTED, self.build(tmp, write(tmp, name + ".dash", data)), name)

    def test_dashui(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "v.dashui", DASHUI)
            exe = self.build(tmp, write(tmp, "ui.dash", UI_MAIN))
            self.assertIn(b"\x00Ma\xf1ana\x00", exe)
            self.assertIn(b"\x00\xa1Hola \xe9\x00", exe)   # (the \u00e9 too, not its UTF-8)


class TestDash1(unittest.TestCase):
    def c_of(self, tmp, src):
        out = src[:-5] + ".c"
        r = subprocess.run([sys.executable, "-m", "compiler.main", src, "-o", out], capture_output=True, cwd=ROOT)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(out, "rb") as f:
            return f.read()

    def test_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name, data in (("latin1", LATIN1), ("utf8", UTF8), ("bom", BOM)):
                self.assertIn(b'\\241Hola, mundo! \\361', self.c_of(tmp, write(tmp, name + ".dash", data)), name)

    def test_dashui(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "v.dashui", DASHUI)
            c = self.c_of(tmp, write(tmp, "ui.dash", UI_MAIN))
            self.assertIn(b'"Ma\\361ana"', c)
            self.assertIn(b'"\\241Hola \\351"', c)


if __name__ == "__main__":
    unittest.main()
