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


@unittest.skipUnless(os.path.exists("/opt/amiga/bin/m68k-amigaos-gcc"), "needs the Amiga toolchain")
class AtTheSameTime(unittest.TestCase):
    """a/main.dash and b/main.dash compiled at once share build/main.c and .elf: three of eight failed and one
    program got the other's code (v13). Now they take turns."""

    def test_same_name_at_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            jobs = []
            for d in "ab":
                os.makedirs(os.path.join(tmp, d))
                with open(os.path.join(tmp, d, "main.dash"), "w") as f:
                    f.write(f'Main\n    Print "soy {d}"\nend\n')
            for i in range(3):
                for d in "ab":
                    exe = os.path.join(tmp, d, "bin", f"main{i}")
                    jobs.append((d, exe, subprocess.Popen(
                        [sys.executable, os.path.join(ROOT, "dash"), "-q", os.path.join(tmp, d, "main.dash"), "-o", exe],
                        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)))
            for d, exe, job in jobs:
                out = job.communicate(timeout=600)[0].decode()
                self.assertEqual(job.returncode, 0, out)
                with open(exe, "rb") as f:
                    self.assertIn(f"soy {d}".encode(), f.read())


class OddText(unittest.TestCase):
    """Sources with a BOM (Windows editors) or in Latin-1 (an editor on the Amiga): they failed with
    "carácter inesperado '\\ufeff'" or a UnicodeDecodeError (v10)."""

    def transpile(self, data, imported=None):
        sys.path.insert(0, ROOT)
        from compiler.main import DashCompiler, read_source
        with tempfile.TemporaryDirectory() as tmp:
            if imported:
                with open(os.path.join(tmp, "modulo.dash"), "wb") as f:
                    f.write(imported)
            path = os.path.join(tmp, "p.dash")
            with open(path, "wb") as f:
                f.write(data)
            c_code, _ = DashCompiler().compile(read_source(path), path)
            return c_code

    def test_bom(self):
        self.assertIn("main", self.transpile(b"\xef\xbb\xbfMain\n    Print \"hola\"\nend\n"))
        c = self.transpile(b'import "modulo.dash"\nMain\n    Print "#{doble(2)}"\nend\n',
                           b"\xef\xbb\xbffunc doble(n: Int) -> Int\n    return n * 2\nend\n")
        self.assertIn("doble", c)

    def test_latin1(self):
        c = self.transpile(b'Main\n    Print "Ca\xf1a"\nend\n')
        self.assertIn("Ca\\361a", c)        # the text in Latin-1 for the Amiga, as from a UTF-8 file


class CpuFlags(unittest.TestCase):
    """./dash --cpu (docs/RECURSOS_LOOP.md R1): 68020 code (the toolchain's libnix is 68000 or 68020) tuned per CPU"""
    def test_flags(self):
        sys.path.insert(0, ROOT)
        from compiler.cflags import cpu_flags
        self.assertEqual(cpu_flags(), [])
        self.assertEqual(cpu_flags("68000"), [])
        self.assertEqual(cpu_flags(None, True), ["-m68020", "-m68881"])
        self.assertEqual(cpu_flags("68020"), ["-m68020"])
        self.assertEqual(cpu_flags("68060", True), ["-m68020", "-mtune=68060", "-m68881"])

    @unittest.skipUnless(os.path.exists("/opt/amiga/bin/m68k-amigaos-gcc"), "needs the Amiga toolchain")
    def test_68060_without_64_bit_multiply(self):
        """Fixed * and / on a 68060: no muls.l/divs.l with a 64-bit pair (68060.library would trap each one)"""
        sys.path.insert(0, ROOT)
        from compiler.main import DashCompiler
        c_code, _ = DashCompiler().compile("Main\n    a = Fixed(2.5)\n    b = Fixed(1.5)\n"
                                           "    Print a * b\n    Print a / b\nend\n", "p.dash")
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "p.c")
            with open(src, "w") as f:
                f.write(c_code)
            asm = {}
            for tune in ("68040", "68060"):
                r = subprocess.run(["/opt/amiga/bin/m68k-amigaos-gcc", "-m68020", f"-mtune={tune}", "-O2",
                                    "-I/opt/amiga/m68k-amigaos/ndk-include", "-S", src, "-o", "-"],
                                   capture_output=True, text=True, timeout=120)
                self.assertEqual(r.returncode, 0, r.stderr)
                asm[tune] = r.stdout
        import re
        pair = re.compile(r"\s(muls|mulu|divs|divu)\.l [^,\n]+,d[0-7]:d[0-7]")
        self.assertTrue(pair.search(asm["68040"]))      # the 68040 does use them
        self.assertIsNone(pair.search(asm["68060"]))


if __name__ == "__main__":
    unittest.main()


class Version(unittest.TestCase):
    def test_version_is_the_package_one(self):
        """./dash --version says the version of compiler/__init__.py (the one releases and the VS Code notice use)"""
        from compiler import __version__
        r = subprocess.run([sys.executable, os.path.join(ROOT, "dash"), "--version"],
                           cwd=ROOT, capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), f"Dash {__version__}")
        self.assertRegex(__version__, r"^\d+\.\d+\.\d+$")
