# Limpieza tras un fallo (bitácora)

Encargo del usuario (2026-11-12): averiguar qué deja colgada la limpieza de un programa Dash tras un fallo. El caso
es Tachyon: un assert de QuickJS llama a abort, el programa sale con exit(127) y, según Tachyon, se queda al 94 % de
CPU sin devolver la memoria. Rama `limpieza-fallo`, worktree `.worktrees/limpieza-fallo`.

## Orden de la limpieza (./dash)

`_dash_quit` → `_dash_finish` (api.c): vaciar la salida, `dl_close_windows`, `_dash_exit_cleanup`, la lista de
atexit, librerías y `dl_malloc_fin` (el pool). `_dash_exit_cleanup` (sale de codegen con gen_lib.py) llama en este
orden: escritorio, CPU, input, memcheck, AppWindow, commodities, red de fondo (`_dash_netbg_cleanup`), runcap,
tareas (`_dash_task_cleanup`, que espera sin límite), ventanas, gadgets, bitmaps, copper, música, sonido, ReAction,
MUI (`_dash_mui_app_end`), teclas... TLS, red y fontweb.

## Pruebas

1. Programa pequeño con `abort()` (por `./dash --gcc`, `@native`), con y sin ventana MUI: TIMEOUT en
   `tools/emu_run.py`. Falsa alarma: el arranque del emulador tenía `FailAt 21` y abort sale con 127, así que el
   guion se paraba y el siguiente programa no corría. Arreglado: `FailAt 1000000` en `tools/emu_run.py` y en
   `tools/coffin/disco.py`. Con eso, RC 127 y el siguiente programa corre.
2. Por `./dash` con el abort en C de `@link` (objeto de gcc), con ventana MUI y con una conexión de `net_bg`
   pendiente: RC 20, sale bien. El abort de `rt_compat.c` sale con 20; el de libnix (`./dash --gcc`), con 127.

Así que el cuelgue de Tachyon depende de algo más que MUI y la red de fondo.
