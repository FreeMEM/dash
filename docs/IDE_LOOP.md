# Entorno de desarrollo de Dash para VS Code (para `/loop`)

Arranque:

```
/loop Sigue las instrucciones de docs/IDE_LOOP.md en ~/Projects/FreeMEMLang-ide: haz UNA tarea y actualiza la bitácora. No hagas pausas entre vuelta y vuelta
```

## Objetivo

Que la extensión de VS Code (`editor/vscode/`) se acerque lo más posible a un IDE profesional para Dash y
`.dashui` (petición del usuario, 2026-10-20): colores completos, errores mientras se escribe, autocompletado,
ir a la definición, esquema del fichero, compilar y ejecutar con un clic, y **depuración con breakpoints,
paso a paso, pila y variables**, en el emulador y, si se puede, en un Amiga real.

## Datos de partida (comprobados el 2026-10-20)

- **Extensión:** `editor/vscode/` (JavaScript, sin compilar; `npm test`, `npm run package` = `vsce package
  --no-dependencies`). Trae gramática TextMate (`syntaxes/dash.tmLanguage.json`, 103 líneas, a mano),
  compilar y ejecutar en FS-UAE por terminal, y el editor visual de `.dashui` (webview) con "Ver en Amiga".
  Instalada en Code - OSS 1.138 (`code --install-extension <vsix> --force`; ajustes del usuario en
  `~/.config/Code - OSS/User/settings.json`: `dash.path`, `dash.emulator.*`).
- **Modo restringido:** desde caa3570 la extensión es `untrustedWorkspaces: limited` (colores y editor siempre;
  compilar y emulador, solo con confianza). Sin eso, VS Code la apagaba entera y no había colores.
- **Depuración:** ni FS-UAE 3.2.35 ni Amiberry 8.2.2 traen servidor GDB (WinUAE sí; uae-dap usa FS-UAE y WinUAE
  parcheados). La toolchain trae `m68k-amigaos-gdb` 18 (`/opt/amiga/bin`), que habla DAP (`gdb -i=dap`), y
  `m68k-amigaos-addr2line`/`objdump`. En el Amiga: `bgdbserver` de bebbo (Aminet `dev/debug/bgdbserver`, GPLv3,
  servidor GDB por TCP con `bsdsocket.library`: vale en FS-UAE/Amiberry con su bsdsocket y en un Amiga real).
  FS-UAE también tiene su depurador de consola (`tools/emu_run.py --debug`, `debug_break()`).
- **Amiberry sin ventana:** ver la memoria `reference_amiberry_headless` (sirve para lo que FS-UAE no emula).

## Reglas de cada iteración

0. **Uso.** Lee `~/.claude/state/uso-7d.txt` (primer número = % de uso semanal). Con 90 o más: para el loop
   (ScheduleWakeup stop), apunta en la bitácora dónde quedó y avisa al usuario.
1. **Rama.** Worktree `~/Projects/FreeMEMLang-ide`, rama local `ide` (sale de caa3570: origin/main + D60 + los
   cambios de la extensión del 2026-10-20). No hagas push, ni toques `main`, `~/Projects/FreeMEMLang` ni el
   worktree `FreeMEMLang-dashweb` (es del loop de dashweb).
2. **Base.** `python3 tests/run_tests.py` y `cd editor/vscode && npm test`. Anota si cambia.
3. **Tarea.** La primera `[ ]`; márcala `[~]` mientras trabajas. Una por iteración; si es grande, divídela en la
   lista y haz la primera parte.
4. **Hacer.** Cada cambio con su test: `editor/vscode/test/run.js` (con el `vscode` falso) para la extensión,
   tests de Python para el servidor de lenguaje, `tests/` del runner para lo que toque al compilador.
   Lo visual se comprueba en un navegador (Playwright, `test/webview.html`) o con una captura (`grim`).
5. **Verificar.** Repite el paso 2. Si tocas el compilador: `python3 tests/run_tests.py --emu` (entorno de
   CLAUDE.md). **Antes de una batería en el emulador o una medida larga, avisa a la sesión de dashweb**
   (ListAgents; comparten FS-UAE y puertos). Mata solo procesos tuyos, por PID.
6. **Instalar.** Si cambió la extensión: `npm run package`, mueve el `.vsix` al scratchpad e instálalo
   (`code --install-extension ... --force`): el usuario la usa ya.
7. **Documentar.** `editor/vscode/README.md` y, si cambia el lenguaje o el compilador, `docs/`.
8. **Cerrar.** Marca `[x]`, entrada en la bitácora, commit local `ide: <tarea> - <resumen>`.
9. **Fin.** Sin tareas `[ ]`: resumen final, para el loop y avisa con PushNotification.

## Límites

- No instales paquetes del sistema. `npm install --save-dev` en `editor/vscode` sí (node_modules fuera de git);
  un venv en el scratchpad, sí. El servidor de lenguaje no puede pedir nada que Dash no pida ya (Python 3 y Lark).
- Nada con licencia que no permita redistribuir (bgdbserver es GPLv3: un script lo descarga, como el SDK de MUI).
- Un programa compilado sin la opción de depuración tiene que salir **idéntico** (mismo C) que antes.
- No publicar la extensión (Marketplace/Open VSX) sin permiso del usuario: déjalo `[?]`.
- Si una tarea exige una decisión del usuario, déjala `[?]` con la pregunta y pasa a la siguiente.

## Estructura (decidida en la tarea 1)

- **Extensión en JavaScript** (CommonJS, como ahora), con `// @ts-check` y JSDoc para que VS Code compruebe tipos;
  sin TypeScript: no hay paso de compilación para el código propio. Cuando lleguen dependencias de ejecución
  (`vscode-languageclient` en la tarea 4), **esbuild** las empaqueta en `dist/extension.js` (`npm run build`;
  `package` = build + `vsce package --no-dependencies`) y `main` apunta a `dist/`.
- **Servidor de lenguaje en Python**, dentro del compilador (`compiler/lsp.py`), sin dependencias más allá de las
  de Dash (Lark): reutiliza parser, transformer y analizador, así nunca discrepa del compilador. La extensión lo
  arranca con `python3 -m compiler.lsp` desde `dash.path`, **solo en carpetas de confianza** (ejecuta código de esa
  carpeta); en modo restringido quedan los colores y el editor visual.
- **Tests:** la extensión, en `test/run.js` (con el `vscode` falso y vscode-textmate para la gramática); el
  servidor, en `tests/lsp/test_*.py` (unittest, mensajes JSON-RPC reales por stdio), que `tests/run_tests.py`
  ejecuta y cuenta como un resultado cada uno.
