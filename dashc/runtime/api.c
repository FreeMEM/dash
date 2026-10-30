/* Lo que dashc añade al runtime de ./dash (gen_lib.py lo incluye al final de dashlib_rt.c): las bases
   de las librerías, el arranque y la salida sin libnix, Print, bench_* y, con nombre dl_*, lo que el
   código de dashc llama (en C son static, macros o en línea). Todo se llama como en C: argumentos en la
   pila, resultado en d0. */
#include <exec/semaphores.h>
#include <devices/timer.h>
#include <proto/timer.h>
#include <proto/graphics.h>

struct ExecBase *SysBase;
struct DosLibrary *DOSBase;
struct IntuitionBase *IntuitionBase;
struct GfxBase *GfxBase;   /* los @native de lib/amiga (en ./dash la abre libnix) */
struct WBStartup *_WBenchMsg;   /* desde el Workbench, su mensaje (como libnix) */
static char *dash_cmdline;      /* desde el Shell, la línea de órdenes partida (argv) */
static BPTR dash_old_dir;
static char *dash_args_buf[64];
static struct timerequest *bench_tr;
static struct EClockVal bench_t0;
static ULONG bench_freq;

void (*_dash_weak_dash_time_init)(void) = _dash_time_init;
/* GadTools, como ./dash la abre al empezar y la cierra al acabar: solo si el programa la usa (lo que
   toca GadToolsBase entra con ella, ver hunk.c) */
static void dl_gt_open(void)
{
    if (!(GadToolsBase = OpenLibrary((CONST_STRPTR)"gadtools.library", 37))) _dash_quit(10);
}
void (*_dash_weak_dl_gt_open)(void) = dl_gt_open;

static void dl_gt_fin(void)
{
    if (GadToolsBase) {
        _dash_gt_cleanup();
        CloseLibrary(GadToolsBase);
        GadToolsBase = NULL;
    }
}

/* ASL, que el runtime abre al usarla */
static void dl_asl_fin(void)
{
    if (AslBase) {
        _dash_asl_cleanup();
        CloseLibrary(AslBase);
        AslBase = NULL;
    }
}

/* La pila de Main (_dash_start, rt_math.s): una nueva de size bytes si la que dio el shell o el Workbench es
   menor (como swapstack de libnix); 0 si basta la que hay o no hay memoria */
static struct StackSwapStruct dl_sss;
static ULONG dl_stack_size;
struct StackSwapStruct *_dash_stack_get(ULONG size)
{
    struct Task *me = FindTask(NULL);
    APTR mem;
    if ((ULONG)me->tc_SPUpper - (ULONG)me->tc_SPLower >= size) return NULL;
    if (!(mem = AllocMem(size, MEMF_ANY))) return NULL;
    dl_sss.stk_Lower = mem;
    dl_sss.stk_Upper = (ULONG)mem + size;
    dl_sss.stk_Pointer = (APTR)dl_sss.stk_Upper;
    dl_stack_size = size;
    return &dl_sss;
}

void _dash_stack_free(void)
{
    FreeMem(dl_sss.stk_Lower, dl_stack_size);
}

/* malloc y free para el C de dentro (zlib, lo de @link...): de un pool de exec que se borra al acabar, como el
   malloc de libnix. Con un semáforo, como el de libnix: el C de @link puede pedir memoria desde una tarea suya (el
   sonido de MintVID) a la vez que el programa (los pools de exec no son para dos a la vez) */
static APTR dl_malloc_pool;
static struct SignalSemaphore dl_malloc_sem;
static volatile LONG dl_malloc_sem_ok;

static void dl_malloc_lock(void)
{
    if (!dl_malloc_sem_ok) {
        Forbid();
        if (!dl_malloc_sem_ok) {
            InitSemaphore(&dl_malloc_sem);
            dl_malloc_sem_ok = 1;
        }
        Permit();
    }
    ObtainSemaphore(&dl_malloc_sem);
}

void *malloc(size_t n)
{
    ULONG *p = NULL;
    dl_malloc_lock();
    if (dl_malloc_pool || (dl_malloc_pool = CreatePool(MEMF_ANY, 16384, 4096)))
        p = AllocPooled(dl_malloc_pool, n + 4);
    ReleaseSemaphore(&dl_malloc_sem);
    if (!p) return NULL;
    *p = n + 4;
    return p + 1;
}

void free(void *x)
{
    if (x) {
        ULONG *p = (ULONG *)x - 1;
        dl_malloc_lock();
        FreePooled(dl_malloc_pool, p, *p);
        ReleaseSemaphore(&dl_malloc_sem);
    }
}

static void dl_malloc_fin(void)
{
    if (dl_malloc_pool) DeletePool(dl_malloc_pool);
    dl_malloc_pool = NULL;
}
void (*_dash_weak_dl_malloc_fin)(void) = dl_malloc_fin;

/* las librerías que libnix abre sola, solo si el programa las usa (runtime/rt_libs.s) */
extern void (*_dash_weak_lib_layers)(LONG), (*_dash_weak_lib_utility)(LONG);

/* 68020 o mejor: rt_math.s usa divs.l y muls.l (como utility.library con gcc) */
UBYTE _dash_cpu020;

/* Los argumentos del Shell, como los parte libnix: separados por espacios, "entre comillas" con
   *" y *N dentro; argv[0], el nombre del programa */
static void dash_split_args(const char *cmd, LONG len)
{
    char *p, *o;
    int n = 0;
    dash_cmdline = AllocVec(len + 1, MEMF_ANY);
    if (!dash_cmdline) return;
    p = o = dash_cmdline;
    CopyMem((APTR)cmd, p, len);
    p[len] = 0;
    dash_args_buf[n++] = "";
    while (*p && n < 63) {
        while (*p == ' ' || *p == '\t' || *p == '\n') p++;
        if (!*p) break;
        dash_args_buf[n++] = o;
        if (*p == '"') {
            p++;
            while (*p && *p != '"') {
                if (*p == '*' && p[1]) {
                    p++;
                    *o++ = (*p == 'N' || *p == 'n') ? '\n' : (*p == 'E' || *p == 'e') ? 27 : *p;
                    p++;
                } else {
                    *o++ = *p++;
                }
            }
            if (*p) p++;
        } else {
            while (*p && *p != ' ' && *p != '\t' && *p != '\n') *o++ = *p++;
        }
        if (*p) p++;
        *o++ = 0;
    }
    dash_args_buf[n] = NULL;
    _dash_argc = n;
    _dash_argv = dash_args_buf;
}

