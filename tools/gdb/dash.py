"""Dash for gdb (m68k-amigaos-gdb -x tools/gdb/dash.py): the values of a Dash program as Dash shows them,
and its stack without the runtime. The VS Code extension loads it in its debugger (docs/IDE_LOOP.md).

- String (STRPTR): "texto", or nil.
- Lists ([T], DashArrayLong *): their elements, as Ints, Strings or objects (by kind, the top byte of capacity).
- Dictionaries ({String: T}, DashDict *): key -> value.
- Structs (_Dash_X *): their fields, or nil. An object in a list is told by its header: the destroy
  function it was made with (_dash_struct_destroy_X), else the only struct of its size.
- Fixed (DashFixed, 16.16): its decimal value. Bool (BOOL): true or false.
- Frames: the runtime's (_dash_*, DashString_*...) leave the stack unless they are the innermost one (not even
  then when it stopped on an error of the program, in _dash_debug_stop: the stack starts at its Dash line), and
  the C temporaries (_dash_*) leave the locals.
"""
import re

import gdb
from gdb.FrameDecorator import FrameDecorator

MAX_CHILDREN = 200
RUNTIME = re.compile(r"^(_dash_|Dash[A-Z]|_Dash_RefHeader|__)")


def _is_nil(val):
    try:
        return int(val) == 0
    except gdb.error:
        return False


def _text(ptr):
    """A C text as Dash writes it: "..." (Latin-1, the Amiga's)."""
    if _is_nil(ptr):
        return "nil"
    try:
        s = ptr.cast(gdb.lookup_type("char").pointer()).string(encoding="latin-1", errors="replace", length=-1)
    except gdb.MemoryError:
        return "<texto ilegible>"
    if len(s) > 400:
        s = s[:400] + "…"
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


_struct_sizes = None


def _structs_by_size():
    """size -> [struct names] of the program's structs (_Dash_X)."""
    global _struct_sizes
    if _struct_sizes is None:
        _struct_sizes = {}
        out = gdb.execute("info types ^_Dash_", to_string=True)
        for name in sorted(set(re.findall(r"\b(_Dash_[A-Za-z0-9_]+)\b", out))):
            if name == "_Dash_RefHeader":
                continue
            try:
                t = gdb.lookup_type(name)
                _struct_sizes.setdefault(t.sizeof, []).append(name)
            except gdb.error:
                pass
    return _struct_sizes


def _object(value):
    """An element of kind 1 (a LONG that points to an object): as a struct or a list, if it can be told."""
    if _is_nil(value):
        return None
    addr = int(value) & 0xFFFFFFFF
    try:
        header_type = gdb.lookup_type("_Dash_RefHeader")
        header = gdb.Value(addr - header_type.sizeof).cast(header_type.pointer()).dereference()
        destroy = int(header["destroy"])
        size = int(header["_size"])
    except gdb.error:
        return None
    if destroy:
        block = gdb.block_for_pc(destroy)
        fn = block.function.name if block is not None and block.function is not None else ""
        m = re.match(r"_dash_struct_destroy_(\w+)$", fn)
        if m:
            name = "_Dash_" + m.group(1)
        elif "array" in fn.lower() or "Array" in fn:
            name = "DashArrayLong"
        elif "dict" in fn.lower():
            name = "DashDict"
        else:
            name = None
    else:
        candidates = _structs_by_size().get(size, [])
        name = candidates[0] if len(candidates) == 1 else None
    if name is None:
        return None
    try:
        return gdb.Value(addr).cast(gdb.lookup_type(name).pointer())
    except gdb.error:
        return None


def _element(raw, kind):
    if kind == 2:
        return raw.cast(gdb.lookup_type("STRPTR"))
    if kind == 1:
        obj = _object(raw)
        return obj if obj is not None else raw
    return raw


class StringPrinter:
    def __init__(self, val):
        self.val = val

    def to_string(self):
        return _text(self.val)


class ListPrinter:
    def __init__(self, val):
        self.val = val

    def to_string(self):
        if _is_nil(self.val):
            return "nil"
        return "lista de %d" % int(self.val["length"])

    def children(self):
        if _is_nil(self.val):
            return
        arr = self.val.dereference()
        kind = (int(arr["capacity"]) & 0xFFFFFFFF) >> 24
        for i in range(min(int(arr["length"]), MAX_CHILDREN)):
            yield "[%d]" % i, _element(arr["data"][i], kind)

    def display_hint(self):
        return "array"


class DictPrinter:
    def __init__(self, val):
        self.val = val

    def to_string(self):
        if _is_nil(self.val):
            return "nil"
        return "diccionario de %d" % int(self.val["count"])

    def children(self):
        if _is_nil(self.val):
            return
        d = self.val.dereference()
        kind = int(d["kind"])
        shown = 0
        for i in range(int(d["cap"])):
            key = d["keys"][i]
            if _is_nil(key):
                continue
            yield "k%d" % i, key.cast(gdb.lookup_type("STRPTR"))
            yield "v%d" % i, _element(d["vals"][i], kind)
            shown += 1
            if shown >= MAX_CHILDREN:
                return

    def display_hint(self):
        return "map"


