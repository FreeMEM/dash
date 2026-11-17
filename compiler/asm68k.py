"""Inline 68k assembler blocks for the C path (./dash --gcc), docs/ASM_DISEÑO.md.

    asm in a0 = datos, d0 = n - 1 out total = d1 uses d2
        moveq   #0,d1
    .bucle:
        add.l   (a0)+,d1
        dbra    d0,.bucle
    end

extract() runs before the parser: it takes each block out of the source and leaves, on its first line,
`__dash_asm(N, inputs...) var = __dash_asm_out(N, 0) ...` (the other lines stay empty, so lines do not move).
The block is kept in BLOCKS[N], already parsed. The analyzer checks its names (check) and the code generator
turns it into the text of a GCC __asm__ for binutils' as (translate), which reads Motorola syntax with bare
register names. The straight compiler (dashc/src/asm68k.c) does the same with its own assembler and the same
error texts.
"""
import os
import re
import struct
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


class AsmError(Exception):
    """An error in an asm block: its message and where (line and column in the .dash)."""

    def __init__(self, message: str, line: int, col: int = 1):
        super().__init__(message)
        self.message, self.line, self.col = message, line, col


# ---- registers ----

ALLOWED = ["d0", "d1", "d2", "d3", "d4", "d5", "d6", "d7", "a0", "a1", "a2", "a3", "a4", "a6"]
_REG_RE = re.compile(r"^(?:[dD][0-7]|[aA][0-7]|[sS][pP])$")


def _reg_name(text: str) -> Optional[str]:
    """d0..d7, a0..a7 (sp is a7), lower case; None if text is not a register."""
    t = text.strip().lower()
    if t == "sp":
        return "a7"
    return t if _REG_RE.match(t) else None


def _bind_reg(text: str, line: int) -> str:
    """A register of in/out/uses: one Dash can lend the block."""
    if text.strip().lower() in _FP_ORDER:
        raise AsmError(f"asm: un registro de la FPU solo va en uses: {text.strip()}", line)
    reg = _reg_name(text)
    if reg is None:
        raise AsmError(f"asm: operando no válido: {text.strip()}", line)
    if reg in ("a5", "a7"):
        raise AsmError(f"asm: el registro {reg} no se puede usar en un bloque asm", line)
    return reg


_FP_ORDER = [f"fp{i}" for i in range(8)]


def _reg_list(text: str, line: int, fp: Optional[List[str]] = None) -> List[str]:
    """d2-d4/a1, d2, d3: the registers of a list (as in movem); fp0-fp7 go to fp (uses)."""
    regs = []
    for part in re.split(r"[,/]", text):
        part = part.strip()
        if not part:
            raise AsmError(f"asm: operando no válido: {text.strip()}", line)
        if part[:2].lower() == "fp" and fp is not None:
            ends = [x.strip().lower() for x in part.split("-")]
            if len(ends) > 2 or any(e not in _FP_ORDER for e in ends) or ends[0] > ends[-1]:
                raise AsmError(f"asm: registro no válido: {part}", line)
            for k in range(int(ends[0][2]), int(ends[-1][2]) + 1):
                if f"fp{k}" not in fp:
                    fp.append(f"fp{k}")
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            ra, rb = _bind_reg(a, line), _bind_reg(b, line)
            if ra[0] != rb[0] or ra > rb:
                raise AsmError(f"asm: operando no válido: {part}", line)
            for k in range(int(ra[1]), int(rb[1]) + 1):
                regs.append(_bind_reg(f"{ra[0]}{k}", line))
        else:
            regs.append(_bind_reg(part, line))
    return regs


# ---- the text, split at the top level ----

def _split_top(text: str, sep: str = ",") -> List[str]:
    """Split at sep outside (), [], {} and quotes."""
    parts, depth, quote, cur = [], 0, None, []
    for c in text:
        if quote:
            cur.append(c)
            if c == quote:
                quote = None
            continue
        if c in "\"'":
            quote = c
        elif c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        elif c == sep and depth == 0:
            parts.append("".join(cur))
            cur = []
            continue
        cur.append(c)
    parts.append("".join(cur))
    return parts


def _strip_dash_comment(text: str) -> str:
    """The header line without its # comment (outside texts)."""
    quote = None
    for i, c in enumerate(text):
        if quote:
            if c == "\\":
                continue
            if c == quote:
                quote = None
        elif c == '"':
            quote = c
        elif c == "#":
            return text[:i]
    return text


_HEADER_KW = ("in", "out", "uses")


def _header_sections(text: str, line: int) -> Dict[str, str]:
    """in ... out ... uses ...: the text of each part (words at the top level)."""
    sections: Dict[str, str] = {}
    depth, quote, i, current, start = 0, None, 0, None, 0
    n = len(text)
    while i < n:
        c = text[i]
        if quote:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                quote = None
            i += 1
            continue
        if c == '"':
            quote = c
        elif c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        elif depth == 0 and (c.isalpha()) and (i == 0 or not (text[i - 1].isalnum() or text[i - 1] == "_")):
            m = re.match(r"[A-Za-z_][A-Za-z0-9_]*", text[i:])
            word = m.group(0)
            if word in _HEADER_KW:
                if current is not None:
                    sections[current] = text[start:i]
                elif text[:i].strip():
                    raise AsmError(f"asm: operando no válido: {text[:i].strip()}", line)
                if word in sections or word == current:
                    raise AsmError(f"asm: {word} va una sola vez", line)
                current, start = word, i + len(word)
            i += len(word)
            continue
        i += 1
    if current is not None:
        sections[current] = text[start:]
    elif text.strip():
        raise AsmError(f"asm: operando no válido: {text.strip()}", line)
    return sections


# ---- blocks ----

@dataclass
class Line:
    """One line of the body: its label(s), what it does and its operands."""
    line: int                      # in the .dash
    col: int
    labels: List[str] = field(default_factory=list)
    op: str = ""                   # mnemonic or directive, lower case ("" only labels)
    size: str = ""                 # b, w, l, s or ""
    operands: List[str] = field(default_factory=list)
    equ: Optional[str] = None      # NAME equ value: the name (operands[0] is the value)


@dataclass
class Block:
    n: int
    filename: str
    directory: str
    line: int                      # the asm line
    ins: List[Tuple[str, str]] = field(default_factory=list)    # (register, Dash expression)
    outs: List[Tuple[str, str]] = field(default_factory=list)   # (variable, register)
    uses: List[str] = field(default_factory=list)
    lines: List[Line] = field(default_factory=list)
    labels: Dict[str, int] = field(default_factory=dict)        # name -> line
    equs: Dict[str, Line] = field(default_factory=dict)
    label_sec: Dict[str, str] = field(default_factory=dict)     # name -> its section (code, data, data_c, bss, bss_c)
    fuses: List[str] = field(default_factory=list)              # uses fp0-fp7 (FPU registers)
    sections: bool = False                                      # section, data_c...: its function is not inlined

    def clobbers(self, calls: bool = False) -> List[str]:
        """The registers gcc must take as changed: uses (and, with a call to a function, d0, d1, a0 and a1)."""
        bound = {r for r, _ in self.ins} | {r for _, r in self.outs}
        uses = set(self.uses) | ({"d0", "d1", "a0", "a1"} if calls else set())
        return [r for r in ALLOWED if r in uses and r not in bound] + [f for f in _FP_ORDER if f in self.fuses]


