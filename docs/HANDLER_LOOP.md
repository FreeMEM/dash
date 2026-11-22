# Handlers de DOS con Dash: plan y bitácora

Idea del usuario (2026-11-22). Dos fases, en orden:

1. **Modo handler de Dash** (este repo, rama `dash-handler`): escribir con Dash un handler de DOS (un sistema de
   archivos) de AmigaOS 3.x, por los dos caminos (`./dash` y `./dash --gcc`).
2. **Handler de DashFS de solo lectura**, escrito en Dash con ese modo (repo local `~/Projects/dashfs-amiga`): lee
   discos DashFS hechos en Linux (formato en `~/Projects/dashos/archivos/redoxfs`, `docs/ARCHIVOS_LOOP.md` y
   `docs/diseño/S5-archivos.md` de DashOS). 68020+ con 8 MB, sin cifrado.

## Por qué hoy no se puede

- El arranque (libnix por `--gcc`, `_dash_init` en el directo) toma el mensaje de arranque de DOS por un
  `WBStartup`: abre una consola y al acabar lo devuelve otra vez.
- `Print` y los errores van a `Output()`, que en un handler es 0; sin consola, un error saca un requester.
- Un handler que llama al DOS sobre su propio volumen se bloquea (espera a sí mismo). Peor: el DOS espera la
  respuesta de sus paquetes en `pr_MsgPort`, y si los paquetes de los clientes llegan ahí también, una llamada al
  DOS se come el paquete de un cliente como si fuera su respuesta.
- No hay órdenes para el bucle de paquetes ni para BPTR/BSTR.

## Diseño

- **Modo:** `./dash --handler` (y `--gcc --handler`) o la directiva `@handler` en el programa (la pone
  `lib/amiga/handler.dash`: importarlo ya es pedir el modo).
- **Arranque:** el mensaje que llega a `pr_MsgPort` es el paquete de arranque (`ln_Name` = el `DosPacket`):
  `dp_Arg1` el nombre (BSTR), `dp_Arg2` `dn_Startup` (la `FileSysStartupMsg` con `Device=`), `dp_Arg3` el
  `DeviceNode`. Por `--gcc`, un `__nocommandline` vacío (sin la consola de libnix) y `_WBenchMsg` a 0 al empezar
  `main`; en el directo, `_dash_init` se lo pasa a `_dash_hd_begin` (puntero débil) si el programa puso
  `_dash_hd_on`.
- **Puerto propio:** los paquetes llegan a un puerto nuevo (`dn_Task` apunta ahí desde el arranque), no a
  `pr_MsgPort`: así el handler puede usar el DOS con otros volúmenes (un registro en `T:`, una imagen de disco).
- **Salida:** `Output()` es `NIL:` hasta que `handler_log(ruta)` abre un registro; `handler_wait` vacía el búfer
  antes de esperar. Un error de ejecución va al registro; sin registro, a un requester (el handler muere: que se
  vea).
- **Al acabar** (bien, con error o con Ctrl-C): en `Forbid`, `dn_Task` y los `dl_Task` de sus volúmenes a 0, los
  paquetes que quedan se contestan con error, y `dn_SegList` a 0 para que el DOS cargue una copia limpia en el
  siguiente acceso (los globales de esta ya no valen). El código viejo queda en memoria: no se puede descargar
  desde dentro.
- **Builtins** (una sola implementación en C, en `compiler/codegen.py`, que el directo toma con `gen_lib.py`):
  `handler_startup`, `handler_name`, `handler_devnode`, `handler_port`, `handler_ready`, `handler_wait`,
  `handler_poll`, `packet_reply`, `handler_log`, `handler_volume_add`, `handler_volume_remove`, `bstr_text`,
  `bstr_put`, `dev_open`, `dev_close`, `dev_read`, `dev_write`, `dev_cmd`.
- **`lib/amiga/handler.dash`:** las estructuras con `@amiga struct` (DosPacket, FileLock, FileInfoBlock,
  InfoData, DeviceNode, FileSysStartupMsg, DosEnvec), las constantes `ACTION_*` y `ERROR_*`, y ayudas en Dash
  (cerraduras, rellenar un FileInfoBlock, fechas).
- **Aviso al compilar:** en modo handler, las funciones de ficheros de Dash (file_*, dir_*...) piden al DOS: si
  la ruta es del propio handler, se bloquea.

## Pruebas

- Ejemplo: `examples/handler_ram.dash`, un sistema de archivos mínimo en memoria (una carpeta, leer y escribir).
- Runner: `# emu-handler: <fichero.dash> <NOMBRE:> [Device=... Unit=...]` compila el handler (por el mismo
  camino que el test), lo monta con `C:Mount` antes de los programas y el test es un cliente normal que lo usa.
  Sin `C:Mount` en el sistema emulado, el test se salta.

## Bitácora

- 2026-11-22: arranque. Worktree `.worktrees/dash-handler` desde main 1512fd1.
