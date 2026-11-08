"""Sistema y memoria (SYSTEM_FUNCTIONS)."""

GROUPS = {
    "SYSTEM_FUNCTIONS": {
        "es": """\
La memoria del Amiga, esperar, números al azar y lo más cercano a la máquina: leer y escribir direcciones de memoria.

**Memoria.** El Amiga tiene memoria chip, la única que ven los chips de vídeo y sonido (imágenes, sprites,
sonidos), y memoria fast, solo para el procesador. `mem_*` dicen cuánta hay. Los textos, listas y structs de Dash
salen de un pool que se libera solo al acabar; los búferes, las arenas y `amiga_alloc` no: hay que liberarlos.

**Esperar.** `time_delay` cuenta en tics de 1/50 de segundo y no gasta CPU mientras espera. `wait_vblank` espera al
siguiente fotograma de la pantalla, para animar a su ritmo.

**Lo peligroso.** `peek_*` y `poke_*` leen y escriben cualquier dirección: escribir donde no se debe cuelga el
Amiga. `retain` y `release` tocan el contador de referencias que Dash lleva solo: equivocarse libera un objeto que
se sigue usando.
""",
        "en": """\
The Amiga's memory, waiting, random numbers and what is closest to the machine: reading and writing memory
addresses.

**Memory.** The Amiga has chip memory, the only one the video and sound chips see (pictures, sprites, sounds), and
fast memory, for the processor only. `mem_*` say how much there is. Dash's texts, lists and structs come from a pool
freed on its own at the end; buffers, arenas and `amiga_alloc` are not: they must be freed.

**Waiting.** `time_delay` counts in ticks of 1/50 of a second and uses no CPU while it waits. `wait_vblank` waits
for the screen's next frame, to animate at its pace.

**The dangerous part.** `peek_*` and `poke_*` read and write any address: writing where you should not hangs the
Amiga. `retain` and `release` touch the reference count Dash keeps on its own: getting it wrong frees an object
still in use.
""",
        "example": "tests/test_doc_sistema.dash",
    },
}


def _f(es, en, see=()):
    return {"es": es, "en": en, "see": list(see)}


_A_ES = "- `arena`: la arena de `arena_new`.\n"
_A_EN = "- `arena`: the arena from `arena_new`.\n"

