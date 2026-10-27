# fdlibm

Las funciones matemáticas de Sun (fdlibm 5.3), tal como las trae GNU Classpath
(`libjava/classpath/native/fdlibm` en las fuentes de GCC 6 del toolchain de bebbo), copiadas de
`third_party/fdlibm` de Tachyon. Licencia: la de Sun que va en cada fichero ("Permission to use, copy,
modify, and distribute this software is freely granted, provided that this notice is preserved").

Cambios de Tachyon: sin `mprec.h` (es de `strtod`/`dtoa`); `fdlibm.h` incluye `<stdint.h>` en su lugar y
`config.h` está vacío. Big-endian (68k) sin definir nada.

Cambios de Dash (Lorraine D4): solo los ficheros que usan las funciones de Double (`sqrt`, `pow`, `exp`,
`log`, `log10`, trigonométricas, `floor`, `ceil`, `fmod`), sin los envoltorios `w_*.c` (el runtime llama a
`__ieee754_*`). `namespace.h` pone el prefijo `dash_fd_` a los nombres públicos (`sin`, `floor`...), para
que no choquen con los de `-lm` ni con los de un programa.

`compiler/clibs.py` lo compila una vez por cada juego de opciones de CPU (con `--fpu`, las cuentas van por la
FPU) y `./dash` y el runner lo enlazan cuando un programa usa una de esas funciones.
