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

## Lo que era

Tachyon (2026-11-12): el 94 % lo vio el monitor de Trasfondo justo tras la caída ("Programs:Network/Tachyon 94.3 %",
con la ventana ya cerrada); en fotos de más tarde el proceso ya no estaba. No es un cuelgue: la salida espera. Tachyon
no pone nada en atexit; sí decodifica las imágenes con `image_decode_start` (prioridad -1), y en las trazas de las
caídas siempre había un `dash_task` en marcha.

3. Medido: en el A1200 emulado (68020), una foto de 1920 x 1080 tarda 8487 tics (170 s) en decodificarse. Con tres
   en marcha y un abort, el programa tardó en salir lo que tardaron las tres: `_dash_task_cleanup` espera a cada
   tarea (`while (!t->done) Delay(1)`) y una decodificación no se podía parar.
4. Además, lo que una tarea decodificó y el programa no recogió con `image_decode_finish` (memoria de exec,
   `AllocVec`) y su trabajo (el nombre del fichero) no se liberaban: la memoria que no volvía.

## Arreglo

- `runtime/imgdec`: `dash_imgdec_stopped` (lo pone la limpieza de Dash). Lo miran TJpgDec (su función de salida
  devuelve 0: `JDR_INTR`), stb_image (los bucles de filas del JPEG base y progresivo, el remuestreo, el inflate y
  las filas del PNG; cambio marcado en `stb_image.h` con `STBI__DASH_STOP()`), WebP (ahora incremental, de 16 KB en
  16 KB con `WebPIUpdate`, mirándolo entre trozos) y la reducción. Una decodificación parada da NULL. Falta SVG y GIF
  (pequeños, de ordinario).
- Codegen (los dos caminos): `_dash_imgdec_stop()` va en la limpieza antes de esperar las tareas; `_DashTask` tiene
  un `drop` que `_dash_task_cleanup` llama para la tarea que nadie recogió: `image_decode_start` libera ahí la
  imagen y su trabajo.
- Test: `tests/test_image_decode_salida.dash` (se lanza a sí mismo: un hijo que acaba con una decodificación a medias
  y otro que acaba sin recoger la imagen).
