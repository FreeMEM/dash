/* El depurador de dashc (docs/DEPURADOR_LOOP.md): los builtins dbg_*, solo de dashc. Va en la librería tras
   api.c (gen_lib.py lo incluye).

   Un programa compilado con dashc --debug lleva un NOP al principio de cada línea y un HUNK_DEBUG con dónde está
   cada cosa (gen68k.c, debug_text). dbg_start lo carga (LoadSeg) y lo lanza en un proceso hijo cuya entrada es
   _dbg_child: pone su tc_TrapCode (el runtime de Dash, al empezar, pone el suyo y le pasa los TRAP que no son
   errores) y espera la orden de empezar; entonces lo ejecuta con RunCommand, la salida a un fichero de T:.

   Un punto de parada cambia el NOP de la línea por TRAP #15. El manejador apunta el PC del marco (la instrucción de
   después del TRAP) y vuelve en modo usuario a _dbg_user_stop, en el proceso hijo: guarda los registros, avisa al
   depurador y espera. Al seguir los repone y salta al PC apuntado: no hay nada que reponer, el TRAP ocupaba el
   sitio de un NOP. Paso a paso: todos los NOP a TRAP, y al parar se mira a7 para ver si es la línea que toca. Sin
   el bit de traza de la CPU, así que vale en Emu68. */

#define _DBG_TRAP 0x4E4F                 /* trap #15 (excepción 47) */
#define _DBG_NOP 0x4E71

enum { DBG_NONE, DBG_PAUSED, DBG_RUNNING, DBG_STOPPED, DBG_ENDED };
enum { DBG_CONT, DBG_STEP, DBG_NEXT, DBG_OUT };

typedef struct { ULONG off; UWORD file, line; } _DbgLine;
typedef struct { char *name; ULONG start, end; UWORD file, line; } _DbgFunc;
typedef struct { char *name, *type; LONG func, off, line; } _DbgVar;     /* func -1: una global (off en datos) */
typedef struct { char *strct, *name, *type; LONG off; } _DbgField;

static struct {
    char *text;                          /* el HUNK_DEBUG, partido en trozos (los nombres apuntan dentro) */
    char *files[64];
    LONG nfiles;
    _DbgLine *lines;
    LONG nlines;
    UBYTE *bp;                           /* un punto de parada en cada línea */
    _DbgFunc *funcs;
    LONG nfuncs;
    _DbgVar *vars;
    LONG nvars;
    _DbgField *fields;
    LONG nfields;
    ULONG quit;                          /* _dash_quit del programa (desplazamiento en el código) */
    BPTR seg;
    ULONG code, data;                    /* dónde quedaron los hunks de código y datos */
    struct Task *owner, *child;
    ULONG owner_mask, child_mask;
    BYTE owner_sig;
    BPTR out;
    char outname[48], *args, *path;
    volatile LONG state, rc, mode, kill;
    ULONG ref_a7, ref_a5;                /* donde se paró al pedir pasar o salir */
    ULONG *regs;                         /* d0-d7, a0-a6 y el PC de vuelta, en la pila del hijo */
    ULONG a7, pc;
    LONG at;                             /* la línea (índice en lines) donde está parado, -1 si ninguna */
    char error[160];
    BOOL atexit_done;
} _dbg;

ULONG _dbg_pc;                           /* (del manejador a _dbg_user_stop) */
APTR _dbg_old_trap;
void _dbg_trap(void);
void _dbg_user_stop(void);
void _dbg_stopped(ULONG *regs) __attribute__((used));

