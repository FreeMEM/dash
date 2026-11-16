#!/usr/bin/env python3
"""La ayuda de Dash para el Amiga, sacada de su documentación: un fichero con índice para que un programa (Forja) lo
lea a trozos, y el mismo contenido en AmigaGuide, para MultiView. En castellano y en inglés.

    python3 tools/gen_ayuda.py                 →  build/ayuda/Dash.ayuda, Dash_en.ayuda, Dash.guide, Dash_en.guide
    python3 tools/gen_ayuda.py --salida DIR    →  en DIR
    python3 tools/gen_ayuda.py --check         →  lo genera en memoria y lo comprueba, sin escribir nada

Fuentes: los builtins (compiler/amiga_builtins.py, compiler/builtins_es.py, compiler/builtins_doc/), sus ejemplos
(tests/test_doc_*.dash), docs/SINTAXIS(.en).md y docs/MANUAL_REFERENCIA(.en).md. El formato del .ayuda está en
docs/AYUDA_FORMATO.md. Los ficheros no van a git: los hace tools/paquete_amiga.py al empaquetar.
"""
import argparse
import datetime
import re
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "tools"))

import compiler  # noqa: E402
import compiler.amiga_builtins as ab  # noqa: E402
from compiler import builtins_doc  # noqa: E402
from compiler.builtins_es import DESC_ES  # noqa: E402
from gen_builtins_doc import GROUPS, TEXTS, example  # noqa: E402

ANCHO = 76                 # columnas del texto (con el prefijo de línea, 77; una ventana de 80 en topaz 8)
FORMATO = 1                # versión del formato del .ayuda (docs/AYUDA_FORMATO.md)
CI, CF = "\x01", "\x02"
MAX_PALABRA = 24           # las palabras más largas no van al índice de palabras (los nombres sí, en el de nombres)
COMUNES = 0.25             # ni las que salen en más de esta parte de las fichas    # marcas internas de un `código en línea` (en el AmigaGuide, enlace si es una ficha)

TEXTOS = {
    "es": {
        "inicio": "Dash {v}: ayuda",
        "intro": "La ayuda del lenguaje Dash y de sus {n} funciones (builtins). Sale de la documentación de Dash "
                 "(docs/BUILTINS.md, docs/SINTAXIS.md y docs/MANUAL_REFERENCIA.md), con tools/gen_ayuda.py.",
        "sintaxis": "Sintaxis en una página", "manual": "Manual de referencia", "grupos": "Funciones por grupo",
        "indice": "Índice alfabético",
        "buscar": "Para buscar una función o una palabra del lenguaje (if, struct, EventLoop...), el índice.",
        "grupos_intro": "Las funciones de Dash por grupos, como en docs/BUILTINS.md.",
        "manual_intro": "Los capítulos del manual de referencia (docs/MANUAL_REFERENCIA.md).",
        "indice_intro": "Funciones, grupos, capítulos del manual y palabras del lenguaje, por orden alfabético.",
        "capitulo": "Apartados", "funciones": "Funciones", "ejemplo": "Ejemplo",
        "ejemplo_de": "Ejemplo (de {p})", "ejemplo_grupo": "Ejemplo ({p})",
        "ver": "Ver también", "grupo": "Grupo", "dashos": "En DashOS",
        "dashos_si": "sí (./dash --dashos).", "dashos_no": "no; allí es un error al compilar.",
        "dashos_solo": "solo allí (./dash --dashos); en el Amiga es un error al compilar.",
        "sin_impl": "Sin implementar: está declarada pero no tiene código.",
        "n_funciones": "{n} funciones",
        "volver": "Inicio",
    },
    "en": {
        "inicio": "Dash {v}: help",
        "intro": "The help of the Dash language and its {n} functions (builtins). It comes from Dash's documentation "
                 "(docs/BUILTINS.en.md, docs/SINTAXIS.en.md and docs/MANUAL_REFERENCIA.en.md), with "
                 "tools/gen_ayuda.py.",
        "sintaxis": "Syntax on one page", "manual": "Reference manual", "grupos": "Functions by group",
        "indice": "Alphabetical index",
        "buscar": "To look up a function or a word of the language (if, struct, EventLoop...), the index.",
        "grupos_intro": "Dash's functions by group, as in docs/BUILTINS.en.md.",
        "manual_intro": "The chapters of the reference manual (docs/MANUAL_REFERENCIA.en.md).",
        "indice_intro": "Functions, groups, chapters of the manual and words of the language, in alphabetical order.",
        "capitulo": "Sections", "funciones": "Functions", "ejemplo": "Example",
        "ejemplo_de": "Example (from {p})", "ejemplo_grupo": "Example ({p})",
        "ver": "See also", "grupo": "Group", "dashos": "On DashOS",
        "dashos_si": "yes (./dash --dashos).", "dashos_no": "no; there it is a compile error.",
        "dashos_solo": "only there (./dash --dashos); on the Amiga it is a compile error.",
        "sin_impl": "Not implemented: it is declared but has no code.",
        "n_funciones": "{n} functions",
        "volver": "Contents",
    },
}