/* desde el Workbench, lo que se abre para la entrada y la salida (__stdiowin de libnix; el programa pone el
   de @workbench_output al arrancar) */
const char *_dash_stdiowin = "CON://///AUTO/CLOSE/WAIT";
static BPTR dash_wb_con, dash_wb_in, dash_wb_out;

/* Desde _dash_start (rt_math.s): 0 si todo fue bien; si no, el código de salida */
LONG _dash_init(const char *cmd, LONG len)
{
    struct Process *pr;
    SysBase = *(struct ExecBase **)4;
    pr = (struct Process *)FindTask(NULL);
    if (!pr->pr_CLI) {
        /* desde el Workbench: su mensaje, y la carpeta del programa como actual (libnix) */
        WaitPort(&pr->pr_MsgPort);
        _WBenchMsg = (struct WBStartup *)GetMsg(&pr->pr_MsgPort);
    } else {
        dash_split_args(cmd, len);
    }
    _dash_cpu020 = (SysBase->AttnFlags & AFF_68020) != 0;
#ifdef __HAVE_68881__
    /* --fpu: la FPU en precisión extendida (bits 6-7 del FPCR a 0). Hay sistemas que dejan el programa en
       precisión simple (el CoffinOS de un usuario de Tachyon: Date.now() a saltos, tarea 49 de Tachyon) */
    if (SysBase->AttnFlags & (AFF_68881 | AFF_68882 | AFF_FPU40)) {
        ULONG v;
        __asm__ volatile ("fmove.l %%fpcr,%0" : "=d"(v));
        v &= ~0xC0UL;
        __asm__ volatile ("fmove.l %0,%%fpcr" : : "d"(v));
    }
#endif
    _dash_trap_on();
    IntuitionBase = (struct IntuitionBase *)OpenLibrary((CONST_STRPTR)"intuition.library", 37);
    DOSBase = (struct DosLibrary *)OpenLibrary((CONST_STRPTR)"dos.library", 37);
    GfxBase = (struct GfxBase *)OpenLibrary((CONST_STRPTR)"graphics.library", 37);
    if (_dash_weak_lib_layers) _dash_weak_lib_layers(1);
    if (_dash_weak_dl_gt_open) _dash_weak_dl_gt_open();
    if (_dash_weak_lib_utility) _dash_weak_lib_utility(1);
    if (!IntuitionBase || !DOSBase) {
        _dash_exit_cleanup();
        return 10;
    }
    if (_WBenchMsg && _dash_stdiowin) {
        /* desde el Workbench, la entrada y la salida (como libnix: su ventana de consola o @workbench_output) */
        if (!(dash_wb_con = Open((CONST_STRPTR)_dash_stdiowin, MODE_OLDFILE))) {
            _dash_exit_cleanup();
            return 20;
        }
        dash_wb_in = SelectInput(dash_wb_con);
        dash_wb_out = SelectOutput(dash_wb_con);
    }
    if (_WBenchMsg && _WBenchMsg->sm_ArgList) dash_old_dir = CurrentDir(_WBenchMsg->sm_ArgList[0].wa_Lock);
    /* time_ms cuenta desde el arranque, como en ./dash (solo si el programa usa el runtime de tiempo) */
    if (_dash_weak_dash_time_init) _dash_weak_dash_time_init();
    return 0;
}

static void dl_close_windows(void);
void (*_dash_weak_dl_close_windows)(void) = dl_close_windows;
#define dl_weak_close_windows _dash_weak_dl_close_windows

/* Desde _dash_quit, al acabar de cualquier forma: como el final de main y la lista de salida de libnix */
void _dash_finish(void)
{
    if (bench_tr) {
        struct MsgPort *port = bench_tr->tr_node.io_Message.mn_ReplyPort;
        CloseDevice((struct IORequest *)bench_tr);
        DeleteIORequest((struct IORequest *)bench_tr);
        DeleteMsgPort(port);
        bench_tr = NULL;
    }
    if (dl_weak_close_windows) dl_weak_close_windows();
    _dash_exit_cleanup();
    _dash_atexit_run();
    if (GfxBase) CloseLibrary((struct Library *)GfxBase);
    if (_dash_weak_lib_layers) _dash_weak_lib_layers(0);
    if (_dash_weak_lib_utility) _dash_weak_lib_utility(0);
    if (_dash_weak_dl_malloc_fin) _dash_weak_dl_malloc_fin();
    if (dash_cmdline) FreeVec(dash_cmdline);
    if (dash_wb_con) {
        SelectInput(dash_wb_in);
        SelectOutput(dash_wb_out);
        Close(dash_wb_con);
        dash_wb_con = 0;
    }
    if (_WBenchMsg) {
        if (dash_old_dir) CurrentDir(dash_old_dir);
        /* el mensaje se devuelve en Forbid: el Workbench descarga el programa al recibirlo */
        Forbid();
        ReplyMsg((struct Message *)_WBenchMsg);
    }
}

void _dash_print_str(STRPTR s)
{
    VPrintf((CONST_STRPTR)"%s\n", (APTR)&s);
}

/* Wait segundos */
void _dash_wait(LONG s)
{
    Delay(s * 50);
}

void _dash_print_int(LONG v)
{
    VPrintf((CONST_STRPTR)"%ld\n", (APTR)&v);
}

void _dash_print_char(LONG c)
{
    LONG v = (UBYTE)c;
    VPrintf((CONST_STRPTR)"%lc\n", (APTR)&v);
}

