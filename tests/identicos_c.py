#!/usr/bin/env python3
"""Red de seguridad del camino por C (docs/AARCH64_LOOP.md): el C de ./dash --gcc puede cambiar de texto (tipos
limpios de tamaño de puntero), pero el código de 68k que sale de él no. Transpila los tests y ejemplos, los
compila con m68k-amigaos-gcc -c (normal, --memcheck y --fpu) y compara los objetos con los guardados.

    python3 tests/identicos_c.py --guardar   # guarda los objetos de ahora como referencia (build/c_ref.json)
    python3 tests/identicos_c.py             # comparar
    python3 tests/identicos_c.py -k lista    # solo los ficheros con "lista" en el nombre

__DATE__ y __TIME__ van fijos; los programas con @version cambian con el día: si difieren, se reintenta una vez."""
import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from compiler.cflags import opt_flags, mui_flags, amissl_flags  # noqa: E402

GCC = "/opt/amiga/bin/m68k-amigaos-gcc"
REF = REPO / "build" / "c_ref.json"
# build_date()/build_time() salen de __DATE__ y __TIME__: fijos, para que no cambien con la hora
FECHA = ["-Wno-builtin-macro-redefined", '-D__DATE__="Nov  3 2026"', '-D__TIME__="12:00:00"']
VARIANTES = {"": [], "mc": ["-DDASH_MEMCHECK"], "fpu": ["-m68020", "-m68881"]}


def corpus():
    return sorted(REPO.glob("tests/test_*.dash")) + sorted(REPO.glob("examples/*.dash")) + \
        sorted(REPO.glob("dashc/tests/*.dash"))


def objetos(src, tmp):
    """{variante: sha256 del objeto, o el texto del error}"""
    d = Path(tempfile.mkdtemp(dir=tmp))
    c = d / "prog.c"
    r = subprocess.run([sys.executable, "-m", "compiler.main", str(src), "-o", str(c)], cwd=REPO,
                       capture_output=True, text=True, timeout=300)
    if r.returncode:
        return {"transpilar": (r.stdout + r.stderr).replace(str(c), "C")[-400:]}
    text = c.read_text(encoding="latin-1")
    try:
        extra = mui_flags([text]) + amissl_flags([text])
    except FileNotFoundError as e:
        return {"sdk": str(e)}
    out = {}
    for nombre, flags in VARIANTES.items():
        o = d / f"prog{nombre}.o"
        r = subprocess.run([GCC, "-noixemul", *FECHA, *flags, *extra, *opt_flags(), "-I/opt/amiga/m68k-amigaos/ndk-include",
                            "-c", "prog.c", "-o", o.name], cwd=d, capture_output=True, text=True, timeout=300)
        out[nombre] = hashlib.sha256(o.read_bytes()).hexdigest() if r.returncode == 0 else \
            "error: " + r.stderr.replace(str(d), "D")[-400:]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--guardar", action="store_true")
    ap.add_argument("-k", default="")
    ap.add_argument("-j", type=int, default=os.cpu_count())
    a = ap.parse_args()
    fs = [f for f in corpus() if a.k in f.name]
    ref = json.loads(REF.read_text()) if REF.exists() else None
    if not a.guardar and ref is None:
        sys.exit("falta la referencia: python3 tests/identicos_c.py --guardar (con el compilador de antes del cambio)")
    with tempfile.TemporaryDirectory() as tmp, cf.ThreadPoolExecutor(a.j) as ex:
        res = dict(zip((str(f.relative_to(REPO)) for f in fs), ex.map(lambda f: objetos(f, tmp), fs)))
        if a.guardar:
            REF.parent.mkdir(exist_ok=True)
            REF.write_text(json.dumps(res, indent=1, sort_keys=True))
            print(f"referencia: {REF} ({len(res)} programas)")
            return
        malos = [k for k in res if res[k] != ref.get(k)]
        # (build_date, @version: otra vez, por si cambió el segundo)
        for k in list(malos):
            if objetos(REPO / k, tmp) == ref.get(k):
                malos.remove(k)
    for k in malos:
        print("DISTINTO", k)
        for v in sorted(set(res[k]) | set(ref.get(k, {}))):
            if res[k].get(v) != ref.get(k, {}).get(v):
                print(f"  {v or 'normal'}: {str(ref.get(k, {}).get(v))[:200]!r} -> {str(res[k].get(v))[:200]!r}")
    print(f"{len(res) - len(malos)}/{len(res)} idénticos")
    sys.exit(1 if malos else 0)


if __name__ == "__main__":
    main()
