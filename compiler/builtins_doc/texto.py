"""Texto (TEXT_FUNCTIONS), búferes (BUFFER_FUNCTIONS) y buscar en un búfer (BUFSEARCH_FUNCTIONS)."""

GROUPS = {
    "TEXT_FUNCTIONS": {
        "es": """\
Buscar, cortar, cambiar y convertir textos, y leer o escribir un fichero de texto entero.

Las funciones devuelven un texto nuevo: el original no cambia. Las posiciones empiezan en 0. Además de estas, el
lenguaje tiene `s.length`, `s[i]` (un carácter), `s[a:b]` (un trozo), `+` para unir, `Int(s)` y la interpolación
`"#{x}"` (manual, sección 5).

Los textos son Latin-1, un byte por carácter: la ñ y las vocales con acento ocupan uno. Un texto acaba en el primer
byte 0, así que al pasar datos de un fichero o un búfer a un texto los bytes 0 se vuelven espacios. Para datos
binarios, los búferes. Para texto UTF-8 (de la red), el grupo UTF-8.
""",
        "en": """\
Find, cut, change and convert texts, and read or write a whole text file.

The functions return a new text: the original does not change. Positions start at 0. Besides these, the language
has `s.length`, `s[i]` (one character), `s[a:b]` (a slice), `+` to join, `Int(s)` and interpolation `"#{x}"`
(manual, section 5).

Texts are Latin-1, one byte per character: ñ and accented vowels take one. A text ends at the first 0 byte, so when
data from a file or a buffer becomes a text, 0 bytes turn into spaces. For binary data, buffers. For UTF-8 text
(from the network), the UTF-8 group.
""",
        "example": "tests/test_doc_texto.dash",
    },
    "BUFFER_FUNCTIONS": {
        "es": """\
Memoria en bruto para datos binarios: ficheros que no son texto, imágenes, lo que se manda por la red. Un búfer es
la dirección de un bloque de memoria; las posiciones (`offset`) son bytes desde su principio.

Dash no comprueba los límites: leer o escribir fuera del búfer toca otra memoria y puede colgar el Amiga. Y no se
libera solo: cada `buffer_alloc` necesita su `buffer_free`, o esa memoria se pierde hasta reiniciar.

Los números de 16 y 32 bits van como en el 68000, el byte alto primero (big-endian), que es como los guardan los
ficheros del Amiga (IFF).
""",
        "en": """\
Raw memory for binary data: files that are not text, pictures, what goes over the network. A buffer is the address
of a block of memory; positions (`offset`) are bytes from its start.

Dash does not check bounds: reading or writing outside the buffer touches other memory and can hang the Amiga. And
it is not freed on its own: every `buffer_alloc` needs its `buffer_free`, or that memory is lost until a reboot.

16 and 32-bit numbers go as on the 68000, high byte first (big-endian), which is how Amiga files (IFF) store them.
""",
    },
    "BUFSEARCH_FUNCTIONS": {
        "es": """\
Comparar y buscar dentro de un búfer sin pasarlo a texto, para leer formatos o protocolos deprisa.
""",
        "en": """\
Compare and search inside a buffer without turning it into a text, to read formats or protocols quickly.
""",
    },
}


def _f(es, en, see=()):
    return {"es": es, "en": en, "see": list(see)}


_S_ES = "- `s`: el texto.\n"
_S_EN = "- `s`: the text.\n"
_BUF_ES = "- `buffer`: el búfer.\n- `offset`: la posición, en bytes desde el principio.\n"
_BUF_EN = "- `buffer`: the buffer.\n- `offset`: the position, in bytes from the start.\n"

