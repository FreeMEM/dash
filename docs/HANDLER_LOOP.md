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
- Runner: `# emu-handler: <fichero.dash>` compila el handler por el mismo camino que el test y lo deja en
  `DH0:h_<test>`; el test es un cliente normal que escribe su mountlist, lo monta con `C:Mount` y lo usa.
  `# emu-needs: C/Mount` salta el test si el sistema emulado no tiene Mount. `# emu-hardfile` añade un disco
  crudo (`uaehf.device` unidad 1, 256 bloques de 512 bytes que empiezan por "BLOQ" y su número).
- Tests: `test_handler_ram` (el ejemplo), `test_handler_bloques` (`FileSystem =` con `Device =`, lee bloques),
  `test_handler_falla` (error de ejecución: registro, paquete contestado y copia nueva), cada uno con su `_directo`.

## Fase 2: DashFS de solo lectura

Repo local `~/Projects/dashfs-amiga` (sin subir: espera el sí del usuario).

- `src/dashfs.dash`: el handler (`./dash --cpu 68020`). `src/seahash.dash` (seahash 4.1 en ensamblador del 68020,
  con `mulu.l` de 64 bits) y `src/lz4.dash` (bloques LZ4 en ensamblador del 68000).
- `herramientas/hacer_disco.rs`: discos de prueba con el RedoxFS de DashOS (ruta `../dashos/archivos/redoxfs`):
  tildes, datos en el nodo, LZ4 y sin comprimir, cajones, comentario y bits, 300 ficheros (H-tree de un nivel), un
  cajón que distingue mayúsculas, la instantánea "antes" y el volumen "Otro". `herramientas/lector.py`: lector de
  referencia en Python (y `comprobar.py`, que lo prueba contra el manifiesto). `herramientas/seahash.py`.
- `pruebas/correr.py`: el disco como `uaehf.device` unidad 1 de FS-UAE, el handler montado tres veces (ahora,
  `INSTANTANEA=antes`, `VOLUMEN=Otro`) y un cliente que lo recorre todo y saca tamaños y sumas.
- Opciones por `Control =` de la mountlist (`dn_Startup` es la FileSysStartupMsg): `VOLUMEN=`, `INSTANTANEA=`,
  `NOMBRE=`, `SINSUMAS`, `LOG=`.
- Formato (visto en el código de RedoxFS de DashOS): cabeceras en un anillo de 256 bloques de 4 KB al principio (la
  buena es la de generación mayor con su suma bien); BlockPtr de 16 bytes (dirección: nivel 4 bits, nivel
  descomprimido 4, índice 36, época 20; y la seahash de lo guardado); árbol de nodos de 4 niveles de TreeList (254
  punteros); nodo de 4 KB (modo, tamaños, tiempos, record_level, flags INLINE_DATA y CASEFOLD, bits del Amiga,
  atributos; desde el byte 128, 128 registros directos y listas de 1 a 4 niveles, o los datos en línea); carpetas con
  la marca en level0[0] (niveles del H-tree) y la raíz en level0[1]; DirList: entradas de 4 bytes de nodo, 1 de largo
  y el nombre en UTF-8, cuenta en 4092; registros comprimidos con 2 bytes de largo y LZ4.

## Bitácora

- 2026-11-22: arranque. Worktree `.worktrees/dash-handler` desde main 1512fd1.
- 2026-11-22: fase 1 hecha en la rama (12 tests de handlers en el emulador, 801/801 sin emulador). Fallos
  encontrados por el camino: `--gcc` perdía los `@amiga struct` de un módulo importado (arreglado); contestar con
  `ERROR_DEVICE_NOT_MOUNTED` al morir dejaba al cliente ante un requester (ahora `ERROR_OBJECT_NOT_FOUND`); un
  `MODE_NEWFILE` dejaba el registro bloqueado para los demás (ahora se abre compartido).
- 2026-11-22: fase 2 empezada. seahash y LZ4 en ensamblador comprobados en el A1200 emulado contra la referencia
  (un registro de 128 KB de un disco real: 240 ms). El lector de Python lee todo el disco de prueba sin fallos.
