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

### 2026-10-25 — R1 (`--cpu`)
- `./dash --cpu 68020|68030|68040|68060` (`compiler/cflags.py` `cpu_flags`): `-m68020` más `-mtune`. `_DASH_68020` en el
  runtime (con `-mtune=68060` GCC define `__mc68060__` y no `__mc68020__`). Fixed en 68060 por el camino de 68000:
  0 `muls.l`/`divs.l` de 64 bits en el ensamblador (test en `tests/unit/test_dash_cli.py`). Fixed con dos constantes
  no pasa por el asm (con él, `fixed_mul_add` iba de 261 a 1.880 ns en el 68040).
- Probado: `test_fixed`, `test_fixed_lists`, `test_fixed_runtime_amiga`, `test_return_types` con `--cpu 68040` en
  un 68040 emulado (OS 3.1) y con `--cpu 68060` en un 68060 (OS 3.2 con 68060.library: con 3.1 el 060 no arranca
  en FS-UAE, ni con código de 68000). 381/381 sin emulador.
- Medida (`R1`, ns, 68040 con código de 68000 → `--cpu 68040`): `fixed_div` 27.727 → 823, `fixed_mul` 6.179 →
  1.598, `fixed_mul_add` 261 → 12, `array_get_set` 6.881 → 4.684, textos −13 % (`string_concat_int` 42.543 →
  36.951, `string_interp` 64.332 → 55.448, `string_return` 47.902 → 40.276), `nested_struct_new` −10 %. Peor:
  `string_compare` +8 %, `struct_new_field` +5 %. Gráficos y Float casi igual (los manda la ROM y softfloat).
  A500 y A1200 sin cambios (es el mismo código).
- No medido: un 68060 (FS-UAE no da tiempos reales de 040/060) ni la libnix de 68020 en un 060 (puede traer
  instrucciones de 64 bits que emula 68060.library).
- R2 descartada: el tamaño de la cabecera de un texto no es su longitud (los textos crecen en su sitio).
