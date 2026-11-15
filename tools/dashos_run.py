#!/usr/bin/env python3
"""Compila un programa Dash para DashOS por el camino de C (docs/AARCH64_LOOP.md, fase A2) y lo ejecuta en el PC
con qemu-aarch64. Para probar: la plataforma es la de Linux (runtime/dashos/plat.c con DASH_PLAT_LINUX).

Lo nativo de DashOS es little-endian; con --be, big-endian (las bibliotecas de la caja Amiga), en qemu-aarch64_be.

    python3 tools/dashos_run.py prog.dash            # compila, ejecuta y enseña la salida
    python3 tools/dashos_run.py prog.dash -o prog    # además deja el ELF
    python3 tools/dashos_run.py prog.dash --dashos -o prog   # el ELF para DashOS de verdad (no se ejecuta)

Sale con el código del programa. Necesita clang (objetivos aarch64-none-elf y aarch64_be-none-elf), ld.lld,
qemu-aarch64 y qemu-aarch64_be."""
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
CFLAGS = ["--target=aarch64-none-elf", "-ffreestanding", "-fno-builtin", "-O2", "-fPIE",
          # con la FPU y SIMD: DashOS guarda sus registros por hilo (C28)
          "-march=armv8-a",
          "-fno-delete-null-pointer-checks", "-fno-strict-aliasing", "-Wno-unknown-attributes", "-Wno-pointer-sign",
          "-Werror=implicit-function-declaration", "-Werror=int-conversion",
          "-Werror=pointer-to-int-cast", "-Werror=int-to-pointer-cast", "-Werror=incompatible-pointer-types",
          "-I" + str(RT / "include"), "-I" + str(RT)]


def cflags(be=False):
    """Las opciones de clang: little-endian (lo nativo de DashOS) o big-endian (la caja Amiga)"""
    return ["--target=aarch64_be-none-elf", *CFLAGS[1:]] if be else CFLAGS


def out_dir(be=False):
    """Donde van las bibliotecas compiladas: build/dashos (little-endian) o build/dashos/be"""
    return REPO / "build" / "dashos" / ("be" if be else "")


_lib_lock = threading.Lock()


def library(name, be=False):
    """La biblioteca del runtime (compiler/clibs.py: zlib, ryu, fdlibm...) compilada para ARM, en build/dashos/"""
    with _lib_lock:   # (tests/dashos_tests.py compila en varios hilos)
        return _library(name, be)


def _library(name, be):
    from compiler.clibs import LIBRARIES
    spec = LIBRARIES[name]
    src_dir = REPO / "runtime" / name
    out = out_dir(be)
    out.mkdir(parents=True, exist_ok=True)
    lib = out / f"{name}.a"
    sources = [src_dir / s for s in spec["sources"]]
    newest = max(p.stat().st_mtime for p in sources + list(src_dir.rglob("*.h")) + list(RT.rglob("*.h")) +
                 [Path(__file__)])
    if lib.exists() and lib.stat().st_mtime >= newest:
        return lib
    flags = [f for f in cflags(be) if not f.startswith("-Werror")] + spec["defines"] + [f"-I{src_dir}"]
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


def link_flags(entry, stack, pie):
    """Las opciones de ld.lld: un ELF estático en 0x400000 (lo que carga hoy DashOS) o, con pie, un PIE estático
    (ET_DYN sin enlazador dinámico) que se reubica solo al arrancar (_dash_relocate de plat.c) y funciona cargado en
    cualquier dirección, también por encima de 4 GB. Cada segmento en sus páginas; la pila, en PT_GNU_STACK."""
    where = ["-pie", "--no-dynamic-linker", "-z", "text"] if pie else ["--image-base=0x400000"]
    return ["-static", *where, "-e", entry, "-z", "separate-loadable-segments", "-z", f"stack-size={stack}"]


def kit_c(be=False):
    """libkit_c.a de DashOS (las ventanas de mui_*: docs/DASHOS_VENTANAS_LOOP.md): la de $DASH_KIT_C, la que deja
    `make -C kernel kit-c` en $DASHOS_DIR/build (de serie ~/Projects/dashos) o la de cargo en kit-c/. Se copia a
    build/dashos/ con el memcpy de la biblioteca dashos débil (manda el de plat.c). Devuelve (ruta, error)"""
    if be:
        return None, "las ventanas (mui_*) en DashOS son de los programas nativos, no de la caja Amiga (--be)\n"
    dashos = Path(os.environ.get("DASHOS_DIR") or Path.home() / "Projects" / "dashos")
    cands = [Path(os.environ["DASH_KIT_C"])] if os.environ.get("DASH_KIT_C") else []
    cands += [dashos / "build" / "libkit_c.a", dashos / "kit-c" / "target" / "aarch64-unknown-none" / "release" / "libkit_c.a"]
    src = next((c for c in cands if c.exists()), None)
    if not src:
        return None, (f"falta libkit_c.a de DashOS para las ventanas (mui_*): make -C kernel kit-c en DashOS, o "
                      f"DASHOS_DIR / DASH_KIT_C (buscado en {', '.join(map(str, cands))})\n")
    out = out_dir() / "libkit_c.a"
    with _lib_lock:
        if not out.exists() or out.stat().st_mtime < src.stat().st_mtime:
            out.parent.mkdir(parents=True, exist_ok=True)
            part = out.with_suffix(".part")
            subprocess.run(["llvm-objcopy", "--weaken-symbol=memcpy", str(src), str(part)], check=True)
            shutil.move(str(part), str(out))
    return out, ""