BLOCKS: Dict[int, Block] = {}
_counter = [0]
_memo: Dict[Tuple[str, str], str] = {}

_ASM_LINE = re.compile(r"^([ \t]*)asm(?=$|[ \t#])(.*)$")


def is_header(text: str) -> bool:
    """Is this line the start of an asm block (asm alone, or followed by in, out or uses)?"""
    m = _ASM_LINE.match(text)
    if not m:
        return False
    header = _strip_dash_comment(m.group(2))
    return not header.strip() or bool(re.match(r"[ \t]*(in|out|uses)\b", header))


# the line that closes a block: end alone, or with a comment (# or ;) after spaces
_END_RE = re.compile(r"^\s*end(?:\s+[#;].*|\s*)$")


def extract(source: str, filename: str = "") -> str:
    """The source with its asm blocks taken out (BLOCKS) and replaced by internal calls."""
    key = (filename, source)
    if key in _memo:
        return _memo[key]
    if "asm" not in source:
        return source
    lines = source.split("\n")
    out = []
    i = 0
    in_native = False
    directory = os.path.dirname(os.path.abspath(filename)) if filename else os.getcwd()
    while i < len(lines):
        text = lines[i]
        if in_native or '"""' in text:
            if text.count('"""') % 2 == 1:
                in_native = not in_native
            out.append(text)
            i += 1
            continue
        if not is_header(text):
            out.append(text)
            i += 1
            continue
        m = _ASM_LINE.match(text)
        header = _strip_dash_comment(m.group(2))
        line_no = i + 1
        indent = m.group(1)
        block = Block(n=_counter[0], filename=filename, directory=directory, line=line_no)
        _counter[0] += 1
        _parse_header(block, header, line_no)
        body = []
        j = i + 1
        while j < len(lines) and not _END_RE.match(lines[j]):
            body.append((j + 1, lines[j]))
            j += 1
        if j >= len(lines):
            raise AsmError("asm: falta el end del bloque asm", line_no, len(indent) + 1)
        _parse_body(block, body)
        BLOCKS[block.n] = block
        args = ", ".join([str(block.n)] + [e for _, e in block.ins])
        call = f"{indent}__dash_asm({args})"
        for k, (var, _) in enumerate(block.outs):
            call += f" {var} = __dash_asm_out({block.n}, {k})"
        out.append(call)
        out.extend([""] * (j - i))          # the body and the end
        i = j + 1
    result = "\n".join(out)
    if len(_memo) > 256:
        _memo.clear()
    _memo[key] = result
    return result


def _parse_header(block: Block, header: str, line: int):
    sections = _header_sections(header, line)
    seen = set()
    if "in" in sections:
        for item in _split_top(sections["in"]):
            m = re.match(r"^\s*([A-Za-z0-9]+)\s*=(?!=)(.*)$", item)
            if not m or not m.group(2).strip():
                raise AsmError(f"asm: operando no válido: {item.strip()}", line)
            reg = _bind_reg(m.group(1), line)
            if reg in seen:
                raise AsmError(f"asm: el registro {reg} se repite", line)
            seen.add(reg)
            block.ins.append((reg, m.group(2).strip()))
    if "out" in sections:
        out_regs, out_vars = set(), set()
        for item in _split_top(sections["out"]):
            m = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=(?!=)\s*([A-Za-z0-9]+)\s*$", item)
            if not m:
                raise AsmError(f"asm: operando no válido: {item.strip()}", line)
            reg = _bind_reg(m.group(2), line)
            if reg in out_regs:
                raise AsmError(f"asm: el registro {reg} se repite", line)
            if m.group(1) in out_vars:
                raise AsmError(f"asm: la variable {m.group(1)} se repite", line)
            out_regs.add(reg)
            out_vars.add(m.group(1))
            block.outs.append((m.group(1), reg))
    if "uses" in sections:
        if not sections["uses"].strip():
            raise AsmError("asm: operando no válido: uses", line)
        for reg in _reg_list(sections["uses"], line, block.fuses):
            if reg not in block.uses:
                block.uses.append(reg)


# ---- the body ----

_CC = ["t", "f", "hi", "ls", "cc", "cs", "ne", "eq", "vc", "vs", "pl", "mi", "ge", "lt", "gt", "le"]
_CC_ALIAS = {"hs": "cc", "lo": "cs"}

# mnemonic -> (sizes, operand counts); "" in sizes: no suffix. 68020-only ones are in _M020.
MNEMONICS: Dict[str, Tuple[str, Tuple[int, ...]]] = {}


def _m(names, sizes, counts):
    for name in names.split():
        MNEMONICS[name] = (sizes, counts)


_m("abcd sbcd nbcd", "b", (2,))
MNEMONICS["nbcd"] = ("b", (1,))
_m("add sub and or eor cmp addi subi andi ori eori cmpi addq subq addx subx move", "bwl", (2,))
_m("adda suba cmpa movea movep", "wl", (2,))
_m("cmpm", "bwl", (2,))
_m("asl asr lsl lsr rol ror roxl roxr", "bwl", (1, 2))
_m("bchg bclr bset btst", "bl", (2,))
_m("chk divs divu muls mulu", "wl", (2,))
_m("divsl divul", "l", (2,))
_m("clr neg negx not tst", "bwl", (1,))
_m("exg", "l", (2,))
_m("ext", "wl", (1,))
_m("extb", "l", (1,))
_m("swap", "w", (1,))
_m("tas", "b", (1,))
_m("illegal nop reset rte rtr rts trapv", "", (0,))
_m("jmp jsr", "", (1,))
_m("pea", "l", (1,))
_m("lea", "l", (2,))
_m("link", "wl", (2,))
_m("unlk", "", (1,))
_m("movem", "wl", (2,))
_m("moveq", "l", (2,))
_m("stop rtd trap", "", (1,))
_m("bftst bfchg bfclr bfset", "", (1,))
_m("bfextu bfexts bfffo bfins", "", (2,))
for _c in _CC[2:] + list(_CC_ALIAS) + ["ra", "sr"]:
    MNEMONICS["b" + _c] = ("sbwl", (1,))
for _c in _CC + list(_CC_ALIAS) + ["ra"]:
    MNEMONICS["db" + _c] = ("w", (2,))
for _c in _CC + list(_CC_ALIAS):
    MNEMONICS["s" + _c] = ("b", (1,))
DIRECTIVES = {"dc": ("bwlsd", None), "ds": ("bwl", (1,)), "even": ("", (0,)), "incbin": ("", (1, 2, 3)),
              "cnop": ("", (2,)), "section": ("", (2,))}
# the sections (section name,type or the type alone): the code, data, chip data, bss and chip bss
SECTION_KINDS = {"code": "code", "text": "code", "data": "data", "data_c": "data_c", "bss": "bss", "bss_c": "bss_c"}
for _k in SECTION_KINDS:
    DIRECTIVES[_k] = ("", (0,))
_AS_SECTION = {"data": ".section .data", "data_c": ".section .datachip", "bss": ".section .bss",
               "bss_c": ".section .bsschip"}   # (this as has no .pushsection: back with .text)
