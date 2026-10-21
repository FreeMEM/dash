"""Dash for gdb (m68k-amigaos-gdb -x tools/gdb/dash.py): the values of a Dash program as Dash shows them,
and its stack without the runtime. The VS Code extension loads it in its debugger (docs/IDE_LOOP.md).

- String (STRPTR): "texto", or nil.
- Lists ([T], DashArrayLong *): their elements, as Ints, Strings or objects (by kind, the top byte of capacity).
- Dictionaries ({String: T}, DashDict *): key -> value.
- Structs (_Dash_X *): their fields, or nil. An object in a list is told by its header: the destroy
  function it was made with (_dash_struct_destroy_X), else the only struct of its size.
- Fixed (DashFixed, 16.16): its decimal value. Bool (BOOL): true or false.
- Steps (F11) go only into functions of a .dash (gdb skip), not into the runtime.
- Frames: the runtime's (_dash_*, DashString_*...) leave the stack unless they are the innermost one (not even
  then when it stopped on an error of the program, in _dash_debug_stop: the stack starts at its Dash line), and
  the C temporaries (_dash_*) leave the locals.
"""
import re
import struct

import gdb
from gdb.FrameDecorator import FrameDecorator

MAX_CHILDREN = 200
MAX_DICT_CHILDREN = 100      # (the debugger's panel asks for all the entries of a dictionary at once; d["k"] for the rest)
RUNTIME = re.compile(r"^(_dash_|Dash[A-Z]|_Dash_RefHeader|__)")


def _is_nil(val):
    try:
        return int(val) == 0
    except gdb.error:
        return False


def _read(addr, n):
    """n bytes of the program's memory in one go: gdb reads a text a byte at a time, and on the emulated
    Amiga (bgdbserver over its network) each is a round trip: 9000 letters took 52 s."""
    return bytes(gdb.selected_inferior().read_memory(addr, n))


def _longs(addr, n):
    """n LONGs (big-endian, signed) from addr, in one read"""
    return struct.unpack(">%dl" % n, _read(addr, 4 * n)) if n > 0 else ()


def _cstring(addr, limit=1 << 20):
    """The bytes of the C text at addr (up to its 0), read in growing blocks"""
    data, size = b"", 64
    while len(data) < limit:
        chunk = _read(addr + len(data), size)
        end = chunk.find(b"\0")
        if end >= 0:
            return data + chunk[:end]
        data += chunk
        size = min(size * 4, 4096)
    return data[:limit]


def _dict_hash(key):
    """_dash_dict_hash of the runtime (djb2 on the Latin-1 bytes, 32 bits)"""
    h = 5381
    for b in key:
        h = (h * 33 + b) & 0xFFFFFFFF
    return h


def _text(ptr):
    """A C text as Dash writes it: "..." (Latin-1, the Amiga's); the first 400 letters, read in two goes."""
    if _is_nil(ptr):
        return "nil"
    addr = int(ptr) & 0xFFFFFFFF
    data = b""
    try:
        for size in (64, 337):
            data += _read(addr + len(data), size)
            if b"\0" in data:
                break
    except gdb.MemoryError:
        if not data:
            return "<texto ilegible>"
    end = data.find(b"\0")
    s = data[:end if end >= 0 else 400].decode("latin-1")
    if end < 0 or end > 400:
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


class ListPrinter(gdb.ValuePrinter):
    """(gdb.ValuePrinter with num_children and child: the debugger's panel counts the elements without reading
    them, and asks for them a page at a time; before, the Locals of a stop read every one of every list)"""

    def __init__(self, val):
        self.val = val
        self._raw = None

    def to_string(self):
        if _is_nil(self.val):
            return "nil"
        return "lista de %d" % int(self.val["length"])

    def num_children(self):
        return 0 if _is_nil(self.val) else min(int(self.val["length"]), MAX_CHILDREN)

    def _elements(self):
        if self._raw is None:                          # all of them in one read, the first time
            arr = self.val.dereference()
            self._kind = (int(arr["capacity"]) & 0xFFFFFFFF) >> 24
            self._type = arr["data"].type.target()
            self._raw = _longs(int(arr["data"]) & 0xFFFFFFFF, self.num_children())
        return self._raw

    def child(self, i):
        return "[%d]" % i, _element(gdb.Value(self._elements()[i]).cast(self._type), self._kind)

    def children(self):
        for i in range(self.num_children()):
            yield self.child(i)

    def display_hint(self):
        return "array"


