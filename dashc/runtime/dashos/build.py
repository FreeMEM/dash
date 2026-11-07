#!/usr/bin/env python3
"""El runtime de dashc para DashOS (docs/AARCH64_LOOP.md, fase A4), como build/dashos/dashc_rt.a (y
dashc_rt_mc.a, el de --memcheck); los de big-endian (--be, la caja Amiga), en build/dashos/be/.

Sale como el del 68000 (runtime/gen_lib.py): el C que genera el Dash de Python para una cocina que lo usa todo
(runtime/dashos/cocina.dash, sin ventanas), ahora para DashOS (DASH_TARGET=dashos), sin lo del programa; más las
envolturas dl_* de runtime/api.c que no tocan AmigaOS, con lo que devuelven como _DashP (un Int de C en w0 deja
la parte alta del registro sin definir, y el código de dashc usa los 64 bits); y runtime/dashos/start.c (arranque,
salida, Print). Se compila con clang como el resto de lo de DashOS (tools/dashos_run.py: sin FP ni SIMD).

    python3 runtime/dashos/build.py [--memcheck] [--be]   # (lo llama tools/dashos_run.py --directo cuando hace falta)
"""
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DASHC = HERE.parent.parent
REPO = DASHC.parent
OUT = REPO / "build" / "dashos"
sys.path.insert(0, str(REPO / "tools"))

# las envolturas de api.c que van (por nombre); las de ventanas, eventos, menús, perfil... son de AmigaOS
SKIP = {"dl_window_open", "dl_init_area", "dl_forget", "dl_window_close", "dl_event_code", "dl_ac_loop",
        "dl_print_flush", "dl_close_windows", "dl_key_char", "dl_others", "dl_get_plain", "dl_fetch",
        "dl_wait_mask", "dl_event_take", "dl_get_gt", "dl_event_take_gt", "dl_event_gt_on", "dl_menu_begin",
        "dl_menu_next", "dl_event_next", "dl_event_next_timer", "dl_win_member", "dl_pc_frame", "dl_pc_sample",
        "dl_prof_tick", "dl_prof_start", "dl_prof_enter", "dl_prof_leave", "dl_prof_report"}


def portables():
    """Los builtins que compilan para DashOS (runtime/dashos/portables.py, que se ejecuta si hace falta)"""
    f = OUT / "portables.txt"
    if not f.exists():
        subprocess.run([sys.executable, str(HERE / "portables.py")], check=True)
    return [n for n in f.read_text().split() if n]


