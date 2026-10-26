"""C libraries of the runtime compiled apart: zlib (Lorraine D6) and Ryu (Lorraine D1, D3).

Each lives unchanged in runtime/<name> with Dash's entry points (dash_*.c) next to it, and is compiled
once for each set of CPU options into a library in build/. The generated C leaves a marker (the first
line of the runtime template that calls the library) and the CLI and the test runner link the library
of each marker found. A library pulls only the objects a program calls.

    zlib: inflate, deflate, crc32 (runtime/zlib/README.md). Z_PREFIX: zlib's names start with z_, so a
          program may have its own inflate or crc32.
    ryu:  a double to its shortest decimal and back (runtime/ryu/LEEME).
"""

import hashlib
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

LIBRARIES = {
    "zlib": {
        "marker": "/* Dash zlib Runtime */",
        "sources": ["adler32.c", "crc32.c", "deflate.c", "inffast.c", "inflate.c", "inftrees.c", "trees.c",
                    "zutil.c", "dash_inflate.c", "dash_deflate.c", "dash_crc32.c"],
        # NO_GZIP: inflate without the gzip header code; Z_TESTW=0: crc32 a byte at a time with one table of
        # 1 KB (the "braided" one adds 20 KB of tables, for 64-bit machines)
        "defines": ["-DZ_PREFIX", "-DNO_GZIP", "-DZ_TESTW=0"],
    },
    "ryu": {
        "marker": "/* Dash Double Runtime */",
        "sources": ["dash_ryu.c"],
        "defines": ["-DNDEBUG"],
    },
}


def uses_library(name: str, c_code: str) -> bool:
    return LIBRARIES[name]["marker"] in c_code


def library(name: str, gcc: str, cpu_flags: list = (), build_dir: Path = ROOT / "build") -> str:
    """Path of the compiled library for these CPU options, rebuilt when a source is newer."""
    from compiler.cflags import opt_flags
    spec = LIBRARIES[name]
    src_dir = ROOT / "runtime" / name
    build_dir = Path(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)
    flags = opt_flags() + list(cpu_flags) + spec["defines"]
    tag = hashlib.md5(" ".join(flags).encode()).hexdigest()[:8]
    lib = build_dir / f"dash_{name}_{tag}.a"
    sources = [src_dir / s for s in spec["sources"]]
    newest = max(p.stat().st_mtime for p in sources + list(src_dir.rglob("*.h")) + [Path(__file__)])
    if lib.exists() and lib.stat().st_mtime >= newest:
        return str(lib)
    objs = []
    for src in sources:
        obj = build_dir / f"dash_{name}_{tag}_{os.getpid()}_{src.stem}.o"   # (runs in parallel)
        subprocess.run([gcc, "-noixemul", *flags, f"-I{src_dir}", "-c", str(src), "-o", str(obj)],
                       check=True, capture_output=True, text=True)
        objs.append(str(obj))
    ar = str(Path(gcc).with_name(Path(gcc).name.replace("gcc", "ar")))
    tmp = lib.with_suffix(f".{os.getpid()}.tmp")
    tmp.unlink(missing_ok=True)
    subprocess.run([ar, "rcs", str(tmp), *objs], check=True, capture_output=True, text=True)
    tmp.replace(lib)
    for obj in objs:
        os.unlink(obj)
    return str(lib)


def libraries_for(c_codes, gcc: str, cpu_flags: list = (), build_dir: Path = ROOT / "build") -> list:
    """The libraries the C sources need (one list of C texts), compiled for these CPU options."""
    codes = list(c_codes)
    return [library(name, gcc, cpu_flags, build_dir) for name in LIBRARIES
            if any(uses_library(name, c) for c in codes)]
