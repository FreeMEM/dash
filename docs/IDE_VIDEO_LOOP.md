# Vídeo tutorial de la extensión de VS Code, y caza de errores (para `/loop`)

Arranque:

```
/loop Sigue las instrucciones de docs/IDE_VIDEO_LOOP.md en ~/Projects/FreeMEMLang-ide: haz UNA tarea y actualiza la bitácora. No hagas pausas entre vuelta y vuelta
```

## Objetivo

Antes de publicar la extensión (petición del usuario, 2026-10-20): **buscar errores y mejoras**. Se hace de dos
maneras:
- Construir un **vídeo tutorial con subtítulos** de la extensión: al grabar cada capítulo como lo haría un
  usuario salen fallos y cosas mejorables, como pasó con el tutorial de dashweb y el del complemento de QGIS.
- **Casos raros**, buscados con imaginación.

Cada fallo encontrado se arregla con su test.

## Cómo se graba (decidido el 2026-10-20, probado)

- **VS Code sin ventana:** el Electron de Code - OSS con `--ozone-platform=headless`. Lo lanza y lo maneja
  Playwright (`_electron.launch`, `playwright-core` en `~/.cache/dash-video/node_modules`, fuera de git).
  - No abre nada en la pantalla del usuario ni necesita el foco del escritorio.
  - Las teclas y los clics van por el protocolo de Chromium.
  - Perfil y carpeta de extensiones propios; la extensión, como `--extensionDevelopmentPath`.
- **El cursor:** dibujado dentro de la página del workbench (un elemento encima de todo, sin eventos). Se mueve
  hasta cada clic con una curva suave. Así las capturas lo llevan solo, también encima de los webviews.
- **Los fotogramas:** capturas de la ventana a ritmo fijo, con su hora. Luego ffmpeg (demuxer concat con
  duraciones) hace el MP4. Los subtítulos (SRT) salen del guion, con las horas reales de cada paso, y casan
  siempre. Es la técnica del vídeo de QGIS: memoria de geosian `reference_video_tutorial_qgis`.
- **Formato:** 1280x720, letra del editor grande para que se lea. Sin el panel de chat ni avisos de bienvenida
  (ajustes del perfil de rodaje). Tema oscuro por defecto.
- **El emulador** (FS-UAE sin ventana) sale en el vídeo por "Ver en Amiga" y por las capturas de `emu_run`.
  Para que se vea el Amiga ejecutando, se intercala su captura o un vídeo corto de `emu_run --screenshot`.

## Reglas de cada iteración

Las de `docs/IDE_LOOP.md` (uso al 90 %, rama `ide` sin push, base, una tarea, test con cada cambio, avisar a
dashweb antes de baterías largas del emulador, matar solo procesos propios, instalar el `.vsix`, documentar,
bitácora y commit `ide: v<n> - <resumen>`). Además:

- **Capítulo:** se escribe el guion (pasos y subtítulos, en español llano y frases cortas) y se graba. Después
  se miran fotogramas sueltos con Read, en los momentos de cada subtítulo. Cada problema o mejora va a la lista
  "Encontrado" de abajo, con su capítulo. Los pequeños se arreglan en la misma vuelta y se graba otra vez.
- **Caza:** cada caso raro se prueba de verdad (VS Code sin ventana, el servidor de lenguaje, el emulador). Si
  falla, test que lo reproduzca y arreglo.
- Lo grabado va a `~/.cache/dash-video/` y al scratchpad, nunca a git; los guiones y el programa de rodaje, sí
  (`editor/vscode/video/`).
- No publicar la extensión: lo decide el usuario.

## Tareas

### A. Rodaje
- [x] v1. **Programa de rodaje** (`editor/vscode/video/rodaje.js`): lanzar VS Code sin ventana con un perfil de
      rodaje (1280x720, letra grande, sin chat ni bienvenida). Funciones: `mover(objetivo)` y `clic(...)` con el
      cursor, `escribir(texto)` a ritmo humano, `tecla(...)`, `esperar(ms)`, `subtitulo(texto, ms)`, `captura`
      continua con su hora. Salida: MP4 (ffmpeg) y SRT. Prueba: un minuto de vídeo con un subtítulo y un clic.
