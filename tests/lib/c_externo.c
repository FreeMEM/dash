/* C from outside for test_c_link (dashweb D10): linked with "@link", not written by Dash */
#include "c_externo.h"

long ext_suma(long a, long b) { return a + b; }

/* calls back the program through a pointer: f(x) * 10 */
long ext_aplicar(long (*f)(long), long x) { return f(x) * 10; }

const char *ext_saludo(void) { return "hola desde C"; }