# Palabras del lenguaje (y temas) que llevan a un apartado del manual: (capítulo, comienzo del título del apartado en
# docs/MANUAL_REFERENCIA.md, sin acentos ni mayúsculas; vacío: el capítulo). El manual en inglés tiene los mismos
# apartados en el mismo orden (se comprueba), así que la clave vale para los dos.
PALABRAS_LENGUAJE = {
    "if": ("6", "if / else"), "else": ("6", "if / else"), "elif": ("6", "if / elif"), "while": ("6", "while"),
    "for": ("6", "for con rango"), "step": ("6", "for con rango"), "break": ("6", "break y continue"),
    "continue": ("6", "break y continue"), "stop": ("6", "comandos de control"), "wait": ("6", "comandos de control"),
    "print": ("6", "comandos de control"), "func": ("7", "definicion basica"), "return": ("7", "definicion basica"),
    "fn": ("7", "funciones como valores"), "lambda": ("7", "funciones como valores"), "struct": ("8", "definicion"),
    "self": ("8", "metodos"), "interface": ("8", "interfaces"), "enum": ("9", "definicion"), "const": ("4", ""),
    "var": ("3", "variables globales"), "fixed": ("3", "fixed"), "double": ("3", "double"), "float": ("3", "float"),
    "int": ("3", "tipos de datos"), "string": ("3", "tipos de datos"), "bool": ("3", "tipos de datos"),
    "nil": ("10", "nil"), "in": ("5", "pertenencia"), "and": ("5", "operadores logicos"),
    "or": ("5", "operadores logicos"), "not": ("5", "operadores logicos"), "array": ("10", ""),
    "dict": ("10", "diccionarios"), "weak": ("17", "campos `weak`"), "import": ("21", "importar modulo"),
    "main": ("2", "estructura basica"), "window": ("12", "definicion de ventana"), "eventloop": ("12", "event loop"),
    "on": ("12", "event loop"), "screen": ("11", ""), "native": ("21", "codigo c"), "extern": ("21", "codigo c"),
    "link": ("21", "c de fuera"), "header": ("21", "c de fuera"), "catalog": ("21", "traducciones"),
    "memcheck": ("17", "buscar fallos"), "arena": ("17", "arena allocator"), "dashos": ("25", ""),
    "gadtools": ("19", ""), "reaction": ("20", ""), "mui": ("20b", ""),
}

# palabras que no se indexan (salen en casi todas las fichas)
VACIAS = set("""
a al algo como con cual cuando de del desde donde dos el en entre era es esa ese eso esta este esto ha hace hay la las
le lo los mas me mismo muy no nos o otra otro para pero poco por que se si sin sobre solo su sus tambien te tiene un
una uno unos y ya
the an and are as at be but by can for from has have if in into is it its of on one or so than that the their them
then there these this to too two was what when which while who will with without you your
""".split())


# --- caracteres: el Amiga lee ISO-8859-1 -------------------------------------------------------------------------

TRANSLIT = {"€": "EUR", "—": "-", "–": "-", "“": '"', "”": '"', "‘": "'", "’": "'", "…": "...", "→": "->",
            "←": "<-", "≤": "<=", "≥": ">=", "≠": "!=", "•": "-", "✓": "si", "✗": "no"}


def latin1(t: str) -> str:
    """El texto con lo que no está en Latin-1 cambiado por su equivalente en ASCII ("?" si no tiene)"""
    if all(ord(c) < 256 for c in t):
        return t
    return "".join(c if ord(c) < 256 else TRANSLIT.get(c, "?") for c in t)


# de à (0xE0) a ÿ (0xFF): la letra sin acento, o un espacio (lib/ayuda.dash, ayuda_plegar, usa la misma tabla)
PLIEGUE = "aaaaaa ceeeeiiii nooooo  uuuuy y"


def plegar(t: str) -> str:
    """Minúsculas y sin acentos: así se guardan las palabras del índice (docs/AYUDA_FORMATO.md)"""
    return "".join(PLIEGUE[ord(c) - 0xE0] if 0xE0 <= ord(c) <= 0xFF else c for c in latin1(t).lower())


def sin_marcas(t: str) -> str:
    return t.replace(CI, "").replace(CF, "")


# --- Markdown a líneas ---------------------------------------------------------------------------------------------

@dataclass
class Linea:
    tipo: str            # T texto, C código, H subtítulo, L enlace, B en blanco
    texto: str = ""
    destino: str = ""    # L: la clave de la ficha
    indexar: bool = True  # False: un texto que pone el generador (Ver también, En DashOS...), fuera del índice