- [x] v2. **Guion como datos** (`editor/vscode/video/capitulos/*.js`) y montaje de varios capítulos en un vídeo:
      portada, títulos de capítulo y subtítulos (SRT aparte y también quemados en otra copia).

### B. Capítulos (cada uno: guion, grabar, mirar, apuntar, arreglar, regrabar)
- [x] v3. **1. Primer proyecto:** la guía de primeros pasos, Dash: Nuevo proyecto, qué hay en la carpeta.
- [x] v4. **2. Escribir código:** colores, completar con parámetros, firmas, hover, ir a la definición, errores al
      teclear y su arreglo rápido, el `end` automático, formatear y renombrar.
- [x] v5. **3. La ventana:** el editor visual (añadir un botón, propiedades, teclado, deshacer), Ver en Amiga, y
      de un evento a su código (creado).
- [x] v6. **4. Compilar y ejecutar:** la tarea de compilar, un error en Problemas, ejecutar en el emulador (y
      elegir máquina), comprobación de memoria y perfil.
- [x] v7. **5. Depurar:** F5, punto de parada, variables y pila en Dash, la consola con expresiones de Dash, paso
      a paso, un punto con condición, un error del programa que para como excepción.
- [x] v8. **6. Un Amiga real:** Preparar para un Amiga real y la configuración de attach (con el emulador haciendo
      de Amiga).

### C. Caza de errores (casos raros)
- [x] v9. **Rutas raras:** espacios, acentos y ñ en carpetas y ficheros (un proyecto "Mi Juego Ñandú"): compilar,
      ejecutar, depurar, Ver en Amiga, ir al evento.
- [x] v10. **Texto raro:** CRLF, BOM, tabuladores, ficheros vacíos o de una línea, en `.dash` y `.dashui` (servidor
      de lenguaje, formatear, `end` automático, editor visual, diagnósticos).
- [ ] v11. **Sin guardar y sin carpeta:** ficheros sin título o sin guardar, sin carpeta abierta, varios `.dash` con
      el mismo nombre en carpetas distintas, espacio de trabajo con varias carpetas.
- [ ] v12. **Falta algo:** sin toolchain, sin ROM, sin SDK de MUI, sin bgdbserver, `dash.path` mal: que cada cosa diga
      claramente qué falta y cómo se arregla.
- [ ] v13. **A la vez:** F5 dos veces, Ver en Amiga mientras se depura, compilar mientras se ejecuta, cerrar VS Code
      con el emulador en marcha (¿quedan procesos?).
- [ ] v14. **`.dashui` extremos:** 200 objetos, nombres con acentos, tipos desconocidos, JSON roto, el mismo fichero
      abierto a la vez como texto y en el editor visual.
- [ ] v15. **Depurador al límite:** recursión profunda, una lista que se contiene, textos enormes, diccionarios grandes,
      punto de parada en una línea vacía o un comentario, en un módulo importado y en `@native`.
- [ ] v16. **Servidor de lenguaje al límite:** teclear deprisa en `lib/maqueta.dash` (4.778 líneas), renombrar a un
      nombre que ya existe o a una palabra reservada, completar dentro de `#{...}`, hover en builtins de MUI.

### D. Final
- [ ] v17. **Montaje:** el vídeo entero (MP4 con subtítulos aparte y quemados), en `~/Videos` o donde diga el usuario,
      y enviado al usuario.
- [ ] v18. **Repaso:** todo lo arreglado con sus tests, versión 0.2.1 y CHANGELOG; resumen para decidir la publicación.

## Encontrado (fallos y mejoras; cada uno pasa a tarea o se arregla en su vuelta)

- [x] (v1) Al escribir `Print "adiós"` se abría la lista de completar entera tras la comilla de cierre: `"` y `/`
      disparan el completado (para las rutas de `import`) y fuera de un `import` el servidor daba todo. Igual con
      `.` tras un número (`1.`). Arreglado en `compiler/lsp.py` con su test.
