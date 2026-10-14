"""Drop the temporaries mark and its releases where nothing can leave a temporary.

Codegen gives every loop and every function a mark of the temporaries list
(`ULONG _dash_tmN = _dash_tmp_mark();`, `ULONG _dash_fm = ...`) and releases it
on each iteration and on exit. That is needed when the body makes strings or
objects, and pure cost otherwise: a call per iteration once the serial moved,
and a bigger function that GCC no longer inlines.

This pass reads the final C. A function "leaves temporaries" when it pushes to
one of the two lists (`_dash_otmp_push`, `_dash_tmp_release_keep`, a
`_dash_str_alloc` / `_dash_str_dup` whose `temp` argument is not FALSE) or
calls a function that does. A user function that releases its own mark
leaves nothing behind except its return value, which is `_dash_str_ret` /
`_dash_obj_float` / `_dash_tmp_release_keep` (pushes, so it counts). Calls to
functions not defined in the file (the OS, libc) and calls through pointers
leave nothing. A loop or function region without a call to a function that
leaves temporaries loses its mark and its releases.
"""

import re
from typing import Dict, List, Optional, Set

_CALL = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
_START = re.compile(r"^(?:static\s+)?(?:__inline__\s+|inline\s+)?[A-Za-z_][\w\s\*]*?\b([A-Za-z_]\w*)\s*\(")
_DEFINE = re.compile(r"^#define\s+([A-Za-z_]\w*)\(([^)]*)\)\s+(.*)$")

# the list pushes themselves
_PUSHERS = {"_dash_otmp_push", "_dash_tmp_release_keep"}
# a temporary only when their last argument is not FALSE
_BY_ARG = {"_dash_str_alloc", "_dash_str_dup"}
_KEYWORDS = {"if", "while", "for", "switch", "return", "sizeof", "__typeof__", "__asm__", "do"}


def _call_args(text: str, open_paren: int) -> Optional[List[str]]:
    """Arguments of the call whose '(' is at open_paren (top-level commas)."""
    depth, start, args = 0, open_paren + 1, []
    for i in range(open_paren, len(text)):
        c = text[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                args.append(text[start:i].strip())
                return args
        elif c == "," and depth == 1:
            args.append(text[start:i].strip())
            start = i + 1
    return None


def _calls(body: str) -> Set[str]:
    """Names called in a piece of C; _BY_ARG calls only when temp is not FALSE."""
    names = set()
    for m in _CALL.finditer(body):
        name = m.group(1)
        if name in _KEYWORDS:
            continue
        if name in _BY_ARG:
            args = _call_args(body, m.end() - 1)
            if args is not None and args[-1] == "FALSE":
                continue
        names.add(name)
    return names


def _definitions(lines: List[str]) -> Dict[str, str]:
    """Function bodies (and function-like macros) by name. A definition starts
    in column 0 with "type name(" and is not a prototype; its body runs to the
    "}" in column 0, or to the end of the line for one-line functions. The
    signature may span lines."""
    defs: Dict[str, str] = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        d = _DEFINE.match(line)
        if d:
            defs[d.group(1)] = d.group(3)
            i += 1
            continue
        m = _START.match(line)
        if not m or line.startswith(("typedef", "return", "else", "if ", "while", "for ", "do ")):
            i += 1
            continue
        # the signature up to its "{" (a ";" first means a prototype)
        j, sig = i, line
        while "{" not in sig and ";" not in sig and j + 1 < len(lines) and j - i < 8:
            j += 1
            sig += "\n" + lines[j]
        if "{" not in sig or (";" in sig and sig.index(";") < sig.index("{")):
            i = j + 1
            continue
        after = sig[sig.index("{") + 1:]
        if after.rstrip().endswith("}"):                 # one-line function
            defs[m.group(1)] = after.rstrip()[:-1]
            i = j + 1
            continue
        k = j + 1
        while k < len(lines) and lines[k] != "}":
            k += 1
        defs[m.group(1)] = after + "\n" + "\n".join(lines[j + 1:k])
        i = k + 1
    return defs


def _leavers(defs: Dict[str, str]) -> Set[str]:
    """Functions that can leave temporaries in the caller's lists."""
    calls = {name: _calls(body) for name, body in defs.items() if name not in _BY_ARG}
    leave = set(_PUSHERS) | {"_dash_str_alloc", "_dash_str_dup"}   # as found by _calls
    changed = True
    while changed:
        changed = False
        for name, called in calls.items():
            if name in leave:
                continue
            body = defs[name]
            own_mark = "ULONG _dash_fm = _dash_tmp_mark();" in body
            # a function with its own mark releases what it made; only what it
            # hands back (pushes in its return path) stays
            relevant = called & leave
            if own_mark:
                relevant = relevant & (_PUSHERS | {"_dash_str_ret", "_dash_obj_float"})
            if relevant:
                leave.add(name)
                changed = True
    return leave


def _strip_region(lines: List[str], start: int, end: int, mark: str) -> None:
    """Blank the mark at lines[start] and the releases of mark up to lines[end]."""
    rel = f"_dash_tmp_release({mark});"
    lines[start] = lines[start].replace(f"ULONG {mark} = _dash_tmp_mark();", "")
    for k in range(start, end + 1):
        if rel in lines[k]:
            lines[k] = lines[k].replace(rel, "")


def strip_unused_marks(c_code: str) -> str:
    if "_dash_tmp_release_f" not in c_code:      # no memory runtime: the macros are no-ops
        return c_code
    lines = c_code.split("\n")
    leave = _leavers(_definitions(lines))

    def leaves(text: str, mark: str) -> bool:
        return bool(_calls(text.replace(f"_dash_tmp_release({mark})", "")) & leave)

    # loops: from "{ ULONG _dash_tmN = _dash_tmp_mark();" to "_dash_tmp_release(_dash_tmN); }"
    loop_mark = re.compile(r"\{ ULONG (_dash_tm\d+) = _dash_tmp_mark\(\);")
    for i, line in enumerate(lines):
        m = loop_mark.search(line)
        if not m:
            continue
        mark = m.group(1)
        close = f"_dash_tmp_release({mark}); }}"
        end = next((j for j in range(i + 1, len(lines)) if close in lines[j]), None)
        if end is None:
            continue
        region = "\n".join(lines[i + 1:end + 1])
        if not leaves(region, mark):
            _strip_region(lines, i, end, mark)

    # functions: "ULONG _dash_fm = _dash_tmp_mark();" to the "}" in column 0
    for i, line in enumerate(lines):
        if line.strip() != "ULONG _dash_fm = _dash_tmp_mark();":
            continue
        end = next((j for j in range(i + 1, len(lines)) if lines[j] == "}"), None)
        if end is None:
            continue
        region = "\n".join(lines[i + 1:end])
        if "_dash_tmp_release_keep(_dash_fm" in region:
            continue
        if not leaves(region, "_dash_fm"):
            _strip_region(lines, i, end, "_dash_fm")
    # lines left empty by the pass
    return "\n".join(l for l in lines if l.strip() or not l)
