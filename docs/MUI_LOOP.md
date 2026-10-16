# Soporte de MUI 5 en Dash (para `/loop`)

Arranque:

```
/loop Sigue las instrucciones de docs/MUI_LOOP.md: haz UNA tarea y actualiza la bitácora. No hagas pausas entre vuelta y vuelta
```

## Objetivo

Tres partes: MUI 5 (tareas 1-11); terminar, mejorar, optimizar y corregir ReAction y GadTools (12-18);
y un editor visual de MUI como complemento de VS Code (19-24).

Que Dash pueda hacer programas con interfaz MUI 5, la que usará el navegador `dashweb`
(`~/Projects/dashweb`, decisión del usuario del 2026-10-15). Hoy Dash solo tiene GadTools y ReAction.

El navegador necesitará, además de lo básico (ventana, grupos, botones, campo de texto):
listas, menús, pestañas, barra de progreso, barra de estado, varias ventanas, una zona de dibujo
propia con scroll (donde se pintará la página), imágenes y un bucle de eventos que también atienda
otras señales (red, temporizador). El plan va en ese orden.

## Datos de partida (comprobados el 2026-10-15)

- **SDK:** MUI 5.0-20210831, del GitHub oficial `amiga-mui/muidev` (es la última versión publicada):
  `https://github.com/amiga-mui/muidev/releases/download/MUI-5.0-20210831/MUI-5.0-20210831-os3.lha`.
  Trae el usuario (`MUI/`, con `Libs/muimaster.library` y `Libs/mui/*.mui|mcc`) y el SDK
  (`SDK/MUI/C/include`: `libraries/mui.h`, `proto/`, `inline/muimaster.h`, `mui/*_mcc.h`; autodocs y ejemplos).
  Extraído en `~/.cache/dash-mui/x` (descarga en `~/.cache/dash-mui/dl`).
- **Licencia del SDK:** solo se puede redistribuir el archivo completo y sin cambios, y no venderlo.
  **No se copia nada del SDK al repo:** un script lo descarga y el compilador lo busca fuera.
- **CPU:** MUI 5 para OS3 está compilado para 68020. Los programas MUI de Dash pueden seguir
  compilándose para 68000, pero solo se prueban en el A1200 (`--emu`), nunca en `--emu-a500`.
- **Clave:** sin `mui.key` MUI funciona; solo limita la configuración de las preferencias.
- **Cabeceras:** el NDK 3.x de la toolchain no define `IPTR`: usar `ULONG` o definirlo.
  `MUI_NewObject` espera `CONST_STRPTR`: con los `MUIC_*` da avisos `-Wpointer-sign` (inofensivos).
- **Prueba hecha:** `hola_mui.c` (scratchpad de la sesión, `mui/hola_mui.c`) compila con
  `m68k-amigaos-gcc -m68020 -O2 -noixemul -I ~/.cache/dash-mui/x/SDK/MUI/C/include`. En el A1200
  emulado con ROM 3.1 y `~/.cache/dash-emu/sys31mui` (sys31 + `MUI/Libs/*` en `Libs/`) **se queda colgado
  sin escribir nada** (timeout de 120 s; la salida va con `printf`, que no se vuelca hasta salir).
  Resuelto en la tarea 1 (ver bitácora): faltaban los `assign` de MUI, la pila de 32 KB y una macro propia
  para `MUI_NewObject`.

## Reglas de cada iteración

1. **Rama.** Trabaja en la rama local `mui` (sale de `main`). No hagas push ni toques `main`.
2. **Base.** `python3 tests/run_tests.py` y `./compile_all.sh`. Anota si cambia respecto a la última entrada.
3. **Tarea.** Coge la primera tarea `[ ]`. Márcala `[~]` mientras trabajas. Una por iteración.
   Si es demasiado grande, divídela en la lista y haz solo la primera parte.
4. **Hacer.** Cada cambio lleva su test en `tests/` (normal, de error o `# expect-c:`), con
   `# emu-needs: muimaster.library` y `# expect-out:` cuando se pueda ejecutar.
   Entorno (no va al repo):
   `export DASH_KICKSTART="/home/freemem/Descargas/Telegram Desktop/ks31a1200.rom"`,
   `DASH_KICKSTART_A500=~/.cache/dash-emu/kick/kick31_a500.rom`, `DASH_EMU_SYS=~/.cache/dash-emu/sys31`,
   `DASH_KICKSTART_32="/home/freemem/Descargas/Telegram Desktop/Kickstart v3.2.3 A1200.47.115_Pack_noSCSI.rom"`,
   `DASH_EMU_SYS_32=~/.cache/dash-emu/sys32`, y para MUI `DASH_EMU_SYS_MUI=~/.cache/dash-emu/sys31mui` y
   `DASH_EMU_SYS_32_MUI=~/.cache/dash-emu/sys32mui` (`tools/emu_sys_mui.sh`). **Sin `DASH_KICKSTART` se usa la ROM AROS** y los
   resultados no valen. Los tests con ventana terminan solos con `--autoclose`/modo test (ver ReAction).
5. **Verificar.** Repite el paso 2 y `python3 tests/run_tests.py --emu --emu-a500 --emu-32`.
   Nada que antes funcionaba puede romperse. Si algo se rompe y no lo arreglas en esta iteración, revierte.
6. **Documentar.** `docs/QUICK_REFERENCE.md`, `docs/MANUAL_REFERENCIA.md` y, si cambian builtins,
   `python3 tools/gen_builtins_doc.py`.
7. **Cerrar.** Marca `[x]`, añade una entrada a la bitácora y commit local `mui: <tarea> - <resumen>`.
8. **Fin.** Si no quedan tareas `[ ]`, escribe el resumen final, para el loop y avisa con PushNotification.

## Límites

- No instales paquetes del sistema. Un `venv` en el scratchpad sí vale.
- Nada del SDK de MUI en git (ver licencia). Sí el script que lo descarga.
- No toques `sesion.txt`, `*.zip` ni `amiga1200_rtg.fs-uae`. No borres tests ni ejemplos.
- Un programa sin MUI tiene que salir **idéntico** (mismo C) que antes: el runtime MUI solo se
  emite si el programa usa algún builtin `mui_`.
- Si una tarea exige una decisión del usuario, déjala `[?]` con la pregunta y pasa a la siguiente.

## Diseño propuesto (fijado en la tarea 2: `docs/MUI_DISEÑO.md`, que manda sobre esta sección)

- **Builtins `mui_`**, como `ra_`, pero con **objetos como valores** (`Pointer`) en vez de un único
  estado global: el navegador tendrá varias ventanas y muchos objetos.
- **Árbol por pila**, como `ra_layout_*`: `mui_vgroup_begin()` ... `mui_group_end()`; cada
  `mui_button(...)`, `mui_text(...)` se añade al grupo abierto y devuelve su objeto.
- **Eventos por número:** `mui_on_press(obj, id)` (y `on_change`, `on_ack`, `on_double`...) monta un
  `MUIM_Notify` con `MUIV_Application_ReturnID`; `mui_wait_event()` devuelve ese número (o -1 al cerrar).
  `mui_wait_event_signals(mask)` también vuelve con otras señales (sockets, timer) para el navegador.
- **Valores:** `mui_get_*`/`mui_set_*` por objeto (texto, número, activo, deshabilitado).
- **Memoria:** MUI es dueño de su árbol; `mui_app_end()` hace `MUI_DisposeObject` de la aplicación.
  Los textos que se pasan a MUI se copian (`MUIA_String_Contents` copia; `MUIA_Text_Contents` también):
  comprobar con `--memcheck` que no queda nada vivo.
- **Cabeceras:** `./dash` añade `-I $DASH_MUI_SDK/C/include` (por defecto `~/.cache/dash-mui/x/SDK/MUI`)
  solo si el programa usa MUI, y da un error claro si no está el SDK.
