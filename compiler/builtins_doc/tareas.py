"""Tareas, reloj, traducciones y escritorio (TASK_FUNCTIONS), primera parte: tareas, commodities, reloj y locale,
catálogos, ficheros vigilados, programas y CPU. El escritorio, los discos, la red y el ratón, en escritorio.py."""

GROUPS = {
    "TASK_FUNCTIONS": {
        "es": """\
Lo que necesitan los programas que viven en el escritorio, como Trasfondo: trabajo en otro proceso, commodities
para Exchange, el reloj y el idioma del usuario, ficheros vigilados, el fondo del escritorio, y datos del sistema
(discos, red, temperatura, CPU por tarea, ratones USB).

**Tareas.** `task_start(f, arg)` ejecuta una función en otro proceso mientras el programa sigue. La función solo
puede usar números, booleanos y builtins que no den textos ni listas (el compilador lo comprueba): los textos de
Dash no se pueden compartir entre procesos. `task_done` dice si acabó, `task_result` da lo que devolvió y
`task_free` la olvida.

**Commodities.** `cx_broker` pone el programa en Exchange, `cx_hotkey` le da una tecla rápida y `cx_wait` espera
sus órdenes sin gastar CPU.

**Traducciones.** `tr(n, "texto")` da el texto número `n` del catálogo del programa en el idioma del usuario, o el
de dentro del programa si no hay catálogo (`@catalog` y `tools/catalogo.py`).
""",
        "en": """\
What programs living on the desktop need, like Trasfondo: work in another process, commodities for Exchange, the
user's clock and language, watched files, the desktop background, and system data (disks, network, temperature, CPU
per task, USB mice).

**Tasks.** `task_start(f, arg)` runs a function in another process while the program carries on. The function may
only use numbers, booleans and builtins that give no texts or lists (the compiler checks): Dash texts cannot be
shared between processes. `task_done` says whether it finished, `task_result` gives what it returned and
`task_free` forgets it.

**Commodities.** `cx_broker` puts the program in Exchange, `cx_hotkey` gives it a hot key and `cx_wait` waits for its
commands without using CPU.

**Translations.** `tr(n, "text")` gives text number `n` of the program's catalog in the user's language, or the one
inside the program if there is no catalog (`@catalog` and `tools/catalogo.py`).
""",
        "example": "tests/test_doc_tareas.dash",
    },
}


def _f(es, en, see=()):
    return {"es": es, "en": en, "see": list(see)}


_T_ES = "- `task`: el número de `task_start`.\n"
_T_EN = "- `task`: the number from `task_start`.\n"
_I_ES = "- `i`: la tarea, desde 0, de la última muestra.\n"
_I_EN = "- `i`: the task, from 0, of the last sample.\n"
_CL_ES = "del último `clock_read`"
_CL_EN = "of the last `clock_read`"