- **Depuración (decidida en la tarea 12):** `bgdbserver` (Aminet, GPLv3, `tools/get_bgdbserver.sh`, en
  `~/.cache/dash-debug`) corre dentro del Amiga (FS-UAE y Amiberry con su bsdsocket, o uno real) con el programa;
  `m68k-amigaos-gdb -i=dap` (gdb 18 con Python: DAP nativo) es el adaptador de VS Code, conectado con `attach` y
  `target: "localhost:PUERTO"`. La extensión compila con información de depuración, arranca el emulador con
  `bgdbserver :PUERTO programa` y le pasa a gdb la configuración. Las líneas pasan de C a Dash con `#line` (tarea 13).

## Tareas

### A. Lenguaje
- [x] 1. **Auditoría y estructura.** Leer la extensión y sus tests; decidir cómo crece (¿TypeScript? ¿empaquetar
      con esbuild para llevar dependencias como `vscode-languageclient`?). Anotar la decisión aquí.
      **Decisión:** ver "Estructura" abajo.
- [x] 2. **Gramática completa, generada.** `tools/gen_tmgrammar.py` saca de `compiler/grammar.py` y
      `compiler/amiga_builtins.py` las palabras clave, tipos, directivas `@` y los 425 builtins; interpolación
      `#{...}`, números hex/binarios, `Window`/`EventLoop`/`On`, `@native`/`@c` con C dentro. El runner comprueba
      que está al día (como `docs/BUILTINS.md`). Tests de tokens.
- [x] 3. **Edición.** Snippets (func, struct, Main, EventLoop, ventana MUI...), sangría y `onEnter` con `end`,
      plegado por bloques, iconos de `.dash`/`.dashui`, comentar con `#`.

