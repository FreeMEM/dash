/* Para tests/test_link_grupo.dash (ver grupo_a.c):
     m68k-amigaos-gcc -noixemul -O2 -ffunction-sections -c grupo_b.c && m68k-amigaos-ar rcs libgrupo_b.a grupo_b.o */
#include <exec/types.h>
LONG grupo_b(LONG n) { return n * 2; }
