*[English](AYUDA_FORMATO.en.md) | Castellano*

# La ayuda de Dash en el Amiga: el formato del .ayuda

`tools/gen_ayuda.py` saca de la documentación de Dash cuatro ficheros, que `tools/paquete_amiga.py` pone en el cajón
`Ayuda` del paquete (en el Amiga, `DASH:Ayuda/`):

| Fichero | Qué es |
|---|---|
| `Dash.ayuda`, `Dash_en.ayuda` | La ayuda con índices, para que un programa (Forja) la lea a trozos |
| `Dash.guide`, `Dash_en.guide` | Lo mismo en AmigaGuide, para MultiView |

Las fuentes: los builtins (`compiler/amiga_builtins.py`, `compiler/builtins_es.py`, `compiler/builtins_doc/`), los
ejemplos de cada grupo (`tests/test_doc_*.dash`), `docs/SINTAXIS.md` y `docs/MANUAL_REFERENCIA.md`, con sus `.en.md`.
Los ficheros no van a git: se hacen al empaquetar. `tests/unit/test_gen_ayuda.py` comprueba que todas las funciones
tienen ficha y que los enlaces llevan a fichas que existen.

```
python3 tools/gen_ayuda.py                  # build/ayuda/
python3 tools/gen_ayuda.py --salida DIR
python3 tools/gen_ayuda.py --check          # solo comprueba
```

<!-- indice -->
<a id="indice"></a>

**Índice**