- Alternativa a valorar en la tarea 2: sintaxis declarativa (`MuiWindow ... end`, como `Window`).
  Solo si sale barata sobre los builtins; si no, apuntarla como pregunta abierta. Tener en cuenta que el
  editor visual (tarea 19) podría leer y escribir esa sintaxis directamente.

## Tareas

- [x] 1. **Entorno.** `tools/get_mui_sdk.sh` (descarga, comprueba tamaño y extrae en `~/.cache/dash-mui`)
      y un sistema emulado con MUI (`tools/emu_sys_mui.sh` → `~/.cache/dash-emu/sys31mui`, variable
      `DASH_EMU_SYS_MUI`; ver qué más necesita: `MUI:`, `ENV:MUI`, `Images`, `Locale`). Arreglar el cuelgue
      de `hola_mui.c` (sacar la salida con `--keep` y captura de pantalla de FS-UAE si hace falta) hasta que
      abra y cierre la ventana. El runner usa ese sistema para los tests `# emu-needs: muimaster.library`.
      Probar también en `--emu-32` (OS 3.2).
- [x] 2. **Diseño.** Fijar la API (sección de arriba) con el caso del navegador delante: ventana con barra de
      URL, botones atrás/adelante/recargar, zona de página con scroll, barra de estado y progreso. Escribirlo
      en `docs/MUI_DISEÑO.md` con un ejemplo en Dash de esa ventana. Decidir si la sintaxis declarativa entra.
- [x] 3. **Núcleo.** `mui_app_begin(title, base)`, `mui_window_begin(title)`/`mui_window_end()`, grupos
      vertical y horizontal, `mui_text`, `mui_button`, `mui_window_open`, `mui_wait_event`, `mui_app_end`,
      `mui_on_close`, `mui_on_press`. Inclusión condicional del runtime y de las cabeceras. Test en emulador
      (pulsación simulada con `MUIA_Pressed`/`set` o cierre por modo test). Ejemplo `examples/mui_hola.dash`.
- [x] 4. **Valores.** Campo de texto (`mui_string`), casilla, ciclo, deslizador, barra de progreso
      (`Gauge`), `mui_get_text`/`mui_set_text`, `mui_get_value`/`mui_set_value`, deshabilitar, `on_change`/`on_ack`.
- [x] 5. **Listas.** `List` + `Listview` de textos: añadir, borrar, vaciar, activo, doble clic. Comprobar memoria.
- [x] 6. **Estructura.** Menús (`Menustrip`), pestañas (`Register`), `Balance`, `Scrollgroup`/`Virtgroup`,
      varias ventanas, barra de estado. `--memcheck` sin restos.
- [x] 7. **Zona de dibujo propia.** Clase propia (`MUI_CreateCustomClass`) con `AskMinMax`, `Draw`,
      `HandleEvent` (ratón, rueda, teclado) y scroll: dibujar con los builtins `gfx_` sobre el `RastPort`
      del objeto, y avisar a Dash con un número de evento cuando haya que repintar. Es la pieza del navegador:
      medir en el A1200 cuánto tarda en repintar.
- [x] 8. **Señales externas.** `mui_wait_event_signals(mask)` para atender sockets y temporizador sin
      bloquear la interfaz. Test con `timer.device` o una señal propia.
- [x] 9. **Imágenes.** `Dtpic` (datatypes) para PNG/JPEG/GIF en un objeto; o dibujar un bitmap en la zona propia.
- [x] 10. **Ejemplo del navegador.** `examples/mui_navegador.dash`: la ventana del diseño (sin red), con
      historial falso y la página pintada en la zona propia. Captura de pantalla en el emulador.
- [x] 11. **Repaso de MUI.** Tamaño del ejecutable, memoria (`--memcheck`), tiempos de apertura en A1200,
      revisión del C generado.

### ReAction y GadTools (petición del usuario del 2026-10-15: terminarlos, mejorarlos, optimizarlos, corregir bugs)

Hoy: 62 builtins `ra_` y 15 `gt_` (más 6 de menús), con **un único estado global** (una ventana, gadgets
por número). ReAction solo se prueba en `--emu-32` (la `window.class` de 3.1 no está en la ROM).

- [x] 12. **Auditoría.** Leer el runtime de los dos (en `compiler/amiga_builtins.py`/`codegen.py`) y sus tests.
      Anotar en la bitácora: bugs (recursos sin liberar, `IDCMP` mal atendidos, valores que no se leen bien,
      textos que se liberan mientras el gadget los usa), qué falta para una aplicación normal, y qué cuesta
      de más (tamaño de runtime, trabajo por evento). Dividir las tareas 13-16 según lo que salga.
- [x] 13a. **Bugs de eventos GadTools/menús** (auditoría 1, 4, 5, 7, 9): la ventana no pide `IDCMP_GADGETUP`/
      `MENUPICK` para `gt_*`/`menu_*` (nunca llegan eventos); las esperas devuelven el primer mensaje y dejan el resto en
      la cola; `gt_event` y `menu_event` se roban mensajes; `ItemAddress` NULL; filtro de `MOUSEMOVE` de los
      deslizadores; `On Menu` en `EventLoop`.
- [x] 13b. **Bugs de valores y vida de los objetos** (auditoría 3, 6, 10, 11, 13): `gt_get/set_value` solo con
      deslizadores; gadgets que apuntan a una ventana cerrada; textos copiados para siempre (`textfield_set`,
      `ra_set_string`, `listview_add` dos veces...); `CloseWindow` con el menú puesto, `menu_attach`/`gt_init` dos
      veces; `gt_*` usa la ventana actual en vez de la suya.
- [x] 13c. **Bugs de ReAction** (auditoría 2, 8, 12, 14): `render_canvas` no compila (`static`); nodos del chooser
      con `AllocMem` sin liberar y sin `AllocChooserNode`, ids fuera de tabla; `RA_EVENT_NONE` = 0 choca con el
      gadget 0; iconificar sin efecto; el dibujo del canvas se llama quizá desde input.device (comprobar).
- [x] 14. **GadTools completo.** Gadgets que faltan: ciclo (`CYCLE_KIND`), opciones (`MX_KIND`), lista
      (`LISTVIEW_KIND`), scroller, número (`NUMBER_KIND`); `gt_set_string`, deshabilitar, refresco
      (`GT_RefreshWindow`, `GT_BeginRefresh`), posiciones según la fuente de la pantalla. Probar en A500 y A1200.
- [x] 15a. **ReAction: gadgets que faltan.** `listbrowser` (lista de textos: añadir, vaciar, elegida), `radiobutton`,
      `fuelgauge` (barra de progreso), `clicktab` (pestañas), con `ra_get_value`/`ra_set_value` y eventos; que los
      `ra_set_*` funcionen antes de abrir la ventana. Nodos con `Alloc*Node` y textos propios, liberados al cerrar.
- [x] 15b. **ReAction: menús y fichero.** Menús en ventanas ReAction (`WINDOW_MenuStrip`, `WMHI_MENUPICK` →
      `RA_EVENT_MENU` + `ra_menu_id()`), `getfile` (botón que abre el selector de ficheros y su ruta).
- [x] 16. **Varias ventanas.** GadTools y ReAction con objetos como valores (como MUI, tarea 2), manteniendo
      la API actual de una ventana para no romper programas. Si choca con la compatibilidad, `[?]`.
- [x] 17. **Optimizar.** Emitir solo la parte del runtime que el programa usa (como ya pasa con otros
      bloques), menos trabajo por evento, tamaño de los ejecutables de `examples/` antes y después.
- [ ] 18. **Repaso final.** Ejemplos actualizados (`./compile_all.sh`), documentación (`CLAUDE.md` local,
      `ROADMAP.md`, manuales, `BUILTINS.md`), resumen final con lo que queda.

### Editor visual de MUI para VS Code (petición del usuario del 2026-10-15, "un Glade para MUI")