class StructPrinter:
    def __init__(self, val, name):
        self.val = val
        self.name = name

    def to_string(self):
        return "nil" if _is_nil(self.val) else self.name

    def children(self):
        if _is_nil(self.val):
            return
        obj = self.val.dereference()
        for field in obj.type.fields():
            yield field.name, obj[field.name]


class FixedPrinter:
    def __init__(self, val):
        self.val = val

    def to_string(self):
        return ("%.4f" % (int(self.val) / 65536.0)).rstrip("0").rstrip(".")


class BoolPrinter:
    def __init__(self, val):
        self.val = val

    def to_string(self):
        return "true" if int(self.val) else "false"


def lookup(val):
    t = val.type
    if t.code == gdb.TYPE_CODE_TYPEDEF:
        if t.name == "STRPTR":
            return StringPrinter(val)
        if t.name == "DashFixed":
            return FixedPrinter(val)
        if t.name == "BOOL":
            return BoolPrinter(val)
    base = t.strip_typedefs()
    if base.code == gdb.TYPE_CODE_PTR:
        target = base.target()
        name = target.name or target.strip_typedefs().tag or ""
        if name == "DashArrayLong":
            return ListPrinter(val)
        if name == "DashDict":
            return DictPrinter(val)
        if name.startswith("_Dash_") and name != "_Dash_RefHeader":
            return StructPrinter(val, name[len("_Dash_"):])
    return None


class DashFrame(FrameDecorator):
    """A frame without the C temporaries of Dash (_dash_r, _dash_t3...) among its locals."""

    def frame_locals(self):
        items = super().frame_locals()
        return [v for v in (items or []) if not str(v.symbol()).startswith("_dash_")] if items else items


class DashFrames:
    """The stack in Dash: the runtime's frames out, unless one is where the program stopped."""

    def __init__(self):
        self.name = "dash"
        self.priority = 100
        self.enabled = True
        gdb.frame_filters[self.name] = self

    def filter(self, frames):
        first = True
        trap = False                    # stopped by an error of the program (./dash --debug): at its line of Dash
        for frame in frames:
            name = frame.function()
            name = name if isinstance(name, str) else ""
            if first and name == "_dash_debug_stop":
                trap = True
            if (not first or trap) and RUNTIME.match(name):
                continue
            first = False
            yield DashFrame(frame)


def _kind_of(val):
    base = val.type.strip_typedefs()
    if base.code == gdb.TYPE_CODE_PTR:
        target = base.target()
        return target.name or target.strip_typedefs().tag or ""
    return ""


class LenFunction(gdb.Function):
    """$len(x): the length of a list, dictionary or text, as x.length in Dash (the debugger's expressions)."""

    def __init__(self):
        super().__init__("len")

    def invoke(self, x):
        if _is_nil(x):
            return 0
        kind = _kind_of(x)
        if kind == "DashArrayLong":
            return int(x["length"])
        if kind == "DashDict":
            return int(x["count"])
        try:
            return len(x.cast(gdb.lookup_type("char").pointer()).string(encoding="latin-1", errors="replace"))
        except gdb.error:
            raise gdb.GdbError("length: not a list, dictionary or text")


class AtFunction(gdb.Function):
    """$at(x, i): x[i] in Dash: an element of a list (typed as Int, String or object), the value of a
    dictionary's key (a text), or a character of a text."""

    def __init__(self):
        super().__init__("at")

    def invoke(self, x, i):
        if _is_nil(x):
            raise gdb.GdbError("nil")
        kind = _kind_of(x)
        if kind == "DashArrayLong":
            arr = x.dereference()
            n = int(i)
            if not 0 <= n < int(arr["length"]):
                raise gdb.GdbError("índice %d fuera de la lista (de %d)" % (n, int(arr["length"])))
            return _element(arr["data"][n], (int(arr["capacity"]) & 0xFFFFFFFF) >> 24)
        if kind == "DashDict":
            d = x.dereference()
            want = i.string() if i.type.strip_typedefs().code in (gdb.TYPE_CODE_ARRAY, gdb.TYPE_CODE_PTR) else str(i)
            for slot in range(int(d["cap"])):
                key = d["keys"][slot]
                if not _is_nil(key) and key.cast(gdb.lookup_type("char").pointer()).string(
                        encoding="latin-1", errors="replace") == want:
                    return _element(d["vals"][slot], int(d["kind"]))
            raise gdb.GdbError("no está la clave %r" % want)
        return x[int(i)]


gdb.pretty_printers.append(lookup)
DashFrames()
LenFunction()
AtFunction()