class DictPrinter(gdb.ValuePrinter):
    def __init__(self, val):
        self.val = val
        self._slots = None

    def to_string(self):
        if _is_nil(self.val):
            return "nil"
        return "diccionario de %d" % int(self.val["count"])

    def _used(self):
        """[(key pointer, raw value)] of the slots in use, up to MAX_DICT_CHILDREN: the keys read in blocks of 64
        slots until there are enough, and the values of those blocks (one key at a time, 500 of them took 24 s;
        the whole arrays, 8 KB through the emulated network, 6 s)"""
        if self._slots is None:
            d = self.val.dereference()
            cap = int(d["cap"])
            keys_at, vals_at = int(d["keys"]) & 0xFFFFFFFF, int(d["vals"]) & 0xFFFFFFFF
            self._kind = int(d["kind"])
            self._type = d["vals"].type.target()
            self._slots = []
            for start in range(0, cap, 64):
                n = min(64, cap - start)
                keys = _longs(keys_at + 4 * start, n)
                if not any(keys):
                    continue
                vals = _longs(vals_at + 4 * start, n)
                self._slots += [(keys[i] & 0xFFFFFFFF, vals[i]) for i in range(n) if keys[i]]
                if len(self._slots) >= MAX_DICT_CHILDREN:
                    break
            self._slots = self._slots[:MAX_DICT_CHILDREN]
        return self._slots

    def num_children(self):         # (from its count: the slots are read when a child is asked for)
        return 0 if _is_nil(self.val) else 2 * min(int(self.val["count"]), MAX_DICT_CHILDREN)

    def child(self, i):
        used = self._used()
        if i // 2 >= len(used):
            return "…", gdb.Value(0)
        key, val = used[i // 2]
        if i % 2 == 0:
            return "k%d" % (i // 2), gdb.Value(key).cast(gdb.lookup_type("STRPTR"))
        return "v%d" % (i // 2), _element(gdb.Value(val).cast(self._type), self._kind)

    def children(self):
        for i in range(self.num_children()):
            yield self.child(i)

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
            return len(_cstring(int(x) & 0xFFFFFFFF))         # (a byte at a time: 9000 letters, a minute)
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
            key = want.encode("latin-1", errors="replace")
            cap = int(d["cap"])
            keys = int(d["keys"]) & 0xFFFFFFFF
            # as _dash_dict_slot does: from its hash, the next slots until an empty one (comparing them all
            # one byte at a time took minutes with 500 keys)
            slot = _dict_hash(key) & (cap - 1) if cap else 0
            for _ in range(cap):
                ptr = _longs(keys + 4 * slot, 1)[0] & 0xFFFFFFFF
                if not ptr:
                    break
                if _cstring(ptr, len(key) + 1) == key:
                    return _element(d["vals"][slot], int(d["kind"]))
                slot = (slot + 1) & (cap - 1)
            raise gdb.GdbError("no está la clave %r" % want)
        return x[int(i)]


gdb.pretty_printers.append(lookup)
DashFrames()
LenFunction()
AtFunction()

# A step into a function (F11) goes only into the program's: those of a .dash (the #line of ./dash --debug), not
# into the runtime, the C of a struct (P_retain...) or a library; a breakpoint there still stops
for _skip in ("skip -gfile *.c", "skip -gfile *.h", "skip -rfunction ^(_dash_|Dash[A-Z]|__)"):
    try:
        gdb.execute(_skip, to_string=True)
    except gdb.error:
        pass
