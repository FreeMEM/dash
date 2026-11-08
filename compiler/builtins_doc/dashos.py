"""DashOS (DASHOS_FUNCTIONS): solo con ./dash --dashos."""

GROUPS = {
    "DASHOS_FUNCTIONS": {
        "es": """\
Las llamadas al núcleo de DashOS, el sistema para ARM que se hace con Dash. Solo existen al compilar con
`./dash --dashos`; en el Amiga son un error de compilación.

**Llaves.** Todo lo del sistema (un canal, un temporizador, un objeto de memoria, un proceso) se maneja con una
llave: un número con derechos (1 leer, 2 escribir, 4 pasar). Una llave se puede copiar con menos derechos
(`handle_copy`), pasar a otro programa por un canal (`channel_pass`) o retirar después (`handle_revocable`). Quien
no tiene la llave no puede tocar la cosa.

**Canales.** `channel_create` da un lado y `channel_other` el otro: lo que se manda por uno se recibe por el otro,
hasta 256 bytes por mensaje y hasta 8 llaves.

**Procesos y grupos.** `process_start` lanza un programa con las llaves que se le dan (`process_give`); un grupo
(`group_create`) les pone un presupuesto de memoria y se puede acabar entero de una vez.

Los errores son números negativos; `dashos_error_text` los explica.
""",
        "en": """\
The calls to the kernel of DashOS, the ARM system being built with Dash. They only exist when compiling with
`./dash --dashos`; on the Amiga they are a compile error.

**Handles.** Everything in the system (a channel, a timer, a memory object, a process) is handled with a handle: a
number with rights (1 read, 2 write, 4 pass). A handle can be copied with fewer rights (`handle_copy`), passed to
another program over a channel (`channel_pass`) or withdrawn later (`handle_revocable`). Whoever lacks the handle
cannot touch the thing.

**Channels.** `channel_create` gives one end and `channel_other` the other: what is sent on one is received on the
other, up to 256 bytes per message and up to 8 handles.

**Processes and groups.** `process_start` launches a program with the handles it is given (`process_give`); a group
(`group_create`) gives them a memory budget and can be ended all at once.

Errors are negative numbers; `dashos_error_text` explains them.
""",
        "example": "tests/dashos/test_dashos_channels.dash",
    },
}


def _f(es, en, see=()):
    return {"es": es, "en": en, "see": list(see)}


_H_ES = "- `handle`: la llave.\n"
_H_EN = "- `handle`: the handle.\n"
_ERR_ES = "0, o un error negativo."
_ERR_EN = "0, or a negative error."

