"""Inline 68k assembler, C path (compiler/asm68k.py, docs/ASM_DISEÑO.md): the blocks taken out of the source,
their text for binutils' as, the errors, and the C of ./dash --gcc (with gcc when it is installed)."""
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from compiler import asm68k                          # noqa: E402
from compiler.lsp_format import format_text           # noqa: E402

AS = os.path.join(os.environ.get("DASH_TOOLCHAIN", "/opt/amiga"), "bin", "m68k-amigaos-as")


def block_of(body, header="", consts=None, filename=""):
    src = "Main\n    asm" + header + "\n" + body + "\n    end\nend\n"
    new = asm68k.extract(src, filename)
    n = max(asm68k.BLOCKS)
    return new, asm68k.BLOCKS[n]


def text_of(body, header="", consts=None, filename=""):
    _, b = block_of(body, header, filename=filename)
    return asm68k.translate(b, consts or {})


class Extract(unittest.TestCase):
    def test_header_becomes_calls(self):
        src = ("Main\n    asm in a0 = datos, d0 = f(1, 2) out total = d1, resto = d0 uses d2-d4/a1\n"
               "        moveq #0,d1\n    end\n    Print total\nend\n")
        new = asm68k.extract(src, "x.dash")
        lines = new.split("\n")
        self.assertEqual(len(lines), len(src.split("\n")))       # the lines do not move
        n = max(asm68k.BLOCKS)
        self.assertEqual(lines[1], f"    __dash_asm({n}, datos, f(1, 2)) total = __dash_asm_out({n}, 0)"
                                   f" resto = __dash_asm_out({n}, 1)")
        self.assertEqual(lines[2:4], ["", ""])
        b = asm68k.BLOCKS[n]
        self.assertEqual(b.ins, [("a0", "datos"), ("d0", "f(1, 2)")])
        self.assertEqual(b.outs, [("total", "d1"), ("resto", "d0")])
        self.assertEqual(b.clobbers(), ["d2", "d3", "d4", "a1"])

    def test_without_inputs(self):
        new, b = block_of("        nop")
        self.assertIn(f"__dash_asm({b.n})", new)

    def test_not_a_block(self):
        for src in ("Main\n    asm = 3\nend\n", 'Main\n    x = 1\nend\n@native func f()\n"""\nasm in\n"""\nend\n'):
            self.assertEqual(asm68k.extract(src, ""), src)

    def test_header_errors(self):
        cases = [("asm in a5 = x", "a5 no se puede usar"), ("asm in sp = x", "a7 no se puede usar"),
                 ("asm in d0 = x, d0 = y", "se repite"), ("asm out x = d9", "operando no válido"),
                 ("asm uses d0 in d1 = 2 uses d2", "una sola vez")]
        for header, msg in cases:
            with self.assertRaises(asm68k.AsmError) as e:
                asm68k.extract(f"Main\n    {header}\n    end\nend\n", "")
            self.assertIn(msg, e.exception.message)
            self.assertEqual(e.exception.line, 2)

    def test_missing_end(self):
        with self.assertRaises(asm68k.AsmError) as e:
            asm68k.extract("Main\n    asm\n        nop\n", "")
        self.assertEqual(e.exception.message, "asm: falta el end del bloque asm")


