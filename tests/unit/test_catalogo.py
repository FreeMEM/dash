"""tools/catalogo.py (dashweb D71): the texts of a program and its .dashui files, the .ct to translate and the
catalog file for locale.library; and the "tr" numbers of a .dashui in the code it becomes."""
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))
import catalogo  # noqa: E402
from compiler.dashui import generate as dashui_to_dash  # noqa: E402

PROGRAM = '''import "ventana.dashui"
const MSG_ADIOS = 2
Main
    Print tr(1, "Hola")
    Print tr(MSG_ADIOS, "Adiós")
    Print tr(0x10, "Línea\\nDos \\"comillas\\"")
    Print tr(1, "Hola")
end
'''
WINDOW = {"dashui": 1, "windows": [{
    "name": "Principal", "title": "Mi programa", "tr": 20,
    "menus": [{"title": "Archivo", "tr": 21, "items": [{"label": "Salir", "key": "Q", "event": 1, "tr": 22},
                                                         {"separator": True}]}],
    "root": {"type": "vgroup", "children": [
        {"type": "button", "name": "ok", "label": "Aceptar", "help": "Cierra", "tr": {"label": 23, "help": 24}},
        {"type": "text", "text": "Sin número"}]}}]}


def parse_catalog(data: bytes):
    """{chunk: bytes} and {number: text} of a catalog file"""
    assert data[:4] == b"FORM" and data[8:12] == b"CTLG"
    assert struct.unpack(">I", data[4:8])[0] == len(data) - 8
    chunks, pos = {}, 12
    while pos < len(data):
        cid, size = data[pos:pos + 4], struct.unpack(">I", data[pos + 4:pos + 8])[0]
        chunks[cid] = data[pos + 8:pos + 8 + size]
        pos += 8 + size + (size & 1)
    strings, strs, pos = {}, chunks[b"STRS"], 0
    while pos < len(strs):
        number, length = struct.unpack(">II", strs[pos:pos + 8])
        text = strs[pos + 8:pos + 8 + length]
        assert text.endswith(b"\0")
        strings[number] = text[:-1].decode("latin-1")
        pos += 8 + length + (-length % 4)
        assert pos % 4 == 0
    return chunks, strings


class TestCatalogo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        (self.dir / "prog.dash").write_text(PROGRAM, encoding="utf-8")
        (self.dir / "ventana.dashui").write_text(json.dumps(WINDOW), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_texts_of_the_program_and_its_window(self):
        texts = catalogo.collect([self.dir / "prog.dash"])
        self.assertEqual(texts[1], ("Hola", None))
        self.assertEqual(texts[2], ("Adiós", "MSG_ADIOS"))
        self.assertEqual(texts[16][0], 'Línea\\nDos \\"comillas\\"')
        self.assertEqual({n: t for n, (t, _) in texts.items() if n >= 20},
                         {20: "Mi programa", 21: "Archivo", 22: "Salir", 23: "Aceptar", 24: "Cierra"})
        cd = catalogo.write_cd(texts, ["prog.dash"])
        self.assertIn("; MSG_ADIOS\nMSG_2 (2//)\nAdiós\n", cd)
        self.assertEqual([(n, i) for n, i, _ in catalogo.read_cd(cd)][:3], [("MSG_1", 1), ("MSG_2", 2), ("MSG_16", 16)])

    def test_one_number_two_texts_is_an_error(self):
        (self.dir / "prog.dash").write_text('Main\n    Print tr(1, "Hola")\n    Print tr(1, "Adiós")\nend\n')
        with self.assertRaisesRegex(catalogo.CatalogError, "number 1"):
            catalogo.collect([self.dir / "prog.dash"])

    def test_tr_of_something_not_a_const(self):
        (self.dir / "prog.dash").write_text('Main\n    Print tr(n, "Hola")\nend\n')
        with self.assertRaisesRegex(catalogo.CatalogError, "not a const"):
            catalogo.collect([self.dir / "prog.dash"])

    def test_ct_to_translate_keeps_what_was_translated(self):
        cd = catalogo.read_cd(catalogo.write_cd(catalogo.collect([self.dir / "prog.dash"]), ["prog.dash"]))
        ct = catalogo.write_ct(cd, "english", "Prog.catalog", "1.0")
        self.assertTrue(ct.startswith("## version $VER: Prog.catalog 1.0 ("))
        self.assertIn("## language english\n", ct)
        self.assertIn("MSG_2\n\n; Adiós\n", ct)
        done = ct.replace("MSG_1\n\n", "MSG_1\nHello\n")
        again = catalogo.write_ct(cd, "english", "Prog.catalog", "1.0", catalogo.read_ct(done)[1])
        self.assertIn("MSG_1\nHello\n; Hola\n", again)

    def test_catalog_file(self):
        ct = ("## version $VER: Prog.catalog 1.2 (23.10.2026)\n## language english\n## codeset 0\n;\n"
              "MSG_2\nGoodbye\n; Adiós\nMSG_1\nHello\n; Hola\nMSG_3\n\n; Sin traducir\n"
              "MSG_16\nLine\\ntwo \\\"quotes\\\" \\e[1mü\\x41\\101\n; Línea\nMSG_4\n; (its line taken away)\nMSG_5\nabc\n")
        name, language, data = catalogo.build_catalog(ct)
        self.assertEqual((name, language), ("Prog.catalog", "english"))
        chunks, strings = parse_catalog(data)
        self.assertEqual(chunks[b"FVER"], b"$VER: Prog.catalog 1.2 (23.10.2026)\0")
        self.assertEqual(chunks[b"LANG"], b"english\0")
        self.assertEqual(chunks[b"CSET"], b"\0" * 32)
        self.assertEqual(strings, {1: "Hello", 2: "Goodbye", 5: "abc",
                                   16: 'Line\ntwo "quotes" \x1b[1müAA'})   # by number, Latin-1, no empty ones

    def test_bad_ct(self):
        with self.assertRaisesRegex(catalogo.CatalogError, "version"):
            catalogo.build_catalog("## language english\nMSG_1\nHello\n")
        with self.assertRaisesRegex(catalogo.CatalogError, "MSG_<number>"):
            catalogo.build_catalog("## version $VER: P.catalog 1.0\n## language english\nHOLA\nHello\n")

    def test_dashui_texts_go_through_tr(self):
        code = dashui_to_dash(json.dumps(WINDOW), "ventana.dashui")
        for line in ('mui_window_begin(tr(20, "Mi programa")', 'mui_menu_begin(tr(21, "Archivo"))',
                     'mui_menu_item(tr(22, "Salir"), "Q", 1)', 'mui_button(tr(23, "Aceptar"))',
                     'mui_help(ok, tr(24, "Cierra"))', 'mui_text("Sin número")'):
            self.assertIn(line, code)


if __name__ == "__main__":
    unittest.main()