__asm__(
"       .section .text._dbg_asm,\"ax\"\n"
"       .even\n"
"       .globl  __dbg_trap\n"
"__dbg_trap:\n"
"       cmpl    #47,sp@\n"
"       bne     9f\n"
"       movel   sp@(6),__dbg_pc\n"          /* el PC del marco (tras el número y el SR) */
"       movel   #__dbg_user_stop,sp@(6)\n"
"       addql   #4,sp\n"
"       rte\n"
"9:     movel   __dbg_old_trap,sp@-\n"
"       rts\n"
"       .globl  __dbg_user_stop\n"
"__dbg_user_stop:\n"
"       subql   #4,sp\n"
"       moveml  d0-d7/a0-a6,sp@-\n"
"       movel   __dbg_pc,sp@(60)\n"
"       movel   sp,sp@-\n"
"       jsr     __dbg_stopped\n"
"       addql   #4,sp\n"
"       moveml  sp@+,d0-d7/a0-a6\n"
"       rts\n"
);

static void _dbg_fail(const char *what) {
    strncpy(_dbg.error, what, sizeof(_dbg.error) - 1);
    _dbg.error[sizeof(_dbg.error) - 1] = 0;
}

/* La línea (índice) del NOP en esa dirección, -1 si no hay (búsqueda binaria: van en orden) */
static LONG _dbg_line_at(ULONG addr) {
    LONG lo = 0, hi = _dbg.nlines - 1;
    ULONG off = addr - _dbg.code;
    while (lo <= hi) {
        LONG m = (lo + hi) / 2;
        if (_dbg.lines[m].off == off) return m;
        if (_dbg.lines[m].off < off) lo = m + 1;
        else hi = m - 1;
    }
    return -1;
}

static void _dbg_patch(LONG i, UWORD op) {
    *(volatile UWORD *)(_dbg.code + _dbg.lines[i].off) = op;
}

/* Los TRAP de ahora: los de los puntos de parada, y todos si se va paso a paso */
static void _dbg_patch_all(BOOL every) {
    LONG i;
    for (i = 0; i < _dbg.nlines; i++) _dbg_patch(i, every || _dbg.bp[i] ? _DBG_TRAP : _DBG_NOP);
    if (SysBase->LibNode.lib_Version >= 37) CacheClearU();
}

/* En el proceso hijo, en cada TRAP: ¿se para aquí? */
void _dbg_stopped(ULONG *regs) {
    ULONG a7 = (ULONG)(regs + 16), pc = regs[15] - 2;
    LONG i = _dbg_line_at(pc);
    if (_dbg.kill) {
        /* acabar: a _dash_quit(20) del programa, con su limpieza de siempre */
        regs[15] = _dbg.code + _dbg.quit;
        ((ULONG *)a7)[1] = 20;
        return;
    }
    if (i < 0) return;
    switch (_dbg.mode) {
    case DBG_CONT: if (!_dbg.bp[i]) return; break;
    case DBG_STEP: break;
    case DBG_NEXT: if (a7 < _dbg.ref_a7 && !_dbg.bp[i]) return; break;   /* más hondo: una función a la que llamó */
    case DBG_OUT: if (a7 <= _dbg.ref_a5 && !_dbg.bp[i]) return; break;  /* aún en la función (o más hondo) */
    }
    _dbg.regs = regs;
    _dbg.a7 = a7;
    _dbg.pc = pc;
    _dbg.at = i;
    _dbg.state = DBG_STOPPED;
    Signal(_dbg.owner, _dbg.owner_mask);
    Wait(_dbg.child_mask);
    _dbg.regs = NULL;
    _dbg.at = -1;
    if (_dbg.kill) {
        regs[15] = _dbg.code + _dbg.quit;
        ((ULONG *)a7)[1] = 20;
    }
}

/* La entrada del proceso hijo: su manejador de TRAP, esperar la orden de empezar y el programa */
static void _dbg_child(void) {
    struct Task *me = FindTask(NULL);
    BYTE sig = AllocSignal(-1);
    LONG rc;
    _dbg_old_trap = me->tc_TrapCode;
    me->tc_TrapCode = (APTR)_dbg_trap;
    _dbg.child_mask = sig >= 0 ? 1UL << sig : SIGBREAKF_CTRL_F;
    _dbg.child = me;
    _dbg.state = DBG_PAUSED;
    Signal(_dbg.owner, _dbg.owner_mask);
    Wait(_dbg.child_mask);
    _dbg.state = DBG_RUNNING;
    SetProgramName((STRPTR)_dbg.path);
    rc = RunCommand(_dbg.seg, 65536, (STRPTR)_dbg.args, strlen(_dbg.args));
    me->tc_TrapCode = _dbg_old_trap;
    if (sig >= 0) FreeSignal(sig);
    Forbid();                            /* (acabado del todo solo cuando ya ha salido de este código) */
    _dbg.rc = rc;
    _dbg.state = DBG_ENDED;
    Signal(_dbg.owner, _dbg.owner_mask);
}

