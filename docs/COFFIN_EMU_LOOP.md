# Amiga de pruebas como CoffinOS (desde 2026-11-06)

Encargo del usuario: un Amiga emulado como su CoffinOS (ROM 3.2.3, 68040 con JIT a toda velocidad, RTG de 32 bits,
mucha Fast), con un fondo chulo, todo el universo Dash, DOpus5 y los programas instalados en Coffin (sin juegos ni
demos). Configurado y probado en FS-UAE y en Amiberry. Worktree `.worktrees/coffin-emu`, rama `coffin-emu`.

## Lo que hay

- Coffin R65: `~/Amiberry/HardDrives/coffin_r65_32GB.img`, RDB con pfs3aio 19.2 y cuatro particiones PFS3:
  DH0 (300 MB, arranque), DH3 (300 MB), DH2 (5 GB), DH1 (22 GB, cilindros 2879-14335, al final).
- Configuración de Coffin: `~/Amiberry/Configurations/coffin.uae` (68040 JIT, `cpu_speed=max`, 8 MB de Chip,
  256 MB Z3, uaegfx Z3 de 32 MB, 32 bits) y `~/Documentos/FS-UAE/Configurations/coffin.fs-uae` (68040-NOMMU,
  JIT, 512 MB Z3, `uaegfx-z3`, bsdsocket).

## Plan

- [x] P1. Ver qué hay en cada partición de Coffin (arrancar un sistema auxiliar con una copia de la imagen).
- [x] P2. Disco nuevo: copia (reflink) de Coffin sin la partición de juegos; quitar juegos y demos que queden y lo
  que los busque al arrancar.
- [x] P3. Universo Dash: paquete de Dash (orden dash, Forja, Inferencia, dashgit), Trasfondo, Tachyon.
- [x] P4. DOpus5 y fondo.
- [x] P5. Configuraciones de FS-UAE y Amiberry; arrancar en los dos con captura.
- [x] P6. `tools/emu_run.py --machine coffin` y el runner: arranque desde una copia del disco, programas desde un
  volumen del PC.
- [x] P7. Documentar (INSTALACION, AGENTS) y PR.

## Bitácora

- 2026-11-06: P1. Las particiones de Coffin son System (DH0), Restore (DH3), MyFiles (DH2) y Programs (DH1, 20 GB:
  13 GB de Games, 2,3 de ScummVM, 1,6 de Demos). DOpus5 y Dash ya estaban instalados (Programs:Productivity/DOpus5,
  Programs:Programming/Dash, user-startup).
- P2. `~/Amiberry/HardDrives/DashCoffin.hdf` (8,5 GB): RDB de rdbtool con el pfs3aio 19.2 de Coffin; DH0 System
  1 GB, DH1 Programs 6 GB, DH2 MyFiles 1,5 GB. Formateado con `C:pfsformat` (el Format de 3.2 sale con 20) y copiado
  con Copy ALL CLONE desde un arranque auxiliar. Sin Games, Demos, ScummVM, Restore, ni Videos y Music de MyFiles.
  Comprobado fichero a fichero contra los listados de Coffin. Ojo: PFS3 guarda en caché lo escrito; si se apaga el
  emulador justo al acabar, se pierde lo último (pasó: la cola de la copia y la primera instalación). Esperar
  unos segundos (Wait 12) antes de apagar.
- P3/P4. Dash 2.4.0 (paquete de build/paquete_amiga, con Forja, Inferencia y dashgit), Trasfondo 2.7 (del lha de
  la release), Tachyon 0.9.0-alfa (Programs:Network/Tachyon). Fondo nuevo (tools/coffin/fondo.py, 1280x1024) en
  System:Prefs/Presets/Themes/dash/dash.jpg y ENVARC:Sys/wbpattern.prefs.
- P5. FS-UAE: con la configuración de Coffin el Workbench salía en AGA (también el Coffin original): faltaba
  `uae_rtg_modes = 0x112`, como en Amiberry. Amiberry: sin ventana (driver offscreen de SDL) no hay tarjeta; con
  `xvfb-run` sí. Las dos máquinas arrancan en 1280x1024 de 32 bits.
- P6. Gancho en S:Startup-Sequence (tras LoadWB): si existe DASHRUN:, ejecuta DASHRUN:Run-Sequence. `emu_run.py
  --machine coffin` (FS-UAE y Amiberry) arranca una copia reflink del disco y deja los programas en DASHRUN: (DH9).
  hola.dash: 30 s con una captura a los 25 en FS-UAE, 20 s en Amiberry.
- P3, comprobado en el emulador con capturas: `dash` 2.4.0 compila y ejecuta hola.dash dentro del Amiga; DOpus5,
  Forja 0.3 y Tachyon 0.9.0-alfa abren. `tools/coffin/disco.py actualizar` (16 s) toma lo último: el lha más nuevo
  de Trasfondo era ya el 2.8 sin publicar de la sesión universo.