- [x] (v1) La acción de la pestaña de un `.dash` ponía el texto "Ejecutar en emulador" (sin icono). Ahora es ▶, y
      su desplegable trae también Depurar.
- [x] (v1) En el vídeo, el título de la ventana dice "[Extension Development Host]": grabar con la extensión
      instalada desde el `.vsix` en el perfil de rodaje (v2).

- [x] (v3) El paso "Dónde está el compilador" de la guía no salía hecho aunque el compilador ya se encontraba
      (solo se marcaba al cambiar el ajuste). Ahora la clave de contexto `dash.compilerFound` lo marca.
- [x] (v3) Los comentarios del programa de la plantilla eran tan largos que se cortaban en la pantalla: más cortos.
- [ ] (v3) Un paso de la guía se marca hecho al pulsar su botón, aunque luego se cancele ("Nuevo proyecto"). Es
      como funcionan las guías de VS Code (`onCommand`); se queda así.
- [ ] (v3) `ventana.dashui` sale en el explorador con el icono de JSON: es JSON para tener sus funciones al
      editarlo como texto; darle icono propio pide un lenguaje aparte y las perdería. Se queda así.

- [x] (v4) Al escribir una comilla sobre el hueco seleccionado de un parámetro (`mui_set_text(obj, text)`), VS
      Code la rodeaba de comillas y al cerrar el texto quedaba `"Otra vez""`. Quitada la comilla de
      `surroundingPairs` (ahora la sustituye y se cierra bien). Test.
- [ ] (v4) La ayuda de las órdenes (hover, completar) está en inglés, con el resto de la extensión en español:
      viene de las descripciones de `compiler/amiga_builtins.py` (425). Traducirlas, o tener las dos, es grande:
      se apunta para después de publicar.
- [ ] (v4) En el hueco de un parámetro, escribir `v.` abre la lista de campos y Tab la acepta en vez de saltar
      al hueco siguiente: así funciona VS Code (Esc y luego Tab). Se queda así.

- [x] (v5) Los campos de propiedades y los botones del editor visual salían blancos, como en un navegador, sin los
      colores del tema de VS Code. Ahora usan sus variables (`--vscode-input-*`, `--vscode-button-*`).
- [ ] (v5) Un `.dashui` abierto desde la línea de órdenes al arrancar VS Code (`code carpeta ventana.dashui`) sale
      como JSON en texto, no en el editor visual (desde el explorador o Ctrl+clic, sí). Investigar si es cosa de
      VS Code (el editor propio aún no está registrado al abrir los ficheros del arranque) y si se puede reabrir
      solo sin estorbar a quien lo abrió como texto a propósito.

- [x] (v6) La salida de compilar y ejecutar llevaba la orden entera ("mkdir -p … && '…/dash' … && python3 …
      emu_run.py …") y cada orden de `./dash` y gcc: ruido. Ahora `./dash -q` (nuevo: solo avisos, errores y el
      resultado), tareas sin eco, y las de ejecutar ponen en palabras qué hacen ("Ejecutar en el emulador: x.dash…").
- [x] (v6) Un error salía dos veces en Problemas: del servidor de lenguaje y del comprobador `$dash` de la tarea.
      Con el servidor encendido la tarea ya no usa `$dash` (quedan `$gcc` y el de memcheck).
- [x] (v6) `c = c + 1x` daba el error en el `end` de la línea siguiente ("no se esperaba `end` aquí"). Ahora sale
      donde está: "no se esperaba el fin de la línea después de `x`; se esperaba `(`, `.`, `=` o `[`". Test.

- [x] (v7) F11 sobre `suma = suma + doble(puntos[i])` entraba en el C del runtime (`DashArray_get` de
      `build/partida.c`) y dejaba abierta esa pestaña. Ahora `tools/gdb/dash.py` pone `skip` a lo que no es de un
      `.dash` (el runtime, el C de los structs, las librerías): F11 entra en `doble`. Comprobado en el vídeo.
- [x] (v7) Sin la ventana del emulador (`dash.emulator.window: false`), `emu_run.py` cortaba la sesión de depurar a
      los 60 s ("Remote connection closed"). Con `--gdbserver` ya no hay límite salvo `--timeout`. Test unitario.
