/* Lo que dashc añade al runtime de ./dash (gen_lib.py lo incluye al final de dashlib_rt.c): las bases
   de las librerías, el arranque y la salida sin libnix, Print, bench_* y, con nombre dl_*, lo que el
   código de dashc llama (en C son static, macros o en línea). Todo se llama como en C: argumentos en la
   pila, resultado en d0. */
#include <devices/timer.h>
#include <proto/timer.h>
#include <proto/graphics.h>

struct ExecBase *SysBase;
struct DosLibrary *DOSBase;
struct IntuitionBase *IntuitionBase;
struct GfxBase *GfxBase;   /* los @native de lib/amiga (en ./dash la abre libnix) */
struct WBStartup *_WBenchMsg;   /* el mensaje del Workbench (libnix); dashc aún arranca solo desde el Shell */
struct Device *TimerBase;
static struct timerequest *bench_tr;
static struct EClockVal bench_t0;
static ULONG bench_freq;

/* 68020 o mejor: rt_math.s usa divs.l y muls.l (como utility.library con gcc) */
UBYTE _dash_cpu020;

/* Desde _dash_start (rt_math.s): 0 si todo fue bien; si no, el código de salida */
LONG _dash_init(void)
{
    SysBase = *(struct ExecBase **)4;
    _dash_cpu020 = (SysBase->AttnFlags & AFF_68020) != 0;
    _dash_trap_on();
    IntuitionBase = (struct IntuitionBase *)OpenLibrary((CONST_STRPTR)"intuition.library", 37);
    DOSBase = (struct DosLibrary *)OpenLibrary((CONST_STRPTR)"dos.library", 37);
    GfxBase = (struct GfxBase *)OpenLibrary((CONST_STRPTR)"graphics.library", 37);
    if (!IntuitionBase || !DOSBase) {
        _dash_exit_cleanup();
        return 10;
    }
    return 0;
}

/* Desde _dash_quit, al acabar de cualquier forma: como el final de main y la lista de salida de libnix */
void _dash_finish(void)
{
    if (TimerBase) {
        struct MsgPort *port = bench_tr->tr_node.io_Message.mn_ReplyPort;
        CloseDevice((struct IORequest *)bench_tr);
        DeleteIORequest((struct IORequest *)bench_tr);
        DeleteMsgPort(port);
        TimerBase = NULL;
    }
    _dash_exit_cleanup();
    _dash_atexit_run();
    if (GfxBase) CloseLibrary((struct Library *)GfxBase);
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
    if (!TimerBase) {
        struct MsgPort *port = CreateMsgPort();
        if (!port) return;
        bench_tr = (struct timerequest *)CreateIORequest(port, sizeof(struct timerequest));
        if (bench_tr && OpenDevice((CONST_STRPTR)TIMERNAME, UNIT_ECLOCK, (struct IORequest *)bench_tr, 0) == 0) {
            TimerBase = bench_tr->tr_node.io_Device;
        } else {
            if (bench_tr) DeleteIORequest((struct IORequest *)bench_tr);
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
    if (!TimerBase) return;
    ReadEClock(&t1);
    args[0] = (ULONG)name;
    args[1] = (ULONG)iterations;
    args[2] = t1.ev_lo - bench_t0.ev_lo;
    args[3] = bench_freq;
    VPrintf((CONST_STRPTR)"BENCH %s %ld %lu %lu\n", (APTR)args);
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
void dl_str_set(STRPTR *var, STRPTR v) { _dash_str_set(var, v); }
void dl_str_set_copy(STRPTR *var, STRPTR v) { _dash_str_set_copy(var, v); }
void dl_str_free(STRPTR p) { _dash_str_free(p); }
STRPTR dl_str_ret(STRPTR p) { return _dash_str_ret(p); }
STRPTR dl_str_tmpcopy(STRPTR p) { return _dash_str_tmpcopy(p); }
void dl_str_append(STRPTR *var, STRPTR add) { _dash_str_append(var, add); }
STRPTR dl_str_concat(STRPTR a, STRPTR b) { return DashString_concat(a, b); }
STRPTR dl_str_join(LONG n, STRPTR *parts) { return DashString_join(n, parts); }
STRPTR dl_str_from_int(LONG n) { return DashString_from_int(n); }
STRPTR dl_str_from_char(LONG c) { return DashString_from_char((char)c); }
LONG dl_str_len(STRPTR s) { return _dash_str_len(s); }
LONG dl_str_code(STRPTR s, LONG i) { return _dash_str_code(s, i); }
STRPTR dl_str_slice(STRPTR s, LONG a, LONG b) { return DashString_slice(s, a, b); }
LONG dl_str_cmp(STRPTR a, STRPTR b) { return _dash_str_cmp(a, b); }

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
