"""./dash --gcc --cabecera (D82): the program's structs as the C path lays them out, its integer constants and its
@export prototypes, with the names of the straight compiler's header (one C for both paths)."""
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DASH = os.path.join(ROOT, "dash")
GCC = os.path.join(os.environ.get("DASH_TOOLCHAIN", "/opt/amiga"), "bin", "m68k-amigaos-gcc")

PROGRAM = '''const K = 7
const SI = true
struct Caja
    v: Int
    b: Bool
    f: Float
    nombre: String
    l: [Int]
    hija: Caja
    weak padre: Caja
end

@export func dash_nombre(n: Int, c: Caja) -> String
    return "#{n} cosas"
end

@export func dash_nada(b: Bool)
    Print b
end

Main
    c = Caja(1, true, 1.5, "a", [1, 2], nil, nil)
    Print dash_nombre(3, c)
end
'''

# the places of the fields in the program's own C (a Bool, BOOL: 2 bytes; the 68000 aligns to 2)
CHECK = '''#include <stddef.h>
#include "tipos.h"
_Static_assert(offsetof(_Dash_Caja, b) == 4, "b");
_Static_assert(offsetof(_Dash_Caja, f) == 6, "f");
_Static_assert(offsetof(_Dash_Caja, nombre) == 10, "nombre");
_Static_assert(offsetof(_Dash_Caja, hija) == 18, "hija");
_Static_assert(sizeof(_Dash_Caja) == 26, "size");
_Static_assert(K == 7 && SI == 1, "const");
LONG usa(_Dash_Caja *c) { return dl_str_len(dash_nombre(c->v, c)) + dl_arr_length(c->l) + db_time_ms(); }
'''


class TestCabeceraGcc(unittest.TestCase):
    def header(self, tmp):
        src = os.path.join(tmp, "p.dash")
        with open(src, "w") as f:
            f.write(PROGRAM)
        h = os.path.join(tmp, "tipos.h")
        r = subprocess.run([sys.executable, DASH, "--gcc", "-q", "--cabecera", h, src], capture_output=True,
                           text=True, cwd=tmp)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(h) as f:
            return f.read()

    def test_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = self.header(tmp)
            self.assertIn("#define K 7L\n", t)
            self.assertIn("#define SI 1L\n", t)
            self.assertIn("    BOOL /* Bool: 0 o 1, 2 bytes */ b;\n", t)
            self.assertIn("    ULONG /* Float: sus bits */ f;\n", t)
            self.assertIn("    DashArray *l;\n", t)
            self.assertIn("    struct _Dash_Caja *padre;   /* weak */\n", t)
            self.assertIn("STRPTR dash_nombre(LONG n, struct _Dash_Caja *c);", t)
            self.assertIn("void dash_nada(BOOL /* Bool: 0 o 1, 2 bytes */ b);", t)
            self.assertIn("LONG dl_arr_get(DashArray *a, LONG i);", t)
            # without -o, only the header: no executable
            self.assertFalse(os.path.exists(os.path.join(tmp, "p")))

    @unittest.skipUnless(os.path.exists(GCC), "no m68k-amigaos-gcc")
    def test_layout_matches_the_program(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.header(tmp)
            c = os.path.join(tmp, "usa.c")
            with open(c, "w") as f:
                f.write(CHECK)
            r = subprocess.run([GCC, "-noixemul", "-std=gnu11", "-Werror", "-c", c, "-o", os.path.join(tmp, "usa.o")],
                               capture_output=True, text=True, cwd=tmp)
            self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