/* ---- la información de depuración ---- */

static char *_dbg_word(char **p) {
    char *s = *p, *e;
    while (*s == ' ') s++;
    for (e = s; *e && *e != ' ' && *e != '\n'; e++) ;
    *p = *e == ' ' ? e + 1 : e;
    if (*e == ' ') *e = 0;
    return s;
}

static LONG _dbg_num(char **p) {
    char *s = _dbg_word(p);
    LONG n = 0, neg = 0;
    if (*s == '-') { neg = 1; s++; }
    while (*s >= '0' && *s <= '9') n = n * 10 + (*s++ - '0');
    return neg ? -n : n;
}

/* El HUNK_DEBUG del ejecutable (el fichero: LoadSeg no lo carga) */
static BOOL _dbg_read_info(STRPTR path) {
    BPTR f = Open(path, MODE_OLDFILE);
    LONG size, at, n, i, nl = 0, nf = 0, nv = 0, ns = 0;
    ULONG *d = NULL, first, last, type;
    char *t, *ln, *next;
    if (!f) { _dbg_fail("no puedo abrir el programa"); return FALSE; }
    Seek(f, 0, OFFSET_END);
    size = Seek(f, 0, OFFSET_BEGINNING);
    if (size > 20 && (d = (ULONG *)AllocVec(size + 4, MEMF_ANY)) && Read(f, d, size) == size) ;
    else { if (d) FreeVec(d); d = NULL; }
    Close(f);
    if (!d || d[0] != 0x3F3) { if (d) FreeVec(d); _dbg_fail("no es un programa de Amiga"); return FALSE; }
    first = d[3];
    last = d[4];
    at = 5 + (last - first + 1);
    t = NULL;
    while (at < size / 4) {
        type = d[at++] & 0x3FFFFFFF;
        if (type == 0x3E9 || type == 0x3EA) at += 1 + d[at];
        else if (type == 0x3EB) at++;
        else if (type == 0x3EC) { while ((n = d[at]) != 0) at += 2 + n; at++; }
        else if (type == 0x3F1) {
            n = d[at];
            if (!strncmp((char *)&d[at + 1], "DASH-DEBUG", 10)) {
                if ((t = (char *)AllocVec(n * 4 + 2, MEMF_ANY))) {
                    CopyMem(&d[at + 1], t, n * 4);
                    t[n * 4] = 0;
                }
                break;
            }
            at += 1 + n;
        } else if (type != 0x3F2) break;
    }
    FreeVec(d);
    if (!t) { _dbg_fail("el programa no lleva informaci\363n de depuraci\363n (comp\355lalo con dash --debug)"); return FALSE; }
    _dbg.text = t;
    for (ln = t; *ln; ln = next) {
        for (next = ln; *next && *next != '\n'; next++) ;
        if (*next) next++;
        if (*ln == 'L') nl++;
        else if (*ln == 'P') nf++;
        else if (*ln == 'V' || *ln == 'G') nv++;
        else if (*ln == 'S') ns++;
    }
    _dbg.lines = (_DbgLine *)AllocVec((nl + 1) * sizeof(_DbgLine), MEMF_ANY | MEMF_CLEAR);
    _dbg.bp = (UBYTE *)AllocVec(nl + 1, MEMF_ANY | MEMF_CLEAR);
    _dbg.funcs = (_DbgFunc *)AllocVec((nf + 1) * sizeof(_DbgFunc), MEMF_ANY | MEMF_CLEAR);
    _dbg.vars = (_DbgVar *)AllocVec((nv + 1) * sizeof(_DbgVar), MEMF_ANY | MEMF_CLEAR);
    _dbg.fields = (_DbgField *)AllocVec((ns + 1) * sizeof(_DbgField), MEMF_ANY | MEMF_CLEAR);
    if (!_dbg.lines || !_dbg.bp || !_dbg.funcs || !_dbg.vars || !_dbg.fields) { _dbg_fail("sin memoria"); return FALSE; }
    for (ln = t; *ln; ln = next) {
        char *p = ln + 2, k = *ln;
        for (next = ln; *next && *next != '\n'; next++) ;
        if (*next) *next++ = 0;
        if (k == 'F') {
            i = _dbg_num(&p);
            if (i >= 0 && i < 64) { _dbg.files[i] = p; if (i >= _dbg.nfiles) _dbg.nfiles = i + 1; }
        } else if (k == 'L') {
            _DbgLine *l = &_dbg.lines[_dbg.nlines++];
            l->off = _dbg_num(&p);
            l->file = _dbg_num(&p);
            l->line = _dbg_num(&p);
        } else if (k == 'P') {
            _DbgFunc *fn = &_dbg.funcs[_dbg.nfuncs++];
            _dbg_num(&p);
            fn->name = _dbg_word(&p);
            fn->start = _dbg_num(&p);
            fn->end = _dbg_num(&p);
            fn->file = _dbg_num(&p);
            fn->line = _dbg_num(&p);
        } else if (k == 'V') {
            _DbgVar *v = &_dbg.vars[_dbg.nvars++];
            v->func = _dbg_num(&p);
            v->name = _dbg_word(&p);
            v->type = _dbg_word(&p);
            v->off = _dbg_num(&p);
            v->line = _dbg_num(&p);
        } else if (k == 'G') {
            _DbgVar *v = &_dbg.vars[_dbg.nvars++];
            v->func = -1;
            v->name = _dbg_word(&p);
            v->type = _dbg_word(&p);
            v->off = _dbg_num(&p);
            v->line = 0;
        } else if (k == 'S') {
            _DbgField *s = &_dbg.fields[_dbg.nfields++];
            s->strct = _dbg_word(&p);
            s->name = _dbg_word(&p);
            s->type = _dbg_word(&p);
            s->off = _dbg_num(&p);
        } else if (k == 'Q') {
            _dbg.quit = _dbg_num(&p);
        }
    }
    return TRUE;
}