### B. Servidor de lenguaje (LSP)
- [x] 4a. **Posiciones en los errores.** Hoy solo 18 tipos de nodo guardan `location` y casi ningún error dice
      la línea (`Error: Variable 'b' is not defined`). Todos los nodos con línea, columna y fichero (también los de
      los módulos importados); la salida de `./dash` y `compiler.main` como `fichero:línea:col: Error: mensaje` (para
      el LSP y para el problem matcher de la tarea 9); el error de sintaxis de Lark, en una frase ("se esperaba
      `end`...") en vez de la lista de tokens. Tests de error (`tests/errors/`) con la línea.
- [x] 4. **Base y errores.** `compiler/lsp.py`: JSON-RPC por stdio sin dependencias, que reutiliza parser y
      analizador; cliente en la extensión (lo arranca con `python3 -m compiler.lsp` desde `dash.path`).
      Diagnósticos al escribir, con línea y columna (y los de los imports). Tests.
- [x] 5. **Autocompletado.** Builtins con firma y descripción, palabras clave, variables/funciones/structs/
      campos/enums en ámbito, rutas de `import`; ayuda de firma (signature help).
- [x] 6. **Navegación.** Hover (tipo, firma, doc), ir a la definición (también entre módulos y hacia el `.dashui`),
      referencias, resaltar las apariciones.
- [x] 7. **Símbolos.** Esquema del documento (Outline, breadcrumbs), símbolos del workspace, renombrar.
- [x] 8. **Formato y arreglos.** Formateador de sangría; acciones rápidas sencillas (crear la función que falta,
      añadir el `import`); tokens semánticos si mejoran los colores.

### C. Compilar y ejecutar
- [x] 9. **Tareas y errores.** TaskProvider (compilar, ejecutar, `--memcheck`, `--profile`), problem matcher del
      compilador de Dash y de gcc, barra de estado, CodeLens "Ejecutar" sobre `Main`.
- [x] 10. **Emulador.** Elegir máquina (A500, A1200 3.1, 3.2, RTG, Amiberry), salida del programa en un panel,
      parar, configuración por proyecto.
- [x] 11. **Memoria y perfil.** Avisos de `--memcheck` como diagnósticos; la tabla de `--profile` en un webview,
      con enlaces a las funciones.

### D. Depuración
- [x] 12. **Prueba de viabilidad.** `tools/get_bgdbserver.sh`; un programa Dash con `-g` en FS-UAE (y Amiberry) con
      bsdsocket; `m68k-amigaos-gdb` → `target remote`; parar en una función, ver registros y variables. Comparar
      con las alternativas (uae-dap, el depurador de consola de FS-UAE) y elegir. Si hace falta, `[?]`.
- [x] 13. **Dash con información de depuración.** `./dash --debug` (`-g -O0`, `#line` hacia el `.dash` en el C):
      gdb y addr2line hablan en líneas de Dash. Tests (C esperado; addr2line sobre el binario).
- [x] 14. **Adaptador.** Configuración de lanzamiento `dash` (launch.json): compila con `--debug`, arranca emulador y
      servidor, conecta gdb (DAP o MI). Breakpoints en `.dash`, continuar, paso a paso (entrar, saltar, salir), pausa.
- [x] 15. **Pila y variables.** Nombres de Dash (locales, globales, structs, Strings, listas, diccionarios) con
      pretty-printers de gdb en Python; ocultar el runtime `_dash_*` de la pila.
- [x] 16a. **Expresiones de Dash.** Consola de depuración (evaluar), watch, hover, breakpoints condicionales y
      logpoints con expresiones de Dash (`p.x`, `l[i]`, `s.length`, `and`/`or`/`not`, `nil`): un adaptador en medio
      que las traduce a C para gdb, y `$len`/`$at` en `tools/gdb/dash.py`.
- [x] 16b. **Salida y errores.** `Print` en la consola de depuración (bajo bgdbserver la salida va a su consola:
      `DASH_OUT`), y parar en los errores del runtime (índice fuera de rango, memcheck) con su mensaje.
- [x] 17. **Amiga real.** Depurar en un Amiga con bgdbserver por red (host y puerto configurables); documentarlo.

### E. `.dashui`
- [x] 18. **Editor visual.** Deshacer/rehacer, arrastrar, copiar y pegar, teclado, accesibilidad; auditoría primero.
- [x] 19. **Código y ventana.** Validación con diagnósticos; de un evento del `.dashui` a su código en el `.dash` y
      crear el que falte.
- [x] 20. **Vista en el Amiga.** Más rápida, repetible, en varias máquinas.

### F. Pulido
- [x] 21. **Primeros pasos.** Walkthrough de VS Code, comando "Dash: Nuevo proyecto" (plantilla con `.dash`,
      `.dashui` y launch.json), README con capturas.
- [x] 22. **Empaquetado.** Bundle, icono, versión 0.2.0, CHANGELOG; preparar la publicación.
- [?] 22b. **Publicar** en el Marketplace de VS Code y en Open VSX: lo decide el usuario (hacen falta el editor `FreeMEM` en cada sitio y sus tokens).
- [ ] 23. **Repaso final.** Todo junto con un proyecto real (dashweb): abrir, completar, compilar, depurar.

## Bitácora

### 2026-10-20 — Plan
- Pedido por el usuario: "un entorno de desarrollo como extensión para trabajar con dash y dashui", "breakpoints,
  debug", "lo más cercano posible a un IDE profesional", como /loop con plan y bitácora.
- Hecho antes del loop (rama dashweb, ya en esta rama): caa3570 (modo restringido) y 81686a7 (botón "Ver en Amiga").

### 2026-10-20 — Tarea 1 (auditoría y estructura)
- Base: `run_tests.py` todo bien; `npm test` todo bien (tras `npm ci` en el worktree nuevo).
- La extensión: 1450 líneas (extension.js 140, amigaPreview.js 95, dashuiEditor.js 54, webview 530, tests 330,
  gramática 103). Sin dependencias de ejecución; `vsce package --no-dependencies`. Gramática a mano y corta.
- Decisiones en "Estructura": JS con `@ts-check`, esbuild cuando haga falta, LSP en Python dentro del compilador,
  solo con confianza; tests de LSP en `tests/lsp` contados por el runner.
- Hallazgo: los errores semánticos casi nunca llevan línea (solo 18 tipos de nodo guardan `location`), y el de
  sintaxis es una lista de tokens de Lark. Sin eso no hay errores en el editor: nueva tarea 4a antes del LSP.
- Hallazgo menor (a mirar en 4a): `y = ` sin valor seguido de `Print noexiste(3)` en la línea siguiente da
  "Variable 'Print' is not defined": el `=` se come el salto de línea.

### 2026-10-20 — Tarea 2 (gramática generada)
- `tools/gen_tmgrammar.py` escribe `editor/vscode/syntaxes/dash.tmLanguage.json` desde `compiler/grammar.py`
  (palabras de la gramática, cada una con su color en `KEYWORDS`: si aparece una nueva sin color, el script para),
  `SemanticAnalyzer._TYPE_NAMES` y `get_all_builtins()` (los 425+, antes solo unos prefijos). Nuevo: directivas `@`
  (y `@native(borrow)`), bloque `Window` con sus propiedades, `On <evento>`, `Struct(...)` como constructor, tipos
  del programa tras `:`/`->`, `Fixed`, métodos de listas y diccionarios, `.length`, `.open`/`.close`, `self`, `weak`,
  `..`, constantes en mayúsculas, `#{...}` con expresiones (comillas `\"` dentro; un `#{` sin cerrar queda texto).
- El runner comprueba que está al día (`editor/tmgrammar`, como `docs/builtins`); probado que falla si no.
- Tests de la gramática: 6 nuevos en `test/run.js`. Repaso con los 317 `.dash` del repositorio y de dashweb: ningún
  bloque queda abierto al final (con la gramática de C de prueba; sin ella el `"""` no se reconoce, como en el test).
- `CLAUDE.md` no está en el repositorio (es local, de `~/Projects/FreeMEMLang`): la línea de `gen_tmgrammar.py` se
  añadirá allí al fusionar.
- Base: run_tests todo bien (más `editor/tmgrammar`); `npm test` todo bien. Extensión instalada.

### 2026-10-20 — Tarea 3 (edición)
- 17 snippets (`snippets/dash.json`): Main, func (con y sin tipos), struct, enum, if, ife, while, for (rango y
  lista), import, const, @native, Window con EventLoop, EventLoop, On (elige el evento), mui y muiui (MUI con
  `.dashui`). Un test compila cada uno con sus valores por defecto (`python3 -m compiler.main`).
- `endwise.js`: Enter al final de una línea que abre bloque añade su `end` si no lo tiene (no en `@extern`, ni en
  `enum E A, B end`, ni si el bloque ya cierra con `end`/`elif`/`else`); ajuste `dash.editor.autoEnd`. Y
  `else`/`elif`/`end` vuelven al nivel de su bloque al escribirlos: VS Code lo hace solo a veces (no si hay un
  `end` debajo, que es justo lo que deja el `end` automático).
- Cosas de VS Code aprendidas con la prueba real: la sangría que pone su Enter se borra en cuanto llega otra
  edición (`editor.trimAutoWhitespace`), y con un `end` debajo sangra como el `end`. Por eso el `end` y la línea
  nueva van en una sola edición (también: un Ctrl+Z lo quita todo).
- `language-configuration.json`: la sangría no sube tras un bloque de una línea; `@c` y `@native(borrow)` abren;
  plegado con `# region`; `wordPattern` con `@`. Icono para `.dash` (`media/dash-file.svg`). `.dashui` sigue como
  JSON (sin icono propio: cambiarle el lenguaje quitaría la validación JSON).
- **Tests dentro de VS Code** (`npm run test:vscode`, `test/integration/`): el Electron de Code - OSS con un perfil
  y carpeta de extensiones propios (no toca los del usuario; abre una ventana unos segundos). 6 pruebas: `end` al
  pulsar Enter, sin `end` doble, anidado, `else`, deshacer, snippets. Servirá para el LSP y la depuración.
- Base: run_tests todo bien; `npm test` 59 bien; `npm run test:vscode` 6 bien. Extensión instalada.

### 2026-10-20 — Tarea 4a (posiciones en los errores)
- `DashASTBuilder(filename)` da a cada nodo el sitio de su regla (`tree.meta` de Lark, que ya tenía
  `propagate_positions`) y el fichero, salvo que la regla ya pusiera uno más exacto; también a las definiciones de
  primer nivel (sus reglas devuelven `""` y van a listas: se miran las listas antes y después). Las expresiones de
  `#{...}` (otro parser, sin sitios) toman la línea del texto y la columna de la expresión.
- Formato como gcc: `fichero:línea:col: Error: mensaje` (`AnalysisError.__str__`); los de sintaxis en una frase
  (`sintaxis: no se esperaba `)` aquí; se esperaba ...`, o `¿falta un `end`?` si el fichero acaba antes) y los
  que lanza el transformer (constante no constante, número de más de 32 bits) también con su sitio. Un error con
  sitio va en su propia línea antes de "Compilation failed at ... stage".
- De los 56 tests de error, 54 dicen ya su sitio. Sin él: `@link` que no existe y los errores dentro de un
  `.dashui` (habría que llevar la línea del JSON: tarea 19). Tests nuevos: `error_position`, `error_in_module`
  (con `tests/lib/modulo_con_error.dash`), `syntax_message`.
- El C generado no cambia (34 ejemplos, idénticos).
- Sin arreglar (anotado en la tarea 1): `y = ` y en la línea siguiente `Print noexiste(3)` se lee como una sola
  expresión: la gramática ignora los saltos de línea dentro de una expresión.
- Base: run_tests todo bien (3 tests más); `npm test` sin cambios.