# the library bases a block can name (move.l GfxBase,a6): the runtime opens them
LIBRARY_BASES = ("SysBase", "DOSBase", "GfxBase", "IntuitionBase")
_M020 = {"divsl", "divul", "extb", "rtd", "bftst", "bfchg", "bfclr", "bfset", "bfextu", "bfexts", "bfffo", "bfins"}
_M020_LONG = {"muls", "mulu", "divs", "divu", "chk", "link"}       # with .l
_BRANCHES = {"b" + c for c in _CC[2:] + list(_CC_ALIAS) + ["ra", "sr"]}
_ALIAS = {"bhs": "bcc", "blo": "bcs", "dbhs": "dbcc", "dblo": "dbcs", "shs": "scc", "slo": "scs"}

_LABEL_RE = re.compile(r"[A-Za-z_.][A-Za-z0-9_]*")


def _strip_asm_comment(text: str) -> str:
    quote = None
    for i, c in enumerate(text):
        if quote:
            if c == quote:
                quote = None
        elif c in "\"'":
            quote = c
        elif c == ";":
            return text[:i]
    return text


def _section_of(op: str, operands: List[str], line_no: int, col: int) -> str:
    """The section a section/code/data... line goes to (dashc's section())."""
    if op != "section":
        return SECTION_KINDS[op]
    t = operands[1].strip().lower()
    if t in SECTION_KINDS:
        return SECTION_KINDS[t]
    if t in ("code_c", "code_f", "data_f", "bss_f"):
        raise AsmError(f"asm: la sección {operands[1].strip()} no se admite: code, data, bss, data_c o bss_c",
                       line_no, col)
    raise AsmError(f"asm: tipo de sección no válido: {operands[1].strip()} (code, data, bss, data_c o bss_c)",
                   line_no, col)


def _parse_body(block: Block, body):
    pending: List[str] = []
    sec = "code"
    for line_no, raw in body:
        text = raw.rstrip("\r")
        if text.strip().startswith("*"):
            continue
        text = _strip_asm_comment(text).rstrip()
        if not text.strip():
            continue
        col = len(text) - len(text.lstrip()) + 1
        rest = text
        labels = []
        # NAME equ value / NAME = value
        m = re.match(r"^\s*([A-Za-z_.][A-Za-z0-9_]*)\s*:?\s*(?:(?i:equ)\b|=(?!=))(.*)$", rest)
        if m:
            name = m.group(1)
            if name in block.equs or name in block.labels:
                raise AsmError(f"asm: {name} ya está definido", line_no, col)
            ln = Line(line=line_no, col=col, op="equ", operands=[m.group(2).strip()], equ=name)
            if not ln.operands[0]:
                raise AsmError(f"asm: operando no válido: {text.strip()}", line_no, col)
            block.equs[name] = ln
            continue
        m = re.match(r"^\s*([A-Za-z_.][A-Za-z0-9_]*):", rest)
        if m:
            labels.append(m.group(1))
            rest = rest[m.end():]
        elif rest[:1] not in (" ", "\t"):
            m = _LABEL_RE.match(rest)
            if not m:
                raise AsmError(f"asm: operando no válido: {text.strip()}", line_no, col)
            labels.append(m.group(0))
            rest = rest[m.end():]
        for name in labels:
            if name in block.labels or name in block.equs:
                raise AsmError(f"asm: {name} ya está definido", line_no, col)
            block.labels[name] = line_no
            block.label_sec[name] = sec
        rest = rest.strip()
        if not rest:
            block.lines.append(Line(line=line_no, col=col, labels=labels))
            continue
        m = re.match(r"^([A-Za-z][A-Za-z0-9_]*)(?:\.([A-Za-z]))?(?=\s|$)", rest)
        if not m:
            raise AsmError(f"asm: instrucción desconocida: {rest.split()[0]}", line_no, col)
        op = m.group(1).lower()
        size = (m.group(2) or "").lower()
        if op not in MNEMONICS and op not in DIRECTIVES:
            raise AsmError(f"asm: instrucción desconocida: {m.group(1)}", line_no, col)
        sizes, counts = MNEMONICS.get(op) or DIRECTIVES[op]
        if size and size not in sizes:
            raise AsmError(f"asm: tamaño .{size} no válido en {op}", line_no, col)
        if op in ("dc", "ds") and not size:
            size = "w"
        ops_text = rest[m.end():].strip()
        operands = [o.strip() for o in _split_top(ops_text)] if ops_text else []
        if counts is not None and len(operands) not in counts:
            # (the texts of dashc: nops, nops2)
            if op == "incbin":
                want = "de 1 a 3 operandos"
            elif len(counts) == 1:
                want = f"{counts[0]} operando" + ("" if counts[0] == 1 else "s")
            else:
                want = " o ".join(str(c) for c in counts) + " operandos"
            raise AsmError(f"asm: {op} pide {want}", line_no, col)
        if op == "dc" and not operands:
            raise AsmError("asm: dc pide al menos un valor", line_no, col)
        if any(not o for o in operands):
            raise AsmError(f"asm: operando no válido: {ops_text}", line_no, col)
        block.lines.append(Line(line=line_no, col=col, labels=labels, op=op, size=size, operands=operands))
        if op == "section" or op in SECTION_KINDS:
            if size:
                raise AsmError(f"asm: tamaño .{size} no válido en {op}", line_no, col)
            sec = _section_of(op, operands, line_no, col)
            if op == "section" or sec != "code":
                block.sections = True


# ---- expressions ----

_TOKEN = re.compile(r"\s*(?:(\$[0-9A-Fa-f]+|0[xX][0-9A-Fa-f]+|%[01]+|0[bB][01]+|\d+)|('(?:[^'])*'|\"[^\"]*\")"
                    r"|([A-Za-z_.][A-Za-z0-9_]*)|(<<|>>|[-+*/&|^~()]))")


class Value:
    """A number plus labels with a coefficient (label - label is a number for the assembler)."""

    def __init__(self, k: int = 0, labels: Optional[Dict[str, int]] = None):
        self.k = k
        self.labels = {n: c for n, c in (labels or {}).items() if c}

    def const(self) -> bool:
        return not self.labels

    def rel(self) -> int:
        """How many labels it adds (dashc's rel): 0 for a number or a difference of labels."""
        return sum(self.labels.values())


