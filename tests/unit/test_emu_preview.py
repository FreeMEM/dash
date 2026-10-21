"""tools/emu_run.py planar_to_png: the planes of a planar screen (tools/amiga/shot.c FILE.dsh) as a PNG, for
tools/emu_preview.py (the Amiga that stays on for "Ver en Amiga").

    python3 -m unittest tests/unit/test_emu_preview.py      (tests/run_tests.py runs it too)
"""
import os
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import emu_run  # noqa: E402


def png_rows(png: Path, width: int):
    data = png.read_bytes()
    idat = b""
    i = 8
    while i < len(data):
        n = int.from_bytes(data[i:i + 4], "big")
        if data[i + 4:i + 8] == b"IDAT":
            idat += data[i + 8:i + 8 + n]
        i += 12 + n
    raw = zlib.decompress(idat)
    stride = 1 + width * 3
    return [raw[y * stride + 1:(y + 1) * stride] for y in range(len(raw) // stride)]


class PlanarTest(unittest.TestCase):
    def test_planes_to_colours(self):
        # 10 x 2 pixels, 2 planes (4 colours), 2 bytes a row: row 0 has colour 1 at x 0, 2 at x 1, 3 at x 9
        pal = bytes([0, 0, 0, 255, 0, 0, 0, 255, 0, 0, 0, 255])
        row0 = bytes([0b10000000, 0b01000000]) + bytes([0b01000000, 0b01000000])   # plane 0, plane 1
        row1 = bytes([0, 0, 0, 0])
        with tempfile.TemporaryDirectory() as d:
            dsh = Path(d) / "s.dsh"
            dsh.write_bytes(b"DSH1 10 2 2 2\n" + pal + row0 + row1)
            self.assertTrue(emu_run.planar_complete(dsh))
            dsh2 = Path(d) / "half.dsh"
            dsh2.write_bytes(b"DSH1 10 2 2 2\n" + pal + row0)
            self.assertFalse(emu_run.planar_complete(dsh2))
            png = Path(d) / "s.png"
            emu_run.planar_to_png(dsh, png)
            rows = png_rows(png, 10)
        px = lambda y, x: tuple(rows[y][3 * x:3 * x + 3])   # noqa: E731
        self.assertEqual(px(0, 0), (255, 0, 0))
        self.assertEqual(px(0, 1), (0, 255, 0))
        self.assertEqual(px(0, 9), (0, 0, 255))
        self.assertEqual(px(0, 2), (0, 0, 0))
        self.assertEqual(px(1, 0), (0, 0, 0))


if __name__ == "__main__":
    unittest.main()