FUNCS = {
    "debug_break": _f("""\
Para el programa en el depurador del emulador (`tools/emu_run.py --debug`). En un Amiga de verdad, o en un emulador
sin ese depurador, no hace nada.
""", """\
Stops the program in the emulator's debugger (`tools/emu_run.py --debug`). On a real Amiga, or an emulator without
that debugger, it does nothing.
""", []),
    "mem_chip_free": _f("Devuelve los bytes de memoria chip libres ahora.\n", "Returns the bytes of chip memory free now.\n",
                        ["mem_chip_total", "mem_fast_free"]),
    "mem_fast_free": _f("Devuelve los bytes de memoria fast libres ahora; 0 en un Amiga sin fast.\n",
                        "Returns the bytes of fast memory free now; 0 on an Amiga without fast.\n",
                        ["mem_fast_total", "mem_chip_free"]),
    "mem_total": _f("Devuelve los bytes libres sumando chip y fast. Es lo que queda, no el tamaño de la memoria.\n",
                    "Returns the free bytes adding chip and fast. It is what is left, not the size of the memory.\n",
                    ["mem_chip_free"]),
    "mem_chip_total": _f("Devuelve el tamaño de la memoria chip en bytes, libre y en uso: algo menos de 2 MB en un A1200.\n",
                         "Returns the size of chip memory in bytes, free and in use: a little under 2 MB on an A1200.\n",
                         ["mem_chip_free"]),
    "mem_fast_total": _f("Devuelve el tamaño de la memoria fast en bytes, libre y en uso.\n",
                         "Returns the size of fast memory in bytes, free and in use.\n", ["mem_fast_free"]),
    "peek_byte": _f("- `addr`: la dirección.\n\nDevuelve el byte que hay en ella, de 0 a 255.\n",
                    "- `addr`: the address.\n\nReturns the byte there, 0 to 255.\n", ["poke_byte", "buffer_get_byte"]),
    "peek_word": _f("- `addr`: la dirección, par.\n\nDevuelve los 16 bits que hay en ella. En un 68000, una dirección impar es un error de la CPU.\n",
                    "- `addr`: the address, even.\n\nReturns the 16 bits there. On a 68000, an odd address is a CPU error.\n",
                    ["poke_word"]),
    "peek_long": _f("- `addr`: la dirección, par.\n\nDevuelve los 32 bits que hay en ella.\n",
                    "- `addr`: the address, even.\n\nReturns the 32 bits there.\n", ["poke_long"]),
    "poke_byte": _f("- `addr`: la dirección.\n- `value`: el byte.\n\nLo escribe ahí. Una dirección equivocada cuelga el Amiga.\n",
                    "- `addr`: the address.\n- `value`: the byte.\n\nWrites it there. A wrong address hangs the Amiga.\n",
                    ["peek_byte"]),
    "poke_word": _f("- `addr`: la dirección, par.\n- `value`: los 16 bits.\n",
                    "- `addr`: the address, even.\n- `value`: the 16 bits.\n", ["peek_word"]),
    "poke_long": _f("- `addr`: la dirección, par.\n- `value`: los 32 bits.\n",
                    "- `addr`: the address, even.\n- `value`: the 32 bits.\n", ["peek_long"]),
    "amiga_alloc": _f("""\
- `size`: cuántos bytes.

Memoria a cero para estructuras de AmigaOS (`@amiga struct`) que se pasan al sistema. Devuelve la dirección, o 0
sin memoria. Se devuelve con `amiga_free` y el mismo tamaño; no se libera sola.
""", """\
- `size`: how many bytes.

Zeroed memory for AmigaOS structures (`@amiga struct`) handed to the system. Returns the address, or 0 without
memory. Give it back with `amiga_free` and the same size; it is not freed on its own.
""", ["amiga_free", "buffer_alloc"]),
    "amiga_free": _f("- `addr`: lo que dio `amiga_alloc`.\n- `size`: el mismo tamaño que se pidió.\n",
                     "- `addr`: what `amiga_alloc` gave.\n- `size`: the same size that was asked for.\n",
                     ["amiga_alloc"]),
    "time_delay": _f("""\
- `ticks`: cuántos tics; hay 50 por segundo (`time_delay(50)` es un segundo).

Espera sin gastar CPU: los demás programas siguen.
""", """\
- `ticks`: how many ticks; there are 50 a second (`time_delay(50)` is one second).

Waits without using CPU: other programs carry on.
""", ["time_delay_ms", "wait_vblank"]),
    "time_delay_ms": _f("""\
- `ms`: cuántos milisegundos.

Como `time_delay`, en milisegundos, de 20 en 20: menos de 20 no espera nada.
""", """\
- `ms`: how many milliseconds.

Like `time_delay`, in milliseconds, in steps of 20: under 20 does not wait at all.
""", ["time_delay"]),
    "random": _f("""\
Devuelve un número al azar de 0 a 32767. La serie es siempre la misma si no se cambia la semilla:
`random_seed(time_ms())` al empezar da una distinta cada vez.
""", """\
Returns a random number from 0 to 32767. The series is always the same unless the seed changes:
`random_seed(time_ms())` at the start gives a different one each time.
""", ["random_range", "random_seed"]),
    "random_range": _f("""\
- `min`, `max`: los extremos, los dos incluidos.

Devuelve un número al azar entre ellos: `random_range(1, 6)` es un dado. Con `max` menor o igual que `min`
devuelve `min`. Para rangos de más de 32768 números, no salen todos.
""", """\
- `min`, `max`: the ends, both included.

Returns a random number between them: `random_range(1, 6)` is a die. With `max` less than or equal to `min` it
returns `min`. For ranges of more than 32768 numbers, not all of them come up.
""", ["random", "random_seed"]),
    "random_seed": _f("- `seed`: la semilla.\n\nCon la misma semilla sale la misma serie de números.\n",
                      "- `seed`: the seed.\n\nThe same seed gives the same series of numbers.\n", ["random"]),
    "wait_vblank": _f("""\
Espera al siguiente retrazado vertical: 50 veces por segundo en PAL, 60 en NTSC. En el bucle de un juego, una
espera por vuelta lo hace ir al ritmo de la pantalla. Con `screen_flip` no hace falta.
""", """\
Waits for the next vertical blank: 50 times a second on PAL, 60 on NTSC. In a game loop, one wait per turn keeps it
at the screen's pace. With `screen_flip` it is not needed.
""", ["screen_flip", "time_delay"]),
    "wait_blit": _f("""\
Espera a que el blitter acabe lo que está haciendo. Los builtins de Dash ya esperan cuando hace falta; sirve para
código propio que lee memoria que el blitter está escribiendo.
""", """\
Waits for the blitter to finish what it is doing. Dash's builtins already wait when needed; it is for code of your
own reading memory the blitter is writing.
""", []),
    "arena_new": _f("""\
- `size`: cuántos bytes.

Crea una arena: un bloque de memoria que se reparte por orden, muy deprisa, y se vacía de golpe. Para muchos datos
pequeños que viven lo mismo (un fotograma, un nivel). Devuelve la arena, o 0 sin memoria. Hay que liberarla con
`arena_free`.
""", """\
- `size`: how many bytes.

Creates an arena: a block of memory handed out in order, very fast, and emptied in one go. For lots of small data
living the same time (a frame, a level). Returns the arena, or 0 without memory. It must be freed with
`arena_free`.
""", ["arena_alloc", "arena_reset", "arena_free"]),
    "arena_alloc": _f(_A_ES + """\
- `size`: cuántos bytes.

Devuelve la dirección de un trozo nuevo, o 0 si ya no cabe. Los trozos van alineados a 4 bytes. Tras un
`arena_reset` traen lo que hubiera antes: no vienen a cero. No se liberan sueltos: se vacía toda la arena.
""", _A_EN + """\
- `size`: how many bytes.

Returns the address of a new piece, or 0 if it no longer fits. Pieces are aligned to 4 bytes. After an
`arena_reset` they hold whatever was there before: they are not zeroed. They are not freed one by one: the whole
arena is emptied.
""", ["arena_reset", "arena_available"]),
    "arena_reset": _f(_A_ES + "\nLa vacía: lo pedido ya no vale y se vuelve a repartir desde el principio.\n",
                      _A_EN + "\nEmpties it: what was handed out is no longer valid and handing out starts over.\n",
                      ["arena_alloc"]),
    "arena_free": _f(_A_ES + "\nDevuelve su memoria al sistema.\n", _A_EN + "\nGives its memory back to the system.\n",
                     ["arena_new"]),
    "arena_used": _f(_A_ES + "\nDevuelve cuántos bytes se han repartido.\n", _A_EN + "\nReturns how many bytes have been handed out.\n",
                     ["arena_available"]),
    "arena_available": _f(_A_ES + "\nDevuelve cuántos bytes quedan.\n", _A_EN + "\nReturns how many bytes are left.\n",
                          ["arena_used"]),
    "refcount": _f("""\
- `obj`: una lista o un struct.

Devuelve cuántas referencias tiene: cuántas variables, campos o listas lo guardan. Para buscar fugas de memoria;
`./dash --memcheck` lo hace mejor.
""", """\
- `obj`: a list or a struct.

Returns how many references it has: how many variables, fields or lists hold it. For hunting memory leaks;
`./dash --memcheck` does it better.
""", ["retain", "release"]),
    "retain": _f("""\
- `obj`: el objeto.

Le suma una referencia, para que no se libere aunque Dash crea que nadie lo usa: por ejemplo, si solo lo guarda
código en C. Cada `retain` necesita su `release`.
""", """\
- `obj`: the object.

Adds a reference to it, so it is not freed even if Dash thinks nobody uses it: for instance, if only C code keeps
it. Each `retain` needs its `release`.
""", ["release", "refcount"]),
    "release": _f("""\
- `obj`: el objeto.

Le quita una referencia; si llega a 0, lo libera. Solo para deshacer un `retain`.
""", """\
- `obj`: the object.

Takes a reference away; if it reaches 0, it frees it. Only to undo a `retain`.
""", ["retain"]),
    "mem_trim": _f("""\
Devuelve al sistema los bloques de memoria pequeña de Dash (hasta 128 bytes) que han quedado del todo libres.
Devuelve cuántos bytes devolvió. Útil tras soltar muchos datos en un programa que sigue en marcha.
""", """\
Gives back to the system Dash's small-memory blocks (up to 128 bytes) left completely free. Returns how many bytes
it gave back. Handy after dropping lots of data in a program that keeps running.
""", ["mem_puddle"]),
    "mem_puddle": _f("""\
- `bytes`: el tamaño de cada trozo que Dash pide al sistema para su memoria, de 1 KB a 1 MB; 4 KB si no se dice.

Solo vale antes de que el programa pida memoria: la primera línea de `Main`. Trozos grandes van mejor con muchos
datos; pequeños, en un Amiga con poca memoria. Devuelve `false` si ya es tarde o el tamaño no vale.
""", """\
- `bytes`: the size of each piece Dash asks the system for its memory, 1 KB to 1 MB; 4 KB if not set.

It only works before the program asks for memory: the first line of `Main`. Large pieces suit lots of data; small
ones, an Amiga short of memory. Returns `false` if it is too late or the size is not valid.
""", ["mem_trim"]),
}
