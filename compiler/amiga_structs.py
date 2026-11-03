"""@amiga struct (docs/AARCH64_LOOP.md, A6): views of memory with the 68000 layout, for the Amiga box of DashOS (and
for AmigaOS's own structures on the Amiga).

    @amiga struct Node
        ln_Succ: Ptr Node
        ln_Type: UByte
        ...
    end

Field types: Byte, UByte, Word, UWord, Long, ULong (read as an Int, written cut to their size), Ptr T (a 32-bit
address of an @amiga struct T or of one of those scalars), BPtr (a dos.library pointer: the address >> 2), another
@amiga struct by value, and tables (UByte[16]). Layout of the 68000: Byte and UByte aligned to 1, the rest to 2;
the size rounded up to 2. A value of type "Ptr T" is an address; "Ptr T(x)" takes it from an Int."""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# scalar: (bytes, signed, C type)
SCALARS = {"Byte": (1, True, "BYTE"), "UByte": (1, False, "UBYTE"), "Word": (2, True, "WORD"),
           "UWord": (2, False, "UWORD"), "Long": (4, True, "LONG"), "ULong": (4, False, "ULONG"),
           "Int": (4, True, "LONG")}


@dataclass
class FieldInfo:
    name: str
    off: int
    size: int            # bytes of the whole field (a table: all of it)
    kind: str            # "scalar", "ptr", "bptr", "struct" (by value), "table"
    scalar: str = ""     # scalar and table: its scalar type ("UByte"...)
    target: str = ""     # ptr: what it points to (a struct or a scalar); struct: its name
    count: int = 0       # table: how many


@dataclass
class Layout:
    name: str
    size: int
    fields: Dict[str, FieldInfo] = field(default_factory=dict)
    order: List[str] = field(default_factory=list)


class AmigaError(Exception):
    pass


def ptr_target(type_name: Optional[str]) -> Optional[str]:
    """"Ptr Node" -> "Node"; anything else -> None"""
    if type_name:
        m = re.fullmatch(r"Ptr\s+([A-Za-z_]\w*)", type_name.strip())
        if m:
            return m.group(1)
    return None


def layouts(program) -> Dict[str, Layout]:
    """The layout of every @amiga struct of the program (nested ones first); AmigaError if one is wrong"""
    defs = {s.name: s for s in getattr(program, "amiga_structs", [])}
    out: Dict[str, Layout] = {}
    busy = set()

    def lay(name):
        if name in out:
            return out[name]
        if name in busy:
            raise AmigaError(f"@amiga struct {name} contains itself")
        busy.add(name)
        s = defs[name]
        off = 0
        lt = Layout(name=name, size=0)
        for f in s.fields:
            t = f.field_type
            m = re.fullmatch(r"([A-Za-z_]\w*)\[(\d+)\]", t)
            target = ptr_target(t)
            if target is not None:
                if target not in defs and target not in SCALARS:
                    raise AmigaError(f"{name}.{f.name}: Ptr {target}: {target} is not an @amiga struct or a scalar type")
                info = FieldInfo(f.name, 0, 4, "ptr", target=target)
            elif t == "BPtr":
                info = FieldInfo(f.name, 0, 4, "bptr")
            elif t in SCALARS:
                info = FieldInfo(f.name, 0, SCALARS[t][0], "scalar", scalar=t)
            elif m and m.group(1) in SCALARS:
                n = int(m.group(2))
                info = FieldInfo(f.name, 0, SCALARS[m.group(1)][0] * n, "table", scalar=m.group(1), count=n)
            elif t in defs:
                info = FieldInfo(f.name, 0, lay(t).size, "struct", target=t)
            else:
                raise AmigaError(f"{name}.{f.name}: unknown type '{t}' (Byte, UByte, Word, UWord, Long, ULong, "
                                 f"Ptr T, BPtr, an @amiga struct or a table like UByte[16])")
            align = 1 if (info.kind in ("scalar", "table") and SCALARS[info.scalar][0] == 1) else 2
            off = (off + align - 1) // align * align
            info.off = off
            off += info.size
            if f.name in lt.fields:
                raise AmigaError(f"{name}: field {f.name} twice")
            lt.fields[f.name] = info
            lt.order.append(f.name)
        lt.size = (off + 1) // 2 * 2
        busy.discard(name)
        out[name] = lt
        return lt

    for n in defs:
        lay(n)
    return out


def field_value_type(layout: Layout, fname: str) -> Optional[str]:
    """What reading the field gives: "Int" for a scalar, "Ptr T" for a pointer, a nested struct or a table (its
    address), "BPtr" as an Int; None if there is no such field"""
    f = layout.fields.get(fname)
    if f is None:
        return None
    if f.kind in ("scalar", "bptr"):
        return "Int"
    if f.kind == "ptr":
        return f"Ptr {f.target}"
    if f.kind == "struct":
        return f"Ptr {f.target}"
    return f"Ptr {f.scalar}"      # a table: the address of its first element
