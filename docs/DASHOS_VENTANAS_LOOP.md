# Ventanas de Dash en DashOS (plan y bitácora)

Que los programas de Dash con ventana (las funciones `mui_*`) funcionen en DashOS nativo (`./dash --dashos`), para
escribir en Dash un editor de catálogos para `SYS:Utilities` de DashOS. Plan aprobado por la sesión que lleva DashOS
(geosian-7d). Rama `dashos-ventanas` (este worktree); en DashOS, rama `dash-ventanas` en
`~/Projects/dashos/.worktrees/dash-ventanas`.

## Decisiones

- **kit-c** (DashOS, `kit-c/`, MPL-2.0): el kit de DashOS (`kit/`, Material 3) con ABI de C, como `staticlib`
  (`libkit_c.a`). Por dentro, el kit, `wayland` y el cliente del compositor de los programas nativos
  (`usuario/src/ventana_cliente.rs`), y el crate `dashos` para las llamadas. Su montón es el `malloc`/`free` del runtime
  de Dash; sin `programa!` ni `monton!`. Cabecera: `kit-c/include/kit_c.h`. Objetivo `aarch64-unknown-none` (con la
  FPU, como el programa de Dash) y código PIC (sirve fijo y con `--pie`).
- `make -C kernel kit-c` (DashOS) deja `build/libkit_c.a`, con el `memcpy` de la biblioteca `dashos` débil (manda el de
  `plat.c`). `tools/dashos_run.py` lo busca en `$DASH_KIT_C`, `$DASHOS_DIR/build` (de serie `~/Projects/dashos`) o
  `$DASHOS_DIR/kit-c/target/...`, y lo enlaza solo si el programa usa `mui_*` (con `--undefined-glob=dash_ui_*`: en el
  runtime las `dash_ui_*` son débiles) y con 256 KB de pila.
- En Dash, con `--dashos`, las `mui_*` de `DASHOS_MUI` (`compiler/amiga_builtins.py`) van a `DASHOS_MUI_RUNTIME`
  (`compiler/codegen.py`), que llama a `dash_ui_*`. El resto de `mui_*` es un error al compilar: por C "'mui_x' is not
  in DashOS yet", por el directo "mui_x aún no está en DashOS" (byte `dashos` = 2 en `BuiltinInfo`).
- El compositor, por la llave 3 (la de lo que lanza `sesiones`: 1 su canal, 2 archivos, 3 ventanas);
  `dash_ui_usar_llave` cambia eso.
- **Aspecto** (Material 3, lo del kit):
  - Una etiqueta (`mui_label`) seguida de un campo, un desplegable o una casilla en el mismo grupo pasa a ser la
    etiqueta de ese control (la flotante de Material). Detrás de una casilla sin etiqueta, también.
  - Los códigos de MUI (`\33c`, `\33b`...) y el subrayado de la tecla (`_Guardar`) no se ven.
  - Ventana con 24 de margen y esquinas de 8, como un diálogo; mide lo que pide su contenido (al menos 280 de ancho).
  - `mui_request`: un diálogo de Material 3 (título, texto, botones al final de la fila; el primero relleno).
  - **Los menús, provisionales**: una fila arriba con un botón de texto por menú, que abre su menú (el de los
    desplegables del kit). S10 y S11 quieren los menús en la barra de la pantalla con el botón derecho, y aún no hay
    protocolo para eso. Las rayas (`mui_menu_separator`) no se ven; una opción desactivada se ve igual y no hace nada.
    Las teclas de los menús (Amiga+tecla) aún no.
- Catálogos (`tr`, `@catalog`, `catalog_open`, `catalog_language`) en DashOS: el mismo lector del IFF CTLG, con el
  fichero por `dash_plat_file_load` (`runtime/dashos/plat.c`) y los idiomas por `_dash_dashos_languages`: lee
  `ENV:Sys/locale.prefs` como locale.library (LCLE: 16 bytes, país en 32 y 10 idiomas de 30); sin él,
  `$DASH_LANGUAGE` (en Linux) o "español". Los textos de DashOS son UTF-8: un catálogo con CSET 106 (como AmigaOS 4)
  va tal cual; uno del Amiga (Latin-1) se pasa a UTF-8. `tools/catalogo.py catalog --utf8` hace los de DashOS.
- Ficheros en DashOS (fase 2): `runtime/dashos/dos.c` (incluido al final de `plat.c`) pone lo de dos.library que usa
  el runtime (Open, Read, Write, Seek, FGetC, FGets, Lock, Examine, ExNext, CreateDir, DeleteFile, Rename,
  SetProtection, SetComment...) sobre el servicio "archivos" (llave 2) o, en Linux (qemu), sobre sus llamadas. Así
  valen por los dos caminos todos los `file_*` y `dir_*` menos los avisos de cambios (`file_notify`) y
  `file_real_path`. Un fichero abierto lleva un búfer de 4 KB; su número va en memoria de búferes (por debajo de 2 GB:
  `file_open` lo da a un Int). Nombres (provisional, hasta que el runtime lea las asignaciones de DashOS, ya en
  `revision`): `SYS:` y `PROGDIR:` son la raíz del cliente, `LOCALE:` su cajón `Locale`, sin volumen desde el cajón
  actual. En Linux, `X:` es `$DASH_X_DIR` (`tests/dashos_tests.py` da a cada test su cajón con `RAM`, `T` y `ENV`);
  sin ella, `LOCALE:` es `Locale` y `SYS:`/`PROGDIR:` el cajón actual. El comentario, en Linux, en el atributo
  `user.amiga.comment`. La fecha no se cambia en DashOS (el servicio no tiene orden).