- P6. Runner: `--emu-coffin` (toda la batería en un arranque; los `# emu-shot` se saltan porque sus píxeles son los
  de las otras pantallas). Primera tanda: fallo del runner (pedía LoadWB en la carpeta de sistema), arreglado.
- 2ª tanda (2026-11-07): 588/863 en total; casi todos los fallos eran por tiempo detrás de un cuelgue. Ahora el
  runner, si un programa pasa 120 s sin acabar, arranca otra vez desde el siguiente (`stall` en run_programs).
- Hallazgo: `test_desktop_canvas` (y los demás `desktop_canvas*`) se cuelga en Coffin con Trasfondo en marcha: no
  llega a escribir nada y tampoco se hace la captura (dash_shot), así que algo deja las capas bloqueadas. Trasfondo
  usa el mismo desktop_canvas. En las otras máquinas pasa. Pendiente de mirar aparte (¿dos lienzos a la vez?).
- Fallos del entorno, no de Dash: idioma español (test_catalog*, test_clock: esperan inglés), Trasfondo ya es dueño
  del semáforo dash.cpu (test_cpu_shared), pantalla RTG por defecto (test_copper, test_bobs, test_blend).
- Confirmado: con Trasfondo parado (se para lanzándolo otra vez) test_desktop_canvas pasa entero en Coffin; con
  Trasfondo en marcha se cuelga. Fallo de Dash: dos desktop_canvas a la vez bloquean la pantalla. En el runner,
  COFFIN_SKIP deja fuera en esta máquina los tests que esperan el sistema pelado (idioma, dash.cpu, AGA, lienzo).
- 3ª tanda: 800/843 en total; en Coffin 245 bien, 43 mal, 26 saltados. Clasificados: entorno (RTG frente a AGA,
  MUI 3.8, clics colocados para 640 px, gestor de ventanas y puerto ARexx de Trasfondo, Poseidon, idioma, 68040, JIT
  demasiado rápido para test_task, pila de red) en COFFIN_SKIP con su motivo. La CA de los servidores TLS del runner
  va ahora en AmiSSL:Certs (disco.py actualizar). test_rtg_pub_screen esperaba la misma profundidad de
  CyberGraphX y de BMA_DEPTH: en 32 bits son 32 y 24; arreglado el test. Quedan por mirar: test_run_program_wb(path)
  (desde_workbench falso al relanzar), test_window_handles, test_window_find.
- 4ª tanda: 807/811; en Coffin solo fallan los cuatro por mirar (test_run_program_wb y wbpath, test_window_find,
  test_window_handles: window_create de tamaño 0 devuelve 0 en Coffin). TLS pasa con la CA. Las máquinas de
  siempre (a1200, a1200-32, Amiberry a1200) siguen dando bien con emu_run. PR #122.

- 2026-11-07, urgente: el cuelgue de dos desktop_canvas. Cada programa pone su gancho de repintado en la ventana
  de fondo y, si en la siguiente actualización no era el de arriba, lo volvía a poner: con dos programas, el
  "anterior" de cada uno acababa siendo el del otro, y un repintado los llamaba sin fin. Ahora los ganchos de lienzo
  se marcan (h_SubEntry impar y h_Data con dónde guarda su programa el anterior) y forman una cadena: un programa
  que ya está en ella no se vuelve a poner encima, y al acabar se quita de donde esté (si hay otro encima, en el
  "anterior" de ese). test_desktop_canvas_dos (y _rtg): el test se lanza a sí mismo como el otro programa; con el
  runtime de antes se cuelga. Hace falta que los dos programas estén compilados con este Dash: un Trasfondo viejo
  se sigue poniendo encima.
- Segundo fallo, visto en Coffin con test_desktop_canvas_modes: al quitar el backdrop, el Workbench de Coffin no
  cierra su ventana de fondo, y el lienzo daba por hecho que se iba con su gancho: el gancho se quedaba en ella
  después de acabar el programa. Ahora se quita de la ventana si sigue en la pantalla.
- Con Trasfondo recompilado con este Dash, en Coffin: 11 de los 15 tests del lienzo pasan y ninguno se cuelga; antes
  se saltaban todos. COFFIN_SKIP deja fuera 4 con su motivo: _modes y _modes_rtg (el Workbench de Coffin conserva
  su ventana de fondo al salir de backdrop y el test no la vuelve a encontrar), _otro (el lienzo de Trasfondo
  también va a la ventana de fondo del test) y _rtg (tras los otros tests del arranque su última actualización
  repinta más de lo que espera; él solo pasa; sin mirar por qué). En A1200 3.1, A500, 3.2 y 3.2 RTG pasan los 52.

## Pendiente (fuera de este encargo)

- Los cuatro tests de arriba en Coffin.
- Publicar Trasfondo compilado con este Dash (el del disco de pruebas ya lo está, sin publicar).
