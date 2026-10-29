/* C de fuera para tests/externo.dash (@link y @extern): se compila una vez con el gcc de Amiga
     m68k-amigaos-gcc -O2 -fomit-frame-pointer -c tests/c/externo.c -o tests/c/externo.o
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
