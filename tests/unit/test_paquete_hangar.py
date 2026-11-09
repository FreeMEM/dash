"""tools/paquete_hangar.py: de un cajón con su paquete.txt, el .lha y el .readme para Aminet y Hangar."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import paquete_hangar as ph  # noqa: E402

PAQUETE = """Short:        Un programa de prueba
Author:       Ana García
Type:         util/misc
Version:      1.2
Requires:     OS 3.1, MUI 3.8
Provides:     prueba.library 1
Install:      drawer Prueba
Run:          Prueba/Prueba

Hace cosas de prueba.
Y más cosas.
"""


class PaqueteHangar(unittest.TestCase):
    def test_readme_y_comprobaciones(self):
        campos, desc = ph.leer_paquete(PAQUETE)
        self.assertEqual(ph.comprobar(campos), [])
        r = ph.readme(campos, desc)
        self.assertTrue(r.startswith("Short:        Un programa de prueba\nAuthor:       Ana García\n"), r)
        self.assertIn("Architecture: m68k-amigaos\nRequires:     OS 3.1, MUI 3.8\nProvides:     prueba.library 1\n", r)
        self.assertIn("Distribution: Aminet\n\nHace cosas de prueba.\nY más cosas.\n", r)
        malos, _ = ph.leer_paquete("Short: " + "x" * 41 + "\nType: cosas\nInstall: en LIBS:\nProvides: algo\nColor: rojo\n")
        f = ph.comprobar(malos)
        for trozo in ["falta Author", "falta Version", "41 letras", "categoría de Aminet", "Install va como",
                      "Provides 'algo'", "campo desconocido Color"]:
            self.assertTrue(any(trozo in x for x in f), (trozo, f))

    @unittest.skipUnless(os.path.exists("/opt/amiga/bin/lha") and shutil.which("lha"), "lha de 68k y lhasa")
    def test_lha(self):
        with tempfile.TemporaryDirectory() as d:
            caj = Path(d) / "Prueba"
            caj.mkdir()
            (caj / "Prueba").write_bytes(b"\x00\x00\x03\xf3programa")
            (caj / "paquete.txt").write_text(PAQUETE, encoding="utf-8")
            out = Path(d) / "out"
            r = subprocess.run([sys.executable, str(ROOT / "tools/paquete_hangar.py"), str(caj), "-o", str(out)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("Ana Garc\xeda".encode("latin-1"), (out / "Prueba.readme").read_bytes())
            lista = subprocess.run(["lha", "l", str(out / "Prueba.lha")], capture_output=True, text=True).stdout
            self.assertIn("Prueba/Prueba", lista)
            self.assertIn("Prueba.readme", lista)
            self.assertNotIn("paquete.txt", lista)


if __name__ == "__main__":
    unittest.main()
