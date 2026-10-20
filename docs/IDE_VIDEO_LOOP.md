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
- [ ] v3. **1. Primer proyecto:** la guía de primeros pasos, Dash: Nuevo proyecto, qué hay en la carpeta.
- [ ] v4. **2. Escribir código:** colores, completar con parámetros, firmas, hover, ir a la definición, errores al
      teclear y su arreglo rápido, el `end` automático, formatear y renombrar.
- [ ] v5. **3. La ventana:** el editor visual (añadir un botón, propiedades, teclado, deshacer), Ver en Amiga, y
      de un evento a su código (creado).
- [ ] v6. **4. Compilar y ejecutar:** la tarea de compilar, un error en Problemas, ejecutar en el emulador (y
      elegir máquina), comprobación de memoria y perfil.
- [ ] v7. **5. Depurar:** F5, punto de parada, variables y pila en Dash, la consola con expresiones de Dash, paso
      a paso, un punto con condición, un error del programa que para como excepción.
- [ ] v8. **6. Un Amiga real:** Preparar para un Amiga real y la configuración de attach (con el emulador haciendo
      de Amiga).

### C. Caza de errores (casos raros)
- [ ] v9. **Rutas raras:** espacios, acentos y ñ en carpetas y ficheros (un proyecto "Mi Juego Ñandú"): compilar,
      ejecutar, depurar, Ver en Amiga, ir al evento.
- [ ] v10. **Texto raro:** CRLF, BOM, tabuladores, ficheros vacíos o de una línea, en `.dash` y `.dashui` (servidor
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

