"""Ficheros (DOS_FUNCTIONS) y la petición de ficheros (ASL_FUNCTIONS)."""

GROUPS = {
    "DOS_FUNCTIONS": {
        "es": """\
Ficheros y cajones con la `dos.library`: abrir, leer, escribir, copiar, borrar, listar un cajón.

**Lo más sencillo primero.** Para un fichero de texto entero no hace falta abrirlo: `file_read_text(ruta)` lo
devuelve como un texto (o `nil` si no se puede leer) y `file_write_text(ruta, texto)` lo escribe (grupo Texto).
Con `str_split(texto, "\\n")` salen las líneas. Para datos binarios enteros, `file_load` y `file_save` con un búfer.

**Abrir y cerrar.** Para leer o escribir por partes:

1. `f = file_open(ruta, modo)`: 1005 para leer un fichero que existe, 1006 para crear uno nuevo (si existía, lo
   vacía), 1004 para leer y escribir uno que existe. Devuelve 0 si no se puede.
2. Leer o escribir: por bytes (`file_read_byte`), por líneas (`file_read_line`, `file_write_line`) o por bloques
   con un búfer (`file_read`, `file_write`).
3. `file_close(f)`. Lo que se escribió no está seguro en el disco hasta cerrarlo.

**Rutas.** Como en AmigaOS: `"RAM:notas.txt"`, `"DH0:Proyectos/juego/nivel1.map"`, `"PROGDIR:datos"` (el cajón del
programa). Una ruta sin volumen cuenta desde el cajón actual. Las mayúsculas no importan.

**Con búfer y sin él.** Las funciones de bytes y líneas (`file_read_byte`, `file_read_line`, `file_write_byte`,
`file_write_line`, `file_print`) usan un búfer de la `dos.library`, rápidas para cosas pequeñas. `file_read` y
`file_write` van directas. No las mezcles en el mismo fichero sin un `file_seek` entre medias.
""",
        "en": """\
Files and drawers with `dos.library`: open, read, write, copy, delete, list a drawer.

**The simplest first.** For a whole text file there is no need to open it: `file_read_text(path)` returns it as a
text (or `nil` if it cannot be read) and `file_write_text(path, text)` writes it (Text group). `str_split(text,
"\\n")` gives the lines. For whole binary data, `file_load` and `file_save` with a buffer.

**Open and close.** To read or write in pieces:

1. `f = file_open(path, mode)`: 1005 to read a file that exists, 1006 to create a new one (if it existed, it is
   emptied), 1004 to read and write one that exists. Returns 0 if it cannot.
2. Read or write: by bytes (`file_read_byte`), by lines (`file_read_line`, `file_write_line`) or by blocks with a
   buffer (`file_read`, `file_write`).
3. `file_close(f)`. What was written is not safe on disk until it is closed.

**Paths.** As in AmigaOS: `"RAM:notes.txt"`, `"DH0:Projects/game/level1.map"`, `"PROGDIR:data"` (the program's
drawer). A path without a volume counts from the current drawer. Case does not matter.

**Buffered and not.** The byte and line functions (`file_read_byte`, `file_read_line`, `file_write_byte`,
`file_write_line`, `file_print`) use a `dos.library` buffer, fast for small things. `file_read` and `file_write` go
direct. Do not mix them on the same file without a `file_seek` in between.
""",
        "example": "tests/test_doc_ficheros.dash",
    },
    "ASL_FUNCTIONS": {
        "es": """\
La petición de ficheros del sistema en dos pasos: `file_open_dialog` o `file_save_dialog` la enseñan, y después
`file_get_path`, `file_get_name` y `file_fullpath` dicen qué se eligió. En un paso, `dialog_file` (grupo Intuition)
devuelve ya la ruta entera. La petición recuerda el último cajón.
""",
        "en": """\
The system's file requester in two steps: `file_open_dialog` or `file_save_dialog` show it, and then
`file_get_path`, `file_get_name` and `file_fullpath` say what was chosen. In one step, `dialog_file` (Intuition
group) returns the full path at once. The requester remembers the last drawer.
""",
    },
}

