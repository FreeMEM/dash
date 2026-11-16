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


if __name__ == "__main__":
    unittest.main()
