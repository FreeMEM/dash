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


def block_of(body, header="", consts=None, filename=""):  # noqa: E302
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

    def test_end_with_comment(self):
        src = "Main\n    asm uses d0\n        moveq #1,d0\n    end   # fin del asm\n    Print 1\nend\n"
        new = asm68k.extract(src, "")
        self.assertEqual(new.count("\n"), src.count("\n"))
        self.assertIn("Print 1", new.split("\n")[4])
        new = asm68k.extract(src.replace("# fin del asm", "; fin"), "")
        self.assertIn("Print 1", new.split("\n")[4])

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
                 ("  cnop 2,4", "asm: cnop: solo cnop 0,n (el desplazamiento, 0)", 3),
                 ("  bra.s x\nx: nop", "asm: un salto .s no puede ir a la instrucción siguiente", 3),
                 ("x: nop\nx: nop", "asm: x ya está definido", 4)]
        for body, msg, line in cases:
            with self.assertRaises(asm68k.AsmError) as e:
                text_of(body)
            self.assertEqual(e.exception.message, msg)
            self.assertEqual(e.exception.line, line)

    def test_errors_as_dashc(self):
        """The same verdict and text as dashc/src/asm68k.c, not gas's messages."""
        cases = [("  lea d0,a0", "asm: operando no válido: d0"),
                 ("  move.b a0,d0", "asm: tamaño .b no válido con un registro de direcciones"),
                 ("  add.b #1,a0", "asm: tamaño .b no válido en add"),
                 ("  jmp d0", "asm: operando no válido: d0"),
                 ("  clr.l a0", "asm: operando no válido: a0"),
                 ("  swap a0", "asm: operando no válido: a0"),
                 ("  asl.l #9,d0", "asm: la cuenta de asl va de 1 a 8"),
                 ("  lsr.l (a0)", "asm: tamaño .l no válido en lsr"),
                 ("  rol.b #1,(a0)", "asm: operando no válido: (a0)"),
                 ("  or.w d0,a0", "asm: operando no válido: a0"),
                 ("  eor.l (a0),d0", "asm: operandos no válidos en eor"),
                 ("  cmp.l d0,(a0)", "asm: operandos no válidos en cmp"),
                 ("  cmpm.w (a0)+,(a1)", "asm: cmpm va con (Ay)+,(Ax)+"),
                 ("  abcd d0,-(a1)", "asm: operandos no válidos en abcd"),
                 ("  addx.l (a0)+,(a1)+", "asm: operandos no válidos en addx"),
                 ("  movem.l d0,d1", "asm: operando no válido: d1"),
                 ("  move.w #70000,d0", "asm: el valor no cabe en 16 bits: 70000"),
                 ("  move.b #-129,d0", "asm: el valor no cabe en un byte: -129"),
                 ("  addq.l #9,d0", "asm: addq va de 1 a 8"),
                 ("  trap #16", "asm: trap va de 0 a 15"),
                 ("  dc.b 256", "asm: el valor no cabe en un byte: 256"),
                 ("  dc.w .x\n.x:", "asm: una etiqueta en dc va con dc.l"),
                 ("  move.l .a(a0),d0\n.a: nop", "asm: una etiqueta como desplazamiento de An no se admite: .a(a0)"),
                 ("  lea 40000(a0),a1", "asm: el desplazamiento no cabe en 16 bits: 40000(a0)"),
                 ("  move.w .a.w,d0\n.a: nop", "asm: una etiqueta como dirección corta no se admite: .a.w"),
                 ("  move.l #.a,d0\n  move.w #.a,d1\n.a: nop", "asm: una etiqueta como inmediato necesita .l"),
                 ("  ds.b -1", "asm: ds: tamaño no válido"),
                 ("  divsl.l d0,d1", "asm: divsl.l va con Dr:Dq"),
                 ("  bfextu d0,d1", "asm: falta el campo {desplazamiento:ancho}: d0"),
                 ("  swap d0,d1", "asm: swap pide 1 operando")]
        for body, msg in cases:
            with self.assertRaises(asm68k.AsmError, msg=body) as e:
                text_of(body)
            self.assertEqual(e.exception.message, msg, body)

    def test_accepted_as_dashc(self):
        """What dashc and vasm take: a list from d to a, a difference of labels, tst.l a0 (68020)."""
        text, need = text_of("  movem.l d0-a6,-(sp)\n  move.l .b-.a(a0),d0\n.a: nop\n.b: nop\n  tst.l a0")
        self.assertIn("d0-a6", text)
        self.assertEqual([w for w, _ in need], ["tst con ese operando"])

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


