"""./dash of Dash 2.0: its own compiler (no C compiler), and --gcc, the path through C with gcc (also by itself for a
program with C or an option only that path has)."""
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DASH = os.path.join(ROOT, "dash")
DASHC = os.path.join(ROOT, "dashc", "dashc")


@unittest.skipUnless(os.path.exists(DASHC), "dashc not built (make -C dashc)")
class TestDash2Cli(unittest.TestCase):
    def run_dash(self, *args):
        return subprocess.run([sys.executable, DASH, *args], capture_output=True, text=True, cwd=ROOT)

    def test_version(self):
        r = self.run_dash("--version")
        self.assertEqual(r.returncode, 0)
        self.assertRegex(r.stdout, r"^Dash 2\.\d+\.\d+\n$")

    def test_compiles_a_hunk_executable(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = os.path.join(tmp, "hola")
            r = self.run_dash(os.path.join(ROOT, "examples", "hola.dash"), "-o", exe)
            self.assertEqual(r.returncode, 0, r.stderr)
            with open(exe, "rb") as f:
                self.assertEqual(f.read(4), b"\x00\x00\x03\xf3")   # HUNK_HEADER

    def test_c_in_the_program_goes_through_gcc(self):
        """a program with C: through C with gcc by itself, and it says so in a line"""
        with tempfile.TemporaryDirectory() as tmp:
            exe = os.path.join(tmp, "x")
            r = self.run_dash("-q", os.path.join(ROOT, "tests", "test_args_wb.dash"), "-o", exe)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("el programa lleva C: se compila por C con gcc", r.stderr)
            with open(exe, "rb") as f:
                self.assertEqual(f.read(4), b"\x00\x00\x03\xf3")

    def test_gcc_option(self):
        """--gcc: through C with gcc, without a line (it was asked for)"""
        with tempfile.TemporaryDirectory() as tmp:
            exe = os.path.join(tmp, "x")
            r = self.run_dash("--gcc", "-q", os.path.join(ROOT, "examples", "hola.dash"), "-o", exe)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertNotIn("se compila por C", r.stderr)
            self.assertTrue(os.path.exists(os.path.join(ROOT, "build", "hola.c")) or os.path.getsize(exe) > 0)

    def test_options_of_the_c_path_go_there(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = self.run_dash("--small", "-q", os.path.join(ROOT, "examples", "hola.dash"), "-o", os.path.join(tmp, "x"))
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("--small: se compila por C con gcc", r.stderr)

    def test_messages_do_not_name_the_parts(self):
        """the user sees one dash: no "dashc" or "dash1" in what ./dash says"""
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "mal.dash")
            with open(src, "w") as f:
                f.write("Main\n    x = \n")
            r = self.run_dash(src, "-o", os.path.join(tmp, "x"))
            self.assertNotEqual(r.returncode, 0)
            for out in (r.stdout + r.stderr, self.run_dash("--help").stdout):
                self.assertNotIn("dashc", out)
                self.assertNotIn("dash1", out)

    def test_fpu_and_cpu_as_in_dash1(self):
        # (como Tachyon, tools/paquete.sh: ./dash --fpu)
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "x")
            r = self.run_dash("--fpu", "--cpu", "68040", os.path.join(ROOT, "examples", "hola.dash"), "-o", out)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue(os.path.getsize(out) > 0)

    def test_test_mode_as_in_dash1(self):
        # DASH_TEST_AUTOCLOSE (the program ends by itself: tools/emu_run.py) and DASH_PRINT_FLUSH (the VS Code
        # extension) while compiling: each adds code (a call in each while, a Flush after each Print)
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "x.dash")
            with open(src, "w") as f:
                f.write('Main\n    n = 0\n    while n < 3\n        n = n + 1\n        Print "#{n}"\n    end\nend\n')
            sizes = {}
            for name, extra in (("plain", {}), ("autoclose", {"DASH_TEST_AUTOCLOSE": "5"}),
                                ("flush", {"DASH_PRINT_FLUSH": "1"})):
                env = {k: v for k, v in os.environ.items() if k not in ("DASH_TEST_AUTOCLOSE", "DASH_PRINT_FLUSH")}
                env.update(extra)
                out = os.path.join(tmp, name)
                r = subprocess.run([DASHC, src, "-o", out], capture_output=True, text=True, env=env)
                self.assertEqual(r.returncode, 0, r.stderr)
                sizes[name] = os.path.getsize(out)
            self.assertGreater(sizes["autoclose"], sizes["plain"])
            self.assertGreater(sizes["flush"], sizes["plain"])

    def test_emu_run_dash2(self):
        # tools/emu_run.py --dash2 (the VS Code extension's "run"): ./dash, also for a program with C (through C)
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import emu_run
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            plain = os.path.join(tmp, "a.dash")
            with open(plain, "w") as f:
                f.write('Main\n    Print "hola"\nend\n')
            with_c = os.path.join(tmp, "c.dash")
            with open(with_c, "w") as f:
                f.write('@native func doble(x: Int) -> Int\n"""\n    return x * 2;\n"""\nend\n\nMain\n    Print doble(2)\nend\n')
            old = emu_run.DASH2
            emu_run.DASH2 = True
            try:
                emu_run.compile_dash(Path(plain), Path(tmp, "a"), False)
                emu_run.compile_dash(Path(with_c), Path(tmp, "c"), False)
            finally:
                emu_run.DASH2 = old
            r = self.run_dash(plain, "-o", os.path.join(tmp, "a_dashc"))
            self.assertEqual(r.returncode, 0, r.stderr)
            with open(os.path.join(tmp, "a"), "rb") as f1, open(os.path.join(tmp, "a_dashc"), "rb") as f2:
                self.assertEqual(f1.read(), f2.read())
            self.assertTrue(os.path.getsize(os.path.join(tmp, "c")) > 0)


if __name__ == "__main__":
    unittest.main()