void _dash_print_bool(LONG v)
{
    PutStr((CONST_STRPTR)(v ? "true\n" : "false\n"));
}

/* rt_math.s salta aquí con un divisor 0 */
void _dash_div_zero(void)
{
    _dash_fail("divisi\363n por cero", NULL);
}

/* Medir, como tests/bench/bench_lib.dash: bench_start() y bench_end("nombre", vueltas)
   escriben "BENCH nombre vueltas ticks_del_EClock frecuencia" */
void _bench_start(void)
{
    if (!bench_tr) {
        struct MsgPort *port = CreateMsgPort();
        if (!port) return;
        bench_tr = (struct timerequest *)CreateIORequest(port, sizeof(struct timerequest));
        if (bench_tr && OpenDevice((CONST_STRPTR)TIMERNAME, UNIT_ECLOCK, (struct IORequest *)bench_tr, 0) == 0) {
            if (!TimerBase) TimerBase = bench_tr->tr_node.io_Device;
        } else {
            if (bench_tr) DeleteIORequest((struct IORequest *)bench_tr);
            bench_tr = NULL;
            DeleteMsgPort(port);
            return;
        }
    }
    bench_freq = ReadEClock(&bench_t0);
}

void _bench_end(const char *name, LONG iterations)
{
    struct EClockVal t1;
    ULONG args[4];
    if (!bench_tr) return;
    ReadEClock(&t1);
    args[0] = (ULONG)name;
    args[1] = (ULONG)iterations;
    args[2] = t1.ev_lo - bench_t0.ev_lo;
    args[3] = bench_freq;
    VPrintf((CONST_STRPTR)"BENCH %s %ld %lu %lu\n", (APTR)args);
}

/* ---- ventanas (Window) y su EventLoop, como el C de ./dash (WINDOW_OPEN, EVENT_LOOP_START) ----
   dashc pone en el código lo de cada ventana; flags: 1 cierre, 2 barra, 4 profundidad, 8 tamaño,
   16 sin bordes, 32 activa */
struct DashWinDesc { STRPTR title; LONG left, top, width, height, flags, idcmp; };

/* las abiertas, para cerrarlas al salir de cualquier forma (./dash las cierra en _dash_exit_cleanup) */
static struct Window *dl_open_wins[16];

/* las variables de las ventanas abiertas (al cerrarlas de otra forma, close_window, quedan a nil) */
static struct Window **dl_win_vars[16];

/* Abre la ventana y la deja en su variable (pvar) */
LONG dl_window_open(const struct DashWinDesc *d, struct Window **pvar)
{
    int i;
    struct Window *w = OpenWindowTags(NULL,
        WA_Left, d->left, WA_Top, d->top,
        WA_Width, d->width, WA_Height, d->height,
        WA_Title, (ULONG)d->title,
        WA_CloseGadget, (d->flags & 1) != 0,
        WA_DragBar, (d->flags & 2) != 0,
        WA_DepthGadget, (d->flags & 4) != 0,
        WA_SizeGadget, (d->flags & 8) != 0,
        WA_Borderless, (d->flags & 16) != 0,
        WA_Activate, (d->flags & 32) != 0,
        WA_MinWidth, 40, WA_MinHeight, 20,
        WA_MaxWidth, (ULONG)~0, WA_MaxHeight, (ULONG)~0,
        WA_GimmeZeroZero, TRUE,
        WA_IDCMP, d->idcmp,
        _dash_screen ? WA_CustomScreen : TAG_IGNORE, (ULONG)_dash_screen,
        TAG_DONE);
    if (!w) _dash_exit(20);
    _dash_win = w;
    _dash_rp = w->RPort;
    for (i = 0; i < 16; i++)
        if (!dl_open_wins[i]) {
            dl_open_wins[i] = w;
            dl_win_vars[i] = pvar;
            break;
        }
    *pvar = w;
    return (LONG)w;
}

/* gfx_circle_fill y compañía: el relleno de áreas de la ventana recién abierta, del tamaño de la ventana */
void dl_init_area(void)
{
    _dash_init_area(_dash_rp, _dash_win->Width, _dash_win->Height);
}

/* Las ventanas de window_create (_dash_windows): solo si el programa las usa (punteros débiles; lo que toca
   _dash_windows entra con ellas, ver hunk.c) */
static void dl_forget(struct Window *w)
{
    LONG i;
    for (i = 1; i <= _DASH_MAX_WINDOWS; i++)
        if (_dash_windows[i] == w) _dash_windows[i] = NULL;
}
void (*_dash_weak_dl_forget)(struct Window *) = dl_forget;

/* una ventana se cierra: fuera de la lista, su variable a nil */
static void _dash_window_closed(struct Window *w)
{
    int i;
    for (i = 0; i < 16; i++)
        if (dl_open_wins[i] == w) {
            dl_open_wins[i] = NULL;
            if (dl_win_vars[i]) *dl_win_vars[i] = NULL;
        }
    if (_dash_weak_dl_forget) _dash_weak_dl_forget(w);
    if (_dash_win == w) {
        _dash_win = NULL;
        _dash_rp = NULL;
    }
}

void dl_window_close(struct Window **pw)
{
    struct Window *w = *pw;
    if (!w) return;
    _dash_window_closed(w);
    _dash_before_close(w);
    CloseWindow(w);
    *pw = NULL;
}

/* close_window(): la ventana actual */
static void _dash_close_window(void)
{
    struct Window *w = _dash_win;
    if (!w) return;
    _dash_window_closed(w);
    _dash_before_close(w);
    CloseWindow(w);
}

static UWORD dl_ev_code;
LONG dl_event_code(void) { return dl_ev_code; }

static void dl_close_windows(void)
{
    int i;
    for (i = 0; i < 16; i++)
        if (dl_open_wins[i]) {
            struct Window *w = dl_open_wins[i];
            dl_window_close(&w);
        }
}
LONG dl_key_char(LONG c) { return _dash_last_key_text[0] == (UBYTE)c && _dash_last_key_text[1] == 0; }

