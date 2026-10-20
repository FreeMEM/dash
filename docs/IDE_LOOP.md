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
- **Depuración:** se decide en la tarea 12.

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
- [ ] 4. **Base y errores.** `compiler/lsp.py`: JSON-RPC por stdio sin dependencias, que reutiliza parser y
      analizador; cliente en la extensión (lo arranca con `python3 -m compiler.lsp` desde `dash.path`).
      Diagnósticos al escribir, con línea y columna (y los de los imports). Tests.
- [ ] 5. **Autocompletado.** Builtins con firma y descripción, palabras clave, variables/funciones/structs/
      campos/enums en ámbito, rutas de `import`; ayuda de firma (signature help).
- [ ] 6. **Navegación.** Hover (tipo, firma, doc), ir a la definición (también entre módulos y hacia el `.dashui`),
      referencias, resaltar las apariciones.
- [ ] 7. **Símbolos.** Esquema del documento (Outline, breadcrumbs), símbolos del workspace, renombrar.
- [ ] 8. **Formato y arreglos.** Formateador de sangría; acciones rápidas sencillas (crear la función que falta,
      añadir el `import`); tokens semánticos si mejoran los colores.

### C. Compilar y ejecutar
- [ ] 9. **Tareas y errores.** TaskProvider (compilar, ejecutar, `--memcheck`, `--profile`), problem matcher del
      compilador de Dash y de gcc, barra de estado, CodeLens "Ejecutar" sobre `Main`.
- [ ] 10. **Emulador.** Elegir máquina (A500, A1200 3.1, 3.2, RTG, Amiberry), salida del programa en un panel,
      parar, configuración por proyecto.
- [ ] 11. **Memoria y perfil.** Avisos de `--memcheck` como diagnósticos; la tabla de `--profile` en un webview,
      con enlaces a las funciones.

### D. Depuración
- [ ] 12. **Prueba de viabilidad.** `tools/get_bgdbserver.sh`; un programa Dash con `-g` en FS-UAE (y Amiberry) con
      bsdsocket; `m68k-amigaos-gdb` → `target remote`; parar en una función, ver registros y variables. Comparar
      con las alternativas (uae-dap, el depurador de consola de FS-UAE) y elegir. Si hace falta, `[?]`.
- [ ] 13. **Dash con información de depuración.** `./dash --debug` (`-g -O0`, `#line` hacia el `.dash` en el C):
      gdb y addr2line hablan en líneas de Dash. Tests (C esperado; addr2line sobre el binario).
- [ ] 14. **Adaptador.** Configuración de lanzamiento `dash` (launch.json): compila con `--debug`, arranca emulador y
      servidor, conecta gdb (DAP o MI). Breakpoints en `.dash`, continuar, paso a paso (entrar, saltar, salir), pausa.
- [ ] 15. **Pila y variables.** Nombres de Dash (locales, globales, structs, Strings, listas, diccionarios) con
      pretty-printers de gdb en Python; ocultar el runtime `_dash_*` de la pila.
- [ ] 16. **Más.** Consola de depuración (evaluar), watch, breakpoints condicionales y logpoints, `Print` en la
      consola de depuración, parar en errores del runtime (índice fuera de rango, memcheck).
- [ ] 17. **Amiga real.** Depurar en un Amiga con bgdbserver por red (host y puerto configurables); documentarlo.

### E. `.dashui`
- [ ] 18. **Editor visual.** Deshacer/rehacer, arrastrar, copiar y pegar, teclado, accesibilidad; auditoría primero.
- [ ] 19. **Código y ventana.** Validación con diagnósticos; de un evento del `.dashui` a su código en el `.dash` y
      crear el que falte.
- [ ] 20. **Vista en el Amiga.** Más rápida, repetible, en varias máquinas.

### F. Pulido
- [ ] 21. **Primeros pasos.** Walkthrough de VS Code, comando "Dash: Nuevo proyecto" (plantilla con `.dash`,
      `.dashui` y launch.json), README con capturas.
- [ ] 22. **Empaquetado.** Bundle, icono, versión 0.2.0, CHANGELOG; preparar la publicación (publicar: `[?]`).
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