class SecondPart(unittest.TestCase):
    """asm func, sections, jsr to functions, the FPU and the rest of the 68020 (the second part, for demos)."""

    def test_asm_func_becomes_a_function(self):
        src = ("asm func suma(a: Int, b: Int) -> Int uses d2  # comentario\n    add.l d1,d0\n    moveq #0,d2\nend\n"
               "Main\n    Print suma(1, 2)\nend\n")
        new = asm68k.extract(src, "x.dash")
        lines = new.split("\n")
        self.assertEqual(len(lines), len(src.split("\n")))       # the lines do not move
        n = max(asm68k.BLOCKS)
        self.assertEqual(lines[0], "func suma(a: Int, b: Int) -> Int")
        self.assertEqual(lines[1], f"    __dash_asm({n}, a, b) __dash_asm_r = __dash_asm_out({n}, 0) return __dash_asm_r")
        self.assertEqual(lines[2:4], ["", "end"])
        b = asm68k.BLOCKS[n]
        self.assertEqual(b.ins, [("d0", "a"), ("d1", "b")])
        self.assertEqual(b.outs, [("__dash_asm_r", "d0")])
        self.assertEqual(b.uses, ["d2"])

    def test_asm_func_with_in_and_out(self):
        new = asm68k.extract("asm func f(l: [Int], n: Int) -> Pointer in a0 = l, d0 = n - 1 out a0\n  nop\nend\n", "")
        n = max(asm68k.BLOCKS)
        self.assertIn(f"__dash_asm({n}, l, n - 1) __dash_asm_r = __dash_asm_out({n}, 0)", new)
        self.assertEqual(asm68k.BLOCKS[n].outs, [("__dash_asm_r", "a0")])
        new = asm68k.extract("asm func g(p: Pointer) in a0 = p\n  clr.l (a0)\nend\n", "")
        self.assertIn("func g(p: Pointer)\n", new)
        self.assertNotIn("return", new)

    def test_asm_func_errors(self):
        cases = [("asm func f() -> String\n  nop\nend\n", "asm func: devuelve Int, Bool o Pointer"),
                 ("asm func f()\nend\n", "asm func: el cuerpo está vacío"),
                 ("asm func f(a) out d0\n  nop\nend\n", "asm func: sin -> Tipo no devuelve nada (quita el out)"),
                 ("asm func f(a) -> Int out r = d0\n  nop\nend\n", "asm func: out lleva solo el registro"),
                 ("asm func f\n  nop\nend\n", "asm func: se esperaba nombre(parámetros)")]
        for src, msg in cases:
            with self.assertRaises(asm68k.AsmError, msg=src) as e:
                asm68k.extract(src, "")
            self.assertTrue(e.exception.message.startswith(msg), e.exception.message)

    def test_sections_for_as(self):
        _, b = block_of("        lea tabla,a0\n        data_c\n    tabla:\n        dc.w 1\n        bss\n"
                        "    cuenta: ds.l 1\n        code\n        nop")
        self.assertTrue(b.sections)
        self.assertEqual(b.label_sec, {"tabla": "data_c", "cuenta": "bss"})
        text = asm68k.translator(b, {}).text.split("\n\t")
        self.assertEqual(text, ["lea .Ld%=Ntabla,a0", ".section .datachip", ".balign 4", ".Ld%=Ntabla:", ".word 1",
                                ".text", ".section .bss", ".balign 4", ".Ld%=Ncuenta:", ".skip 4", ".text", "nop"])

    def test_cnop_and_float_data(self):
        text = asm68k.translator(block_of("  nop\n  cnop 0,8\n.a: dc.s 1.5\n  dc.d -2")[1], {}).text
        self.assertEqual(text.split("\n\t"), ["nop", ".balignw 8,0x4e71", ".Ld%=La:", ".long 1069547520",
                                               ".long 3221225472,0"])

    def test_jsr_to_a_function_and_a_base(self):
        _, b = block_of("  jsr doble\n  move.l GfxBase,a6\n  lea doble,a0")
        tr = asm68k.translator(b, {}, {"doble": "doble"})
        self.assertEqual(tr.func_refs, ["doble"])
        self.assertEqual(tr.text.split("\n\t"), ["jsr \x01F0\x01", "move.l _GfxBase,a6", "lea \x01F0\x01,a0"])
        self.assertEqual(b.clobbers(True), ["d0", "d1", "a0", "a1"])

    def test_fpu_text(self):
        tr = asm68k.translator(block_of("  fmove.l d0,fp0\n  fmul.s #2.5,fp0\n  fadd.d #3,fp0\n"
                                        "  fmove.x #0.5,fp1\n  fbeq .x\n.x: fmovem.x fp2-fp7,-(sp)", " uses fp2-fp7")[1], {})
        self.assertEqual(tr.text.split("\n\t"),
                         ["fmove.l d0,fp0", "fmul.s #0r2.5,fp0", "fadd.d #0r3.0,fp0",
                          ".word 62012,18560,16382,0,32768,0,0,0", "fbeq .Ld%=Lx", ".Ld%=Lx:",
                          "fmovem.x fp2-fp7,-(a7)"])
        self.assertEqual([w for w, _ in tr.needs_fpu][:2], ["fmove.l", "fmul.s"])

    def test_more_020(self):
        tr = asm68k.translator(block_of("  move.l ([4,a0,d0.l*4],8),d1\n  cas2.l d0:d1,d2:d3,(a0):(a1)\n"
                                        "  cmp2.w (a0),d0\n  pack d0,d1,#0\n  trapeq\n  movec vbr,d0")[1], {})
        self.assertEqual(tr.text.split("\n\t"),
                         ["move.l ([4,a0,d0.l*4],8),d1", "cas2.l d0:d1,d2:d3,(a0):(a1)", "cmp2.w (a0),d0",
                          "pack d0,d1,#0", "trapeq", "movec vbr,d0"])
        self.assertEqual(len({line for _, line in tr.needs_020}), 6)

    def test_fix_chip_hunks(self):
        import struct
        from compiler.cflags import fix_chip_hunks
        with tempfile.TemporaryDirectory() as d:
            exe = os.path.join(d, "a")
            with open(exe, "wb") as f:
                f.write(struct.pack(">9I", 0x3F3, 0, 4, 0, 3, 10, 2, 5, 1))
            fix_chip_hunks(["x"], exe)                                   # no chip section: as it was
            self.assertEqual(struct.unpack(">4I", open(exe, "rb").read()[20:36]), (10, 2, 5, 1))
            fix_chip_hunks(['__asm__("\t.section .datachip")'], exe)   # the last hunk, in chip memory
            self.assertEqual(struct.unpack(">4I", open(exe, "rb").read()[20:36]), (10, 2, 5, 0x40000001))


class Format(unittest.TestCase):
    def test_formatter_keeps_the_body(self):
        src = ("func f(x: Int) -> Int\nasm in d0 = x out x = d0\n.l:  addq.l #1,d0 ; uno\n"
               "        dbra d1,.l\nend\nreturn x\nend\n")
        self.assertEqual(format_text(src), "func f(x: Int) -> Int\n    asm in d0 = x out x = d0\n"
                                           ".l:  addq.l #1,d0 ; uno\n        dbra d1,.l\n    end\n"
                                           "    return x\nend\n")


if __name__ == "__main__":
    unittest.main()
