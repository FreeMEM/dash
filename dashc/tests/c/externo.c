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
