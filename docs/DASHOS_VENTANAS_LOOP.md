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
- Ficheros en DashOS (provisional, hasta las asignaciones de DashOS, rama `asignaciones`): por el servicio "archivos"
  (llave 2), desde la raíz del cliente; `SYS:` es ella y `LOCALE:` su cajón `Locale`. En Linux (qemu), `LOCALE:` es
  `$DASH_LOCALE_DIR` (de serie `Locale`), `ENV:` `$DASH_ENV_DIR` y `PROGDIR:` el cajón actual.

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