Un complemento de VS Code donde se monta la ventana arrastrando objetos (grupos, botones, listas...) y
que genera el código Dash. Ya estaba en el plan de AmiCachy (`~/Projects/AmiCachy`: `PROJECT_CONTEXT.md`,
`ARCHITECTURE.md` sección 5 "AmiCachyDev"): perfil `dev_station` con VS Code + Amiberry, carpeta compartida
`DEV:` y un puente de depuración VS Code <-> Amiberry. El usuario recuerda haber hablado también del formato
del fichero que describe la interfaz; no se encontró escrito (buscado el 2026-10-15 en shiva y pegaso:
repos, sesiones de Claude y Antigravity).

- [ ] 19. **Diseño.** Formato del fichero de interfaz: si la tarea 2 adopta la sintaxis declarativa, el editor
      lee y escribe ese mismo Dash (sin formato propio); si no, un `.dashui` (JSON) que el compilador convierte.
      Dónde vive (carpeta `vscode/` en este repo o repo aparte `FreeMEM/dash-vscode`: si hay duda, `[?]`).
      Vista previa: árbol + propiedades en un webview, dibujo aproximado en el navegador y vista real con
      captura de pantalla del emulador (`tools/emu_run.py` + captura de FS-UAE). Escribirlo en `docs/MUI_EDITOR.md`.
- [ ] 20. **Esqueleto.** Extensión mínima: resaltado de sintaxis de Dash, comando "Compilar" (`./dash`) y
      "Ejecutar en emulador". Empaquetado con `vsce` instalado en un `node_modules` local (no global).
- [ ] 21. **Editor.** Webview con paleta de objetos MUI, árbol, panel de propiedades y eventos; guardar y abrir.
- [ ] 22. **Ida y vuelta.** Abrir el código generado, cambiarlo a mano y volver a abrirlo en el editor sin perder nada.
- [ ] 23. **Vista real.** Botón "Ver en Amiga": compila, arranca el emulador y muestra la captura en el webview.
- [ ] 24. **Ejemplo y documentación.** La ventana del navegador (tarea 10) hecha con el editor.

## Bitácora

Formato:

### YYYY-MM-DD — Tarea N
- Hecho:
- Tests:
- Pendiente / riesgos:

### 2026-10-15 — Tarea 1 (entorno de MUI)
- Hecho:
  - `tools/get_mui_sdk.sh`: descarga MUI 5.0-20210831 del GitHub oficial, comprueba el SHA-256 y lo extrae en
    `~/.cache/dash-mui/x` (`MUI/` y `SDK/MUI/`).
  - `tools/emu_sys_mui.sh`: sistema emulado = ficheros de Workbench + `SYS:MUI` (Libs, Images, Locale) +
    `S/Startup-Extra` con los `assign` del instalador (`MUI:`, `LIBS: MUI:Libs ADD`, `LOCALE: MUI:Locale ADD`).
    Hechos `~/.cache/dash-emu/sys31mui` y `sys32mui`.
  - `tools/emu_run.py`: copia todas las carpetas del sistema (no solo Libs/C/Classes) y ejecuta su `S/Startup-Extra`.
  - Runner: los tests con `# emu-needs: muimaster.library` arrancan en una segunda máquina con MUI
    (`DASH_EMU_SYS_MUI`, `DASH_EMU_SYS_32_MUI`); en el A500 se saltan ("MUI needs a 68020").
  - Codegen: si el C final menciona `muimaster.library`, la pila por defecto pasa de 16 a 32 KB
    (`--stack N` sigue mandando).
  - `tests/test_mui_open.dash`: abre muimaster (versión 21) y comprueba la pila.
