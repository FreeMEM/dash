# La ayuda de Dash, y DashOS

- **Mayúsculas+F1** sobre un nombre (`file_seek`, `mui_window_begin`, `if`, `struct`...) abre su ficha en la vista
  de ayuda: firma, parámetros, texto, ejemplo, "ver también" y si está en DashOS. Es la misma ayuda que la de Forja
  en el Amiga (`tools/gen_ayuda.py` de Dash). **Dash: Buscar en la ayuda** busca por palabras.
- **Probar** abre el ejemplo de la ficha en un fichero y lo ejecuta en el Amiga emulado; **Probar en DashOS**, en
  QEMU.
- Al pasar el ratón por una función de Dash se ven sus parámetros, si está en DashOS y un enlace a su ficha.
- **DashOS** sobre `Main` (o **Dash: Ejecutar en DashOS**) compila el programa con `./dash --dashos` y lo ejecuta en
  el PC con QEMU (`qemu-aarch64`); su salida sale en el panel. Hace falta `qemu-user`, `clang` y `lld`. En QEMU no hay
  compositor: las ventanas no se ven.