static void _dbg_free(void) {
    if (_dbg.seg) { UnLoadSeg(_dbg.seg); _dbg.seg = 0; }
    if (_dbg.text) FreeVec(_dbg.text);
    if (_dbg.lines) FreeVec(_dbg.lines);
    if (_dbg.bp) FreeVec(_dbg.bp);
    if (_dbg.funcs) FreeVec(_dbg.funcs);
    if (_dbg.vars) FreeVec(_dbg.vars);
    if (_dbg.fields) FreeVec(_dbg.fields);
    if (_dbg.args) FreeVec(_dbg.args);
    if (_dbg.path) FreeVec(_dbg.path);
    if (_dbg.owner_sig >= 0 && _dbg.owner) FreeSignal(_dbg.owner_sig);
    if (_dbg.outname[0]) DeleteFile((STRPTR)_dbg.outname);
    {
        char err[160];
        CopyMem(_dbg.error, err, sizeof(err));
        memset(&_dbg, 0, sizeof(_dbg));
        CopyMem(err, _dbg.error, sizeof(err));
    }
    _dbg.owner_sig = -1;
}

/* Esperar a que deje de correr, hasta ms (0: sin tope): el estado */
static LONG _dbg_wait_ms(LONG ms) {
    LONG t = 0;
    while (_dbg.state == DBG_RUNNING && (ms <= 0 || t < ms)) {
        Delay(1);
        t += 20;
    }
    SetSignal(0, _dbg.owner_mask);
    return _dbg.state;
}

