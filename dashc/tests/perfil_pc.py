#!/usr/bin/env python3
"""El tiempo por rutina del runtime (D15): junta las líneas "perfil-pc:" de un programa compilado con
`dashc --perfil` (el sitio del PC en cada VBlank, en trozos de 16 bytes del hunk de código) con el mapa del
enlazador de la misma compilación (`DASHC_MAPA=1`, a la salida de error), y dice dónde se fue el tiempo.

    DASHC_MAPA=1 ./dash --perfil prog.dash -o prog 2> mapa.txt
    (ejecutarlo en el emulador y guardar su salida en salida.txt)
    python3 dashc/tests/perfil_pc.py mapa.txt salida.txt [--todas]

Lo de antes de la primera rutina del runtime es el código del programa (sus funciones, en la tabla de --perfil).
"""
import argparse
import bisect
import re
import sys


def leer_mapa(path):
    """[(sitio, tamaño, nombre)] de los hunks de código del runtime, por sitio"""
    rutinas = []
    for linea in open(path, encoding="utf-8", errors="replace"):
        m = re.match(r"\s*(\d+) C ([0-9a-f]{6}) (.*?)(?: <- .*)?$", linea)
        if m:
            rutinas.append((int(m.group(2), 16), int(m.group(1)), m.group(3)))
    rutinas.sort()
    return rutinas


def leer_muestras(path):
    """{sitio: muestras} y las de fuera del programa"""
    cuenta, fuera = {}, 0
    for linea in open(path, encoding="utf-8", errors="replace"):
        if not linea.startswith("perfil-pc:"):
            continue
        m = re.match(r"perfil-pc: fuera (\d+)", linea)
        if m:
            fuera = int(m.group(1))
            continue
        for sitio, n in re.findall(r"([0-9a-fA-F]+):(\d+)", linea):
            cuenta[int(sitio, 16)] = cuenta.get(int(sitio, 16), 0) + int(n)
    return cuenta, fuera


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mapa")
    ap.add_argument("salida")
    ap.add_argument("--todas", action="store_true", help="también las que tienen menos del 0,5 %%")
    args = ap.parse_args()
    rutinas = leer_mapa(args.mapa)
    cuenta, fuera = leer_muestras(args.salida)
    if not rutinas or not cuenta:
        sys.exit("perfil_pc: sin mapa o sin muestras (¿DASHC_MAPA=1 y --perfil?)")
    sitios = [r[0] for r in rutinas]
    por = {}
    for sitio, n in cuenta.items():
        i = bisect.bisect_right(sitios, sitio) - 1
        if i < 0:
            nombre = "(el código del programa)"
        elif sitio < rutinas[i][0] + rutinas[i][1] + 16:
            nombre = rutinas[i][2]
        else:
            nombre = "(?)"
        por[nombre] = por.get(nombre, 0) + n
    total = sum(por.values()) + fuera
    print(f"{total} muestras; {fuera} fuera del programa (la ROM u otras tareas)")
    for nombre, n in sorted(por.items(), key=lambda x: -x[1]):
        if n * 200 < total and not args.todas:
            break
        print(f"{n * 100 / total:5.1f}% {n:6d}  {nombre}")


if __name__ == "__main__":
    main()
