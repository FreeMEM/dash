"""Builds docs/COMPARATIVA(.en).md and the comparison page (HTML, $PAGE) from the measured results
(res_a1200.txt, res_a500.txt: what timeit printed; sizes.txt). See docs/COMPARATIVA.md, "How it was measured"."""
import os
import html

C = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(C))
LANGS = ["dash", "blitz", "amos", "sasc", "gcc"]
NAMES = {"dash": "Dash", "blitz": "AmiBlitz3", "amos": "AMOS Pro", "sasc": "SAS/C 6.59", "gcc": "GCC 6.5"}
BENCH = ["bucle", "llamada", "texto", "lista", "flotante", "lineas"]
STACK = 65536   # the stack of the process each program ran in (counted in the memory peak)


def load(name):
    p = os.path.join(C, name)
    res = {}
    if not os.path.exists(p):
        return None
    for line in open(p):
        parts = line.split()
        if len(parts) == 4 and "_" in parts[0]:
            lang, bench = parts[0].split("_", 1)
            res[(lang, bench)] = (int(parts[1]), int(parts[2]))
    return res or None


def sizes():
    """sizes.txt: "lang_bench bytes" of each executable"""
    out = {}
    for line in open(os.path.join(C, "sizes.txt")):
        name, n = line.split()
        lang, bench = name.split("_", 1)
        out[(lang, bench)] = int(n)
    return out


A1200, A500, SIZE = load("res_a1200.txt"), load("res_a500.txt"), sizes()
MACHINES = [("A1200", A1200)] + ([("A500", A500)] if A500 else [])

