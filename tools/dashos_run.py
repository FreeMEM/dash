#!/usr/bin/env python3
"""Compila un programa Dash para DashOS por el camino de C (docs/AARCH64_LOOP.md, fase A2) y lo ejecuta en el PC
con qemu-aarch64_be. Para probar: la plataforma es la de Linux (runtime/dashos/plat.c con DASH_PLAT_LINUX).

    python3 tools/dashos_run.py prog.dash            # compila, ejecuta y enseña la salida
    python3 tools/dashos_run.py prog.dash -o prog    # además deja el ELF
    python3 tools/dashos_run.py prog.dash --dashos -o prog   # el ELF para DashOS de verdad (no se ejecuta)

Sale con el código del programa. Necesita clang (objetivo aarch64_be-none-elf), ld.lld y qemu-aarch64_be."""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RT = REPO / "runtime" / "dashos"
sys.path.insert(0, str(REPO))
CFLAGS = ["--target=aarch64_be-none-elf", "-ffreestanding", "-fno-builtin", "-O2", "-fno-pic", "-fno-pie",
          # sin registros de coma flotante ni SIMD: DashOS no los deja usar en los programas (no los guarda al
          # cambiar de hilo); Float y Double van por software (fp-bit de runtime/softfloat, softfloat_lib)
          "-march=armv8-a+nofp+nosimd", "-mabi=aapcs-soft",
          "-fno-delete-null-pointer-checks", "-fno-strict-aliasing", "-Wno-unknown-attributes", "-Wno-pointer-sign",
          "-Werror=implicit-function-declaration", "-Werror=int-conversion",
          "-Werror=pointer-to-int-cast", "-Werror=int-to-pointer-cast", "-Werror=incompatible-pointer-types",
          "-I" + str(RT / "include"), "-I" + str(RT)]


_lib_lock = threading.Lock()


def library(name):
    """La biblioteca del runtime (compiler/clibs.py: zlib, ryu, fdlibm...) compilada para ARM, en build/dashos/"""
    with _lib_lock:   # (tests/dashos_tests.py compila en varios hilos)
        return _library(name)


def _library(name):
    from compiler.clibs import LIBRARIES
    spec = LIBRARIES[name]
    src_dir = REPO / "runtime" / name
    out = REPO / "build" / "dashos"
    out.mkdir(parents=True, exist_ok=True)
    lib = out / f"{name}.a"
    sources = [src_dir / s for s in spec["sources"]]
    newest = max(p.stat().st_mtime for p in sources + list(src_dir.rglob("*.h")) + list(RT.rglob("*.h")) +
                 [Path(__file__)])
    if lib.exists() and lib.stat().st_mtime >= newest:
        return lib
    flags = [f for f in CFLAGS if not f.startswith("-Werror")] + spec["defines"] + [f"-I{src_dir}"]
    with tempfile.TemporaryDirectory() as tmp:
        objs = []
        for s in sources:
            o = Path(tmp) / (s.stem + ".o")
            subprocess.run(["clang", *flags, "-w", "-c", str(s), "-o", str(o)], check=True)
            objs.append(str(o))
        part = Path(tmp) / lib.name
        subprocess.run(["llvm-ar", "rcs", str(part), *objs], check=True)
        shutil.move(str(part), str(lib))
    return lib


def softfloat_lib():
    """Float y Double por software: el fp-bit de GCC (runtime/softfloat), de precisión simple y doble"""
    with _lib_lock:
        src = REPO / "runtime" / "softfloat"
        lib = REPO / "build" / "dashos" / "softfloat.a"
        lib.parent.mkdir(parents=True, exist_ok=True)
        extra = RT / "softfloat_extra.c"   # (las conversiones que fp-bit no trae)
        newest = max(p.stat().st_mtime for p in [src / "fp-bit.c", src / "fp-bit.h", extra, Path(__file__)])
        if lib.exists() and lib.stat().st_mtime >= newest:
            return lib
        # (CMPtype: clang no conoce el modo de libgcc; mira el resultado en w0: un int)
        flags = [f for f in CFLAGS if not f.startswith("-Werror")] + [f"-I{src / 'stub'}", f"-I{src}", "-w",
                                                                      "-D__libgcc_cmp_return__=__SI__",
                                                                      # (clang no lo define, y sin él fp-bit
                                                                      # cambia de orden las mitades de un double)
                                                                      "-D__FLOAT_WORD_ORDER__=__ORDER_BIG_ENDIAN__"]
        with tempfile.TemporaryDirectory() as tmp:
            objs = []
            for name, defs in (("sf", ["-DFLOAT", "-DFLOAT_ONLY"]), ("df", [])):
                o = Path(tmp) / f"fpbit_{name}.o"
                subprocess.run(["clang", *flags, *defs, "-c", str(src / "fp-bit.c"), "-o", str(o)], check=True)
                objs.append(str(o))
            o = Path(tmp) / "extra.o"
            subprocess.run(["clang", *flags, "-c", str(extra), "-o", str(o)], check=True)
            objs.append(str(o))
            subprocess.run(["llvm-ar", "rcs", str(Path(tmp) / lib.name), *objs], check=True)
            shutil.move(str(Path(tmp) / lib.name), str(lib))
        return lib


