"""./dash with odd paths (docs/IDE_VIDEO_LOOP.md v9): spaces, accents and ñ in folders and files, an import
from a folder like that, and -o into a folder that is not there yet (it ended in a traceback); -q leaves only the
result.

    python3 -m unittest tests/unit/test_dash_cli.py      (tests/run_tests.py runs it too)
"""
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@unittest.skipUnless(os.path.exists("/opt/amiga/bin/m68k-amigaos-gcc"), "needs the Amiga toolchain")
class OddPaths(unittest.TestCase):
    def test_spaces_accents_and_a_new_output_folder(self):
        with tempfile.TemporaryDirectory(prefix="dash ñ ") as tmp:
            folder = os.path.join(tmp, "Mi Juego Ñandú")
            os.makedirs(os.path.join(folder, "sub carpeta"))
            with open(os.path.join(folder, "sub carpeta", "útil ñ.dash"), "w") as f:
                f.write("func doble(n: Int) -> Int\n    return n * 2\nend\n")
            program = os.path.join(folder, "juego ñandú.dash")
            with open(program, "w") as f:
                f.write('import "sub carpeta/útil ñ.dash"\nMain\n    Print "Ñandú: #{doble(21)}"\nend\n')
            exe = os.path.join(folder, "bin", "juego ñandú")
            r = subprocess.run([sys.executable, os.path.join(ROOT, "dash"), "-q", program, "-o", exe],
                               cwd=ROOT, capture_output=True, text=True, timeout=300)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertTrue(os.path.exists(exe))
            self.assertNotIn("Transpiled", r.stdout)
            self.assertIn("Success!", r.stdout)


if __name__ == "__main__":
    unittest.main()
