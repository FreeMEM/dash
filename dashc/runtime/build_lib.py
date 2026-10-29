#!/usr/bin/env python3
"""Construye runtime/dashrt.o, runtime/dashrt_mc.o (--memcheck) y runtime/dashrt_fpu.o (--fpu): el runtime que dashc lleva dentro.

    python3 runtime/build_lib.py        (make runtime)

1. gen_lib.py saca el runtime de ./dash (con los @native de lib/amiga y los builtins) a build/dashlib_rt.c.
2. Se compila con gcc de bebbo, normal y con DASH_MEMCHECK, una sección por función (hunk.c se queda solo
   con lo que usa cada programa).
3. Se añaden las librerías de C que ./dash compila aparte (compiler/clibs.py: zlib...), la libc mínima de
   rt_libc.c, las rutinas de rt_math.s y las de libgcc que hacen falta (64 bits).
4. Los objetos van uno tras otro (sin ld -r, que juntaría las secciones): hunk.c lee las unidades.

Necesita el gcc de bebbo, el Dash de Python y el SDK de AmiSSL (tools/get_amissl.sh)."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DASHC = HERE.parent
REPO = DASHC.parent
GCC = "/opt/amiga/bin/m68k-amigaos-gcc"
AR = "/opt/amiga/bin/m68k-amigaos-ar"
AMISSL = os.environ.get("DASH_AMISSL_SDK") or os.path.expanduser("~/.cache/dash-amissl/x/AmiSSL/Developer")
# (las de ./dash, compiler/cflags.py: sin las pasadas de -fbbb que dan código erróneo)
sys.path.insert(0, str(REPO))
from compiler.cflags import opt_flags  # noqa: E402
FLAGS = [*opt_flags(), "-m68000", "-noixemul", "-fno-common", "-ffunction-sections", "-fdata-sections"]
LIBGCC = ["_udivdi3.o", "_umoddi3.o", "_divdi3.o", "_moddi3.o", "_muldi3.o", "_udivmoddi4.o", "_clz.o",
          "_fixunssfsi.o", "_clzsi2.o", "_clzdi2.o", "xfpgnulib__extendsfdf2.o",
          # (para el C de @link: desplazamientos y conversiones de 64 bits)
          "_ashldi3.o", "_lshrdi3.o", "_ashrdi3.o", "_cmpdi2.o", "_ucmpdi2.o", "_negdi2.o", "_fixdfdi.o",
          "_fixunsdfdi.o", "_floatdidf.o", "_floatundidf.o", "_fixunsdfsi.o", "_ctzsi2.o", "_ctzdi2.o",
          "_popcountsi2.o", "_popcountdi2.o", "_popcount_tab.o", "_bswapsi2.o", "_bswapdi2.o", "_ffssi2.o", "_ffsdi2.o"]


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"falla: {' '.join(cmd)}\n{r.stdout}{r.stderr}")


def main():
    build = DASHC / "build"
    build.mkdir(exist_ok=True)
    src = build / "dashlib_rt.c"
    run([sys.executable, str(HERE / "gen_lib.py"), str(src)])
    # (el SDK de MUI, tools/get_mui_sdk.sh: sus cabeceras no van en git)
    sys.path.insert(0, str(REPO))
    from compiler.cflags import mui_sdk
    inc = [f"-I{HERE}", f"-I{AMISSL}/include", f"-I{os.path.join(mui_sdk(), 'C', 'include')}"]
    run([GCC, *FLAGS, *inc, "-c", str(src), "-o", str(build / "dashlib.o")])
    run([GCC, *FLAGS, *inc, "-DDASH_MEMCHECK", "-c", str(src), "-o", str(build / "dashlib_mc.o")])
    common = objects(build, FLAGS, "", "-m68000")
    for out, lib in (("dashrt.o", "dashlib.o"), ("dashrt_mc.o", "dashlib_mc.o")):
        write(HERE / out, [build / lib] + common)
    # --fpu: todo para 68020 + 68881 (como ./dash --fpu), el Float de dashc por rt_fpu.s
    fpu = [f for f in FLAGS if f != "-m68000"] + ["-m68020", "-m68881"]
    run([GCC, *fpu, *inc, "-c", str(src), "-o", str(build / "dashlib_fpu.o")])
    write(HERE / "dashrt_fpu.o", [build / "dashlib_fpu.o"] + objects(build, fpu, "_fpu", "-m68020", "-m68881"))


def write(out, objs):
    with open(out, "wb") as f:
        for p in objs:
            f.write(p.read_bytes())


def objects(build, flags, sfx, *cpu):
    """lo que va tras el C del runtime: libc, rutinas en ensamblador, las librerías de C, el float por software
    (sin FPU) y lo de libgcc, para esa CPU"""
    fpu = "-m68881" in cpu
    common = []
    run([GCC, *flags, "-fno-builtin", "-fno-tree-loop-distribute-patterns", "-c", str(HERE / "rt_libc.c"),
         "-o", str(build / f"rt_libc{sfx}.o")])
    common.append(build / f"rt_libc{sfx}.o")
    # lo de libc y libm que pide el C de @link (QuickJS...)
    run([GCC, *flags, "-fno-builtin", "-c", str(HERE / "rt_compat.c"), "-o", str(build / f"rt_compat{sfx}.o")])
    common.append(build / f"rt_compat{sfx}.o")
    run([GCC, "-m68000", "-c", str(HERE / "rt_math.s"), "-o", str(build / "rt_math.o")])
    common.append(build / "rt_math.o")
    run([GCC, "-m68000", "-c", str(HERE / "rt_libs.s"), "-o", str(build / "rt_libs.o")])
    common.append(build / "rt_libs.o")
    # las librerías de C de ./dash, con sus opciones
    from compiler.clibs import LIBRARIES
    for name, spec in LIBRARIES.items():
        for s in spec["sources"]:
            obj = build / f"{name}_{Path(s).stem}{sfx}.o"
            run([GCC, *flags, *spec["defines"], f"-I{REPO / 'runtime' / name}", "-c",
                 str(REPO / "runtime" / name / s), "-o", str(obj)])
            common.append(obj)
    if fpu:
        run([GCC, *cpu, "-c", str(HERE / "rt_fpu.s"), "-o", str(build / "rt_fpu.o")])
        common.append(build / "rt_fpu.o")
    else:
        # Float por software, como compiler/softfloat.py (fp-bit.c en simple precisión, con su suma, resta y
        # producto renombrados, y fastfp.c, que los usa de respaldo), una sección por función
        from compiler.softfloat import SRC_DIR, FPBIT, FASTFP, RENAMES
        raw = build / "softfloat_raw.o"
        run([GCC, *flags, "-DFLOAT", "-DFLOAT_ONLY", f"-I{SRC_DIR / 'stub'}", f"-I{SRC_DIR}", "-c", str(FPBIT),
             "-o", str(raw)])
        renames = []
        for old, new in RENAMES.items():
            renames += ["--redefine-sym", f"{old}={new}"]
        run([GCC.replace("gcc", "objcopy"), *renames, str(raw), str(build / "softfloat.o")])
        common.append(build / "softfloat.o")
        run([GCC, *flags, "-c", str(FASTFP), "-o", str(build / "fastfp.o")])
        common.append(build / "fastfp.o")
        # y en doble precisión (Double), como softfloat_double_objects
        run([GCC, *flags, f"-I{SRC_DIR / 'stub'}", f"-I{SRC_DIR}", "-c", str(FPBIT), "-o",
             str(build / "softfloat_df.o")])
        common.append(build / "softfloat_df.o")
    # de libgcc, la aritmética de 64 bits
    libgcc = subprocess.run([GCC, *cpu, "-print-libgcc-file-name"], capture_output=True,
                            text=True).stdout.strip()
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([AR, "x", libgcc, *LIBGCC], cwd=tmp, check=True)
        for o in LIBGCC:
            dst = build / f"libgcc{sfx}{o}"
            dst.write_bytes((Path(tmp) / o).read_bytes())
            common.append(dst)
    return common

if __name__ == "__main__":
    main()