- [x] (v7) La primera parada decía "Paused on attach": VS Code veía la parada de engancharse y luego la extensión
      seguía a sus espaldas. Ahora el proxy se la traga y sigue tras `configurationDone` (salvo `stopOnEntry`). Test.
- [x] (v7) Ruido de gdb: mensajes rojos al arrancar ("No source file named…", "No symbol table is loaded", puntos
      "pending" que luego funcionan), los filtros de excepciones de Ada y C++ en Puntos de parada, y el grupo
      Registers en las variables. Quitados en el proxy (los registros siguen con `-exec info registers`). Test.
- [x] (v7) Rodaje: el perfil no apagaba la ventana del emulador (`dash.emulator.window` es `true` por defecto). En
      v6 FS-UAE pudo abrir ventanas en el escritorio. Ahora el perfil la apaga. Y un subtítulo nuevo corta el
      anterior (en v7 se pisaban dos tras un corte).
- [ ] (v7) En la primera parada "Locals" sale plegado (en las siguientes, abierto); gdb da los mismos scopes. Parece
      cosa de VS Code al abrir la vista de depurar en ese momento. En el vídeo se abre con un clic. Se queda así.

- [x] (v8) El texto de "Preparar para un Amiga real" decía "F5 con la configuración Amiga real", pero F5 arranca la
      elegida en Ejecutar y depurar (la primera es la del emulador). Ahora dice que se elija (o "Debug: Select and
      Start Debugging"). El vídeo aún enseña el texto viejo: se regraba en v17.

- [x] (v9) `./dash -o carpeta/x` con una carpeta que no existe acababa en un traceback de Python (`shutil.move`).
      Ahora la crea. Y `-q` dejaba pasar "Transpiled! …". Test (`tests/unit/test_dash_cli.py`, ruta con ñ).
- [x] (v9) "Dash: Nuevo proyecto" con "Mi Juego Ñandú" daba `Mi_Juego_and` ("Árbol", `rbol`): borraba las
      letras con tilde. Ahora les quita la tilde: `Mi_Juego_Nandu`, `Arbol`. Test.
- [x] (v9) Al compilar un programa MUI, gcc avisaba de `GetVPModeID` sin declarar (runtime de MUI); el lienzo de MUI
      llamaba a `layers.library` sin su cabecera, igual. Sin prototipo, la llamada va por el stub de libamiga en
      el mejor caso. Puestas sus cabeceras, y el runner compila los tests con
      `-Werror=implicit-function-declaration`: salieron esos 19 tests (y `sqrt` sin declarar en un `@native`
      de un test). Probado en el emulador (lienzo, FPU, `.dashui`, pantalla completa).
- [ ] (v9) Ojo para el futuro: incluir `<math.h>` en el runtime de Float rompe un programa con una función
      `round` o `sin` propia (choca con su prototipo). No se incluye.
- [ ] (v9) El editor visual abierto en media pantalla (junto al `.dash`) se aprieta: el árbol queda en una columna
      de 40 píxeles y "Ver en Amiga" en dos líneas. Para v14 (`.dashui` extremos).

- [x] (v10) Un `.dash` con BOM (Bloc de notas de Windows) no compilaba: "carácter inesperado '\ufeff'". Uno en
      Latin-1 (un editor del Amiga) acababa en un `UnicodeDecodeError` de Python. Ahora `read_source` quita el
      BOM y lee Latin-1 si no es UTF-8 (compilador, imports y servidor de lenguaje). Tests unitarios.
- [x] (v10) Un `.dash` en Latin-1 se veía en VS Code con caracteres rotos: la extensión pone
      `files.autoGuessEncoding` para `[dash]`. Comprobado en VS Code (sin el ajuste, "Ca�a").
- [x] (v10) Formatear un fichero CRLF ya bien formateado lo daba cambiado (con `\n`): con "formatear al guardar"
      quedaría siempre modificado. Ahora conserva CRLF. Test.
- [x] (v10) Cualquier módulo sin `Main` abierto en VS Code salía con el aviso "Program has no Main block" en
      Problemas. El servidor ya no lo da; en la línea de órdenes sale en español. Test.
- [x] (v10) Una línea que acaba en `+` (o `and`, `==`…) sigue en la siguiente, y el error salía más abajo con un
      mensaje que despistaba ("¿falta un `end`?", "no se esperaba `=`"). Ahora añade "(la línea 3 acaba en `+`: la
      expresión sigue en la siguiente)". Test en `tests/errors`.