# Las ventanas piden pila: el kit dibuja letras y coloca grupos con recursión
UI_STACK = 262144


def build(src, exe, linux=True, memcheck=False, pie=False, be=False):
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
            r = subprocess.run(["clang", *cflags(be), *defs, "-c", str(f), "-o", str(o)], capture_output=True, text=True)
            if r.returncode:
                return False, r.stderr.replace(str(c), "prog.c")
            objs.append(str(o))
        from compiler.clibs import LIBRARIES, uses_library
        objs += [str(library(n, be)) for n in LIBRARIES if uses_library(n, text)]
        if "dash_ui_" in text:                       # (mui_*: las ventanas de kit-c)
            ui, err = kit_c(be)
            if not ui:
                return False, err
            objs += [str(ui), "--undefined-glob=dash_ui_*"]
            stack = max(stack, UI_STACK)
        r = subprocess.run(["ld.lld", *link_flags("_start", stack, pie), *objs, "-o", str(exe)], capture_output=True, text=True)
        if r.returncode:
            return False, r.stderr
    return True, ""


def _no_core():
    import resource
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))   # (un volcado de qemu lleva el entorno: secretos)


def build_direct(src, exe, linux=True, memcheck=False, pie=False, be=False):
    """Por el compilador directo (dashc-a64: docs/AARCH64_LOOP.md, A4), sin C: el objeto ELF del programa, enlazado
    con el runtime de dashc para ARM (runtime/dashos/build.py)"""
    sys.path.insert(0, str(REPO / "dashc" / "runtime" / "dashos"))
    import build as rt_build
    dashc = REPO / "dashc" / "dashc-a64"
    with tempfile.TemporaryDirectory() as tmp:
        o = Path(tmp) / "prog.o"
        r = subprocess.run([str(dashc), str(src), "-o", str(o), *(["--memcheck"] if memcheck else []),
                            *(["--be"] if be else [])],
                           cwd=REPO, capture_output=True, text=True)
        if r.returncode:
            return False, r.stdout + r.stderr
        with _lib_lock:
            rt = rt_build.build(memcheck, be)
        plat = Path(tmp) / "plat.o"
        r = subprocess.run(["clang", *cflags(be), *(["-DDASH_PLAT_LINUX"] if linux else []), "-c", str(RT / "plat.c"),
                            "-o", str(plat)], capture_output=True, text=True)
        if r.returncode:
            return False, r.stderr
        libs = [str(library(n, be)) for n in ("ryu", "fdlibm", "zlib")]
        stack = 65536
        nm = subprocess.run(["llvm-nm", "-u", str(o)], capture_output=True, text=True).stdout
        if "db_mui_" in nm:                          # (mui_*: las ventanas de kit-c)
            ui, err = kit_c(be)
            if not ui:
                return False, err
            libs += [str(ui), "--undefined-glob=dash_ui_*"]
            stack = UI_STACK
        r = subprocess.run(["ld.lld", *link_flags("_dash_entry", stack, pie),
                            str(o), str(rt), str(plat), *libs, str(rt), "-o", str(exe)], capture_output=True, text=True)
        if r.returncode:
            return False, r.stderr
    return True, ""


def run(exe, timeout=30, cwd=None, env=None):
    """Lo ejecuta en qemu: (código, salida, errores). env, variables de más (DASH_LANGUAGE, DASH_LOCALE_DIR...)"""
    with open(exe, "rb") as f:
        be = f.read(6)[5] == 2                         # (EI_DATA)
    r = subprocess.run(["qemu-aarch64_be" if be else "qemu-aarch64", str(Path(exe).resolve())], capture_output=True,
                       timeout=timeout, preexec_fn=_no_core, cwd=cwd, env=dict(os.environ, **(env or {})))
    return r.returncode, r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace")   # (DashOS: UTF-8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("-o")
    ap.add_argument("--dashos", action="store_true", help="plataforma de DashOS (no se ejecuta)")
    ap.add_argument("--memcheck", action="store_true", help="como ./dash --memcheck")
    ap.add_argument("--directo", action="store_true", help="por el compilador directo (dashc-a64), sin C")
    ap.add_argument("--pie", action="store_true", help="PIE estático: se carga en cualquier dirección")
    ap.add_argument("--be", action="store_true", help="big-endian (bibliotecas de la caja Amiga)")
    a = ap.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        exe = Path(a.o) if a.o else Path(tmp) / "prog"
        ok, msg = (build_direct if a.directo else build)(Path(a.src).resolve(), exe.resolve(), linux=not a.dashos,
                                                         memcheck=a.memcheck, pie=a.pie, be=a.be)
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