/* Acabar el programa depurado: Ctrl-C, todas las líneas paran y van a _dash_quit; espera hasta ms */
static BOOL _dbg_end(LONG ms) {
    if (_dbg.state == DBG_NONE) return TRUE;
    if (_dbg.state == DBG_PAUSED) {
        /* (sin empezar: empieza y acaba en su primera línea) */
        _dbg.kill = 1;
        _dbg_patch_all(TRUE);
        Signal(_dbg.child, _dbg.child_mask);
        _dbg.state = DBG_RUNNING;
    } else if (_dbg.state != DBG_ENDED) {
        _dbg.kill = 1;
        _dbg_patch_all(TRUE);
        Signal(_dbg.child, SIGBREAKF_CTRL_C);
        if (_dbg.state == DBG_STOPPED) {
            _dbg.state = DBG_RUNNING;
            Signal(_dbg.child, _dbg.child_mask);
        }
    }
    _dbg_wait_ms(ms);
    if (_dbg.state != DBG_ENDED) return FALSE;   /* sigue: no se puede descargar su código */
    if (_dbg.out) { Close(_dbg.out); _dbg.out = 0; }
    _dbg_free();
    return TRUE;
}

static void _dbg_cleanup(void) {
    _dbg_end(0);
}

/* ---- los builtins ---- */

/* dbg_start(programa, argumentos): cargado y en pausa antes de su primera línea */
LONG db_dbg_start(LONG path_, LONG args_) {
    STRPTR path = (STRPTR)path_, args = (STRPTR)args_;
    struct Process *me = (struct Process *)FindTask(NULL);
    BPTR in;
    if (_dbg.state != DBG_NONE && !_dbg_end(5000)) { _dbg_fail("el programa de antes no acaba"); return FALSE; }
    _dbg.error[0] = 0;
    _dbg.owner_sig = -1;
    _dbg.at = -1;
    if (!path || !*path) { _dbg_fail("sin programa"); return FALSE; }
    if (!_dbg.atexit_done) { _dash_atexit(_dbg_cleanup); _dbg.atexit_done = TRUE; }
    if (!_dbg_read_info(path)) { _dbg_free(); return FALSE; }
    if (!_dbg.quit) { _dbg_free(); _dbg_fail("informaci\363n de depuraci\363n vieja (sin _dash_quit)"); return FALSE; }
    if (!(_dbg.seg = LoadSeg(path))) { _dbg_free(); _dbg_fail("no puedo cargar el programa"); return FALSE; }
    _dbg.code = (ULONG)BADDR(_dbg.seg) + 4;
    _dbg.data = *(BPTR *)BADDR(_dbg.seg) ? (ULONG)BADDR(*(BPTR *)BADDR(_dbg.seg)) + 4 : 0;
    _dbg.path = (char *)AllocVec(strlen((char *)path) + 1, MEMF_ANY);
    _dbg.args = (char *)AllocVec((args ? strlen((char *)args) : 0) + 2, MEMF_ANY);
    if (!_dbg.path || !_dbg.args) { _dbg_free(); _dbg_fail("sin memoria"); return FALSE; }
    strcpy(_dbg.path, (char *)path);
    strcpy(_dbg.args, args ? (char *)args : "");
    strcat(_dbg.args, "\n");
    _dbg.owner = &me->pr_Task;
    if ((_dbg.owner_sig = AllocSignal(-1)) < 0) { _dbg_free(); _dbg_fail("sin se\361ales libres"); return FALSE; }
    _dbg.owner_mask = 1UL << _dbg.owner_sig;
    /* (compartido, no MODE_NEWFILE: dbg_output lo lee mientras el programa escribe) */
    sprintf(_dbg.outname, "T:dash_dbg_%lx", (unsigned long)me);
    DeleteFile((STRPTR)_dbg.outname);
    if (!(_dbg.out = Open((STRPTR)_dbg.outname, MODE_READWRITE))) {
        sprintf(_dbg.outname, "RAM:dash_dbg_%lx", (unsigned long)me);
        DeleteFile((STRPTR)_dbg.outname);
        _dbg.out = Open((STRPTR)_dbg.outname, MODE_READWRITE);
    }
    in = Open((STRPTR)"NIL:", MODE_OLDFILE);
    if (!_dbg.out || !in) {
        if (in) Close(in);
        if (_dbg.out) { Close(_dbg.out); _dbg.out = 0; }
        _dbg_free();
        _dbg_fail("no puedo abrir la salida del programa");
        return FALSE;
    }
    SetSignal(0, _dbg.owner_mask);
    if (!CreateNewProcTags(NP_Entry, (ULONG)_dbg_child, NP_Name, (ULONG)FilePart(path), NP_Cli, TRUE,
                           NP_Input, in, NP_Output, _dbg.out, NP_CloseInput, TRUE, NP_CloseOutput, FALSE,
                           NP_StackSize, 8192, TAG_DONE)) {
        Close(in);
        Close(_dbg.out);
        _dbg.out = 0;
        _dbg_free();
        _dbg_fail("no puedo crear el proceso");
        return FALSE;
    }
    while (_dbg.state != DBG_PAUSED) Wait(_dbg.owner_mask);
    return TRUE;
}

