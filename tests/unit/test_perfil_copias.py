"""./dash --profile con funciones pequeñas (lo vio Forja): el directo copia en línea las funciones pequeñas, las de una
línea y las que se llaman desde un solo sitio, y así el perfil solo veía Main. Con --profile no las copia (como con
--debug). Sin emulador se comprueba que compila por los dos caminos; con tests/run_tests.py --emu (DASH_TEST_EMU=1),
que el informe del perfil trae cada función con sus llamadas, por los dos caminos.

    python3 -m unittest tests/unit/test_perfil_copias.py      (tests/run_tests.py lo corre también)
"""
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent

PROGRAMA = """\
func doble(x: Int) -> Int
    return x * 2
end

func pequena(x: Int) -> Int
    y = x + 1
    return y * 3
end

func una_vez(n: Int) -> Int
    s = 0
    for i in (1..n)
        s = s + i
    end
    return s
end

Main
    t = 0
    for i in (1..300)
        t = t + doble(i) + pequena(i)
    end
    t = t + una_vez(50)
    Print "total #{t}"
end
"""

# (función, llamadas) que el informe tiene que traer
ESPERADO = [("doble", 300), ("pequena", 300), ("una_vez", 1)]


class PerfilCopias(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.src = Path(self.dir) / "perfil_copias.dash"
        self.src.write_text(PROGRAMA)

    def compilar(self, extra):
        exe = Path(self.dir) / ("p_gcc" if extra else "p_directo")
        r = subprocess.run([str(RAIZ / "dash"), *extra, "--profile", str(self.src), "-o", str(exe)], cwd=RAIZ,
                           capture_output=True, text=True)
        if "falta el compilador" in r.stderr + r.stdout:
            self.skipTest("sin dashc (make -C dashc)")
        if not Path("/opt/amiga/bin/m68k-amigaos-gcc").exists() and extra:
            self.skipTest("sin el gcc de bebbo")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return exe

    def test_compila_por_los_dos_caminos(self):
        for extra in ([], ["--gcc"]):
            self.assertTrue(self.compilar(extra).exists())

    @unittest.skipUnless(os.environ.get("DASH_TEST_EMU") and os.environ.get("DASH_KICKSTART"),
                         "solo con tests/run_tests.py --emu (DASH_TEST_EMU=1) y $DASH_KICKSTART")
    def test_el_informe_trae_las_funciones(self):
        for extra in ([], ["--gcc"]):
            exe = self.compilar(extra)
            r = subprocess.run([sys.executable, str(RAIZ / "tools/emu_run.py"), str(exe)], cwd=RAIZ,
                               capture_output=True, text=True, timeout=300)
            salida = r.stdout
            self.assertIn("total 227925", salida, salida + r.stderr)
            for nombre, llamadas in ESPERADO:
                self.assertRegex(salida, re.compile(rf"^perfil: .*\s{llamadas}\s+{nombre}$", re.M),
                                 f"{' '.join(extra) or 'directo'}: falta {nombre} con {llamadas} llamadas\n{salida}")


if __name__ == "__main__":
    unittest.main()
