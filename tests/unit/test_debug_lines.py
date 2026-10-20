"""./dash --debug (compiler/debuglines.py): the C says the .dash line of each statement (#line), so
m68k-amigaos-gdb speaks in Dash lines.

    python3 -m unittest tests/unit/test_debug_lines.py      (tests/run_tests.py runs it too)
"""
import os
import shutil
import subprocess
import tempfile
import unittest

from compiler import debuglines

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GDB = "/opt/amiga/bin/m68k-amigaos-gdb"
PROGRAM = "func doble(n: Int) -> Int\n    r = n * 2\n    return r\nend\n\nMain\n    x = 20\n    y = doble(x)\n    Print y\nend\n"


class ApplyTest(unittest.TestCase):
    def test_marks_become_line_directives(self):
        code = ("int a;\n"
                + debuglines.mark(7, "/p/x.dash") + "    b = 1;\n    c = 2;\n"
                + debuglines.mark(8, "/p/x.dash") + "    d = 3;\n"
                + debuglines.NOLINE + "\n" + "int e;\n")
        out = debuglines.apply(code, "/b/x.c").split("\n")
        # one statement, one physical line (one entry in the line table: one breakpoint place, one step)
        self.assertEqual(out, ["int a;",
                               '#line 7 "/p/x.dash"', "b = 1; c = 2;",
                               '#line 8 "/p/x.dash"', "d = 3;",
                               '#line 7 "/b/x.c"', "int e;", ""])
        # after the noline the lines are the C file's own: "int e;" is line 7 of the output
        self.assertEqual(out.index("int e;") + 1, 7)

    def test_preprocessor_and_line_comments_stay_apart(self):
        code = (debuglines.mark(3, "/p/x.dash") + "    a();\n#if X\n    b();\n#endif\n    c(); // nota\n    d();\n"
                + debuglines.NOLINE + "\n")
        out = debuglines.apply(code, "/b/x.c").split("\n")
        self.assertEqual(out[:9], ['#line 3 "/p/x.dash"', "a();", "#if X", '#line 3 "/p/x.dash"', "b();", "#endif",
                                   '#line 3 "/p/x.dash"', "    c(); // nota", '#line 3 "/p/x.dash"'])

    def test_quotes_in_names(self):
        out = debuglines.apply(debuglines.mark(1, '/p/a"b.dash') + "x;\n", "/b/x.c")
        self.assertIn('#line 1 "/p/a\\"b.dash"', out)


class CompileTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="dash_dbg_")
        self.src = os.path.join(self.dir, "prog.dash")
        with open(self.src, "w") as f:
            f.write(PROGRAM)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_c_has_line_directives_only_with_debug(self):
        out = os.path.join(self.dir, "prog.c")
        env = dict(os.environ, DASH_DEBUG_LINES="1")
        subprocess.run(["python3", "-m", "compiler.main", self.src, "-o", out], cwd=ROOT, env=env, check=True,
                       capture_output=True)
        with open(out) as f:
            c = f.read()
        self.assertIn(f'#line 2 "{self.src}"', c)
        self.assertIn(f'#line 8 "{self.src}"', c)
        self.assertNotIn("/*@dash-", c)
        env.pop("DASH_DEBUG_LINES")
        subprocess.run(["python3", "-m", "compiler.main", self.src, "-o", out], cwd=ROOT, env=env, check=True,
                       capture_output=True)
        with open(out) as f:
            self.assertNotIn("#line", f.read())

    @unittest.skipUnless(os.path.exists(GDB) and os.path.exists("/opt/amiga/bin/m68k-amigaos-gcc"), "no toolchain")
    def test_gdb_reads_dash_lines(self):
        exe = os.path.join(self.dir, "prog")
        subprocess.run([os.path.join(ROOT, "dash"), "--debug", self.src, "-o", exe], cwd=ROOT, check=True,
                       capture_output=True)
        run = subprocess.run([GDB, "-batch", "-ex", "info line doble", "-ex", "info line prog.dash:8",
                              "-ex", "info scope doble", exe], capture_output=True, text=True, timeout=120)
        self.assertIn(f'Line 1 of "{self.src}"', run.stdout)
        self.assertIn(f'Line 8 of "{self.src}"', run.stdout)
        self.assertIn("Symbol n ", run.stdout)
        self.assertIn("Symbol r ", run.stdout)


if __name__ == "__main__":
    unittest.main()