@dataclass
class Ficha:
    clave: str
    tipo: str            # F función, G grupo, M manual, S sintaxis, I portada e índices
    titulo: str
    campos: list = field(default_factory=list)   # (nombre, valor)
    lineas: list = field(default_factory=list)


def limpiar(t: str) -> str:
    """Una línea de Markdown a texto llano: el código en línea queda entre CI y CF; enlaces, negrita y HTML fuera"""
    codigos = []

    def guardar(m):
        codigos.append(m.group(1) or m.group(2))
        return f"\x03{len(codigos) - 1}\x04"
    t = re.sub(r"``\s*(.+?)\s*``|`([^`]+)`", guardar, t)
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", t)
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"\1", t)
    t = re.sub(r"__([^_]+)__", r"\1", t)
    t = re.sub(r"(?<![\w*])\*([^*\s][^*]*)\*(?![\w*])", r"\1", t)
    t = re.sub(r"<[^>]+>", "", t)
    t = t.replace("\\|", "|").replace("\\*", "*").replace("\\_", "_")
    t = re.sub(r"\x03(\d+)\x04", lambda m: CI + codigos[int(m.group(1))] + CF, t)
    return latin1(t.strip())


def cortar(t: str, sangria: str = "", primera: str = None) -> list:
    return textwrap.wrap(t, ANCHO, initial_indent=primera if primera is not None else sangria,
                         subsequent_indent=sangria, break_long_words=False, break_on_hyphens=False) or [""]


LISTA = re.compile(r"(\s*)([-*+]|\d+\.)\s+(.*)")


def md_lineas(md: str) -> list:
    """Markdown a líneas de ficha: párrafos y listas cortados a ANCHO, código tal cual, tablas alineadas"""
    sal = []
    parrafo = []
    lineas = md.splitlines()
    i = 0

    def blanco():
        if sal and sal[-1].tipo != "B":
            sal.append(Linea("B"))

    def soltar():
        if parrafo:
            sal.extend(Linea("T", l) for l in cortar(limpiar(" ".join(parrafo))))
            blanco()
            parrafo.clear()

    while i < len(lineas):
        l = lineas[i].rstrip()
        s = l.strip()
        if s.startswith("```"):
            soltar()
            i += 1
            while i < len(lineas) and not lineas[i].strip().startswith("```"):
                sal.append(Linea("C", latin1(lineas[i].rstrip().expandtabs(4))))
                i += 1
            blanco()
        elif s.startswith("|"):
            soltar()
            filas = []
            while i < len(lineas) and lineas[i].strip().startswith("|"):
                celdas = [limpiar(c) for c in re.split(r"(?<!\\)\|", lineas[i].strip().strip("|"))]
                if not all(re.fullmatch(r":?-+:?", c) for c in celdas if c):
                    filas.append(celdas)
                i += 1
            sal.extend(tabla(filas))
            blanco()
            continue
        elif re.match(r"#{1,6} ", s):
            soltar()
            t = limpiar(s.lstrip("#"))
            if t:
                sal.append(Linea("H", t))
        elif re.fullmatch(r"-{3,}|\*{3,}", s):
            soltar()
        elif LISTA.match(l):
            soltar()
            m = LISTA.match(l)
            base = len(m.group(1).expandtabs())
            marca = "-" if m.group(2) in "-*+" else m.group(2)
            texto = [m.group(3)]
            i += 1
            while (i < len(lineas) and lineas[i].strip() and not LISTA.match(lineas[i])
                   and not lineas[i].strip().startswith(("```", "|", "#"))
                   and len(lineas[i]) - len(lineas[i].lstrip()) > base):
                texto.append(lineas[i].strip())
                i += 1
            sangria = " " * (base + len(marca) + 1)
            sal.extend(Linea("T", x) for x in cortar(limpiar(" ".join(texto)), sangria, " " * base + marca + " "))
            if i >= len(lineas) or not LISTA.match(lineas[i]):
                blanco()
            continue
        elif not s:
            soltar()
        elif s.startswith(">"):
            parrafo.append(s.lstrip("> "))
        else:
            parrafo.append(s)
        i += 1
    soltar()
    while sal and sal[-1].tipo == "B":
        sal.pop()
    return sal


def tabla(filas: list) -> list:
    """Una tabla en columnas alineadas si cabe en ANCHO; si no, la primera columna y debajo, con sangría, el resto"""
    if not filas:
        return []
    n = max(len(f) for f in filas)
    filas = [f + [""] * (n - len(f)) for f in filas]
    anchos = [max(len(sin_marcas(f[c])) for f in filas) for c in range(n)]
    if sum(anchos) + 2 * (n - 1) <= ANCHO:
        sal = []
        for k, f in enumerate(filas):
            celdas = [f[c] + " " * (anchos[c] - len(sin_marcas(f[c]))) for c in range(n)]
            sal.append(Linea("T", "  ".join(celdas).rstrip()))
            if k == 0 and len(filas) > 1:
                sal.append(Linea("T", "  ".join("-" * a for a in anchos)))
        return sal
    sal = []
    for k, f in enumerate(filas):
        if k == 0 and len(filas) > 1:
            continue                                   # (los títulos de las columnas)
        sal.extend(Linea("T", x) for x in cortar(f[0]))
        resto = " - ".join(c for c in f[1:] if c)
        if resto:
            sal.extend(Linea("T", x) for x in cortar(resto, "    "))
    return sal


