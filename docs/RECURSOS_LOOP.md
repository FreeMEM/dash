# Bucle de consumo de recursos (velocidad y memoria)

Encargo (2026-10-25): optimizar velocidad y memoria del código que genera Dash, medir cada cambio con
`tools/bench.py --save` y anotarlo en el panel de benchmarks (https://claude.ai/artifact/9XyJ1JNSGuDo5q6NCRzM2N,
`tools/bench_report.py` y subir los CSV). Pensar también en máquinas reales con 68040/68060 y tarjetas
gráficas Zorro II/III, no solo en A500/A1200.

Tope: al 90 % del uso semanal (`~/.claude/state/uso-7d.txt`) se para (al empezar estaba en 85 %).

## Tareas

- R1 `./dash --cpu 68020|68030|68040|68060`: código de 68020 afinado para cada CPU (`-m68020 -mtune=...`; la
  toolchain solo trae libnix de 68000 y 68020). En 68060 el runtime no usa `muls.l`/`divs.l` de 64 bits (el 060
  no los tiene: 68060.library los emula con una excepción por cada uno). Máquina `a4000` en `tools/bench.py`
  (68040 con fast RAM): mismo benchmark con código de 68000 y con `--cpu 68040`.
- R2 Textos: `+` e interpolación sin `strlen` de libnix cuando el texto es de Dash (su tamaño está en la cabecera).
- R3 Cabecera de objetos de 20 a 16 bytes (un struct de dos Int pasa de bloques de 32 a 24 bytes). El usuario lo
  aparcó en 27c "salvo que un programa real lo pida"; con este encargo de memoria, se mide antes de decidir.
- R4 RTG en Zorro II/III: leer de la memoria de la tarjeta es lo más caro (Zorro II, unos 3 MB/s). Buscar en los
  runtimes de gráficos lecturas de la pantalla que se puedan evitar. FS-UAE no emula la lentitud del bus: se
  mide contando bytes leídos de la tarjeta, no tiempo.

## Bitácora