class Translate(unittest.TestCase):
    def test_labels_numbers_data(self):
        text, need = text_of(".bucle:  add.l (a0)+,d1 ; suma\n* comentario\n  dbra d0,.bucle\n"
                             "fin\n  move.l #%1010+$10+'A',d2\n  lea tabla(pc),a1\n  bra.s fin\n"
                             "tabla: dc.b \"hi\",1\n  dc.w 2\n  dc.l tabla\n  ds.b 1\n")
        self.assertEqual(need, [])
        self.assertEqual(text.split("\n\t"), [
            ".Ld%=Lbucle:", "add.l (a0)+,d1", "dbra d0,.Ld%=Lbucle", ".Ld%=Nfin:", "move.l #91,d2",
            "lea .Ld%=Ntabla(pc),a1", "bra.s .Ld%=Nfin", ".Ld%=Ntabla:", ".byte 104,105,1", ".even", ".word 2",
            ".long .Ld%=Ntabla", ".skip 1", ".even"])

    def test_equ_and_consts(self):
        text, _ = text_of("ANCHO equ 320\nALTO = K*2\n  move.l #ANCHO*ALTO,d0\n  move.w $dff006,d1",
                          consts={"K": 128})
        self.assertEqual(text.split("\n\t"), ["move.l #81920,d0", "move.w 14675974,d1"])

    def test_addressing_modes(self):
        text, need = text_of("  move.w (4,a0),8(a1)\n  move.l -2(a0,d1),(a2,a3.l)\n  move.l 4.w,a6\n"
                             "  movem.l d2-d7/a2-a6,-(sp)\n  lsl.w d0\n  add.l #1,d3\n  cmp.w #1,a0\n"
                             "  move.l (a0,d1.l*4),d2\n  bfextu d0{4:8},d1")
        self.assertEqual(text.split("\n\t"), [
            "move.w 4(a0),8(a1)", "move.l -2(a0,d1.w*1),0(a2,a3.l*1)", "move.l 4.w,a6",
            "movem.l d2-d7/a2-a6,-(a7)", "lsl.w #1,d0", "addi.l #1,d3", "cmp.w #1,a0",
            "move.l 0(a0,d1.l*4),d2", "bfextu d0{4:8},d1"])
        self.assertEqual([w for w, _ in need], ["(a0,d1.l*4)", "bfextu"])

    def test_incbin(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "datos.bin"), "wb") as f:
                f.write(b"12345")
            text, _ = text_of('  incbin "datos.bin",1,3\n  nop', filename=os.path.join(d, "p.dash"))
            self.assertEqual(text.split("\n\t"), [f'.incbin "{d}/datos.bin",1,3', ".even", "nop"])

    def test_errors(self):
        cases = [("  movx d0,d1", "asm: instrucción desconocida: movx", 3),
                 ("  move.l #FOO,d0", "asm: nombre desconocido: FOO", 3),
                 ("  moveq.w #1,d0", "asm: tamaño .w no válido en moveq", 3),
                 ("  nop d0", "asm: nop pide 0 operandos", 3),
                 ("  moveq #200,d0", "asm: moveq va de -128 a 127", 3),
                 ("  move.l d0,#1", "asm: operando no válido: #1", 3),
                 ("  cnop 0,4", "asm: instrucción desconocida: cnop", 3),
                 ("  bra.s x\nx: nop", "asm: un salto .s no puede ir a la instrucción siguiente", 3),
                 ("x: nop\nx: nop", "asm: x ya está definido", 4)]
        for body, msg, line in cases:
            with self.assertRaises(asm68k.AsmError) as e:
                text_of(body)
            self.assertEqual(e.exception.message, msg)
            self.assertEqual(e.exception.line, line)

    def test_c_string(self):
        self.assertEqual(asm68k.c_string('\t.Ld%=Nx:\n\t.incbin "a%b"'),
                         '"\\t.Ld%=Nx:\\n\\t.incbin \\"a%%b\\""')

    @unittest.skipUnless(os.path.exists(AS), "sin m68k-amigaos-as")
    def test_as_accepts_it(self):
        text, _ = text_of("  move.l d0,d1\n.l: move.w (4,a0,d1.l),-(a1)\n  dbra d0,.l\n  bra .l\n"
                          "  movem.l d2-d7/a2-a4/a6,-(sp)\n  movem.l (sp)+,d2-d7/a2-a4/a6\n"
                          "  btst #6,$bfe001\n  bne.s .l\n  dc.b 1\n  rts")
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "a.s")
            with open(src, "w") as f:
                f.write("\t" + text.replace("%=", "1") + "\n")
            r = subprocess.run([AS, "-m68000", "-o", os.path.join(d, "a.o"), src], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)


class Format(unittest.TestCase):
    def test_formatter_keeps_the_body(self):
        src = ("func f(x: Int) -> Int\nasm in d0 = x out x = d0\n.l:  addq.l #1,d0 ; uno\n"
               "        dbra d1,.l\nend\nreturn x\nend\n")
        self.assertEqual(format_text(src), "func f(x: Int) -> Int\n    asm in d0 = x out x = d0\n"
                                           ".l:  addq.l #1,d0 ; uno\n        dbra d1,.l\n    end\n"
                                           "    return x\nend\n")


if __name__ == "__main__":
    unittest.main()