# --- las fichas ------------------------------------------------------------------------------------------------

def tipo_dash(b, lang):
    return TEXTS[lang]["types"].get(b.return_type, b.return_type) if b.return_type != "void" else ""


def firma(nombre, lang):
    b = ab.ALL_BUILTINS[nombre]
    ret = tipo_dash(b, lang)
    return f"{nombre}({', '.join(b.params)})" + (f" -> {ret}" if ret else "")


def desc_corta(nombre, lang):
    b = ab.ALL_BUILTINS[nombre]
    return latin1(DESC_ES[nombre] if lang == "es" else b.description)


def estado_dashos(nombre):
    b = ab.ALL_BUILTINS[nombre]
    if b.needs_dashos:
        return "solo"
    return "no" if ab.dashos_missing(nombre) else "si"


def extracto(nombre, codigo):
    """Las líneas del ejemplo de un grupo alrededor del primer uso de la función (hasta 3 antes y 3 después, sin pasar
    de un blanco ni salir de su bloque), o None si no la usa"""
    lineas = codigo.splitlines()
    pat = re.compile(r"\b" + re.escape(nombre) + r"\s*\(")

    def sangria(x):
        return len(x) - len(x.lstrip())
    for k, l in enumerate(lineas):
        if l.lstrip().startswith("#") or not pat.search(l.split(" #", 1)[0]):
            continue
        a = k
        while (a > 0 and k - a < 3 and lineas[a - 1].strip() and sangria(lineas[a - 1]) <= sangria(l)
               and lineas[a - 1].strip() != "end"):
            a -= 1
        z = k
        while z + 1 < len(lineas) and z - k < 3 and lineas[z + 1].strip() and sangria(lineas[z + 1]) >= sangria(l):
            z += 1
        s = min(sangria(x) for x in lineas[a:z + 1] if x.strip())
        return [x[s:] for x in lineas[a:z + 1]]
    return None


def ejemplos_grupo(attr):
    ex = builtins_doc.GROUPS.get(attr, {}).get("example") or []
    return [ex] if isinstance(ex, str) else list(ex)


def fichas_builtins(lang, tx):
    fichas, grupos = [], []
    for attr, t_es, t_en in GROUPS:
        clave = attr.lower()
        titulo = latin1(t_es if lang == "es" else t_en)
        grupo = getattr(ab, attr)
        g = Ficha(clave, "G", titulo, [("funciones", str(len(grupo)))])
        gdoc = builtins_doc.GROUPS.get(attr)
        if gdoc:
            g.lineas += md_lineas(gdoc[lang]) + [Linea("B")]
        codigos = []
        for p in ejemplos_grupo(attr):
            codigo = latin1(example(p))
            codigos.append((p, codigo))
            g.campos.append(("ejemplo", p))
            g.lineas += [Linea("H", tx["ejemplo_grupo"].format(p=p), indexar=False)]
            g.lineas += [Linea("C", x.expandtabs(4)) for x in codigo.splitlines()] + [Linea("B")]
        g.lineas.append(Linea("H", tx["funciones"], indexar=False))
        for nombre in grupo:
            g.lineas.append(Linea("L", f"{firma(nombre, lang)}: {desc_corta(nombre, lang)}", nombre))
        g.lineas += [Linea("B"), Linea("L", tx["grupos"], "grupos")]
        fichas.append(g)
        grupos.append(g)
        for nombre in grupo:
            fichas.append(ficha_funcion(nombre, clave, titulo, codigos, lang, tx))
    return fichas, grupos


