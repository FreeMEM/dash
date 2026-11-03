/* El arranque y la salida del código de dashc para DashOS (runtime/dashos/build.py): lo que en el 68000 hacen
   rt_math.s (_dash_start, _dash_quit) y _dash_init/_dash_finish de api.c. El código de dashc entra en _dashc_start,
   que llama a _dash_start(main, ficheros, pila). */
const char *_dash_srcfiles[64];
/* lo que el código de dashc pone al arrancar y en DashOS aún no se usa */
LONG _dash_ac_secs;
const char *_dash_stdiowin;


void _dash_quit(int code)
{
    _dash_exit_cleanup();
    exit(code);
}

void _dash_start(void (*main_fn)(void), const char *const *files, _DashP stack)
{
    int i;
    (void)stack;                                       /* (la pila la pone el cargador: PT_GNU_STACK) */
    for (i = 0; i < 63 && files[i]; i++) _dash_srcfiles[i] = files[i];
    main_fn();
    _dash_quit(0);
}

void _dash_print_str(STRPTR s) { Printf((CONST_STRPTR)"%s\n", s); }
void _dash_print_int(_DashP v) { Printf((CONST_STRPTR)"%ld\n", (LONG)v); }
void _dash_print_char(_DashP c) { Printf((CONST_STRPTR)"%lc\n", (LONG)(UBYTE)c); }
void _dash_print_bool(_DashP v) { PutStr((CONST_STRPTR)(v ? "true\n" : "false\n")); }
void dl_div_zero(void) { _dash_fail("divisi\363n por cero", NULL); }
void dl_a32_fail(void) { _dash_fail("puntero de Amiga de 4 GB o m\341s", NULL); }
