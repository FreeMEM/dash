#!/usr/bin/env python3
"""Hace un paquete para AmigaOS 3.x: el .lha con el cajón del programa y su .readme, listos para Aminet y para
Hangar (la tienda de hangar.freemem.space), que leen el mismo fichero.

    python3 tools/paquete_hangar.py CAJON [-o SALIDA]

CAJON es el cajón del programa tal como se instalará (por ejemplo build/Trasfondo, con el programa, sus iconos y
lo que lleve). Dentro, un fichero paquete.txt con los campos del .readme de Aminet, uno por línea, y debajo, tras
una línea en blanco, la descripción:

    Short:        Monitor de recursos en el fondo del Workbench
    Author:       FreeMEM
    Uploader:     correo@del.autor
    Type:         util/wb
    Version:      2.8.5
    Architecture: m68k-amigaos >= 3.1
    Requires:     OS 3.1, 68020, MUI 3.8, reqtools.library 38
    Provides:     trasfondo.library 2
    Install:      drawer Trasfondo
    Run:          Trasfondo/Trasfondo
    License:      MIT
    URL:          https://trasfondo.freemem.space

    Lo que hace el programa, en varias líneas.

Short, Author, Type y Version hacen falta. Requires, Provides, Install, Run y License los usa Hangar para saber
qué necesita, qué trae para otros programas, dónde se instala y qué ejecutar (Aminet los ignora). Sale
SALIDA/Nombre.lha (con Nombre.readme también dentro) y SALIDA/Nombre.readme, en Latin-1. El .lha se hace con el
lha de 68k (/opt/amiga/bin/lha, o $LHA), que guarda bien los atributos del Amiga.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ORDEN = ["Short", "Author", "Uploader", "Type", "Version", "Replaces", "Architecture", "Requires", "Provides",
         "Install", "Run", "License", "URL", "Distribution"]
OBLIGATORIOS = ["Short", "Author", "Type", "Version"]
CAJONES_AMINET = {"biz", "comm", "demo", "dev", "disk", "docs", "driver", "game", "gfx", "hard", "misc", "mods",
                  "mus", "pix", "text", "util"}


def leer_paquete(texto):
    """Los campos (en su orden) y la descripción de un paquete.txt"""
    campos, desc, en_desc = {}, [], False
    for linea in texto.splitlines():
        if en_desc:
            desc.append(linea.rstrip())
            continue
        if not linea.strip():
            en_desc = bool(campos)
            continue
        m = re.match(r"^([A-Za-z]+):\s*(.*)$", linea)
        if not m:
            raise ValueError(f"no entiendo esta línea de paquete.txt: {linea!r} (va Campo: valor)")
        campos[m.group(1).capitalize() if m.group(1).upper() != "URL" else "URL"] = m.group(2).strip()
    return campos, "\n".join(desc).strip()


def comprobar(campos):
    """Lo que falta o no cuadra; lista vacía si está bien"""
    faltas = [f"falta {k}:" for k in OBLIGATORIOS if not campos.get(k)]
    if len(campos.get("Short", "")) > 40:
        faltas.append(f"Short tiene {len(campos['Short'])} letras: Aminet admite 40")
    tipo = campos.get("Type", "")
    if tipo and (tipo.count("/") != 1 or tipo.split("/")[0] not in CAJONES_AMINET):
        faltas.append(f"Type {tipo!r} no es una categoría de Aminet (como util/wb o game/shoot)")
    inst = campos.get("Install", "")
    if inst and not re.match(r"^(drawer\s+\S+|system\s+.+)$", inst):
        faltas.append("Install va como 'drawer Nombre' o 'system LIBS:x.library, C:x'")
    for t in campos.get("Provides", "").split(","):
        if t.strip() and not re.match(r"^\S+\.(library|device|datatype|mcc|mcp|font|resource)(\s+\d+(\.\d+)?)?$", t.strip()):
            faltas.append(f"Provides {t.strip()!r}: va como 'nombre.library 2'")
    for k in campos:
        if k not in ORDEN:
            faltas.append(f"campo desconocido {k}:")
    try:
        "".join(campos.values()).encode("latin-1")
    except UnicodeEncodeError:
        faltas.append("hay letras que no caben en Latin-1 (lo que lee el Amiga)")
    return faltas


def readme(campos, desc):
    """El .readme con el formato de Aminet: cada campo con su valor en la columna 15"""
    c = dict(campos)
    c.setdefault("Architecture", "m68k-amigaos")
    c.setdefault("Distribution", "Aminet")
    lineas = [f"{k + ':':<14}{c[k]}" for k in ORDEN if c.get(k)]
    return "\n".join(lineas) + "\n\n" + (desc or c["Short"]) + "\n"


def main():
    ap = argparse.ArgumentParser(description="El .lha y el .readme de un programa para Aminet y Hangar")
    ap.add_argument("cajon", help="el cajón del programa, con su paquete.txt dentro")
    ap.add_argument("-o", "--salida", default=".", help="dónde dejar Nombre.lha y Nombre.readme")
    a = ap.parse_args()
    cajon = Path(a.cajon).resolve()
    pt = cajon / "paquete.txt"
    if not pt.exists():
        sys.exit(f"falta {pt} (mira la ayuda: python3 {sys.argv[0]} --help)")
    campos, desc = leer_paquete(pt.read_text(encoding="utf-8"))
    faltas = comprobar(campos)
    if faltas:
        sys.exit("paquete.txt no vale:\n  " + "\n  ".join(faltas))
    nombre = cajon.name
    texto = readme(campos, desc).encode("latin-1", "replace")
    salida = Path(a.salida).resolve()
    salida.mkdir(parents=True, exist_ok=True)
    (salida / f"{nombre}.readme").write_bytes(texto)
    lha = os.environ.get("LHA", "/opt/amiga/bin/lha")
    if not shutil.which(lha):
        sys.exit(f"no encuentro el lha de 68k ({lha}); pon su ruta en $LHA")
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        shutil.copytree(cajon, t / nombre, ignore=shutil.ignore_patterns("paquete.txt"))
        info = cajon.parent / f"{nombre}.info"     # el icono del cajón, si lo hay al lado
        if info.exists():
            shutil.copy(info, t / info.name)
        (t / f"{nombre}.readme").write_bytes(texto)
        todos = [str(p.relative_to(t)) for p in sorted(t.rglob("*")) if p.is_file()]
        destino = salida / f"{nombre}.lha"
        if destino.exists():
            destino.unlink()
        subprocess.run([lha, "ao5q", str(destino)] + todos, cwd=t, check=True)
    print(f"{destino} y {salida / (nombre + '.readme')}")


if __name__ == "__main__":
    main()
