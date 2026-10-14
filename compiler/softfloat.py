"""Software floating point object for programs that use Float.

See runtime/softfloat/README.md: GCC's fp-bit.c compiled for single precision,
linked before -lm so Float never goes through mathieeesingbas.library.
"""

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "runtime" / "softfloat" / "fp-bit.c"

# Marker that the Float runtime leaves in the generated C
FLOAT_MARKER = "/* Dash Float Runtime */"


def uses_float(c_code: str) -> bool:
    return FLOAT_MARKER in c_code


def softfloat_object(gcc: str, build_dir: Path = ROOT / "build") -> str:
    """Path of the compiled fp-bit object, rebuilt when the source is newer."""
    build_dir = Path(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)
    obj = build_dir / "dash_softfloat.o"
    if not obj.exists() or obj.stat().st_mtime < SOURCE.stat().st_mtime:
        src_dir = SOURCE.parent
        subprocess.run([gcc, "-O2", "-DFLOAT", "-DFLOAT_ONLY",
                        f"-I{src_dir / 'stub'}", f"-I{src_dir}",
                        "-c", str(SOURCE), "-o", str(obj)],
                       check=True, capture_output=True, text=True)
    return str(obj)