def ficha_funcion(nombre, grupo, titulo_grupo, codigos, lang, tx):
    b = ab.ALL_BUILTINS[nombre]
    f = Ficha(nombre, "F", nombre)
    f.campos = [("firma", firma(nombre, lang)), ("devuelve", tipo_dash(b, lang) or "-"), ("grupo", grupo),
                ("dashos", estado_dashos(nombre))]
    f.lineas = [Linea("H", firma(nombre, lang), indexar=False)]
    f.lineas += [Linea("T", x) for x in cortar(desc_corta(nombre, lang).rstrip(".") + ".")] + [Linea("B")]
    from compiler.codegen import unimplemented_builtins
    if nombre in unimplemented_builtins():
        f.campos.append(("estado", "sin implementar"))
        f.lineas += [Linea("T", x) for x in cortar(tx["sin_impl"])] + [Linea("B")]
    doc = builtins_doc.FUNCS.get(nombre)
    if doc:
        f.lineas += md_lineas(doc[lang]) + [Linea("B")]
    if not (doc and "```" in doc[lang]):
        for p, codigo in codigos:
            ex = extracto(nombre, codigo)
            if ex:
                f.campos.append(("ejemplo", p))
                f.lineas += [Linea("H", tx["ejemplo_de"].format(p=p), indexar=False)]
                f.lineas += [Linea("C", x.expandtabs(4)) for x in ex] + [Linea("B")]
                break
    if doc and doc.get("see"):
        f.lineas.append(Linea("H", tx["ver"], indexar=False))
        for s in doc["see"]:
            f.lineas.append(Linea("L", f"{firma(s, lang)}: {desc_corta(s, lang)}", s))
        f.lineas.append(Linea("B"))
    f.lineas.append(Linea("T", f"{tx['dashos']}: " + tx["dashos_" + estado_dashos(nombre)], indexar=False))
    f.lineas += [Linea("B"), Linea("L", f"{tx['grupo']}: {titulo_grupo}", grupo)]
    return f


def secciones_md(md: str):
    """Los capítulos (##) y apartados (###) de un Markdown, sin los que están dentro de un bloque de código:
    [(título, texto de antes del primer ###, [(título, texto)])]"""
    caps = []
    cod = False
    actual = None
    for l in md.splitlines():
        if l.strip().startswith("```"):
            cod = not cod
        if not cod and l.startswith("## "):
            caps.append([l[3:].strip(), [], []])
            actual = caps[-1][1]
            continue
        if not cod and l.startswith("### ") and caps:
            caps[-1][2].append([l[4:].strip(), []])
            actual = caps[-1][2][-1][1]
            continue
        if actual is not None:
            actual.append(l)
    return [(t, "\n".join(intro), [(st, "\n".join(x)) for st, x in subs]) for t, intro, subs in caps]


def clave_capitulo(titulo, n):
    m = re.match(r"(\d+[a-z]?)\.\s", titulo)
    return "m" + (m.group(1) if m else f"x{n}")


def fichas_manual(lang, tx):
    """Una ficha por capítulo (su introducción y la lista de apartados) y otra por apartado"""
    nombre = "MANUAL_REFERENCIA.md" if lang == "es" else "MANUAL_REFERENCIA.en.md"
    caps = [c for c in secciones_md((RAIZ / "docs" / nombre).read_text())
            if not re.match(r"(tabla de contenidos|table of contents)", c[0], re.I)]
    fichas, secciones = [], []
    raiz = Ficha("manual", "I", latin1(tx["manual"]))
    raiz.lineas = [Linea("T", x) for x in cortar(tx["manual_intro"])] + [Linea("B")]
    for n, (titulo, intro, subs) in enumerate(caps):
        clave = clave_capitulo(titulo, n)
        cap = Ficha(clave, "M", limpiar(titulo).replace(CI, "").replace(CF, ""))
        cap.lineas = md_lineas(intro)
        if subs:
            cap.lineas += [Linea("B"), Linea("H", tx["capitulo"], indexar=False)]
        raiz.lineas.append(Linea("L", cap.titulo, clave))
        secciones.append((cap, 1))
        fichas.append(cap)
        hijos = []
        for k, (st, texto) in enumerate(subs, 1):
            sub = Ficha(f"{clave}_{k}", "M", sin_marcas(limpiar(st)))
            sub.lineas = md_lineas(texto) + [Linea("B"), Linea("L", cap.titulo, clave)]
            cap.lineas.append(Linea("L", sub.titulo, sub.clave))
            hijos.append(sub)
            secciones.append((sub, 2))
        cap.lineas += [Linea("B"), Linea("L", tx["manual"], "manual")]
        fichas += hijos
    return raiz, fichas, secciones, caps


def alias_lenguaje(caps_es):
    """PALABRAS_LENGUAJE: palabra -> clave de su ficha del manual"""
    out = {}
    for palabra, (num, comienzo) in PALABRAS_LENGUAJE.items():
        destino = None
        for n, (titulo, _, subs) in enumerate(caps_es):
            clave = clave_capitulo(titulo, n)
            if clave != "m" + num:
                continue
            if not comienzo:
                destino = clave
            for k, (st, _) in enumerate(subs, 1):
                if plegar(st).startswith(comienzo):
                    destino = f"{clave}_{k}"
                    break
        if destino is None:
            raise SystemExit(f"tools/gen_ayuda.py: PALABRAS_LENGUAJE: {palabra} no encuentra {num} {comienzo!r} en "
                             "docs/MANUAL_REFERENCIA.md")
        out[palabra] = destino
    return out