T = {
"es": dict(
    title="Dash, Blitz y AMOS",
    lead="Dash frente a los lenguajes «fáciles» de siempre (AmiBlitz3 y AMOS Professional) y frente a C (SAS/C y GCC), con los mismos programas medidos en el mismo Amiga emulado.",
    sum_h="En resumen",
    summary=[
        "Velocidad: Dash va a la par que C con GCC en cálculo y llamadas, y es el más rápido con textos y listas. AmiBlitz3 y AMOS van de 10 a 40 veces más despacio en cálculo, llamadas y listas, y de 1,2 a 2 veces con textos. En coma flotante gana SAS/C (FFP de la ROM). En líneas gana C: Dash va un 8 % detrás en el A1200 y un 19 % en el A500 (dibuja en una ventana); AmiBlitz3 y AMOS, hasta un 66 % en el A500.",
        "Arranque y tamaño: AmiBlitz3 y SAS/C hacen los ejecutables más pequeños; Dash queda cerca (4-9 KB). AMOS mete su runtime en cada programa: 54 KB y casi un segundo para arrancar en un A1200.",
        "Memoria: Dash es el que menos ocupa al ejecutarse (17 KB de media), seguido de SAS/C (21 KB), AmiBlitz3 (30 KB) y GCC (39 KB). AMOS necesita unos 170 KB. Con pantalla, Dash y AmiBlitz3 gastan unos 45 KB más que C (Dash dibuja en una ventana).",
        "Estabilidad: Dash y AMOS paran limpiamente ante una división por cero; C se cuelga y AmiBlitz3 sigue con un resultado falso. Ante un índice fuera de rango, solo AMOS avisa; Dash lo ignora sin corromper memoria; AmiBlitz3 y C escriben fuera de la lista.",
        "Capacidades: Dash cubre ventanas del sistema (GadTools, MUI, ReAction), RTG, red y TLS desde el propio lenguaje. AMOS manda en juegos con el hardware (AMAL, bobs, música) pero ignora el sistema. AmiBlitz3 llega a todo, a cambio de punteros y memoria a mano.",
    ],
    cap_h="Qué cubre cada uno",
    cap_note="Según la documentación de cada uno y lo que trae Coffin OS R65; no está todo medido.",
    perf_h="Velocidad",
    perf_note="Milisegundos de cada programa completo (carga, arranque y trabajo) en FS-UAE a velocidad real. Menos es mejor. La barra es relativa al más lento de cada prueba.",
    mem_h="Memoria y tamaño",
    mem_note="Tamaño del ejecutable y memoria que ocupa al ejecutarse (el mayor descenso de memoria libre mientras corre, sin los 64 KB de pila del proceso).",
    est_h="Estabilidad",
    est_note="Qué pasa ante dos fallos típicos, en un A1200 emulado con OS 3.1. Cada prueba en un arranque propio.",
    met_h="Cómo se midió",
    bench_desc={
        "bucle": "300.000 vueltas de sumas y una comparación",
        "llamada": "100.000 llamadas a una función de dos parámetros",
        "texto": "20.000 veces texto + número",
        "lista": "100.000 lecturas y escrituras en una lista de 10 con módulo",
        "flotante": "20.000 sumas y multiplicaciones de coma flotante",
        "lineas": "2.000 líneas en una pantalla de 320×256 y 32 colores",
    },
    cols=["", "Dash", "AmiBlitz3", "AMOS Pro", "SAS/C", "GCC (C)", "VBCC", "Ensamblador"],
    cap_rows=[
        ("Estado", "En desarrollo (2026)", "Código abierto, 3.11 (2026)", "Código abierto desde 2019; última versión 1993", "Comercial, cerrado en 1995", "bebbo 6.5, en desarrollo", "0.9h (2022)", "ASM-One, DevPac"),
        ("Cómo funciona", "Pasa a C y compila con GCC en el PC", "Compilador en el Amiga", "Intérprete con IDE + compilador", "Compilador en el Amiga", "Compilador cruzado en el PC", "En el Amiga o en el PC", "Ensamblador"),
        ("CPU", "68000; --cpu 020-060", "68000 (IDE: 020)", "68000; AGA no oficial", "68000-060", "68000-060", "68000-060", "Cualquiera"),
        ("Estructuras", "struct, listas, diccionarios", "NEWTYPE, listas enlazadas, punteros", "No (solo arrays)", "struct, punteros", "struct, punteros", "struct, punteros", "A mano"),
        ("Memoria", "Automática (conteo de referencias)", "Textos automáticos; el resto a mano", "Automática", "A mano", "A mano", "A mano", "A mano"),
        ("Números", "Int, Float, Fixed 16.16", "Long, Quick 16.16, Float FFP", "Entero, Float (doble opcional)", "Todos los de C", "Todos los de C", "Todos los de C", "A mano"),
        ("Ventanas del sistema", "Intuition, GadTools, MUI, ReAction", "Intuition, GadTools (includes)", "No: pantallas propias", "Con las librerías del SO", "Con las librerías del SO", "Con las librerías del SO", "Con las librerías del SO"),
        ("Tarjeta gráfica (RTG)", "Sí (P96, CGX)", "Con includes", "No", "Con librerías", "Con librerías", "Con librerías", "Con librerías"),
        ("Hardware (copper, sprites, blitter)", "Sí", "Sí (modo Blitz)", "Sí, y AMAL para animar", "A mano", "A mano", "A mano", "Sí"),
        ("Red y TLS", "bsdsocket y AmiSSL", "bsdsocket y http (includes)", "No", "Con librerías", "Con librerías", "Con librerías", "A mano"),
        ("Errores en ejecución", "Mensaje y salida limpia, sin Guru", "Con el depurador; sin él, no", "Mensaje de error", "Guru", "Guru", "Guru", "Guru"),
        ("Dónde se programa", "VS Code en el PC (y emulador)", "IDE propio en el Amiga", "IDE propio en el Amiga", "Amiga", "PC", "Amiga o PC", "Amiga"),
    ],
    est_cols=["", "División por cero", "Índice fuera de rango"],
    est_rows={
        "dash": ("Mensaje de error y salida limpia (código 20); el Amiga sigue", "Lee 0 y no escribe; sigue sin avisar"),
        "blitz": ("Da 2147483647 y sigue sin avisar", "Escribe fuera de la lista y sigue"),
        "amos": ("Para con error (código 20); el Amiga sigue", "Para con error (código 20); el Amiga sigue"),
        "sasc": ("El Amiga se cuelga", "Escribe fuera de la lista y sigue"),
        "gcc": ("El Amiga se cuelga", "Escribe fuera de la lista y sigue"),
    },
    exe_h="Ejecutable vacío", exe2_h="Ejecutable medio", run_h="Memoria al ejecutar (media)", scr_h="Con pantalla (líneas)",
    start_h="Arranque",
    method=[
        "Máquinas: FS-UAE a velocidad real (ciclo a ciclo), Kickstart 3.1. A1200: 68020 a 14 MHz con 8 MB de fast RAM. A500: 68000 a 7 MHz.",
        "Compiladores: Dash 528c3cc (por defecto, -O2); AmiBlitz3 3.11.4 con -r; AMOS Professional Compiler 2.0 (TYPE=1 INCLIB); SAS/C 6.59 con OPTIMIZE y MATH=FFP; GCC 6.5 de bebbo con -O2 y libnix. Los de Coffin OS R65, copiados de la imagen en modo solo lectura (a AMOS le faltaban AMOSPro_Compiler_Config y AMOSPro_Interpreter_Config: los del repositorio oficial de AMOS Pro).",
        "Medida: un programa en C lanza cada ejecutable y toma el tiempo con el EClock y el pico de memoria muestreando AvailMem cada 1/50 s. Una pasada por programa (el emulador es determinista).",
        "Mismo algoritmo en todos. En C, «texto» es sprintf en un búfer fijo (C no tiene textos dinámicos). AmiBlitz3 con DEFTYPE .l y opciones por defecto: no lo he afinado.",
        "Sin medir todavía: VBCC (el de Coffin no trae instalado el target de AmigaOS), el GCC 2.95 de ADE y el ensamblador.",
        "La prueba de líneas destapó un fallo de Dash: en un 68000, abrir una pantalla propia daba un Guru (SA_Pens). Arreglado en el PR #55; la cifra de Dash en líneas del A500 es con el arreglo.",
    ],
    src="Los programas de cada lenguaje, el medidor (timeit.c), los datos y este generador están en tools/comparativa.",
    ms="ms", winner="mejor",
),
"en": dict(
    title="Dash, Blitz and AMOS",
    lead="Dash against the classic “easy” languages (AmiBlitz3 and AMOS Professional) and against C (SAS/C and GCC), with the same programs measured on the same emulated Amiga.",
    sum_h="Summary",
    summary=[
        "Speed: Dash is on par with C (GCC) for arithmetic and calls, and the fastest with strings and lists. AmiBlitz3 and AMOS are 10 to 40 times slower for arithmetic, calls and lists, and 1.2 to 2 times slower with strings. SAS/C wins floating point (the ROM's FFP). C wins drawing lines: Dash is 8 % behind on the A1200 and 19 % on the A500 (it draws in a window); AmiBlitz3 and AMOS up to 66 % on the A500.",
        "Startup and size: AmiBlitz3 and SAS/C make the smallest executables; Dash is close (4-9 KB). AMOS puts its runtime in every program: 54 KB and almost a second to start on an A1200.",
        "Memory: Dash uses the least while running (17 KB on average), then SAS/C (21 KB), AmiBlitz3 (30 KB) and GCC (39 KB). AMOS needs about 170 KB. With a screen, Dash and AmiBlitz3 use about 45 KB more than C (Dash draws in a window).",
        "Stability: Dash and AMOS stop cleanly on a division by zero; C hangs the Amiga and AmiBlitz3 goes on with a wrong result. On an index out of range only AMOS reports it; Dash ignores it without corrupting memory; AmiBlitz3 and C write outside the list.",
        "Features: Dash covers system windows (GadTools, MUI, ReAction), RTG, networking and TLS from the language itself. AMOS rules hardware games (AMAL, bobs, music) but ignores the OS. AmiBlitz3 reaches everything, at the cost of pointers and manual memory.",
    ],
    cap_h="What each one covers",
    cap_note="From each one's documentation and what Coffin OS R65 ships; not all of it is measured.",
    perf_h="Speed",
    perf_note="Milliseconds for each whole program (load, start and work) in FS-UAE at real speed. Lower is better. The bar is relative to the slowest in each test.",
    mem_h="Memory and size",
    mem_note="Executable size and memory used while running (the largest drop of free memory while it runs, minus the 64 KB stack of the process).",
    est_h="Stability",
    est_note="What happens on two typical bugs, on an emulated A1200 with OS 3.1. Each test in its own boot.",
    met_h="How it was measured",
    bench_desc={
        "bucle": "300,000 loops of additions and a comparison",
        "llamada": "100,000 calls to a two-parameter function",
        "texto": "20,000 times string + number",
        "lista": "100,000 reads and writes in a 10-element list with modulo",
        "flotante": "20,000 floating point additions and multiplications",
        "lineas": "2,000 lines on a 320×256, 32-color screen",
    },
    cols=["", "Dash", "AmiBlitz3", "AMOS Pro", "SAS/C", "GCC (C)", "VBCC", "Assembler"],
    cap_rows=[
        ("Status", "In development (2026)", "Open source, 3.11 (2026)", "Open source since 2019; last release 1993", "Commercial, discontinued 1995", "bebbo 6.5, in development", "0.9h (2022)", "ASM-One, DevPac"),
        ("How it works", "Translates to C, compiled with GCC on the PC", "Compiler on the Amiga", "Interpreter with IDE + compiler", "Compiler on the Amiga", "Cross compiler on the PC", "On the Amiga or the PC", "Assembler"),
        ("CPU", "68000; --cpu 020-060", "68000 (IDE: 020)", "68000; AGA unofficial", "68000-060", "68000-060", "68000-060", "Any"),
        ("Structures", "structs, lists, dictionaries", "NEWTYPE, linked lists, pointers", "No (arrays only)", "structs, pointers", "structs, pointers", "structs, pointers", "By hand"),
        ("Memory", "Automatic (reference counting)", "Strings automatic; the rest by hand", "Automatic", "By hand", "By hand", "By hand", "By hand"),
        ("Numbers", "Int, Float, Fixed 16.16", "Long, Quick 16.16, FFP Float", "Integer, Float (double optional)", "All of C's", "All of C's", "All of C's", "By hand"),
        ("System windows", "Intuition, GadTools, MUI, ReAction", "Intuition, GadTools (includes)", "No: its own screens", "Through OS libraries", "Through OS libraries", "Through OS libraries", "Through OS libraries"),
        ("Graphics cards (RTG)", "Yes (P96, CGX)", "With includes", "No", "With libraries", "With libraries", "With libraries", "With libraries"),
        ("Hardware (copper, sprites, blitter)", "Yes", "Yes (Blitz mode)", "Yes, plus AMAL for animation", "By hand", "By hand", "By hand", "Yes"),
        ("Networking and TLS", "bsdsocket and AmiSSL", "bsdsocket and http (includes)", "No", "With libraries", "With libraries", "With libraries", "By hand"),
        ("Runtime errors", "Message and clean exit, no Guru", "With the debugger; without it, no", "Error message", "Guru", "Guru", "Guru", "Guru"),
        ("Where you write it", "VS Code on the PC (and emulator)", "Its own IDE on the Amiga", "Its own IDE on the Amiga", "Amiga", "PC", "Amiga or PC", "Amiga"),
    ],
    est_cols=["", "Division by zero", "Index out of range"],
    est_rows={
        "dash": ("Error message and clean exit (code 20); the Amiga goes on", "Reads 0 and does not write; goes on silently"),
        "blitz": ("Gives 2147483647 and goes on silently", "Writes outside the list and goes on"),
        "amos": ("Stops with an error (code 20); the Amiga goes on", "Stops with an error (code 20); the Amiga goes on"),
        "sasc": ("The Amiga hangs", "Writes outside the list and goes on"),
        "gcc": ("The Amiga hangs", "Writes outside the list and goes on"),
    },
    exe_h="Empty executable", exe2_h="Typical executable", run_h="Memory while running (mean)", scr_h="With a screen (lines)",
    start_h="Startup",
    method=[
        "Machines: FS-UAE at real (cycle-exact) speed, Kickstart 3.1. A1200: 68020 at 14 MHz with 8 MB fast RAM. A500: 68000 at 7 MHz.",
        "Compilers: Dash 528c3cc (default, -O2); AmiBlitz3 3.11.4 with -r; AMOS Professional Compiler 2.0 (TYPE=1 INCLIB); SAS/C 6.59 with OPTIMIZE and MATH=FFP; bebbo's GCC 6.5 with -O2 and libnix. The ones in Coffin OS R65, copied from its image mounted read only (AMOS lacked AMOSPro_Compiler_Config and AMOSPro_Interpreter_Config: taken from the official AMOS Pro repository).",
        "Measuring: a C program runs each executable, times it with the EClock and samples AvailMem every 1/50 s for the memory peak. One run per program (the emulator is deterministic).",
        "Same algorithm everywhere. In C, “texto” is sprintf into a fixed buffer (C has no dynamic strings). AmiBlitz3 with DEFTYPE .l and default options: not tuned.",
        "Not measured yet: VBCC (Coffin's lacks the AmigaOS target), ADE's GCC 2.95 and assembler.",
        "The lines test found a Dash bug: on a 68000, opening its own screen gave a Guru (SA_Pens). Fixed in PR #55; Dash's A500 lines figure is with the fix.",
    ],
    src="Each language's programs, the timer (timeit.c), the data and this generator are in tools/comparativa.",
    ms="ms", winner="best",
),
}


