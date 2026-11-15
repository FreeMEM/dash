# Bucle del universo Dash (desde 2026-11-06)

Todo el universo Dash se lleva en la sesión freememlang (salvo DashOS y Dash para AArch64, que lleva la sesión
DashOS). Este fichero (worktree .worktrees/universo, rama universo) es el plan y la bitácora del /loop. Cada vuelta:
tomar la primera tarea sin hacer, hacerla, probarla, anotarla aquí y hacer commit en su repo. Nada hacia fuera
(push a main, releases, Telegram, webs) sin permiso del usuario.

## Plan

### T1. Trasfondo 2.8 (~/Projects/trasfondo, commits sin rastro de Claude)
- [x] Ver los segundos (SEGUNDOS) en el fondo y la barra. Commit 5baa7aa.
- [x] Barra, dock y ventanas en Exchange. Probado en el emulador con cx_send: ocultar, mostrar y quitar, las dos piezas.
- [x] Elegir qué enseña la barra (BARRA_VER_*). Visto en el emulador: sin fecha ni CPU, con segundos.
- [x] Editor del dock en TrasfondoPrefs (f82e72a). Probado en el emulador: elegir, Subir, Aceptar y Usar, y el dock
  sale con el orden nuevo. De paso, Usar ya no para piezas arrancadas después de abrir las Prefs.
- [x] La ciudad admite el país tras una coma ("Valencia, ES"); comprobado lo que da el buscador, no en el Amiga.
- [x] Probado en el emulador (vista.py) y en el CoffinOS emulado (--machine coffin de la rama coffin-emu): barra en la
  de título con segundos y sin fecha, fondo con segundos, dock. README al día; paquete 2.8 hecho, sin publicar.
- [x] Fuga de memoria (Oskisrp): era el fondo (la barra y el dock, estables; sin Trasfondo, estable). Causa, en
  Dash: las funciones no marcadas reads_only reciben copias permanentes de sus textos calculados; tooltype no lo
  estaba y el fondo la llama dos veces por medida (caja_dock -> conf -> tooltype). Marcadas reads_only tooltype,
  date_text, file_copy, screen_font_text_width y notify (f550628, rama saltos). Medido: el fondo con el arreglo no
  pierde nada en 15 min (antes, 42 KB). Paquete 2.8 rehecho con el Dash de la rama saltos. Queda revisar las otras
  ~500 funciones sin la marca (las que solo leen sus textos).
- [x] Dock con imágenes PNG como el de CoffinOS: ruta|imagen en la lista, la de WBDock o la de Barjack por nombre
  si no; image_from_decoded_size en Dash (71732af, rama saltos); botón Imagen... en el editor. Visto en el
  CoffinOS emulado: el Shell sale con su imagen de WBDock.

### T2. dashgit T4-T9 (agente en segundo plano, rama arreglos-t4)
- [~] Revisados por encima el token (solo https y al host de DASHGIT_HOST; no sigue redirecciones) y los nombres
  que el disco no admite: bien. Informe recibido: T4-T8 hechas, T9 a medias (nombres de más de 30 letras en FFS sin probar); las 8 pruebas en
  "TODO BIEN"; commits 4b033d9..067d763 en arreglos-t4. Falta: revisarla yo y, con permiso, fusionar y subir.

### T3. Tachyon 57, guardar página y enlace (agente en segundo plano, rama dev)
- [~] Hecha (159d485 en dev, sin push): "Save link as..." y "Save page as..." (menú del botón derecho, Proyecto,
  Amiga-S); test_guardar, test_descargas, documento y test_http_volcar pasan; probada con MUI 3.8 y 5. Arregló de
  paso los atajos con MUI 3.8 y el menú contextual (atajos copiados en atajo_de_menu: mantener a mano). Pendiente:
  Amiga izquierda + letra también hace el atajo (no es lo normal); revisar y subir con permiso.

### T4b. Fallos de Dash que encontró el agente de Forja
- Rama saltos (todos los arreglos de Dash de la noche: saltos, depuración, reads_only, image_from_decoded_size):
  batería con --emu --emu-a500 --emu-32, 1368/1368. Sin subir ni fusionar.
- [x] grow_branches: arreglado en la rama saltos (25db818): tras insert_code, el desplazamiento vuelve a su sitio.
  tests/test_salto_crece.dash (bucle de más de 32 KB, sus saltos pasan a jmp; no consigue que crezca uno corto).
- [x] Entradas de depuración de funciones tiradas: mark/undo guardan también dbg_lines/funcs/vars (4b209c6, rama
  saltos), tests/unit/test_debug_sin_usar.py; comprobado con --debug-info. make -C dashc test: "todo bien" (el
  arreglo de la depuración entró a media tanda). Rama saltos sin subir ni fusionar.
- [ ] mui_canvas guarda solo la última tecla: una cola de teclas (mejora; hace falta decidir cuándo se da por
  leída una tecla). A 12 teclas por segundo no se pierde ninguna.