- [Las fichas](#las-fichas)
- [El fichero](#el-fichero)
- [Leerlo desde Dash](#leerlo-desde-dash)
- [El AmigaGuide](#el-amigaguide)
<!-- /indice -->

<a id="las-fichas"></a>

## Las fichas

Todo es una ficha, con una clave única (letras, cifras y `_`):

| Tipo | Clave | Qué tiene |
|---|---|---|
| `F` función | su nombre: `file_seek`, `RA_EVENT_CLOSE` | firma, qué hace, parámetros, ejemplo, ver también, DashOS |
| `G` grupo | el de `docs/BUILTINS.md` en minúsculas: `audio_functions` | introducción, ejemplo entero, lista de funciones |
| `M` manual | `m6` (capítulo 6), `m6_1` (su primer apartado), `m20b`, `mx26` (el apéndice) | el texto del capítulo o del apartado |
| `S` sintaxis | `sintaxis` | `docs/SINTAXIS.md` |
| `I` portada e índices | `inicio`, `manual`, `grupos`, `indice` | listas de enlaces |

Las claves `m...` son las mismas en los dos idiomas (el manual en inglés tiene los mismos apartados; el generador lo
comprueba).

[Volver al índice](#indice)

<a id="el-fichero"></a>

## El fichero

Texto Latin-1 (ISO-8859-1), líneas acabadas en `\n` (10). Los números van en decimal con ceros delante y ancho fijo,
así que los registros de los índices tienen todos el mismo largo y el registro `i` está en `inicio + i * largo`: se
llega con un `file_seek` y se lee con un `file_read`, sin cargar el índice.

Partes, en este orden: cabecera, tabla de fichas, nombres, palabras, ids, grupos, secciones y el texto de las fichas.

### Cabecera

Unas líneas de texto, menos de 512 bytes, que acaban en una línea con un punto:

```
DASHAYUDA 1
idioma es
version 2.15.0
fichas 00000213 01277 047
nombres 00060232 01329 035
palabras 00106747 05341 039
ids 00315046 00214170
grupos 00529216 00041
secciones 00530377 00218
texto 00536910 01206024
.
```

- `DASHAYUDA 1`: el formato, versión 1. Un lector que no la conoce no debe seguir.
- `fichas`, `nombres`, `palabras`: dónde empieza la tabla (byte desde el principio), cuántos registros y el largo de
  cada uno (con su `\n`).
- `ids`: dónde empieza la zona de ids y cuántos bytes tiene.
- `grupos`, `secciones`: dónde empiezan y cuántas líneas tienen.
- `texto`: dónde empieza el texto de las fichas y cuántos bytes tiene.

Un lector debe tomar los anchos de la cabecera, no de este documento: pueden cambiar al regenerar.

### Tabla de fichas

Un registro por ficha, en el orden del texto. El número de una ficha (su id, desde 0) es su sitio en esta tabla.

```
00600555 000428 I inicio
```

Posición de la ficha (8 cifras), su largo en bytes (6), su tipo (1 letra) y su clave, rellena con espacios hasta el
largo del registro. Columnas: 0, 9, 16 y 18.

### Nombres

Para "Ayuda sobre la palabra del cursor": los nombres ordenados byte a byte, en minúsculas, con el id de su ficha.

```
file_seek                    00538
```

El nombre, relleno con espacios hasta `largo - 7`, un espacio y el id (5 cifras). Están las claves de todas las
fichas (en minúsculas: `ra_event_close`) y las palabras del lenguaje y de temas que llevan a un apartado del manual
(`if`, `while`, `struct`, `eventloop`, `window`, `nil`, `memcheck`...). Se busca con búsqueda binaria: el nombre
pedido en minúsculas, y se compara con el del registro sin los espacios del final.

### Palabras e ids

El índice para buscar. Cada palabra de las fichas (también las del código de los ejemplos), plegada: en minúsculas,
sin acentos y con lo que no sea `a-z`, `0-9` o `_` como separador:

| Latin-1 | Queda |
|---|---|
| `à á â ã ä å` | `a` |
| `ç` | `c` |
| `è é ê ë` | `e` |
| `ì í î ï` | `i` |
| `ñ` | `n` |
| `ò ó ô õ ö` | `o` |
| `ù ú û ü` | `u` |
| `ý ÿ` | `y` |
| `æ ð ÷ ø þ ß` y el resto | separador |

(en el código, una tabla de un carácter por código desde 0xE0: `"aaaaaa ceeeeiiii nooooo  uuuuy y"`). Un nombre con `_` está
entero y por partes (`sound_play`, `sound`, `play`). Se quedan fuera las de menos de 3 letras o más de 24, los
números, unas palabras vacías (`de`, `the`...) y las que salen en más de la cuarta parte de las fichas.

```
musica                   00315046 0013
```

La palabra, rellena hasta `largo - 15`, un espacio, dónde están sus ids (8 cifras) y cuántos son (4). Los ids son
números de 5 cifras, cada uno con un espacio detrás salvo el último, que lleva `\n`: el id `k` de la lista está en
`posición + k * 6`. Van de más a menos puntos: 10 si la palabra está en la clave o el título de la ficha, y uno por
cada vez que sale en su texto.

Como están ordenadas, una búsqueda binaria da también la primera palabra que empieza por un prefijo, para completar
lo que se escribe.

### Grupos y secciones

Líneas de texto, para pintar el índice sin leer las fichas:

```
00041 Gráficos básicos              (grupos: id y título, en el orden de docs/BUILTINS.md)
00003 1 1. Introduccion             (secciones: id, nivel 1 capítulo o 2 apartado, y título)
```

### El texto de una ficha

Desde su posición, su largo en bytes; entre una ficha y la siguiente hay una línea en blanco que no cuenta. El
primer carácter de cada línea dice qué es:

| Prefijo | Línea |
|---|---|
| `@` | La primera: `@clave tipo título` |
| `%` | Un campo: `%nombre valor` (abajo) |
| `#` | Un subtítulo |
| ` ` (espacio) | Texto, ya cortado a 76 columnas (77 con el prefijo); las listas y las tablas, ya alineadas |
| `\|` | Una línea de código, tal cual (sin cortar: puede pasar de 76) |
| `*` | Un enlace: `*clave texto`. La clave es la de otra ficha; el texto, lo que se enseña |
| (vacía) | Una línea en blanco |

Campos de las funciones: `%firma file_seek(handle, position, mode) -> Int`, `%devuelve Int` (`-` si nada),
`%grupo dos_functions` (la clave de su grupo), `%dashos si|no|solo` (si está en DashOS, `./dash --dashos`; `solo`:
solo allí) y `%ejemplo tests/test_doc_ficheros.dash` (de dónde sale su ejemplo, si tiene). Los de los grupos:
`%funciones 42` y `%ejemplo ...`. Un lector debe saltarse los campos que no conoce.

El texto no lleva marcas de Markdown. Los nombres de funciones dentro del texto no son enlaces en el `.ayuda` (en el
AmigaGuide sí); un lector puede buscar una palabra del texto en el índice de nombres para hacerla enlace.

[Volver al índice](#indice)

<a id="leerlo-desde-dash"></a>

## Leerlo desde Dash

`lib/ayuda.dash` lo hace con poca memoria (un búfer de 512 bytes y el de la ficha que se lee):

```dash
import "lib/ayuda.dash"

Main
    a = ayuda_abrir("DASH:Ayuda/Dash.ayuda")
    if a == nil
        return
    end
    for l in ayuda_ficha(a, ayuda_buscar(a, "file_seek"))
        Print l
    end
    for id in ayuda_palabra(a, "música")
        Print ayuda_clave(a, id) + ": " + ayuda_titulo(a, id)
    end
    ayuda_cerrar(a)
end
```

Además: `ayuda_fichas` (cuántas hay), `ayuda_tipo`, `ayuda_prefijo(a, "sou", 10)` (palabras que empiezan así) y
`ayuda_plegar`. `tests/ayuda/leer_fichas.dash` es la prueba: `tests/unit/test_gen_ayuda.py` la corre en el emulador
con `tests/run_tests.py --emu`.

[Volver al índice](#indice)

<a id="el-amigaguide"></a>

## El AmigaGuide

Un nodo por ficha, con la clave por nombre (la portada es `MAIN`), en el mismo orden, así que `Browse` pasa de un
grupo a sus funciones. `@index` es el nodo `indice`; `Contents` (`@toc`) lleva de una función a su grupo y de un
apartado a su capítulo. En el texto, los nombres de funciones que tienen ficha son enlaces. Abre con el MultiView de
AmigaOS 3.1 (probado en el emulador: necesita `REXX:` y `HELP:` asignados, como en un Workbench normal); tarda unos
segundos en cargar, porque son 1,2 MB.

[Volver al índice](#indice)