### 2026-10-20 — Tarea 4 (servidor de lenguaje: base y errores)
- `DashCompiler.analyze(source, filename)`: parse, imports y análisis sin generar C; los errores y avisos quedan en
  el resultado, sin imprimir. `compile()` lo usa (mismo comportamiento: la batería sigue igual).
  `_read_module` mira primero `self.overlay` (el texto de los ficheros abiertos en el editor).
- `compiler/lsp.py`: LSP por stdio sin dependencias (Content-Length + JSON), `select` para esperar; comprueba un
  documento 0,3 s después del último cambio; publica errores y avisos (también los de los módulos importados, en su
  fichero, y los borra cuando se arreglan); un fallo del compilador sale como "error interno", no tira el servidor.
  `sys.stdout` va a stderr (nada que imprima el compilador entra en el protocolo).
- Velocidad: `dashweb.dash` con todos sus módulos tardaba 2,5 s por comprobación (70 % Lark). Ahora el servidor
  guarda el árbol de Lark de cada fichero con su texto (`tree_cache`: solo se vuelve a analizar lo que cambia; el
  transformer no toca el árbol) y el parser de Lark se construye una vez por proceso: ~1,2 s. Un cambio comprueba
  solo su documento; guardar, todos los abiertos.
- Extensión: `lspClient.js` con `vscode-languageclient` 9, empaquetado con esbuild en `dist/extension.js`
  (`npm run build`; el .vsix lleva solo `dist/` y `media/`). Arranca con el primer `.dash`, solo con confianza;
  ajustes `dash.languageServer.enabled` y `dash.python`; orden "Dash: Reiniciar el servidor de lenguaje". Si
  `dash.path` es un Dash sin `compiler/lsp.py` lo dice una vez y no arranca (el `dash.path` del usuario es el
  worktree de dashweb, que aún no lo tiene).
- Tests: `tests/lsp/test_lsp.py` (8, JSON-RPC real; el runner los cuenta uno a uno: `lsp/<test>`); en VS Code, 1
  más (el error sale mientras se escribe en su sitio y se va al arreglarlo). npm test bien; test:vscode 7/7.

### 2026-10-20 — Tarea 5 (autocompletado y ayuda de firmas)
- `compiler/lsp_index.py`: lo que el servidor sabe de un programa (sirve también para la tarea 6). `Index` sobre el
  árbol del último análisis que entró (mientras se escribe el texto no suele entrar): funciones (sin las privadas
  de otros módulos), structs, enums, ventanas, constantes, globales; el bloque que tiene una línea (función,
  método o Main: el último que empieza antes) y las variables vistas allí (parámetros, asignaciones anteriores,
  variables de `for`, `self` en un método) con su tipo cuando se ve sin el analizador (constructor, literal,
  llamada con tipo de vuelta); el tipo de `a.b.c` por los campos; los miembros de un tipo (struct, enum, lista,
  diccionario, String, Window); la firma de lo que se llama.
- Servidor: `completion` (builtins con sus parámetros como snippet y su descripción, palabras de la gramática,
  símbolos, variables primero; tras `x.` los miembros; tras `:`/`->` los tipos; dentro de `import "` los ficheros y
  cajones; nada dentro de un texto salvo en `#{`) y `signatureHelp` (la llamada y el argumento en el que está el
  cursor, contando paréntesis, corchetes y textos; parámetros marcados por posición en la etiqueta).
- Arreglado al probar en VS Code: el retraso de la comprobación contaba desde el último mensaje, y las peticiones de
  completado mientras se escribe llegan más seguido: no se comprobaba nunca. Ahora cuenta desde el último cambio
  de cada documento; y la primera petición de un documento sin analizar lo analiza en el momento.
- Tests: 4 más del servidor (12 en total) y 1 más en VS Code (9). Base: todo bien. Extensión instalada.

### 2026-10-20 — Tarea 6 (navegación)
- `lsp_index`: `resolve(chain, name, line)` dice qué es un nombre (local, función, struct, enum, ventana,
  constante, global, campo, método, valor de enum, método de lista, builtin, tipo); `word_at`, `code_spans` (lo
  que es código en una línea: fuera de textos salvo `#{...}` y de comentarios) y `occurrences` (usos de un nombre,
  con o sin punto delante, sin entrar en los bloques `"""` de C); `files()` (el fichero y sus módulos);
  `body_range` (líneas de la función que tiene una línea, para las locales).
- Servidor: `hover` (bloque de código con firma/tipo y la descripción de los builtins), `definition` (sobre el
  nombre en su línea; en módulos; en un `.dashui` busca `"name": "<ventana u objeto>"`, porque sus líneas son las
  del código generado; desde `import "x"` abre el fichero), `references` (locales solo en su función; campos,
  métodos y valores de enum con punto, más su definición) y `documentHighlight`.
- Tests: 4 más del servidor (16) y 1 más en VS Code (10). Base: todo bien. Extensión instalada.

### 2026-10-20 — Tarea 7 (símbolos y renombrar)
- `documentSymbol`: el esquema jerárquico de un fichero (structs con campos y métodos, enums con valores,
  funciones, `@native`/`@extern`, Main, ventanas, constantes, globales); el final de cada bloque por la sangría
  (su `end`). `workspace/symbol`: los ficheros de los programas abiertos y sus módulos, más los `.dash` de las
  carpetas del workspace (hasta 500; solo se analiza el texto, con la caché de árboles), búsqueda difusa.
- `prepareRename`/`rename`: con las referencias de la tarea 6; rechaza builtins, tipos, métodos de lista, `self`,
  palabras de la gramática como nombre nuevo, y lo que viene de un `.dashui` (se renombra en su editor). El C de
  los bloques `@native` no se toca (dicho en el README). Los rechazos van como errores LSP con su frase
  (`LspError`).
- Tests: 3 más del servidor (19) y 1 más en VS Code (11: esquema y F2). Base: todo bien. Extensión instalada.

### 2026-10-20 — Tarea 8 (formato y arreglos rápidos)
- `compiler/lsp_format.py`: la sangría de cada línea por sus bloques (`end`; `elif`/`else` un paso fuera; bloques
  de una línea `enum E A, B end`; `@extern` + `func` sin cuerpo); el C de `"""` intacto; una línea que sigue un
  paréntesis abierto conserva la suya; los árboles de MUI/ReAction (`mui_*_begin` ... `mui_group_end()`...)
  como bloques solo si ya iban sangrados (es costumbre, no regla). Fuera los espacios al final de las líneas de
  código; los comentarios guardan su final (`# expect-c: /* x: ` lo necesita) y los comentarios alineados bajo el
  comentario final de la línea de arriba se quedan donde están.
- Prueba fuerte: formatear los 231 `.dash` del repositorio y los 31 de dashweb: el C generado es idéntico en todos,
  formatear dos veces da lo mismo, y solo cambian 3 ficheros (sangría rara en `examples/hola.dash`,
  `tests/test_transformer_edge.dash` y `lib/colores.dash` de dashweb).