- El selector de ficheros (`file_open_dialog`, `file_save_dialog`, `dialog_file`, `dialog_file_at`; en DashOS,
  `DASHOS_ASL_RUNTIME`, sin asl ni GadTools): para abrir, el usuario elige un fichero que el selector cede como asa y
  el programa lee como `Elegido:` (el nombre no llega: el selector solo da la asa); para guardar, una carpeta, que cede
  como raíz 3 y es `Carpeta:` (el fichero, el de `dialog_file_at` o "Sin título"). El servicio no deja ceder otra raíz
  3: la carpeta se elige una vez por ejecución.
- Qué es cada llave lo sabe el runtime por cuántas trae el programa (DashOS no lo dice): 3, lo de `sesiones` (1 su
  canal, 2 archivos, 3 ventanas); 2, lo de `inicio` (1 ventanas, 2 archivos); 4, la prueba `dash-ventana` (1 ventanas,
  2 archivos, 3 sesiones, 4 selector: `inicio` da los canales en el orden de su lista, no en el del programa).
  `sesiones` aún no reparte el selector: un programa lanzado por él no lo tiene (el diálogo da false).

## Bitácora

- 2026-11-15: kit-c (ventana, grupos, texto, etiqueta, botón, campo, casilla, desplegable, lista, menús, eventos,
  `mui_request`, `mui_wait_event`) y las `mui_*` del subconjunto en los dos caminos. Error claro para las demás.
  `kit-c/pruebas/ventana.dash` (DashOS) compila por los dos caminos. Catálogos en DashOS por los dos caminos:
  `tests/test_catalog.dash` (Latin-1, english) y `tests/dashos/test_dashos_catalogo.dash` (UTF-8, castellano de
  serie) pasan en qemu-aarch64.
- 2026-11-15: en DashOS la salida de `Print` sale por líneas (antes, solo en Linux): la de un programa con ventana no
  salía hasta acabar. La llave del compositor la decide `plat.c` al nacer el programa (`dash_plat_windows_key`: 3 si
  traía tres llaves, si no 1) y el runtime se la da a kit-c: el catálogo crea un canal antes de la ventana y kit-c,
  mirando entonces, tomaba la llave 3 de ese canal. En qemu, sin regresiones: por C 114 de 377 (`origin/main`: 112),
  por el directo 101 (99); los dos nuevos son los de catálogos. 68k idéntico: 2904/2904 y 484/484. Tests 636/636.
- 2026-11-15, se para aquí (reinicio de la máquina). `make arranque-virt` de DashOS (rama `dash-ventanas`, duodécima
  vuelta): todas las líneas de `arranque_virt.txt` salieron, también las de `dash-ventana` (catálogo en castellano,
  ventana abierta, clic en "Añadir": "pulsado: Pulsado 1 veces; líneas: 2", fin). Solo faltó la parte del reinicio,
  porque se paró QEMU a mano en ella. Lecciones de la prueba: el programa va al final de `inicio` (antes, su ventana
  cambiaba la cascada y Ajustes tapaba el botón de cerrar de la ventana Amiga), espera 20 s antes de abrir la ventana
  (si sale mientras el guion teclea en el centro de control, se lleva el teclado), el guion la trae delante con un clic
  en su margen antes de pulsar el botón, reintenta si una pregunta de `guardian` lo tapa, y el programa acaba tras el
  clic (delante taparía otras ventanas).

- 2026-11-15, tras el reinicio: `make arranque-virt` entero (también el reinicio) y `make prueba` de DashOS, bien; solo
  falló `captura_cambio.py` (U6): la captura de la ventana de Ana se hizo con la sesión bloqueada (carrera del guion,
  no de Dash). Fase 2: ficheros (`runtime/dashos/dos.c`) y selector. `mui_request` probado en pantalla (captura
  `target/dash-nativo-pregunta.ppm` de DashOS: título, texto y los dos botones de Material 3; el clic en "Guardar"
  da 1). En QEMU, `dash-ventana` guarda su lista en su cajón, hace un cajón, la mueve, lo lista, la lee (por líneas y
  entera) y lo borra todo, por el servicio de archivos. Lección: la ventana de la sesión de archivos se proyecta para
  escribir (3; con 1, escribir en ella tumbaba el programa). En qemu-aarch64, `tests/dashos/test_dashos_ficheros.dash`
  y 8 tests de ficheros más pasan: por C 123 de 377 (antes 114), por el directo 111 (antes 101), sin perder ninguno.
  `test_inflate_auto`, por el directo, ahora enlaza y cae (antes no enlazaba: le faltaba `str_to_buffer`); lo suyo es
  un `Pointer` de 64 bits que llega de un búfer de 32, no los ficheros. `test_utf8` queda fuera en DashOS (sus
  literales son Latin-1; el de DashOS es `tests/dashos/test_utf8.dash`). Tests 636/636; el runtime del 68000, igual
  (solo cambiaba la fecha de compilación).

### Qué toca después

1. Los menús en la barra de la pantalla (S10) cuando haya protocolo; hoy, fila dentro de la ventana (decisión del
   usuario pendiente).
2. Que `sesiones` reparta el selector (DashOS): sin él, el editor de catálogos lanzado desde el disco no puede abrir
   ni guardar con diálogo. Y que el selector diga el nombre de lo elegido y deje escribir el de lo que se guarda.
3. Las asignaciones de DashOS (ya en `revision`: `dashos::asignaciones`, la tabla que da `sesiones`): `ENV:`, `RAM:`,
   `LOCALE:` de verdad. Solo cambia `dos_volumen` de `runtime/dashos/dos.c`.
4. `file_notify` y `file_real_path` en DashOS.
