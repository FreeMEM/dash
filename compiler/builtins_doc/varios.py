"""Argumentos, compresión, UTF-8, Double, matemáticas, expresiones regulares, portapapeles, ordenar y JSON."""

GROUPS = {
    "ARGS_FUNCTIONS": {
        "es": """\
Lo que recibe el programa al arrancar: los argumentos del Shell, o los iconos de proyecto con los que se abrió
desde el Workbench. Y dos cosas más de esa época del lenguaje: dónde fue el último clic y el reloj del programa.
""",
        "en": """\
What the program gets when it starts: the Shell arguments, or the project icons it was opened with from the
Workbench. And two more things from that stage of the language: where the last click was and the program's clock.
""",
        "example": "tests/test_doc_varios.dash",
    },
    "ZLIB_FUNCTIONS": {
        "es": """\
Comprimir y descomprimir deflate, gzip y zlib (lo de ZIP, PNG y HTTP), sumas de comprobación (CRC-32, Adler-32) y
SHA-1, todo sobre búferes. Es la zlib de siempre dentro del programa: no hace falta ninguna librería instalada.
""",
        "en": """\
Compressing and decompressing deflate, gzip and zlib (what ZIP, PNG and HTTP use), checksums (CRC-32, Adler-32) and
SHA-1, all on buffers. It is the usual zlib inside the program: no library needs to be installed.
""",
    },
    "UTF8_FUNCTIONS": {
        "es": """\
Los textos de Dash son Latin-1, pero lo que llega de la red suele ser UTF-8, donde un carácter ocupa de 1 a 4
bytes. Estas funciones recorren un texto UTF-8 carácter a carácter (las posiciones son bytes) y lo pasan a
Latin-1 y al revés.
""",
        "en": """\
Dash's texts are Latin-1, but what comes from the network is usually UTF-8, where a character takes 1 to 4 bytes.
These functions walk a UTF-8 text character by character (positions are bytes) and convert it to Latin-1 and back.
""",
    },
    "DOUBLE_FUNCTIONS": {
        "es": """\
Pasar un `Double` (64 bits) a texto con los decimales que se quieran, y un texto a `Double`, sin perder cifras.
""",
        "en": """\
Turning a `Double` (64 bits) into a text with the decimals you want, and a text into a `Double`, without losing
digits.
""",
    },
    "MATH_FUNCTIONS": {
        "es": """\
Las funciones matemáticas de siempre con `Double`. Los ángulos van en radianes (180 grados son 3.14159...). Un
resultado imposible no para el programa: da `nan` (no es un número) o `inf`, que se miran con `is_nan` e `is_inf`.
""",
        "en": """\
The usual maths functions with `Double`. Angles are in radians (180 degrees is 3.14159...). An impossible result
does not stop the program: it gives `nan` (not a number) or `inf`, checked with `is_nan` and `is_inf`.
""",
    },
    "REGEX_FUNCTIONS": {
        "es": """\
Expresiones regulares (la sintaxis común de ICU) y comodines de hoja de cálculo sobre textos UTF-8; las
posiciones y largos van en bytes. Un patrón mal escrito no para el programa: da `false` o -1 y `regex_error`
dice por qué. La sintaxis entera, en el manual (sección 5).
""",
        "en": """\
Regular expressions (ICU's common syntax) and spreadsheet wildcards on UTF-8 texts; positions and lengths are in
bytes. A badly written pattern does not stop the program: it gives `false` or -1 and `regex_error` says why. The
full syntax is in the manual (section 5).
""",
    },
    "CLIP_FUNCTIONS": {
        "es": """\
El portapapeles del sistema: copiar y pegar texto con los demás programas, y bloques propios que solo entiende el
programa (unas celdas, un dibujo) unidos a ese texto.
""",
        "en": """\
The system clipboard: copying and pasting text with other programs, and blocks of your own that only the program
understands (some cells, a drawing) tied to that text.
""",
    },
    "COLLATE_FUNCTIONS": {
        "es": "Ordenar textos como lo hace el idioma del usuario, no por el código de cada letra.\n",
        "en": "Sorting texts the way the user's language does, not by each letter's code.\n",
    },
    "JSON_FUNCTIONS": {
        "es": """\
La parte en C del lector de JSON. Para usar JSON en un programa, mejor el módulo `lib/json.dash`, que hace con
esto un árbol cómodo de recorrer.
""",
        "en": """\
The C part of the JSON reader. To use JSON in a program, the `lib/json.dash` module is better: it builds an
easy-to-walk tree from this.
""",
    },
}