/* Por qué falló el último dbg_start */
LONG db_dbg_error(void) { return (LONG)_dash_str_dup((STRPTR)_dbg.error, TRUE); }

/* El estado: 0 sin programa, 1 en pausa sin empezar, 2 corriendo, 3 parado en una línea, 4 acabado */
LONG db_dbg_state(void) { return _dbg.state; }

/* La señal que el depurador recibe cuando el programa para o acaba (para mui_wait_event_signals) */
LONG db_dbg_signal(void) { return (LONG)_dbg.owner_mask; }

LONG db_dbg_wait(LONG ms) { return _dbg_wait_ms(ms); }

/* Las líneas de ese fichero (por el final de su nombre: "prog.dash") con un NOP: true si hay alguna */
static BOOL _dbg_set(STRPTR file, LONG line, UBYTE on) {
    LONG i, k = file ? strlen((char *)file) : 0;
    BOOL found = FALSE;
    for (i = 0; i < _dbg.nlines; i++) {
        char *f = _dbg.lines[i].file < _dbg.nfiles ? _dbg.files[_dbg.lines[i].file] : NULL;
        LONG fl;
        if (!f || _dbg.lines[i].line != line) continue;
        fl = strlen(f);
        if (k > fl || strcmp(f + fl - k, (char *)file) || (fl > k && f[fl - k - 1] != '/' && f[fl - k - 1] != ':'))
            continue;
        _dbg.bp[i] = on;
        found = TRUE;
    }
    if (found && _dbg.state != DBG_RUNNING) _dbg_patch_all(FALSE);
    else if (found) {
        /* corriendo: solo ese cambio (no se quitan los de paso a paso, que no los hay) */
        for (i = 0; i < _dbg.nlines; i++) _dbg_patch(i, _dbg.bp[i] ? _DBG_TRAP : _DBG_NOP);
        if (SysBase->LibNode.lib_Version >= 37) CacheClearU();
    }
    return found;
}

LONG db_dbg_break(LONG file, LONG line) { return _dbg_set((STRPTR)file, line, 1); }
LONG db_dbg_unbreak(LONG file, LONG line) { return _dbg_set((STRPTR)file, line, 0); }

/* Seguir (de la pausa del principio o de una parada) hasta un punto de parada o el final */
static LONG _dbg_go(LONG mode) {
    if (_dbg.state != DBG_PAUSED && _dbg.state != DBG_STOPPED) return FALSE;
    _dbg.mode = mode;
    if (_dbg.state == DBG_STOPPED) {
        _dbg.ref_a7 = _dbg.a7;
        _dbg.ref_a5 = _dbg.regs ? _dbg.regs[13] : 0;
    } else {
        _dbg.ref_a7 = 0xFFFFFFFF;
        _dbg.ref_a5 = 0;
    }
    _dbg_patch_all(mode != DBG_CONT);
    SetSignal(0, _dbg.owner_mask);
    _dbg.state = DBG_RUNNING;
    Signal(_dbg.child, _dbg.child_mask);
    return TRUE;
}

