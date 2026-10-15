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
  Sospecha: MUI pide un volumen (`MUI:`, `ENV:MUI`, `Images`...) y espera en un requester. Es la tarea 1.

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
   `DASH_EMU_SYS_32=~/.cache/dash-emu/sys32`. **Sin `DASH_KICKSTART` se usa la ROM AROS** y los
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

## Diseño propuesto (se fija en la tarea 2)

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

- [~] 1. **Entorno.** `tools/get_mui_sdk.sh` (descarga, comprueba tamaño y extrae en `~/.cache/dash-mui`)
      y un sistema emulado con MUI (`tools/emu_sys_mui.sh` → `~/.cache/dash-emu/sys31mui`, variable
      `DASH_EMU_SYS_MUI`; ver qué más necesita: `MUI:`, `ENV:MUI`, `Images`, `Locale`). Arreglar el cuelgue
      de `hola_mui.c` (sacar la salida con `--keep` y captura de pantalla de FS-UAE si hace falta) hasta que
      abra y cierre la ventana. El runner usa ese sistema para los tests `# emu-needs: muimaster.library`.
      Probar también en `--emu-32` (OS 3.2).
- [ ] 2. **Diseño.** Fijar la API (sección de arriba) con el caso del navegador delante: ventana con barra de
      URL, botones atrás/adelante/recargar, zona de página con scroll, barra de estado y progreso. Escribirlo
      en `docs/MUI_DISEÑO.md` con un ejemplo en Dash de esa ventana. Decidir si la sintaxis declarativa entra.
- [ ] 3. **Núcleo.** `mui_app_begin(title, base)`, `mui_window_begin(title)`/`mui_window_end()`, grupos
      vertical y horizontal, `mui_text`, `mui_button`, `mui_window_open`, `mui_wait_event`, `mui_app_end`,
      `mui_on_close`, `mui_on_press`. Inclusión condicional del runtime y de las cabeceras. Test en emulador
      (pulsación simulada con `MUIA_Pressed`/`set` o cierre por modo test). Ejemplo `examples/mui_hola.dash`.
- [ ] 4. **Valores.** Campo de texto (`mui_string`), casilla, ciclo, deslizador, barra de progreso
      (`Gauge`), `mui_get_text`/`mui_set_text`, `mui_get_value`/`mui_set_value`, deshabilitar, `on_change`/`on_ack`.
- [ ] 5. **Listas.** `List` + `Listview` de textos: añadir, borrar, vaciar, activo, doble clic. Comprobar memoria.
- [ ] 6. **Estructura.** Menús (`Menustrip`), pestañas (`Register`), `Balance`, `Scrollgroup`/`Virtgroup`,
      varias ventanas, barra de estado. `--memcheck` sin restos.
- [ ] 7. **Zona de dibujo propia.** Clase propia (`MUI_CreateCustomClass`) con `AskMinMax`, `Draw`,
      `HandleEvent` (ratón, rueda, teclado) y scroll: dibujar con los builtins `gfx_` sobre el `RastPort`
      del objeto, y avisar a Dash con un número de evento cuando haya que repintar. Es la pieza del navegador:
      medir en el A1200 cuánto tarda en repintar.
- [ ] 8. **Señales externas.** `mui_wait_event_signals(mask)` para atender sockets y temporizador sin
      bloquear la interfaz. Test con `timer.device` o una señal propia.
- [ ] 9. **Imágenes.** `Dtpic` (datatypes) para PNG/JPEG/GIF en un objeto; o dibujar un bitmap en la zona propia.
- [ ] 10. **Ejemplo del navegador.** `examples/mui_navegador.dash`: la ventana del diseño (sin red), con
      historial falso y la página pintada en la zona propia. Captura de pantalla en el emulador.
- [ ] 11. **Repaso de MUI.** Tamaño del ejecutable, memoria (`--memcheck`), tiempos de apertura en A1200,
      revisión del C generado.

### ReAction y GadTools (petición del usuario del 2026-10-15: terminarlos, mejorarlos, optimizarlos, corregir bugs)

Hoy: 62 builtins `ra_` y 15 `gt_` (más 6 de menús), con **un único estado global** (una ventana, gadgets
por número). ReAction solo se prueba en `--emu-32` (la `window.class` de 3.1 no está en la ROM).

- [ ] 12. **Auditoría.** Leer el runtime de los dos (en `compiler/amiga_builtins.py`/`codegen.py`) y sus tests.
      Anotar en la bitácora: bugs (recursos sin liberar, `IDCMP` mal atendidos, valores que no se leen bien,
      textos que se liberan mientras el gadget los usa), qué falta para una aplicación normal, y qué cuesta
      de más (tamaño de runtime, trabajo por evento). Dividir las tareas 13-16 según lo que salga.
- [ ] 13. **Bugs.** Corregir lo encontrado en la 12, cada uno con su test (en emulador cuando se pueda).
- [ ] 14. **GadTools completo.** Gadgets que faltan: ciclo (`CYCLE_KIND`), opciones (`MX_KIND`), lista
      (`LISTVIEW_KIND`), scroller, número (`NUMBER_KIND`); `gt_set_string`, deshabilitar, refresco
      (`GT_RefreshWindow`, `GT_BeginRefresh`), posiciones según la fuente de la pantalla. Probar en A500 y A1200.
- [ ] 15. **ReAction completo.** Clases que faltan: `listbrowser`, `clicktab` (pestañas), `radiobutton`,
      `getfile`, `fuelgauge`, `button` con imagen; menús en ventanas ReAction; `ra_set_*`/`ra_get_*` que falten.
- [ ] 16. **Varias ventanas.** GadTools y ReAction con objetos como valores (como MUI, tarea 2), manteniendo
      la API actual de una ventana para no romper programas. Si choca con la compatibilidad, `[?]`.
- [ ] 17. **Optimizar.** Emitir solo la parte del runtime que el programa usa (como ya pasa con otros
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