def generar(lang: str):
    """Todas las fichas de un idioma, en orden, y los índices: (fichas, alias, grupos, secciones)"""
    tx = TEXTOS[lang]
    v = compiler.__version__
    inicio = Ficha("inicio", "I", tx["inicio"].format(v=v))
    sint = Ficha("sintaxis", "S", latin1(tx["sintaxis"]))
    sint.lineas = md_lineas((RAIZ / "docs" / ("SINTAXIS.md" if lang == "es" else "SINTAXIS.en.md")).read_text())
    if sint.lineas and sint.lineas[0].tipo == "H":     # (su título: el de la ficha)
        sint.lineas = sint.lineas[1:]
    sint.lineas += [Linea("B"), Linea("L", tx["volver"], "inicio")]
    fb, grupos = fichas_builtins(lang, tx)
    raiz_m, fm, secciones, caps = fichas_manual(lang, tx)
    raiz_m.lineas += [Linea("B"), Linea("L", tx["volver"], "inicio")]
    caps_es = secciones_md((RAIZ / "docs/MANUAL_REFERENCIA.md").read_text())
    caps_es = [c for c in caps_es if not re.match(r"tabla de contenidos", c[0], re.I)]
    if [len(c[2]) for c in caps_es] != [len(c[2]) for c in caps]:
        raise SystemExit("tools/gen_ayuda.py: MANUAL_REFERENCIA.md y .en.md no tienen los mismos apartados")
    alias = alias_lenguaje(caps_es)
    gr = Ficha("grupos", "I", latin1(tx["grupos"]))
    gr.lineas = [Linea("T", x) for x in cortar(tx["grupos_intro"])] + [Linea("B")]
    for g in grupos:
        gr.lineas.append(Linea("L", f"{g.titulo} ({tx['n_funciones'].format(n=dict(g.campos)['funciones'])})",
                               g.clave))
    gr.lineas += [Linea("B"), Linea("L", tx["volver"], "inicio")]
    ind = Ficha("indice", "I", latin1(tx["indice"]))
    inicio.lineas = [Linea("T", x) for x in cortar(tx["intro"].format(n=len(ab.ALL_BUILTINS)))] + [Linea("B")]
    inicio.lineas += [Linea("L", sint.titulo, "sintaxis"), Linea("L", raiz_m.titulo, "manual"),
                      Linea("L", gr.titulo, "grupos"), Linea("L", ind.titulo, "indice"), Linea("B")]
    inicio.lineas += [Linea("T", x) for x in cortar(latin1(tx["buscar"]))]
    fichas = [inicio, sint, raiz_m] + fm + [gr] + fb + [ind]
    por_clave = {f.clave: f for f in fichas}
    # el índice alfabético: cada nombre (las claves y las palabras del lenguaje) con su título
    ind.lineas = [Linea("T", x) for x in cortar(tx["indice_intro"])] + [Linea("B")]
    nombres = {}
    for f in fichas:
        if f.tipo == "F":
            nombres[f.clave] = (f.clave, f.clave)
        elif f.tipo in "GM":
            nombres[plegar(f.titulo) + "\x00" + f.clave] = (f.titulo, f.clave)
    for palabra, destino in alias.items():
        nombres[palabra + "\x00"] = (f"{palabra}: {por_clave[destino].titulo}", destino)
    # (por la primera letra: sin el número del capítulo ni los guiones de "--debug")
    for k in sorted(nombres, key=lambda k: re.sub(r"^[^a-z]*(\d+[a-z]?\.\s)?[^a-z]*", "", plegar(k)) or plegar(k)):
        texto, destino = nombres[k]
        ind.lineas.append(Linea("L", texto, destino))
    ind.lineas += [Linea("B"), Linea("L", tx["volver"], "inicio")]
    return fichas, alias, grupos, secciones


# --- el índice de palabras ------------------------------------------------------------------------------------

def palabras(f: Ficha) -> dict:
    """palabra -> puntos en esta ficha (10 si está en la clave o el título, y una por vez que sale)"""
    pts = {}

    def contar(texto, peso):
        for tok in re.findall(r"[a-z0-9_]+", plegar(sin_marcas(texto))):
            tok = tok.strip("_")
            partes = [tok] + (tok.split("_") if "_" in tok else [])
            for p in partes:
                if 3 <= len(p) <= MAX_PALABRA and not p.isdigit() and p not in VACIAS:
                    pts[p] = pts.get(p, 0) + peso
    contar(f.clave + " " + f.titulo, 10)
    for l in f.lineas:
        if l.tipo != "L" and l.indexar:
            contar(l.texto, 1)
    return pts


# --- el .ayuda ---------------------------------------------------------------------------------------------------

def texto_ficha(f: Ficha) -> str:
    out = [f"@{f.clave} {f.tipo} {f.titulo}"]
    out += [f"%{n} {v}" for n, v in f.campos]
    for l in f.lineas:
        t = sin_marcas(l.texto)
        out.append({"T": " " + t, "C": "|" + t, "H": "#" + t, "L": f"*{l.destino} {t}", "B": ""}[l.tipo])
    return "\n".join(x.rstrip() for x in out) + "\n"