- Acciones rápidas sobre "Function/Variable 'x' is not defined": crear la función (tantos parámetros como la
  llamada, antes de Main), importarla de un fichero del workspace que la tenga (con la ruta relativa, tras los
  imports) y "Cambiar a '...'" (difflib entre lo visible y los builtins). El servidor recibe ahora las carpetas del
  workspace en `initialize`.
- Tokens semánticos: no. La gramática generada (tarea 2) ya colorea builtins, tipos, constructores y miembros; lo
  que añadirían (locales frente a globales) no compensa un análisis más en cada cambio.
- Tests: 2 más del servidor (21) y 1 más en VS Code (12). Base: todo bien. Extensión instalada.

### 2026-10-20 — Tarea 9 (tareas y errores enlazados)
- `tasks.js`: proveedor de tareas de tipo `dash` (`compile`, `run`, `memcheck`, `profile`; también desde
  `tasks.json`, con `file` o el fichero abierto); `run`/`memcheck`/`profile` compilan con su opción y luego
  `emu_run.py` ejecuta el binario (`--autoclose` = `DASH_TEST_AUTOCLOSE` delante de `./dash`). Problem matcher
  `$dash` (la salida `fichero:línea:col: Error:` de la tarea 4a) y `$gcc`. Las órdenes Compilar/Ejecutar usan ahora
  estas tareas; órdenes nuevas "Ejecutar con comprobación de memoria" y "con perfil"; CodeLens sobre `Main` y botón
  ▶ Dash en la barra de estado.
- Aprendido con la prueba real: VS Code no da tareas en una ventana sin carpeta abierta (`fetchTasks` vacío):
  `test/integration/run.sh` abre una carpeta temporal. Y el comando `type` no llega al editor si la ventana no tiene
  el foco del escritorio (el usuario estaba usando otra): las 6 pruebas que escriben se saltan entonces con
  `SKIP` en vez de fallar (pasaron en las tareas 3-8; su código no ha cambiado).
- Tests: 2 más sin VS Code (la orden de cada tarea; la expresión de `$dash` contra la salida real del compilador) y
  1 más en VS Code (la tarea `compile` del proveedor compila el programa de verdad y está la CodeLens). Base: todo
  bien. Extensión instalada.

### 2026-10-20 — Tarea 10 (emulador: máquinas, ventana, salida en vivo)
- `tools/emu_run.py`: `--machine a1200|a500|a1200-32|rtg` (ROM, sistema y opciones de las máquinas del runner, de sus
  variables), `--emulator amiberry` (A1200/A500; sin `--debug`, capturas ni opciones de FS-UAE), `--window` (la
  ventana y el sonido del emulador, sin límite de tiempo) y `--follow` (la salida mientras corre: lee el
  `out<i>.txt` del disco del host). `SIGTERM`/`SIGHUP` paran el emulador (el `finally` que lo mata se ejecuta):
  parar una tarea de VS Code lo cierra.
- La salida en vivo necesitaba que `Print` no se quedase en el búfer de dos.library: `DASH_PRINT_FLUSH=1` al compilar
  añade `Flush(Output())` tras cada `Print` (sin la variable el C no cambia; la batería sigue igual).
- Probado: un programa con 3 `Print` separados 2 s sale línea a línea en A1200, A500, A1200 3.2 y Amiberry; `SIGTERM`
  a `emu_run` deja el emulador cerrado.
- Extensión: ajustes `dash.emulator.machine`, `dash.emulator.program`, `dash.emulator.window` y ROM/sistema de cada
  máquina (pasan a `emu_run` por las variables); por proyecto en `.vscode/settings.json`; selector en la barra de
  estado; la tarea "ejecutar" compila con `DASH_PRINT_FLUSH` y corre `emu_run --follow --window`; con MUI en el A1200
  3.1, `muiSystem`. Tests: la orden con todas las opciones; en VS Code la tarea `run` de verdad (oculta) acaba con 0.

### 2026-10-20 — Tarea 11 (memoria y perfil en el editor)
- Los errores de `--memcheck` no decían dónde. Ahora, solo en esas compilaciones, `CodeGenerator.visit` pone antes de
  cada sentencia `_DASH_MC_WHERE("fichero.dash:línea")` (macro: guarda el sitio en `_dash_mc_where` si está el
  runtime de memoria, nada si no) y `_dash_mc_error` lo dice: `memcheck: ERROR campo de nil (en x.dash:15)`. La
  batería con `--memcheck` compila entera (275); el C normal no cambia. El runner quita de la salida el prefijo
  absoluto del repositorio, para que un test pueda esperar `tests/x.dash:N`: test `test_memcheck_where`.
- Extensión: problem matcher `$dash-memcheck`. Las tareas que ejecutan corren ahora en un terminal propio
  (`CustomExecution`, `shellTerminal`: `sh -c` en su grupo de procesos; parar o Ctrl+C lo terminan) para leer la
  salida: con `--profile`, su tabla se abre en un panel ordenado por tiempo propio, con barras, y cada función
  enlaza a su código (símbolos del servidor de lenguaje; `Struct.metodo` por su contenedor).
- Tests: el parser del perfil y la expresión de memcheck; en VS Code, la tarea `memcheck` deja el error en su línea y
  la de `profile` abre su panel (14 en total). Base: todo bien. Extensión instalada.

### 2026-10-20 — Tarea 12 (depuración: prueba de viabilidad)
- `./dash -O0` con `DASH_CFLAGS=-g`: el ejecutable (hunk) lleva DWARF en `.dwarf2` (no stabs: la toolchain compila a
  ELF y convierte); `m68k-amigaos-gdb` lo lee: funciones, líneas (del C, por ahora), parámetros y locales.
- `bgdbserver 1.3` (Aminet `dev/debug`, binario y fuentes; `tools/get_bgdbserver.sh` lo baja y comprueba su SHA-256):
  en FS-UAE con `bsdsocket_library = 1`, `bgdbserver DH0:p1` escucha en el puerto 2345 **del PC** (la bsdsocket de
  FS-UAE usa los sockets del PC); `gdb` con `target remote :2345`: breakpoint en `doble`, `continue` para con `n=20`,
  `bt` (doble ← main), `info args`, `next`, `info locals` (`r = 40`), `finish` (devuelve 40). Las direcciones se
  recolocan solas (aviso "unsupported offsets", inofensivo). Igual en **Amiberry** 8.2.2.
- `m68k-amigaos-gdb -i=dap` responde a `initialize` de DAP con breakpoints condicionales, logpoints, evaluar,
  cambiar variables, memoria, desensamblado, paso por instrucción: VS Code puede hablar con él directamente.