class _Expr:
    def __init__(self, text: str, resolve, err):
        self.toks = []
        pos = 0
        text = text.strip()
        while pos < len(text):
            m = _TOKEN.match(text, pos)
            if not m or m.end() == pos:
                err()
            if m.group(1):
                t = m.group(1)
                if t[0] == "$":
                    v = int(t[1:], 16)
                elif t[:2] in ("0x", "0X"):
                    v = int(t[2:], 16)
                elif t[0] == "%":
                    v = int(t[1:], 2)
                elif t[:2] in ("0b", "0B"):
                    v = int(t[2:], 2)
                else:
                    v = int(t)
                self.toks.append(("n", v))
            elif m.group(2):
                s = m.group(2)[1:-1]
                if not 1 <= len(s) <= 4:
                    err()
                v = 0
                for ch in s:
                    v = v << 8 | (ord(ch) & 0xFF)
                self.toks.append(("n", v))
            elif m.group(3):
                self.toks.append(("id", m.group(3)))
            else:
                self.toks.append(("op", m.group(4)))
            pos = m.end()
            while pos < len(text) and text[pos] in " \t":
                pos += 1
        self.i = 0
        self.resolve, self.err = resolve, err

    def parse(self) -> Value:
        if not self.toks:
            self.err()
        v = self._binary(0)
        if self.i != len(self.toks):
            self.err()
        return v

    _PREC = [("|",), ("^",), ("&",), ("<<", ">>"), ("+", "-"), ("*", "/")]

    def _peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else (None, None)

    def _binary(self, level) -> Value:
        if level == len(self._PREC):
            return self._unary()
        left = self._binary(level + 1)
        while True:
            kind, t = self._peek()
            if kind != "op" or t not in self._PREC[level]:
                return left
            self.i += 1
            right = self._binary(level + 1)
            left = self._apply(t, left, right)

    def _apply(self, op, a: Value, b: Value) -> Value:
        if op == "+":
            labels = dict(a.labels)
            for n, c in b.labels.items():
                labels[n] = labels.get(n, 0) + c
            return Value(a.k + b.k, labels)
        if op == "-":
            labels = dict(a.labels)
            for n, c in b.labels.items():
                labels[n] = labels.get(n, 0) - c
            return Value(a.k - b.k, labels)
        if not (a.const() and b.const()):
            self.err()
        x, y = a.k, b.k
        if op == "*":
            return Value(x * y)
        if op == "/":
            if y == 0:
                self.err()
            return Value(int(x / y))
        if op == "<<":
            return Value(x << y if 0 <= y < 64 else 0)
        if op == ">>":
            return Value(x >> y if 0 <= y < 64 else 0)
        return Value({"&": x & y, "|": x | y, "^": x ^ y}[op])

    def _unary(self) -> Value:
        kind, t = self._peek()
        if kind == "op" and t in ("-", "+", "~"):
            self.i += 1
            v = self._unary()
            if t == "+":
                return v
            if t == "-":
                return Value(-v.k, {n: -c for n, c in v.labels.items()})
            if not v.const():
                self.err()
            return Value(~v.k)
        if kind == "op" and t == "(":
            self.i += 1
            v = self._binary(0)
            if self._peek() != ("op", ")"):
                self.err()
            self.i += 1
            return v
        if kind == "n":
            self.i += 1
            return Value(t)
        if kind == "id":
            self.i += 1
            return self.resolve(t)
        self.err()


# ---- operands ----

_REG_ORDER = [f"d{i}" for i in range(8)] + [f"a{i}" for i in range(8)]
_INDEX_RE = re.compile(r"^(d[0-7]|a[0-7]|sp)(?:\.([wl]))?(?:\*([1248]))?$", re.I)
_SPECIAL = {"sr", "ccr", "usp", "pc"}


@dataclass
class Operand:
    kind: str                    # dn an imm abs ind postinc predec disp index pcdisp pcindex reglist special pair bf
    text: str                    # for as
    value: Optional[Value] = None
    needs_020: bool = False
    base_mode: str = ""          # bf: the mode of the operand with the field


# ---- addressing modes, as dashc names them (dashc/src/asm68k.c: A_ALL, A_DATA...) ----
ALL = {"dn", "an", "ind", "post", "pre", "d16", "idx", "absw", "absl", "pcd", "pcidx", "imm"}
DATA = ALL - {"an"}
MEM = DATA - {"dn"}
CTRL = {"ind", "d16", "idx", "absw", "absl", "pcd", "pcidx"}
ALT = ALL - {"imm", "pcd", "pcidx"}
DALT = DATA & ALT
MALT = MEM & ALT
CALT = CTRL & ALT


def _s32(k: int) -> int:
    """A value as dashc keeps it: 32 bits with sign."""
    k &= 0xFFFFFFFF
    return k - 0x100000000 if k >= 0x80000000 else k


def _nospace(text: str) -> str:
    """An operand as dashc shows it: without spaces outside quotes."""
    out, quote = [], None
    for c in text.strip():
        if quote:
            if c == quote:
                quote = None
        elif c in "\"'":
            quote = c
        elif c in " \t":
            continue
        out.append(c)
    return "".join(out)


def _mode(o) -> str:
    """The mode of an operand with dashc's names (M_DN, M_ABSW...)."""
    k = o.kind
    if k == "abs":
        return "absw" if o.text.lower().endswith(".w") else "absl"
    if k == "special":
        return o.text
    return {"disp": "d16", "index": "idx", "postinc": "post", "predec": "pre", "pcdisp": "pcd",
            "pcindex": "pcidx", "reglist": "list"}.get(k, k)


def _imm_fits(tr, v, nbytes: int):
    """An immediate of nbytes (dashc's out_imm): a label only in a long, and the value has to fit."""
    if v is None:
        return
    if not v.const():
        if nbytes != 4 and v.rel():
            tr._error("asm: una etiqueta como inmediato necesita .l")
        return
    k = _s32(v.k)
    if nbytes == 1 and not -128 <= k <= 255:
        tr._error(f"asm: el valor no cabe en un byte: {k}")
    if nbytes == 2 and not -32768 <= k <= 65535:
        tr._error(f"asm: el valor no cabe en 16 bits: {k}")