/* De dónde vino el último mensaje (event_window(): el número de una ventana de window_create, 0 la del
   EventLoop) */
static struct Window *dl_ev_win, *dl_ev_main;
static LONG _dash_event_window_handle(void)
{
    LONG i;
    if (!dl_ev_win || dl_ev_win == dl_ev_main) return 0;
    for (i = 1; i <= _DASH_MAX_WINDOWS; i++)
        if (_dash_windows[i] == dl_ev_win) return i;
    return 0;
}

/* El EventLoop escucha también las ventanas de window_create, como ./dash (_dash_loop_next): con pm, el mensaje
   de una de ellas (1 si hay); sin él, la máscara de sus señales. Solo si el programa usa window_create. */
static ULONG dl_others(struct Window *main, struct IntuiMessage **pm, struct IntuiMessage *(*gm)(struct MsgPort *))
{
    ULONG mask = 0;
    LONG i;
    for (i = 1; i <= _DASH_MAX_WINDOWS; i++) {
        struct Window *w = _dash_windows[i];
        if (!w || w == main || !w->UserPort) continue;
        if (!pm) mask |= 1UL << w->UserPort->mp_SigBit;
        else if ((*pm = gm(w->UserPort)) != NULL) return 1;
    }
    return mask;
}
ULONG (*_dash_weak_dl_others)(struct Window *, struct IntuiMessage **, struct IntuiMessage *(*)(struct MsgPort *)) =
    dl_others;

static struct IntuiMessage *dl_get_plain(struct MsgPort *p) { return (struct IntuiMessage *)GetMsg(p); }

static struct IntuiMessage *dl_fetch(struct Window *main, struct IntuiMessage *(*gm)(struct MsgPort *))
{
    struct IntuiMessage *m = gm(main->UserPort);
    dl_ev_main = main;
    if (!m && _dash_weak_dl_others) _dash_weak_dl_others(main, &m, gm);
    if (m) dl_ev_win = m->IDCMPWindow;
    return m;
}

/* las señales que despiertan al EventLoop */
static ULONG dl_wait_mask(struct Window *w)
{
    ULONG m = 1UL << w->UserPort->mp_SigBit;
    if (_dash_weak_dl_others) m |= _dash_weak_dl_others(w, NULL, NULL);
    return m;
}

/* El siguiente mensaje de la ventana: su clase (0 si la ventana ya no está). Antes de devolverlo
   apunta la tecla (_dash_key_record) o el clic, como el EventLoop de ./dash. */
static LONG dl_event_take(struct Window *w)
{
    struct IntuiMessage *msg = dl_fetch(w, dl_get_plain);
    ULONG cls;
    if (!msg) return 0;
    cls = msg->Class;
    dl_ev_code = msg->Code;
    if (cls == IDCMP_RAWKEY) _dash_key_record(msg);
    if (cls == IDCMP_MOUSEBUTTONS) {
        _dash_click_x = msg->MouseX - msg->IDCMPWindow->BorderLeft;
        _dash_click_y = msg->MouseY - msg->IDCMPWindow->BorderTop;
    }
    ReplyMsg((struct Message *)msg);
    return (LONG)cls;
}
static LONG (*dl_take)(struct Window *) = dl_event_take;

/* Con gadgets de GadTools (On Gadget, button_create...): GT_GetIMsg, y el gadget del mensaje apuntado antes
   de devolverlo (gadget_id); la clase de un mensaje de gadget pasa a GADGETUP (On Gadget) y la de otro
   GADGETDOWN o MOUSEMOVE a MOUSEMOVE (ningún On). keys: las teclas de los gadgets ("_Vale") como un clic. */
static LONG dl_gt_keys;
static struct IntuiMessage *dl_get_gt(struct MsgPort *p) { return GT_GetIMsg(p); }

static LONG dl_event_take_gt(struct Window *w)
{
    struct IntuiMessage *msg = dl_fetch(w, dl_get_gt);
    ULONG cls;
    LONG gev;
    if (!msg) return 0;
    cls = msg->Class;
    dl_ev_code = msg->Code;
    if (cls == IDCMP_RAWKEY) _dash_key_record(msg);
    if (cls == IDCMP_MOUSEBUTTONS) {
        _dash_click_x = msg->MouseX - msg->IDCMPWindow->BorderLeft;
        _dash_click_y = msg->MouseY - msg->IDCMPWindow->BorderTop;
    }
    gev = _dash_gadget_event(msg);
    if (!gev && dl_gt_keys && cls == IDCMP_RAWKEY && (gev = _dash_gadget_key(msg))) cls = IDCMP_GADGETUP;
    if (cls == IDCMP_REFRESHWINDOW) {
        GT_BeginRefresh(msg->IDCMPWindow);
        GT_EndRefresh(msg->IDCMPWindow, TRUE);
    }
    GT_ReplyIMsg(msg);
    if (cls == IDCMP_GADGETUP || cls == IDCMP_GADGETDOWN || cls == IDCMP_MOUSEMOVE)
        cls = gev ? IDCMP_GADGETUP : IDCMP_MOUSEMOVE;
    return (LONG)cls;
}

void dl_event_gt_on(LONG keys)
{
    dl_take = dl_event_take_gt;
    dl_gt_keys = keys;
}

/* On Menu: su cuerpo, una vez por cada opción de una selección múltiple (dl_menu_next da 0 al acabar) */
static UWORD dl_mc;
static LONG dl_mguard;
void dl_menu_begin(void)
{
    dl_mc = dl_ev_code;
    dl_mguard = 64;
}

LONG dl_menu_next(void)
{
    struct MenuItem *mi;
    if (dl_mc == MENUNULL || !_dash_menu || !dl_mguard--) return 0;
    mi = ItemAddress(_dash_menu, dl_mc);
    if (!mi) return 0;
    _dash_menu_last = (LONG)GTMENUITEM_USERDATA(mi);
    dl_mc = mi->NextSelect;
    return 1;
}

