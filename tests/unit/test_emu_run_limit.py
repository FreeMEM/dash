"""tools/emu_run.py time_limit: how long a run may last. A debug session (--gdbserver) without the window was
cut at 60 s, in the middle of it (the video tutorial, docs/IDE_VIDEO_LOOP.md v7).

    python3 -m unittest tests/unit/test_emu_run_limit.py      (tests/run_tests.py runs it too)
"""
import os
import sys
import unittest
from argparse import Namespace

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import emu_run  # noqa: E402


def limit(argv, window=False, gdbserver=None, timeout=60.0):
    return emu_run.time_limit(Namespace(window=window, gdbserver=gdbserver, timeout=timeout), ["emu_run.py"] + argv)


class TimeLimit(unittest.TestCase):
    def test_tests_and_programs_have_60_seconds(self):
        self.assertEqual(limit(["p"]), 60.0)

    def test_window_and_debugger_have_none(self):
        self.assertEqual(limit(["--window", "p"], window=True), 0)
        self.assertEqual(limit(["--gdbserver", "2345", "p"], gdbserver=2345), 0)

    def test_timeout_given_wins(self):
        self.assertEqual(limit(["--gdbserver", "2345", "--timeout", "30", "p"], gdbserver=2345, timeout=30.0), 30.0)
        self.assertEqual(limit(["--window", "--timeout=5", "p"], window=True, timeout=5.0), 5.0)


if __name__ == "__main__":
    unittest.main()