FUNCS = {
    "channel_create": _f("Crea un canal y devuelve la llave de uno de sus lados (el otro, `channel_other`), o un error negativo.\n",
                         "Creates a channel and returns the handle of one of its ends (the other, `channel_other`), or a negative error.\n",
                         ["channel_other", "channel_send"]),
    "channel_other": _f("Devuelve la llave del otro lado del último `channel_create`.\n", "Returns the handle of the other end of the last `channel_create`.\n", ["channel_create"]),
    "channel_pass": _f(_H_ES + f"\nLa mete en el siguiente `channel_send`: sale de este programa (hace falta el derecho de pasar). Hasta 8 por mensaje. Devuelve 0, o -1 si ya hay 8.\n",
                       _H_EN + f"\nPuts it in the next `channel_send`: it leaves this program (the pass right is needed). Up to 8 per message. Returns 0, or -1 if there are 8 already.\n",
                       ["channel_send", "channel_handles"]),
    "channel_send": _f(_H_ES + f"- `text`: hasta 256 bytes.\n\nLo manda al otro lado sin esperar. Devuelve {_ERR_ES}\n",
                       _H_EN + f"- `text`: up to 256 bytes.\n\nSends it to the other end without waiting. Returns {_ERR_EN}\n", ["channel_receive"]),
    "channel_send_buffer": _f(_H_ES + f"- `buffer`, `length`: hasta 256 bytes.\n\nComo `channel_send`, con datos binarios. Devuelve {_ERR_ES}\n",
                              _H_EN + f"- `buffer`, `length`: up to 256 bytes.\n\nLike `channel_send`, with binary data. Returns {_ERR_EN}\n", ["channel_send"]),
    "channel_receive": _f(_H_ES + "\nEspera el siguiente mensaje y lo devuelve como texto, o `nil` si hubo un error (`channel_error`). Sus llaves, con `channel_handles`; quién lo mandó, con `channel_mark`.\n",
                          _H_EN + "\nWaits for the next message and returns it as a text, or `nil` on an error (`channel_error`). Its handles, with `channel_handles`; who sent it, with `channel_mark`.\n",
                          ["channel_handles", "channel_mark", "channel_error"]),
    "channel_receive_buffer": _f(_H_ES + "- `buffer`, `max`: dónde y cuánto cabe (con 256 basta).\n\nEspera el siguiente mensaje y lo copia. Devuelve su largo o un error negativo.\n",
                                 _H_EN + "- `buffer`, `max`: where and how much fits (256 is enough).\n\nWaits for the next message and copies it. Returns its length or a negative error.\n",
                                 ["channel_receive"]),
    "channel_handles": _f("Devuelve cuántas llaves llegaron con el último mensaje recibido.\n", "Returns how many handles came with the last message received.\n", ["channel_handle"]),
    "channel_handle": _f("- `i`: la llave, desde 0.\n\nDevuelve esa llave del último mensaje recibido; 0 si no hay.\n", "- `i`: the handle, from 0.\n\nReturns that handle of the last message received; 0 if none.\n", ["channel_handles"]),
    "channel_mark": _f("Devuelve la marca de la llave con la que se escribió el último mensaje (`handle_copy`): quién lo mandó. 0 sin marca o del núcleo (los temporizadores).\n",
                       "Returns the mark of the handle the last message was written with (`handle_copy`): who sent it. 0 without a mark or from the kernel (timers).\n",
                       ["handle_copy"]),
    "channel_error": _f("Devuelve el error del último `channel_receive`: 0 ninguno, -4 el otro lado se cerró.\n", "Returns the last `channel_receive` error: 0 none, -4 the other end closed.\n", ["channel_receive"]),
    "handle_copy": _f(_H_ES + """\
- `rights`: los derechos de la copia, iguales o menos: 1 leer, 2 escribir, 4 pasar, sumados.
- `mark`: una marca para la copia si la llave no tenía (0: la suya).

Devuelve la llave nueva o un error negativo.
""", _H_EN + """\
- `rights`: the copy's rights, the same or fewer: 1 read, 2 write, 4 pass, added up.
- `mark`: a mark for the copy if the handle had none (0: its own).

Returns the new handle or a negative error.
""", ["channel_mark", "handle_close"]),
    "handle_close": _f(_H_ES + f"\nLa cierra; la última llave de un lado de un canal cierra ese lado. Devuelve {_ERR_ES}\n",
                       _H_EN + f"\nCloses it; the last handle of a channel end closes that end. Returns {_ERR_EN}\n", ["handle_copy"]),
    "handle_revocable": _f(_H_ES + "\nDevuelve una copia que se puede retirar después (su revocador, `handle_revoker`), o un error negativo.\n",
                           _H_EN + "\nReturns a copy that can be withdrawn later (its revoker, `handle_revoker`), or a negative error.\n",
                           ["handle_revoker", "handle_revoke"]),
    "handle_revoker": _f("Devuelve el revocador del último `handle_revocable`.\n", "Returns the revoker of the last `handle_revocable`.\n", ["handle_revoke"]),
    "handle_revoke": _f(f"- `revoker`: el revocador.\n\nRetira la llave y todas las copias hechas de ella: desde entonces no valen. Devuelve {_ERR_ES}\n",
                        f"- `revoker`: the revoker.\n\nWithdraws the handle and every copy made from it: from then on they are not valid. Returns {_ERR_EN}\n",
                        ["handle_revocable"]),
    "timer_create": _f(_H_ES.replace("la llave", "un lado de un canal") + """\
- `first_ms`: cuándo llega el primer mensaje.
- `period_ms`: cada cuánto los siguientes; 0 una sola vez. En pasos de 10 ms.

Un temporizador que manda mensajes al otro lado del canal; se para al cerrar su llave. Devuelve la llave o un error
negativo.
""", _H_EN.replace("the handle", "one end of a channel") + """\
- `first_ms`: when the first message arrives.
- `period_ms`: how often the next ones; 0 just once. In steps of 10 ms.

A timer that sends messages to the other end of the channel; it stops when its handle closes. Returns the handle or a
negative error.
""", ["channel_receive"]),
    "memory_create": _f("- `size`: hasta 4 MB.\n\nUn objeto de memoria a cero, que se puede pasar a otro programa (memoria compartida). Devuelve su llave o un error negativo.\n",
                        "- `size`: up to 4 MB.\n\nA zeroed memory object that can be passed to another program (shared memory). Returns its handle or a negative error.\n",
                        ["memory_map"]),
    "memory_map": _f(_H_ES + "- `writable`: `true` para escribir.\n\nLo pone en la memoria de este programa y devuelve un búfer para los `buffer_*`, o 0.\n",
                     _H_EN + "- `writable`: `true` to write.\n\nMaps it into this program's memory and returns a buffer for the `buffer_*` functions, or 0.\n",
                     ["memory_unmap", "buffer_get_byte"]),
    "memory_unmap": _f(f"- `buffer`: lo que dio `memory_map`.\n\nLo quita; el objeto sigue mientras tenga llaves. Devuelve {_ERR_ES}\n",
                       f"- `buffer`: what `memory_map` gave.\n\nUnmaps it; the object lives on while it has handles. Returns {_ERR_EN}\n", ["memory_map"]),
    "process_give": _f(_H_ES + "\nUna llave para el siguiente `process_start`: el programa nuevo las recibe como llaves 1, 2... en este orden. Hasta 16. Devuelve 0, o -1 si ya hay 16.\n",
                       _H_EN + "\nA handle for the next `process_start`: the new program gets them as handles 1, 2... in this order. Up to 16. Returns 0, or -1 if there are 16 already.\n",
                       ["process_start"]),
    "process_group": _f("- `group`: el grupo de los siguientes procesos; 0 el de este programa.\n", "- `group`: the group of the following processes; 0 this program's.\n", ["group_create"]),
    "process_start": _f("- `memory`: un objeto de memoria con el programa (ELF).\n- `size`: sus primeros bytes que lo forman.\n\nLo lanza con las llaves de `process_give`. Devuelve el proceso o un error negativo.\n",
                        "- `memory`: a memory object holding the program (ELF).\n- `size`: its first bytes making it up.\n\nLaunches it with the `process_give` handles. Returns the process or a negative error.\n",
                        ["process_wait", "process_start_buffer"]),
    "process_start_buffer": _f("- `buffer`, `length`: el ELF, hasta 4 MB.\n\nComo `process_start`, con el programa en un búfer.\n",
                               "- `buffer`, `length`: the ELF, up to 4 MB.\n\nLike `process_start`, with the program in a buffer.\n", ["process_start"]),
    "process_kill": _f(f"- `process`: el proceso.\n\nLo acaba. Devuelve {_ERR_ES}\n", f"- `process`: the process.\n\nEnds it. Returns {_ERR_EN}\n", ["process_wait"]),
    "process_wait": _f("- `process`: el proceso.\n\nEspera a que acabe y devuelve su código de salida (cómo acabó, `process_end`), o un error negativo.\n",
                       "- `process`: the process.\n\nWaits for it to end and returns its exit code (how it ended, `process_end`), or a negative error.\n",
                       ["process_end"]),
    "process_end": _f("Devuelve cómo acabó el proceso del último `process_wait`: 0 salió, 1 lo mataron, 2 falló.\n",
                      "Returns how the process of the last `process_wait` ended: 0 exited, 1 killed, 2 crashed.\n", ["process_wait"]),
    "group_create": _f("- `bytes`: el presupuesto, sacado del de este programa.\n\nUn grupo: lo que crean sus procesos se cobra ahí. Devuelve el grupo o un error negativo.\n",
                       "- `bytes`: the budget, taken from this program's.\n\nA group: what its processes create is charged there. Returns the group or a negative error.\n",
                       ["process_group", "group_kill"]),
    "group_kill": _f(f"- `group`: el grupo.\n\nAcaba todos sus procesos y suelta todo lo que tenía. Devuelve {_ERR_ES}\n",
                     f"- `group`: the group.\n\nEnds all its processes and releases everything it held. Returns {_ERR_EN}\n", ["group_create"]),
    "group_used": _f("- `group`: el grupo; 0 el de este programa.\n\nDevuelve los bytes que lleva gastados, o un error negativo.\n",
                     "- `group`: the group; 0 this program's.\n\nReturns the bytes it has spent, or a negative error.\n", ["group_limit"]),
    "group_limit": _f("- `group`: el grupo; 0 el de este programa.\n\nDevuelve su presupuesto en bytes, o un error negativo.\n",
                      "- `group`: the group; 0 this program's.\n\nReturns its budget in bytes, or a negative error.\n", ["group_used"]),
    "dashos_error_text": _f("- `code`: un error negativo de DashOS.\n\nDevuelve qué quiere decir, como texto.\n", "- `code`: a negative DashOS error.\n\nReturns what it means, as a text.\n", []),
}