LONG dl_event_next(struct Window **pw)
{
    for (;;) {
        LONG cls;
        if (!*pw) return 0;
        if ((cls = dl_take(*pw)) != 0) return cls;
        Wait(dl_wait_mask(*pw));
    }
}

/* Con On Timer: -1 cuando pasa el tiempo (_dash_lt_* de ./dash) */
LONG dl_event_next_timer(struct Window **pw, LONG ms)
{
    for (;;) {
        LONG cls;
        if (!*pw) return 0;
        if ((cls = dl_take(*pw)) != 0) return cls;
        _dash_lt_send(ms);
        Wait(dl_wait_mask(*pw) | _dash_lt_signal());
        if (_dash_lt_fired()) return -1;
    }
}

/* ---- textos ---- */
ULONG dl_tmp_mark(void) { return _dash_tmp_mark(); }
void dl_tmp_release(ULONG m) { _dash_tmp_release(m); }
/* al salir de una función: fuera sus temporales menos el texto que devuelve, que sigue en d0 */
STRPTR dl_tmp_release_keep(ULONG m, STRPTR keep) { _dash_tmp_release_keep(m, keep); return keep; }
LONG dl_tmp_release_ret(ULONG m, LONG v) { _dash_tmp_release(m); return v; }
/* var = valor devolviendo el texto nuevo de var (dashc no siempre tiene la dirección de var:
   puede ir en un registro) */
STRPTR dl_str_assign(STRPTR var, STRPTR v) { _dash_str_set(&var, v); return var; }
STRPTR dl_str_assign_copy(STRPTR var, STRPTR v) { _dash_str_set_copy(&var, v); return var; }
STRPTR dl_str_append_r(STRPTR var, STRPTR add) { _dash_str_append(&var, add); return var; }
STRPTR dl_str_dup(STRPTR s) { return _dash_str_dup(s, FALSE); }
/* para el C de @link (dashc --cabecera): un temporal de Dash (se libera solo). dl_str_forget ya no hace nada: el
   largo va en la cabecera de cada texto de Dash (R8 de main) y un texto de C no la tiene; se queda por el C ya
   compilado que la llama */
STRPTR dl_str_temp(STRPTR s) { return _dash_str_dup(s, TRUE); }
/* un literal de dashc como texto de Dash fijo (dash_lit de gen68k.c, que deja 12 bytes delante para la cabecera):
   escapado, nunca se libera ni se escribe en su sitio */
typedef char _dl_str_hdr_12[sizeof(_DashStrHdr) == 12 ? 1 : -1];
/* (y lo que str_ours de gen68k.c lee en línea: el largo en +4, self en +8 y la clave) */
typedef char _dl_str_hdr_len[__builtin_offsetof(_DashStrHdr, len) == 4 ? 1 : -1];
typedef char _dl_str_hdr_self[__builtin_offsetof(_DashStrHdr, self) == 8 ? 1 : -1];
typedef char _dl_str_key[_DASH_STR_KEY == 0xDA5C7E57UL ? 1 : -1];
void dl_str_lit(STRPTR t) {
    _DashStrHdr *h = _DASH_STR_HDR(t);
    ULONG n = strlen((const char *)t);
    h->size = (sizeof(_DashStrHdr) + n + 1) | _DASH_STR_TAG | _DASH_STR_KEEP;
    h->len = n;
    h->self = (ULONG)h + _DASH_STR_KEY;
}
void dl_str_forget(STRPTR s) { (void)s; }
void dl_str_set(STRPTR *var, STRPTR v) { _dash_str_set(var, v); }
void dl_str_set_copy(STRPTR *var, STRPTR v) { _dash_str_set_copy(var, v); }
void dl_str_free(STRPTR p) { _dash_str_free(p); }
STRPTR dl_str_ret(STRPTR p) { return _dash_str_ret(p); }
STRPTR dl_str_tmpcopy(STRPTR p) { return _dash_str_tmpcopy(p); }
/* lo que devuelve una @extern: un texto de C, quizá en un búfer suyo que reutiliza */
STRPTR dl_str_tmpcopy_c(STRPTR p) { return _dash_str_tmpcopy(p); }
void dl_str_append(STRPTR *var, STRPTR add) { _dash_str_append(var, add); }
STRPTR dl_str_concat(STRPTR a, STRPTR b) { return DashString_concat(a, b); }
STRPTR dl_str_join(LONG n, STRPTR *parts) { return DashString_join(n, parts); }
STRPTR dl_str_from_int(LONG n) { return DashString_from_int(n); }
STRPTR dl_str_from_char(LONG c) { return DashString_from_char((char)c); }
LONG dl_str_len(STRPTR s) { return _dash_str_len(s); }
LONG dl_str_code(STRPTR s, LONG i) { return _dash_str_code(s, i); }
STRPTR dl_str_slice(STRPTR s, LONG a, LONG b) { return DashString_slice(s, a, b); }
LONG dl_str_cmp(STRPTR a, STRPTR b) { return _dash_str_cmp(a, b); }

STRPTR dl_str_from_float(LONG bits) { return DashString_from_float(_dash_l2f(bits)); }

/* ---- objetos con contador ---- */
void *dl_rc_new_obj(LONG size, const _DashType *t) { return _dash_rc_new_obj(size, t); }
void *dl_rc_alloc_obj(LONG size, const _DashType *t) { return _dash_rc_alloc_obj(size, t); }
void dl_retain(void *p) { _dash_retain(p); }
void dl_release(void *p) { _dash_release(p); }
void dl_release_child(void *p) { _dash_release_child(p); }
void dl_hold(void *p) { _dash_hold(p); }
void dl_obj_set(void **var, void *v) { _dash_obj_set(var, v); }
void dl_obj_set_new(void **var, void *v) { _dash_obj_set_new(var, v); }
void *dl_obj_float(void *p) { return _dash_obj_float(p); }
void *dl_obj_lend(void *p) { return _dash_obj_lend(p); }
void *dl_obj_escape(void *p) { return _dash_obj_escape(p); }
STRPTR dl_str_escape(STRPTR p) { return _dash_str_escape(p); }