- Alternativas descartadas: uae-dap (FS-UAE y WinUAE parcheados; binarios ajenos, solo emulador) y el depurador de
  consola de FS-UAE (`emu_run.py --debug`: sin símbolos ni fuentes, habría que escribir un adaptador entero). La
  elegida vale también para un Amiga real (tarea 17).
- Pendiente para las tareas 13-14: al acabar el programa bgdbserver dice "SIGKILL" (gdb lo da por terminado: vale);
  la salida del programa depurado no se ve (va a la consola de bgdbserver: mirar en la 16); un puerto libre por
  sesión (otras sesiones usan el emulador a la vez).

### 2026-10-20 — Tarea 13 (./dash --debug)
- `./dash --debug`: `-O0 -g` y `DASH_DEBUG_LINES=1` al transpilar. El generador deja una marca
  `/*@dash-line N "ruta absoluta"*/` antes de cada sentencia (el mismo enganche de `visit` que el sitio de memcheck)
  y `/*@dash-noline*/` al final de cada función, método y del código de Main; `compiler/debuglines.py` las cambia por
  `#line` al escribir el C: cada línea de C de una sentencia lleva su línea de Dash (un paso no se queda a medias de
  una sentencia de varias líneas de C) y tras un noline vuelve la numeración real del C (runtime y `@native`).
- En FS-UAE con bgdbserver: `break prueba.dash:8`, `continue` para en `y = doble(x)`, `step` entra en `doble` (línea
  2), `next` (3), `bt` en líneas `.dash`, `finish` devuelve 40, `info locals` x = 20, y = 40.
- Sin `--debug` el C no cambia (batería entera); con `--debug` compilan los 34 ejemplos (MUI incluidos).
- Tests: `tests/unit/test_debug_lines.py` (4: las directivas, nombres con comillas, el C con y sin la variable, gdb lee
  `prog.dash:8` y los símbolos `n` y `r`); el runner ejecuta ahora `tests/lsp` y `tests/unit`.
- Queda para la 15: un `}` de cierre de bloque se atribuye a la última sentencia de dentro (no al `end`).

### 2026-10-20 — Tarea 14 (adaptador de depuración: F5)
- `tools/emu_run.py --gdbserver PUERTO`: el primer programa corre bajo `C:bgdbserver :PUERTO` (copiado al disco;
  `$DASH_BGDBSERVER` o el de `tools/get_bgdbserver.sh`), con la bsdsocket de FS-UAE encendida.
- Probado el diálogo DAP a mano contra `gdb -i=dap`: en gdb 18 la respuesta a `attach` llega **después** de
  `configurationDone` (VS Code no la espera: bien); `attach` con `target: "localhost:P"` y `program`; el breakpoint de
  `prueba.dash:8` sale verificado; gdb deja el programa parado al conectar (`stopped`, reason `attach`).
- `editor/vscode/debug.js`: tipo de depuración `dash` (`launch`: `program`, `stopOnEntry`, `machine`, `emulator`,
  `window`; `attach`: `target`, `program`, para un Amiga real). Al resolver `launch`: compila con `./dash --debug` (salida
  al canal "Dash: Amiga"), busca un puerto libre, arranca `emu_run --follow --gdbserver P` (ventana según los ajustes) y
  espera a que escuche leyendo `/proc/net/tcp` (conectarse se llevaría la única conexión que acepta bgdbserver);
  entonces pasa a `attach` con `target`. El adaptador es el propio gdb (`DebugAdapterExecutable`, `dash.debug.gdb`); un
  tracker continúa tras el `stopped` de `attach` salvo `stopOnEntry`; al acabar la sesión se para el emulador.
  Orden "Dash: Depurar en el Amiga" y "Depurar" en la CodeLens de `Main`; breakpoints en ficheros `.dash`.
- Prueba en VS Code (15): breakpoint en la línea 8, `startDebugging`: para allí, la pila dice línea 8 de `depura.dash`,
  las variables tienen `x = 20`, `continue` y la sesión termina sola. Base: todo bien. Extensión instalada.

### 2026-10-20 — Tarea 15 (pila y variables en Dash)
- `tools/gdb/dash.py` (gdb con `-x`; la extensión lo carga si `dash.path` lo tiene): pretty-printers por nombre de
  tipo del C: `STRPTR` → `"texto"`/nil; `DashArrayLong *` → "lista de N" con sus elementos (Ints, Strings u objetos
  según el byte alto de `capacity`); `DashDict *` → mapa clave → valor; `_Dash_X *` → X con sus campos o nil;
  `DashFixed` en decimal; `BOOL` true/false. Un objeto de una lista se reconoce por su cabecera (`destroy` =
  `_dash_struct_destroy_X`, o el único struct de su tamaño). Un filtro de marcos quita los del runtime salvo el más
  interno y las locales `_dash_*`.
- En gdb (emulador): `mirar (p=Punto = {...}, l=lista de 3 = {...}, ..., f=1.5, b=true, s="hola")`; `info locals` en
  Main: `ps = lista de 2 = {Punto = {x = 1, nombre = "a"}, ...}`, `n = nil`.
- Arreglado por la prueba de VS Code: una sentencia de Dash que da varias líneas de C (`Print` con `Flush`) daba un
  breakpoint con 2 sitios y el programa paraba dos veces. Ahora `debuglines.apply` escribe el C de cada sentencia
  en una sola línea física (los saltos de línea son espacios para C; el preprocesador y los `//` quedan aparte):
  una entrada de la tabla de líneas por sentencia. 34/34 ejemplos compilan con `--debug`.
- Tests: 1 más en `tests/unit` (5); la prueba de F5 en VS Code mira además `s = "hola"`, `l` = "lista de 2" con 1 y 2,
  ninguna `_dash_*`, y que la sesión acaba. Base: todo bien. Extensión instalada.

### 2026-10-20 — Tarea 16a (expresiones de Dash en el depurador)
- `editor/vscode/debugProxy.js`: el adaptador que ve VS Code es ahora uno nuestro en línea
  (`DebugAdapterInlineImplementation`) que lanza `gdb -i=dap` detrás y pasa los mensajes, traduciendo de Dash a C
  `evaluate`/`setExpression` y las condiciones y logpoints de `setBreakpoints`: `p.x` → `p->x`, `l[i]` → `$at(l, i)`,
  `s.length` → `$len(s)`, `and`/`or`/`not`, `true`/`false`/`nil`, `Color.ROJO` → `Color_ROJO`; los textos entre
  comillas no se tocan (se apartan con marcadores y vuelven al final).
- `tools/gdb/dash.py`: funciones de gdb `$len(x)` (lista, diccionario o texto) y `$at(x, i)` (elemento de una lista
  con su tipo, valor de una clave de diccionario, carácter de un texto; avisa si el índice no está).
- Aprendido: en la consola (contexto `repl`) gdb toma el texto como una orden suya: el adaptador lo manda como
  expresión (contexto `watch`) salvo que empiece por `-exec`.
