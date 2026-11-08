"""Depurador (DEBUGGER_FUNCTIONS)."""

GROUPS = {
    "DEBUGGER_FUNCTIONS": {
        "es": """\
Para escribir un depurador en Dash, como el de Forja: cargar otro programa compilado con `dash --debug`, ponerle
puntos de parada, ir línea a línea y mirar sus variables.

**El flujo:**

1. `dbg_start(programa, argumentos)`: lo carga en un proceso propio, en pausa antes de su primera línea.
2. `dbg_break(fichero, línea)`: los puntos de parada.
3. `dbg_continue()`, `dbg_step()`, `dbg_next()` o `dbg_out()`: lo ponen en marcha, y `dbg_wait` espera a que pare
   o acabe (con MUI, `dbg_signal` con `mui_wait_event_signals`).
4. Parado: `dbg_file`, `dbg_line` y `dbg_function` dicen dónde; `dbg_frames` y `dbg_frame_*`, la pila de llamadas;
   `dbg_vars`, `dbg_var_*` y `dbg_value`, las variables.
5. Al acabar (`dbg_state()` 4), `dbg_rc` y `dbg_output`.

Solo hay un programa depurado a la vez. Las llamadas se numeran desde la de la parada: 0 donde paró, 1 la que la
llamó...
""",
        "en": """\
For writing a debugger in Dash, like Forja's: load another program compiled with `dash --debug`, set breakpoints on
it, go line by line and look at its variables.

**The flow:**

1. `dbg_start(program, arguments)`: loads it in a process of its own, paused before its first line.
2. `dbg_break(file, line)`: the breakpoints.
3. `dbg_continue()`, `dbg_step()`, `dbg_next()` or `dbg_out()`: set it going, and `dbg_wait` waits for it to stop
   or end (with MUI, `dbg_signal` with `mui_wait_event_signals`).
4. Stopped: `dbg_file`, `dbg_line` and `dbg_function` say where; `dbg_frames` and `dbg_frame_*`, the call stack;
   `dbg_vars`, `dbg_var_*` and `dbg_value`, the variables.
5. When it ends (`dbg_state()` 4), `dbg_rc` and `dbg_output`.

There is one debugged program at a time. Calls are numbered from the stopping point: 0 where it stopped, 1 its
caller...
""",
        "example": "dashc/tests/depurar/basico.dash",
    },
}


def _f(es, en, see=()):
    return {"es": es, "en": en, "see": list(see)}


_FR_ES = "- `i`: la llamada: 0 donde paró, 1 la que la llamó...\n"
_FR_EN = "- `i`: the call: 0 where it stopped, 1 its caller...\n"
_GO_ES = "Devuelve `false` si no hay un programa en pausa o parado. No espera: `dbg_wait`.\n"
_GO_EN = "Returns `false` if there is no paused or stopped program. It does not wait: `dbg_wait`.\n"