void *dl_retain_r(void *p) { _dash_retain(p); return p; }
/* un parámetro objeto que la función cambia: una referencia, sin sacar de los temporales uno que lo es (es de quien
   llamó: al soltarla al salir no se libera) */
void *dl_hold_r(void *p) { _dash_hold(p); return p; }
/* var = valor para una lista o un struct, devolviendo lo que queda en var */
void *dl_obj_assign(void *var, void *v) { _dash_obj_set(&var, v); return var; }
void *dl_obj_assign_new(void *var, void *v) { _dash_obj_set_new(&var, v); return var; }

/* ---- diccionarios: clave texto (dl_dict_*) o número (dl_dict_*i) ---- */
DashDict *dl_dict_new(LONG kind) { return DashDict_new(kind); }
DashDict *dl_dict_from(LONG kind, LONG n, STRPTR *k, LONG *v) { return DashDict_from(kind, n, k, v); }
DashDict *dl_dict_fromi(LONG kind, LONG n, LONG *k, LONG *v) { return DashDict_fromi(kind, n, k, v); }
LONG dl_dict_get(DashDict *d, STRPTR k) { return DashDict_get(d, k); }
LONG dl_dict_geti(DashDict *d, LONG k) { return DashDict_geti(d, k); }
LONG dl_dict_get_or(DashDict *d, STRPTR k, LONG v) { return DashDict_get_or(d, k, v); }
LONG dl_dict_get_ori(DashDict *d, LONG k, LONG v) { return DashDict_get_ori(d, k, v); }
void dl_dict_set(DashDict *d, STRPTR k, LONG v) { DashDict_set(d, k, v); }
void dl_dict_seti(DashDict *d, LONG k, LONG v) { DashDict_seti(d, k, v); }
void dl_dict_set_obj(DashDict *d, STRPTR k, void *v) { DashDict_set_obj(d, k, v); }
void dl_dict_set_obji(DashDict *d, LONG k, void *v) { DashDict_set_obji(d, k, v); }
void dl_dict_set_str(DashDict *d, STRPTR k, STRPTR v) { DashDict_set_str(d, k, v); }
void dl_dict_set_stri(DashDict *d, LONG k, STRPTR v) { DashDict_set_stri(d, k, v); }
LONG dl_dict_has(DashDict *d, STRPTR k) { return DashDict_has(d, k) ? 1 : 0; }
LONG dl_dict_hasi(DashDict *d, LONG k) { return DashDict_hasi(d, k) ? 1 : 0; }
void dl_dict_remove(DashDict *d, STRPTR k) { DashDict_remove(d, k); }
void dl_dict_removei(DashDict *d, LONG k) { DashDict_removei(d, k); }
void dl_dict_clear(DashDict *d) { DashDict_clear(d); }
LONG dl_dict_length(DashDict *d) { return DashDict_length(d); }
DashArrayLong *dl_dict_keys(DashDict *d) { return DashDict_keys(d); }

/* ---- listas ---- */
DashArrayLong *dl_arr_create(LONG n) { return DashArray_create(n); }
void dl_arr_insert(DashArrayLong *a, LONG i, LONG v) { DashArray_insert(a, i, v); }
void dl_arr_insert_obj(DashArrayLong *a, LONG i, void *v) { DashArray_insert_obj(a, i, v); }
void dl_arr_insert_str(DashArrayLong *a, LONG i, STRPTR v) { DashArray_insert_str(a, i, v); }
LONG dl_arr_pop(DashArrayLong *a) { return DashArray_pop(a); }
void *dl_arr_pop_obj(DashArrayLong *a) { return DashArray_pop_obj(a); }
STRPTR dl_arr_pop_str(DashArrayLong *a) { return DashArray_pop_str(a); }
void dl_arr_remove(DashArrayLong *a, LONG i) { DashArray_remove(a, i); }
void dl_arr_clear(DashArrayLong *a) { DashArray_clear(a); }
DashArrayLong *dl_arr_from(LONG n, const LONG *v) { return DashArray_from(n, v); }
DashArrayLong *dl_arr_from_new(LONG n, const LONG *v) { return DashArray_from_new(n, v); }
DashArrayLong *dl_arr_own(DashArrayLong *a, LONG kind) { return DashArray_own(a, kind); }
LONG dl_arr_get(DashArrayLong *a, LONG i) { return DashArray_get(a, i); }
void dl_arr_set(DashArrayLong *a, LONG i, LONG v) { DashArray_set(a, i, v); }
void dl_arr_set_obj(DashArrayLong *a, LONG i, void *v) { DashArray_set_obj(a, i, v); }
void dl_arr_set_str(DashArrayLong *a, LONG i, STRPTR v) { DashArray_set_str(a, i, v); }
LONG dl_arr_length(DashArrayLong *a) { return DashArray_length(a); }
DashArrayLong *dl_arr_concat(DashArrayLong *a, DashArrayLong *b) { return DashArray_concat(a, b); }
DashArrayLong *dl_arr_slice(DashArrayLong *a, LONG s, LONG e) { return DashArray_slice(a, s, e); }
void dl_arr_push(DashArrayLong *a, LONG v) { DashArray_push(a, v); }
void dl_arr_push_obj(DashArrayLong *a, void *v) { DashArray_push_obj(a, v); }
void dl_arr_push_str(DashArrayLong *a, STRPTR v) { DashArray_push_str(a, v); }

/* ---- errores ---- */
void dl_fail_at(const char *what, LONG w) { _dash_fail_at(what, w); }

#ifdef DASH_MEMCHECK
/* --memcheck: un campo de nil avisa y sigue (con una zona a cero); al acabar Main, fuera los temporales */
void *dl_mc_nn(void *p) { return _dash_mc_nn(p); }
void dl_tmp_release_all(void) { _dash_tmp_release_f(0); }
#endif

