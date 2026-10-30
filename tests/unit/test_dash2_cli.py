"""./dash of Dash 2.0: dashc (no C compiler), and what it leaves to ./dash1 (the Dash that compiles through C)."""
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

    def test_version_is_dashc(self):
        r = self.run_dash("--version")
        self.assertEqual(r.returncode, 0)
        self.assertIn("(dashc)", r.stdout)

    def test_compiles_a_hunk_executable(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = os.path.join(tmp, "hola")
            r = self.run_dash(os.path.join(ROOT, "examples", "hola.dash"), "-o", exe)
            self.assertEqual(r.returncode, 0, r.stderr)
            with open(exe, "rb") as f:
                self.assertEqual(f.read(4), b"\x00\x00\x03\xf3")   # HUNK_HEADER

    def test_c_in_the_program_points_to_dash1(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = self.run_dash(os.path.join(ROOT, "tests", "test_c_link.dash"), "-o", os.path.join(tmp, "x"))
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("./dash1", r.stderr)

    def test_options_of_dash1_point_to_it(self):
        r = self.run_dash("--small", os.path.join(ROOT, "examples", "hola.dash"), "-o", "/dev/null")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("./dash1 --small", r.stderr)

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


if __name__ == "__main__":
    unittest.main()
