"""Handlers de DOS, sistemas de archivos escritos en Dash (HANDLER_FUNCTIONS; docs/HANDLER_LOOP.md)."""

GROUPS = {
    "HANDLER_FUNCTIONS": {
        "es": """\
Un handler de DOS es el programa que hay detrás de un dispositivo como `DF0:` o `RAM:`: el DOS le manda un paquete
por cada cosa que piden los demás programas (abrir, leer, listar un cajón...) y él contesta. Con Dash se escribe
uno compilando con `./dash --handler` (o `--gcc --handler`), o importando `lib/amiga/handler.dash`, que ya lo pide
y trae las estructuras (`DosPacket`, `FileLock`, `FileInfoBlock`, `InfoData`...), las constantes `ACTION_*` y
`ERROR_*` y ayudas para cerraduras y fechas. Se monta con una mountlist (`Handler =` o, con un dispositivo de bloques,
`FileSystem =` y `Device =`) con `GlobVec = -1`.

El esquema: `handler_ready(true, 0)` al acabar de prepararse, y un bucle con `handler_wait()`, que da cada
paquete, y `packet_reply(paquete, res1, res2)`. Sin consola: `Print` no va a ninguna parte hasta `handler_log`, y un
error de ejecución va a ese registro. Un handler no debe pedir al DOS rutas de su propio volumen (se esperaría a sí
mismo); las de otros volúmenes, sí. Si acaba (con error o no), el DOS carga una copia nueva en el siguiente acceso.
Ejemplo completo: `examples/handler_ram.dash`, un disco en memoria. Más en la sección 28 del manual.
""",
        "en": """\
A DOS handler is the program behind a device such as `DF0:` or `RAM:`: the DOS sends it a packet for each thing
other programs ask for (open, read, list a drawer...) and it answers. In Dash you write one by compiling with
`./dash --handler` (or `--gcc --handler`), or by importing `lib/amiga/handler.dash`, which asks for it and brings the
structures (`DosPacket`, `FileLock`, `FileInfoBlock`, `InfoData`...), the `ACTION_*` and `ERROR_*` constants and
helpers for locks and dates. It is mounted with a mountlist (`Handler =` or, with a block device, `FileSystem =` and
`Device =`) with `GlobVec = -1`.

The outline: `handler_ready(true, 0)` once it is ready, and a loop with `handler_wait()`, which gives each packet,
and `packet_reply(packet, res1, res2)`. There is no console: `Print` goes nowhere until `handler_log`, and a runtime
error goes to that log. A handler must not ask the DOS for paths on its own volume (it would wait for itself);
other volumes are fine. If it ends (with an error or not), the DOS loads a new copy on the next access. Complete
example: `examples/handler_ram.dash`, a disk in memory. More in section 28 of the manual.
""",
    },
}


def _f(es, en, see=()):
    return {"es": es, "en": en, "see": list(see)}