- Tests: 13 traducciones sin VS Code; en VS Code, en el breakpoint: `l[1] + 1` = 3, `s.length` = 4, `x == 20 and y == 40`
  = 1; breakpoint con condición `i == 3 and total > 0` en un bucle (para con i = 3) y logpoint "total vale {total}"
  (sale "total vale 15"). Base: todo bien. Extensión instalada.

### 2026-10-20 — Tarea 16b (salida del programa y errores en el depurador)
- Salida: bajo bgdbserver el programa escribe en la consola de este. Con `--debug` el programa abre al empezar el
  fichero de la variable de DOS `DASH_OUT` si existe (`_dash_debug_output`), y cada `Print` sale en el momento
  (`DASH_PRINT_FLUSH`). `tools/emu_run.py --gdbserver` pone `DASH_OUT` = `DH0:dashout.txt` y `--follow` lo va leyendo;
  la extensión lo manda a la consola de depuración (`output` de categoría `stdout`).
- Errores: con `--debug` el runtime llama a `_dash_debug_stop()` (índice fuera de la lista, errores de memcheck) tras
  dejar el texto en `_dash_debug_what`. El adaptador pone un breakpoint de función ahí, oculto para VS Code. Cuando
  para en él, lo cambia por una parada de tipo `exception` con el texto, y lo escribe en la consola.
  `tools/gdb/dash.py` quita de la pila los marcos del runtime en ese caso: la pila empieza en la línea de Dash.
- Aprendido: gdb leía mal las globales con bgdbserver. El DWARF guarda las direcciones del ELF intermedio
  (`.data` detrás de `.text`, `.bss` detrás de `.data`). gdb las recoloca con los `qOffsets` de bgdbserver, pero un solo
  desplazamiento vale para `.data` y `.bss`, y en el Amiga son dos hunks sueltos (avisa "unsupported offsets").
  `add-symbol-file` con secciones tumba gdb 18. Arreglo:
  - `./dash --debug` enlaza con el guion del propio ld, pero con `.bss` dentro de `.data` (`compiler/cflags.py`,
    `debug_link_flags`). El ejecutable crece lo que ocupa el bss.
  - `tools/gdb_relay.py` se pone entre gdb y bgdbserver y cambia `Data` por `Data - tamaño del código`.
    `emu_run.py --gdbserver` lo pone solo: bgdbserver escucha en un puerto interno por debajo de 32768, porque
    bgdbserver lee el puerto como número de 16 bits con signo. Para un Amiga real, a mano (tarea 17).
- Tests: `tests/unit/test_gdb_relay.py` (5: cuentas de qOffsets, paquete partido, globales del DWARF en su sitio). En
  VS Code: la salida de `Print` en la consola de depuración y "un error para como excepción" (`l[7]`: para en la
  línea 4 con "índice fuera de la lista" y la pila en el `.dash`). Comprobado a mano en el emulador: `cuenta` vale 0 y
  luego 7 tras la función. Base: 285/285, VS Code 17/17. Sin emulador nuevo en el runner.

### 2026-10-20 — Tarea 17 (depurar en un Amiga real)
- `attach` (launch.json, "Amiga real"): `target` = host:puerto de un bgdbserver en marcha y `program` = el `.dash`
  (usa `bin/<nombre>.debug`) o el ejecutable. La extensión arranca `tools/gdb_relay.py` en un puerto libre del PC
  hacia `target`, y gdb conecta ahí: las globales salen bien también en un Amiga real. Con `"relay": false`, directo.
  El relé se para con la sesión.
- Comando **Dash: Preparar para un Amiga real**: compila con `--debug` a `bin/<nombre>.debug` y dice qué copiar y
  qué escribir en el Shell del Amiga (`bgdbserver :2345 <nombre>.debug`).
- `tools/emu_run.py --no-relay`: bgdbserver directo en el puerto, como en un Amiga real (para probar el attach).
- README: sección "Debugging on a real Amiga" (pila TCP/IP, bgdbserver de Aminet, pasos, `DASH_OUT` para la salida).
- Tests: en VS Code, "attach a un bgdbserver" con el emulador haciendo de Amiga: para en el breakpoint y `cuenta`
  vale 7 (global, por el relé). VS Code 18/18. Sin Amiga real: no probado en hardware.

### 2026-10-20 — Tarea 18 (editor visual: teclado, portapapeles, arrastrar, accesibilidad)
- Auditoría: deshacer y rehacer ya eran los del documento (CustomTextEditor), pero sin botones. No se podía
  copiar ni pegar. El árbol no tenía teclado (solo Supr, y también con el foco en un botón) y la paleta solo
  iba con ratón (divs). Al arrastrar no se podía soltar delante de un objeto ni en la vista. No había roles
  ARIA, y el foco se perdía en cada repintado.
- `media/model.js`: `copy`, `paste` (los nombres que ya hay en la ventana llevan un número: boton → boton2),
  `moveBy` (subir y bajar entre hermanos), `dropTarget` (delante, detrás o dentro) y `paths` (orden del árbol).
- `media/editor.js`:
  - Árbol con `role=tree`/`treeitem`, `aria-level`/`selected`/`expanded` y tabindex móvil. Teclado: flechas,
    Inicio/Fin, izquierda (su grupo), derecha (dentro), Alt+flechas (mover), Supr, F2 (nombre), Intro
    (propiedades) y Ctrl+D (duplicar). El foco sigue en el árbol tras cada cambio, y tras un clic en la vista.
  - Copiar, cortar y pegar con los sucesos del portapapeles (son los que VS Code manda al webview con sus órdenes).
    En un campo de propiedades, el portapapeles es del campo.
  - Paleta de botones (clic o Intro añade).
  - Arrastrar desde la paleta, el árbol o la vista, delante, detrás o dentro según dónde se suelte, con una marca.
  - Botones ↶ ↷ (el anfitrión ejecuta `undo`/`redo`), problemas con `aria-live` y etiquetas en los campos de
    los menús.
- Tests:
  - `test/webview.js`: el webview en un Chromium sin ventana, por el protocolo de DevTools (teclas de verdad,
    sucesos del portapapeles, arrastrar). 6 tests; se salta sin Chromium.
  - Modelo: 2 más.
  - En VS Code: deshacer y rehacer con el editor visual abierto. VS Code 19/19.

