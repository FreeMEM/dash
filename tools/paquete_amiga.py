#!/usr/bin/env python3
"""El paquete de Dash 2.0 para el Amiga: el compilador (la orden dash), que corre en el propio Amiga (68000, OS 2.0 o superior), con sus
runtimes, la carpeta lib/ de los import, los ejemplos que compila y el instalador.

    python3 tools/paquete_amiga.py        →  build/paquete_amiga/Dash/...  y  build/dash-<versión>-amiga.lha

Construye dashc para el Amiga (make -C dashc amiga, con el gcc de bebbo) y prueba qué ejemplos compila dashc (los
que llevan C no van). Necesita el lha de 68k (/opt/amiga/bin/lha) para que el archivo guarde bien los atributos.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

raiz = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(raiz / "tools"))
from iconos_wb import cajon, documento, instalador, info, WBDRAWER, WBPROJECT   # noqa: E402


def situar(icono, x, y):
    """El icono en (x, y) de su cajón (do_CurrentX/Y; sin esto, el Workbench lo coloca donde quiere)."""
    b = bytearray(icono)
    b[58:62] = x.to_bytes(4, "big")
    b[62:66] = y.to_bytes(4, "big")
    return bytes(b)


def main():
    subprocess.run(["make", "-C", str(raiz / "dashc"), "amiga"], check=True, stdout=subprocess.DEVNULL)
    version = re.search(r"Dash (\S+)", subprocess.run([str(raiz / "dash"), "--version"], capture_output=True,
                                                      text=True).stdout).group(1)
    dest = raiz / "build/paquete_amiga"
    shutil.rmtree(dest, ignore_errors=True)
    caj = dest / "Dash"
    caj.mkdir(parents=True)
    (dest / "Dash.info").write_bytes(situar(info(cajon(), WBDRAWER), 10, 6))
    b = raiz / "dashc/build"
    # (en el Amiga la orden se llama dash, como en el PC; sus runtimes, dash_*.drt)
    shutil.copy(b / "dashc.amiga", caj / "dash")
    (caj / "dash").chmod(0o755)
    for drt in ("mc", "fpu", "fpu_mc"):
        shutil.copy(b / f"dashc_{drt}.drt", caj / f"dash_{drt}.drt")
    shutil.copytree(raiz / "lib", caj / "lib", ignore=shutil.ignore_patterns("__pycache__"))
    # los ejemplos que compila dashc (en el PC, con el mismo dashc)
    (caj / "examples").mkdir()
    fuera = []
    with __import__("tempfile").TemporaryDirectory() as tmp:
        for f in sorted((raiz / "examples").iterdir()):
            if f.suffix not in (".dash", ".dashui"):
                continue
            r = subprocess.run([str(raiz / "dashc/dashc"), str(f), "-o", os.path.join(tmp, "x")],
                               cwd=raiz, capture_output=True, text=True)
            if r.returncode == 0:
                shutil.copy(f, caj / "examples" / f.name)
            else:
                fuera.append(f.name)
    # Forja (el IDE de Dash) e Inferencia (la IA que programa en el Amiga por ARexx con Forja), ya empaquetadas por su
    # tools/paquete.py en build/paquete/ de su proyecto (FORJA y INFERENCIA, o ~/Projects/forja e inferencia): sus
    # cajones van dentro del de Dash, y el instalador los copia con él. Si falta alguna, el paquete sale sin ella.
    for nombre, var in (("Forja", "FORJA"), ("Inferencia", "INFERENCIA")):
        pq = Path(os.environ.get(var) or Path.home() / "Projects" / nombre.lower()) / "build/paquete"
        if (pq / nombre).is_dir():
            shutil.copytree(pq / nombre, caj / nombre)
            if (pq / f"{nombre}.info").exists():
                shutil.copy(pq / f"{nombre}.info", caj / f"{nombre}.info")
        else:
            print(f"sin {nombre}: falta {pq / nombre} (python3 tools/paquete.py en su proyecto)")
    # el Amiga lee ISO-8859-1: el script (con el número de la versión) y los textos, de UTF-8 a Latin-1
    (caj / "Instalar").write_bytes((raiz / "paquete/Instalar").read_text().replace("@VERSION@", version)
                                   .encode("latin-1"))
    (caj / "Instalar.info").write_bytes(
        situar(info(instalador(), WBPROJECT, herramienta="Installer",
                    tooltypes=["APPNAME=Dash", "MINUSER=AVERAGE", "DEFUSER=AVERAGE"]), 10, 6))
    (caj / "LEEME").write_bytes((raiz / "README.es.md").read_text().encode("latin-1", "replace"))
    (caj / "LEEME.info").write_bytes(situar(info(documento(), WBPROJECT, herramienta="SYS:Utilities/MultiView"), 90, 6))
    (caj / "README").write_bytes((raiz / "README.md").read_text().encode("latin-1", "replace"))
    (caj / "README.info").write_bytes(situar(info(documento(), WBPROJECT, herramienta="SYS:Utilities/MultiView"), 170, 6))
    shutil.copy(raiz / "LICENSE", caj / "LICENSE")
    lha = raiz / f"build/dash-{version}-amiga.lha"
    lha.unlink(missing_ok=True)
    ficheros = sorted(os.path.relpath(os.path.join(d, f), dest) for d, _, fs in os.walk(caj) for f in fs)
    subprocess.run(["/opt/amiga/bin/lha", "ao5q", str(lha), "Dash", "Dash.info"] + ficheros, cwd=dest, check=True)
    print(lha)
    if fuera:
        print("ejemplos fuera (llevan C):", " ".join(fuera))


if __name__ == "__main__":
    main()