FUNCS = {
    "task_start": _f("""\
- `func`: una función `f(arg: Int) -> Int` de Dash, que solo use `Int`, `Bool`, `Float` y builtins que no den textos
  ni listas; o una de C (`@native`, `@extern`).
- `arg`: el número que recibe.

La ejecuta en otro proceso, con 128 KB de pila y la prioridad del programa, y vuelve enseguida. Devuelve la tarea, o
0 si no pudo. El programa espera al acabar a las que sigan.
""", """\
- `func`: a Dash function `f(arg: Int) -> Int` that only uses `Int`, `Bool`, `Float` and builtins giving no texts or
  lists; or a C one (`@native`, `@extern`).
- `arg`: the number it receives.

Runs it in another process, with 128 KB of stack and the program's priority, and returns at once. Returns the task,
or 0 if it could not. The program waits for any still running when it ends.
""", ["task_done", "task_result", "task_free", "task_start_with"]),
    "task_start_with": _f("""\
- `func`, `arg`: como en `task_start`.
- `stack`: la pila en bytes; 0 = 128 KB.
- `priority`: respecto a la del programa; -1 = solo corre cuando el programa espera.
""", """\
- `func`, `arg`: as in `task_start`.
- `stack`: the stack in bytes; 0 = 128 KB.
- `priority`: relative to the program's; -1 = it only runs while the program waits.
""", ["task_start"]),
    "task_done": _f(_T_ES + "\nDevuelve `true` cuando la función ha acabado, sin esperar.\n",
                    _T_EN + "\nReturns `true` once the function has finished, without waiting.\n", ["task_result", "task_signal"]),
    "task_result": _f(_T_ES + "\nDevuelve lo que devolvió la función; si no ha acabado, espera.\n",
                      _T_EN + "\nReturns what the function returned; if it has not finished, it waits.\n", ["task_done"]),
    "task_free": _f(_T_ES + "\nLa olvida y deja libre su número; si sigue en marcha, espera a que acabe.\n",
                    _T_EN + "\nForgets it and frees its number; if it is still running, it waits for it to end.\n", ["task_start"]),
    "task_signal": _f("""\
Devuelve la señal que cada tarea envía al programa al acabar, para `mui_wait_event_signals`: así la ventana sigue
respondiendo y el programa se entera en cuanto acaba. 0 si no queda ninguna señal libre.
""", """\
Returns the signal each task sends the program when it ends, for `mui_wait_event_signals`: the window keeps
responding and the program learns as soon as it ends. 0 if no signal is free.
""", ["task_done", "mui_wait_event_signals"]),
    "break_check": _f("Devuelve `true` si llegó un Ctrl-C (`Break` en el Shell, u otra copia del programa con `single_instance`), y lo borra. Para un bucle largo que se pueda parar.\n",
                      "Returns `true` if a Ctrl-C arrived (`Break` in the Shell, or another copy of the program with `single_instance`), and clears it. For a long loop that can be stopped.\n",
                      ["single_instance"]),
    "single_instance": _f("""\
- `name`: un nombre único para el programa.

Para que solo corra una copia: si ya hay otra, le manda un Ctrl-C y devuelve `false` (la nueva debe acabar; la
vieja lo ve con `break_check`). Si no, devuelve `true`.
""", """\
- `name`: a unique name for the program.

So only one copy runs: if there is another, it sends it a Ctrl-C and returns `false` (the new one should end; the
old one sees it with `break_check`). Otherwise it returns `true`.
""", ["break_check"]),
    "tooltype": _f("""\
- `name`: el nombre: `"DELAY"`.
- `default`: lo que devuelve si no está.

Desde el Shell, el argumento `NOMBRE=valor`; desde el Workbench, el tooltype del icono del programa.
""", """\
- `name`: the name: `"DELAY"`.
- `default`: what it returns if it is not there.

From the Shell, the argument `NAME=value`; from the Workbench, the program icon's tooltype.
""", ["arg"]),
    "cx_broker": _f("""\
- `name`: el nombre en Exchange, hasta 23 letras.
- `title`, `description`: lo que enseña Exchange, hasta 39 letras cada uno.
- `priority`: la de la commodity; 0 normalmente.

Pone el programa en Exchange como commodity, con Mostrar y Ocultar, y activada. Devuelve `false` sin
`commodities.library` o si ya hay una con ese nombre.
""", """\
- `name`: the name in Exchange, up to 23 letters.
- `title`, `description`: what Exchange shows, up to 39 letters each.
- `priority`: the commodity's; usually 0.

Puts the program in Exchange as a commodity, with Show and Hide, and enabled. Returns `false` without
`commodities.library` or if one with that name exists.
""", ["cx_hotkey", "cx_wait", "cx_command"]),
    "cx_hotkey": _f("""\
- `description`: la tecla, como la escribe Exchange: `"ctrl alt t"`; `""` la quita.

La tecla rápida de la commodity: al pulsarla, `cx_command` da 6. Devuelve `false` si la descripción no vale.
""", """\
- `description`: the key, as Exchange writes it: `"ctrl alt t"`; `""` removes it.

The commodity's hot key: pressing it makes `cx_command` give 6. Returns `false` if the description is not valid.
""", ["cx_key_add", "cx_command"]),
    "cx_key_add": _f("""\
- `description`: la tecla, o un botón del ratón (`"rawmouse lalt mouse_leftpress"`); `""` la quita.
- `n`: su número, de 1 a 64.

Una tecla rápida más: `cx_command` da 100 + `n` al pulsarla, y el evento no sigue a los demás programas.
""", """\
- `description`: the key, or a mouse button (`"rawmouse lalt mouse_leftpress"`); `""` removes it.
- `n`: its number, 1 to 64.

One more hot key: `cx_command` gives 100 + `n` when pressed, and the event does not go on to other programs.
""", ["cx_hotkey"]),
    "cx_watch_add": _f("""\
- `description`: el evento, como en `cx_key_add` (`"rawmouse mouse_leftpress"`, `"rawmouse upstroke mouse_leftpress"`).
- `n`: su número, de 1 a 64 (el mismo espacio que `cx_key_add`).

Como `cx_key_add`, pero el evento sigue también a los demás programas: sirve para mirar clics y teclas sin
quitárselos (un doble clic en la barra de título de cualquier ventana, por ejemplo). `cx_command` da 100 + `n`, y
`cx_event_x`, `cx_event_y` y `cx_event_ms` dicen dónde y cuándo fue. Devuelve `false` si la descripción no vale.
""", """\
- `description`: the event, as in `cx_key_add` (`"rawmouse mouse_leftpress"`, `"rawmouse upstroke mouse_leftpress"`).
- `n`: its number, 1 to 64 (the same numbers as `cx_key_add`).

Like `cx_key_add`, but the event also goes on to the other programs: it is for watching clicks and keys without
taking them (a double click on any window's title bar, for instance). `cx_command` gives 100 + `n`, and
`cx_event_x`, `cx_event_y` and `cx_event_ms` tell where and when it happened. Returns `false` if the description is
not valid.
""", ["cx_key_add", "cx_event_x"]),
    "cx_event_x": _f("Devuelve dónde estaba el puntero (x, en la pantalla del Workbench) en el último evento que dio `cx_command`, de `cx_key_add` o `cx_watch_add`.\n",
                     "Returns where the pointer was (x, on the Workbench screen) at the last event `cx_command` gave, from `cx_key_add` or `cx_watch_add`.\n",
                     ["cx_event_y", "cx_event_ms"]),
    "cx_event_y": _f("Devuelve dónde estaba el puntero (y) en el último evento que dio `cx_command`.\n",
                     "Returns where the pointer was (y) at the last event `cx_command` gave.\n", ["cx_event_x"]),
    "cx_event_ms": _f("Devuelve cuándo fue el último evento que dio `cx_command`, en milisegundos. Solo vale la diferencia entre dos: con `wm_double_click_ms`, si dos clics son un doble clic.\n",
                      "Returns when the last event `cx_command` gave happened, in milliseconds. Only the difference between two means anything: with `wm_double_click_ms`, whether two clicks are a double click.\n",
                      ["wm_double_click_ms"]),
    "cx_command": _f("Devuelve la siguiente orden de Exchange o de una tecla rápida: 0 ninguna, 1 ocultar, 2 mostrar, 3 desactivar, 4 activar, 5 quitar, 6 la tecla rápida, 100 + n las de `cx_key_add`.\n",
                     "Returns the next command from Exchange or a hot key: 0 none, 1 hide, 2 show, 3 disable, 4 enable, 5 quit, 6 the hot key, 100 + n those of `cx_key_add`.\n",
                     ["cx_wait"]),
    "cx_wait": _f("""\
- `ms`: cuánto esperar como mucho.

Espera sin gastar CPU hasta que llegue una orden (la devuelve, como `cx_command`), un Ctrl-C (-1) o pase el tiempo
(0). Un fichero vigilado que cambia da 7.
""", """\
- `ms`: the longest to wait.

Waits without using CPU until a command arrives (it returns it, like `cx_command`), a Ctrl-C (-1) or the time runs
out (0). A watched file that changes gives 7.
""", ["cx_command", "file_notify"]),
    "tr": _f("""\
- `id`: el número del texto en el catálogo.
- `text`: el texto en el idioma del programa.

Devuelve la traducción del catálogo del programa al idioma del usuario, o `text` si no hay catálogo, no tiene ese
número o falta `locale.library`.
""", """\
- `id`: the text's number in the catalog.
- `text`: the text in the program's language.

Returns the translation from the program's catalog into the user's language, or `text` if there is no catalog, it
lacks that number or `locale.library` is missing.
""", ["catalog_open", "catalog_language"]),
    "catalog_open": _f("- `name`: el catálogo: `\"X.catalog\"`.\n- `version`: la versión; 0 cualquiera.\n\nUsa ese catálogo en vez del del programa. Devuelve `false` si no hay.\n",
                       "- `name`: the catalog: `\"X.catalog\"`.\n- `version`: the version; 0 any.\n\nUses that catalog instead of the program's. Returns `false` if there is none.\n",
                       ["tr"]),
    "catalog_language": _f("Devuelve el idioma del catálogo en uso (`\"english\"`), o `\"\"` si no hay.\n", "Returns the language of the catalog in use (`\"english\"`), or `\"\"` if none.\n", ["tr"]),
    "clock_read": _f("Toma la fecha y la hora del reloj del sistema; `clock_year`, `clock_month` y las demás dan sus partes.\n",
                     "Takes the date and time from the system clock; `clock_year`, `clock_month` and the rest give its parts.\n",
                     ["clock_year", "date_text"]),
    "clock_year": _f(f"Devuelve el año {_CL_ES}.\n", f"Returns the year {_CL_EN}.\n", ["clock_read"]),
    "clock_month": _f(f"Devuelve el mes {_CL_ES}, de 1 a 12.\n", f"Returns the month {_CL_EN}, 1 to 12.\n", ["clock_read"]),
    "clock_day": _f(f"Devuelve el día del mes {_CL_ES}, de 1 a 31.\n", f"Returns the day of the month {_CL_EN}, 1 to 31.\n", ["clock_read"]),
    "clock_weekday": _f(f"Devuelve el día de la semana {_CL_ES}: 0 domingo, 1 lunes... 6 sábado.\n", f"Returns the weekday {_CL_EN}: 0 Sunday, 1 Monday... 6 Saturday.\n", ["clock_read"]),
    "clock_hour": _f(f"Devuelve la hora {_CL_ES}, de 0 a 23.\n", f"Returns the hour {_CL_EN}, 0 to 23.\n", ["clock_read"]),
    "clock_minute": _f(f"Devuelve el minuto {_CL_ES}.\n", f"Returns the minute {_CL_EN}.\n", ["clock_read"]),
    "clock_second": _f(f"Devuelve el segundo {_CL_ES}.\n", f"Returns the second {_CL_EN}.\n", ["clock_read"]),
    "date_text": _f("""\
- `format`: el formato de `FormatDate`: `%A` el día de la semana, `%d-%m-%Y`, `%b` el mes abreviado, `%H:%M:%S`...

Devuelve la fecha y la hora de ahora así, en el idioma y el país del usuario (en inglés sin `locale.library`).
""", """\
- `format`: the `FormatDate` format: `%A` the weekday, `%d-%m-%Y`, `%b` the short month, `%H:%M:%S`...

Returns the current date and time that way, in the user's language and country (in English without
`locale.library`).
""", ["clock_read"]),
    "locale_gmt_offset": _f("Devuelve cuántos minutos va el reloj del Amiga por delante de GMT, según Locale (60 en España en invierno); 0 sin `locale.library`.\n",
                            "Returns how many minutes the Amiga's clock runs ahead of GMT, by Locale (60 in Spain in winter); 0 without `locale.library`.\n",
                            ["time_unix"]),
    "locale_decimal_point": _f("Devuelve lo que va antes de los decimales en el país del usuario: `\",\"` en España, `\".\"` en inglés.\n",
                               "Returns what goes before the decimals in the user's country: `\",\"` in Spain, `\".\"` in English.\n",
                               ["locale_group_separator"]),
    "locale_group_separator": _f("Devuelve lo que separa los miles en el país del usuario: `\".\"` en España, `\",\"` en inglés; puede ser `\"\"`.\n",
                                 "Returns the thousands separator in the user's country: `\".\"` in Spain, `\",\"` in English; it can be `\"\"`.\n",
                                 ["locale_decimal_point"]),
    "locale_date_order": _f("Devuelve el orden de la fecha corta del usuario: `\"DMY\"`, `\"MDY\"` o `\"YMD\"`.\n",
                            "Returns the order of the user's short date: `\"DMY\"`, `\"MDY\"` or `\"YMD\"`.\n", ["date_text"]),
    "program_version": _f("Devuelve el nombre y la versión de `@version` (`\"Trasfondo 0.7\"`), o `\"\"` si el programa no la tiene.\n",
                          "Returns the name and version from `@version` (`\"Trasfondo 0.7\"`), or `\"\"` if the program has none.\n", []),
    "file_notify": _f("""\
- `path`: el fichero; puede no existir aún.

Lo vigila: cada vez que cambia, `cx_wait` da 7 y `file_changed` lo dice. Devuelve su número (1 a 8), o 0 si no se
puede vigilar.
""", """\
- `path`: the file; it may not exist yet.

Watches it: each time it changes, `cx_wait` gives 7 and `file_changed` says so. Returns its number (1 to 8), or 0 if
it cannot be watched.
""", ["file_changed", "file_notify_end", "file_notify_signal"]),
    "file_changed": _f("- `n`: el número de `file_notify`.\n\nDevuelve `true` si cambió desde el último `file_changed`.\n",
                       "- `n`: the number from `file_notify`.\n\nReturns `true` if it changed since the last `file_changed`.\n", ["file_notify"]),
    "file_notify_end": _f("- `n`: el número de `file_notify`.\n\nDeja de vigilarlo. Al acabar el programa se dejan todos.\n",
                          "- `n`: the number from `file_notify`.\n\nStops watching it. All are dropped when the program ends.\n", ["file_notify"]),
    "file_notify_signal": _f("Devuelve la señal de los ficheros vigilados, para `mui_wait_event_signals`; 0 antes de un `file_notify`.\n",
                             "Returns the watched files' signal, for `mui_wait_event_signals`; 0 before a `file_notify`.\n", ["file_notify"]),
    "run_program": _f("""\
- `command`: la orden: `"SYS:Prefs/Font"`, `"\\"Work:Mi Prog\\" arg"`.

La empieza en otro proceso sin esperar, con su entrada y su salida en `NIL:`. Devuelve `false` si no pudo empezar.
Para lanzar programas desde un menú o un dock.
""", """\
- `command`: the command: `"SYS:Prefs/Font"`, `"\\"Work:My Prog\\" arg"`.

Starts it in another process without waiting, with its input and output in `NIL:`. Returns `false` if it could not
start. To launch programs from a menu or a dock.
""", ["run_command", "wb_open"]),
    "program_relaunch": _f("""\
Al acabar, el programa vuelve a empezar como empezó, desde el Workbench o desde el Shell con sus argumentos, después
de toda su limpieza. Para aplicar una actualización.
""", """\
When it ends, the program starts again the way it started, from the Workbench or the Shell with its arguments, after
all its cleanup. To apply an update.
""", ["program_exit"]),
    "dos_requesters": _f("""\
- `on`: `false` quita los requesters de "Inserta el volumen" y de errores de disco para este programa (la llamada
  falla en su lugar); `true` los vuelve a poner.

Al acabar el programa vuelven como estaban.
""", """\
- `on`: `false` removes the "Please insert volume" and disk error requesters for this program (the call fails
  instead); `true` puts them back.

They return to how they were when the program ends.
""", ["file_exists"]),
    "base64_to_file": _f("""\
- `text`: el texto en base64; los espacios y saltos de línea no cuentan.
- `file`: el fichero que se escribe.

Devuelve los bytes escritos, o -1 si el texto no es base64 (y entonces no se crea el fichero) o no se puede escribir.
""", """\
- `text`: the base64 text; spaces and line breaks do not count.
- `file`: the file to write.

Returns the bytes written, or -1 if the text is not base64 (and then no file is created) or it cannot be written.
""", []),
    "cpu_start": _f("Empieza a medir la CPU que gasta cada tarea. Devuelve `false` antes de AmigaOS 2.04 o sin el reloj fino del sistema.\n",
                    "Starts measuring the CPU each task uses. Returns `false` before AmigaOS 2.04 or without the system's fine clock.\n",
                    ["cpu_sample", "cpu_stop"]),
    "cpu_sample": _f("Toma una muestra y devuelve cuántas tareas hay, ordenadas de la que más gastó desde la muestra anterior a la que menos.\n",
                     "Takes a sample and returns how many tasks there are, sorted from the one that used most since the previous sample to the least.\n",
                     ["cpu_task_name", "cpu_task_load"]),
    "cpu_task_name": _f(_I_ES + "\nDevuelve su nombre (de un proceso de Shell, su orden).\n", _I_EN + "\nReturns its name (for a Shell process, its command).\n", ["cpu_sample"]),
    "cpu_task_load": _f(_I_ES + "\nDevuelve la CPU que gastó, en tanto por mil.\n", _I_EN + "\nReturns the CPU it used, in parts per thousand.\n", ["cpu_total"]),
    "cpu_total": _f("Devuelve la CPU de todas las tareas en la última muestra, en tanto por mil; lo demás es reposo.\n",
                    "Returns the CPU of all tasks in the last sample, in parts per thousand; the rest is idle.\n", ["cpu_sample"]),
    "cpu_stop": _f("Deja de medir. Al acabar el programa se hace solo.\n", "Stops measuring. It happens on its own when the program ends.\n", ["cpu_start"]),
}