FUNCS = {
    "handler_ready": _f("""\
- `ok`: `true` si el handler está listo; `false` si no puede funcionar.
- `error`: con `false`, el error que verá quien lo montó (`ERROR_NO_FREE_STORE`, `ERROR_NO_DISK`...).

Contesta al paquete de arranque. Hasta entonces, quien monta el dispositivo espera, y los paquetes de los demás se
quedan en cola. Con `false`, el programa debería acabar después.
""", """\
- `ok`: `true` if the handler is ready; `false` if it cannot work.
- `error`: with `false`, the error whoever mounted it will see (`ERROR_NO_FREE_STORE`, `ERROR_NO_DISK`...).

Answers the startup packet. Until then whoever mounts the device waits, and the packets of the others queue up.
With `false`, the program should end afterwards.
""", ["handler_wait", "handler_startup"]),
    "handler_wait": _f("""\
Espera el siguiente paquete y devuelve su dirección: con `Ptr DosPacket(p)` (de `lib/amiga/handler.dash`) se leen
`dp_Type` y `dp_Arg1`... Devuelve 0 si el handler recibe Ctrl-C (por ejemplo con `Break`). Antes de esperar,
vacía el registro de `handler_log`.

Cada paquete se contesta una vez con `packet_reply`. Si el programa acaba con un paquete sin contestar (un error de
ejecución), el runtime lo contesta con `ERROR_OBJECT_NOT_FOUND`, y también los que quedaban en cola.
""", """\
Waits for the next packet and gives its address: `Ptr DosPacket(p)` (from `lib/amiga/handler.dash`) reads `dp_Type`
and `dp_Arg1`... Gives 0 if the handler gets Ctrl-C (for instance with `Break`). Before waiting, it flushes the log
of `handler_log`.

Each packet is answered once with `packet_reply`. If the program ends with a packet unanswered (a runtime error),
the runtime answers it with `ERROR_OBJECT_NOT_FOUND`, and the ones still queued too.
""", ["packet_reply", "handler_poll"]),
    "packet_reply": _f("""\
- `packet`: lo que dio `handler_wait`.
- `res1`: el resultado (`DOSTRUE`, `DOSFALSE`, un BPTR de cerradura, los bytes leídos, -1...).
- `res2`: el error para `IoErr()` cuando falla (`ERROR_OBJECT_NOT_FOUND`...), 0 si no.

Ojo con `ERROR_DISK_WRITE_PROTECTED`, `ERROR_NO_DISK` y `ERROR_DEVICE_NOT_MOUNTED`: el DOS del cliente abre un
requester con ellos y espera a que alguien lo cierre.
""", """\
- `packet`: what `handler_wait` gave.
- `res1`: the result (`DOSTRUE`, `DOSFALSE`, the BPTR of a lock, the bytes read, -1...).
- `res2`: the error for `IoErr()` when it fails (`ERROR_OBJECT_NOT_FOUND`...), 0 if not.

Mind `ERROR_DISK_WRITE_PROTECTED`, `ERROR_NO_DISK` and `ERROR_DEVICE_NOT_MOUNTED`: the client's DOS opens a
requester with them and waits for someone to close it.
""", ["handler_wait"]),
    "handler_log": _f("""\
- `path`: un fichero de otro volumen (`T:mi.log`); se vacía al abrirlo y se puede leer mientras el handler va.

Desde ahí, `Print` y los errores de ejecución van a ese fichero. Sin él, `Print` no va a ninguna parte y un error
abre un requester.
""", """\
- `path`: a file of another volume (`T:my.log`); it is emptied when opened and can be read while the handler runs.

From then on, `Print` and the runtime errors go to that file. Without it, `Print` goes nowhere and an error opens a
requester.
"""),
    "handler_volume_add": _f("""\
- `name`: el nombre del volumen, sin los dos puntos.
- `disk_type`: lo que dirá `Info` (`ID_DOS_DISK`...).

El volumen apunta al puerto del handler, con la fecha de ahora. Se avisa al Workbench para que enseñe su icono. Al
acabar el programa, el volumen se queda como un disco sacado (por si alguien tiene cerraduras suyas): para
quitarlo, `handler_volume_remove`.
""", """\
- `name`: the volume's name, without the colon.
- `disk_type`: what `Info` will say (`ID_DOS_DISK`...).

The volume points to the handler's port, with the date of now. The Workbench is told, so it shows its icon. When
the program ends the volume stays as a disk taken out (someone may hold locks of it): `handler_volume_remove`
removes it.
""", ["handler_volume_remove"]),
    "bstr_put": _f("""\
- `addr`: dónde escribirlo (el `fib_FileName` de un `FileInfoBlock`: `fib + offsetof(FileInfoBlock, fib_FileName)`).
- `text`: el texto.
- `max`: los bytes que hay ahí (108 para `fib_FileName`, 80 para `fib_Comment`).

Pone un byte con el largo, las letras y un 0 detrás si cabe. Un texto más largo se corta.
""", """\
- `addr`: where to write it (the `fib_FileName` of a `FileInfoBlock`: `fib + offsetof(FileInfoBlock, fib_FileName)`).
- `text`: the text.
- `max`: the bytes there are (108 for `fib_FileName`, 80 for `fib_Comment`).

Writes a length byte, the characters and a 0 after them if it fits. A longer text is cut.
""", ["bstr_text"]),
    "dev_read": _f("""\
- `dev`: lo que dio `dev_open` (o `fssm_open()` de `lib/amiga/handler.dash`, con el dispositivo del montaje).
- `block`, `block_size`: desde qué bloque y de qué tamaño (el sitio en bytes es su producto, en 64 bits).
- `buf`, `len`: dónde dejarlo y cuántos bytes.

Devuelve 0 o el error del dispositivo. Hasta 4 GB usa `CMD_READ`; más allá, `TD_READ64` y, si el dispositivo no lo
conoce, `NSCMD_TD_READ64`. `buf` debe ser memoria que el dispositivo pueda usar (la de `buffer_alloc` vale).
""", """\
- `dev`: what `dev_open` gave (or `fssm_open()` from `lib/amiga/handler.dash`, with the mount's device).
- `block`, `block_size`: from which block and of what size (the place in bytes is their product, in 64 bits).
- `buf`, `len`: where to put it and how many bytes.

Gives 0 or the device's error. Up to 4 GB it uses `CMD_READ`; beyond, `TD_READ64` and, if the device does not know
it, `NSCMD_TD_READ64`. `buf` must be memory the device can use (`buffer_alloc`'s is fine).
""", ["dev_open", "dev_write", "dev_cmd"]),
}