def fmt(n, lang):
    s = f"{n:,}"
    return s.replace(",", ".") if lang == "es" else s


def mem_run(data, lang):
    vals = [data[(lang, b)][1] - STACK for b in ["bucle", "llamada", "texto", "lista", "flotante"] if (lang, b) in data]
    return sum(vals) // len(vals) if vals else None


def mean_size(lang):
    vals = [SIZE[(lang, b)] for b in BENCH if (lang, b) in SIZE]
    return sum(vals) // len(vals)


def markdown(lang):
    t = T[lang]
    other = "COMPARATIVA.en.md" if lang == "es" else "COMPARATIVA.md"
    sel = f"[English]({other}) · **Castellano**" if lang == "es" else f"**English** · [Castellano]({other})"
    o = [f"# {t['title']}", "", sel, "", t["lead"], "", f"## {t['sum_h']}", ""]
    o += [f"- {s}" for s in t["summary"]] + ["", f"## {t['perf_h']}", "", t["perf_note"], ""]
    for mname, data in MACHINES:
        o += [f"### {mname}", "", "| | " + " | ".join(NAMES[l] for l in LANGS) + " |", "|---|" + "---:|" * len(LANGS)]
        for b in ["vacio"] + BENCH:
            row = [data[(l, b)][0] for l in LANGS if (l, b) in data]
            best = min(row) if row else None
            label = t["start_h"] if b == "vacio" else f"{b} ({t['bench_desc'][b]})"
            cells = []
            for l in LANGS:
                v = data.get((l, b))
                cells.append("—" if not v else (f"**{fmt(v[0], lang)}**" if v[0] == best else fmt(v[0], lang)))
            o.append(f"| {label} | " + " | ".join(cells) + " |")
        o.append("")
    o += [f"## {t['mem_h']}", "", t["mem_note"], "", "| | " + " | ".join(NAMES[l] for l in LANGS) + " |", "|---|" + "---:|" * len(LANGS)]
    o.append(f"| {t['exe_h']} | " + " | ".join(fmt(SIZE[(l, 'vacio')], lang) + " B" for l in LANGS) + " |")
    o.append(f"| {t['exe2_h']} | " + " | ".join(fmt(mean_size(l), lang) + " B" for l in LANGS) + " |")
    o.append(f"| {t['run_h']} (A1200) | " + " | ".join(fmt(mem_run(A1200, l), lang) + " B" for l in LANGS) + " |")
    o.append(f"| {t['scr_h']} (A1200) | " + " | ".join(fmt(A1200[(l, 'lineas')][1] - STACK, lang) + " B" for l in LANGS) + " |")
    o += ["", f"## {t['est_h']}", "", t["est_note"], "", "| " + " | ".join(t["est_cols"]) + " |", "|---|---|---|"]
    for l in LANGS:
        o.append(f"| {NAMES[l]} | {t['est_rows'][l][0]} | {t['est_rows'][l][1]} |")
    o += ["", f"## {t['cap_h']}", "", t["cap_note"], "", "| " + " | ".join(t["cols"]) + " |", "|---" * len(t["cols"]) + "|"]
    for r in t["cap_rows"]:
        o.append("| " + " | ".join(r) + " |")
    o += ["", f"## {t['met_h']}", ""] + [f"- {m}" for m in t["method"]] + ["", t["src"], ""]
    return "\n".join(o)