/* ---- Double (dashc): un texto de 16 cifras hexadecimales con sus 8 bytes, para que la variable, el campo
   o el elemento que lo guarda sea dueño de él como de un texto (copias, temporales, liberación). Las
   cuentas, con el float doble de gcc por software, como ./dash. Una caja nil vale 0.0. ---- */
static double dl_dget(STRPTR s)
{
    union { double d; ULONG w[2]; } u;
    int i;
    u.w[0] = u.w[1] = 0;
    if (s)
        for (i = 0; i < 16 && s[i]; i++) {
            UBYTE c = s[i];
            u.w[i >> 3] = u.w[i >> 3] << 4 | (c <= '9' ? c - '0' : c - 'A' + 10);
        }
    return u.d;
}

static STRPTR dl_dbox(double d)
{
    static const char hex[] = "0123456789ABCDEF";
    union { double d; ULONG w[2]; } u;
    STRPTR s = _dash_str_alloc(16, TRUE);
    int i;
    if (!s) return NULL;
    u.d = d;
    for (i = 0; i < 16; i++) s[i] = hex[(u.w[i >> 3] >> (28 - 4 * (i & 7))) & 15];
    s[16] = 0;
    return s;
}

/* a op b: 0 +, 1 -, 2 *, 3 / */
STRPTR dl_d_op(STRPTR a, STRPTR b, LONG op)
{
    double x = dl_dget(a), y = dl_dget(b);
    switch (op) {
    case 0: return dl_dbox(x + y);
    case 1: return dl_dbox(x - y);
    case 2: return dl_dbox(x * y);
    default: return dl_dbox(x / y);
    }
}

STRPTR dl_d_neg(STRPTR a) { return dl_dbox(-dl_dget(a)); }

/* -1, 0 o 1; 2 si alguno es nan (entonces solo != es cierto) */
LONG dl_d_cmp(STRPTR a, STRPTR b)
{
    double x = dl_dget(a), y = dl_dget(b);
    return x < y ? -1 : x > y ? 1 : x == y ? 0 : 2;
}

STRPTR dl_d_from_int(LONG k) { return dl_dbox((double)k); }
STRPTR dl_d_from_float(LONG bits) { union { float f; LONG l; } u; u.l = bits; return dl_dbox((double)u.f); }
STRPTR dl_d_from_str(STRPTR s) { return dl_dbox(_dash_double_from_str(s)); }
LONG dl_d_to_int(STRPTR a) { return (LONG)dl_dget(a); }
LONG dl_d_to_float(STRPTR a) { union { float f; LONG l; } u; u.f = (float)dl_dget(a); return u.l; }
STRPTR dl_d_str(STRPTR a) { return DashString_from_double(dl_dget(a)); }

/* l.sort(f): f(a, b) de dashc (como una de C, con los elementos como LONG: un número, los bits de un Float, un
   texto, una caja de Double, un objeto); boolean: f dice si a va antes que b; si no, da un Int (> 0: después) */
static LONG (*dl_sort_fn)(LONG, LONG);
static LONG dl_sort_bool;
static LONG dl_sort_after(const LONG *a, const LONG *b)
{
    return dl_sort_bool ? dl_sort_fn(*b, *a) != 0 : dl_sort_fn(*a, *b) > 0;
}

void dl_arr_sort(DashArrayLong *arr, APTR fn, LONG boolean)
{
    dl_sort_fn = (LONG (*)(LONG, LONG))fn;
    dl_sort_bool = boolean;
    DashArray_sort(arr, dl_sort_after);
}

/* ---- Fixed: coma fija 16.16 en un LONG, con las funciones de ./dash ---- */
LONG dl_fx_mul(LONG a, LONG b) { return _dash_fx_mul(a, b); }
LONG dl_fx_div(LONG a, LONG b) { return _dash_fx_div(a, b); }
LONG dl_fx_int(LONG a) { return _dash_fx_int(a); }
LONG dl_fx_sqrt(LONG a) { return _dash_fx_sqrt(a); }
LONG dl_fx_sin(LONG a) { return _dash_fx_sin(a); }
LONG dl_fx_cos(LONG a) { return _dash_fx_cos(a); }
STRPTR dl_fx_str(LONG a) { return DashString_from_fixed(a); }
LONG dl_fx_from_float(LONG bits) { union { float f; LONG l; } u; u.l = bits; return (LONG)(u.f * 65536.0f); }
LONG dl_fx_to_float(LONG a) { union { float f; LONG l; } u; u.f = (float)a / 65536.0f; return u.l; }

/* Win.width, height, left, top, title (0-4) de la ventana abierta, o los de su definición; inner_left, inner_top,
   inner_width, inner_height (5-8): lo de dentro de los bordes, 0 sin abrir (como ./dash) */
LONG dl_win_member(struct Window *w, const struct DashWinDesc *d, LONG m)
{
    if (!w) {
        switch (m) {
        case 0: return d->width;
        case 1: return d->height;
        case 2: return d->left;
        case 3: return d->top;
        case 4: return (LONG)d->title;
        default: return 0;
        }
    }
    switch (m) {
    case 0: return w->Width;
    case 1: return w->Height;
    case 2: return w->LeftEdge;
    case 3: return w->TopEdge;
    case 4: return (LONG)w->Title;
    case 5: return (w->Flags & WFLG_GIMMEZEROZERO) ? 0 : w->BorderLeft;
    case 6: return (w->Flags & WFLG_GIMMEZEROZERO) ? 0 : w->BorderTop;
    case 7: return (w->Flags & WFLG_GIMMEZEROZERO) ? w->GZZWidth : w->Width - w->BorderLeft - w->BorderRight;
    default: return (w->Flags & WFLG_GIMMEZEROZERO) ? w->GZZHeight : w->Height - w->BorderTop - w->BorderBottom;
    }
}

#ifdef DASH_MEMCHECK
/* --memcheck: leer un campo weak cuyo objeto ya se liberó es un error (y nil) */
APTR dl_weak_check(APTR p) { return _dash_weak_check(p); }
#endif