def _f(es, en, see=()):
    return {"es": es, "en": en, "see": list(see)}


_X_ES = "- `x`: el número, un `Double`.\n"
_X_EN = "- `x`: the number, a `Double`.\n"
_SHA_ES = "- `sha`: el número de `sha1_new`.\n"
_SHA_EN = "- `sha`: the number from `sha1_new`.\n"
_J_ES = "- `i`: el nodo, desde 0.\n"
_J_EN = "- `i`: the node, from 0.\n"


def _m(es_txt, en_txt, see=()):
    return _f(_X_ES + "\n" + es_txt, _X_EN + "\n" + en_txt, see)


FUNCS = {
    # ------------------------------------------------------------ argumentos
    "arg_count": _f("""\
Devuelve cuántos argumentos recibió: las palabras tras el nombre en el Shell, o los iconos de proyecto con los que
se abrió desde el Workbench (un doble clic en un documento, o Mayúsculas y clic en varios).
""", """\
Returns how many arguments it got: the words after the name in the Shell, or the project icons it was opened with
from the Workbench (a double click on a document, or Shift and click on several).
""", ["arg"]),
    "arg": _f("""\
- `i`: el argumento, desde 0.

Devuelve ese argumento, o `""` si no lo hay. Desde el Workbench, la ruta entera del icono. Un argumento entre
comillas en el Shell llega sin ellas, como uno solo.
""", """\
- `i`: the argument, from 0.

Returns that argument, or `""` if there is none. From the Workbench, the icon's full path. An argument in quotes in
the Shell arrives without them, as a single one.
""", ["arg_count"]),
    "click_x": _f("Dentro de un `On Click`, devuelve la X del clic dentro de los bordes de la ventana.\n",
                  "Inside an `On Click`, returns the click's X inside the window's borders.\n", ["click_y"]),
    "click_y": _f("Dentro de un `On Click`, devuelve la Y del clic dentro de los bordes de la ventana.\n",
                  "Inside an `On Click`, returns the click's Y inside the window's borders.\n", ["click_x"]),
    "time_ms": _f("""\
Devuelve los milisegundos desde que empezó el programa, con el reloj fino del sistema. Para medir cuánto tarda
algo o mover las cosas de un juego al mismo ritmo en cualquier máquina.
""", """\
Returns the milliseconds since the program started, with the system's fine clock. To time something or move a
game's things at the same pace on any machine.
""", ["time_delay"]),
    # ------------------------------------------------------------ zlib
    "inflate": _f("""\
- `src`, `n`: el búfer comprimido y cuántos bytes tiene.
- `dest`, `max`: dónde se descomprime y cuánto cabe.

Descomprime deflate sin cabecera (el de dentro de un ZIP). Devuelve los bytes escritos, -1 si no es deflate o está
cortado, -2 si no cabe en `max`, -3 sin memoria.
""", """\
- `src`, `n`: the compressed buffer and how many bytes it has.
- `dest`, `max`: where to decompress to and how much fits.

Decompresses headerless deflate (what is inside a ZIP). Returns the bytes written, -1 if it is not deflate or is
cut short, -2 if it does not fit in `max`, -3 without memory.
""", ["inflate_auto", "deflate", "inflate_used"]),
    "inflate_auto": _f("""\
- `src`, `n`, `dest`, `max`: como en `inflate`.

Como `inflate`, pero mira los primeros bytes y sirve para gzip, zlib o deflate sin cabecera: lo que llega por HTTP
con `Content-Encoding: gzip`.
""", """\
- `src`, `n`, `dest`, `max`: as in `inflate`.

Like `inflate`, but it looks at the first bytes and handles gzip, zlib or headerless deflate: what arrives over HTTP
with `Content-Encoding: gzip`.
""", ["inflate"]),
    "deflate": _f("""\
- `src`, `n`: lo que se comprime.
- `dest`, `max`: dónde y cuánto cabe.
- `level`: de 0 (sin comprimir, rápido) a 9 (lo más pequeño); -1 = 6.

Comprime como deflate sin cabecera. Devuelve los bytes escritos, -2 si no caben, -3 sin memoria. Mientras trabaja
usa unos 260 KB.
""", """\
- `src`, `n`: what to compress.
- `dest`, `max`: where and how much fits.
- `level`: 0 (uncompressed, fast) to 9 (smallest); -1 = 6.

Compresses as headerless deflate. Returns the bytes written, -2 if they do not fit, -3 without memory. While working
it uses about 260 KB.
""", ["inflate"]),
    "crc32": _f("""\
- `buffer`, `n`: los bytes.
- `crc`: el CRC de lo anterior, para seguir por partes; 0 para empezar.

Devuelve el CRC-32, el de ZIP y PNG.
""", """\
- `buffer`, `n`: the bytes.
- `crc`: the CRC so far, to go on in parts; 0 to start.

Returns the CRC-32, the one ZIP and PNG use.
""", ["adler32"]),
    "adler32": _f("- `buffer`, `n`: los bytes.\n- `a`: lo anterior; 1 para empezar.\n\nDevuelve el Adler-32, la suma del final de un zlib.\n",
                  "- `buffer`, `n`: the bytes.\n- `a`: the value so far; 1 to start.\n\nReturns the Adler-32, the checksum at the end of a zlib stream.\n",
                  ["crc32"]),
    "inflate_used": _f("""\
Devuelve cuántos bytes de entrada usó el último `inflate` o `inflate_auto`: dónde empieza lo siguiente si van
varias cosas comprimidas seguidas (como en un pack de git).
""", """\
Returns how many input bytes the last `inflate` or `inflate_auto` used: where the next one starts if several
compressed things come one after another (as in a git pack).
""", ["inflate"]),
    "sha1": _f("- `buffer`, `n`: los bytes.\n\nDevuelve su SHA-1 en 40 cifras hexadecimales.\n",
               "- `buffer`, `n`: the bytes.\n\nReturns their SHA-1 as 40 hex digits.\n", ["sha1_text", "sha1_new"]),
    "sha1_text": _f("- `s`: el texto.\n\nDevuelve su SHA-1 en 40 cifras hexadecimales.\n",
                    "- `s`: the text.\n\nReturns its SHA-1 as 40 hex digits.\n", ["sha1"]),
    "sha1_new": _f("""\
Empieza un SHA-1 por partes, para datos que no están todos juntos. Devuelve su número (1 a 8), o 0 si están todos
en uso. Se le añade con `sha1_add*` y se acaba con `sha1_hex` o `sha1_bytes`.
""", """\
Starts a SHA-1 in parts, for data not all in one place. Returns its number (1 to 8), or 0 if all are in use. Add to
it with `sha1_add*` and finish with `sha1_hex` or `sha1_bytes`.
""", ["sha1_add", "sha1_hex"]),
    "sha1_add": _f(_SHA_ES + "- `buffer`, `n`: los bytes que se añaden.\n", _SHA_EN + "- `buffer`, `n`: the bytes to add.\n",
                   ["sha1_new"]),
    "sha1_add_text": _f(_SHA_ES + "- `s`: el texto que se añade.\n", _SHA_EN + "- `s`: the text to add.\n", ["sha1_new"]),
    "sha1_add_byte": _f(_SHA_ES + "- `b`: el byte, de 0 a 255.\n", _SHA_EN + "- `b`: the byte, 0 to 255.\n", ["sha1_new"]),
    "sha1_hex": _f(_SHA_ES + "\nLo acaba y devuelve las 40 cifras hexadecimales; `\"\"` si ese número no está en uso. El número queda libre.\n",
                   _SHA_EN + "\nFinishes it and returns the 40 hex digits; `\"\"` if that number is not in use. The number becomes free.\n",
                   ["sha1_bytes"]),
    "sha1_bytes": _f(_SHA_ES + "- `out`: un búfer de 20 bytes.\n\nLo acaba y escribe sus 20 bytes en `out`. Devuelve `false` si ese número no está en uso.\n",
                     _SHA_EN + "- `out`: a 20-byte buffer.\n\nFinishes it and writes its 20 bytes to `out`. Returns `false` if that number is not in use.\n",
                     ["sha1_hex"]),
    # ------------------------------------------------------------ UTF-8
    "utf8_next": _f("- `s`: el texto UTF-8.\n- `i`: la posición de un carácter, en bytes.\n\nDevuelve dónde empieza el siguiente carácter; al final, el largo del texto.\n",
                    "- `s`: the UTF-8 text.\n- `i`: a character's position, in bytes.\n\nReturns where the next character starts; at the end, the text's length.\n",
                    ["utf8_prev", "utf8_code"]),
    "utf8_prev": _f("- `s`: el texto UTF-8.\n- `i`: una posición en bytes.\n\nDevuelve dónde empieza el carácter anterior; 0 al principio.\n",
                    "- `s`: the UTF-8 text.\n- `i`: a position in bytes.\n\nReturns where the previous character starts; 0 at the beginning.\n",
                    ["utf8_next"]),
    "utf8_code": _f("- `s`: el texto UTF-8.\n- `i`: la posición del carácter.\n\nDevuelve su número Unicode; 65533 para un byte que no es UTF-8 válido, 0 fuera del texto.\n",
                    "- `s`: the UTF-8 text.\n- `i`: the character's position.\n\nReturns its Unicode number; 65533 for a byte that is not valid UTF-8, 0 outside the text.\n",
                    ["utf8_char"]),
    "utf8_char": _f("- `code`: un número Unicode.\n\nDevuelve ese carácter en UTF-8; `\"\"` para 0.\n",
                    "- `code`: a Unicode number.\n\nReturns that character in UTF-8; `\"\"` for 0.\n", ["utf8_code"]),
    "utf8_length": _f("- `s`: el texto UTF-8.\n\nDevuelve cuántos caracteres tiene (no bytes).\n",
                      "- `s`: the UTF-8 text.\n\nReturns how many characters it has (not bytes).\n", ["utf8_next"]),
    "utf8_to_latin1": _f("""\
- `s`: el texto UTF-8.

Devuelve el texto en Latin-1, para enseñarlo con las fuentes del Amiga. Lo que Latin-1 no tiene pasa a algo
parecido (las comillas curvas a rectas, € a EUR) o a `?`.
""", """\
- `s`: the UTF-8 text.

Returns the text in Latin-1, to show it with Amiga fonts. What Latin-1 lacks becomes something close (curly quotes
to straight ones, € to EUR) or `?`.
""", ["latin1_to_utf8"]),
    "latin1_to_utf8": _f("- `s`: un texto de Dash (Latin-1).\n\nDevuelve el texto en UTF-8, para mandarlo por la red o guardarlo para otros sistemas.\n",
                         "- `s`: a Dash text (Latin-1).\n\nReturns the text in UTF-8, to send it over the network or store it for other systems.\n",
                         ["utf8_to_latin1"]),
    "utf8_check": _f("- `buffer`: el búfer.\n- `from`, `to`: de `from` a `to - 1`.\n\nDevuelve la posición del primer byte que no es UTF-8 válido (o empieza un carácter cortado por `to`); -1 si todo vale.\n",
                     "- `buffer`: the buffer.\n- `from`, `to`: from `from` to `to - 1`.\n\nReturns the position of the first byte that is not valid UTF-8 (or starts a character cut by `to`); -1 if it is all valid.\n",
                     ["utf8_to_latin1"]),
    # ------------------------------------------------------------ Double
    "str_from_double": _f("""\
- `d`: el número.
- `decimals`: cuántos decimales; 0 ninguno; negativo, los justos para que se lea igual.

Devuelve el número como texto, redondeando las mitades lejos del cero: `str_from_double(2.675, 2)` es `"2.68"`.
""", """\
- `d`: the number.
- `decimals`: how many decimals; 0 none; negative, just enough to read back the same.

Returns the number as a text, rounding halves away from zero: `str_from_double(2.675, 2)` is `"2.68"`.
""", ["str_to_double"]),
    "str_to_double": _f("- `s`: el texto.\n\nDevuelve el número del principio del texto, exacto hasta 17 cifras; 0.0 si no hay número. Es `Double(s)`.\n",
                        "- `s`: the text.\n\nReturns the number at the start of the text, exact to 17 digits; 0.0 if there is no number. It is `Double(s)`.\n",
                        ["str_from_double"]),
    # ------------------------------------------------------------ matemáticas
    "sqrt": _m("Devuelve la raíz cuadrada; `nan` para un negativo.\n", "Returns the square root; `nan` for a negative.\n", ["pow"]),
    "pow": _f("- `x`: la base.\n- `y`: el exponente.\n\nDevuelve `x` elevado a `y`.\n", "- `x`: the base.\n- `y`: the exponent.\n\nReturns `x` to the power of `y`.\n", ["sqrt", "exp"]),
    "exp": _m("Devuelve e elevado a `x`.\n", "Returns e to the power of `x`.\n", ["log"]),
    "log": _m("Devuelve el logaritmo neperiano; `-inf` para 0, `nan` para un negativo.\n", "Returns the natural logarithm; `-inf` for 0, `nan` for a negative.\n", ["log10", "exp"]),
    "log10": _m("Devuelve el logaritmo en base 10.\n", "Returns the base-10 logarithm.\n", ["log"]),
    "sin": _m("Devuelve el seno de `x` radianes.\n", "Returns the sine of `x` radians.\n", ["cos", "asin"]),
    "cos": _m("Devuelve el coseno de `x` radianes.\n", "Returns the cosine of `x` radians.\n", ["sin"]),
    "tan": _m("Devuelve la tangente de `x` radianes.\n", "Returns the tangent of `x` radians.\n", ["atan"]),
    "asin": _m("Devuelve el arcoseno en radianes, de -pi/2 a pi/2; `nan` fuera de -1..1.\n", "Returns the arcsine in radians, -pi/2 to pi/2; `nan` outside -1..1.\n", ["sin"]),
    "acos": _m("Devuelve el arcocoseno en radianes, de 0 a pi; `nan` fuera de -1..1.\n", "Returns the arccosine in radians, 0 to pi; `nan` outside -1..1.\n", ["cos"]),
    "atan": _m("Devuelve el arcotangente en radianes, de -pi/2 a pi/2.\n", "Returns the arctangent in radians, -pi/2 to pi/2.\n", ["atan2"]),
    "atan2": _f("- `y`, `x`: el punto (fíjate en el orden).\n\nDevuelve el ángulo del punto en radianes, de -pi a pi: hacia dónde apunta, para girar un sprite hacia un objetivo.\n",
                "- `y`, `x`: the point (mind the order).\n\nReturns the point's angle in radians, -pi to pi: where it points, to turn a sprite towards a target.\n",
                ["atan"]),
    "floor": _m("Devuelve el mayor entero que no pasa de `x`, como `Double`: `floor(-2.5)` es -3.0.\n", "Returns the largest whole number not above `x`, as a `Double`: `floor(-2.5)` is -3.0.\n", ["ceil", "round", "trunc"]),
    "ceil": _m("Devuelve el menor entero que no es menor que `x`, como `Double`.\n", "Returns the smallest whole number not below `x`, as a `Double`.\n", ["floor"]),
    "round": _m("Devuelve el entero más cercano, las mitades lejos del cero: 2.5 da 3.0 y -2.5 da -3.0.\n", "Returns the nearest whole number, halves away from zero: 2.5 gives 3.0 and -2.5 gives -3.0.\n", ["floor", "trunc"]),
    "trunc": _m("Devuelve la parte entera, hacia el cero: -2.7 da -2.0.\n", "Returns the whole part, towards zero: -2.7 gives -2.0.\n", ["floor"]),
    "fmod": _f("- `x`, `y`: los dos números.\n\nDevuelve el resto de `x / y` con el signo de `x`; `nan` si `y` es 0.\n",
               "- `x`, `y`: the two numbers.\n\nReturns the remainder of `x / y` with the sign of `x`; `nan` if `y` is 0.\n", []),
    "abs": _m("Devuelve el valor absoluto, un `Double`.\n", "Returns the absolute value, a `Double`.\n", []),
    "is_nan": _m("Devuelve `true` si `x` es `nan`: el resultado de algo imposible, como `sqrt(-1.0)` o `0.0 / 0.0`.\n", "Returns `true` if `x` is `nan`: the result of something impossible, like `sqrt(-1.0)` or `0.0 / 0.0`.\n", ["is_inf"]),
    "is_inf": _m("Devuelve `true` si `x` es `inf` o `-inf`, como `1.0 / 0.0`.\n", "Returns `true` if `x` is `inf` or `-inf`, like `1.0 / 0.0`.\n", ["is_nan"]),
    # ------------------------------------------------------------ expresiones regulares
    "regex_match": _f("""\
- `pattern`: la expresión regular.
- `text`: el texto, en UTF-8.
- `ignore_case`: `true` para no distinguir mayúsculas.

Devuelve `true` si el texto entero encaja. `false` también si el patrón está mal (`regex_error`).
""", """\
- `pattern`: the regular expression.
- `text`: the text, in UTF-8.
- `ignore_case`: `true` to ignore case.

Returns `true` if the whole text matches. Also `false` if the pattern is wrong (`regex_error`).
""", ["regex_find", "wildcard_match"]),
    "regex_find": _f("""\
- `pattern`, `text`, `ignore_case`: como en `regex_match`.
- `from`: desde qué byte se busca.

Devuelve dónde empieza lo primero que encaja, o -1. `regex_length` da cuánto mide.
""", """\
- `pattern`, `text`, `ignore_case`: as in `regex_match`.
- `from`: the byte to start searching at.

Returns where the first match starts, or -1. `regex_length` gives its length.
""", ["regex_length", "regex_match"]),
    "regex_length": _f("Devuelve el largo en bytes de lo último que encajó; 0 si nada.\n", "Returns the length in bytes of the last match; 0 if none.\n", ["regex_find"]),
    "regex_error": _f("Devuelve por qué está mal el último patrón, o `\"\"` si está bien.\n", "Returns why the last pattern is wrong, or `\"\"` if it is fine.\n", ["regex_match"]),
    "wildcard_match": _f("""\
- `pattern`: con comodines de hoja de cálculo: `*` cualquier cosa, `?` un carácter, `~` delante de uno lo toma tal
  cual (`~*`).
- `text`, `ignore_case`: como en `regex_match`.

Devuelve `true` si el texto entero encaja. Para los comodines de AmigaDOS (`#?`), `dialog_file`.
""", """\
- `pattern`: with spreadsheet wildcards: `*` anything, `?` one character, `~` before one takes it literally
  (`~*`).
- `text`, `ignore_case`: as in `regex_match`.

Returns `true` if the whole text matches. For AmigaDOS wildcards (`#?`), `dialog_file`.
""", ["regex_match"]),
    # ------------------------------------------------------------ portapapeles
    "clip_write_text": _f("""\
- `s`: el texto, en UTF-8 (un texto normal de Dash vale si no tiene acentos; si los tiene, `latin1_to_utf8` antes).

Lo copia al portapapeles como lo leen los demás programas. Devuelve `false` si no se puede.
""", """\
- `s`: the text, in UTF-8 (a plain Dash text works if it has no accents; if it does, `latin1_to_utf8` first).

Copies it to the clipboard the way other programs read it. Returns `false` if it cannot.
""", ["clip_read_text"]),
    "clip_read_text": _f("Devuelve el texto del portapapeles en UTF-8 (`utf8_to_latin1` para enseñarlo); `\"\"` si está vacío o no tiene texto.\n",
                         "Returns the clipboard text in UTF-8 (`utf8_to_latin1` to show it); `\"\"` if it is empty or holds no text.\n",
                         ["clip_write_text"]),
    "clip_write_block": _f("""\
- `unit`: una unidad del portapapeles, de 1 a 255.
- `type`: un tipo de 4 letras propio (`"CELD"`).
- `buffer`, `n`: los bytes.

Después de `clip_write_text`, guarda un bloque propio unido a ese texto: si luego se copia otra cosa, el bloque deja
de valer. Así se pegan en el mismo programa unas celdas con su formato y en otros, el texto.
""", """\
- `unit`: a clipboard unit, 1 to 255.
- `type`: a 4-letter type of your own (`"CELL"`).
- `buffer`, `n`: the bytes.

After `clip_write_text`, stores a block of your own tied to that text: if something else is copied later, the block
is no longer valid. That way the same program pastes some cells with their format and others paste the text.
""", ["clip_read_block", "clip_block_size"]),
    "clip_block_size": _f("- `unit`, `type`: como en `clip_write_block`.\n\nDevuelve el tamaño del bloque, o -1 si no hay o se copió otra cosa después.\n",
                          "- `unit`, `type`: as in `clip_write_block`.\n\nReturns the block's size, or -1 if there is none or something else was copied since.\n",
                          ["clip_read_block"]),
    "clip_read_block": _f("- `unit`, `type`: como en `clip_write_block`.\n- `dest`, `max`: dónde y cuánto cabe.\n\nCopia el bloque. Devuelve sus bytes, -1 si no hay, -2 si no cabe.\n",
                          "- `unit`, `type`: as in `clip_write_block`.\n- `dest`, `max`: where and how much fits.\n\nCopies the block. Returns its bytes, -1 if there is none, -2 if it does not fit.\n",
                          ["clip_block_size"]),
    # ------------------------------------------------------------ ordenar
    "str_compare_locale": _f("""\
- `a`, `b`: los dos textos, en UTF-8.
- `ignore_case`: `true` para no distinguir mayúsculas.

Devuelve -1 si `a` va antes, 0 si son iguales y 1 si va antes `b`, en el orden del idioma del usuario: los acentos
y las mayúsculas cuentan solo después de las letras ("árbol" antes que "barco").
""", """\
- `a`, `b`: the two texts, in UTF-8.
- `ignore_case`: `true` to ignore case.

Returns -1 if `a` goes first, 0 if they are equal and 1 if `b` goes first, in the user's language order: accents and
case only count after the letters ("árbol" before "barco").
""", []),
    # ------------------------------------------------------------ JSON
    "json_scan": _f("""\
- `text`: el JSON.

Lo lee a una tabla de nodos en orden, cada uno seguido de lo que contiene. Devuelve cuántos nodos, o -1 si no es
JSON (`json_scan_error`).
""", """\
- `text`: the JSON.

Reads it into a table of nodes in order, each followed by what it contains. Returns how many nodes, or -1 if it is
not JSON (`json_scan_error`).
""", ["json_scan_kind", "json_scan_error"]),
    "json_scan_error": _f("Devuelve por qué el último `json_scan` dio -1 y en qué byte.\n", "Returns why the last `json_scan` gave -1 and at which byte.\n", ["json_scan"]),
    "json_scan_kind": _f(_J_ES + "\nDevuelve su tipo: 0 null, 1 true o false, 2 número, 3 texto, 4 lista, 5 objeto.\n",
                         _J_EN + "\nReturns its kind: 0 null, 1 true or false, 2 number, 3 text, 4 list, 5 object.\n", ["json_scan_count"]),
    "json_scan_count": _f(_J_ES + "\nEn una lista u objeto, cuántos elementos tiene (van detrás); en un booleano, 1 si es true.\n",
                          _J_EN + "\nFor a list or object, how many elements it has (they follow it); for a boolean, 1 if true.\n", ["json_scan_kind"]),
    "json_scan_text": _f(_J_ES + "\nDevuelve el texto de un nodo de texto, sin escapes y en UTF-8, o un número tal como está escrito.\n",
                         _J_EN + "\nReturns the text of a text node, unescaped and in UTF-8, or a number as written.\n", ["json_scan_name"]),
    "json_scan_name": _f(_J_ES + "\nDevuelve su nombre dentro de su objeto; `\"\"` en una lista o arriba del todo.\n",
                         _J_EN + "\nReturns its name inside its object; `\"\"` in a list or at the top.\n", ["json_scan_text"]),
}