def build(src, exe, linux=True, memcheck=False):
    """Transpila y enlaza; devuelve (ok, mensajes)"""
    with tempfile.TemporaryDirectory() as tmp:
        c = Path(tmp) / "prog.c"
        env = dict(os.environ, DASH_TARGET="dashos", **({"DASH_MEMCHECK_C": "1"} if memcheck else {}))
        r = subprocess.run([sys.executable, "-m", "compiler.main", str(src), "-o", str(c)], cwd=REPO, env=env,
                           capture_output=True, text=True)
        if r.returncode:
            return False, r.stdout + r.stderr
        text = c.read_text(encoding="latin-1")
        m = re.search(r"^#define DASH_STACK (\d+)", text, re.M)
        stack = max(int(m.group(1)) if m else 16384, 16384)
        objs = []
        for f, defs in ((c, ["-DDASH_MEMCHECK"] if memcheck else []), (RT / "plat.c", ["-DDASH_PLAT_LINUX"] if linux else [])):
            o = Path(tmp) / (f.stem + ".o")
            r = subprocess.run(["clang", *CFLAGS, *defs, "-c", str(f), "-o", str(o)], capture_output=True, text=True)
            if r.returncode:
                return False, r.stderr.replace(str(c), "prog.c")
            objs.append(str(o))
        from compiler.clibs import LIBRARIES, uses_library
        objs += [str(library(n)) for n in LIBRARIES if uses_library(n, text)] + [str(softfloat_lib())]
        r = subprocess.run(["ld.lld", "-static", "-e", "_start", "--image-base=0x400000",
                            "-z", "separate-loadable-segments", "-z", f"stack-size={stack}",
                            *objs, "-o", str(exe)], capture_output=True, text=True)
        if r.returncode:
            return False, r.stderr
    return True, ""


def _no_core():
    import resource
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))   # (un volcado de qemu lleva el entorno: secretos)


def build_direct(src, exe, linux=True, memcheck=False):
    """Por el compilador directo (dashc-a64: docs/AARCH64_LOOP.md, A4), sin C: el objeto ELF del programa, enlazado
    con el runtime de dashc para ARM (runtime/dashos/build.py)"""
    sys.path.insert(0, str(REPO / "dashc" / "runtime" / "dashos"))
    import build as rt_build
    dashc = REPO / "dashc" / "dashc-a64"
    with tempfile.TemporaryDirectory() as tmp:
        o = Path(tmp) / "prog.o"
        r = subprocess.run([str(dashc), str(src), "-o", str(o), *(["--memcheck"] if memcheck else [])],
                           cwd=REPO, capture_output=True, text=True)
        if r.returncode:
            return False, r.stdout + r.stderr
        with _lib_lock:
            rt = rt_build.build(memcheck)
        plat = Path(tmp) / "plat.o"
        r = subprocess.run(["clang", *CFLAGS, *(["-DDASH_PLAT_LINUX"] if linux else []), "-c", str(RT / "plat.c"),
                            "-o", str(plat)], capture_output=True, text=True)
        if r.returncode:
            return False, r.stderr
        libs = [str(library(n)) for n in ("ryu", "fdlibm", "zlib")] + [str(softfloat_lib())]
        r = subprocess.run(["ld.lld", "-static", "-e", "_dashc_start", "--image-base=0x400000",
                            "-z", "separate-loadable-segments", "-z", "stack-size=65536",
                            str(o), str(rt), str(plat), *libs, str(rt), "-o", str(exe)], capture_output=True, text=True)
        if r.returncode:
            return False, r.stderr
    return True, ""


def run(exe, timeout=30):
    r = subprocess.run(["qemu-aarch64_be", str(exe)], capture_output=True, timeout=timeout, preexec_fn=_no_core)
    return r.returncode, r.stdout.decode("latin-1"), r.stderr.decode("latin-1")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("-o")
    ap.add_argument("--dashos", action="store_true", help="plataforma de DashOS (no se ejecuta)")
    ap.add_argument("--memcheck", action="store_true", help="como ./dash --memcheck")
    ap.add_argument("--directo", action="store_true", help="por el compilador directo (dashc-a64), sin C")
    a = ap.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        exe = Path(a.o) if a.o else Path(tmp) / "prog"
        ok, msg = (build_direct if a.directo else build)(Path(a.src).resolve(), exe.resolve(), linux=not a.dashos,
                                                         memcheck=a.memcheck)
        if not ok:
            sys.exit(msg)
        if a.dashos:
            return
        rc, out, err = run(exe)
        sys.stdout.write(out)
        sys.stderr.write(err)
        sys.exit(rc)


if __name__ == "__main__":
    main()