FUNCS = {
    "str_code": _f(_S_ES + "- `i`: la posición, desde 0.\n\nDevuelve el código Latin-1 (0 a 255) del carácter; 0 fuera del texto. Es `Int(s[i])`.\n",
                   _S_EN + "- `i`: the position, from 0.\n\nReturns the character's Latin-1 code (0 to 255); 0 outside the text. It is `Int(s[i])`.\n",
                   ["str_char"]),
    "str_char": _f("- `code`: un código Latin-1, de 1 a 255.\n\nDevuelve un texto de un carácter: `str_char(65)` es `\"A\"`.\n",
                   "- `code`: a Latin-1 code, 1 to 255.\n\nReturns a one-character text: `str_char(65)` is `\"A\"`.\n",
                   ["str_code"]),
    "str_find": _f(_S_ES + "- `sub`: lo que se busca.\n\nDevuelve la posición de su primera aparición, o -1 si no está. Distingue mayúsculas.\n",
                   _S_EN + "- `sub`: what to look for.\n\nReturns the position of its first appearance, or -1 if it is not there. It is case sensitive.\n",
                   ["str_find_from", "str_contains"]),
    "str_find_from": _f(_S_ES + """\
- `sub`: lo que se busca.
- `start`: desde qué posición.

Como `str_find`, empezando en `start`. Para encontrar todas: se vuelve a buscar desde la anterior más uno.
""", _S_EN + """\
- `sub`: what to look for.
- `start`: the position to start at.

Like `str_find`, starting at `start`. To find them all, search again from the previous one plus one.
""", ["str_find"]),
    "str_starts": _f(_S_ES + "- `prefix`: el principio.\n\nDevuelve `true` si `s` empieza por `prefix`.\n",
                     _S_EN + "- `prefix`: the beginning.\n\nReturns `true` if `s` starts with `prefix`.\n", ["str_ends"]),
    "str_ends": _f(_S_ES + "- `suffix`: el final.\n\nDevuelve `true` si `s` acaba en `suffix`: `str_ends(nombre, \".iff\")`.\n",
                   _S_EN + "- `suffix`: the end.\n\nReturns `true` if `s` ends with `suffix`: `str_ends(name, \".iff\")`.\n",
                   ["str_starts"]),
    "str_lower": _f(_S_ES + "\nDevuelve una copia en minúsculas, también las letras con acento y la Ñ.\n",
                    _S_EN + "\nReturns a lower-case copy, accented letters and Ñ included.\n", ["str_upper"]),
    "str_upper": _f(_S_ES + "\nDevuelve una copia en mayúsculas, también las letras con acento y la ñ.\n",
                    _S_EN + "\nReturns an upper-case copy, accented letters and ñ included.\n", ["str_lower"]),
    "str_trim": _f(_S_ES + "\nDevuelve una copia sin los espacios, tabuladores y saltos de línea del principio y del final.\n",
                   _S_EN + "\nReturns a copy without the spaces, tabs and line breaks at the start and the end.\n",
                   ["str_split"]),
    "str_to_int": _f(_S_ES + """\
- `base`: la base, de 2 a 36; otra cuenta como 10.

Devuelve el número escrito al principio del texto: salta los espacios, admite un signo y lee cifras de esa base
(letras en mayúscula o minúscula) hasta la primera que no lo es. 0 si no hay ninguna. `str_to_int("ff", 16)` es
255.
""", _S_EN + """\
- `base`: the base, 2 to 36; any other counts as 10.

Returns the number written at the start of the text: it skips spaces, takes a sign and reads digits of that base
(letters in either case) up to the first one that is not. 0 if there are none. `str_to_int("ff", 16)` is 255.
""", ["str_from_int"]),
    "str_from_int": _f("""\
- `n`: el número.
- `base`: la base, de 2 a 36.

Devuelve el número escrito en esa base, con letras en minúscula: `str_from_int(255, 16)` es `"ff"`. En base 10
basta la interpolación: `"#{n}"`.
""", """\
- `n`: the number.
- `base`: the base, 2 to 36.

Returns the number written in that base, with lower-case letters: `str_from_int(255, 16)` is `"ff"`. In base 10,
interpolation is enough: `"#{n}"`.
""", ["str_to_int"]),
    "str_replace": _f(_S_ES + """\
- `from`: lo que se cambia.
- `to`: por qué; `""` lo quita.

Devuelve una copia con cada aparición de `from` cambiada por `to`.
""", _S_EN + """\
- `from`: what to change.
- `to`: what to put instead; `""` removes it.

Returns a copy with every appearance of `from` changed to `to`.
""", ["str_find"]),
    "str_contains": _f(_S_ES + "- `sub`: lo que se busca.\n\nDevuelve `true` si `sub` está en `s`. `\"\"` está en todos.\n",
                       _S_EN + "- `sub`: what to look for.\n\nReturns `true` if `sub` is in `s`. `\"\"` is in every text.\n",
                       ["str_find"]),
    "str_split": _f(_S_ES + """\
- `sep`: el separador.

Devuelve una lista `[String]` con los trozos de `s` entre cada `sep`. Dos separadores seguidos dan un trozo `""`.
Con `sep` vacío, o si no aparece, la lista tiene solo `s`. `str_split(texto, "\\n")` da las líneas.
""", _S_EN + """\
- `sep`: the separator.

Returns a `[String]` list with the pieces of `s` between each `sep`. Two separators in a row give a `""` piece.
With an empty `sep`, or if it does not appear, the list holds just `s`. `str_split(text, "\\n")` gives the lines.
""", ["str_trim", "file_read_text"]),
    "file_read_text": _f("""\
- `filename`: la ruta.

Devuelve el fichero entero como un texto, o `nil` si no se puede leer. Los bytes 0 se vuelven espacios. Para
ficheros grandes hace falta memoria para todo el texto.
""", """\
- `filename`: the path.

Returns the whole file as a text, or `nil` if it cannot be read. 0 bytes turn into spaces. Large files need memory
for the whole text.
""", ["file_write_text", "str_split"]),
    "file_write_text": _f("""\
- `filename`: la ruta; si existía, se reemplaza.
- `text`: el texto.

Escribe el texto como el fichero entero. Devuelve `true` si se escribió todo.
""", """\
- `filename`: the path; if it existed, it is replaced.
- `text`: the text.

Writes the text as the whole file. Returns `true` if everything was written.
""", ["file_read_text", "file_write_line"]),
    "str_from_buffer": _f(_BUF_ES + """\
- `length`: cuántos bytes.

Devuelve un texto con esos bytes del búfer; los bytes 0 se vuelven espacios.
""", _BUF_EN + """\
- `length`: how many bytes.

Returns a text with those bytes of the buffer; 0 bytes turn into spaces.
""", ["str_to_buffer"]),
    "str_to_buffer": _f(_S_ES + """\
- `buffer`: el búfer, con sitio para el texto.
- `offset`: dónde se copia.

Copia los bytes del texto, sin el 0 del final, y devuelve cuántos copió.
""", _S_EN + """\
- `buffer`: the buffer, with room for the text.
- `offset`: where to copy it.

Copies the text's bytes, without the final 0, and returns how many it copied.
""", ["str_from_buffer"]),
    # ------------------------------------------------------------ búferes
    "buffer_alloc": _f("""\
- `size`: cuántos bytes.

Pide un bloque de memoria, lleno de ceros. Devuelve su dirección, o 0 si no hay memoria. Hay que liberarlo con
`buffer_free`.
""", """\
- `size`: how many bytes.

Asks for a block of memory, filled with zeros. Returns its address, or 0 if there is no memory. It must be freed
with `buffer_free`.
""", ["buffer_free", "file_load"]),
    "buffer_free": _f("- `buffer`: el búfer; 0 no hace nada.\n\nDevuelve la memoria. Después el búfer no se puede usar.\n",
                      "- `buffer`: the buffer; 0 does nothing.\n\nGives the memory back. Afterwards the buffer cannot be used.\n",
                      ["buffer_alloc"]),
    "buffer_get_byte": _f(_BUF_ES + "\nDevuelve el byte, de 0 a 255.\n", _BUF_EN + "\nReturns the byte, 0 to 255.\n",
                          ["buffer_set_byte"]),
    "buffer_set_byte": _f(_BUF_ES + "- `value`: el byte; cuentan sus 8 bits de abajo.\n",
                          _BUF_EN + "- `value`: the byte; its low 8 bits count.\n", ["buffer_get_byte"]),
    "buffer_get_word": _f(_BUF_ES + "\nDevuelve el número de 16 bits de esa posición, de 0 a 65535, con el byte alto primero.\n",
                          _BUF_EN + "\nReturns the 16-bit number at that position, 0 to 65535, high byte first.\n",
                          ["buffer_set_word"]),
    "buffer_set_word": _f(_BUF_ES + "- `value`: el número; cuentan sus 16 bits de abajo.\n",
                          _BUF_EN + "- `value`: the number; its low 16 bits count.\n", ["buffer_get_word"]),
    "buffer_get_long": _f(_BUF_ES + "\nDevuelve el número de 32 bits de esa posición, con signo, con el byte alto primero.\n",
                          _BUF_EN + "\nReturns the signed 32-bit number at that position, high byte first.\n",
                          ["buffer_set_long"]),
    "buffer_set_long": _f(_BUF_ES + "- `value`: el número.\n", _BUF_EN + "- `value`: the number.\n",
                          ["buffer_get_long"]),
    "buffer_copy": _f("""\
- `dest`, `dest_offset`: adónde.
- `src`, `src_offset`: de dónde.
- `length`: cuántos bytes.

Copia bytes de un búfer a otro, o dentro del mismo si las zonas no se pisan.
""", """\
- `dest`, `dest_offset`: where to.
- `src`, `src_offset`: where from.
- `length`: how many bytes.

Copies bytes from one buffer to another, or within the same one if the areas do not overlap.
""", ["buffer_fill"]),
    "buffer_fill": _f(_BUF_ES + "- `length`: cuántos bytes.\n- `value`: el byte con el que se llenan.\n",
                      _BUF_EN + "- `length`: how many bytes.\n- `value`: the byte to fill them with.\n", ["buffer_copy"]),
    "buffer_equals": _f(_BUF_ES + """\
- `n`: cuántos bytes.
- `s`: el texto.

Devuelve `true` si esos `n` bytes son exactamente el texto `s` y `s` tiene `n` bytes. Para mirar la cabecera de un
fichero: `buffer_equals(b, 0, 4, "FORM")`.
""", _BUF_EN + """\
- `n`: how many bytes.
- `s`: the text.

Returns `true` if those `n` bytes are exactly the text `s` and `s` has `n` bytes. To check a file's header:
`buffer_equals(b, 0, 4, "FORM")`.
""", ["buffer_find_byte"]),
    "buffer_find_byte": _f("""\
- `buffer`: el búfer.
- `from`, `to`: dónde se busca, de `from` a `to - 1`.
- `byte`: el byte que se busca.

Devuelve la posición del primero, o -1. Para encontrar el final de una línea: `buffer_find_byte(b, i, n, 10)`.
""", """\
- `buffer`: the buffer.
- `from`, `to`: where to search, from `from` to `to - 1`.
- `byte`: the byte to look for.

Returns the position of the first one, or -1. To find the end of a line: `buffer_find_byte(b, i, n, 10)`.
""", ["buffer_find_any"]),
    "buffer_find_any": _f("""\
- `buffer`: el búfer.
- `from`, `to`: de `from` a `to - 1`.
- `bytes`: un texto con los bytes que valen.

Devuelve la posición del primer byte que sea cualquiera de los de `bytes`, o -1.
""", """\
- `buffer`: the buffer.
- `from`, `to`: from `from` to `to - 1`.
- `bytes`: a text with the bytes that match.

Returns the position of the first byte that is any of those in `bytes`, or -1.
""", ["buffer_find_byte"]),
}
