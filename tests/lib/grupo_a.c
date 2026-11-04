/* Para tests/test_link_grupo.dash: una librería que llama a otra (grupo_b, de libgrupo_b.a) y que lleva una función
   que el programa no usa y que llama a algo que no existe. Se compila con -ffunction-sections:
     m68k-amigaos-gcc -noixemul -O2 -ffunction-sections -c grupo_a.c && m68k-amigaos-ar rcs libgrupo_a.a grupo_a.o */
#include <exec/types.h>
LONG grupo_b(LONG n);
LONG no_existe(void);
LONG grupo_a(LONG n) { return grupo_b(n) + 1; }
LONG grupo_a_sin_usar(void) { return no_existe(); }
