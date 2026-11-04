/* C de @link para tests/test_link_api.dash (D82): la API del compilador directo (dl_*, db_nombre), que por C con gcc
   (./dash --gcc) da el propio programa. Sin cabecera generada: los prototipos, aquí */
#include <exec/types.h>
#include <string.h>

typedef struct DashArray DashArray;
LONG dl_arr_length(DashArray *a);
LONG dl_arr_get(DashArray *a, LONG i);
STRPTR dl_str_temp(STRPTR s);
STRPTR dl_str_dup(STRPTR s);
void dl_str_free(STRPTR s);
LONG dl_str_len(STRPTR s);
void dl_str_forget(STRPTR s);
void dl_retain(void *o);
void dl_release(void *o);
LONG db_time_ms(void);
LONG db_str_upper(LONG s);
STRPTR dash_eco(LONG n);            /* @export del programa */

/* la suma de una lista de Int y su largo * 10 */
LONG c_suma_lista(DashArray *l)
{
    LONG i, s = 0;
    for (i = 0; i < dl_arr_length(l); i++) s += dl_arr_get(l, i);
    return s + dl_arr_length(l) * 10;
}

/* un texto de C como temporal de Dash, en mayúsculas por el builtin str_upper */
STRPTR c_grita(STRPTR s)
{
    static char buf[40];
    STRPTR t;
    strcpy(buf, "[");
    strcat(buf, (char *)s);
    strcat(buf, "]");
    dl_str_forget((STRPTR)buf);
    t = dl_str_temp((STRPTR)buf);
    return (STRPTR)db_str_upper((LONG)t);
}

/* una copia de Dash que se suelta: su largo */
LONG c_largo_copia(STRPTR s)
{
    STRPTR c = dl_str_dup(s);
    LONG n = dl_str_len(c);
    dl_str_free(c);
    return n;
}

/* sostener y soltar un objeto (el programa aún lo tiene) */
LONG c_sostiene(void *o)
{
    dl_retain(o);
    dl_release(o);
    return o != 0;
}

/* uno que el C se queda (dl_retain) y suelta más tarde: con memcheck, nada vivo al final */
static void *guardado;
LONG c_guarda(void *o)
{
    dl_retain(o);
    guardado = o;
    return o != 0;
}

void c_suelta(void)
{
    if (guardado) dl_release(guardado);
    guardado = 0;
}

LONG c_reloj(void) { return db_time_ms() >= 0; }

/* C que llama a una @export de Dash */
LONG c_llama_dash(LONG n) { return (LONG)strlen((char *)dash_eco(n)); }