FUNCS = {
    "dbg_start": _f("""\
- `program`: el ejecutable, compilado con `dash --debug`.
- `args`: sus argumentos, como en el Shell.

Lo carga y lo deja en pausa antes de su primera línea, para poner los puntos de parada. Devuelve `false` si no
pudo; `dbg_error` dice por qué (un programa sin `--debug`, por ejemplo).
""", """\
- `program`: the executable, compiled with `dash --debug`.
- `args`: its arguments, as in the Shell.

Loads it and leaves it paused before its first line, to set the breakpoints. Returns `false` if it could not;
`dbg_error` says why (a program without `--debug`, for instance).
""", ["dbg_break", "dbg_continue", "dbg_error"]),
    "dbg_error": _f("Devuelve por qué falló el último `dbg_start`.\n", "Returns why the last `dbg_start` failed.\n", ["dbg_start"]),
    "dbg_state": _f("Devuelve cómo está el programa: 0 no hay ninguno, 1 en pausa antes de empezar, 2 corriendo, 3 parado en una línea, 4 acabado.\n",
                    "Returns the program's state: 0 none, 1 paused before starting, 2 running, 3 stopped at a line, 4 finished.\n",
                    ["dbg_wait"]),
    "dbg_signal": _f("Devuelve la señal que recibe el depurador cuando el programa para o acaba, para `mui_wait_event_signals`.\n",
                     "Returns the signal the debugger gets when the program stops or ends, for `mui_wait_event_signals`.\n",
                     ["dbg_wait", "mui_wait_event_signals"]),
    "dbg_wait": _f("- `ms`: cuánto esperar como mucho; 0 sin tope.\n\nEspera a que el programa pare o acabe y devuelve su estado, como `dbg_state`.\n",
                   "- `ms`: the longest to wait; 0 no limit.\n\nWaits for the program to stop or end and returns its state, like `dbg_state`.\n",
                   ["dbg_state"]),
    "dbg_break": _f("""\
- `file`: el fichero, por el final de su ruta: `"juego.dash"`.
- `line`: la línea.

Pone un punto de parada. Devuelve `false` si esa línea no tiene código (un comentario, una línea vacía).
""", """\
- `file`: the file, by the end of its path: `"game.dash"`.
- `line`: the line.

Sets a breakpoint. Returns `false` if that line has no code (a comment, an empty line).
""", ["dbg_unbreak", "dbg_continue"]),
    "dbg_unbreak": _f("- `file`, `line`: como en `dbg_break`.\n\nQuita ese punto de parada.\n", "- `file`, `line`: as in `dbg_break`.\n\nRemoves that breakpoint.\n", ["dbg_break"]),
    "dbg_continue": _f("Sigue, desde el principio o desde una parada, hasta un punto de parada o el final. " + _GO_ES,
                       "Carries on, from the start or a stop, until a breakpoint or the end. " + _GO_EN, ["dbg_step", "dbg_wait"]),
    "dbg_step": _f("Sigue hasta la línea siguiente, entrando en las funciones a las que llama. " + _GO_ES,
                   "Carries on to the next line, stepping into the functions it calls. " + _GO_EN, ["dbg_next", "dbg_out"]),
    "dbg_next": _f("Sigue hasta la línea siguiente de esta función, sin entrar en las que llama (o hasta la que la llamó si acaba). " + _GO_ES,
                   "Carries on to the next line of this function, without stepping into those it calls (or to its caller if it ends). " + _GO_EN,
                   ["dbg_step"]),
    "dbg_out": _f("Sigue hasta que la función vuelve: la línea siguiente de la que la llamó. " + _GO_ES,
                  "Carries on until the function returns: the next line of its caller. " + _GO_EN, ["dbg_step"]),
    "dbg_pause": _f("Para el programa en marcha en la siguiente línea que ejecute. Devuelve `false` si no estaba corriendo.\n",
                    "Stops the running program at the next line it executes. Returns `false` if it was not running.\n", ["dbg_continue"]),
    "dbg_end": _f("""\
- `ms`: cuánto esperar como mucho.

Acaba el programa: le manda Ctrl-C y, en su siguiente línea, sale con su limpieza de siempre. Devuelve `true` si
acabó a tiempo.
""", """\
- `ms`: the longest to wait.

Ends the program: it sends Ctrl-C and, at its next line, it exits with its usual cleanup. Returns `true` if it ended
in time.
""", ["dbg_rc"]),
    "dbg_rc": _f("Devuelve el código de retorno del programa acabado.\n", "Returns the finished program's return code.\n", ["dbg_output"]),
    "dbg_file": _f("Devuelve el fichero, con su ruta entera, de la línea donde paró.\n", "Returns the file, with its full path, of the line where it stopped.\n", ["dbg_line"]),
    "dbg_line": _f("Devuelve la línea donde paró; 0 si no está parado.\n", "Returns the line where it stopped; 0 if it is not stopped.\n", ["dbg_file", "dbg_function"]),
    "dbg_function": _f("Devuelve la función donde paró: `\"Main\"`, `\"Punto.mover\"`.\n", "Returns the function where it stopped: `\"Main\"`, `\"Point.move\"`.\n", ["dbg_frames"]),
    "dbg_frames": _f("Devuelve cuántas llamadas hay abiertas donde paró: 1 en `Main`, 2 en una función que llamó `Main`...; 0 si no está parado.\n",
                     "Returns how many calls are open where it stopped: 1 in `Main`, 2 in a function `Main` called...; 0 if not stopped.\n",
                     ["dbg_frame_function"]),
    "dbg_frame_function": _f(_FR_ES + "\nDevuelve la función de esa llamada.\n", _FR_EN + "\nReturns that call's function.\n", ["dbg_frame_line"]),
    "dbg_frame_line": _f(_FR_ES + "\nDevuelve la línea donde está esa llamada.\n", _FR_EN + "\nReturns the line that call is at.\n", ["dbg_frame_file"]),
    "dbg_frame_file": _f(_FR_ES + "\nDevuelve el fichero de esa llamada, con su ruta entera.\n", _FR_EN + "\nReturns that call's file, with its full path.\n", ["dbg_frame_line"]),
    "dbg_vars": _f(_FR_ES + "\nDevuelve cuántas variables ve: sus parámetros y las declaradas antes de su línea.\n",
                   _FR_EN + "\nReturns how many variables it sees: its parameters and those declared before its line.\n", ["dbg_var_name", "dbg_value"]),
    "dbg_var_name": _f(_FR_ES + "- `k`: la variable, desde 0.\n\nDevuelve su nombre.\n", _FR_EN + "- `k`: the variable, from 0.\n\nReturns its name.\n", ["dbg_var_type"]),
    "dbg_var_type": _f(_FR_ES + "- `k`: la variable.\n\nDevuelve su tipo como se escribe en Dash: `\"Int\"`, `\"[String]\"`, `\"Punto\"`.\n",
                       _FR_EN + "- `k`: the variable.\n\nReturns its type as written in Dash: `\"Int\"`, `\"[String]\"`, `\"Point\"`.\n", ["dbg_var_name"]),
    "dbg_globals": _f("Devuelve cuántas variables globales tiene el programa.\n", "Returns how many global variables the program has.\n", ["dbg_global_name"]),
    "dbg_global_name": _f("- `g`: la global, desde 0.\n\nDevuelve su nombre.\n", "- `g`: the global, from 0.\n\nReturns its name.\n", ["dbg_globals"]),
    "dbg_value": _f(_FR_ES + """\
- `expr`: una variable de esa llamada o una global, con `.campo` y `[n]` detrás: `"p.hijos[0].x"`.

Devuelve su valor como texto: `3`, `"hola"`, `Punto(x: 3, y: 4)`, `[1, 2]`, `nil`. Si no se puede, `"? "` y el
porqué.
""", _FR_EN + """\
- `expr`: a variable of that call or a global, with `.field` and `[n]` after it: `"p.children[0].x"`.

Returns its value as a text: `3`, `"hello"`, `Point(x: 3, y: 4)`, `[1, 2]`, `nil`. If it cannot, `"? "` and why.
""", ["dbg_value_type", "dbg_vars"]),
    "dbg_value_type": _f(_FR_ES + "- `expr`: como en `dbg_value`.\n\nDevuelve su tipo; `\"\"` si no se puede.\n",
                         _FR_EN + "- `expr`: as in `dbg_value`.\n\nReturns its type; `\"\"` if it cannot.\n", ["dbg_value"]),
    "dbg_reg": _f("- `n`: 0 a 7 los registros d0 a d7, 8 a 15 a0 a a7, 16 el contador de programa.\n\nDevuelve ese registro del programa parado.\n",
                  "- `n`: 0 to 7 registers d0 to d7, 8 to 15 a0 to a7, 16 the program counter.\n\nReturns that register of the stopped program.\n",
                  ["dbg_peek"]),
    "dbg_peek": _f("- `addr`: la dirección.\n- `size`: 1, 2 o 4 bytes.\n\nDevuelve lo que hay en la memoria, sin signo.\n",
                   "- `addr`: the address.\n- `size`: 1, 2 or 4 bytes.\n\nReturns what is in memory, unsigned.\n", ["dbg_reg"]),
    "dbg_output": _f("Devuelve todo lo que el programa ha escrito hasta ahora, su salida y sus errores.\n",
                     "Returns everything the program has written so far, its output and its errors.\n", ["dbg_rc"]),
}
