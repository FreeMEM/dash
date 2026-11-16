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
    reg = _reg_name(text)
    if reg is None:
        raise AsmError(f"asm: operando no válido: {text.strip()}", line)
    if reg in ("a5", "a7"):
        raise AsmError(f"asm: el registro {reg} no se puede usar en un bloque asm", line)
    return reg


def _reg_list(text: str, line: int) -> List[str]:
    """d2-d4/a1, d2, d3: the registers of a list (as in movem)."""
    regs = []
    for part in re.split(r"[,/]", text):
        part = part.strip()
        if not part:
            raise AsmError(f"asm: operando no válido: {text.strip()}", line)
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

    def clobbers(self) -> List[str]:
        bound = {r for r, _ in self.ins} | {r for _, r in self.outs}
        return [r for r in ALLOWED if r in self.uses and r not in bound]


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
        while j < len(lines) and lines[j].strip() != "end":
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
        for reg in _reg_list(sections["uses"], line):
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
DIRECTIVES = {"dc": ("bwl", None), "ds": ("bwl", (1,)), "even": ("", (0,)), "incbin": ("", (1, 2, 3))}
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


def _parse_body(block: Block, body):
    pending: List[str] = []
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
        rest = rest.strip()
        if not rest:
            block.lines.append(Line(line=line_no, col=col, labels=labels))
            continue
        m = re.match(r"^([A-Za-z][A-Za-z0-9]*)(?:\.([A-Za-z]))?(?=\s|$)", rest)
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
            want = " o ".join(str(c) for c in counts)
            raise AsmError(f"asm: {op} pide {want} operandos", line_no, col)
        if op == "dc" and not operands:
            raise AsmError("asm: dc pide 1 o más operandos", line_no, col)
        if any(not o for o in operands):
            raise AsmError(f"asm: operando no válido: {ops_text}", line_no, col)
        block.lines.append(Line(line=line_no, col=col, labels=labels, op=op, size=size, operands=operands))


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

_INDEX_RE = re.compile(r"^(d[0-7]|a[0-7]|sp)(?:\.([wl]))?(?:\*([1248]))?$", re.I)
_SPECIAL = {"sr", "ccr", "usp", "pc"}


@dataclass
class Operand:
    kind: str                    # dn an imm abs ind postinc predec disp index pcdisp pcindex reglist special pair bf
    text: str                    # for as
    value: Optional[Value] = None
    needs_020: bool = False