- Encontrado (con un programa espía que vuelca los títulos de las ventanas y los textos de sus botones a un fichero):
  1. Sin `assign MUI:` se colgaba en `OpenLibrary`.
  2. **Pila:** por debajo de 32 KB MUI abre una petición "MUI warning" ("The stack size ... is lower than the
     recommended minimum") y espera. Con 16 KB salta ya en `OpenLibrary`; con 24 KB al crear la aplicación.
  3. **`MUI_NewObject` del SDK está roto con GCC 6 `-O2`:** es una función `__inline` que pasa `&tags` (la dirección
     de su primer argumento variable); al meterla en línea, las etiquetas que siguen son basura. La ventana no se
     abría y `get` devolvía basura. Arreglo: `#define NO_INLINE_STDARG` y una macro propia
     `({ ULONG _t[] = { __VA_ARGS__ }; MUI_NewObjectA(cl, (struct TagItem *)_t); })`. El runtime de Dash (tarea 3)
     tiene que hacerlo así para todas las funciones con etiquetas variables (`DoMethod` incluido).
- Probado: `hola_mui.c` abre la ventana "Hola MUI" (184 x 47) y lee su texto en el A1200 con 3.1 y con 3.2.
- Tests: 121/121 sin emulador (antes 120); 283/283 con `--emu --emu-a500 --emu-32` (antes 280); ejemplos 31/31.
- Pendiente / riesgos: el espía (`scratchpad/mui/spy.c`) no está en el repo; si hace falta más veces, pasarlo a
  `tools/` como opción de `emu_run.py`. MUI sin registrar no ha mostrado ninguna petición.

### 2026-10-15 — Tarea 2 (diseño de la API de MUI)
- Hecho: `docs/MUI_DISEÑO.md`. Builtins `mui_` con objetos como `Pointer`; árbol con pila (`*_begin`/`mui_group_end`,
  hijos con `OM_ADDMEMBER`); eventos por número (`mui_on_press/change/ack/double/close`, menús) y `mui_wait_event`,
  `mui_poll_event`, `mui_wait_event_signals`; valores por objeto (`mui_get/set_text`, `mui_get/set_value`, `enabled`,
  `visible`, `range`); listas; zona de dibujo propia con una función Dash (`Func`, ya funciona pasar funciones como
  valor) y barra de desplazamiento aparte; `mui_press` para tests y atajos. Ejemplo completo de la ventana del navegador.
- Decidido: la sintaxis declarativa queda para la tarea 19, como capa sobre estos builtins y como formato del editor
  visual (bloque Dash, sin fichero aparte). El usuario no recuerda el formato que se habló.
- Tests: sin cambios de código (solo documentación).
- Pendiente / riesgos: comprobar en la tarea 3 que `OM_ADDMEMBER` en grupos ya creados funciona antes de abrir la
  ventana, y que un `Pointer` de Dash se puede comparar con `nil`.

### 2026-10-15 — Tarea 3 (núcleo de MUI)
- Hecho:
  - `CTemplates.MUI_RUNTIME` (antes de `RTG_RUNTIME`, flag `needs_mui` por `runtime_index`) y 16 builtins en
    `MUI_FUNCTIONS`: `mui_app_begin/end`, `mui_window_begin/end/open/close`, `mui_vgroup_begin`, `mui_hgroup_begin`,
    `mui_group_end`, `mui_text`, `mui_button`, `mui_on_press`, `mui_on_close`, `mui_press`, `mui_wait_event`, `mui_poll_event`.
  - Objetos como números (convención de Dash para handles: el codegen castea a puntero al llamar y el retorno a LONG),
    no `Pointer`; `docs/MUI_DISEÑO.md` corregido.
  - Por dentro: `NO_INLINE_STDARG` + `MUI_NOSHORTCUTS` (sin macros `get`/`set`/`String`... que choquen con nombres del
    programa); etiquetas en arrays (`_DASH_MUI_NEW`, `_DASH_MUI_DO` con `DoMethodA`); la ventana se crea en
    `mui_window_begin` con un grupo raíz vacío y los hijos entran con `OM_ADDMEMBER` (funciona antes de abrir).
    Títulos copiados en un pool propio. Comprueba 68020 (`AttnFlags`) antes de abrir muimaster. `_dash_mui_app_end()`
    en la limpieza de salida. Cerrar la primera ventana = -1 (`MUIM_KillNotify` al cambiarlo con `mui_on_close`).
  - `compiler/cflags.py`: `mui_flags()` añade `-I` del SDK (`DASH_MUI_SDK`, por defecto `~/.cache/dash-mui/x/SDK/MUI`)
    si el C incluye `libraries/mui.h`; error claro sin SDK. Lo usan `./dash` y el runner.
  - `examples/mui_hola.dash` (32 ejemplos), documentación en QUICK_REFERENCE, MANUAL_REFERENCIA (20b) y BUILTINS.md.
- **Bug general encontrado y arreglado: los textos con acentos llegaban al Amiga en UTF-8** ("botón" = 6 bytes y
  basura en pantalla). `compiler/latin1.py`: pasada final que escribe cada carácter no ASCII de un literal C como octal
  Latin-1 (`bot\363n`; fuera de Latin-1 = `?`), en `compile` y `compile_multifile`. `tools/emu_run.py` lee la salida en
  Latin-1. Test `tests/test_latin1.dash` (longitud 5, `ñ` por índice, interpolación) en las tres máquinas.
  Comparado el C de todos los tests y ejemplos con el de antes: solo cambian `scope_test` y `test_latin1`, y solo en eso.
- Probado en emulador: `test_mui_core` (ventana con grupos, `mui_press` → evento 2 y 1, `mui_poll_event` = 0) en A1200
  3.1 y 3.2; con `--memcheck` sin restos; en A500 imprime "MUI: needs a 68020 or better" y sigue; `mui_hola` con
  `--autoclose 3` termina con RC 0.
- Coordinación: otra sesión (`freememlang-ff`) trabaja en dashweb y en un worktree de Dash (`~/Projects/FreeMEMLang-dashweb`,
  rama `dashweb` sobre `mui`). Acordado: ella no toca `MUI_FUNCTIONS`/`MUI_RUNTIME`; yo no toco sus bloques (red,
  fuentes, textos, listas). Las imágenes por datatypes fuera de MUI son suyas (su D12); mi tarea 9 se apoyará en ellas.
  Avisarle antes de cambiar la API de `mui_canvas` o `mui_wait_event_signals`.
- Tests: 123/123 sin emulador; 290/290 con `--emu --emu-a500 --emu-32` (antes 283); ejemplos 32/32.
- Pendiente / riesgos: `docs/BUILTINS.md` dice `APTR` en "Devuelve" de los `mui_` (es el tipo C; en Dash son números).
  La sección 20b del manual no tiene número propio para no renumerar el resto.

### 2026-10-15 — Tarea 4 (valores)
- Hecho: 13 builtins: `mui_label`, `mui_string`, `mui_checkbox`, `mui_cycle` ("A|B|C", copias en el pool con array
  terminado en NULL), `mui_slider`, `mui_gauge`, `mui_get_value`/`mui_set_value`, `mui_get_text`/`mui_set_text`,
  `mui_set_enabled`, `mui_on_change`, `mui_on_ack`. Cada objeto guarda su tipo en `MUIA_UserData` (texto, botón, campo,
  casilla, ciclo, deslizador, barra, ventana): así `get/set_value` y `get/set_text` saben qué atributo tocar sin tablas.
  `mui_set_value` usa `SetAttrs`, que dispara las notificaciones (los tests simulan al usuario así). El título de
  ventana se copia al pool (MUI guarda el puntero). `MUIA_CycleChain` en los objetos de entrada (Tab entre ellos).
- Probado en A1200 3.1 y 3.2 (`test_mui_values`, también con `--memcheck`): texto con `ñ` ida y vuelta, eventos de
  casilla y ciclo, valores de deslizador y barra, títulos.
- Limitación de Dash vista: la interpolación `#{...}` solo admite nombres de variable, no llamadas
  (`"#{mui_get_text(url)}"` da "Variable ... is not defined"). Apuntado para la auditoría (tarea 12).
- Tests: 124/124 sin emulador; 293/293 con `--emu --emu-a500 --emu-32`; ejemplos 32/32.
- Pendiente: `mui_on_ack` no se puede disparar sin teclado en el emulador (solo se comprueba que se monta).

### 2026-10-15 — Tarea 5 (listas)
- Hecho: 9 builtins: `mui_list()` (sin parámetro de líneas: MUI calcula el alto), `mui_list_add`, `mui_list_insert`,
  `mui_list_remove`, `mui_list_clear`, `mui_list_count`, `mui_list_get`, `mui_list_quiet`, `mui_on_double`. El handle
  es el `Listview` (tipo `_DASH_MUI_LIST` en su `UserData`); las funciones sacan el `List` de dentro con
  `MUIA_Listview_List`. El valor (`mui_get/set_value`, `mui_on_change`) es `MUIA_List_Active` del `List` (-1 = ninguna).
  Las líneas las copia MUI (`ConstructHook_String`/`DestructHook_String`), así que los temporales de Dash se pueden
  liberar. `mui_list_get` devuelve la copia de MUI ("" fuera de rango) y Dash la copia al guardarla.
- Probado en A1200 3.1 y 3.2 (`test_mui_list`, también `--memcheck`): insertar arriba, borrar en medio, recorrer,
  línea activa con evento, fuera de rango, vaciar.
- Tests: 125/125 sin emulador; 296/296 con `--emu --emu-a500 --emu-32`; ejemplos 32/32.
- Pendiente: medir cuánto tarda añadir cientos de líneas (historial del navegador) en la tarea 11.

### 2026-10-15 — Tarea 6 (estructura)
- Hecho: 12 builtins: `mui_frame_begin`, `mui_columns_begin`, `mui_register_begin` (pestañas; valor = página,
  `MUIA_Group_ActivePage`), `mui_scroll_begin` (`Scrollgroup` con un `Virtgroup`: los hijos van al `Virtgroup`),
  `mui_space`, `mui_balance`, `mui_weight` (`HorizWeight`/`VertWeight`, que sí se pueden cambiar tras crear),
  `mui_set_visible` (`ShowMe`), `mui_menu_begin/item/separator/end`. Menús: `Menustrip` creado al primer
  `mui_menu_begin` de la ventana y puesto con `SetAttrs(MUIA_Window_Menustrip)` (isg en MUI 5); las opciones avisan con
  `MUIA_Menuitem_Trigger`; `mui_set_enabled` usa `MUIA_Menuitem_Enabled` en ellas; `mui_press` en una opción hace el
  `Trigger` (como elegirla). Varias ventanas: las que no son la primera se cierran solas con su botón de cerrar
  (notificación a sí mismas), salvo `mui_on_close`. `_dash_mui_push` reúne la apertura de grupos.
- Probado en A1200 3.1 y 3.2 (`test_mui_layout`, también `--memcheck`): ventana con menú, pestañas con un formulario en
  columnas y un marco, balance y pesos, zona con 20 líneas desplazable, objeto oculto, segunda ventana, evento de
  pestaña y de menú.
- **No verificado:** que el menú se vea. MUI 5 en OS3 dibuja sus propios menús: el `Window->MenuStrip` de Intuition
  está vacío incluso con el menú puesto al crear la ventana y la ventana activa (comprobado con un programa en C y el
  espía, que ahora también vuelca menús y ventana activa). Se comprueba la cadena de objetos y notificaciones, no el
  dibujo. Hace falta una captura de pantalla (tarea 10) o probarlo a mano.
- Tests: 126/126 sin emulador; 299/299 con `--emu --emu-a500 --emu-32`; ejemplos 32/32.

### 2026-10-15 — Tarea 7 (zona de dibujo propia)
- Hecho: plantilla aparte `CTemplates.MUI_CANVAS_RUNTIME` (flag `uses_mui_canvas`, que activa `needs_gfx` y
  `needs_mui`: un programa MUI sin zona de dibujo no arrastra graphics). Clase propia sobre `Area` con
  `MUI_CreateCustomClass`; despachador con parámetros en registros (`__asm("a0")`, `a2`, `a1`). Métodos:
  `AskMinMax` (mínimo pedido, máximo `MUI_MAXMAX`), `Draw` (con `MADF_DRAWOBJECT`: `_dash_rp` = RastPort de la ventana,
  `MUI_AddClipping` al interior del objeto, llama a la función Dash `f(x, y, ancho, alto)` y restaura `_dash_rp`),
  `Setup`/`Cleanup` (manejador de eventos `IDCMP_MOUSEBUTTONS | IDCMP_RAWKEY` solo si hay `mui_canvas_on_input`),
  `HandleEvent` (clic dentro, rueda 0x7A/0x7B sobre la zona, teclas; guarda la entrada y devuelve el número con
  `ReturnID`). Clase borrada en `_dash_mui_app_end` antes de cerrar MUI (`_dash_mui_end_hook`). Macros propias
  `_DASH_MLEFT`... porque `_mleft`/`_rp` de mui.h están tras `MUI_NOSHORTCUTS`.
  Barra de desplazamiento (`Scrollbar`, valor `MUIA_Prop_First`, `mui_set_range` = `Prop_Entries`/`Prop_Visible`).
  11 builtins: `mui_canvas`, `mui_canvas_on_draw`, `mui_canvas_on_input`, `mui_canvas_redraw`, `mui_canvas_mouse_x/_y`,
  `mui_canvas_button`, `mui_canvas_wheel`, `mui_canvas_key`, `mui_scrollbar`, `mui_set_range`. API igual a `MUI_DISEÑO.md`.
- Probado en A1200 3.1 y 3.2 (`test_mui_canvas`, también `--memcheck`): MUI llama a la función al abrir, respeta el
  tamaño mínimo, el píxel de la esquina es 1 y el del centro 2 (pinta dentro y en su sitio), `mui_canvas_redraw` llama
  una vez, barra con rango, valor y evento. **No probado:** clic, rueda y teclas (sin ratón en el emulador).
- Medido en A1200 3.1 emulado (programa en el scratchpad, `bench_canvas.dash`): repintar 320 x 200 = 20 ms el fondo;
  con 20 líneas de 50 caracteres = 114 ms (unos 4,7 ms por línea). Para el navegador: repintar por partes y
  desplazar con `ScrollRaster` en vez de repintar todo.
- Visto de paso (para la auditoría): avisos de GCC en runtimes viejos (`diminfo` sin usar en `_dash_open_screen_custom`,
  `_dash_nil_area` sin usar).
- Tests: 127/127 sin emulador; 302/302 con `--emu --emu-a500 --emu-32`; ejemplos 32/32.

### 2026-10-15 — Tarea 8 (señales externas y temporizador)
- Hecho: `mui_wait_event_signals(mask)` (el bucle de `NewInput` espera también `mask`; vuelve con 0 y deja en
  `mui_signals()` las que llegaron), `mui_wait_event` = la misma con máscara 0. `mui_timer(ms, id)`: temporizador de un
  disparo con `timer.device` (`UNIT_MICROHZ`) en plantilla aparte `MUI_TIMER_RUNTIME` (flag `uses_mui_timer`); el bucle
  de espera incluye su señal y lo consulta con un puntero a función (`_dash_mui_timer_hook`), así un programa sin
  temporizador no lleva `timer.device`. `mui_poll_event` también lo mira. Varios ganchos de cierre
  (`_dash_mui_on_end`, hasta 4: clase de dibujo, temporizador) en vez de uno.
- Probado en A1200 3.1 y 3.2 (`test_mui_signals`, también `--memcheck`): temporizador de 200 ms, señal propia
  (Ctrl-E) mientras espera eventos MUI, cancelar y que no salte, y volver a armarlo.
- Coordinación: la sesión de dashweb usará `mui_timer` para `setTimeout`/`setInterval` de JavaScript. Me cuenta que en
  su rama `dashweb` añade `reads_only` a `BuiltinFunc` (builtins que solo leen sus textos no los copian con
  `_dash_str_escape`). **Pendiente para la tarea 11:** hoy los textos que se pasan a los `mui_` se escapan (se hacen
  permanentes hasta salir); cuando `reads_only` llegue, marcar los `mui_` que no guardan el texto (MUI copia).
- Tests: 128/128 sin emulador; 305/305 con `--emu --emu-a500 --emu-32`; ejemplos 32/32.

### 2026-10-16 — Tarea 9 (imágenes)
- Hecho: `mui_image(fichero)` (`Dtpic`, nombre copiado al pool; `mui_set_text` lo cambia), `mui_width`/`mui_height`
  (`MUIA_Width`/`MUIA_Height`, sirven para cualquier objeto). Entorno: `tools/emu_sys_from_hdf.sh` copia ahora
  `Devs/DataTypes` y `C/AddDataTypes`, y `tools/emu_run.py` ejecuta `AddDataTypes REFRESH QUIET` al arrancar si están.
  Rehechos `sys31`, `sys32`, `sys31mui` y `sys32mui` (3.1 trae ILBM; 3.2 además PNG, JPEG, GIF, BMP).
- Probado: `test_mui_image` escribe un ILBM de 8 x 4 con `@native` y lo muestra: mide 8 x 4 en A1200 3.1 y 3.2 (también
  `--memcheck`); un fichero que no existe no cuelga. A mano en 3.2: un PNG de 6 x 3 generado igual mide 6 x 3.
- Limitación: con un fichero que falta, MUI da al objeto un tamaño igual, así que el programa no puede saber si cargó.
  Para el navegador las imágenes irán pintadas en la zona de dibujo (tarea D12 de la sesión de dashweb), no con `Dtpic`.
- Tests: 129/129 sin emulador; 308/308 con `--emu --emu-a500 --emu-32` (con datatypes en los cuatro sistemas); ejemplos 32/32.

### 2026-10-16 — Tarea 10 (ejemplo del navegador y capturas)
- Hecho:
  - `examples/mui_navegador.dash` (33 ejemplos): la ventana del diseño con menú, barra de direcciones, atrás/adelante/
    recargar, historial (lista con balance), página en una zona de dibujo con barra de desplazamiento y rueda, estado,
    progreso animado con `mui_timer` y ventana "Acerca de".
  - **Capturas de pantalla:** `tools/amiga/shot.c` (lee la pantalla delantera con `ReadPixelLine8` y su paleta
    `GetRGB32`, escribe un PPM) y `tools/emu_run.py --screenshot SEGUNDOS fichero.png` (lo compila en
    `~/.cache/dash-emu/shot`, lo lanza con `Run` antes del programa y pasa el PPM a PNG en Python sin paquetes).
    Captura en `docs/img/mui_navegador.png`, enlazada desde el manual (20b).
- Comprobado mirando las capturas (3.1 y 3.2): la ventana se dibuja entera, acentos bien ("Línea"), botones
  desactivados en gris, lista, balance, página pintada con su barra.
- Encontrado:
  - La primera versión de `shot.c` escribía línea a línea (256 `Write`) y, si la captura coincidía con el final del
    programa en 3.2 + Workbench, el programa no terminaba (TIMEOUT reproducible con autocierre 40 y captura a 30 s).
    Con una sola escritura de toda la imagen termina en 50 s.
  - Dos fallos de Dash al escribir el ejemplo: `lista + [x]` genera C inválido, y una lista declarada `var x: Array`
    pierde el tipo de sus elementos (textos pasados como enteros). El primero está arreglado en la rama `dashweb`
    (su D1); el segundo era un pendiente conocido. El ejemplo los evita.
  - La barra de progreso al 0 % no se distingue del fondo con los colores por defecto de MUI (al 50 y 75 % sí se ve).
- No visto: los menús (MUI 5 los dibuja al pulsar el botón derecho, sin ratón no salen).
- Tests: 129/129 sin emulador; 308/308 con `--emu --emu-a500 --emu-32`; ejemplos 33/33.

### 2026-10-16 — Tarea 11 (repaso de MUI)
- **Memoria (arreglado):** los textos que se pasaban a los `mui_` recibían una copia permanente (`_dash_str_escape`,
  no se libera hasta salir): un bucle de `mui_list_add` o `mui_set_text` hacía crecer la memoria sin límite. Los `mui_`
  que reciben texto van ahora en `_STRING_READERS` (codegen): MUI copia lo que muestra (Text, String, líneas de lista) y
  el runtime ya copiaba al pool lo que MUI solo apunta (títulos, opciones, menús, ficheros). Test `test_mui_texts`
  (`# memcheck`, que rellena lo liberado con 0xDB): texto, botón, campo, línea, título y texto cambiado se leen bien
  después de liberar sus temporales, y el resumen dice 0 textos escapados. (La sesión de dashweb tiene en su rama un
  campo `reads_only` para lo mismo; al juntar ramas, pasar estos nombres a ese campo.)
- **Medidas** (A1200 3.1 emulado, `scratchpad/bench_mui.dash`): abrir MUI + ventana con 3 objetos, una lista y un texto:
  1,9 s. `mui_list_add`: 35 ms por línea; con `mui_list_quiet`: 7 ms (×5). `mui_set_text` en un campo: 8 ms. Quitar la
  copia permanente no cambia los tiempos: el coste está en MUI. Idea para luego: añadir muchas líneas de una vez
  (`MUIM_List_Insert` con un array).
- **Tamaño:** `mui_hola` 9.204 bytes (un programa con `Print` solo: 4.996), `mui_navegador` 18.736.
- **C generado:** sin avisos de GCC con `-Wall` en el runtime MUI. Visto para la tarea 17: los argumentos no simples de
  los builtins se calculan en temporales `volatile` (necesario para las macros con `register asm` del NDK), también en
  las llamadas a funciones del runtime (`_dash_*`), donde no hace falta y obliga a pasar por memoria.
- Documentación: `ROADMAP.md` (sesión 7 y pendientes del lenguaje), `CLAUDE.md` local.
- Tests: 130/130 sin emulador; 311/311 con `--emu --emu-a500 --emu-32`; 193/193 con `--emu --memcheck`; ejemplos 33/33.

### 2026-10-16 — Tarea 12 (auditoría de GadTools y ReAction)
- Hecho con un subagente que solo leyó y transpiló (sin tocar el repo). Comprobados aquí los dos más graves:
  la ventana de `examples/test_gadtools.dash` solo pide `IDCMP_CLOSEWINDOW`, y un programa ReAction con
  `render_canvas` da "static declaration of 'render_canvas' follows non-static declaration".
- **Bugs** (codegen.py; numeración de la auditoría, de más grave a menos):
  1. `gt_*`/`menu_*` no reciben eventos: `visit_WindowOpen` solo añade `IDCMP_GADGETUP`/`MENUPICK` si `needs_gadtools`
     ya está activo, el preescaneo solo mira `button_`, `checkbox_`..., y `_dash_gt_init`/`_dash_gt_attach`/
     `_dash_menu_attach` no llaman a `ModifyIDCMP`.
  2. `render_canvas` declarada sin `static` en el runtime ReAction: no compila (afecta a `blixel/blixel.dash`).
  3. `gt_get_value`/`gt_set_value` usan `GTSL_Level` para todo: casilla, paleta y entero leen 0 (el manual enseña ese uso).
  4. `_dash_gt_wait_event` y `ra_wait_event` hacen `Wait` y devuelven el primer mensaje: los demás quedan en la cola
     sin señal nueva.
  5. `gt_event` y `menu_event` vacían el mismo puerto y tiran lo que no es suyo (un `MENUPICK` se pierde); en
     `EventLoop` no hay `On Menu`.
  6. Cerrar una ventana deja `_dash_gads[i].win` apuntando a ella: `slider_set` después puede colgar.
  7. `_dash_menu_event` lee `item->NextSelect` con `item` NULL; solo devuelve el primero de una selección múltiple.
  8. Chooser ReAction: nodos con `AllocMem` sin liberar, `struct Node` en vez de `AllocChooserNode`, `CHOOSER_Labels`
     fuera del array con id >= 64, `_ra_gadgets[-1]` con id negativo.
  9. Filtro de `MOUSEMOVE` (`GadgetType & GTYP_GADGETTYPE`) que los gadgets GadTools no cumplen: el deslizador solo
     avisa al soltar (sin verificar en emulador).
  10. Textos copiados hasta salir: `listview_add` copia dos veces, `listview_clear` no libera, `textfield_set`,
      `ra_set_string`, `ra_chooser_add_item`, `window_title` no están en `_STRING_READERS`.
  11. `CloseWindow` con el menú puesto (sin `ClearMenuStrip`); `menu_attach`/`gt_init` dos veces pierden lo anterior.
  12. `RA_EVENT_NONE` = 0 = un gadget con id 0; el iconificar no se ejecuta nunca.
  13. `gt_*` usa `_dash_win`, que cambian `window_create` o `ra_get_rastport`.
  14. (Sin verificar) el gancho de dibujo del canvas ReAction ejecuta código Dash en `GM_RENDER`, que Intuition puede
      llamar desde input.device; usa el pool sin protección.
- **Falta:** `gt_cycle`/`gt_listview` existen en el runtime sin builtin; no hay MX, NUMBER, SCROLLER; ni cambiar textos
  ni desactivar gadgets; sin atajos de teclado (`GT_Underscore`); posiciones fijas sin mirar la fuente; menús sin marca
  ni desactivar; `EventLoop` sin `On Menu`, ratón, tamaño, temporizador; ventanas de `window_create` sin lector de
  mensajes; ReAction sin listbrowser (incluida pero sin API), clicktab, radiobutton, getfile, fuelgauge, menús, teclas,
  `WMHI_NEWSIZE`; `ra_set_*` sin efecto antes de abrir. Todo es una ventana global (`_dash_glist`, `_dash_vi`,
  `_dash_menu`, tablas de 64; en ReAction `_ra_winobj`, `_ra_window`...).
- **Coste:** ventana + `EventLoop` 2.500 bytes de código; con un `button_create` 5.224 (+7.884 de bss); `gt_button`
  3.720; ReAction mínimo 3.984. La plantilla `main` de GadTools abre asl.library y crea un requester aunque no se use;
  `needs_gadtools` arrastra gráficos y ASL. Por gadget: `GetVisualInfo`, `CreateContext`, `AddGList`, `RefreshGList`,
  `GT_RefreshWindow`, `ModifyIDCMP`. `IDCMP_INTUITICKS` en toda ventana con gadgets (10 despertares por segundo; solo lo
  necesitan las listas). `listview_add` quita y pone la lista y la redibuja entera en cada línea.
- **Tres APIs para lo mismo** (más MUI): `gt_*` + `menu_*` (ids desde 0, sondeo; solo `examples/test_gadtools` y
  `flowpaint2`, rotos por el bug 1, sin test), por número de gadget `button_`/`slider_`/`listview_`... + `On Gadget`
  (ids desde 1, `EventLoop`; `tests/test_gadgets.dash`), `ra_*` (propias, sondeo; `test_reaction_values`,
  `examples/test_reaction`, `flowpaint3`, `blixel`). Chocan si se mezclan en una ventana.
- **Decisión** (el usuario pidió terminar y mejorar GadTools y ReAction, no quitar): se arreglan las tres APIs sin
  romper programas; la recomendada para programas nuevos con GadTools será la de número de gadget + `EventLoop`
  (se documenta así). Tarea 13 dividida en 13a, 13b y 13c.
- Tests: sin cambios de código.

### 2026-10-16 — Tarea 13a (eventos de GadTools y menús)
- Hecho:
  - `gt_*`/`menu_*` reciben eventos: el preescaneo marca `needs_gadtools` con cualquier `gt_`/`menu_` (la ventana abre
    con `IDCMP_GADGETUP`, `MENUPICK`...) y además `gt_attach`/`menu_attach` hacen `ModifyIDCMP` (ventanas abiertas de
    otra forma).
  - `gt_event` y `menu_event` comparten un lector (`_dash_gt_read`) con una cola de 16 eventos: lo que una lee para la
    otra queda guardado; `REFRESHWINDOW` con `GT_BeginRefresh`/`GT_EndRefresh`; solo cuenta lo que viene de sus gadgets
    (por dirección); selección múltiple de menú completa, sin leer de NULL y con tope de 64.
  - `gt_wait_event` solo duerme cuando no queda nada que leer.
  - Gadgets por número: se reconocen por dirección (antes un filtro `GTYP_GADGETTYPE` descartaba todos los `MOUSEMOVE`
    de los deslizadores GadTools); `gadget_id` sale de la tabla, no de `GadgetID`.
  - `On Menu` en `EventLoop` (gramática, AST `OnMenuHandler`, analizador, codegen: `case IDCMP_MENUPICK` que recorre la
    selección) y builtin `menu_id()`.
- Probado en las tres máquinas (`test_gt_events`): un proceso mete clics y elecciones de menú por `input.device`;
  llegan "Dos" y "Uno", `menu_event` devuelve el menú aunque antes hubiera un clic, y luego `gt_event` da los dos clics;
  `On Menu` recibe la segunda opción.
- Aprendido para tests de menús: Intuition no mueve el puntero con `NEWPOINTERPOS` mientras el menú está abierto; hay
  que poner el puntero en el título, pulsar el botón derecho y bajar con movimientos relativos de un paso mirando
  `screen->MouseX/Y` (un paso no es un píxel en vertical). Las coordenadas de `gt_*` cuentan desde dentro de los bordes
  (ventanas `GIMMEZEROZERO`). Diagnóstico con capturas (`--screenshot`): la primera prueba fallaba por clicar encima de
  los botones.
- Sin probar: arrastrar un deslizador (los `MOUSEMOVE` deberían llegar ahora).
- Tests: 131/131 sin emulador; 315/315 con `--emu --emu-a500 --emu-32`; ejemplos 33/33.

### 2026-10-16 — Tarea 13b (valores y vida de los objetos de GadTools)
- Hecho:
  - Paso común antes de cerrar una ventana: `_dash_before_close(win)` (en `WINDOW_RUNTIME`/`GRAPHICS_RUNTIME`) llama a
    los runtimes que se apuntan con `_dash_on_close`; está en los seis sitios que cierran ventanas propias (`Win.close`,
    fin de `EventLoop`, limpieza final, `window_close`, `close_window`).
  - GadTools (`gt_*` y menús) recuerda su ventana (`_dash_gt_win`, la de `gt_init`): antes usaba `_dash_win`, que cambia
    con `window_create`. Al cerrarla: `ClearMenuStrip` y `RemoveGList` (antes `CloseWindow` con el menú puesto).
    `gt_init` otra vez libera lo anterior; `menu_attach` otra vez cambia los menús; `gt_attach` dos veces no añade la
    lista dos veces.
  - `gt_get_value`/`gt_set_value` según el tipo guardado al crear cada gadget: casilla (`GTCB_Checked`), paleta
    (`GTPA_Color`), entero (`GTIN_Number`), deslizador, ciclo y lista.
  - Gadgets por número: al cerrar su ventana olvidan el puntero (`GT_SetGadgetAttrs` con ventana NULL no dibuja).
  - Textos: `textfield_set`, `ra_set_string` y `listview_add` en `_STRING_READERS`; las líneas de un listview son una
    copia propia que `listview_clear` y la limpieza final liberan (antes, dos copias permanentes por línea).
- Probado en las tres máquinas, con `# memcheck` (`test_gt_values`): valores de casilla, paleta, entero y deslizador
  leídos y cambiados; `gt_set_value` tras `window_create`; menús cambiados; 20 `textfield_set` y `listview_add` con
  textos interpolados; deslizador de una ventana cerrada; al salir 0 vivos y 0 escapados.
- Visto: `_dash_check_close` (`window_check_close`) vacía el puerto con `GetMsg` y tira todo lo que no es cerrar
  (mismo problema que tenían `gt_event`/`menu_event`); queda para la tarea 16 (varias ventanas).
- Tests: 132/132 sin emulador; 319/319 con `--emu --emu-a500 --emu-32`; 197/197 con `--emu --memcheck`; ejemplos 33/33. Tres `expect-c` con el `CloseWindow` exacto actualizados (`test_exit_cleanup`, `test_window_handles`, `test_windows_adv`).

### 2026-10-16 — Tarea 13c (bugs de ReAction)
- Hecho:
  - `render_canvas` declarada `static` en el runtime: **`blixel/blixel.dash` no compilaba** (y cualquier programa
    ReAction con `render_canvas`); ahora compila.
  - El gancho de dibujo del área (`SPACE_RenderHook`) **nunca se enganchaba**: `ra_init_canvas_render`/
    `ra_canvas_enable` no hacían nada. Se engancha si `ra_init_canvas_render()` va antes de `ra_add_drawing_area`
    (así `blixel`, que no lo llama, no cambia), y la función recibe sus argumentos en registros (`a0`, `a2`, `a1`),
    como llama Intuition a un gancho. Si Intuition lo llama desde otra tarea, el código Dash no corre ahí: se apunta,
    se despierta al programa y el área se repinta desde `ra_handle_events`.
  - `RA_EVENT_NONE` = -3 (era 0, igual que un gadget con id 0).
  - `ra_wait_event` lee primero lo pendiente y luego espera (antes dejaba mensajes en la cola sin señal nueva); sigue
    pudiendo devolver "nada" tras despertar, porque `blixel` y `flowpaint3` lo usan para mirar el ratón.
  - Chooser: nodos con `AllocChooserNodeA` (antes `AllocMem` de un `struct Node` que la clase no espera, sin liberar),
    texto propio, lista quitada y puesta en el gadget al añadir, nodos y textos liberados en `ra_window_close`.
  - Ids negativos o >= 64 ignorados en todos los `ra_add_*` (`(ULONG)id`).
  - Iconificar deja `_ra_window` a NULL (el código sigue sin usarse: falta `WINDOW_IconifyGadget`).
- Probado en A1200 3.2 (`test_ra_events`, con `# memcheck`): "nada" = -3, chooser con 3 opciones y selección 2,
  `render_canvas` llamada al abrir y con `ra_refresh_canvas`, clic real en el botón de id 0 (proceso con
  `input.device`) devuelve 0, id -1 sin efecto; 0 vivos y 0 escapados al salir.
- Tests: 133/133 sin emulador; 321/321 con `--emu --emu-a500 --emu-32`; 265/265 con `--emu --emu-32 --memcheck`; ejemplos 33/33 (`blixel` también compila).

### 2026-10-16 — Tarea 14 (GadTools completo)
- Hecho (21 builtins nuevos, 411 en total):
  - Gadgets por número (la API recomendada): `cycle_create/get/set`, `radio_create/get/set` (MX; responde en
    `GADGETDOWN`), `integer_create/get/set`, `palette_create/get/set`, `number_create`/`number_set`. Opciones "A|B|C"
    partidas en una copia que guarda el gadget hasta salir. `On Gadget` actualiza su valor. El preescaneo solo cuenta
    builtins (una función del usuario `number_x` ya no activa GadTools).
  - API `gt_*`: `gt_cycle` (con "A|B"; el runtime ya tenía la función sin builtin), `gt_enable`/`gt_disable`,
    `gt_set_text` (`gt_text` creado con `GTTX_CopyText`, o `gt_string`).
  - Menús: `menu_check_item` (`CHECKIT|MENUTOGGLE`), `menu_checked`, `menu_enable` (`OnMenu`/`OffMenu` con el número
    calculado recorriendo menús, opciones y subopciones), atajo `""` = sin atajo (antes quedaba el símbolo Amiga solo).
  - `MXWIDTH`/`MXHEIGHT` definidos si el NDK no los trae (el de la toolchain no los tiene).
- Probado en las tres máquinas (`test_gt_more`): valores iniciales y cambiados de los cinco gadgets nuevos, `gt_cycle`
  y `gt_set_text`; con clics reales, el ciclo pasa de "Tres" a "Uno" y el tercer botón de radio queda elegido (`On
  Gadget`), y la opción con marca da `menu_checked` = 1 en `On Menu`.
- No hecho: atajos de teclado con `_` (GadTools solo subraya la letra; el programa tendría que atender las teclas) y
  posiciones según la fuente de la pantalla. Quedan como pendientes.
- Tests: 134/134 sin emulador; 325/325 con `--emu --emu-a500 --emu-32`; 200/200 con `--emu --memcheck`; ejemplos 33/33. `test_window_handles` agotaba el tiempo en la batería `--memcheck` (pasa solo): todos los tests de una máquina van en un arranque y ya no cabían en 180 s; límites subidos a 360 s (A1200), 700 s (A500) y 480 s (3.2).

### 2026-10-16 — Tarea 15a (ReAction: gadgets que faltaban)
- Hecho (7 builtins): `ra_add_listbrowser` + `ra_listbrowser_add/clear/count` (nodos con `AllocListBrowserNodeA` y
  `LBNCA_CopyText`), `ra_add_radio` (`AllocRadioButtonNodeA`), `ra_add_clicktab` (`AllocClickTabNodeA`),
  `ra_add_fuelgauge` (con porcentaje). Sus valores por `ra_get_value`/`ra_set_value` (`LISTBROWSER_Selected`,
  `RADIOBUTTON_Selected`, `CLICKTAB_Current`, `FUELGAUGE_Level`). Listas de nodos por id liberadas en
  `ra_window_close` (después de `DisposeObject`, antes de cerrar las clases), con la copia de las opciones.
  `ra_set_value` ya no exige la ventana abierta (`SetGadgetAttrs` con ventana NULL no dibuja). Funciones con
  etiquetas en array (versiones `...A`).
- Probado en A1200 3.2 (`test_ra_more`, con `# memcheck`): barra puesta antes de abrir (25), lista con 3 líneas,
  elegida -1 y luego 1, vaciada; radio 2, pestaña 1, barra 40; 0 vivos y 0 escapados.
- Sin probar: clics en estos gadgets (las posiciones de sus opciones dependen de la fuente).
- Tests: 135/135 sin emulador; 327/327 con `--emu --emu-a500 --emu-32`; 204/204 con `--emu-32 --memcheck`; ejemplos 33/33.

### 2026-10-16 — Tarea 15b (ReAction: menús y fichero)
- Hecho (6 builtins): `ra_menu_title`, `ra_menu_item`, `ra_menu_separator` (antes de `ra_window_open`; GadTools
  `CreateMenusA`/`LayoutMenusA` con la `VisualInfo` de la pantalla pública y `WINDOW_MenuStrip`), `RA_EVENT_MENU()`
  (-4) y `ra_menu_id()` (`WMHI_MENUPICK`; las selecciones múltiples se entregan una por llamada), `ra_add_getfile`
  (botón de `getfile.gadget`; al pulsarlo el runtime abre el selector con `GFILE_REQUEST` y luego devuelve el id;
  `ra_get_string` da `GETFILE_FullFile`). `GadToolsBase` definida una sola vez aunque el programa use GadTools y
  ReAction (`_DASH_GADTOOLSBASE`); si ReAction la abrió, la cierra. Menús, `VisualInfo` y gadtools liberados en
  `ra_window_close`.
- Probado en A1200 3.2 (`test_ra_menus`): un proceso elige "Salir" con el ratón (botón derecho sobre el título y bajando
  a la opción) y llega `RA_EVENT_MENU()` con `ra_menu_id()` = 12; `ra_get_string` del selector vacío da "".
- Sin probar: el requester de `getfile` (se queda esperando a que alguien elija; haría falta clicar en él).
- Tests: 136/136 sin emulador; 329/329 con `--emu --emu-a500 --emu-32`; 206/206 con `--emu-32 --memcheck`; ejemplos 33/33.

### 2026-10-16 — Tarea 16 (varias ventanas)
- Decidido: la API de una ventana se mantiene. Las ventanas de `window_create` (con gadgets por número) son la forma de
  tener varias ventanas con GadTools; `gt_*` y ReAction siguen siendo de una sola ventana (pasarlas a objetos sería
  rehacer las dos APIs, y para aplicaciones con muchas ventanas está MUI). Documentado así en el manual.
- Hecho: un `EventLoop` escucha también las ventanas de `window_create` (antes nadie leía sus mensajes: ni sus gadgets
  ni su botón de cerrar hacían nada). Cuando el programa usa ventanas por número, el codegen sustituye el `WaitPort`
  por `_dash_loop_wait` (espera las señales de todas) y la lectura por `_dash_loop_next` (la ventana del bucle primero,
  luego las demás; con `GT_GetIMsg` si hay gadgets). Nuevo builtin `event_window()`: número de la ventana del último
  mensaje, 0 = la del bucle. Sin ventanas por número el C sale igual que antes.
- Probado en las tres máquinas (`test_event_window`): con clics reales, el botón de la segunda ventana llega a `On
  Gadget` con `event_window()` = 1; su botón de cerrar llega a `On Close` con 1 (se cierra solo esa) y el de la
  principal con 0 (fin del bucle).
- No hecho: `window_check_close` sigue vaciando el puerto con `GetMsg` y tirando lo que no es cerrar (cambiarlo podría
  dejar mensajes sin contestar en programas que solo preguntan por el cierre); documentado en la auditoría.
- Tests: 137/137 sin emulador; 333/333 con `--emu --emu-a500 --emu-32`; 204/204 con `--emu --memcheck`; ejemplos 33/33.

### 2026-10-16 — Tarea 17 (optimizar GadTools y ReAction)
- Hecho:
  - Los programas GadTools ya no abren `asl.library` ni crean un requester de ficheros al empezar si no usan un builtin
    de ASL (`_get_main_template` quita esas líneas; antes `needs_gadtools` forzaba `needs_asl`).
  - `IDCMP_INTUITICKS` (10 despertares por segundo) solo en ventanas con un listview (lo necesitan sus flechas); antes
    en toda ventana con gadgets por número y en las de `gt_attach`.
  - Argumentos de builtins: los temporales `volatile` (necesarios para las macros del NDK con `register asm`) ya no se
    usan en las llamadas normales a funciones del runtime (`_dash_*`, `ra_*`, cada argumento una vez).
  - Fuera los dos avisos de GCC de runtimes viejos (`diminfo` sin usar, `_dash_nil_area` sin usar).
- Medido (42 programas: los 33 ejemplos y los tests de GUI, `./dash` por defecto): 390.840 → 390.064 bytes (-776,
  -0,2 %). Los que más bajan: `test_gadgets` -244, `test_gt_events` -208, `test_gt_values` -104, `mui_navegador` -76.
  El ahorro en tamaño es pequeño; lo que cambia es el trabajo al arrancar (sin abrir ASL) y en reposo (sin ticks).
- No hecho: cada gadget por número tiene su `VisualInfo` y su lista (`GetVisualInfo`, `CreateContext`, `AddGList`,
  `RefreshGList` por gadget): es lo que permite crearlos en cualquier momento y en cualquier ventana; agruparlos cambiaría
  la API. `listview_add` redibuja la lista entera en cada línea (GadTools obliga a quitar y poner la lista).
- Tests: 137/137 sin emulador; 333/333 con `--emu --emu-a500 --emu-32`; 204/204 con `--emu --memcheck`; ejemplos 33/33.