- [x] (v10) El editor visual comparaba su texto (`\n`) con el del documento (CRLF): cualquier acción, aunque no
      cambiara nada, reescribía el fichero entero. Ahora compara sin los `\r`. "Ver en Amiga" quita el BOM.

## Bitácora

### 2026-10-20 — v1 (programa de rodaje)
- `editor/vscode/video/rodaje.js`:
  - `Rodaje.start({workspace, open, settings})`: el Electron de Code - OSS con `--ozone-platform=headless`, por
    Playwright. Perfil propio: letra 17, sin chat ni bienvenida ni minimapa. Ventana 1280x720.
  - El cursor es un elemento dentro del workbench (hecho elemento a elemento: el workbench exige Trusted Types y no
    acepta `innerHTML`), con un anillo al hacer clic.
  - `mover` (curva suave, también el ratón de verdad), `clic`, `escribir` a ritmo humano, `tecla`, `orden`
    (F1 y su nombre), `subtitulo` y `decir`.
  - Las capturas van a unos 8 por segundo, con su hora.
  - `fin(out)`: `out.mp4`, `out.srt` y `out-sub.mp4` con los subtítulos quemados (ffmpeg). Cada fotograma de
    30 por segundo es un enlace a la captura de su momento: la duración sale exacta (con el concat de ffmpeg y
    duraciones salía 8,2 s de 8,9).
- Prueba de 8 s (abrir, clic en el explorador, escribir una línea, dos subtítulos): sin abrir nada en la pantalla
  del usuario. Al mirarla salieron los dos primeros fallos de "Encontrado", arreglados.
- Tests: node (SRT y un vídeo de 3 s exacto con tres fotogramas), servidor de lenguaje (22: los caracteres que
  disparan el completado). Base: todo bien.

### 2026-10-20 — v2 (guiones como datos y montaje)
- `video/rodaje.js`: con `vsix`, instala la extensión en el perfil de rodaje con la línea de órdenes de VS Code
  (`ELECTRON_RUN_AS_NODE=1 electron out/cli.js code.mjs --install-extension`). Así se graba como la tiene un
  usuario, sin "[Extension Development Host]" en el título. `fin` deja también `out.json` (duración y subtítulos).
  Subtítulos en tamaño 13 (libass escala a su pantalla de referencia: el 18 salía enorme).
- `video/grabar.js`:
  - empaqueta la extensión (`npm run package`) y graba cada capítulo de `video/capitulos/NN_*.js` (`titulo`,
    `resumen`, `preparar`, `open`, `guion`) en una carpeta propia;
  - hace la portada y una tarjeta de título por capítulo (ffmpeg, DejaVu, el azul del icono) y lo junta todo:
    `tutorial.mp4`, `tutorial.srt` (cada subtítulo desplazado a su sitio) y `tutorial-sub.mp4`;
  - opciones `--solo 3,5` y `--dev`. Si un capítulo falla, deja captura y vídeo de lo grabado hasta ahí.
- Capítulo 1 provisional (se completa en v3). Probado: portada, título y capítulo, 14 s, subtítulos en su sitio.
- Tests: node (tarjetas y `juntar`: duración y desplazamiento de subtítulos; escape de textos de drawtext).

### 2026-10-20 — v3 (capítulo 1: primer proyecto)
- `video/capitulos/01_primer_proyecto.js`: VS Code sin carpeta; la guía (Welcome: Open Walkthrough), el paso del
  compilador ya hecho, Nuevo proyecto (nombre y carpeta en el diálogo de VS Code), la ventana se recarga con el
  proyecto y se explica cada fichero. 65 s, 11 subtítulos.
