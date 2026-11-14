/* C de fuera para tests/externo.dash (@link y @extern): se compila una vez con el gcc de Amiga
     m68k-amigaos-gcc -noixemul -O2 -fomit-frame-pointer -c tests/c/externo.c -o tests/c/externo.o
   y dashc enlaza el objeto (va en git: dashc no necesita gcc). */
#include <string.h>

static long cuenta;            /* (un estático de datos) */
long contador;                 /* (un común: sin -fno-common) */

long ext_suma(long a, long b) { return a + b; }

long ext_largo(const char *s) { return (long)strlen(s); }

const char *ext_saludo(void) { return "hola desde C"; }

long ext_es_par(long n) { return (n & 1) ? 0 : 4; }   /* (un BOOL de C distinto de 1) */

void ext_contar(void) { cuenta++; contador += 10; }

long ext_cuenta(void) { return cuenta * 1000 + contador; }

/* lo de libc y libm de rt_compat.c (con gcc, el de libnix) */
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>

static char buf[160];

const char *ext_formato(long n)
{
    long long g = (long long)n * 1000000007LL;
    snprintf(buf, sizeof buf, "[%05ld|%-4s|%x|%lld|%.3s|%*d|%c|%+d|%u]", n, "ab", (unsigned)n, g, "abcdef", 4, 7, 'z',
             (int)n, (unsigned)n);
    return buf;
}

/* sprintf (no snprintf): precisión, anchura con * y l (el de dashc no sabía la precisión: D16) */
const char *ext_sprintf(long n)
{
    sprintf(buf, "<%.3s|%6.2s|%-4ld|%*s|%05lu|%.60s>", "abcdef", "xyz", n, 3, "q", (unsigned long)n, "fin");
    return buf;
}

long ext_crece(long n)
{
    long i, s = 0;
    long *v = NULL;
    for (i = 1; i <= n; i++) {
        v = (long *)realloc(v, i * sizeof(long));
        v[i - 1] = i;
    }
    for (i = 0; i < n; i++) s += v[i];
    free(v);
    return s;
}

const char *ext_fecha(long t)
{
    time_t tt = (time_t)t;
    struct tm *tm = gmtime(&tt);
    snprintf(buf, sizeof buf, "%04d-%02d-%02d %02d:%02d:%02d %d %d", tm->tm_year + 1900, tm->tm_mon + 1, tm->tm_mday,
             tm->tm_hour, tm->tm_min, tm->tm_sec, tm->tm_wday, tm->tm_yday);
    return buf;
}

long ext_mates(long x)
{
    /* (en enteros: lo que se compara son los resultados) */
    /* (log2 redondeado: el de libnix da 5,999... para 64) */
    return (long)(log2((double)x) * 1000 + 0.5) + (long)round(x / 4.0) * 10 + (long)trunc(-x / 3.0) + lrint(2.5);
}

/* retrollamadas: C llama a una función de Dash (Func) y espera que respete sus registros (d2-d7, a2-a6) */
long ext_aplicar(long (*f)(long), long x) { return f(x) * 10; }

static long tabla[6] = {1, 2, 3, 4, 5, 6};

long ext_sumar_con(long (*f)(long))
{
    long i, s = 0;
    const long *p = tabla;          /* (en un registro mientras se llama a f) */
    for (i = 0; i < 6; i++) s += f(p[i]) + p[i];
    return s;
}

/* malloc y free sin parar (para una tarea y el programa a la vez: el malloc del runtime de dashc lleva semáforo) */
long ext_malloc_vueltas(long n)
{
    long i, j, suma = 0;
    for (i = 0; i < n; i++) {
        long tam = 16 + (i * 37) % 900;
        unsigned char *p = (unsigned char *)malloc(tam);
        if (!p) return -1;
        for (j = 0; j < tam; j++) p[j] = (unsigned char)(i + j);
        for (j = 0; j < tam; j += 7) suma += p[j];
        free(p);
    }
    return suma;
}

/* El FreePooled de exec 40 (Kickstart 3.1) da por vacío un charco si el long tras su MemHeader vale lo que el
   charco: con la memoria libre llena de 0x4000 (lo que dejó otro programa), el charco nuevo del malloc de dashc sale
   de ahí y, sin el arreglo de api.c (dl_pool_sano), un free lo devuelve al sistema con bloques vivos dentro, que el
   malloc siguiente pisa. Los bytes pisados (0 si bien) */