def escribir_ayuda(lang, fichas, alias, grupos, secciones) -> bytes:
    ids = {f.clave: i for i, f in enumerate(fichas)}
    # el texto de las fichas, con su sitio relativo
    trozos, rel = [], []
    pos = 0
    for f in fichas:
        b = texto_ficha(f).encode("latin-1")
        rel.append((pos, len(b)))
        trozos.append(b + b"\n")
        pos += len(b) + 1
    texto = b"".join(trozos)
    kf = max(len(f.clave) for f in fichas)
    # (en minúsculas: se busca sin distinguir mayúsculas, RA_EVENT_CLOSE como ra_event_close)
    nombres = sorted([(f.clave.lower(), ids[f.clave]) for f in fichas] + [(p, ids[d]) for p, d in alias.items()])
    if len({n for n, _ in nombres}) != len(nombres):
        raise SystemExit("tools/gen_ayuda.py: dos fichas (o una palabra del lenguaje) con el mismo nombre")
    kn = max(len(n) for n, _ in nombres)
    # palabras -> fichas, por puntos
    post = {}
    for i, f in enumerate(fichas):
        for p, pts in palabras(f).items():
            post.setdefault(p, []).append((-pts, i))
    post = {p: v for p, v in post.items() if len(v) <= COMUNES * len(fichas)}
    lista_p = sorted(post)
    kp = max(len(p) for p in lista_p)

    rec_f = 8 + 1 + 6 + 1 + 1 + 1 + kf + 1
    rec_n = kn + 1 + 5 + 1
    rec_p = kp + 1 + 8 + 1 + 4 + 1
    grupos_b = b"".join(f"{ids[g.clave]:05d} {g.titulo}\n".encode("latin-1") for g in grupos)
    secc_b = b"".join(f"{ids[s.clave]:05d} {n} {s.titulo}\n".encode("latin-1") for s, n in secciones)
    ids_len = sum(len(v) * 6 for v in post.values())

    def cabecera(o):
        return (f"DASHAYUDA {FORMATO}\nidioma {lang}\nversion {compiler.__version__}\n"
                f"fichas {o['f']:08d} {len(fichas):05d} {rec_f:03d}\n"
                f"nombres {o['n']:08d} {len(nombres):05d} {rec_n:03d}\n"
                f"palabras {o['p']:08d} {len(lista_p):05d} {rec_p:03d}\n"
                f"ids {o['i']:08d} {ids_len:08d}\n"
                f"grupos {o['g']:08d} {len(grupos):05d}\n"
                f"secciones {o['s']:08d} {len(secciones):05d}\n"
                f"texto {o['t']:08d} {len(texto):08d}\n.\n").encode("ascii")
    o = dict.fromkeys("fnpigst", 0)
    o["f"] = len(cabecera(o))
    o["n"] = o["f"] + rec_f * len(fichas)
    o["p"] = o["n"] + rec_n * len(nombres)
    o["i"] = o["p"] + rec_p * len(lista_p)
    o["g"] = o["i"] + ids_len
    o["s"] = o["g"] + len(grupos_b)
    o["t"] = o["s"] + len(secc_b)
    out = [cabecera(o)]
    out += [f"{o['t'] + a:08d} {n:06d} {f.tipo} {f.clave:<{kf}}\n".encode("ascii") for f, (a, n) in zip(fichas, rel)]
    out += [f"{n:<{kn}} {i:05d}\n".encode("ascii") for n, i in nombres]
    lista_ids = []
    p_off = o["i"]
    for p in lista_p:
        v = sorted(post[p])
        out.append(f"{p:<{kp}} {p_off:08d} {len(v):04d}\n".encode("ascii"))
        lista_ids.append((" ".join(f"{i:05d}" for _, i in v) + "\n").encode("ascii"))
        p_off += len(v) * 6
    out += lista_ids + [grupos_b, secc_b, texto]
    datos = b"".join(out)
    assert len(datos) == o["t"] + len(texto)
    return datos


# --- el AmigaGuide -----------------------------------------------------------------------------------------------

def nodo(clave):
    return "MAIN" if clave == "inicio" else clave


def guia_texto(t: str, claves: set, propia: str) -> str:
    """Una línea de texto para el AmigaGuide: @ y \\ escapados, y `nombre` como enlace si es una ficha"""
    def esc(x):
        return x.replace("\\", "\\\\").replace("@", "\\@")
    out = []
    for parte in re.split(f"({CI}[^{CI}{CF}]*{CF})", t):
        if parte.startswith(CI) and parte.endswith(CF):
            nombre = parte[1:-1]
            base = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)(\(\))?", nombre)
            if base and base.group(1) in claves and base.group(1) != propia:
                out.append(f'@{{"{esc(nombre)}" link {nodo(base.group(1))}}}')
                continue
            out.append(esc(nombre))
        else:
            out.append(esc(sin_marcas(parte)))
    return "".join(out)


