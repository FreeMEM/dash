/* Runtime mínimo de la prueba de dashc: se compila una vez con gcc (make runtime)
   y dashc lo lleva dentro. Los usuarios de dashc no necesitan gcc. */
#include <exec/types.h>
#include <exec/execbase.h>
#include <dos/dos.h>
#include <devices/timer.h>
#include <proto/exec.h>
#include <proto/dos.h>
#include <proto/timer.h>

struct ExecBase *SysBase;
struct DosLibrary *DOSBase;
struct Device *TimerBase;
static struct timerequest *bench_tr;
static struct EClockVal bench_t0;
static ULONG bench_freq;

/* 68020 o mejor: rt_math.s usa divs.l y muls.l (como utility.library con gcc) */
UBYTE _dash_cpu020;

/* 0 si todo fue bien; si no, el programa sale con 20 */
LONG _dash_init(void)
{
    SysBase = *(struct ExecBase **)4;
    _dash_cpu020 = (SysBase->AttnFlags & AFF_68020) != 0;
    DOSBase = (struct DosLibrary *)OpenLibrary((CONST_STRPTR)"dos.library", 37);
    return DOSBase ? 0 : 20;
}

void _dash_exit(void)
{
    if (TimerBase) {
        struct MsgPort *port = bench_tr->tr_node.io_Message.mn_ReplyPort;
        CloseDevice((struct IORequest *)bench_tr);
        DeleteIORequest((struct IORequest *)bench_tr);
        DeleteMsgPort(port);
    }
    if (DOSBase) CloseLibrary((struct Library *)DOSBase);
}

void _dash_print_str(const char *s)
{
    PutStr((CONST_STRPTR)s);
    PutStr((CONST_STRPTR)"\n");
}

void _dash_print_int(LONG v)
{
    VPrintf((CONST_STRPTR)"%ld\n", (APTR)&v);
}

void _dash_print_bool(LONG v)
{
    PutStr((CONST_STRPTR)(v ? "true\n" : "false\n"));
}

/* rt_math.s salta aquí con un divisor 0. Prueba: sale sin cerrar dos.library. */
void _dash_div_zero(void)
{
    PutStr((CONST_STRPTR)"Error: división por cero\n");
    Exit(20);
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