- [x] D83 de Tachyon: mui_on_drop (PR #126, e3da1d0): iconos soltados sobre ventanas MUI; probado arrastrando de
  verdad en 3.2 con MUI 5 (test_mui_drop_wb, # workbench) y a mano con MUI 3.8. Avisada tachyon-97.
- [ ] `return` en Main: ./dash lo admite y ./dash --gcc da "'return' outside of function". Igualar (en --gcc,
  saltar a la limpieza del final de main).
- [ ] ./dash --gcc y == con un elemento de una lista global [String]: el caso sencillo no da aviso; sin reproducir.

### T4. Forja: IntelliSense completo (agente en segundo plano, rama autocompletar)
- Autocompletado de palabras clave, builtins y símbolos del proyecto (también de los módulos importados), ir a la
  definición y volver, ayuda de argumentos, buscar referencias; tests/ficheros.sh y tests/depurar.sh.
- [~] Hecho (rama autocompletar: 4b323c8, f3e7952, 8a1a109 Forja 0.4): autocompletado completo, ayuda de
  argumentos, ir a la definición (Amiga-J, Ctrl+clic) y volver (Amiga-U), dónde se usa (Amiga-H), menú Código;
  lo de David arreglado (la ventana del programa se quedaba el teclado), con tests/depurar_ventana.sh; ficheros.sh
  arreglado. Fallan como en main mapas_forja, sprites_fotogramas, sprites_forja; depurar.sh por Dash (T4b); git.sh
  sin pasar (red). Falta: revisarla yo y, con permiso, fusionar y subir.
- [x] sprites_forja (Amiga-K en un sprite no compilaba): Forja busca DASH:dash antes de avisar y, sin la asignación
  DASH:, el Amiga pedía insertar ese volumen y Forja se quedaba esperando detrás. Arreglado (e0d27e1, rama
  autocompletar): programa_de_dash sin peticiones del sistema. Sin comprobar en la prueba: en 3 de 4 pasadas los
  clics no llegan a Forja desde el principio (abrir red.dash falla), con el mismo código que en otra pasó.
  Comprobado después: falla igual con Forja de main, con el Dash de main y con el de saltos, y también
  mapas_forja (18 fallos) y sprites_fotogramas (2): es el entorno de las pruebas con clics, no la rama. Sin
  averiguar la causa (input_click mueve el puntero de uno en uno hasta MouseX; la ventana de Forja sale en x=123).
- Fugas como la de Trasfondo: en el C de trasfondo, barra, dock y panel solo quedan copias permanentes para
  run_program (una por lanzamiento) y cx_broker_new/cx_hotkey (deben guardarse). Nada más que arreglar ahí.

### T6. Lo que han contado en Dash Amiga (6/11)
- [ ] David: depurando examples/fixed_gravedad.dash en Forja se queda en la línea 42 (lista de structs con Fixed);
  F5 y F10 dejan de responder, los botones sí. Pasado al agente de Forja (T4).
- [ ] Santi: ¿hay actualización para la extensión de VS Code o se hace a mano? Mirar editor/vscode/updates.js y
  contestar (el usuario manda el mensaje).
- [ ] Ferrán (23:33): a Oskisrp (PiStorm, Emu68) se le iban los problemas de memoria quitando Trasfondo; sin más
  detalle. Buscar fugas: dejar el fondo, la barra y el dock horas en el emulador midiendo la memoria libre (y con
  --memcheck), sobre todo con los paneles, el tiempo (red) y la actualización.

- [ ] Ferrán (privado, 23:35): la raya gris de la barra ya no le sale con la 2.7, pero cree que fue por actualizar
  una rtg.library muy antigua. Investigar si con una rtg.library vieja la barra (o ChangeWindowBox, o el pintado)
  deja esa raya, y si Trasfondo debe pedir una versión mínima o evitarlo. Vídeo suyo en tmp/tg (13:12, con la 2.7).

- [ ] Ferrán (#378): en el panel del fondo, dos puntitos antes del nombre de cada volumen: verde al leer, rojo al
  escribir. Mirado: AmigaOS no cuenta accesos por volumen; habría que parchear BeginIO del driver de cada disco
  (scsi.device, trackdisk...) contando CMD_READ/CMD_WRITE por unidad y unirlo a los volúmenes por la DosList, como
  hacen las utilidades de leds. Delicado (quitar el parche al salir). Que lo decida el usuario.
- [ ] Tolkien (#398): no tener que usar la asignación DASH:, tirar de PROGDIR:. Mirado: el compilador ya busca sus
  .drt y lib/ en PROGDIR: (dashc/src/main.c); DASH: solo lo usan el instalador (Assign y Path DASH:) y Forja
  (ENV:Forja/dashc, luego DASH:dash, luego "dash" del Path; y los import en DASH:). Hecho en Forja (d6e62d2, rama
  autocompletar): dash y dashgit también en PROGDIR:/ (con la ruta entera), y los import salen del cajón de ese
  dash. Falta el instalador (paquete/Instalar): preguntar si poner el Assign y, si no, el Path y ENV:Forja/dashc con
  la ruta del cajón. Sin hacer: hay que probar el Installer en el emulador; que lo decida el usuario.
- [x] Tolkien (#406-413), modo traza de Emu68: el paso a paso de Dash pone un TRAP por línea, no usa traza. Lo de
  David era la ventana del programa quedándose el teclado (arreglado en Forja).

### T5. Lo que quede
- [x] Repaso de examples/ con Dash main (2.4.0), ocho a la vez sin cerrojo (dash-repaso-ejemplos/ejecuta-par.sh):
  33 de 34 con RC 0; test_intuition da TIMEOUT porque espera que se pulse su aviso (normal sin nadie delante).
  flowpaint, que en la 2.2.0 se colgaba, ya va. Capturas revisadas (shots24/): todas como se espera.
- [ ] Tachyon: lo siguiente de docs/DASHWEB_LOOP.md (41d WPT JS, 41c detalles de Acid3, 58c paquete por --gcc).
- [ ] Detalles menores: ciudades con el mismo nombre en el tiempo de Trasfondo; Amiga+C en la salida de Forja.

## Ronda 2 (desde 2026-11-07, el usuario: "dale caña")

- [x] R1. `return` en Main por `./dash --gcc` (hoy "'return' outside of function"; `./dash` lo admite): igualar.
- [x] R2. tests/test_mui_drop_wb.dash: arrastrar el primer icono que no tape la ventana (como hizo Tachyon).
- [x] R3. (no hacía falta: MUI da un evento por tecla; test_mui_canvas_keys_queue lo comprueba) mui_canvas: una cola de teclas en lugar de solo la última (lo vio el agente de Forja).
- [x] R4. (PR #128, release v2.6.0, webs) Dash 2.6.0 (autorizada): builtins de DashOS (PR #124), mui_on_drop (PR #126) y R1-R3. Notas, paquete
  del Amiga, release, web.
- [~] R5. (borrador enseñado al usuario) Telegram: borrador del aviso (Dash 2.5.0/2.6.0, Forja 0.4, Trasfondo 2.8) para el grupo Dash Amiga;
  enseñarlo al usuario antes de enviar.
- [ ] R6. Instalador sin DASH: (Tolkien): probar el Installer en el emulador; si no se pone el Assign, el Path y
  ENV:Forja/dashc con la ruta del cajón.
- [-] R7. Pruebas de Forja con clics: fuera, otra sesión trabaja con Forja (2026-11-07).
- [x] R8. La raya gris con una rtg.library vieja: sin rtg.library vieja para reproducirlo; a Ferrán se le fue con la 2.7 (la barra ya solo crece). Cerrado salvo que vuelva.
- [x] R10. (2.8.1) Trasfondo (Ferrán #660): en Prefs, "Buscar versiones nuevas en GitHub" pisaba "Ver los segundos".
- [x] R11. (2.8.1, release y web) Trasfondo (Ferrán #661): la temperatura de la Pi en la línea del título del fondo, entre el nombre y la
  CPU (solo si hay lectura). Las dos, en una 2.8.1.
- [x] R9. dashgit en FFS sin nombres largos: git necesita 50 letras (.git/objects), así que ahora lo dice claro (init, clone, las demás); tests/ffs.sh con un disquete FFS, raros y fase3 bien. Subido a main de dashgit.

- [ ] R12. (decide el usuario) JaviTecH (#685): instalar Dash y sus programas desde el Amiga por Internet. Se
  podría con el actualizador de Trasfondo (https, AmiSSL) hecho programa aparte, o dentro de una tienda de programas.

- [x] R13. (PR #133) Dash: un carácter (`t[i]`) pasado donde va un String (`str_find(s, t[i])`) va como puntero: basura
  (-1 o un número raro, sin aviso). Por los dos caminos. Convertirlo a un texto de una letra o dar error de tipos.
  Lo vi al hacer un programa con MUI.
- [ ] R14. Dash: comillas dentro de `#{...}` en un texto (`"#{str_find("abc", x)}"`): `./dash --gcc` da error de
  sintaxis y `./dash` lo compila y da resultados raros. Igualar (error claro, o admitirlo bien en los dos).

Fuera de la ronda (decide el usuario): puntos de lectura/escritura por volumen; aspecto del dock (falta captura).

## Bitácora

- 2026-11-07: publicado con permiso del usuario: Dash 2.5.0 (PR #123, release con el lha), Forja 0.4 (main y
  release v0.4), dashgit 0.2 alfa (main), Trasfondo 2.8 (release); webs dash, forja, inferencia y trasfondo
  desplegadas. Sin aviso en los grupos. El 95 % que paró el bucle era de otra cuenta (uso-7d.txt): esta mira
  ~/.claude-ftapias/state/uso-7d-ftapias.txt.

- 2026-11-07 04:00: bucle parado al 95 % del uso semanal (tope del encargo: 90 %).

- 2026-11-06: traspasos de tachyon-0b, forja-87 y aarch64 (en la memoria del proyecto). DashOS/AArch64 pasado a la
  sesión DashOS. Dash 2.4.0: batería 1362/1363 (el que falló, test_mui_field_colors, pasa al repetirlo). Tachyon dev
  subida (3 commits). Agentes lanzados para T2, T3 y T4.