class Translator:
    """Checks a block against the program's constants and writes it for binutils' as."""

    def __init__(self, block: Block, consts: Dict[str, int]):
        self.block, self.consts = block, consts
        self.cur: Optional[Line] = None
        self.needs_020: List[Tuple[str, int]] = []
        self._equ_busy = set()

    # names
    def _error(self, msg):
        line = self.cur.line if self.cur else self.block.line
        col = self.cur.col if self.cur else 1
        raise AsmError(msg, line, col)

    def label(self, name: str) -> str:
        # (a dot inside a name confuses as: .Ld1.x is read as .Ld1 with a size)
        return f".Ld%={'L' + name[1:] if name.startswith('.') else 'N' + name}"

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
        self._error(f"asm: nombre desconocido: {name}")

    def expr(self, text: str, keep_line=False) -> Value:
        def err():
            self._error(f"asm: operando no válido: {text.strip()}")
        return _Expr(text, self.resolve, err).parse()

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
                if len(rr) == 2 and (rr[0][0] != rr[1][0] or rr[0] > rr[1]):
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
            return Operand("bf", f"{base.text}{{{fields[0]}:{fields[1]}}}")   # (the bf instruction asks for the 68020)
        # absolute size suffix
        size_sfx = ""
        m = re.match(r"^(.*)\.([wl])$", t, re.I | re.S)
        if m and not m.group(1).rstrip().endswith((")",)) or (m and re.search(r"\)\s*$", m.group(1)) and
                                                                 not self._is_indirect(m.group(1))):
            body = m.group(1)
            if not self._is_indirect(body):
                v = self.expr(body)
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
        if index is None:
            if disp.const() and not -32768 <= disp.k <= 32767 and base_reg != "pc":
                bad()
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
        odd = False

        def flush_labels():
            for name in pending:
                out.append(self.label(name) + ":")
            pending.clear()

        def align():
            nonlocal odd
            if odd:
                out.append(".even")
                odd = False

        for ln in self.block.lines:
            self.cur = ln
            pending.extend(ln.labels)
            if not ln.op:
                continue
            op, size, ops = ln.op, ln.size, ln.operands
            if op == "dc":
                if size == "b":
                    flush_labels()
                    data = []
                    for o in ops:
                        if o[:1] in ("\"", "'") and o[-1:] == o[:1] and len(o) >= 2:
                            data.extend(str(b) for b in o[1:-1].encode("latin-1", "replace"))
                        else:
                            v = self.expr(o)
                            if v.const() and not -128 <= v.k <= 255:
                                self._error(f"asm: operando no válido: {o}")
                            data.append(self.value_text(v))
                    out.append(".byte " + ",".join(data))
                    if len(data) % 2:
                        odd = not odd
                else:
                    align()
                    flush_labels()
                    vals = []
                    for o in ops:
                        v = self.expr(o)
                        if size == "w" and v.const() and not -32768 <= v.k <= 65535:
                            self._error(f"asm: operando no válido: {o}")
                        vals.append(self.value_text(v))
                    out.append((".word " if size == "w" else ".long ") + ",".join(vals))
                continue
            if op == "ds":
                count = self.const(ops[0])
                if count < 0:
                    self._error(f"asm: operando no válido: {ops[0]}")
                if size != "b":
                    align()
                flush_labels()
                nbytes = count * {"b": 1, "w": 2, "l": 4}[size]
                if nbytes:
                    out.append(f".skip {nbytes}")
                if size == "b" and count % 2:
                    odd = not odd
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
                    odd = not odd
                continue
            align()
            flush_labels()
            out.append(self.instruction(ln))
            if op in _BRANCHES and size in ("s", "b"):
                self._short_to_next(ln)
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
        if "pair" in kinds and not (op in ("muls", "mulu", "divs", "divu", "divsl", "divul") and size == "l"
                                    and kinds[-1] == "pair"):
            self._error(f"asm: operando no válido: {ln.operands[kinds.index('pair')]}")
        if op in ("muls", "mulu", "divs", "divu") and size == "l" and kinds[-1] == "pair":
            pass
        if op in ("divsl", "divul") and kinds[-1] != "pair":
            self._error(f"asm: operando no válido: {ln.operands[-1]}")
        if "bf" in kinds and not op.startswith("bf"):
            self._error(f"asm: operando no válido: {ln.operands[kinds.index('bf')]}")
        if op.startswith("bf") and kinds[0] != "bf" and not (op == "bfins" and kinds[1] == "bf"):
            self._error(f"asm: operando no válido: {ln.operands[0]}")
        if "reglist" in kinds and op != "movem":
            self._error(f"asm: operando no válido: {ln.operands[kinds.index('reglist')]}")
        if op == "moveq":
            if kinds[0] != "imm" or kinds[1] != "dn":
                self._error(f"asm: operando no válido: {ln.operands[0] if kinds[0] != 'imm' else ln.operands[1]}")
            v = operands[0].value
            if not v.const() or not -128 <= v.k <= 127:
                self._error("asm: moveq va de -128 a 127")
        if op in ("addq", "subq"):
            v = operands[0].value
            if kinds[0] != "imm" or not v.const() or not 1 <= v.k <= 8:
                self._error(f"asm: operando no válido: {ln.operands[0]}")
        if op.startswith("db") and kinds[0] != "dn":
            self._error(f"asm: operando no válido: {ln.operands[0]}")
        if op == "lea" and kinds[1] != "an":
            self._error(f"asm: operando no válido: {ln.operands[1]}")
        if op in ("trap",):
            v = operands[0].value
            if kinds[0] != "imm" or not v.const() or not 0 <= v.k <= 15:
                self._error(f"asm: operando no válido: {ln.operands[0]}")
        # what cannot be written: a number or something read through pc
        if len(kinds) == 2 and kinds[1] in ("imm", "pcdisp", "pcindex") and op not in ("link", "btst", "cmp", "cmpi"):
            self._error(f"asm: operando no válido: {ln.operands[1]}")
        if len(kinds) == 1 and op not in _BRANCHES:
            if kinds[0] == "imm" and op not in ("stop", "rtd", "trap", "tst"):
                self._error(f"asm: operando no válido: {ln.operands[0]}")
            if kinds[0] in ("pcdisp", "pcindex") and op not in ("jmp", "jsr", "pea", "tst") and not op.startswith("bf"):
                self._error(f"asm: operando no válido: {ln.operands[0]}")
        if op in ("add", "sub", "cmp", "and", "or", "eor") and kinds[0] == "imm" and kinds[1] != "an":
            name = op + "i"
        if op in ("asl", "asr", "lsl", "lsr", "rol", "ror", "roxl", "roxr") and kinds == ["dn"]:
            texts = ["#1"] + texts                 # lsl d0: by one
        mn = name + (f".{'s' if size == 'b' and op in _BRANCHES else size}" if size else "")
        return mn + (" " + ",".join(texts) if texts else "")

    def _target(self, text: str, op: str):
        v = self.expr(text)
        if len(v.labels) != 1 or list(v.labels.values())[0] != 1:
            self._error(f"asm: operando no válido: {text.strip()}")
        return Operand("target", self.value_text(v), v)


def check(block: Block, consts: Dict[str, int]):
    """Raises AsmError on the first problem (names, operands) of a block."""
    Translator(block, consts).translate()


def translate(block: Block, consts: Dict[str, int]) -> Tuple[str, List[Tuple[str, int]]]:
    return Translator(block, consts).translate()


def c_string(text: str) -> str:
    """The as text as a C literal, for an asm template with operands (% doubled, but not %=)."""
    text = text.replace("%", "%%").replace("%%=", "%=")
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t") + '"'