def page():
    t = T["es"]
    e = html.escape
    parts = []
    for mname, data in MACHINES:
        blocks = []
        for b in BENCH:
            row = {l: data[(l, b)][0] for l in LANGS if (l, b) in data}
            top, best = max(row.values()), min(row.values())
            bars = "".join(
                f'<div class="bar-row{" is-best" if row[l] == best else ""}{" is-dash" if l == "dash" else ""}">'
                f'<span class="bar-name">{e(NAMES[l])}</span>'
                f'<span class="bar-track"><span class="bar" style="width:{max(1.5, 100 * row[l] / top):.1f}%"></span></span>'
                f'<span class="bar-val">{fmt(row[l], "es")}</span></div>' for l in LANGS if l in row)
            blocks.append(f'<figure class="bench"><figcaption><b>{e(b)}</b> <span>{e(t["bench_desc"][b])}</span></figcaption>{bars}</figure>')
        start = " · ".join(f"{e(NAMES[l])} {fmt(data[(l, 'vacio')][0], 'es')}" for l in LANGS)
        parts.append(f'<section class="machine"><h3>{mname} <small>{"68020 · 14 MHz" if mname == "A1200" else "68000 · 7 MHz"}</small></h3>'
                     f'<p class="start">{e(t["start_h"])} (programa vacío, ms): {start}</p><div class="bench-grid">{"".join(blocks)}</div></section>')
    mem_rows = [
        (t["exe_h"], {l: SIZE[(l, "vacio")] for l in LANGS}),
        (t["exe2_h"], {l: mean_size(l) for l in LANGS}),
        (t["run_h"] + " · A1200", {l: mem_run(A1200, l) for l in LANGS}),
        (t["scr_h"] + " · A1200", {l: A1200[(l, "lineas")][1] - STACK for l in LANGS}),
    ]
    mem_html = "".join(
        f'<tr><th scope="row">{e(n)}</th>' + "".join(
            f'<td class="{"is-best" if v[l] == min(v.values()) else ""}">{fmt(v[l], "es")}<small> B</small></td>' for l in LANGS) + "</tr>"
        for n, v in mem_rows)
    est_html = "".join(
        f'<tr><th scope="row">{e(NAMES[l])}</th>' + "".join(
            f'<td><span class="pill {cls(x)}">{e(x)}</span></td>' for x in T["es"]["est_rows"][l]) + "</tr>" for l in LANGS)
    cap_html = "".join("<tr>" + f'<th scope="row">{e(r[0])}</th>' + "".join(f"<td>{e(c)}</td>" for c in r[1:]) + "</tr>" for r in t["cap_rows"])
    tpl = open(os.path.join(C, "page.tpl.html"), encoding="utf-8").read()
    return (tpl.replace("{{SUMMARY}}", "".join(f"<li>{e(s)}</li>" for s in t["summary"]))
            .replace("{{MACHINES}}", "".join(parts))
            .replace("{{HEAD_LANGS}}", "".join(f"<th scope=\"col\">{e(NAMES[l])}</th>" for l in LANGS))
            .replace("{{MEM}}", mem_html).replace("{{EST}}", est_html)
            .replace("{{CAP_HEAD}}", "".join(f'<th scope="col">{e(c)}</th>' for c in t["cols"]))
            .replace("{{CAP}}", cap_html)
            .replace("{{METHOD}}", "".join(f"<li>{e(m)}</li>" for m in t["method"])))


def cls(text):
    t = text.lower()
    if "cuelga" in t or "fuera de la lista" in t or "2147483647" in t:
        return "bad"
    if "sin avisar" in t:
        return "warn"
    return "ok"


open(os.path.join(REPO, "docs", "COMPARATIVA.md"), "w").write(markdown("es"))
open(os.path.join(REPO, "docs", "COMPARATIVA.en.md"), "w").write(markdown("en"))
open(os.environ.get("PAGE", os.path.join(C, "comparativa.html")), "w").write(page())
print("ok", [m for m, _ in MACHINES])