### 2026-10-20 — Tarea 19 (código y ventana)
- `editor/vscode/dashuiLinks.js` (sin VS Code, se prueba en node):
  - `problems`: JSON no válido (en su sitio), tipos desconocidos, nombres no válidos o repetidos, ventanas
    repetidas y números de evento que no son enteros mayores que 0. Avisa si un número va en varios objetos
    de una ventana y alguno no tiene nombre. Cada problema lleva su línea: el objeto se busca en el texto en el
    orden del recorrido.
  - `handlers`: dónde trata un `.dash` el evento n. Son sus constantes con ese valor y las comparaciones con
    ellas o con el número, sin contar textos ni comentarios.
  - `addHandler`: añade `const ID_<NOMBRE> = n` tras las constantes e imports, y
    `if ev == ID_<NOMBRE>` justo después de `ev = mui_wait_event()` (con la variable y la sangría del programa).
- `dashuiCode.js`: diagnósticos de los `.dashui` en Problemas, al abrir y al cambiar (también editando en el
  editor visual). La orden `dash.gotoEvent(uri, n, nombre, crear)` busca los `.dash` que importan el fichero
  (en la carpeta del espacio de trabajo, si no en la suya) y va al primer sitio que trata el evento. Si no hay
  ninguno, pregunta y lo crea.
- Editor visual: botón → junto a cada número de evento (también en las opciones de menú); sin número, apagado.
- Tests:
  - 2 en node: problemas en su línea; buscar y crear el código.
  - 1 en el Chromium: el botón pide la orden con el número y el nombre.
  - En VS Code: los diagnósticos llegan; `gotoEvent` crea la constante y el `if`, deja el cursor en el comentario
    nuevo y la segunda vez lo encuentra. VS Code 20/20.

### 2026-10-20 — Tarea 20 (Ver en Amiga: más rápida, repetible, en varias máquinas)
- Antes: cada vista arrancaba un emulador nuevo y capturaba a los 12 s (unos 30 s en total).
- `tools/emu_preview.py`: un Amiga emulado que se queda encendido. Órdenes por stdin (`show <programa> <png>`,
  `quit`) y respuestas por stdout (`ready`, `ok`, `error`).
  - Dentro, un vigía en Dash (compilado una vez, en caché) espera `DH0:pide` y ejecuta `DH0:vista`.
  - La vista abre la ventana, se captura sola (`C:dash_shot 1 DH0:shot.dsh`) y acaba.
  - `emu_run.run_programs(on_disk=...)` da el directorio del disco emulado para hablar así con los programas.
  - Los manejadores de señales solo se ponen en el hilo principal.
- `tools/amiga/shot.c`:
  - Copia cada fila de cada plano a memoria Fast (CopyMem) en vez de leer la Chip píxel a píxel.
  - Con un nombre `.dsh` guarda los planos tal cual más la paleta (40 KB en vez de 480 de PPM: el disco emulado
    escribe despacio), y `emu_run.planar_to_png` hace el PNG.
  - El binario en caché va por hash del fuente (`shot_<hash>`): otras copias del repositorio tienen otra versión.
- Extensión:
  - `PreviewServer` (uno por máquina, se apaga a los 10 minutos sin uso) y `preview()`, que compila con caché
    por el texto del `.dashui` y la ventana.
  - La máquina es la de `dash.emulator.machine` (A500 → A1200, sin 68020 para MUI). Ajuste nuevo
    `dash.emulator.muiSystem32`.
- Medido, por vista: A1200 3.1 2,4 s, A1200 3.2 2,5 s, 68040 RTG 1,8 s. El arranque, 2,5, 5 y 1,7 s.
- Tests:
  - En node: el protocolo con un servidor falso (orden, errores, servidor caído, sin ROM).
  - Real con `DASH_PREVIEW_EMU=1`: dos vistas de la misma ventana, la segunda sin compilar y en menos de 8 s.
  - `tests/unit/test_emu_preview.py`: planos a PNG.
  - Siguen pasando las capturas del runner (`test_emu_shots`, `test_mui_canvas_buffered`, en A1200 y 3.2).
  - VS Code: 13 bien y 7 saltados, porque la ventana no tenía el foco del escritorio (los de escribir y deshacer).

### 2026-10-20 — Tarea 21 (primeros pasos)
- **Dash: Nuevo proyecto** (`newProject.js`): pide nombre y carpeta y crea:
  - `<nombre>.dash`: abre la ventana; Contar cambia el texto; Salir y el menú acaban;
  - `ventana.dashui`;
  - `.vscode/launch.json`: F5 en el emulador, y "Amiga real";
  - `.gitignore`;
  - `.vscode/settings.json` con `dash.path` si lo encontró por la carpeta y no hay ajuste.
  Luego abre la carpeta: en otra ventana si ya hay una abierta; si no, en esta, con el programa abierto al recargar.
- **Dash: Elegir la carpeta del compilador** (`dash.path`, comprobando que tenga `./dash` y `compiler/`).
- Walkthrough "Primeros pasos con Dash" en 4 pasos, cada uno con su texto en `walkthrough/*.md` y se marca solo
  al hacerlo: el compilador, el proyecto nuevo, la ventana (editor visual, Ver en Amiga, del evento al código),
  y ejecutar y depurar.
- README: capturas (`images/editor.png`, `images/amiga.png`) y "Getting started". `test/screenshots.js` rehace
  la del editor (el webview en Chromium con la ventana del proyecto nuevo). La del Amiga es el programa del
  proyecto nuevo en el A1200 con MUI (`emu_run --screenshot`).
- Tests:
  - En node: ficheros del proyecto; su ventana sin problemas; su programa compila.
  - Comprobado a mano en el emulador: la ventana sale y el programa acaba bien.
  - En VS Code: la orden crea la carpeta, y las páginas de la guía y `dash.choosePath` están. VS Code 14 bien y
    7 saltados por falta de foco.
- Visto de paso (no arreglado, es del runtime de MUI): `GetVPModeID` y `GetBitMapAttr` sin prototipo en los
  programas MUI (aviso de gcc, también en `examples/mui_hola.dash`).

### 2026-10-20 — Tarea 22 (empaquetado)
- Versión 0.2.0, `displayName` "Dash for Amiga", descripción de todo lo que hace.
- Categorías: lenguajes, depuradores, fragmentos, formateadores, linters.
- Palabras clave, `homepage`, `bugs` y banner.
- `CHANGELOG.md` con 0.1.0 y 0.2.0.
- Icono: `images/icon.svg` (bola de Boing con una D), que `test/screenshots.js` pasa a PNG de 128 en el Chromium
  sin ventana, con fondo transparente.
- `npm run package` minimiza el bundle (401 KB en vez de 829); el paquete tiene 23 ficheros y 188 KB, sin tests.
- Títulos de las órdenes sin "Dash:" delante (la categoría ya lo pone; salían "Dash: Dash: Compilar").
- Publicar: los pasos están en el README (Marketplace con `vsce` y Open VSX con `ovsx`); no se ha publicado,
  queda en `[?]` 22b.
- Tests: node todo bien. VS Code con el bundle minimizado: 14 bien y 7 saltados por falta de foco.
  Instalado el 0.2.0.

