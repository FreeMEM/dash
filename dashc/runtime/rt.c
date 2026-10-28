/* Runtime mínimo de la prueba de dashc: se compila una vez con gcc (make runtime)
   y dashc lo lleva dentro. Los usuarios de dashc no necesitan gcc. */
#include <exec/types.h>
#include <exec/execbase.h>
#include <dos/dos.h>
#include <proto/exec.h>
#include <proto/dos.h>

struct ExecBase *SysBase;
struct DosLibrary *DOSBase;

/* 0 si todo fue bien; si no, el programa sale con 20 */
LONG _dash_init(void)
{
    SysBase = *(struct ExecBase **)4;
    DOSBase = (struct DosLibrary *)OpenLibrary((CONST_STRPTR)"dos.library", 37);
    return DOSBase ? 0 : 20;
}

void _dash_exit(void)
{
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