- Rodaje: `files.simpleDialog.enable` (los diálogos del sistema no se ven sin ventana), VS Code sin carpeta
  (`workspace: null`), `recargada()` tras abrir una carpeta en la misma ventana. `grabar.js`: `sinCarpeta`.
  Revisión con una hoja de contactos de fotogramas a mitad de cada subtítulo (scratchpad `vid/hoja.py`).
- Encontrado: el paso del compilador sin marcar, y los comentarios largos de la plantilla. Arreglados y
  regrabado. Dos cosas que se quedan como están (ver "Encontrado").
- Tests: node todo bien.

### 2026-10-20 — v4 (capítulo 2: escribir código)
- `video/capitulos/02_escribir_codigo.js` (sobre los ficheros del proyecto nuevo):
  - los colores;
  - un error tecleado (`vecs`), subrayado al momento, con su arreglo rápido (Ctrl+. → "Cambiar a 'veces'");
  - completar `mui_set_t` con sus huecos;
  - el `end` que se pone solo tras un `if`;
  - la ayuda al pasar el ratón;
  - Ctrl+clic en `Hola_create`, que lleva a la ventana en el editor visual, y vuelta;
  - F2 de `veces` a `pulsaciones`, también dentro de `#{...}`.
  68 s, 10 subtítulos.
- Rodaje: `clic(..., {modifiers})`, `linea(texto)` y `palabra(texto)` para apuntar al editor.
- Encontrado: la comilla sobre un hueco (arreglado, test), la ayuda en inglés (apuntado) y Tab con la lista
  abierta (es de VS Code).
- Tests: node todo bien.

### 2026-10-20 — v5 (capítulo 3: la ventana)
- `video/capitulos/03_la_ventana.js`:
  - la ventana se abre desde el explorador;
  - un botón nuevo tras el texto (paleta) y sus propiedades (nombre `otro`, texto `_Otro`, evento 3);
  - moverlo con Alt+flechas, deshacer y rehacer;
  - "Ver en Amiga": la ventana real en el A1200 con MUI, con el botón nuevo;
  - la flecha del evento: aviso "hola.dash no trata el evento 3", "Crear", y queda `const ID_OTRO = 3` con su
    `if` en el bucle.
  67 s, 10 subtítulos.
- Rodaje: `web(selector)` para el webview (dos iframes anidados).
- Encontrado: colores del editor visual (arreglado) y un `.dashui` abierto al arrancar sale como texto
  (apuntado para investigar).
- De paso, fuera del bucle: el PR #3 (Trasfondo: CPU y lienzo, 573/573 en el emulador) y el #4 (`break_check`,
  `single_instance`) fusionados en main de Dash, desde la rama `trasfondo`.
- Tests: node todo bien.

### 2026-10-20 — v6 (capítulo 4: compilar y ejecutar)
- `video/capitulos/04_compilar_ejecutar.js`: un programa que cuenta primos:
  - compilar con el CodeLens;
  - un error, que va a Problemas;
  - ejecutar en FS-UAE ("Hay 303 primos hasta 2000");
  - cambiar a A500 en la barra de estado y otra vez;
  - "Perfil", con su tabla (es_primo 66 %).
  48 s de vídeo de unos 70 de rodaje.
- Rodaje:
  - `saltar(trabajo)`: sin capturas mientras el emulador trabaja, el vídeo salta (corte);
  - `irALinea(n)` con Ctrl+G;
  - terminal sin aceleración gráfica (su texto se lee en la página; antes cada espera agotaba su tiempo y
    la toma tardaba 10 minutos).
- Encontrado y arreglado: ruido en la terminal (`./dash -q`, sin eco), errores duplicados en Problemas, y el
  sitio del error de una línea sin terminar (`compiler/main.py`, `tests/errors/syntax_unfinished_line.dash`).
- Tests: base 292, node todo bien.

