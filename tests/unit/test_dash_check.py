"""./dash --check (Forja marks the errors on saving): the errors of a program as compiling gives them, without making the
executable and without -o; by both paths (./dash and ./dash --gcc, this one without gcc)."""
import os
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DASH = os.path.join(ROOT, "dash")
DASHC = os.path.join(ROOT, "dashc", "dashc")

GOOD = "Main\n    x = 2\n    Print x * 3\nend\n"
BAD = "Main\n    x = 2\n    Print z\nend\n"


@unittest.skipUnless(os.path.exists(DASHC), "dashc not built (make -C dashc)")
class TestDashCheck(unittest.TestCase):
    def check(self, source, *opts):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "prog.dash")
            with open(src, "w") as f:
                f.write(source)
            r = subprocess.run([sys.executable, DASH, "--check", *opts, src], capture_output=True, text=True,
                               cwd=tmp)
            self.assertEqual(sorted(os.listdir(tmp)), ["prog.dash"])   # nothing written next to it
            return r, src

    def test_good_program(self):
        for opts in ((), ("--gcc",)):
            r, _ = self.check(GOOD, *opts)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertEqual(r.stdout + r.stderr, "")

    def test_error_with_its_place(self):
        for opts in ((), ("--gcc",)):
            r, src = self.check(BAD, *opts)
            self.assertNotEqual(r.returncode, 0)
            self.assertRegex(r.stdout + r.stderr, re.escape(src) + r":3:11: Error: .*\bz\b")

    def test_same_message_as_compiling(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "prog.dash")
            with open(src, "w") as f:
                f.write(BAD)
            build = subprocess.run([sys.executable, DASH, src, "-o", os.path.join(tmp, "prog")],
                                   capture_output=True, text=True)
        r, _ = self.check(BAD)
        line = [l for l in build.stderr.splitlines() if ": Error: " in l][0]
        self.assertIn(line.split("prog.dash", 1)[1], r.stderr)


MANY = """func a()
    Print zz
end

func b() -> Int
    x = 1 + qq
    Print x
    return x * 2
end

Main
    a()
    Print b()
    s = "a"
    s = 5
    Print ww
end
"""


def run(*args, cwd=None):
    r = subprocess.run([sys.executable, DASH, *args], capture_output=True, text=True, cwd=cwd)
    return r, r.stdout + r.stderr


def error_lines(out):
    """(line, column) of each error, in the order they come"""
    return [(int(m.group(1)), int(m.group(2))) for m in re.finditer(r"\.dash:(\d+):(\d+): Error: ", out)]


@unittest.skipUnless(os.path.exists(DASHC), "dashc not built (make -C dashc)")
class TestDashCheckAll(unittest.TestCase):
    """--check gives every error it can, not only the first one (Forja marks them all), in order, each once, at most
    20, and without the ones that come from another (a variable whose assignment failed)"""

    def write(self, tmp, name, text):
        path = os.path.join(tmp, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(text)
        return path

    def test_every_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = self.write(tmp, "prog.dash", MANY)
            for opts in ((), ("--gcc",)):
                r, out = run("--check", *opts, src)
                self.assertNotEqual(r.returncode, 0)
                # zz, qq (not x after it: it comes from qq), s = 5, ww
                self.assertEqual(error_lines(out), [(2, 11), (6, 13), (15, 5), (16, 11)], out)

    def test_at_most_20(self):
        text = "Main\n" + "".join(f"    Print v{i}\n" for i in range(30)) + "end\n"
        with tempfile.TemporaryDirectory() as tmp:
            src = self.write(tmp, "prog.dash", text)
            for opts in ((), ("--gcc",)):
                r, out = run("--check", *opts, src)
                self.assertEqual(error_lines(out), [(i + 2, 11) for i in range(20)], out)
                self.assertIn("dash: Error: demasiados errores (20): no se miran más", out)

    def test_module_without_main(self):
        with tempfile.TemporaryDirectory() as tmp:
            good = self.write(tmp, "lib/m.dash", "func doble(x: Int) -> Int\n    return x * 2\nend\n")
            bad = self.write(tmp, "lib/mal.dash", "func doble(x: Int) -> Int\n    return x * falta\nend\n")
            for opts in ((), ("--gcc",)):
                r, out = run("--check", *opts, good)
                self.assertEqual(r.returncode, 0, out)
                self.assertNotIn("Error", out)
                r, out = run("--check", *opts, bad)
                self.assertNotEqual(r.returncode, 0)
                self.assertRegex(out, r"mal\.dash:2:16: Error: .*\bfalta\b")
            # without --check, a program still needs its Main
            r, out = run(good, "-o", os.path.join(tmp, "m"))
            self.assertNotEqual(r.returncode, 0)

    def test_unsaved_module_text(self):
        """--texto lib/m.dash=copia: the module's text comes from the copy (what the editor has not saved), and the
        errors name the module, also from another folder"""
        with tempfile.TemporaryDirectory() as tmp:
            self.write(tmp, "proj/main.dash", 'import "lib/m.dash"\n\nMain\n    Print doble(4)\nend\n')
            self.write(tmp, "proj/lib/m.dash", "func doble(x: Int) -> Int\n    return x * 2\nend\n")
            copy = self.write(tmp, "copia.txt", "func doble(x: Int) -> Int\n    y = x * 2\n    return y + falta\nend\n")
            proj = os.path.join(tmp, "proj")
            for opts in ((), ("--gcc",)):
                r, out = run("--check", *opts, "main.dash", cwd=proj)
                self.assertEqual(r.returncode, 0, out)
                for cwd, main, mod in ((proj, "main.dash", "lib/m.dash"),
                                       (os.path.join(proj, "lib"), "../main.dash", "m.dash")):
                    r, out = run("--check", *opts, main, "--texto", f"{mod}={copy}", cwd=cwd)
                    self.assertNotEqual(r.returncode, 0)
                    self.assertRegex(out, r"lib/m\.dash:3:16: Error: .*\bfalta\b")
                    self.assertNotIn("copia", out)
                # the module alone, with its unsaved text
                r, out = run("--check", *opts, "lib/m.dash", "--texto", f"lib/m.dash={copy}", cwd=proj)
                self.assertRegex(out, r"lib/m\.dash:3:16: Error: .*\bfalta\b")
            # the files are as they were
            with open(os.path.join(proj, "lib/m.dash")) as f:
                self.assertNotIn("falta", f.read())


if __name__ == "__main__":
    unittest.main()