def escribir_guia(lang, fichas) -> bytes:
    nombre = "Dash.guide" if lang == "es" else "Dash_en.guide"
    claves = {f.clave for f in fichas}
    por_clave = {f.clave: f for f in fichas}
    hoy = datetime.date.today()
    out = [f"@database {nombre}", f"@$VER: {nombre} {compiler.__version__} ({hoy.day}.{hoy.month}.{hoy.year})",
           "@author FreeMEM", "@remark Generado por tools/gen_ayuda.py desde la documentacion de Dash. No editar.",
           "@index indice", ""]
    for f in fichas:
        titulo = f.titulo.replace('"', "'")
        out.append(f'@node {nodo(f.clave)} "{titulo}"')
        if f.tipo == "F":
            out.append(f"@toc {dict(f.campos)['grupo']}")
        elif f.tipo == "M" and "_" in f.clave:
            out.append(f"@toc {f.clave.split('_')[0]}")
        elif f.clave != "inicio":
            out.append("@toc MAIN")
        out += [f"@{{b}}{guia_texto(f.titulo, set(), '')}@{{ub}}", ""]
        for l in f.lineas:
            if l.tipo == "T":
                out.append(guia_texto(l.texto, claves, f.clave))
            elif l.tipo == "C":
                out.append("  " + guia_texto(sin_marcas(l.texto), set(), ""))
            elif l.tipo == "H":
                if out[-1] != "":
                    out.append("")
                out.append(f"@{{b}}{guia_texto(sin_marcas(l.texto), set(), '')}@{{ub}}")
            elif l.tipo == "B":
                out.append("")
            elif l.tipo == "L":
                t = sin_marcas(l.texto)
                destino = por_clave[l.destino]
                # el enlace con el nombre (o el texto entero si es corto) y, si no cabe, el resto debajo
                if f.tipo != "I" and destino.tipo == "F" and t.startswith(l.destino):
                    cab, resto = l.destino, t[len(l.destino):]
                else:
                    cab, resto = t, ""
                partes = cortar(cab + resto, "    ", "")
                primera = partes[0]
                enlace = f'@{{" {guia_texto(cab, set(), "")} " link {nodo(l.destino)}}}'
                out.append(enlace + guia_texto(primera[len(cab):], set(), ""))
                out += [guia_texto(x, set(), "") for x in partes[1:]]
        out.append("@endnode")
        out.append("")
    return ("\n".join(out)).encode("latin-1")


# --- comprobar ---------------------------------------------------------------------------------------------------

def comprobar(lang, fichas, alias) -> list:
    errores = []
    claves = [f.clave for f in fichas]
    if len(set(claves)) != len(claves):
        errores.append(f"{lang}: claves repetidas")
    if len({c.lower() for c in claves}) != len(claves):
        errores.append(f"{lang}: claves que solo cambian en mayúsculas (los nodos del AmigaGuide no las distinguen)")
    cs = set(claves)
    for nombre in ab.ALL_BUILTINS:
        if nombre not in cs:
            errores.append(f"{lang}: {nombre} sin ficha")
    for f in fichas:
        if not re.fullmatch(r"[A-Za-z0-9_]+", f.clave):
            errores.append(f"{lang}: clave {f.clave!r} con caracteres raros")
        for l in f.lineas:
            if l.tipo == "L" and l.destino not in cs:
                errores.append(f"{lang}: {f.clave} enlaza a {l.destino}, que no es una ficha")
            if "\n" in l.texto:
                errores.append(f"{lang}: {f.clave}: salto de línea dentro de una línea")
    for p, d in alias.items():
        if p in cs:
            errores.append(f"{lang}: la palabra {p} es también una ficha")
    return errores


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--salida", default=str(RAIZ / "build" / "ayuda"))
    ap.add_argument("--check", action="store_true", help="genera en memoria y comprueba, sin escribir")
    args = ap.parse_args()
    errores = []
    salida = {}
    for lang, suf in (("es", ""), ("en", "_en")):
        fichas, alias, grupos, secciones = generar(lang)
        errores += comprobar(lang, fichas, alias)
        salida[f"Dash{suf}.ayuda"] = escribir_ayuda(lang, fichas, alias, grupos, secciones)
        salida[f"Dash{suf}.guide"] = escribir_guia(lang, fichas)
    if errores:
        print("\n".join(errores))
        sys.exit(1)
    if args.check:
        return
    d = Path(args.salida)
    d.mkdir(parents=True, exist_ok=True)
    for nombre, datos in salida.items():
        (d / nombre).write_bytes(datos)
        print(f"{d / nombre} ({len(datos) // 1024} KB)")


if __name__ == "__main__":
    main()
