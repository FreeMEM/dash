# Extensión de VS Code: paridad con Forja (sprites, mapas, juegos)

Pedido del usuario (2026-11-07): poner al día la extensión y darle lo que Forja ya tiene para hacer juegos, el
editor de sprites y BOBs y el de mapas de tiles, y lo que venga al estilo pygame/Godot (Fragua). La tienda de VS
Code, cuando la extensión esté lista. Rama `vscode-0.5.0` (worktree `.worktrees/vscode-050`, PR #127).

## Lo que tiene Forja y la extensión no

| Forja (`~/Projects/forja`, README) | Extensión hoy | Tarea |
|---|---|---|
| Editor de sprites y BOBs: IFF ILBM con fotogramas, FRJA, GRAB | Nada | V1, V2, V3 |
| Amiga-B: sprite de hardware, acoplado de 15 colores o BOB nuevo | Nada | V3 |
| Editor de mapas `.fmap` (FORM FMAP): tiles, capas, choques, objetos | Nada | V1, V4 |
| "C": copia las líneas de Dash que cargan el sprite o el mapa | Nada | V2, V4 |
| Autocompletado, ir a la definición, dónde se usa | Sí (`compiler/lsp.py`) | — |
| Depurar, `.dashui`, compilar, ejecutar | Sí | — |
| Git (dashgit) | El Git de VS Code | — |
| Inferencia por ARexx | No aplica en el PC | — |
| Editor de escenas (Godot) | Aún no existe en Forja tampoco (diseño en `docs/JUEGOS_DISENO.md` de Forja) | V7, cuando Forja lo tenga |

## Reglas

- Los mismos ficheros que Forja y Dash, byte a byte: lo que guarda la extensión lo abren Forja, `bob_load`,
  `sprite_load`, `sprite_load_attached` y `tilemap_load`, y al revés. Referencia: `tests/iff.py` y `tests/fmap.py`
  de Forja, y `docs/SPRITES_LOOP.md` y `docs/MAPAS_DISENO.md` de Forja.
- Las mismas teclas que Forja donde se pueda (P lápiz, L línea, B caja, F relleno, K cuentagotas...), y deshacer
  con el de VS Code (editor propio con documento binario, `CustomEditorProvider`).
- Sin dependencias nuevas en tiempo de ejecución: el webview en JS normal, como el editor de `.dashui`.
- Cada tarea con sus pruebas en `npm test` (sin VS Code) y, si cabe, en `npm run test:vscode`.

## Tareas

- [x] V1. **Leer y escribir los ficheros en JS** (`iff.js`): ILBM (BMHD, CMAP, GRAB, FRJA, BODY sin comprimir y
      ByteRun1, masking 0, 1 y 2; sin FRJA, la regla de `bob_load`) y FMAP (MHDR, TSET, LAYR, OBJS). Pruebas con
      ficheros escritos por Forja y por Dash (`bitmap_save`, `tilemap_save`) y la vuelta: leer, escribir, igual.
- [x] V2. **Editor de sprites y BOBs** (`.iff`, `.ilbm`, `.lbm`, `.brush`, `.bob`, `.spr`): rejilla con zoom;
      lápiz, línea, caja (rellena con Mayúsculas), relleno, cuentagotas, punto de agarre; paleta con R G B (4 bits
      para sprites de hardware, 8 para BOBs); fotogramas (nuevo, duplicar, quitar, vaciar, espejo H y V, mover,
      desplazar, copiar y pegar), piel de cebolla, vista animada con velocidad (FRJA); tamaño y tipo (sprite de
      hardware de 16 de ancho y 3 colores, acoplado de 15, BOB); "Copiar código Dash".
- [x] V3. **Nuevo sprite, BOB o mapa** (orden y menú del explorador), como Amiga-B de Forja.
- [x] V4. **Editor de mapas** (`.fmap`): el tileset desde un BOB (un fotograma por tile de 8, 16 o 32); lápiz,
      caja, relleno, cuentagotas, borrar, espejo H y V; capas (ver, nueva, quitar, orden), capa de choques
      (sólido, plataforma, escalera, daño, con su trama), objetos (jugador, enemigo, moneda, puerta, otro; con
      sprite); ancho, alto, zoom, rejilla; "Copiar código Dash" con los choques y los objetos.
- [x] V5. **Ver en Amiga** para un sprite o un mapa: un programa pequeño lo enseña en el emulador, como la vista
      previa de MUI (`tools/emu_preview.py`).
- [x] V6. **Proyecto de juego**: "Dash: Nuevo proyecto" pregunta el tipo (aplicación MUI, como ahora, o juego); el
      juego trae un sprite, un mapa y un `main.dash` que los carga y mueve al jugador.
- [ ] V7. **Escenas (Godot)**: cuando Forja tenga su editor de escenas, el mismo en la extensión.
- [ ] V8. **Cierre**: README, CHANGELOG, capturas, versión, y la tienda (con el token del usuario).

## Decisiones

- El proyecto de juego (V6) usa los builtins de Dash; Fragua, cuando se publique (decisión del usuario, 2026-11-07).
- La extensión y Forja van a la par también con Fragua: lo que Forja tenga para Fragua (escenas, nodos, plantillas),
  la extensión lo tiene a la vez (usuario, 2026-11-07).

## Bitácora

- 2026-11-07, V1: `editor/vscode/media/iff.js` (Node y webview: `window.DashIFF`). ILBM portado de `sp_leer` y
  `sp_escribir` de Forja; FMAP de `tilemap_save`/`tilemap_load` del runtime. Ficheros fijos en `test/fixtures`
  escritos con `tests/iff.py` y `tests/fmap.py` de Forja (sin compresión, ByteRun1 con máscara, sprite de hardware,
  mapa con espejos, choques y objetos). Volver a escribir da los mismos bytes. 9 pruebas en `npm test`. Falta
  comprobar en el emulador que `bob_load` y `tilemap_load` leen lo que escribe la extensión: en V5.
- 2026-11-07, V2: editor de sprites y BOBs. `media/spriteModel.js` (las operaciones de `src/sprites.dash` de Forja:
  Bresenham, caja, relleno por lados, fotogramas, tamaño, T de tipo, colores de 4 bits en sprites de hardware,
  velocidad 1-50 y el mismo texto de "C"); `media/sprite.{html,css,js}` (el webview, con las teclas de Forja; el
  botón derecho también borra; Ctrl+rueda acerca); `spriteEditor.js` (`BinaryEditorProvider`, documento binario:
  cada cambio llega como el fichero entero, con deshacer, rehacer, guardar, revertir y copia de seguridad de VS Code;
  sirve también para el editor de mapas). Un fichero vacío se abre como BOB de 32 x 32 y 16 colores. Un `.iff` que no
  es ILBM (un 8SVX) dice que se abra con otro editor. Pruebas: 5 del modelo, 2 del proveedor y 8 del webview en
  Chromium sin ventana con clics y teclas de verdad (`test/sprite.js`, `test/sprite.html`).
- 2026-11-07, V4 (antes que V3, que necesita el editor de mapas para abrir uno nuevo): editor de mapas `.fmap`.
  `media/mapModel.js` (de `src/mapas.dash` de Forja: celdas, línea, caja, relleno, capas hasta 8, capa de choques,
  objetos hasta 256 que se mueven de celda en celda, tamaño hasta 1.024, y el mismo texto de "C"; además, renombrar
  capa y lado del tile, que Forja no tiene); `media/map.{html,js}` (vista por trozos con zoom 1-8, tileset leído
  junto al mapa por `readFile`, choques con su color, objetos con su sprite o su inicial; páginas Tiles, Capas, Mapa
  y Objetos; teclas de Forja: P B F K E, H V, coma y punto, G, + -, flechas, Supr). Mismo `BinaryEditorProvider`;
  un `.fmap` vacío se abre como 64 x 32 tiles de 16. Pruebas: 4 del modelo y 7 del webview (`test/map.js`).
  Arreglado al probar: la caché de tiles guardaba "sin imagen" antes de llegar el tileset; ocultar una capa ya no
  cambia la capa elegida.
- 2026-11-07, V3: "Dash: Nuevo sprite, BOB o mapa" (`dash.newGraphic`, `newGraphic.js`), en la paleta de órdenes y
  en el menú de una carpeta del explorador. Pregunta el tipo (sprite de hardware 16 x 16, acoplado, BOB 32 x 32 de 16
  colores, mapa 64 x 32 de tiles de 16: los tamaños de Forja), dónde guardarlo, y lo abre en su editor. Prueba en
  `extension: a new sprite, BOB or map`.
- 2026-11-07, V5: "Ver en Amiga" en los dos editores (`amigaView.js`). Un programa de Dash carga el fichero como un
  juego (BOB: todos los fotogramas con `bob_paste` y uno animado; sprite o acoplado: `sprite_load(_attached)` y
  animado; mapa: `tilemap_load` y su tileset con `tilemap_draw` y `tilemap_draw_masked` desde la esquina de la vista,
  sin las capas de choques ni las ocultas) en una pantalla PAL de baja resolución; `tools/emu_run.py --file` (nuevo:
  copia ficheros al disco emulado) lo ejecuta y la captura sale en el panel del editor. Va lo que tiene el editor,
  guardado o no. Comprobado en FS-UAE (A1200, 3.1): Dash carga el BOB, el sprite acoplado y el mapa que escribe la
  extensión (lo que faltaba de V1). Pruebas en `test/amigaView.js`: los programas compilan con `./dash`; con
  `DASH_PREVIEW_EMU=1`, 4 en el emulador.
- 2026-11-07, V6: "Dash: Nuevo proyecto" pregunta el tipo: aplicación MUI (como antes) o juego (`newProject.js`,
  `gameFiles`). El juego trae `jugador.iff` (sprite de hardware de 2 fotogramas), `tiles.iff` (BOB de 3 tiles),
  `nivel.fmap` (20 x 16, capa de choques con suelo sólido y plataformas que se cruzan desde abajo, y el objeto
  "jugador" donde empieza) y un programa que corre y salta con joystick o flechas, con `tilemap_get` en la capa de
  choques. No necesita MUI (va también en un A500). Probado en FS-UAE: el jugador cae y queda de pie en el suelo.
  Encontrado al probar: la captura (`tools/amiga/shot.c`) lee el dibujo de la pantalla y los sprites de hardware no
  están en él; "Ver en Amiga" de un sprite pinta además sus fotogramas ampliados con los lápices 17-31, que son los
  colores del sprite. Y un fallo de Dash, pasado a la sesión de Dash para la 2.6.0: `_dash_is_rtg_screen` toma una
  pantalla PAL nativa (0x21000) por RTG y `sprite_load` avisa "RTG screen detected".