### 2026-10-20 — v7 (capítulo 5: depurar)
- `video/capitulos/05_depurar.js`: un programa que suma puntos y se sale de la lista:
  - punto de parada con un clic en el margen y F5;
  - variables (el texto, la lista abierta con sus elementos);
  - la consola con `puntos[i] * 2` y `nombre.length`;
  - F11 a `doble` con su pila, Mayúsculas+F11 y F10;
  - punto con condición `i == 3`;
  - sin el punto, el error "índice fuera de la lista" para como excepción.
  76 s, 11 subtítulos.
- Rodaje: `margen(texto)` (el margen de una línea, para los puntos de parada).
- Encontrado y arreglado: F11 entraba en el runtime, la sesión se cortaba a los 60 s sin ventana, "Paused on
  attach", ruido de gdb. `DASH_DAP_LOG=fichero` deja todos los mensajes entre VS Code y gdb (así salió el corte
  de los 60 s).
- `test/integration/run.sh`: `DASH_IT_FLAGS=--ozone-platform=headless` los pasa sin ventana en la pantalla.
- De paso, fuera del bucle: D62 para dashweb (alfa de verdad en imágenes en RTG), PR #5 fusionado en main.
- Tests: base 295, node todo bien, integración de VS Code 21/21 (sin ventana).

### 2026-10-20 — v8 (capítulo 6: un Amiga de verdad)
- `video/capitulos/06_amiga_real.js`, con el emulador haciendo de Amiga (`emu_run.py --gdbserver PORT --no-relay`,
  lanzado por el guion y parado al final por su grupo de procesos):
  - "Dash: Preparar para un Amiga real" y sus pasos en "Dash: Amiga";
  - qué hace falta en el Amiga (pila TCP/IP, bgdbserver) y la orden de su Shell;
  - en `launch.json`, "Amiga real" con la dirección (`localhost:PUERTO` en el vídeo);
  - punto de parada, "Debug: Select and Start Debugging" → "Amiga real", parada con variables y otra vuelta.
  77 s, 10 subtítulos. Funcionó a la primera: gdb_relay en medio, globales y pasos como en el emulador.
- Encontrado: el texto de los pasos (arreglado).
- Tests: node todo bien.

### 2026-10-20 — v9 (rutas raras)
- Un proyecto de "Nuevo proyecto" en `…/v9 ñ XXXX/Mi Juego Ñandú/`, con `juego ñandú.dash` y `ventana ñ.dashui`
  (y su `import`), en VS Code sin ventana (`v9probe.js` del scratchpad): el servidor de lenguaje sin errores,
  compilar, `bin/juego ñandú`, ejecutar (con autoclose), depurar (para en el punto), Ver en Amiga e ir al evento.
  Todo bien. Por la línea de órdenes, un `import "sub carpeta/útil ñ.dash"` también.
- Encontrado y arreglado: `-o` a una carpeta nueva, `-q` con "Transpiled!", nombres con tilde en Nuevo proyecto,
  llamadas sin prototipo en los runtimes de MUI (con la regla nueva del runner). El CLAUDE.md del proyecto no
  está en git: la regla nueva del runner hay que apuntarla allí al fusionar.
- Tests: base 296, emulador (A1200 y 3.2) de lienzo, FPU, `.dashui`, pantalla completa y autoclose bien;
  `./compile_all.sh` 34/34; node todo bien.

### 2026-10-20 — v10 (texto raro)
- Por la línea de órdenes: CRLF, BOM, tabuladores, mezcla, vacío, una sola línea, sin salto final, solo un
  comentario, Latin-1, un `.dashui` con BOM y otro en Latin-1. Fallaban el BOM y el Latin-1.
- Servidor de lenguaje (`v10lsp.py` del scratchpad): diagnósticos, formatear, renombrar, hover, definición,
  símbolos y completar con CRLF, tabuladores y un fichero vacío. Fallaban formatear con CRLF y el aviso sin `Main`.
- VS Code sin ventana (`v10probe.js`): el `end` automático con tabuladores, un `.dash` en Latin-1, formatear un
  CRLF, y un `.dashui` con BOM y CRLF en el editor visual (lo lee, no lo marca modificado, al guardar conserva
  BOM y CRLF). Todo bien con los arreglos.
- Tests: base 301, LSP 26, node todo bien.