def runtime_c(memcheck):
    """El C del runtime: el de la cocina (más una llamada a cada builtin que se puede usar) sin lo del programa"""
    sys.path.insert(0, str(DASHC / "runtime"))
    import gen_lib
    bs = gen_lib.builtins(dashos=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "cocina.dash"
        src.write_text((HERE / "cocina.dash").read_text(encoding="utf-8") + "\nfunc _cocina_builtins()\n" +
                       "".join(f"    {n}({', '.join('0' for _ in bs[n].params)})\n" for n in portables()) + "end\n",
                       encoding="utf-8")
        c = Path(tmp) / "cocina.c"
        env = dict(os.environ, DASH_TARGET="dashos")
        if memcheck:
            env["DASH_MEMCHECK_C"] = "1"
        r = subprocess.run([sys.executable, "-m", "compiler.main", str(src), "-o", str(c)],
                           cwd=REPO, capture_output=True, text=True, env=env)
        if r.returncode:
            sys.exit(f"dashos/build.py: no transpila la cocina:\n{r.stdout}{r.stderr}")
        text = c.read_text(encoding="utf-8")
    a = text.index("/* Struct Definitions */")
    b = text.index("static void _dash_exit_cleanup(void)", a)
    text = text[:a] + text[b:]
    text = text[:text.index("\nint main(")] + "\n"
    text, n = re.subn(r"static const char \*const _dash_srcfiles\[\] = \{[^\n]*\};", "extern const char *_dash_srcfiles[64];", text)
    assert n == 1, "no encuentro _dash_srcfiles"
    text = text.replace("static const char *_dash_mc_where = NULL;", "const char *_dash_mc_where = NULL;")
    # @version: program_version() da lo que pone el programa al arrancar (como gen_lib.py)
    old = "static STRPTR _dash_program_version(void) { return (STRPTR)_DASH_VERSION; }"
    if old in text:
        text = text.replace(old, 'char *_dash_version = "";\n'
                            'static STRPTR _dash_program_version(void) { return (STRPTR)_dash_version; }')
    return text


def api_wrappers():
    """Las funciones de api.c que no tocan AmigaOS, desde los textos hasta el final (sin lo del perfil)"""
    src = (DASHC / "runtime" / "api.c").read_text(encoding="latin-1")
    src = src[src.index("/* ---- textos ---- */"):]
    a = src.index("/* ---- --perfil")
    b = src.index("/* ---- diccionarios con una clave literal")
    src = src[:a] + src[b:]
    lines, out, i = src.split("\n"), [], 0
    while i < len(lines):
        ln = lines[i]
        j = i
        if re.match(r"^[A-Za-z_]", ln) and not ln.rstrip().endswith(";") and not re.search(r"\{.*\}\s*$", ln):
            while j < len(lines) and lines[j] != "}":     # hasta la } de la columna 0
                j += 1
        block = "\n".join(lines[i:j + 1])
        m = re.match(r"^[A-Za-z_][\w \*]*?\b(dl_\w+)\s*\(", ln)
        if not (m and m.group(1) in SKIP):
            out.append(block)
        i = j + 1
    text = "\n".join(out)
    # lo que devuelven las dl_* de Int, Bool o ULONG: a _DashP
    text = re.sub(r"^(?:LONG|ULONG|BOOL) (dl_\w+\()", r"_DashP \1", text, flags=re.M)
    return text


def builtin_wrappers():
    """Cada builtin que se puede usar como db_nombre(_DashP...), como gen_lib.builtin_wrappers pero de 64 bits"""
    from string import Template
    sys.path.insert(0, str(DASHC / "runtime"))
    import gen_lib
    bs = gen_lib.builtins(dashos=True)
    from compiler import amiga_builtins as ab
    out = ["\n/* ---- builtins (compiler/amiga_builtins.py) ---- */\n"
           "#pragma clang diagnostic ignored \"-Wint-conversion\"\n"
           "#pragma clang diagnostic ignored \"-Wint-to-pointer-cast\"\n"
           "#pragma clang diagnostic ignored \"-Wpointer-to-int-cast\"\n"]
    for n in portables():
        b = bs[n]
        params = ", ".join(f"_DashP _a{i}" for i in range(len(b.params))) or "void"
        dp = gen_lib.double_params(n, b)
        code = Template(ab.DASHOS_TEMPLATES.get(n, b.c_template)).substitute({p: f"dl_dget((STRPTR)_a{i})" if i in dp else f"_a{i}"
                                                  for i, p in enumerate(b.params)})
        if b.return_type == "double":
            out.append(f"_DashP db_{n}({params}) {{ return (_DashP)dl_dbox({code}); }}\n")
        elif b.return_type == "void":
            out.append(f"_DashP db_{n}({params}) {{ {code}; return 0; }}\n")
        else:
            out.append(f"_DashP db_{n}({params}) {{ return (_DashP)({code}); }}\n")
    return "".join(out)


def build(memcheck=False, be=False):
    import dashos_run
    out = dashos_run.out_dir(be)
    out.mkdir(parents=True, exist_ok=True)
    lib = out / ("dashc_rt_mc.a" if memcheck else "dashc_rt.a")
    srcs = [HERE / "cocina.dash", HERE / "start.c", DASHC / "runtime" / "api.c", Path(__file__),
            REPO / "compiler" / "codegen.py", REPO / "compiler" / "latin1.py", REPO / "tools" / "dashos_run.py"]
    if lib.exists() and lib.stat().st_mtime >= max(p.stat().st_mtime for p in srcs):
        return lib
    sys.path.insert(0, str(REPO))
    from compiler.latin1 import latin1_escapes_to_utf8      # (los textos de DashOS son UTF-8)
    text = runtime_c(memcheck) + "\n/* ---- runtime/api.c ---- */\n" + \
        latin1_escapes_to_utf8(api_wrappers() + "\n" + (HERE / "start.c").read_text(encoding="utf-8")) + builtin_wrappers()
    with tempfile.TemporaryDirectory() as tmp:
        c = Path(tmp) / "dashc_rt.c"
        c.write_text(text, encoding="utf-8")
        o = Path(tmp) / "dashc_rt.o"
        flags = [f for f in dashos_run.cflags(be) if f != "-Werror=implicit-function-declaration"]
        r = subprocess.run(["clang", *flags, *(["-DDASH_MEMCHECK"] if memcheck else []), "-Wno-unused-function",
                            "-c", str(c), "-o", str(o)], capture_output=True, text=True)
        if r.returncode:
            (out / "dashc_rt_error.c").write_text(text, encoding="utf-8")
            sys.exit(f"dashos/build.py: el runtime no compila (en {out / 'dashc_rt_error.c'}):\n{r.stderr[-6000:]}")
        part = Path(tmp) / lib.name
        subprocess.run(["llvm-ar", "rcs", str(part), str(o)], check=True)
        import shutil
        shutil.move(str(part), str(lib))
    return lib


if __name__ == "__main__":
    print(build("--memcheck" in sys.argv, "--be" in sys.argv))
