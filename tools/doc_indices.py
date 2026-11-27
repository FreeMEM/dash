#!/usr/bin/env python3
"""Índice y enlaces de vuelta en los documentos de docs/ (lo pidió Ferrán García, para leerlos en el Amiga con el
datatype de Markdown).

    python3 tools/doc_indices.py            # pone al día los documentos
    python3 tools/doc_indices.py --check    # solo dice cuáles no lo están (el runner lo comprueba)

En cada documento de DOCS (y su .en.md):
- un índice de sus apartados (##) antes del primero, entre <!-- indice --> y <!-- /indice -->; si el documento ya
  tiene el suyo escrito a mano (## Tabla de Contenidos), se usa ese;
- un ancla <a id="..."></a> antes de cada apartado, la misma que le da GitHub, para que los enlaces del índice
  vayan también donde no se sacan solas del título;
- al final de cada apartado, un enlace de vuelta al índice.
Todo lo que pone lo quita antes de ponerlo otra vez: se puede pasar las veces que haga falta. tools/gen_ayuda.py
lo quita con quitar() antes de leer los documentos. BUILTINS.md lo hace tools/gen_builtins_doc.py.
"""

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

DOCS = ["MANUAL_REFERENCIA", "QUICK_REFERENCE", "INSTALACION", "DOCUMENTACION_LENGUAJE", "SINTAXIS", "AMIGA_API",
        "MUI_DISEÑO", "MUI_EDITOR", "MINIGL", "COMPARATIVA", "AYUDA_FORMATO"]

TEXTOS = {
    "es": {"ancla": "indice", "titulo": "**Índice**", "volver": "[Volver al índice](#indice)"},
    "en": {"ancla": "index", "titulo": "**Index**", "volver": "[Back to the index](#index)"},
}
# los índices escritos a mano: si el documento tiene uno, los enlaces de vuelta van a él
A_MANO = re.compile(r"(tabla de contenidos|table of contents|índice|index|contenido|contents)$", re.I)
INICIO, FIN = "<!-- indice -->", "<!-- /indice -->"
ANCLA = re.compile(r'<a id="([^"]+)"></a>$')
VOLVER = re.compile(r"\[(Volver al índice|Back to the index)\]\(#[^)]+\)$")


def slug(titulo: str) -> str:
    """El ancla que GitHub le da a un título: en minúsculas, sin signos, con guiones en vez de espacios"""
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", titulo)          # de un enlace, su texto
    t = t.replace("`", "").strip().lower()
    t = re.sub(r"[^\w\- ]", "", t)
    return t.replace(" ", "-")


def quitar(md: str) -> str:
    """El documento sin lo que pone este programa"""
    lineas = md.split("\n")
    sal = []
    i = 0
    while i < len(lineas):
        l = lineas[i]
        if l.strip() == INICIO:
            while i < len(lineas) and lineas[i].strip() != FIN:
                i += 1
            i += 1
            if i < len(lineas) and not lineas[i].strip():
                i += 1
            continue
        if VOLVER.match(l.strip()):
            i += 1
            if i < len(lineas) and not lineas[i].strip():
                i += 1
            continue
        m = ANCLA.match(l.strip())
        if m:
            j = i + 1
            while j < len(lineas) and not lineas[j].strip():
                j += 1
            # (los títulos repetidos llevan -1, -2...)
            if (j < len(lineas) and lineas[j].startswith("## ")
                    and re.fullmatch(re.escape(slug(lineas[j][3:])) + r"(-\d+)?", m.group(1))):
                i = j
                continue
        sal.append(l)
        i += 1
    return "\n".join(sal)


def apartados(lineas: list) -> list:
    """(número de línea, título) de cada ## fuera de los bloques de código"""
    cod = False
    sal = []
    for n, l in enumerate(lineas):
        if l.strip().startswith("```"):
            cod = not cod
        elif not cod and l.startswith("## "):
            sal.append((n, l[3:].strip()))
    return sal


def poner(md: str, lang: str) -> str:
    t = TEXTOS[lang]
    lineas = quitar(md).split("\n")
    aps = apartados(lineas)
    if len(aps) < 2:
        return "\n".join(lineas)
    a_mano = [(n, ti) for n, ti in aps if A_MANO.match(ti)]
    ancla = slug(a_mano[0][1]) if a_mano else t["ancla"]
    volver = t["volver"].replace(f"(#{t['ancla']})", f"(#{ancla})")
    vistos = {}
    anclas = {}
    for n, ti in aps:
        s = slug(ti)
        if s in vistos:                                   # GitHub numera los repetidos
            vistos[s] += 1
            s = f"{s}-{vistos[s]}"
        else:
            vistos[s] = 0
        anclas[n] = s
    sal = []
    primero = aps[0][0]
    for n, l in enumerate(lineas):
        if n in anclas:
            if n != primero and not (a_mano and n == a_mano[0][0]):
                # el enlace de vuelta, al final del apartado de antes (antes de sus líneas en blanco y su ---)
                k = len(sal)
                while k > 0 and (not sal[k - 1].strip() or re.fullmatch(r"-{3,}", sal[k - 1].strip())):
                    k -= 1
                sal[k:k] = ["", volver]
            if n == primero and not a_mano:
                sal += [INICIO, f'<a id="{ancla}"></a>', "", t["titulo"], ""]
                sal += [f"- [{ti}](#{anclas[m]})" for m, ti in aps]
                sal += [FIN, ""]
            sal += [f'<a id="{anclas[n]}"></a>', ""]
        sal.append(l)
    # y al final del último
    k = len(sal)
    while k > 0 and not sal[k - 1].strip():
        k -= 1
    sal[k:k] = ["", volver]
    return "\n".join(sal)


def main():
    viejos = []
    for doc in DOCS:
        for lang, nombre in (("es", f"{doc}.md"), ("en", f"{doc}.en.md")):
            f = RAIZ / "docs" / nombre
            antes = f.read_text()
            despues = poner(antes, lang)
            if despues == antes:
                continue
            if "--check" in sys.argv:
                viejos.append(f"docs/{nombre}")
            else:
                f.write_text(despues)
                print(f"docs/{nombre}")
    if viejos:
        print(f"{', '.join(viejos)}: sin el índice al día: python3 tools/doc_indices.py")
        sys.exit(1)


if __name__ == "__main__":
    main()
