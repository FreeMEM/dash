"""zlib for inflate, deflate and crc32 (Lorraine D6).

runtime/zlib holds zlib 1.3.1 unchanged (the files raw deflate needs) plus dash_*.c, the entry points the
generated C calls (one object each: a program that only inflates does not link deflate). They are compiled
once for each set of CPU options into a library in build/, with the symbols prefixed (Z_PREFIX:
z_inflate...), so a Dash program may still have its own inflate or crc32.
The CLI and the test runner link it whenever a program uses those builtins.
"""

import hashlib
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "runtime" / "zlib"
SOURCES = ["adler32.c", "crc32.c", "deflate.c", "inffast.c", "inflate.c", "inftrees.c", "trees.c", "zutil.c",
           "dash_inflate.c", "dash_deflate.c", "dash_crc32.c"]

# Marker that the zlib runtime leaves in the generated C
ZLIB_MARKER = "/* Dash zlib Runtime */"

# Z_PREFIX: z_ names; NO_GZIP: inflate without the gzip header code; Z_TESTW=0: crc32 a byte at a time
# with one table of 1 KB (the "braided" one adds 20 KB of tables, for 64-bit machines)
DEFINES = ["-DZ_PREFIX", "-DNO_GZIP", "-DZ_TESTW=0"]


def uses_zlib(c_code: str) -> bool:
    return ZLIB_MARKER in c_code


def zlib_library(gcc: str, cpu_flags: list = (), build_dir: Path = ROOT / "build") -> str:
    """Path of the compiled library for these CPU options, rebuilt when a source is newer."""
    from compiler.cflags import opt_flags
    build_dir = Path(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)
    flags = opt_flags() + list(cpu_flags) + DEFINES
    tag = hashlib.md5(" ".join(flags).encode()).hexdigest()[:8]
    lib = build_dir / f"dash_zlib_{tag}.a"
    sources = [SRC_DIR / s for s in SOURCES]
    newest = max(p.stat().st_mtime for p in sources + list(SRC_DIR.glob("*.h")) + [Path(__file__)])
    if lib.exists() and lib.stat().st_mtime >= newest:
        return str(lib)
    objs = []
    for src in sources:
        obj = build_dir / f"dash_zlib_{tag}_{os.getpid()}_{src.stem}.o"   # (runs in parallel)
        subprocess.run([gcc, "-noixemul", *flags, f"-I{SRC_DIR}", "-c", str(src), "-o", str(obj)],
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
