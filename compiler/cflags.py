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
#   - "s" (removes a copy between registers when the copied one looks unused): in dashweb's
#     lib/maqueta.dash (_absoluto, inlined in _bloque_en) "if w > cw then w = cw" became
#     "move.l d2,(-172,a5)" instead of "move.l d2,d7 / move.l d7,(-172,a5)", but d7 (w) was
#     still read after the jge that follows (it tests the flags of that store): an absolute
#     box with right: 0 came out 1 pixel wide (test_maqueta_cajas of dashweb, 2026-10-16;
#     a Print after the call hid it). No small Dash case found: 240 random programs, none
#     changed by "s".
# The default is "abcefhilmnprsz0"; without "e", "r" and "s" the benchmarks keep their
# speed and size.
BBB = "-fbbb=abcfhilmnpz0"
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


# ./dash --debug: the zeroed globals (.bss) go in the hunk of .data, after its own. The DWARF keeps
# the addresses of the ELF the linker made the hunk file from (.data after .text, .bss after .data)
# and gdb places them with the offsets bgdbserver gives (qOffsets); gdb takes one offset for .data
# and .bss together, and on the Amiga they are two hunks anywhere in memory: with a single hunk,
# tools/gdb_relay.py makes the one offset right for both. The program is bigger by its .bss.
BSS_IN_DATA = "    *(.bss)\n    *(.bss.*)\n    *(COMMON)\n"


def debug_link_flags(ld: str, build_dir: str) -> list:
    """-T with the toolchain's own linker script but .bss in .data (written to build_dir)."""
    import os
    import subprocess
    text = subprocess.run([ld, "--verbose"], capture_output=True, text=True).stdout
    parts = text.split("=" * 50)
    if len(parts) < 3 or BSS_IN_DATA not in parts[1] or "    __edata = .;\n" not in parts[1]:
        return []                                  # another linker: as it is (globals in .bss misplaced)
    script = parts[1].strip("\n").replace(BSS_IN_DATA, "", 1)
    script = script.replace("    __edata = .;\n", BSS_IN_DATA + "    __edata = .;\n", 1)
    path = os.path.join(build_dir, "dash_debug.x")
    with open(path, "w") as f:
        f.write(script + "\n")
    return ["-Wl,-T," + path]
