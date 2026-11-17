"""tools/gen_ayuda.py: la ayuda para el Amiga (Dash.ayuda y Dash.guide, en castellano y en inglés). Todas las funciones
tienen ficha, los enlaces llevan a fichas que existen, los índices del .ayuda están ordenados y apuntan donde dicen,
y el AmigaGuide tiene un nodo por ficha. tests/ayuda/leer_fichas.dash (con lib/ayuda.dash) compila por los dos
caminos y, con tests/run_tests.py --emu (DASH_TEST_EMU=1), lee unas fichas en el emulador.

    python3 -m unittest tests/unit/test_gen_ayuda.py      (tests/run_tests.py lo corre también)
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(RAIZ / "tools"))
import gen_ayuda  # noqa: E402
from compiler import amiga_builtins  # noqa: E402

PROGRAMA = RAIZ / "tests" / "ayuda" / "leer_fichas.dash"


class Ayuda:
    """Un lector del .ayuda en Python, como el de lib/ayuda.dash, para comprobar el formato"""

    def __init__(self, datos: bytes):
        self.d = datos
        self.cab = {}
        for l in datos[:512].split(b"\n"):
            if l == b".":
                break
            t = l.decode("ascii").split(" ")
            self.cab[t[0]] = [int(x) if x.isdigit() else x for x in t[1:]]

    def registro(self, tabla, i):
        off, n, rec = self.cab[tabla][:3]
        assert 0 <= i < n
        return self.d[off + i * rec:off + (i + 1) * rec].decode("latin-1")

    def nombres(self):
        return [self.registro("nombres", i) for i in range(self.cab["nombres"][1])]

    def buscar(self, nombre):
        for r in self.nombres():
            if r[:-7].rstrip() == nombre.lower():
                return int(r[-6:-1])
        return -1

    def ficha(self, i):
        r = self.registro("fichas", i)
        off, largo = int(r[0:8]), int(r[9:15])
        return self.d[off:off + largo].decode("latin-1").split("\n")[:-1]

    def clave(self, i):
        return self.registro("fichas", i)[18:-1].rstrip()

    def tipo(self, i):
        return self.registro("fichas", i)[16]

    def palabra(self, p):
        for i in range(self.cab["palabras"][1]):
            r = self.registro("palabras", i)
            largo = len(r) - 15
            if r[:largo].rstrip() == p:
                off, n = int(r[largo + 1:largo + 9]), int(r[largo + 10:largo + 14])
                return [int(x) for x in self.d[off:off + n * 6].decode("ascii").split()]
        return []


class GenAyuda(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.mkdtemp()
        r = subprocess.run([sys.executable, str(RAIZ / "tools/gen_ayuda.py"), "--salida", cls.dir],
                           capture_output=True, text=True)
        if r.returncode:
            raise AssertionError(r.stdout + r.stderr)
        cls.es = Ayuda((Path(cls.dir) / "Dash.ayuda").read_bytes())
        cls.en = Ayuda((Path(cls.dir) / "Dash_en.ayuda").read_bytes())

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.dir, ignore_errors=True)

    def test_every_builtin_has_its_page_in_both_languages(self):
        for a in (self.es, self.en):
            for nombre in amiga_builtins.ALL_BUILTINS:
                i = a.buscar(nombre)
                self.assertGreaterEqual(i, 0, nombre)
                self.assertEqual(a.clave(i), nombre)
                self.assertEqual(a.tipo(i), "F")
                lineas = a.ficha(i)
                self.assertEqual(lineas[0].split(" ")[0], "@" + nombre)
                self.assertTrue(any(l.startswith("%firma " + nombre + "(") for l in lineas), nombre)

    def test_links_and_fields(self):
        for a in (self.es, self.en):
            claves = {a.clave(i) for i in range(a.cab["fichas"][1])}
            for i in range(a.cab["fichas"][1]):
                lineas = a.ficha(i)
                self.assertTrue(lineas[0].startswith(f"@{a.clave(i)} {a.tipo(i)} "))
                for l in lineas[1:]:
                    self.assertTrue(l == "" or l[0] in "% #|*", (a.clave(i), l))
                    if l.startswith("*"):
                        self.assertIn(l[1:].split(" ")[0], claves, (a.clave(i), l))
                    if l.startswith("%dashos "):
                        self.assertIn(l.split(" ")[1], ("si", "no", "solo"))

    def test_every_example_can_be_tried(self):
        """Forja's "Probar": the whole program of the page (code lines with Main), or else the first example of the
        function's group. A function whose example is a piece of another one gets it whole (lo pidió Forja)"""
        for a in (self.es, self.en):
            for i in range(a.cab["fichas"][1]):
                if a.tipo(i) != "F":
                    continue
                lineas = a.ficha(i)
                campos = {l[1:].split(" ", 1)[0]: l.split(" ", 1)[1] for l in lineas if l.startswith("%")}
                if "ejemplo" not in campos:
                    continue
                if any(re.match(r"\|Main(\s|#|$)", l) for l in lineas):
                    continue
                grupo = a.ficha(a.buscar(campos["grupo"]))
                primero = next(l.split(" ", 1)[1] for l in grupo if l.startswith("%ejemplo "))
                self.assertEqual(campos["ejemplo"], primero, a.clave(i))
        # the small examples of some functions, whole in their pages
        lineas = self.es.ficha(self.es.buscar("sprite_set_row"))
        self.assertIn("%ejemplo tests/test_doc_sprite.dash", lineas)
        self.assertIn("|Main", lineas)

    def test_indexes_are_sorted_and_point_right(self):
        for a in (self.es, self.en):
            nombres = [r[:-7].rstrip() for r in a.nombres()]
            self.assertEqual(nombres, sorted(nombres))
            self.assertEqual(len(nombres), len(set(nombres)))
            palabras = [a.registro("palabras", i)[:-15].rstrip() for i in range(a.cab["palabras"][1])]
            self.assertEqual(palabras, sorted(palabras))
            # las fichas, seguidas y una detrás de otra en la zona de texto
            off, largo = a.cab["texto"]
            fin = off
            for i in range(a.cab["fichas"][1]):
                r = a.registro("fichas", i)
                self.assertEqual(int(r[0:8]), fin)
                fin += int(r[9:15]) + 1
            self.assertEqual(fin, off + largo)
            self.assertEqual(off + largo, len(a.d))

    def test_words_of_the_language_and_search(self):
        self.assertEqual(self.es.ficha(self.es.buscar("eventloop"))[0], "@m12_5 M Event Loop")
        self.assertEqual(self.en.ficha(self.en.buscar("EventLoop"))[0].split(" ")[0], "@m12_5")
        ids = self.es.palabra("sonido")
        self.assertTrue(ids)
        self.assertIn(self.es.buscar("sound_play"), ids)
        self.assertEqual(gen_ayuda.plegar("Música ÑANDÚ"), "musica nandu")

    def test_groups_and_sections(self):
        for a in (self.es, self.en):
            off, n = a.cab["grupos"]
            lineas = a.d[off:a.cab["secciones"][0]].decode("latin-1").splitlines()
            self.assertEqual(len(lineas), n)
            self.assertEqual(n, len(gen_ayuda.GROUPS))
            for l in lineas:
                self.assertEqual(a.tipo(int(l[:5])), "G")

    def test_guide_has_a_node_per_page(self):
        for nombre, a in (("Dash.guide", self.es), ("Dash_en.guide", self.en)):
            guia = (Path(self.dir) / nombre).read_bytes().decode("latin-1")
            self.assertTrue(guia.startswith(f"@database {nombre}\n"))
            nodos = re.findall(r"^@node (\S+) ", guia, re.M)
            self.assertEqual(len(nodos), a.cab["fichas"][1])
            self.assertEqual(guia.count("\n@endnode"), len(nodos))
            self.assertEqual(nodos[0], "MAIN")
            enlaces = set(re.findall(r'@\{"[^"]*" link (\S+)\}', guia))
            self.assertFalse(enlaces - set(nodos))
            # una @ suelta en el texto abriría un comando: todas van escapadas
            for l in guia.splitlines():
                if not l.startswith(("@database", "@$VER", "@author", "@remark", "@index", "@node", "@toc",
                                     "@endnode")):
                    self.assertIsNone(re.search(r'(?<!\\)@(?!\{)', l.replace("\\\\", "")), l)

    def test_reader_compiles_both_ways(self):
        for extra in ([], ["--gcc"]):
            r = subprocess.run([str(RAIZ / "dash"), *extra, "--check", str(PROGRAMA)], cwd=RAIZ,
                               capture_output=True, text=True)
            if "falta el compilador" in r.stderr + r.stdout:
                self.skipTest("sin dashc (make -C dashc)")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    @unittest.skipUnless(os.environ.get("DASH_TEST_EMU") and os.environ.get("DASH_KICKSTART"),
                         "solo con tests/run_tests.py --emu (DASH_TEST_EMU=1) y $DASH_KICKSTART")
    def test_reads_pages_on_the_amiga(self):
        a = self.es

        def mostrar(nombre):
            i = a.buscar(nombre)
            if i < 0:
                return [f"{nombre}: no esta"]
            lineas = a.ficha(i)
            out = [f"{nombre}: ficha {i} {a.tipo(i)} {a.clave(i)}, {len(lineas)} lineas",
                   "  titulo: " + lineas[0].split(" ", 2)[2], "  " + lineas[0], "  " + lineas[1]]
            for l in lineas:
                if l.startswith("*"):
                    d = l[1:].split(" ")[0]
                    out.append(f"  enlace: {d} -> " + a.ficha(a.buscar(d))[0].split(" ", 2)[2])
                    break
            return out
        esperado = [f"ayuda es {a.cab['version'][0]}, {a.cab['fichas'][1]} fichas"]
        for n in ("file_seek", "EventLoop", "RA_EVENT_CLOSE", "no_existe"):
            esperado += mostrar(n)
        ids = a.palabra("musica")
        esperado.append(f"musica: {len(ids)} fichas, la primera {a.clave(ids[0])}")
        palabras = [a.registro("palabras", i)[:-15].rstrip() for i in range(a.cab["palabras"][1])]
        esperado.append("sound*: " + " ".join([p for p in palabras if p.startswith("sound")][:4]))
        esperado.append("fin")
        for extra in ([], ["--dash2"]):
            r = subprocess.run([sys.executable, str(RAIZ / "tools/emu_run.py"), *extra, "--file",
                                str(Path(self.dir) / "Dash.ayuda"), str(PROGRAMA)], cwd=RAIZ,
                               capture_output=True, text=True, timeout=300)
            salida = r.stdout.split("RC=0\n", 1)[-1].splitlines()
            self.assertEqual(salida[:len(esperado)], esperado, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
