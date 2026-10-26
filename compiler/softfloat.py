"""Software floating point objects for programs that use Float.

See runtime/softfloat/README.md: GCC's fp-bit.c compiled for single precision
(with its add/sub/mul renamed to __dash_fb_*) plus fastfp.c, faster add/sub/mul
for the common case on 68000 that falls back to fp-bit for the rest. Linked
before -lm so Float never goes through mathieeesingbas.library.
"""

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "runtime" / "softfloat"
FPBIT = SRC_DIR / "fp-bit.c"
FASTFP = SRC_DIR / "fastfp.c"

# Marker that the Float runtime leaves in the generated C
FLOAT_MARKER = "/* Dash Float Runtime */"
# ... and the Double runtime (Lorraine D1)
DOUBLE_MARKER = "/* Dash Double Runtime */"

# fp-bit's versions keep working as the exact fallback of fastfp.c
RENAMES = {"___addsf3": "___dash_fb_addsf3", "___subsf3": "___dash_fb_subsf3",
           "___mulsf3": "___dash_fb_mulsf3"}


def uses_float(c_code: str) -> bool:
    return FLOAT_MARKER in c_code


def uses_double(c_code: str) -> bool:
    return DOUBLE_MARKER in c_code


def softfloat_double_objects(gcc: str, build_dir: Path = ROOT / "build") -> list:
    """fp-bit.c compiled for double (Lorraine D1), and the single precision objects: __adddf3, __muldf3,
    __divdf3, the comparisons and conversions. Without them GCC's calls go to libnix's libm, that is to mathieeedoubbas.library of
    the ROM, and that one's single sibling hangs in FS-UAE with Kickstart 3.1 (see the top)."""
    build_dir = Path(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)
    obj = build_dir / "dash_softfloat_df.o"
    if _stale(obj, FPBIT, Path(__file__)):
        tmp = build_dir / f"dash_softfloat_df.{os.getpid()}.o"
        subprocess.run([gcc, "-O2", f"-I{SRC_DIR / 'stub'}", f"-I{SRC_DIR}", "-c", str(FPBIT), "-o", str(tmp)],
                       check=True, capture_output=True, text=True)
        tmp.replace(obj)
    # (its __truncdfsf2, Double to Float, packs with the single precision's __make_fp)
    return [str(obj)] + softfloat_objects(gcc, build_dir)


def _stale(obj: Path, *sources: Path) -> bool:
    return not obj.exists() or any(obj.stat().st_mtime < s.stat().st_mtime for s in sources)


def softfloat_objects(gcc: str, build_dir: Path = ROOT / "build") -> list:
    """Paths of the compiled objects, rebuilt when a source is newer."""
    build_dir = Path(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)
    fpbit = build_dir / "dash_softfloat.o"
    fast = build_dir / "dash_fastfp.o"
    if _stale(fpbit, FPBIT, Path(__file__)):
        tmp = build_dir / "dash_softfloat_raw.o"
        subprocess.run([gcc, "-O2", "-DFLOAT", "-DFLOAT_ONLY", f"-I{SRC_DIR / 'stub'}", f"-I{SRC_DIR}",
                        "-c", str(FPBIT), "-o", str(tmp)], check=True, capture_output=True, text=True)
        objcopy = str(Path(gcc).with_name(Path(gcc).name.replace("gcc", "objcopy")))
        args = [objcopy]
        for old, new in RENAMES.items():
            args += ["--redefine-sym", f"{old}={new}"]
        subprocess.run(args + [str(tmp), str(fpbit)], check=True, capture_output=True, text=True)
    if _stale(fast, FASTFP):
        subprocess.run([gcc, "-O2", "-c", str(FASTFP), "-o", str(fast)], check=True,
                       capture_output=True, text=True)
    return [str(fpbit), str(fast)]


