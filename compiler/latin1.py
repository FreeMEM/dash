"""AmigaOS texts are ISO-8859-1 (Latin-1); Dash sources are UTF-8.

The last pass over the generated C writes every non-ASCII character inside a C string
or character literal as an octal escape of its Latin-1 byte ("botón" -> "bot\\363n"),
so the Amiga shows it right. Characters Latin-1 does not have become "?". Comments
and the rest of the C stay as they are (GCC reads them as bytes)."""


def latin1_literals(c_code: str) -> str:
    if c_code.isascii():
        return c_code
    out = []
    i, n = 0, len(c_code)
    state = None          # None, '"', "'", "//", "/*"
    while i < n:
        ch = c_code[i]
        if state is None:
            if ch in "\"'":
                state = ch
            elif c_code.startswith("//", i):
                state = "//"
            elif c_code.startswith("/*", i):
                state = "/*"
                out.append("/*")
                i += 2
                continue
            out.append(ch)
        elif state in "\"'":
            if ch == "\\" and i + 1 < n:
                out.append(c_code[i:i + 2])
                i += 2
                continue
            if ch == state or ch == "\n":
                state = None
                out.append(ch)
            elif ord(ch) > 127:
                code = ord(ch) if ord(ch) < 256 else ord("?")
                out.append(f"\\{code:03o}" if code != ord("?") else "?")
            else:
                out.append(ch)
        elif state == "//":
            if ch == "\n":
                state = None
            out.append(ch)
        else:   # /* ... */
            if c_code.startswith("*/", i):
                state = None
                out.append("*/")
                i += 2
                continue
            out.append(ch)
        i += 1
    return "".join(out)


def latin1_escapes_to_utf8(c_code: str) -> str:
    """For DashOS, whose texts are UTF-8: a C source written for the Amiga ("divisi\\363n") with its Latin-1 octal
    escapes as the bytes of the same character in UTF-8 ("divisi\\303\\263n")"""
    import re

    def one(m):
        code = int(m.group(2), 8)
        return m.group(1) + "".join(f"\\{b:03o}" for b in chr(code).encode("utf-8"))
    return re.sub(r"(?<!\\)((?:\\\\)*)\\([23][0-7][0-7])", one, c_code)
