"""gcc options for the generated C, shared by ./dash and tests/run_tests.py."""

# -O2 by default: tested in FS-UAE (Kickstart 3.1) with the 30 examples and the
# emu tests, same output as -O0 and about half the size.
# -fomit-frame-pointer: no link/unlk in every function, one more address register.
# -fbbb without "e" and "r": bebbo's optimizer (run after GCC's own passes) gave
# wrong code twice, found by tools/fuzz_refcount.py in --memcheck builds on the A1200:
#   - "r" (register renaming) with "e": a value kept in a1 across calls that change
#     a1; the list literal [Punto(1, 1), L[2], L[0]] got L[0] as 0.
#   - "e" alone (remove dead assignments and "redundant" loads): a sum read a stale
#     value (139 instead of 144, seed 12).
# The default is "abcefhilmnprsz0"; without "e" and "r" the benchmarks keep their
# speed and size.
BBB = "-fbbb=abcfhilmnpsz0"
# Address 0 is readable memory on an Amiga, and nil is C NULL. Without these, GCC
# turns a read through a pointer it knows is NULL ("var n: Nodo = nil" then n.valor)
# into a trap instruction (the program crashes instead of reading garbage), and drops
# NULL checks that come after a dereference.
NULL_OK = ["-fno-isolate-erroneous-paths-dereference", "-fno-delete-null-pointer-checks"]
OPTIMIZE = ["-O2", "-fomit-frame-pointer", BBB] + NULL_OK
SMALL = ["-Os", "-fomit-frame-pointer", BBB] + NULL_OK
DEBUG = ["-O0"]


def opt_flags(no_optimize: bool = False, small: bool = False):
    return list(DEBUG if no_optimize else SMALL if small else OPTIMIZE)


# MUI: the SDK headers are not in the toolchain and may not go in git (license), so
# tools/get_mui_sdk.sh unpacks them in ~/.cache/dash-mui; DASH_MUI_SDK = its SDK/MUI.
MUI_MARK = "#include <libraries/mui.h>"


def mui_sdk() -> str:
    import os
    return os.environ.get("DASH_MUI_SDK") or os.path.expanduser("~/.cache/dash-mui/x/SDK/MUI")


def mui_flags(sources) -> list:
    """-I for the MUI SDK when one of the C sources uses MUI; FileNotFoundError without it."""
    import os
    if not any(MUI_MARK in s for s in sources):
        return []
    include = os.path.join(mui_sdk(), "C", "include")
    if not os.path.isfile(os.path.join(include, "libraries", "mui.h")):
        raise FileNotFoundError(f"MUI SDK not found in {mui_sdk()}: run tools/get_mui_sdk.sh or set DASH_MUI_SDK")
    return ["-I" + include]


# AmiSSL (dashweb D11): its SDK headers come from tools/get_amissl.sh (~/.cache/dash-amissl);
# DASH_AMISSL_SDK = its AmiSSL/Developer directory.
AMISSL_MARK = "#include <amissl/amissl.h>"


def amissl_flags(sources) -> list:
    """-I for the AmiSSL SDK when one of the C sources uses TLS; FileNotFoundError without it."""
    import os
    if not any(AMISSL_MARK in s for s in sources):
        return []
    sdk = os.environ.get("DASH_AMISSL_SDK") or os.path.expanduser("~/.cache/dash-amissl/x/AmiSSL/Developer")
    include = os.path.join(sdk, "include")
    if not os.path.isfile(os.path.join(include, "amissl", "amissl.h")):
        raise FileNotFoundError(f"AmiSSL SDK not found in {sdk}: run tools/get_amissl.sh or set DASH_AMISSL_SDK")
    return ["-I" + include]


# C from outside (dashweb D10): each "@link file" of the program is written in the C as
# "/* dash-link: /full/path */"; gcc gets the file after the C sources, and its directory
# with -I (a library's headers usually sit next to it).
LINK_MARK = "/* dash-link: "


def link_flags(sources) -> tuple:
    """(-I options, files to link) of the @link lines in the C sources; FileNotFoundError if one is missing."""
    import os
    files = []
    for s in sources:
        for line in s.splitlines():
            if line.startswith(LINK_MARK) and line.endswith(" */"):
                path = line[len(LINK_MARK):-3]
                if path not in files:
                    files.append(path)
    for path in files:
        if not os.path.isfile(path):
            raise FileNotFoundError(f"@link: {path} not found")
    includes = []
    for path in files:
        d = "-I" + os.path.dirname(path)
        if d not in includes:
            includes.append(d)
    return includes, files
