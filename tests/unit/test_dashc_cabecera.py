"""dashc --cabecera (Dash 2.0, D11j): los structs del programa en C para el C de @link, con la forma que les da dashc."""
import os
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DASHC = os.path.join(ROOT, "dashc", "dashc")


@unittest.skipUnless(os.path.exists(DASHC), "falta dashc/dashc (make -C dashc)")
class TestCabecera(unittest.TestCase):
    def test_un_modulo_sin_main(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "m.dash")
            with open(src, "w") as f:
                f.write("struct Nodo\n    n: Int\n    nombre: String\n    hijos: [Nodo]\n    weak padre: Nodo\n"
                        "    visto: Bool\n    x: Float\nend\n")
            h = os.path.join(tmp, "m.h")
            r = subprocess.run([DASHC, "--cabecera", h, src], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            with open(h) as f:
                t = f.read()
            self.assertIn("typedef struct _Dash_Nodo {\n    LONG n;\n    STRPTR nombre;\n    DashArray *hijos;\n"
                          "    struct _Dash_Nodo *padre;   /* weak */\n    LONG /* Bool: 0 o 1 */ visto;\n"
                          "    ULONG /* Float: sus bits */ x;\n} _Dash_Nodo;", t)
            self.assertIn("LONG dl_arr_get(DashArray *a, LONG i);", t)


if __name__ == "__main__":
    unittest.main()
