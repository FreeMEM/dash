"""Sistema y programa (SYSPROG_FUNCTIONS)."""

GROUPS = {
    "SYSPROG_FUNCTIONS": {
        "es": """\
El programa y el sistema que lo rodea: la hora, el procesador, las librerías, ejecutar órdenes, variables de
entorno, ARexx y listas de lo que hay en marcha (puertos, tareas, asignaciones).

**Ejecutar órdenes.** `run_command` ejecuta y espera, con la salida de la orden en la del programa. `run_capture`
la recoge en un texto. `run_start` hace lo mismo sin esperar, para que la ventana siga respondiendo; después
`run_ready` y `run_finish`.

**ARexx.** `rexx_send` manda una orden al puerto de otro programa y espera su respuesta. Para que otros programas
manden órdenes al propio: `rexx_port`, `rexx_get` y `rexx_reply` (con MUI, `mui_app_rexx` es más cómodo).

**Listas.** `ports_read`, `tasks_read` y `assigns_read` leen una foto de lo que hay ahora y devuelven cuántos;
las funciones de cada uno los dan por número, desde 0, hasta la siguiente lectura.
""",
        "en": """\
The program and the system around it: the time, the processor, libraries, running commands, environment variables,
ARexx and lists of what is running (ports, tasks, assigns).

**Running commands.** `run_command` runs and waits, with the command's output in the program's. `run_capture`
collects it in a text. `run_start` does the same without waiting, so the window keeps responding; then `run_ready`
and `run_finish`.

**ARexx.** `rexx_send` sends a command to another program's port and waits for its reply. For other programs to
send commands to yours: `rexx_port`, `rexx_get` and `rexx_reply` (with MUI, `mui_app_rexx` is easier).

**Lists.** `ports_read`, `tasks_read` and `assigns_read` take a snapshot of what is there now and return how many;
each one's functions give them by number, from 0, until the next read.
""",
        "example": "tests/test_doc_sysprog.dash",
    },
}


def _f(es, en, see=()):
    return {"es": es, "en": en, "see": list(see)}


_I_ES = "- `i`: el número, desde 0.\n"
_I_EN = "- `i`: the number, from 0.\n"
_R_ES = "- `run`: el número de `run_start`.\n"
_R_EN = "- `run`: the number from `run_start`.\n"

