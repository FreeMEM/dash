"""La documentación ampliada de los builtins, para docs/BUILTINS.md y docs/BUILTINS.en.md (tools/gen_builtins_doc.py).

La descripción corta de cada builtin sigue en compiler/amiga_builtins.py (inglés) y compiler/builtins_es.py
(castellano): sale en la tabla de cada grupo, que hace de índice. Aquí va lo que no cabe en una línea:

- GROUPS: por grupo (el nombre de su diccionario en amiga_builtins.py), una introducción en los dos idiomas (para
  qué sirve, qué hace falta antes, el flujo de siempre) y un ejemplo. El ejemplo es un test del runner
  (tests/test_doc_*.dash): compila por los dos caminos y su salida se comprueba en el emulador. Las líneas de
  órdenes del runner (# expect-out:, # emu-needs:...) no salen en la documentación.
- FUNCS: por builtin, qué es cada parámetro y su rango, qué devuelve, qué pasa si falla, y "see", las funciones
  relacionadas.

Textos llanos, con comillas rectas. Un builtin sin entrada aquí sale solo en la tabla.

Un módulo por grupo (o por unos pocos grupos), cada uno con su GROUPS y su FUNCS; aquí se juntan.
"""

from . import entrada, ficheros, graficos, mui, mui_lienzo, sprites, ventanas

GROUPS = {}
FUNCS = {}
for _m in (graficos, ventanas, entrada, ficheros, mui, mui_lienzo, sprites):
    for _k in _m.GROUPS:
        assert _k not in GROUPS, _k
    for _k in _m.FUNCS:
        assert _k not in FUNCS, _k
    GROUPS.update(_m.GROUPS)
    FUNCS.update(_m.FUNCS)