LONG db_dbg_continue(void) { return _dbg_go(DBG_CONT); }
LONG db_dbg_step(void) { return _dbg_go(DBG_STEP); }
LONG db_dbg_next(void) { return _dbg_go(DBG_NEXT); }
LONG db_dbg_out(void) { return _dbg_go(DBG_OUT); }

/* Parar en la siguiente línea que pase (el programa corriendo) */
LONG db_dbg_pause(void) {
    if (_dbg.state != DBG_RUNNING) return FALSE;
    _dbg.mode = DBG_STEP;
    _dbg_patch_all(TRUE);
    return TRUE;
}

/* Acabarlo (Ctrl-C y _dash_quit en su siguiente línea): true si acabó en ms */
LONG db_dbg_end(LONG ms) { return _dbg_end(ms); }

/* El código de salida del programa (acabado) */
LONG db_dbg_rc(void) { return _dbg.rc; }

/* Dónde está parado: fichero (el nombre entero), línea y función */
LONG db_dbg_file(void) {
    char *f = _dbg.at >= 0 && _dbg.lines[_dbg.at].file < _dbg.nfiles ? _dbg.files[_dbg.lines[_dbg.at].file] : NULL;
    return (LONG)_dash_str_dup((STRPTR)(f ? f : ""), TRUE);
}

LONG db_dbg_line(void) { return _dbg.at >= 0 ? _dbg.lines[_dbg.at].line : 0; }

static _DbgFunc *_dbg_func_at(ULONG pc) {
    LONG i;
    ULONG off = pc - _dbg.code;
    for (i = 0; i < _dbg.nfuncs; i++)
        if (off >= _dbg.funcs[i].start && off < _dbg.funcs[i].end) return &_dbg.funcs[i];
    return NULL;
}

LONG db_dbg_function(void) {
    _DbgFunc *f = _dbg.at >= 0 ? _dbg_func_at(_dbg.pc) : NULL;
    return (LONG)_dash_str_dup((STRPTR)(f ? f->name : ""), TRUE);
}

/* Un registro del programa parado: 0-7 d0-d7, 8-15 a0-a7, 16 el PC (la línea) */
LONG db_dbg_reg(LONG n) {
    if (_dbg.state != DBG_STOPPED || !_dbg.regs) return 0;
    if (n >= 0 && n < 15) return _dbg.regs[n];
    if (n == 15) return _dbg.a7;
    if (n == 16) return _dbg.pc;
    return 0;
}

/* Memoria: 1, 2 o 4 bytes en addr (sin signo); 0 en una dirección impar con 2 o 4 */
LONG db_dbg_peek(LONG addr, LONG size) {
    if (size == 1) return *(volatile UBYTE *)addr;
    if (addr & 1) return 0;
    if (size == 2) return *(volatile UWORD *)addr;
    return *(volatile ULONG *)addr;
}

/* Lo que el programa ha escrito hasta ahora (su salida y su salida de errores) */
LONG db_dbg_output(void) {
    BPTR f;
    STRPTR s = NULL;
    LONG n;
    if (!_dbg.outname[0]) return (LONG)_dash_str_dup((STRPTR)"", TRUE);
    if (_dbg.out) Flush(_dbg.out);
    if ((f = Open((STRPTR)_dbg.outname, MODE_OLDFILE))) {
        Seek(f, 0, OFFSET_END);
        n = Seek(f, 0, OFFSET_BEGINNING);
        if (n > 0 && (s = _dash_str_alloc(n, TRUE))) {
            LONG got = Read(f, s, n);
            s[got > 0 ? got : 0] = 0;
        }
        Close(f);
    }
    return (LONG)(s ? s : _dash_str_dup((STRPTR)"", TRUE));
}