FUNCS = {
    "time_unix": _f("Devuelve la hora del reloj del sistema en segundos desde el 1 de enero de 1970, como las fechas de Internet.\n",
                    "Returns the system clock's time in seconds since 1 January 1970, like Internet dates.\n", ["clock_days", "dir_entry_date"]),
    "clock_days": _f("Devuelve los días desde el 1 de enero de 1978, la fecha cero del Amiga, según el reloj del sistema.\n",
                     "Returns the days since 1 January 1978, the Amiga's day zero, by the system clock.\n", ["time_unix"]),
    "mem_largest": _f("Devuelve el bloque de memoria libre más grande, chip o fast. Lo más grande que se puede pedir de una vez.\n",
                      "Returns the largest free memory block, chip or fast. The biggest thing that can be asked for in one go.\n",
                      ["mem_total"]),
    "program_exit": _f("""\
- `rc`: el código de retorno: 0 bien, 5 aviso, 10 error, 20 fallo.

Acaba el programa ya, desde cualquier sitio, con la limpieza de siempre: cierra ventanas y ficheros y devuelve la
memoria. Un script del Shell puede mirar el código con `If WARN` o `If ERROR`.
""", """\
- `rc`: the return code: 0 fine, 5 warning, 10 error, 20 failure.

Ends the program now, from anywhere, with the usual cleanup: it closes windows and files and gives memory back. A
Shell script can check the code with `If WARN` or `If ERROR`.
""", []),
    "run_command": _f("""\
- `command`: la orden, como en el Shell: `"Copy RAM:a TO RAM:b"`.

La ejecuta y espera a que acabe; lo que escriba sale en la salida del programa. Devuelve su código de retorno, o -1
si no pudo empezar.
""", """\
- `command`: the command, as in the Shell: `"Copy RAM:a TO RAM:b"`.

Runs it and waits for it to finish; what it writes goes to the program's output. Returns its return code, or -1 if
it could not start.
""", ["run_capture", "run_start"]),
    "wb_open": _f("""\
- `path`: un cajón, un programa o un documento.

Lo abre como un doble clic en su icono: un documento se abre con su programa. Necesita AmigaOS 3.5 o más. Devuelve
`false` si no pudo.
""", """\
- `path`: a drawer, a program or a document.

Opens it like a double click on its icon: a document opens with its program. It needs AmigaOS 3.5 or later. Returns
`false` if it could not.
""", ["run_command"]),
    "program_path": _f("Devuelve la ruta entera del programa (`\"Work:Juegos/Nave\"`), arranque desde el Shell o desde el Workbench.\n",
                       "Returns the program's full path (`\"Work:Games/Ship\"`), started from the Shell or the Workbench.\n", []),
    "locale_language": _f("Devuelve el primer idioma de las preferencias de Locale del usuario (`\"español\"`), o `\"\"` si no hay.\n",
                          "Returns the first language in the user's Locale preferences (`\"español\"`), or `\"\"` if none.\n", []),
    "cpu_model": _f("Devuelve el procesador: 68000, 68010, 68020, 68030, 68040 o 68060.\n",
                    "Returns the processor: 68000, 68010, 68020, 68030, 68040 or 68060.\n", ["fpu_model"]),
    "fpu_model": _f("Devuelve el coprocesador matemático: 68881, 68882, 68040 o 68060 (el del procesador); 0 si no hay.\n",
                    "Returns the maths coprocessor: 68881, 68882, 68040 or 68060 (the processor's own); 0 if none.\n", ["cpu_model"]),
    "library_version": _f("""\
- `name`: el nombre de la librería: `"muimaster.library"`.

Devuelve su versión, cargándola del disco si no está en memoria, o -1 si no está instalada. Para avisar antes de
usar algo que necesita una versión concreta.
""", """\
- `name`: the library's name: `"muimaster.library"`.

Returns its version, loading it from disk if it is not in memory, or -1 if it is not installed. To warn before using
something that needs a given version.
""", ["library_revision"]),
    "library_revision": _f("- `name`: el nombre de la librería.\n\nDevuelve su revisión (el 3 de 47.3), o -1.\n",
                           "- `name`: the library's name.\n\nReturns its revision (the 3 in 47.3), or -1.\n", ["library_version"]),
    "resident_version": _f("- `name`: el nombre de un módulo residente.\n\nDevuelve su versión, o -1. `resident_version(\"MorphOS\")` mayor que 0 dice que el programa corre en MorphOS.\n",
                           "- `name`: a resident module's name.\n\nReturns its version, or -1. `resident_version(\"MorphOS\")` above 0 says the program runs on MorphOS.\n",
                           ["library_version"]),
    "task_priority": _f("""\
- `n`: la prioridad nueva, de -128 a 127; el Shell da 0.

Cambia la prioridad del programa y devuelve la que tenía. Con -1, un trabajo largo deja ir fluido a lo demás.
""", """\
- `n`: the new priority, -128 to 127; the Shell gives 0.

Changes the program's priority and returns the old one. At -1, a long job lets everything else run smoothly.
""", []),
    "build_date": _f("Devuelve la fecha en que se compiló el programa: `\"2026-10-28\"`.\n", "Returns the date the program was compiled: `\"2026-10-28\"`.\n", ["build_time"]),
    "build_time": _f("Devuelve la hora en que se compiló: `\"20:45:10\"`.\n", "Returns the time it was compiled: `\"20:45:10\"`.\n", ["build_date"]),
    "console_flush": _f("Saca ya lo que `Print` dejó en el búfer de la salida: para una línea de progreso que se escribe a trozos.\n",
                        "Pushes out now what `Print` left in the output buffer: for a progress line written in pieces.\n", ["console_write"]),
    "run_capture": _f("""\
- `command`: la orden.
- `timeout_ms`: tiempo máximo; al pasarlo la orden recibe Ctrl-C (y otro cada segundo hasta que acaba). 0 = sin
  tope.

La ejecuta, espera y devuelve todo lo que escribió. Su código de retorno, en `run_rc()`. Solo la salida normal:
AmigaOS no da un canal de errores aparte.
""", """\
- `command`: the command.
- `timeout_ms`: the time limit; past it the command gets Ctrl-C (and another every second until it ends). 0 = no
  limit.

Runs it, waits and returns everything it wrote. Its return code is in `run_rc()`. Only the normal output: AmigaOS
gives no separate error channel.
""", ["run_rc", "run_start"]),
    "run_start": _f("""\
- `command`, `timeout_ms`: como en `run_capture`.

La empieza sin esperar. Devuelve un número para `run_ready`, `run_break` y `run_finish`, o 0 si no pudo empezar.
Al acabar el programa se espera a las que sigan.
""", """\
- `command`, `timeout_ms`: as in `run_capture`.

Starts it without waiting. Returns a number for `run_ready`, `run_break` and `run_finish`, or 0 if it could not
start. When the program ends it waits for any still running.
""", ["run_ready", "run_finish"]),
    "run_ready": _f(_R_ES + "\nDevuelve `true` cuando ha acabado, sin esperar.\n", _R_EN + "\nReturns `true` once it has finished, without waiting.\n",
                    ["run_finish"]),
    "run_break": _f(_R_ES + "\nLe manda Ctrl-C, y otro cada segundo hasta que acaba.\n", _R_EN + "\nSends it Ctrl-C, and another every second until it ends.\n",
                    ["run_start"]),
    "run_finish": _f(_R_ES + "\nDevuelve lo que escribió, como `run_capture`; si sigue en marcha, espera. Hay que llamarla siempre: libera su número.\n",
                     _R_EN + "\nReturns what it wrote, like `run_capture`; if it is still running, it waits. Always call it: it frees its number.\n",
                     ["run_rc"]),
    "run_rc": _f("Devuelve el código de retorno del último `run_capture` o `run_finish`; -1 si no pudo empezar, -2 si se le acabó el tiempo.\n",
                 "Returns the return code of the last `run_capture` or `run_finish`; -1 if it could not start, -2 if it ran out of time.\n",
                 ["run_capture"]),
    "env_get": _f("- `name`: el nombre: `\"Language\"`, `\"Forja/ejecutables\"`.\n\nDevuelve su valor, de la Shell del programa o de `ENV:`, hasta el primer fin de línea; `\"\"` si no existe.\n",
                  "- `name`: the name: `\"Language\"`, `\"Forja/ejecutables\"`.\n\nReturns its value, from the program's Shell or from `ENV:`, up to the first line end; `\"\"` if it does not exist.\n",
                  ["env_set"]),
    "env_set": _f("""\
- `name`: el nombre; con `/` va en un cajón de `ENV:`.
- `value`: el valor.
- `save`: `true` lo guarda también en `ENVARC:`, para que siga tras reiniciar.

Devuelve `false` si no pudo.
""", """\
- `name`: the name; with `/` it goes in a drawer of `ENV:`.
- `value`: the value.
- `save`: `true` also stores it in `ENVARC:`, so it survives a reboot.

Returns `false` if it could not.
""", ["env_get"]),
    "rexx_send": _f("""\
- `port`: el puerto ARexx de otro programa (`"MULTIVIEW.1"`); `"REXX"` ejecuta un script.
- `command`: la orden.

La manda y espera la respuesta. Devuelve su RESULT (`""` si no hay); el RC, en `rexx_rc()`. No al puerto del propio
programa: se esperaría a sí mismo.
""", """\
- `port`: another program's ARexx port (`"MULTIVIEW.1"`); `"REXX"` runs a script.
- `command`: the command.

Sends it and waits for the reply. Returns its RESULT (`""` if none); the RC goes to `rexx_rc()`. Not to the
program's own port: it would wait for itself.
""", ["rexx_rc", "ports_read"]),
    "rexx_rc": _f("Devuelve el RC del último `rexx_send`: 0 bien, 5, 10, 20 los del programa; -1 si no existe el puerto, -2 sin `rexxsyslib.library`.\n",
                  "Returns the RC of the last `rexx_send`: 0 fine, 5, 10, 20 the program's; -1 if the port does not exist, -2 without `rexxsyslib.library`.\n",
                  ["rexx_send"]),
    "rexx_port": _f("""\
- `name`: el nombre del puerto, en mayúsculas.

Abre el puerto ARexx del programa: desde ARexx, `ADDRESS NOMBRE`. Devuelve `false` si ese nombre ya existe o falta
`rexxsyslib.library`. Las órdenes se leen con `rexx_get`.
""", """\
- `name`: the port's name, in capitals.

Opens the program's ARexx port: from ARexx, `ADDRESS NAME`. Returns `false` if that name exists already or
`rexxsyslib.library` is missing. Commands are read with `rexx_get`.
""", ["rexx_get", "rexx_reply"]),
    "rexx_get": _f("""\
Devuelve la siguiente orden que llegó al puerto de `rexx_port`, o `""` si ninguna. No espera. Quien la mandó espera
la respuesta: `rexx_reply` (si no, el siguiente `rexx_get` la contesta con RC 0).
""", """\
Returns the next command that reached the `rexx_port` port, or `""` if none. It does not wait. Whoever sent it waits
for the reply: `rexx_reply` (otherwise the next `rexx_get` answers it with RC 0).
""", ["rexx_reply"]),
    "rexx_reply": _f("""\
- `rc`: 0 bien, 5 aviso, 10 error, 20 fallo.
- `result`: con `rc` 0, el RESULT que recibe quien la mandó; `""` ninguno.
""", """\
- `rc`: 0 fine, 5 warning, 10 error, 20 failure.
- `result`: with `rc` 0, the RESULT the sender gets; `""` none.
""", ["rexx_get"]),
    "notify": _f("""\
- `title`: el título del aviso.
- `text`: el texto.

Manda un aviso al escritorio, con el nombre del programa: a la barra de Trasfondo si está en marcha; si no, a su
lista, que enseña al arrancar. Devuelve `false` si no llegó a ninguno de los dos.
""", """\
- `title`: the notice's title.
- `text`: the text.

Sends a notice to the desktop, with the program's name: to Trasfondo's bar if it is running; otherwise to its list,
shown when it starts. Returns `false` if it reached neither.
""", []),
    "ports_read": _f("Lee los nombres de los puertos públicos abiertos (los de ARexx entre ellos) y devuelve cuántos hay.\n",
                     "Reads the names of the open public ports (ARexx ones among them) and returns how many there are.\n", ["port_name"]),
    "port_name": _f(_I_ES + "\nDevuelve el nombre de ese puerto del último `ports_read`.\n", _I_EN + "\nReturns that port's name from the last `ports_read`.\n",
                    ["ports_read"]),
    "tasks_read": _f("Lee las tareas y procesos del sistema (el primero, el propio programa) y devuelve cuántos hay.\n",
                     "Reads the system's tasks and processes (the first, the program itself) and returns how many there are.\n",
                     ["task_entry_name"]),
    "task_entry_name": _f(_I_ES + "\nDevuelve su nombre: `\"Shell Process\"`, `\"input.device\"`.\n", _I_EN + "\nReturns its name: `\"Shell Process\"`, `\"input.device\"`.\n",
                          ["tasks_read"]),
    "task_entry_command": _f(_I_ES + "\nDevuelve la orden que ejecuta un proceso de Shell; `\"\"` si ninguna.\n",
                             _I_EN + "\nReturns the command a Shell process is running; `\"\"` if none.\n", ["tasks_read"]),
    "task_entry_state": _f(_I_ES + "\nDevuelve su estado: `\"running\"` (el programa), `\"ready\"` o `\"waiting\"`.\n",
                           _I_EN + "\nReturns its state: `\"running\"` (the program), `\"ready\"` or `\"waiting\"`.\n", ["tasks_read"]),
    "task_entry_priority": _f(_I_ES + "\nDevuelve su prioridad.\n", _I_EN + "\nReturns its priority.\n", ["tasks_read"]),
    "task_entry_cli": _f(_I_ES + "\nDevuelve su número de Shell (el que da `Status`, para `Break`); 0 si no es un proceso de Shell.\n",
                         _I_EN + "\nReturns its Shell number (the one `Status` gives, for `Break`); 0 if it is not a Shell process.\n", ["tasks_read"]),
    "assigns_read": _f("Lee las asignaciones (`C:`, `LIBS:`, las de `Assign`) y devuelve cuántas hay.\n",
                       "Reads the assigns (`C:`, `LIBS:`, those from `Assign`) and returns how many there are.\n", ["assign_name"]),
    "assign_name": _f(_I_ES + "\nDevuelve su nombre, sin los dos puntos.\n", _I_EN + "\nReturns its name, without the colon.\n", ["assign_path"]),
    "assign_path": _f(_I_ES + "\nDevuelve adónde apunta: un cajón (`\"Workbench:C\"`), varios separados por `;`, o el nombre que buscará una asignación diferida.\n",
                      _I_EN + "\nReturns where it points: a drawer (`\"Workbench:C\"`), several separated by `;`, or the name a deferred assign will look for.\n",
                      ["assign_name"]),
}