#include <exec/memory.h>
#include <proto/exec.h>
long ext_pool_basura(void)
{
    static ULONG *trozo[64];
    unsigned char *f[8], *g[4];
    long i, k, n, mal = 0;
    for (n = 0; n < 64 && (trozo[n] = (ULONG *)AllocMem(32768, MEMF_ANY)); n++)
        for (k = 0; k < 8192; k++) trozo[n][k] = 0x4000;
    for (i = 0; i < n; i++) FreeMem(trozo[i], 32768);
    /* charcos nuevos de esa memoria (y los pares sueltos: sin el arreglo, el charco se va con los impares dentro) */
    for (i = 0; i < 8; i++) {
        if (!(f[i] = (unsigned char *)malloc(4000))) return -1;
        memset(f[i], 0x5A, 4000);
    }
    for (i = 0; i < 8; i += 2) free(f[i]);
    for (i = 0; i < 4; i++) {
        g[i] = (unsigned char *)malloc(4000);
        if (g[i]) memset(g[i], 0x11, 4000);
    }
    for (i = 1; i < 8; i += 2)
        for (k = 0; k < 4000; k++) if (f[i][k] != 0x5A) mal++;
    for (i = 0; i < 4; i++) free(g[i]);
    for (i = 1; i < 8; i += 2) free(f[i]);
    return mal;
}

/* Muchos malloc y free al azar (de 8 bytes a 12 KB), comprobando el contenido: con el exec 45 de 3.9, el arreglo
   de api.c en su forma primera (el 0 en +32 sin mirar mh_Lower) le rompía el pool y esto se colgaba. Los bytes
   pisados (0 si bien) */
long ext_pool_vueltas(void)
{
    static unsigned char *v[400];
    static unsigned long t[400];
    unsigned long semilla = 12345, j;
    long i, k, mal = 0;
    for (k = 0; k < 20000; k++) {
        semilla = semilla * 1103515245 + 12345;
        i = (long)((semilla >> 8) % 400);
        if (v[i]) {
            for (j = 0; j < t[i]; j += 97) if (v[i][j] != (unsigned char)i) mal++;
            free(v[i]);
            v[i] = 0;
        } else {
            semilla = semilla * 1103515245 + 12345;
            t[i] = ((semilla >> 8) % 7 == 0) ? 4000 + (semilla >> 12) % 8000 : 8 + (semilla >> 12) % 600;
            if (!(v[i] = (unsigned char *)malloc(t[i]))) return -1;
            memset(v[i], (int)i, t[i]);
        }
    }
    for (i = 0; i < 400; i++) if (v[i]) { free(v[i]); v[i] = 0; }
    return mal;
}

/* @export (Dash 2.0): C que llama por su nombre a funciones de Dash del programa */
extern long dash_triple(long x);
extern const char *dash_nombre(long n);
long ext_llama_dash(long x) { return dash_triple(x) + 1; }
long ext_largo_dash(long n) { return (long)strlen(dash_nombre(n)); }

/* @extern con structs (D11j): el puntero de un objeto de Dash, que apunta a su primer campo */
long ext_caja_v(long *c) { return c ? c[0] : -1; }
void *ext_mismo(void *c) { return c; }

/* strtod, strdup y cexp (rt_compat.c; con gcc, los de libnix) */
#include <complex.h>
const char *ext_strtod(const char *s)
{
    char *fin;
    double d = strtod(s, &fin);
    char *c = strdup(s);
    double complex z = cexp(I * 0.0 + 1.0);
    snprintf(buf, sizeof buf, "%ld %ld %ld %ld", (long)(d * 1000.0), (long)(fin - s), (long)strlen(c),
             (long)(creal(z) * 1000.0));
    free(c);
    return buf;
}

/* ctype de libnix (sus macros leen el puntero _ctype_: rt_compat.c lo pone) */
#include <ctype.h>
const char *ext_ctype(const char *s)
{
    long may = 0, dig = 0, i;
    for (i = 0; s[i]; i++) {
        if (isupper((unsigned char)s[i])) may++;
        if (isdigit((unsigned char)s[i])) dig++;
        buf[i] = (char)tolower((unsigned char)s[i]);
    }
    buf[i] = 0;
    snprintf(buf + 100, 50, " %ld %ld", may, dig);
    strcat(buf, buf + 100);
    return buf;
}
