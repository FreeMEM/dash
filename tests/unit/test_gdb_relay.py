"""tools/gdb_relay.py and the linking of ./dash --debug: gdb finds the program's globals where they are.

    python3 -m unittest tests/unit/test_gdb_relay.py      (tests/run_tests.py runs it too)
"""
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import gdb_relay  # noqa: E402

GDB = "/opt/amiga/bin/m68k-amigaos-gdb"
NM = "/opt/amiga/bin/m68k-amigaos-nm"
PROGRAM = "var cuenta: Int = 0\nvar nombre: String = \"x\"\n\nfunc sube()\n    cuenta = cuenta + 7\nend\n\nMain\n    sube()\n    Print cuenta\nend\n"


def packet(body):
    return b"$" + body + b"#" + gdb_relay._checksum(body).encode()


class OffsetsTest(unittest.TestCase):
    def test_data_and_bss_go_back_by_the_hunks_before(self):
        out = gdb_relay.fix_offsets(packet(b"Text=00200000;Data=00300000;Bss=00400000"), [0x954, 0x58, 0x44])
        self.assertEqual(out, packet(b"Text=00200000;Data=002ff6ac;Bss=003ff654"))

    def test_two_hunks_bss_is_data(self):
        # ./dash --debug: .bss inside .data; bgdbserver repeats Data as Bss
        out = gdb_relay.fix_offsets(packet(b"Text=00200000;Data=00300000;Bss=00300000"), [0x954, 0x9c])
        self.assertEqual(out, packet(b"Text=00200000;Data=002ff6ac;Bss=002ff6ac"))

    def test_other_packets_as_they_are(self):
        for p in (packet(b"OK"), packet(b"T05"), b"+"):
            self.assertEqual(gdb_relay.fix_offsets(p, [4, 4]), p)

    def test_answer_cut_in_pieces(self):
        a, b = socket.socketpair()
        c, d = socket.socketpair()
        threading.Thread(target=gdb_relay._pipe, args=(b, c, [0x10, 0x10]), daemon=True).start()
        for piece in (b"+$OK#9a+$Text=0000", b"1000;Data=00002000;Bss=0000200", b"0#", b"00"):
            a.sendall(piece)
        a.close()
        got = b""
        while True:
            chunk = d.recv(1000)
            if not chunk:
                break
            got += chunk
        self.assertEqual(got, b"+$OK#9a+" + packet(b"Text=00001000;Data=00001ff0;Bss=00001ff0"))


@unittest.skipUnless(os.path.exists(GDB) and os.path.exists("/opt/amiga/bin/m68k-amigaos-gcc"), "no toolchain")
class DebugLinkTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="dash_relay_")
        self.src = os.path.join(self.dir, "prog.dash")
        with open(self.src, "w") as f:
            f.write(PROGRAM)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_globals_in_one_hunk_at_their_dwarf_place(self):
        exe = os.path.join(self.dir, "prog")
        subprocess.run([os.path.join(ROOT, "dash"), "--debug", self.src, "-o", exe], cwd=ROOT, check=True,
                       capture_output=True)
        sizes = gdb_relay.hunk_sizes(exe)
        self.assertEqual(len(sizes), 2)                       # code, and data with the bss in it
        dwarf = subprocess.run([GDB, "-batch", "-ex", "info address cuenta", exe],
                               capture_output=True, text=True, timeout=120).stdout
        at = int(re.search(r"at address (0x[0-9a-f]+)", dwarf).group(1), 16)
        nm = subprocess.run([NM, exe], capture_output=True, text=True).stdout
        offset = int(re.search(r"^([0-9a-f]+) [DdBb] _cuenta$", nm, re.M).group(1), 16)
        # in the hunk of data at offset; for gdb, at that offset after the code: Data - size(code) is right
        self.assertEqual(at, sizes[0] + offset)


if __name__ == "__main__":
    unittest.main()
