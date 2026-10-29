"""Los builtins que solo tiene dashc (Dash 2.0), con su C en dashc/runtime (depurar.c: db_nombre), aparte de
compiler/amiga_builtins.py, que es de los dos Dash. Nombre: (parámetros, lo que devuelve, descripción)."""

DASHC_BUILTINS = {
    # el depurador (docs/DEPURADOR_LOOP.md): el programa depurado, compilado con dash --debug
    "dbg_start": (["program", "args"], "BOOL",
                  "Load a program built with dash --debug and start it in a process of its own, paused before its "
                  "first line (set breakpoints, then dbg_continue): false if it could not (dbg_error says why)"),
    "dbg_error": ([], "STRPTR", "Why the last dbg_start failed"),
    "dbg_state": ([], "LONG", "The debugged program: 0 none, 1 paused before starting, 2 running, 3 stopped at a "
                               "line, 4 ended"),
    "dbg_signal": ([], "LONG", "The signal the debugger gets when the program stops or ends (for "
                                "mui_wait_event_signals)"),
    "dbg_wait": (["ms"], "LONG", "Wait until the program stops or ends, ms at most (0: no limit): its state"),
    "dbg_break": (["file", "line"], "BOOL", "A breakpoint at that line of that file (\"prog.dash\": the end of its "
                                            "path): false if the line has no code"),
    "dbg_unbreak": (["file", "line"], "BOOL", "Take the breakpoint out of that line"),
    "dbg_continue": ([], "BOOL", "Go on (from the start or a stop) until a breakpoint or the end"),
    "dbg_step": ([], "BOOL", "Go on to the next line, into the functions it calls"),
    "dbg_next": ([], "BOOL", "Go on to the next line of this function (or of the one that called it)"),
    "dbg_out": ([], "BOOL", "Go on until the function returns: the next line of the one that called it"),
    "dbg_pause": ([], "BOOL", "Stop the running program at the next line it runs"),
    "dbg_end": (["ms"], "BOOL", "End the program (Ctrl-C, and at its next line its usual end): true if it ended "
                                "within ms"),
    "dbg_rc": ([], "LONG", "The return code of the ended program"),
    "dbg_file": ([], "STRPTR", "The file of the line where the program stopped (its full path)"),
    "dbg_line": ([], "LONG", "The line where the program stopped (0 if it is not stopped)"),
    "dbg_function": ([], "STRPTR", "The function where the program stopped (\"Main\", \"Punto.mover\"...)"),
    "dbg_reg": (["n"], "LONG", "A register of the stopped program: 0-7 d0-d7, 8-15 a0-a7, 16 the PC"),
    "dbg_peek": (["addr", "size"], "LONG", "1, 2 or 4 bytes of memory at addr, without sign"),
    "dbg_output": ([], "STRPTR", "What the program has written so far (output and error output)"),
}