/* ---- --perfil (como ./dash --profile, dashweb D23): cada función de Dash pone su número en una pila mientras
   corre (dl_prof_enter/dl_prof_leave, que dashc pone a la entrada y a la salida; las copiadas en línea cuentan
   como la que las contiene) y una interrupción de VBlank (50 veces por segundo en PAL) mira dónde está: la cima
   (tiempo propio) y todas las de la pila (total). Al acabar Main, la tabla, de la más lenta a la más rápida. ---- */
#include <hardware/intbits.h>
#define DL_PROF_DEPTH 256
static STRPTR *dl_prof_names;
static LONG dl_prof_n;
static ULONG *dl_prof_calls, *dl_prof_self, *dl_prof_total;
static UWORD *dl_prof_seen;
static UWORD dl_prof_gen;
static volatile WORD dl_prof_stack[DL_PROF_DEPTH];
static volatile LONG dl_prof_depth;
static volatile ULONG dl_prof_samples;
static struct Interrupt dl_prof_int;
static BOOL dl_prof_on;

static ULONG dl_prof_tick(void)
{
    LONG d = dl_prof_depth, i;
    WORD id;
    if (d > DL_PROF_DEPTH) d = DL_PROF_DEPTH;
    dl_prof_samples++;
    dl_prof_gen++;
    dl_prof_total[0]++;
    if (d == 0) dl_prof_self[0]++;
    else dl_prof_self[dl_prof_stack[d - 1]]++;
    for (i = 0; i < d; i++) {
        id = dl_prof_stack[i];
        if (dl_prof_seen[id] != dl_prof_gen) {
            dl_prof_seen[id] = dl_prof_gen;
            dl_prof_total[id]++;
        }
    }
    return 0;
}

/* names: los nombres (0 es Main), n cuántos */
void dl_prof_start(STRPTR *names, LONG n)
{
    ULONG *p = AllocVec((ULONG)n * 14, MEMF_CLEAR);
    if (!p) return;
    dl_prof_names = names;
    dl_prof_n = n;
    dl_prof_calls = p;
    dl_prof_self = p + n;
    dl_prof_total = p + 2 * n;
    dl_prof_seen = (UWORD *)(p + 3 * n);
    dl_prof_calls[0] = 1;
    dl_prof_int.is_Node.ln_Type = NT_INTERRUPT;
    dl_prof_int.is_Node.ln_Pri = -60;
    dl_prof_int.is_Node.ln_Name = (char *)"dash profiler";
    dl_prof_int.is_Data = NULL;
    dl_prof_int.is_Code = (VOID (*)())dl_prof_tick;
    AddIntServer(INTB_VERTB, &dl_prof_int);
    dl_prof_on = TRUE;
}

void dl_prof_enter(LONG id)
{
    if (!dl_prof_on) return;
    dl_prof_calls[id]++;
    if (dl_prof_depth < DL_PROF_DEPTH) dl_prof_stack[dl_prof_depth] = (WORD)id;
    dl_prof_depth++;
}

void dl_prof_leave(void)
{
    if (dl_prof_depth > 0) dl_prof_depth--;
}

void dl_prof_report(void)
{
    LONG i, j, best, n = dl_prof_n;
    ULONG s, args[6];
    UBYTE *done;
    if (!dl_prof_on) return;
    RemIntServer(INTB_VERTB, &dl_prof_int);
    dl_prof_on = FALSE;
    if (!(done = AllocVec((ULONG)n, MEMF_CLEAR))) return;
    s = dl_prof_samples ? dl_prof_samples : 1;
    args[0] = dl_prof_samples;
    VPrintf((CONST_STRPTR)"perfil: %lu muestras (VBlank)\n", (APTR)args);
    PutStr((CONST_STRPTR)"perfil:  propio   total  llamadas  funcion\n");
    for (i = 0; i < n; i++) {
        best = -1;
        for (j = 0; j < n; j++)
            if (!done[j] && (best < 0 || dl_prof_self[j] > dl_prof_self[best]
                             || (dl_prof_self[j] == dl_prof_self[best] && dl_prof_total[j] > dl_prof_total[best])))
                best = j;
        if (best < 0) break;
        done[best] = 1;
        if (!dl_prof_calls[best] && !dl_prof_total[best]) continue;
        args[0] = dl_prof_self[best] * 100 / s;
        args[1] = dl_prof_self[best] * 1000 / s % 10;
        args[2] = dl_prof_total[best] * 100 / s;
        args[3] = dl_prof_total[best] * 1000 / s % 10;
        args[4] = dl_prof_calls[best];
        args[5] = (ULONG)dl_prof_names[best];
        VPrintf((CONST_STRPTR)"perfil: %3ld.%ld%% %3ld.%ld%% %9lu  %s\n", (APTR)args);
    }
    FreeVec(done);
}

/* ---- diccionarios con una clave literal: su hash (_dash_dict_hash) lo calcula dashc al compilar (como hace gcc en
   el C de ./dash con un literal) ---- */
static LONG dl_dict_slot_h(DashDict *d, STRPTR key, ULONG h)
{
    ULONG mask = d->cap - 1, i = h & mask;
    while (d->keys[i] && strcmp((char *)d->keys[i], (char *)key)) i = (i + 1) & mask;
    return (LONG)i;
}

LONG dl_dict_get_h(DashDict *d, STRPTR k, ULONG h)
{
    LONG s;
    if (!d || !d->cap) return 0;
    s = dl_dict_slot_h(d, k, h);
    return d->keys[s] ? d->vals[s] : 0;
}

LONG dl_dict_get_or_h(DashDict *d, STRPTR k, LONG v, ULONG h)
{
    LONG s;
    if (!d || !d->cap) return v;
    s = dl_dict_slot_h(d, k, h);
    return d->keys[s] ? d->vals[s] : v;
}

LONG dl_dict_has_h(DashDict *d, STRPTR k, ULONG h)
{
    return d && d->cap && d->keys[dl_dict_slot_h(d, k, h)] != NULL;
}