FUNCS = {
    "file_open": {
        "es": """\
- `filename`: la ruta.
- `mode`: 1005 = leer uno que existe; 1006 = crear uno nuevo, vaciándolo si existía; 1004 = leer y escribir uno
  que existe, empezando por el principio.

Devuelve el fichero abierto, un número que se pasa a las demás funciones, o 0 si no se pudo: no existe, el cajón
no existe, el disco está protegido. Con 1006 y 1004, otro programa no puede abrirlo a la vez.
""",
        "en": """\
- `filename`: the path.
- `mode`: 1005 = read one that exists; 1006 = create a new one, emptying it if it existed; 1004 = read and write
  one that exists, starting at the beginning.

Returns the open file, a number passed to the other functions, or 0 if it could not: it does not exist, the drawer
does not exist, the disk is protected. With 1006 and 1004 no other program can open it at the same time.
""",
        "see": ["file_close", "file_read_line", "file_read_text"],
    },
    "file_close": {
        "es": """\
- `handle`: el fichero de `file_open`.

Cierra el fichero y escribe en el disco lo que quedaba en el búfer. Hay que cerrarlo siempre: un fichero abierto
queda bloqueado para los demás programas.
""",
        "en": """\
- `handle`: the file from `file_open`.

Closes the file and writes to disk what was left in the buffer. Always close it: an open file stays locked for
other programs.
""",
        "see": ["file_open"],
    },
    "file_read_byte": {
        "es": "- `handle`: el fichero.\n\nDevuelve el siguiente byte, de 0 a 255, o -1 al final del fichero.\n",
        "en": "- `handle`: the file.\n\nReturns the next byte, from 0 to 255, or -1 at the end of the file.\n",
        "see": ["file_eof", "file_read"],
    },
    "file_read_line": {
        "es": """\
- `handle`: el fichero.
- `buffer`: un búfer de `buffer_alloc` donde se lee la línea.
- `maxlen`: su tamaño en bytes; una línea más larga sale en trozos.

Devuelve la siguiente línea, con su `"\\n"` al final (`str_trim` lo quita), o `nil` al final del fichero. Lo que
devuelve vive en el búfer hasta la siguiente lectura; guardarlo en una variable hace una copia.
""",
        "en": """\
- `handle`: the file.
- `buffer`: a `buffer_alloc` buffer the line is read into.
- `maxlen`: its size in bytes; a longer line comes in pieces.

Returns the next line, with its `"\\n"` at the end (`str_trim` removes it), or `nil` at the end of the file. What it
returns lives in the buffer until the next read; storing it in a variable makes a copy.
""",
        "see": ["file_write_line", "file_read_text", "buffer_alloc"],
    },
    "file_read": {
        "es": """\
- `handle`: el fichero.
- `buffer`: dónde se leen los bytes.
- `length`: cuántos, como mucho; el búfer tiene que tener sitio.

Devuelve cuántos bytes leyó: menos que `length` cerca del final, 0 al final y -1 si hubo un error.
""",
        "en": """\
- `handle`: the file.
- `buffer`: where the bytes are read into.
- `length`: how many at most; the buffer must have room.

Returns how many bytes it read: fewer than `length` near the end, 0 at the end and -1 on an error.
""",
        "see": ["file_write", "file_load", "buffer_get_byte"],
    },
    "file_eof": {
        "es": """\
- `handle`: el fichero.

Devuelve `true` si ya no quedan bytes. Mira el siguiente sin gastarlo, así que se puede preguntar antes de cada
lectura: `while not file_eof(f)`.
""",
        "en": """\
- `handle`: the file.

Returns `true` if no bytes are left. It looks at the next one without using it up, so it can be asked before each
read: `while not file_eof(f)`.
""",
        "see": ["file_read_byte"],
    },
    "file_write_byte": {
        "es": "- `handle`: el fichero.\n- `byte`: el byte, de 0 a 255.\n\nDevuelve el byte escrito, o -1 si hubo un error.\n",
        "en": "- `handle`: the file.\n- `byte`: the byte, from 0 to 255.\n\nReturns the byte written, or -1 on an error.\n",
        "see": ["file_read_byte", "file_write"],
    },
    "file_write_line": {
        "es": """\
- `handle`: el fichero.
- `str`: el texto.

Escribe el texto y un salto de línea. Devuelve 0 si fue bien y -1 si hubo un error (el disco lleno).
""",
        "en": """\
- `handle`: the file.
- `str`: the text.

Writes the text and a line break. Returns 0 if it went well and -1 on an error (a full disk).
""",
        "see": ["file_print", "file_read_line", "file_write_text"],
    },
    "file_write": {
        "es": """\
- `handle`: el fichero.
- `buffer`: los bytes.
- `length`: cuántos.

Devuelve cuántos bytes escribió; menos que `length`, o -1, es un error.
""",
        "en": """\
- `handle`: the file.
- `buffer`: the bytes.
- `length`: how many.

Returns how many bytes it wrote; fewer than `length`, or -1, is an error.
""",
        "see": ["file_read", "file_save"],
    },
    "file_print": {
        "es": "- `handle`: el fichero.\n- `str`: el texto.\n\nEscribe el texto tal cual, sin salto de línea.\n",
        "en": "- `handle`: the file.\n- `str`: the text.\n\nWrites the text as it is, without a line break.\n",
        "see": ["file_write_line"],
    },
    "file_seek": {
        "es": """\
- `handle`: el fichero.
- `position`: cuántos bytes.
- `mode`: desde dónde: -1 = el principio, 0 = el sitio actual, 1 = el final. Dash no tiene las constantes
  `OFFSET_*`: se pone el número.

Lleva el sitio de lectura y escritura a esa posición: `file_seek(f, 0, -1)` vuelve al principio. Devuelve el
sitio de antes, o -1 si no pudo.
""",
        "en": """\
- `handle`: the file.
- `position`: how many bytes.
- `mode`: from where: -1 = the beginning, 0 = the current place, 1 = the end. Dash has no `OFFSET_*` constants: use
  the number.

Moves the read and write place to that position: `file_seek(f, 0, -1)` goes back to the start. Returns the place
before, or -1 if it could not.
""",
        "see": ["file_pos"],
    },
    "file_pos": {
        "es": "- `handle`: el fichero.\n\nDevuelve el sitio actual, en bytes desde el principio.\n",
        "en": "- `handle`: the file.\n\nReturns the current place, in bytes from the start.\n",
        "see": ["file_seek"],
    },
    "file_size": {
        "es": "- `filename`: la ruta.\n\nDevuelve el tamaño en bytes, sin abrirlo, o -1 si no existe.\n",
        "en": "- `filename`: the path.\n\nReturns the size in bytes, without opening it, or -1 if it does not exist.\n",
        "see": ["file_exists", "dir_entry_size"],
    },
    "file_exists": {
        "es": "- `filename`: la ruta.\n\nDevuelve `true` si existe, sea fichero o cajón.\n",
        "en": "- `filename`: the path.\n\nReturns `true` if it exists, file or drawer.\n",
        "see": ["file_size"],
    },
    "file_delete": {
        "es": """\
- `filename`: la ruta.

Borra el fichero, o el cajón si está vacío. Devuelve `false` si no pudo: no existe, está abierto, está protegido.
""",
        "en": """\
- `filename`: the path.

Deletes the file, or the drawer if it is empty. Returns `false` if it could not: it does not exist, it is open, it
is protected.
""",
        "see": ["file_rename"],
    },
    "file_rename": {
        "es": """\
- `oldname`, `newname`: la ruta de antes y la nueva.

Cambia el nombre o lo mueve a otro cajón del mismo disco. Devuelve `false` si no pudo; entre discos distintos no
se puede: `file_copy` y luego `file_delete`.
""",
        "en": """\
- `oldname`, `newname`: the old path and the new one.

Renames it or moves it to another drawer on the same disk. Returns `false` if it could not; across different disks
it cannot: `file_copy` and then `file_delete`.
""",
        "see": ["file_copy", "file_delete"],
    },
    "file_copy": {
        "es": """\
- `src`: el fichero que se copia.
- `dest`: la copia; si existía, se reemplaza.

Devuelve `true` si copió todo.
""",
        "en": """\
- `src`: the file to copy.
- `dest`: the copy; if it existed, it is replaced.

Returns `true` if it copied everything.
""",
        "see": ["file_rename"],
    },
    "dir_create": {
        "es": "- `path`: la ruta del cajón nuevo.\n\nLo crea. Devuelve `false` si no pudo o ya existía. No crea los de encima.\n",
        "en": "- `path`: the new drawer's path.\n\nCreates it. Returns `false` if it could not or it already existed. It does not create the ones above.\n",
        "see": ["dir_read", "dir_change"],
    },
    "dir_change": {
        "es": """\
- `path`: el cajón.

Lo hace el cajón actual: las rutas sin volumen cuentan desde él. Devuelve `false` si no existe. Al acabar el
programa se deja el cajón de antes.
""",
        "en": """\
- `path`: the drawer.

Makes it the current drawer: paths without a volume count from it. Returns `false` if it does not exist. When the
program ends, the old drawer is put back.
""",
        "see": ["dir_current"],
    },
    "dir_current": {
        "es": "Devuelve la ruta entera del cajón actual, con el nombre del volumen: `\"Ram Disk:\"`, `\"Work:Proyectos\"`.\n",
        "en": "Returns the full path of the current drawer, with the volume's name: `\"Ram Disk:\"`, `\"Work:Projects\"`.\n",
        "see": ["dir_change"],
    },
    "dir_read": {
        "es": """\
- `path`: el cajón.

Lee lo que hay en él, ordenado por nombre sin mirar mayúsculas, y devuelve cuántas entradas tiene; -1 si no es un
cajón que se pueda leer. Después, `dir_entry_name(i)` y las demás dan cada entrada, de 0 a la cuenta menos uno,
hasta el siguiente `dir_read`.
""",
        "en": """\
- `path`: the drawer.

Reads what is in it, sorted by name ignoring case, and returns how many entries it has; -1 if it is not a drawer
that can be read. Then `dir_entry_name(i)` and the others give each entry, from 0 to the count minus one, until the
next `dir_read`.
""",
        "see": ["dir_entry_name", "dir_entry_is_dir", "dir_entry_size", "dir_entry_date"],
    },
    "dir_entry_name": {
        "es": "- `i`: la entrada, desde 0.\n\nDevuelve su nombre, sin la ruta; `\"\"` si no hay entrada `i`.\n",
        "en": "- `i`: the entry, from 0.\n\nReturns its name, without the path; `\"\"` if there is no entry `i`.\n",
        "see": ["dir_read"],
    },
    "dir_entry_size": {
        "es": "- `i`: la entrada, desde 0.\n\nDevuelve su tamaño en bytes; 0 si es un cajón.\n",
        "en": "- `i`: the entry, from 0.\n\nReturns its size in bytes; 0 if it is a drawer.\n",
        "see": ["dir_read"],
    },
    "dir_entry_is_dir": {
        "es": "- `i`: la entrada, desde 0.\n\nDevuelve `true` si es un cajón.\n",
        "en": "- `i`: the entry, from 0.\n\nReturns `true` if it is a drawer.\n",
        "see": ["dir_read"],
    },
    "dir_entry_date": {
        "es": """\
- `i`: la entrada, desde 0.

Devuelve la fecha de su último cambio en segundos desde el 1 de enero de 1970, como `time_unix`. 0 si no hay
entrada `i`.
""",
        "en": """\
- `i`: the entry, from 0.

Returns the date of its last change in seconds since 1 January 1970, like `time_unix`. 0 if there is no entry `i`.
""",
        "see": ["dir_read", "time_unix"],
    },
    "dir_entry_protection": {
        "es": """\
- `i`: la entrada, desde 0.

Devuelve sus bits de protección tal como los guarda el sistema de ficheros: los bits 0 a 3 (d borrar, e ejecutar,
w escribir, r leer) puestos quieren decir que eso **no** se permite; 4 a (archivado), 5 p (puro), 6 s (guion),
7 h (oculto). -1 si no hay entrada `i`. Para un explorador de ficheros, como `List`.
""",
        "en": """\
- `i`: the entry, from 0.

Returns its protection bits as the file system keeps them: bits 0 to 3 (d delete, e execute, w write, r read) set
mean that is **not** allowed; 4 a (archived), 5 p (pure), 6 s (script), 7 h (hidden). -1 if there is no entry `i`.
For a file manager, like `List`.
""",
        "see": ["dir_read", "file_protection"],
    },
    "dir_entry_comment": {
        "es": "- `i`: la entrada, desde 0.\n\nDevuelve su comentario (la nota de `FileNote`); `\"\"` si no tiene.\n",
        "en": "- `i`: the entry, from 0.\n\nReturns its comment (the note of `FileNote`); `\"\"` if it has none.\n",
        "see": ["dir_read", "file_comment"],
    },
    "file_protection": {
        "es": """\
- `path`: el fichero o cajón.

Devuelve sus bits de protección (como `dir_entry_protection`); -1 si no existe o no se puede leer.

```dash
p = file_protection("RAM:hola")
if p & 4 != 0
    Print "no se puede escribir"
    ok = file_set_protection("RAM:hola", p - 4)   # que se pueda
end
```
""",
        "en": """\
- `path`: the file or drawer.

Returns its protection bits (like `dir_entry_protection`); -1 if it does not exist or cannot be read.

```dash
p = file_protection("RAM:hello")
if p & 4 != 0
    Print "it cannot be written"
    ok = file_set_protection("RAM:hello", p - 4)   # let it be
end
```
""",
        "see": ["file_set_protection", "dir_entry_protection"],
    },
    "file_set_protection": {
        "es": "- `path`: el fichero o cajón.\n- `bits`: los bits, como los da `file_protection`.\n\nLos pone, como `Protect`. Devuelve `false` si no pudo.\n",
        "en": "- `path`: the file or drawer.\n- `bits`: the bits, as `file_protection` gives them.\n\nSets them, like `Protect`. Returns `false` if it could not.\n",
        "see": ["file_protection"],
    },
    "file_comment": {
        "es": "- `path`: el fichero o cajón.\n\nDevuelve su comentario (la nota de `FileNote`); `\"\"` si no tiene o no se puede leer.\n",
        "en": "- `path`: the file or drawer.\n\nReturns its comment (the note of `FileNote`); `\"\"` if it has none or cannot be read.\n",
        "see": ["file_set_comment", "dir_entry_comment"],
    },
    "file_set_comment": {
        "es": "- `path`: el fichero o cajón.\n- `text`: el comentario, hasta 79 letras; `\"\"` lo quita.\n\nLo pone, como `FileNote`. Devuelve `false` si no pudo.\n",
        "en": "- `path`: the file or drawer.\n- `text`: the comment, up to 79 characters; `\"\"` removes it.\n\nSets it, like `FileNote`. Returns `false` if it could not.\n",
        "see": ["file_comment"],
    },
    "file_date": {
        "es": "- `path`: el fichero o cajón.\n\nDevuelve la fecha de su último cambio, como `time_unix`; 0 si no se puede leer.\n",
        "en": "- `path`: the file or drawer.\n\nReturns the date of its last change, like `time_unix`; 0 if it cannot be read.\n",
        "see": ["file_set_date", "dir_entry_date"],
    },
    "file_set_date": {
        "es": "- `path`: el fichero o cajón.\n- `t`: la fecha, como `time_unix`.\n\nLa pone, como `SetDate`. Devuelve `false` si no pudo.\n",
        "en": "- `path`: the file or drawer.\n- `t`: the date, like `time_unix`.\n\nSets it, like `SetDate`. Returns `false` if it could not.\n",
        "see": ["file_date"],
    },
    "file_copy_attrs": {
        "es": """\
- `src`: el original.
- `dest`: la copia.

Da a `dest` los bits de protección, el comentario y la fecha de `src`, para que la copia quede igual que el
original (como `Copy CLONE`). Devuelve `false` si alguno no se pudo poner.
""",
        "en": """\
- `src`: the original.
- `dest`: the copy.

Gives `dest` the protection bits, the comment and the date of `src`, so the copy is the same as the original (like
`Copy CLONE`). Returns `false` if any could not be set.
""",
        "see": ["file_copy", "file_copy_begin"],
    },
    "file_copy_begin": {
        "es": """\
- `src`: el fichero que se copia.
- `dest`: la copia; si existía, se reemplaza.

Empieza a copiar a trozos: entre un trozo y otro se puede enseñar cómo va y dejarlo a medias. Devuelve el número
de la copia (1 a 8; caben 8 a la vez), o 0 si no se puede abrir alguno de los dos.

```dash
n = file_copy_begin("DH0:grande.lha", "RAM:grande.lha")
total = file_size("DH0:grande.lha")
hecho = 0
paso = file_copy_step(n, 65536)
while paso > 0 and not parar
    hecho = hecho + paso
    Print "#{hecho * 100 / total} %"
    paso = file_copy_step(n, 65536)
end
ok = file_copy_end(n, paso == 0)    # entera: se queda; si no, se borra
```
""",
        "en": """\
- `src`: the file to copy.
- `dest`: the copy; if it existed, it is replaced.

Starts copying in steps: between one step and the next the progress can be shown and the copy left half done.
Returns the copy's number (1 to 8; 8 fit at once), or 0 if either file cannot be opened.

```dash
n = file_copy_begin("DH0:big.lha", "RAM:big.lha")
total = file_size("DH0:big.lha")
done = 0
step = file_copy_step(n, 65536)
while step > 0 and not stop
    done = done + step
    Print "#{done * 100 / total} %"
    step = file_copy_step(n, 65536)
end
ok = file_copy_end(n, step == 0)    # whole: it stays; otherwise it is deleted
```
""",
        "see": ["file_copy_step", "file_copy_end", "file_copy"],
    },
    "file_copy_step": {
        "es": "- `n`: la copia de `file_copy_begin`.\n- `most`: cuántos bytes como mucho en este trozo.\n\nDevuelve cuántos copió; 0 cuando ya está entera; -1 si hubo un error (disco lleno...).\n",
        "en": "- `n`: the copy from `file_copy_begin`.\n- `most`: how many bytes at most in this step.\n\nReturns how many it copied; 0 when it is whole; -1 on an error (disk full...).\n",
        "see": ["file_copy_begin", "file_copy_end"],
    },
    "file_copy_end": {
        "es": """\
- `n`: la copia de `file_copy_begin`.
- `keep`: `true` para quedársela.

Cierra los dos ficheros. Con `keep` y la copia entera, la copia se queda con los bits, el comentario y la fecha del
original y devuelve `true`; si no (cancelada, a medias o con error), borra lo copiado y devuelve `false`. Las que
queden abiertas al acabar el programa se borran.
""",
        "en": """\
- `n`: the copy from `file_copy_begin`.
- `keep`: `true` to keep it.

Closes both files. With `keep` and the copy whole, the copy gets the original's bits, comment and date and it
returns `true`; otherwise (cancelled, half done or with an error) it deletes what was copied and returns `false`.
Those still open when the program ends are deleted.
""",
        "see": ["file_copy_begin", "file_copy_step"],
    },
    "console_read": {
        "es": """\
- `buffer`: dónde se lee.
- `maxlen`: cuántos bytes como mucho.

Lee de la entrada del programa: el Shell, o lo que llegue con `<`. En el Shell espera a que se pulse Return y
devuelve cuántos bytes leyó, con el salto de línea; 0 al final de la entrada.
""",
        "en": """\
- `buffer`: where to read into.
- `maxlen`: how many bytes at most.

Reads from the program's input: the Shell, or what comes in with `<`. In the Shell it waits for Return and returns
how many bytes it read, line break included; 0 at the end of the input.
""",
        "see": ["console_write"],
    },
    "console_write": {
        "es": """\
- `str`: el texto.

Lo escribe en la salida del programa, sin salto de línea y sin búfer: sale al momento. Para una línea, `Print`.
""",
        "en": """\
- `str`: the text.

Writes it to the program's output, without a line break and without a buffer: it shows at once. For a line,
`Print`.
""",
        "see": ["console_read"],
    },
    "file_load": {
        "es": """\
- `filename`: la ruta.
- `buffer`: un búfer de `buffer_alloc`.
- `maxsize`: su tamaño.

Carga el fichero entero en el búfer. Devuelve los bytes leídos, o -1 si no existe o no cabe (`file_size` dice
cuánto hace falta).
""",
        "en": """\
- `filename`: the path.
- `buffer`: a `buffer_alloc` buffer.
- `maxsize`: its size.

Loads the whole file into the buffer. Returns the bytes read, or -1 if it does not exist or does not fit
(`file_size` says how much is needed).
""",
        "see": ["file_save", "file_size", "file_read_text"],
    },
    "file_save": {
        "es": """\
- `filename`: la ruta; si existía, se reemplaza.
- `buffer`: los bytes.
- `size`: cuántos.

Guarda el búfer como el fichero entero. Devuelve los bytes escritos: si no es `size`, falló (0 si no pudo crearlo).
""",
        "en": """\
- `filename`: the path; if it existed, it is replaced.
- `buffer`: the bytes.
- `size`: how many.

Saves the buffer as the whole file. Returns the bytes written: if it is not `size`, it failed (0 if it could not
create it).
""",
        "see": ["file_load", "file_write_text"],
    },
    "file_open_dialog": {
        "es": """\
- `title`: el título de la petición.
- `pattern`: qué ficheros se ven, con comodines de AmigaDOS (`"#?.iff"`).

Enseña la petición de abrir y espera. Devuelve `true` si se eligió un fichero: `file_fullpath()` da su ruta.
""",
        "en": """\
- `title`: the requester's title.
- `pattern`: which files show, with AmigaDOS wildcards (`"#?.iff"`).

Shows the open requester and waits. Returns `true` if a file was chosen: `file_fullpath()` gives its path.
""",
        "see": ["file_fullpath", "file_save_dialog", "dialog_file"],
    },
    "file_save_dialog": {
        "es": """\
- `title`, `pattern`: como en `file_open_dialog`.

Enseña la petición de guardar, donde se puede escribir un nombre nuevo, y espera. Devuelve `true` si se eligió uno.
""",
        "en": """\
- `title`, `pattern`: as in `file_open_dialog`.

Shows the save requester, where a new name can be typed, and waits. Returns `true` if one was chosen.
""",
        "see": ["file_open_dialog", "file_fullpath"],
    },
    "file_get_path": {
        "es": "Devuelve el cajón elegido en la última petición que se aceptó: `\"Work:Imágenes\"`.\n",
        "en": "Returns the drawer chosen in the last accepted requester: `\"Work:Pictures\"`.\n",
        "see": ["file_get_name", "file_fullpath"],
    },
    "file_get_name": {
        "es": "Devuelve el nombre del fichero elegido en la última petición que se aceptó, sin el cajón.\n",
        "en": "Returns the name of the file chosen in the last accepted requester, without the drawer.\n",
        "see": ["file_get_path", "file_fullpath"],
    },
    "file_fullpath": {
        "es": "Devuelve la ruta entera de la última petición aceptada: el cajón y el nombre, con su `/` si hace falta.\n",
        "en": "Returns the full path of the last accepted requester: the drawer and the name, with a `/` when needed.\n",
        "see": ["file_open_dialog", "dialog_file"],
    },
}