class Translator:
    """Checks a block against the program's constants and writes it for binutils' as."""

    def __init__(self, block: Block, consts: Dict[str, int], funcs: Optional[Dict[str, str]] = None):
        self.block, self.consts = block, consts
        self.funcs = funcs or {}                 # Dash function -> its C name (jsr nombre)
        self.func_refs: List[str] = []           # the C names the block uses, in order (asm operands %cN)
        self.cur: Optional[Line] = None
        self.needs_020: List[Tuple[str, int]] = []
        self.needs_fpu: List[Tuple[str, int]] = []
        self.code_align = 2
        self._equ_busy = set()

    def _float_value(self, o: str) -> float:
        """A number for dc.s, dc.d and the FPU's .s/.d/.x immediates: 1.5, -2e3, or an integer expression."""
        t = o.strip()
        body = t.lstrip("+-")
        if body[:1].isdigit() and not body.lower().startswith("0x") and ("." in body or "e" in body.lower()):
            try:
                return float(t)
            except ValueError:
                self._error(f"asm: número no válido: {_nospace(t)}")
        return float(_s32(self.const(t)))

    # names
    def _error(self, msg):
        line = self.cur.line if self.cur else self.block.line
        col = self.cur.col if self.cur else 1
        raise AsmError(msg, line, col)

    def label(self, name: str) -> str:
        if name.startswith("\x00b:"):                 # a library base: its C symbol
            return "_" + name[3:]
        if name.startswith("\x00f:"):                 # a Dash function: an asm operand (codegen puts %cN)
            return f"\x01F{self.func_refs.index(name[3:])}\x01"
        # (a dot inside a name confuses as: .Ld1.x is read as .Ld1 with a size)
        return f".Ld%={'L' + name[1:] if name.startswith('.') else 'N' + name}"

    def section_of(self, name: str) -> str:
        """The section of a label of the block, or ext:name for a function or a library base."""
        if name.startswith("\x00"):
            return "ext:" + name[3:]
        return self.block.label_sec.get(name, "code")

    def net_section(self, v: Value) -> Optional[str]:
        """The section of the label a value points to (None: a number)."""
        for n, c in v.labels.items():
            if c == 1:
                return self.section_of(n)
        return None

    def resolve(self, name: str) -> Value:
        if _reg_name(name) or name.lower() in _SPECIAL:
            self._error(f"asm: operando no válido: {name}")
        if name in self.block.labels:
            return Value(0, {name: 1})
        if name in self.block.equs:
            if name in self._equ_busy:
                self._error(f"asm: operando no válido: {name}")
            self._equ_busy.add(name)
            ln = self.block.equs[name]
            v = self.expr(ln.operands[0], keep_line=True)
            self._equ_busy.discard(name)
            return v
        if name in self.consts:
            return Value(self.consts[name])
        if name in LIBRARY_BASES:
            return Value(0, {"\x00b:" + name: 1})
        if name in self.funcs:
            if self.funcs[name] not in self.func_refs:
                self.func_refs.append(self.funcs[name])
            return Value(0, {"\x00f:" + self.funcs[name]: 1})
        self._error(f"asm: nombre desconocido: {name}")

    def expr(self, text: str, keep_line=False) -> Value:
        def err():
            self._error(f"asm: operando no válido: {text.strip()}")
        v = _Expr(text, self.resolve, err).parse()
        if v.labels:
            sums: Dict[str, int] = {}
            for n, c in v.labels.items():
                sums[self.section_of(n)] = sums.get(self.section_of(n), 0) + c
            if v.rel() not in (0, 1):
                self._error(f"asm: expresión no válida: {_nospace(text)}")
            live = {k: c for k, c in sums.items() if c}
            if len(live) > 1 or any(c not in (0, 1) for c in live.values()):
                if any(c < 0 for c in sums.values()):
                    self._error("asm: solo se restan etiquetas de la misma sección")
                self._error("asm: una etiqueta solo se puede sumar o restar")
            sec = next(iter(live), None)
            if sec and sec.startswith("ext:") and v.k:
                self._error(f"asm: a una función o una base de librería no se le suma nada: {_nospace(text)}")
        return v

    def value_text(self, v: Value) -> str:
        k = v.k & 0xFFFFFFFF
        if k >= 0x80000000:
            k -= 0x100000000
        parts = []
        for n, c in sorted(v.labels.items(), key=lambda x: -x[1]):
            if c not in (1, -1):
                self._error("asm: operando no válido: una etiqueta multiplicada")
            parts.append(("-" if c < 0 else ("+" if parts else "")) + self.label(n))
        if not parts:
            return str(k)
        text = "".join(parts)
        if k:
            text += f"{k:+d}"
        return f"({text})" if len(parts) > 1 or k else text

    def const(self, text: str) -> int:
        v = self.expr(text)
        if not v.const():
            self._error(f"asm: operando no válido: {text.strip()}")
        return v.k

    def operand(self, text: str) -> Operand:
        t = text.strip()
        low = t.lower()
        bad = lambda: self._error(f"asm: operando no válido: {t}")
        if "[" in t:
            bad()
        if t.startswith("#"):
            v = self.expr(t[1:])
            return Operand("imm", "#" + self.value_text(v), v)
        reg = _reg_name(t)
        if reg:
            return Operand("dn" if reg[0] == "d" else "an", reg)
        if low in ("sr", "ccr", "usp"):
            return Operand("special", low)
        # Dh:Dl (muls.l, divs.l)
        m = re.match(r"^(d[0-7])\s*:\s*(d[0-7])$", low)
        if m:
            return Operand("pair", f"{m.group(1)}:{m.group(2)}")
        # register list
        if re.match(r"^(?:d[0-7]|a[0-7]|sp)(?:\s*-\s*(?:d[0-7]|a[0-7]|sp))?"
                    r"(?:\s*/\s*(?:d[0-7]|a[0-7]|sp)(?:\s*-\s*(?:d[0-7]|a[0-7]|sp))?)*$", low):
            parts = []
            for part in low.replace(" ", "").split("/"):
                rr = [_reg_name(x) for x in part.split("-")]
                if len(rr) == 2 and _REG_ORDER.index(rr[0]) > _REG_ORDER.index(rr[1]):
                    bad()
                parts.append("-".join(rr))
            return Operand("reglist", "/".join(parts))
        m = re.match(r"^-\s*\(\s*(a[0-7]|sp)\s*\)$", low)
        if m:
            return Operand("predec", f"-({_reg_name(m.group(1))})")
        m = re.match(r"^\(\s*(a[0-7]|sp)\s*\)(\+)?$", low)
        if m:
            r = _reg_name(m.group(1))
            return Operand("postinc", f"({r})+") if m.group(2) else Operand("ind", f"({r})")
        # bitfield: ea{offset:width}
        m = re.match(r"^(.*)\{\s*([^:{}]+?)\s*:\s*([^:{}]+?)\s*\}$", t, re.S)
        if m:
            base = self.operand(m.group(1))
            if base.kind in ("imm", "an", "postinc", "predec", "reglist", "special", "pair", "bf"):
                bad()
            fields = []
            for f in (m.group(2), m.group(3)):
                r = _reg_name(f)
                if r and r[0] == "d":
                    fields.append(r)
                else:
                    fields.append(str(self.const(f)))
            return Operand("bf", f"{base.text}{{{fields[0]}:{fields[1]}}}",   # (the bf instruction asks for the 68020)
                           base.value, base.needs_020, _mode(base))
        # absolute size suffix
        size_sfx = ""
        m = re.match(r"^(.*)\.([wl])$", t, re.I | re.S)
        if m and not m.group(1).rstrip().endswith((")",)) or (m and re.search(r"\)\s*$", m.group(1)) and
                                                                 not self._is_indirect(m.group(1))):
            body = m.group(1)
            if not self._is_indirect(body):
                v = self.expr(body)
                if m.group(2).lower() == "w":
                    if v.rel():
                        self._error(f"asm: una etiqueta como dirección corta no se admite: {_nospace(t)}")
                    if v.const() and not -32768 <= _s32(v.k) <= 65535:
                        self._error(f"asm: la dirección no cabe en 16 bits: {_nospace(t)}")
                return Operand("abs", f"{self.value_text(v)}.{m.group(2).lower()}", v)
        if t.endswith(")"):
            return self._indirect(t, bad)
        v = self.expr(t)
        return Operand("abs", self.value_text(v), v)

    def _is_indirect(self, t: str) -> bool:
        t = t.strip()
        if not t.endswith(")"):
            return False
        open_at = self._matching_open(t)
        if open_at is None:
            return False
        parts = [p.strip() for p in _split_top(t[open_at + 1:-1])]
        return any(_reg_name(p) or p.lower() == "pc" or _INDEX_RE.match(p) for p in parts)

    @staticmethod
    def _matching_open(t: str) -> Optional[int]:
        depth = 0
        for i in range(len(t) - 1, -1, -1):
            if t[i] == ")":
                depth += 1
            elif t[i] == "(":
                depth -= 1
                if depth == 0:
                    return i
        return None

    def _indirect(self, t: str, bad) -> Operand:
        open_at = self._matching_open(t)
        if open_at is None:
            bad()
        prefix = t[:open_at].strip()
        parts = [p.strip() for p in _split_top(t[open_at + 1:-1])]
        if not self._is_indirect(t):
            v = self.expr(t)
            return Operand("abs", self.value_text(v), v)
        base_i = 0
        if not (_reg_name(parts[0]) or parts[0].lower() == "pc"):
            if prefix:
                bad()
            prefix, base_i = parts[0], 1
        if base_i >= len(parts) or len(parts) - base_i > 2:
            bad()
        base = parts[base_i].lower()
        if base == "pc":
            base_reg = "pc"
        else:
            base_reg = _reg_name(base)
            if not base_reg or base_reg[0] != "a":
                bad()
        disp = self.expr(prefix) if prefix else Value(0)
        index = parts[base_i + 1] if base_i + 1 < len(parts) else None
        need = False
        if base_reg == "pc":
            self._code_label(disp, t)
        if base_reg != "pc" and disp.rel():
            self._error(f"asm: una etiqueta como desplazamiento de An no se admite: {_nospace(t)}")
        if index is None:
            if disp.const() and not -32768 <= _s32(disp.k) <= 32767 and base_reg != "pc":
                self._error(f"asm: el desplazamiento no cabe en 16 bits: {_nospace(t)}")
            kind = "pcdisp" if base_reg == "pc" else "disp"
            if base_reg != "pc" and disp.const() and disp.k == 0 and not prefix:
                return Operand("ind", f"({base_reg})")
            return Operand(kind, f"{self.value_text(disp)}({base_reg})", disp)
        m = _INDEX_RE.match(index)
        if not m:
            bad()
        xr = _reg_name(m.group(1))
        xs = (m.group(2) or "w").lower()
        scale = m.group(3) or "1"
        if scale != "1":
            need = True
        if disp.const() and base_reg != "pc" and not -128 <= disp.k <= 127:
            need = True
        text = f"{self.value_text(disp)}({base_reg},{xr}.{xs}*{scale})"
        return Operand("pcindex" if base_reg == "pc" else "index", text, disp, needs_020=need)

    # instructions
    def translate(self) -> Tuple[str, List[Tuple[str, int]]]:
        """The text for as (lines joined with \\n\\t) and what needs a 68020 (what, line)."""
        out: List[str] = []
        pending: List[str] = []
        odd_of = {k: False for k in ("code", "data", "data_c", "bss", "bss_c")}
        sec = "code"
        entered = set()

        def flush_labels():
            for name in pending:
                out.append(self.label(name) + ":")
            pending.clear()

        def align():
            if odd_of[sec]:
                out.append(".even")
                odd_of[sec] = False

        def flip():
            odd_of[sec] = not odd_of[sec]

        for ln in self.block.lines:
            self.cur = ln
            pending.extend(ln.labels)
            if not ln.op:
                continue
            op, size, ops = ln.op, ln.size, ln.operands
            if op == "section" or op in SECTION_KINDS:
                new = _section_of(op, ops, ln.line, ln.col)
                flush_labels()
                if sec != "code":
                    align()
                    out.append(".text")
                sec = new
                if sec != "code":
                    out.append(_AS_SECTION[sec])
                    if sec not in entered:
                        out.append(".balign 4")
                        entered.add(sec)
                continue
            if op == "cnop":
                off, al = self.const(ops[0]), self.const(ops[1])
                if al not in (2, 4, 8):
                    self._error("asm: cnop alinea a 2, 4 u 8 (los hunks empiezan alineados a 8)")
                if off != 0:
                    self._error("asm: cnop: solo cnop 0,n (el desplazamiento, 0)")
                flush_labels()
                if sec == "code":
                    align()
                    out.append(f".balignw {al},0x4e71")
                    self.code_align = max(self.code_align, al)
                else:
                    out.append(f".balign {al}")
                odd_of[sec] = False
                continue
            if sec in ("bss", "bss_c") and op not in ("ds", "even"):
                self._error("asm: en bss solo van ds, even y cnop")
            if op == "dc" and size in ("s", "d"):
                align()
                flush_labels()
                vals = []
                for o in ops:
                    d = self._float_value(o)
                    if size == "s":
                        try:
                            bits = struct.unpack(">I", struct.pack(">f", d))[0]
                        except OverflowError:
                            bits = 0xFF800000 if d < 0 else 0x7F800000
                        vals.append(str(bits))
                    else:
                        bits = struct.unpack(">Q", struct.pack(">d", d))[0]
                        vals.extend([str(bits >> 32), str(bits & 0xFFFFFFFF)])
                out.append(".long " + ",".join(vals))
                continue
            if op == "dc":
                if size == "b":
                    flush_labels()
                    data = []
                    for o in ops:
                        if o[:1] in ("\"", "'") and o[-1:] == o[:1] and len(o) >= 2:
                            data.extend(str(b) for b in o[1:-1].encode("latin-1", "replace"))
                        else:
                            v = self.expr(o)
                            if v.rel():
                                self._error("asm: una etiqueta en dc va con dc.l")
                            if v.const() and not -128 <= _s32(v.k) <= 255:
                                self._error(f"asm: el valor no cabe en un byte: {_s32(v.k)}")
                            data.append(self.value_text(v))
                    out.append(".byte " + ",".join(data))
                    if len(data) % 2:
                        flip()
                else:
                    align()
                    flush_labels()
                    vals = []
                    for o in ops:
                        v = self.expr(o)
                        if size == "w" and v.rel():
                            self._error("asm: una etiqueta en dc va con dc.l")
                        if size == "w" and not -32768 <= _s32(v.k) <= 65535:
                            self._error(f"asm: el valor no cabe en 16 bits: {_s32(v.k)}")
                        vals.append(self.value_text(v))
                    out.append((".word " if size == "w" else ".long ") + ",".join(vals))
                continue
            if op == "ds":
                count = self.const(ops[0])
                if not 0 <= count <= 0x1000000:
                    self._error("asm: ds: tamaño no válido")
                if size != "b":
                    align()
                flush_labels()
                nbytes = count * {"b": 1, "w": 2, "l": 4}[size]
                if nbytes:
                    out.append(f".skip {nbytes}")
                if size == "b" and count % 2:
                    flip()
                continue
            if op == "even":
                align()
                flush_labels()
                continue
            if op == "incbin":
                path = ops[0]
                if not (len(path) >= 2 and path[0] == path[-1] and path[0] in "\"'"):
                    self._error(f"asm: operando no válido: {path}")
                path = path[1:-1]
                full = path if os.path.isabs(path) else os.path.join(self.block.directory, path)
                if not os.path.isfile(full):
                    self._error(f"asm: no se puede leer {path}")
                size_total = os.path.getsize(full)
                start = self.const(ops[1]) if len(ops) > 1 else 0
                count = self.const(ops[2]) if len(ops) > 2 else size_total - start
                if start < 0 or count < 0 or start + count > size_total:
                    self._error(f"asm: operando no válido: {', '.join(ops[1:])}")
                flush_labels()
                full = os.path.abspath(full).replace("\\", "\\\\").replace('"', '\\"')
                out.append(f'.incbin "{full}",{start},{count}')
                if count % 2:
                    flip()
                continue
            if sec != "code":
                self._error(f"asm: en una sección de datos solo van datos (dc, ds, incbin...): {op}")
            align()
            flush_labels()
            out.append(self.instruction(ln))
            if op in _BRANCHES and size in ("s", "b"):
                self._short_to_next(ln)
        if sec != "code":
            align()
            flush_labels()
            out.append(".text")
            sec = "code"
        align()
        flush_labels()
        self.cur = None
        return "\n\t".join(out), self.needs_020

    def _short_to_next(self, ln: Line):
        """bra.s to the very next instruction: the 68000 reads a 0 there as .w."""
        lines = self.block.lines
        target = ln.operands[0].strip()
        k = lines.index(ln) + 1
        while k < len(lines):
            if target in lines[k].labels:
                self._error("asm: un salto .s no puede ir a la instrucción siguiente")
            if lines[k].op:
                return
            k += 1
        return

    def _020(self, what: str):
        self.needs_020.append((what, self.cur.line))

    def instruction(self, ln: Line) -> str:
        op, size = ln.op, ln.size
        name = _ALIAS.get(op, op)
        operands = []
        for o in ln.operands:
            if op in _BRANCHES or (op.startswith("db") and o is ln.operands[-1]):
                operands.append(self._target(o, op))
                continue
            opd = self.operand(o)
            if opd.needs_020:
                self._020(o.strip())
            operands.append(opd)
        kinds = [o.kind for o in operands]
        texts = [o.text for o in operands]
        if op in _M020 or (op in _M020_LONG and size == "l") or (op in _BRANCHES and size == "l"):
            self._020(f"{op}.{size}" if size else op)
        self._validate(op, size, operands)
        if op in ("add", "sub", "cmp", "and", "or", "eor") and kinds[0] == "imm" and kinds[1] != "an":
            name = op + "i"
        if op in ("asl", "asr", "lsl", "lsr", "rol", "ror", "roxl", "roxr") and kinds == ["dn"]:
            texts = ["#1"] + texts                 # lsl d0: by one
        mn = name + (f".{'s' if size == 'b' and op in _BRANCHES else size}" if size else "")
        return mn + (" " + ",".join(texts) if texts else "")

    # ---- the checks of each instruction, as dashc does them (ins_* in dashc/src/asm68k.c) ----
    def _validate(self, op: str, size: str, operands: List[Operand]):
        ln = self.cur
        raw = [_nospace(o) for o in ln.operands]
        modes = [_mode(o) for o in operands]

        def bad(i):
            self._error(f"asm: operando no válido: {raw[i]}")

        def check(i, mask):
            if modes[i] not in mask:
                bad(i)

        def sizes(ok, default):
            sz = size or default
            if sz not in ok:
                self._error(f"asm: tamaño .{sz} no válido en {op}")
            return sz

        def imm(i, nbytes):
            if modes[i] == "imm":
                _imm_fits(self, operands[i].value, nbytes)

        def need_imm(i):
            if modes[i] != "imm":
                self._error(f"asm: operando no válido: {raw[i]} (va un #inmediato)")

        def no_byte_an(i, sz):
            if modes[i] == "an" and sz == "b":
                self._error("asm: tamaño .b no válido con un registro de direcciones")

        def nbytes(sz):
            return {"b": 1, "w": 2, "l": 4}[sz]

        cc = None
        if op.startswith("s") and op[1:] in _CC + list(_CC_ALIAS):
            cc = "s"
        if op in _BRANCHES:
            return
        if op.startswith("db") and (op[2:] in _CC + list(_CC_ALIAS) or op == "dbra"):
            if modes[0] != "dn":
                bad(0)
            return
        if op in ("move", "movea"):
            if op == "movea" and modes[1] != "an":
                bad(1)
            if modes[1] in ("ccr", "sr"):
                if size and size != "w":
                    self._error(f"asm: tamaño .{size} no válido en {op}")
                check(0, DATA)
                imm(0, 2)
                return
            if modes[0] in ("sr", "ccr"):
                if size and size != "w":
                    self._error(f"asm: tamaño .{size} no válido en {op}")
                if modes[0] == "ccr":
                    self._020("move ccr")
                check(1, DALT)
                return
            if "usp" in modes:
                if size and size != "l":
                    self._error(f"asm: tamaño .{size} no válido en {op}")
                if sorted(modes) != ["an", "usp"]:
                    self._error("asm: operandos no válidos en move")
                return
            if modes[1] == "an":
                sz = sizes("wl", "w")
            else:
                sz = sizes("bwl", "w")
                check(1, DALT)
                no_byte_an(0, sz)
            check(0, ALL)
            imm(0, nbytes(sz))
            return
        if op == "moveq":
            if size and size != "l":
                self._error(f"asm: tamaño .{size} no válido en moveq")
            need_imm(0)
            if modes[1] != "dn":
                bad(1)
            v = operands[0].value
            if not v.const() or not -128 <= _s32(v.k) <= 127:
                self._error("asm: moveq va de -128 a 127")
            return
        if op == "movem":
            sizes("wl", "w")
            if modes[0] in ("dn", "an", "list"):
                check(1, CALT | {"pre"})
            elif modes[1] in ("dn", "an", "list"):
                check(0, CTRL | {"post"})
            else:
                self._error("asm: movem pide una lista de registros")
            return
        if op == "movep":
            sizes("wl", "w")
            if not ((modes[0] == "dn" and modes[1] in ("d16", "ind")) or (modes[1] == "dn" and modes[0] in ("d16", "ind"))):
                self._error("asm: operandos no válidos en movep")
            return
        if op in ("add", "sub", "cmp", "and", "or", "eor", "adda", "suba", "cmpa"):
            if op in ("adda", "suba", "cmpa"):
                if modes[1] != "an":
                    bad(1)
                check(0, ALL)
                op = op[:-1] if op != "cmpa" else "cmp"
                op = {"add": "add", "sub": "sub", "cmp": "cmp"}.get(op, op)
            if modes[1] == "an" and op in ("add", "sub", "cmp"):
                sz = sizes("wl", "w")
                check(0, ALL)
                imm(0, nbytes(sz))
                return
            if modes[0] == "imm" and not (modes[1] == "dn" and op != "eor"):
                self._imm_form({"add": "addi", "sub": "subi", "cmp": "cmpi", "and": "andi", "or": "ori",
                                "eor": "eori"}[op], size, operands, modes, raw)
                return
            sz = sizes("bwl", "w")
            if modes[1] == "dn" and op != "eor":
                check(0, DATA if op in ("and", "or") else ALL)
                no_byte_an(0, sz)
                imm(0, nbytes(sz))
                return
            if modes[0] == "dn" and op != "cmp":
                check(1, DALT if op == "eor" else MALT)
                return
            self._error(f"asm: operandos no válidos en {ln.op}")
        if op in ("addi", "subi", "cmpi", "andi", "ori", "eori"):
            self._imm_form(op, size, operands, modes, raw)
            return
        if op in ("addq", "subq"):
            need_imm(0)
            sz = sizes("bwl", "w")
            check(1, ALT)
            no_byte_an(1, sz)
            v = operands[0].value
            if not v.const() or not 1 <= _s32(v.k) <= 8:
                self._error(f"asm: {op} va de 1 a 8")
            return
        if op in ("addx", "subx", "abcd", "sbcd"):
            if op[1] == "b":
                sizes("b", "b")
            else:
                sizes("bwl", "w")
            if modes not in (["dn", "dn"], ["pre", "pre"]):
                self._error(f"asm: operandos no válidos en {op}")
            return
        if op == "cmpm":
            sizes("bwl", "w")
            if modes != ["post", "post"]:
                self._error("asm: cmpm va con (Ay)+,(Ax)+")
            return
        if op in ("muls", "mulu", "divs", "divu", "divsl", "divul"):
            check(0, DATA)
            sz = sizes("l", "l") if op in ("divsl", "divul") else sizes("wl", "w")
            if sz == "w":
                if modes[1] != "dn":
                    bad(1)
                imm(0, 2)
                return
            if modes[1] == "dn":
                if op in ("divsl", "divul"):
                    self._error(f"asm: {op}.l va con Dr:Dq")
            elif modes[1] != "pair":
                bad(1)
            imm(0, 4)
            return
        if op in ("asl", "asr", "lsl", "lsr", "rol", "ror", "roxl", "roxr"):
            if len(operands) == 1:
                if modes[0] == "dn":
                    sizes("bwl", "w")
                    return
                sizes("w", "w")
                check(0, MALT)
                return
            sizes("bwl", "w")
            if modes[1] != "dn":
                bad(1)
            if modes[0] == "imm":
                v = operands[0].value
                if not v.const() or not 1 <= _s32(v.k) <= 8:
                    self._error(f"asm: la cuenta de {op} va de 1 a 8")
            elif modes[0] != "dn":
                bad(0)
            return
        if op in ("btst", "bchg", "bclr", "bset"):
            want = "l" if modes[1] == "dn" else "b"
            if size and size != want:
                self._error(f"asm: tamaño .{size} no válido en {op}")
            if modes[0] == "dn":
                check(1, DATA if op == "btst" else DALT)
                imm(1, 1)
            elif modes[0] == "imm":
                check(1, (DATA - {"imm"}) if op == "btst" else DALT)
                if not operands[0].value.const():
                    self._error("asm: el número de bit es un número")
            else:
                bad(0)
            return
        if op.startswith("bf"):
            if size:
                self._error(f"asm: tamaño .{size} no válido en {op}")
            if op in ("bfextu", "bfexts", "bfffo"):
                f = 0
                if modes[1] != "dn":
                    bad(1)
            elif op == "bfins":
                f = 1
                if modes[0] != "dn":
                    bad(0)
            else:
                f = 0
            if operands[f].kind != "bf":
                self._error(f"asm: falta el campo {{desplazamiento:ancho}}: {raw[f]}")
            mask = {"dn"} | (CTRL if op in ("bftst", "bfextu", "bfexts", "bfffo") else CALT)
            if operands[f].base_mode not in mask:
                bad(f)
            for i, k in enumerate(operands):
                if k.kind == "bf" and i != f:
                    bad(i)
            return
        if op in ("clr", "neg", "negx", "not", "tst", "nbcd", "tas") or cc == "s":
            if op == "tst":
                if modes[0] in ("an", "imm", "pcd", "pcidx"):
                    self._020("tst con ese operando")
                sz = sizes("bwl", "w")
                check(0, ALL)
            elif op in ("nbcd", "tas") or cc == "s":
                sz = sizes("b", "b")
                check(0, DALT)
            else:
                sz = sizes("bwl", "w")
                check(0, DALT)
            no_byte_an(0, sz)
            imm(0, nbytes(sz))
            return
        if op == "lea":
            sizes("l", "l")
            check(0, CTRL)
            if modes[1] != "an":
                bad(1)
            return
        if op in ("pea", "jmp", "jsr"):
            if op == "pea":
                sizes("l", "l")
            elif size:
                self._error(f"asm: tamaño .{size} no válido en {op}")
            check(0, CTRL)
            return
        if op == "chk":
            sz = sizes("wl", "w")
            check(0, DATA)
            if modes[1] != "dn":
                bad(1)
            imm(0, nbytes(sz))
            return
        if op in ("ext", "extb"):
            if modes[0] != "dn":
                bad(0)
            if op == "extb":
                sizes("l", "l")
            else:
                sizes("wl", "w")
            return
        if op == "swap":
            sizes("w", "w")
            if modes[0] != "dn":
                bad(0)
            return
        if op == "exg":
            sizes("l", "l")
            if not all(m in ("dn", "an") for m in modes):
                self._error("asm: operandos no válidos en exg")
            return
        if op == "link":
            sz = sizes("wl", "w")
            if modes[0] != "an":
                bad(0)
            need_imm(1)
            v = operands[1].value
            if sz == "l":
                _imm_fits(self, v, 4)
            else:
                if v.const() and not -32768 <= _s32(v.k) <= 32767:
                    self._error(f"asm: el valor no cabe en 16 bits: {_s32(v.k)}")
                _imm_fits(self, v, 2)
            return
        if op == "unlk":
            if size:
                self._error(f"asm: tamaño .{size} no válido en unlk")
            if modes[0] != "an":
                bad(0)
            return
        if op in ("trap", "stop", "rtd"):
            if size:
                self._error(f"asm: tamaño .{size} no válido en {op}")
            need_imm(0)
            v = operands[0].value
            if op == "trap":
                if not v.const() or not 0 <= _s32(v.k) <= 15:
                    self._error("asm: trap va de 0 a 15")
            else:
                _imm_fits(self, v, 2)
            return

    def _imm_form(self, op: str, size: str, operands: List[Operand], modes: List[str], raw: List[str]):
        """ori, andi, subi, addi, eori, cmpi: #n,<ea> (and to ccr or sr), as dashc's ins_imm."""
        if modes[0] != "imm":
            self._error(f"asm: operando no válido: {raw[0]} (va un #inmediato)")
        if modes[1] in ("ccr", "sr"):
            if op not in ("ori", "andi", "eori"):
                self._error(f"asm: operando no válido: {raw[1]}")
            want = "b" if modes[1] == "ccr" else "w"
            if size and size != want:
                self._error(f"asm: tamaño .{size} no válido en {self.cur.op}")
            _imm_fits(self, operands[0].value, 1 if modes[1] == "ccr" else 2)
            return
        sz = size or "w"
        if sz not in "bwl":
            self._error(f"asm: tamaño .{sz} no válido en {self.cur.op}")
        if op == "cmpi" and modes[1] in ("pcd", "pcidx"):
            self._020("cmpi con (pc)")
        elif modes[1] not in DALT:
            self._error(f"asm: operando no válido: {raw[1]}")
        _imm_fits(self, operands[0].value, {"b": 1, "w": 2, "l": 4}[sz])

    def _target(self, text: str, op: str):
        v = self.expr(text)
        sec = self.net_section(v)
        if sec and sec.startswith("ext:"):
            self._error(f"asm: a una función se llega con jsr, no con un salto: {_nospace(text)}")
        if len(v.labels) != 1 or list(v.labels.values())[0] != 1 or sec != "code":
            self._error(f"asm: un salto va a una etiqueta del código del bloque: {_nospace(text)}")
        return Operand("target", self.value_text(v), v)

    def _code_label(self, v: Value, text: str):
        """(pc): only to the block's code (dashc's code_label)."""
        sec = self.net_section(v)
        if sec and sec != "code":
            if sec.startswith("ext:"):
                self._error(f"asm: a una función se llega con jsr (sin pc): {_nospace(text)}")
            self._error(f"asm: (pc) y los saltos solo llegan al código del bloque, no a otra sección: {_nospace(text)}")


def check(block: Block, consts: Dict[str, int], funcs: Optional[Dict[str, str]] = None):
    """Raises AsmError on the first problem (names, operands) of a block."""
    Translator(block, consts, funcs).translate()


def translate(block: Block, consts: Dict[str, int]) -> Tuple[str, List[Tuple[str, int]]]:
    return Translator(block, consts).translate()


def translator(block: Block, consts: Dict[str, int], funcs: Optional[Dict[str, str]] = None) -> "Translator":
    """The block for as: .text (the lines), .needs_020, .needs_fpu, .func_refs (C names, the \\x01Fk\\x01 of the
    text) and .code_align (its largest cnop)."""
    tr = Translator(block, consts, funcs)
    tr.text, _ = tr.translate()
    return tr


def c_string(text: str) -> str:
    """The as text as a C literal, for an asm template with operands (% doubled, but not %=)."""
    text = text.replace("%", "%%").replace("%%=", "%=")
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t") + '"'
