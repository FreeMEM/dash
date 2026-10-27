# Requisitos Funcionales de Dash
Versión: 2.0 (estado repasado el 2026-10-24)

> **Aviso:** estos son los requisitos originales del proyecto. Debajo de cada uno, **Hoy** dice cómo está:
> hecho (y cómo), hecho de otra forma, a medias, descartado o no hay. La lista real de funciones está en
> `BUILTINS.md` (681, generada del código); la sintaxis, en `QUICK_REFERENCE.md` y `MANUAL_REFERENCIA.md`; lo
> hecho y cuándo, en `ROADMAP.md` y en `git log`. Cambios de fondo: los programas piden AmigaOS 3.0 o superior
> (no 2.0) y funcionan en un 68000; no hay versión PPC; el gcc de bebbo genera Hunk directamente, sin `elf2hunk`.
> Las llamadas del estilo `System.algo` no existen: todo son funciones (`file_open_dialog`, `copper_create`...)
> o bloques del lenguaje (`Window`, `EventLoop`).

Este documento detalla los requisitos funcionales para el lenguaje de programación Dash.

## RF1: Módulo de Sistema (Workbench/OS)
El lenguaje debe proporcionar una capa de abstracción de alto nivel para interactuar con el entorno de escritorio de AmigaOS.

- **RF1.1: Gestión de Librerías:** Apertura y cierre automático de librerías críticas como `intuition.library` y `graphics.library` sin intervención del programador.
  - **Hoy: hecho.** El C generado abre al empezar las librerías que usa el programa y las cierra al salir. Las
    opcionales (red, AmiSSL, MUI, commodities, locale, CyberGraphX...) se abren al usarlas por primera vez; si
    no están, la función devuelve 0 o `false` en vez de colgarse.
- **RF1.2: Creación de Ventanas:** Soporte para la creación y gestión de ventanas de Intuition a través de un comando simple como `Window.open`.
  - **Hoy: hecho.** Un bloque `Window Nombre ... end` y `Nombre.open`, o `window_create(...)` (hasta 16
    ventanas a la vez, con su tamaño interior si se pide). Pantallas propias con `screen_open` y
    `screen_open_custom`. Las ventanas que quedan abiertas se cierran al salir.
- **RF1.3: Soporte de Gadgets:** Capacidad para definir y manejar gadgets estándar de AmigaOS, incluyendo `Button`, `Slider`, `Checkbox`, `String`, `ListView` y `Menu`.
  - **Hoy: hecho, y con más de un sistema.** GadTools: botón, casilla, texto, número, deslizador, ciclo,
    paleta, radio, lista (`listview_create`) y menús (`menu_*`), con `On Gadget` y `On Menu` en el `EventLoop`.
    También ReAction (`ra_*`, hasta 4 ventanas, clases de AmigaOS 3.2) y MUI 3.8 o 5 (`mui_*`, con editor
    visual en VS Code).
- **RF1.4: Selector de Archivos:** Integración con la `asl.library` para permitir la selección de archivos mediante un comando como `System.request_file`.
  - **Hoy: hecho.** `file_open_dialog` y `file_save_dialog` (con `file_get_path`, `file_get_name`,
    `file_fullpath`), y `dialog_file`, `dialog_color` y `dialog_font`.

## RF2: Módulo Bare Metal (Acceso Directo al Hardware)
Dash debe permitir a los desarrolladores tomar control total de la máquina para la creación de juegos y demos de alto rendimiento.

- **RF2.1: Control del Sistema:** Implementación de `System.takeover` para apagar de forma segura el sistema operativo y `System.restore` para devolver el control al Workbench.
  - **Hoy: no hay.** Dash no apaga el sistema: sprites, copper, audio y blitter van por las funciones del
    sistema (`GetSprite`, listas de copper de usuario, `audio.device`, `OwnBlitter`), y los programas conviven
    con el Workbench. Quitarle la máquina al sistema solo se puede con C propio (`@native`).
- **RF2.2: Acceso a Registros:** Acceso directo a los registros del chipset Custom (Agnus, Denise, Paula) a través de un objeto global `Custom`, permitiendo la manipulación directa de hardware (e.g., `Custom.color00 = #F00`).
  - **Hoy: a medias, sin el objeto `Custom`.** `peek_byte`/`peek_word`/`peek_long` y `poke_byte`/`poke_word`/
    `poke_long` leen y escriben cualquier dirección (`poke_word($DFF180, $F00)`), y los enteros admiten `$DFF000`
    y `0xDFF000`. `wait_vblank` y `wait_blit` esperan al barrido y al blitter.
- **RF2.3: Control del Copper:** Sintaxis declarativa para generar `Copper lists`, permitiendo efectos de video que cambian en sincronía con el barrido de pantalla.
  - **Hoy: hecho con funciones, no con sintaxis propia.** `copper_create`, `copper_wait`, `copper_move`,
    `copper_color`, `copper_end`, `copper_install` y `copper_free` (una lista de copper de usuario del
    sistema). El módulo `lib/amiga/copper.dash` añade degradados, arco iris y pantalla partida.
- **RF2.4: Sprites de Hardware:** Gestión completa de los 8 sprites de hardware nativos del Amiga, incluyendo su posición, datos de imagen y adjuntado (`attach`) para aumentar el número de colores.
  - **Hoy: a medias.** `sprite_create`/`sprite_load` (desde un dibujo, con marcos), `sprite_set_row`,
    `sprite_color`, `sprite_pos`, `sprite_show`/`sprite_hide`, `sprite_frame`, `sprite_collision` y
    `sprite_free`: los sprites libres del sistema (hasta 8), de 16 píxeles y 3 colores. **No hay** sprites
    adjuntados (`attach`, 15 colores). Además: sprites por software (`soft_sprite_*`, también en RTG) y BOBs
    (`bob_*`).

## RF3: Sonido y Redes
El lenguaje debe incluir funcionalidades para multimedia y conectividad.

- **RF3.1: Reproducción de Módulos:** Motor de audio capaz de reproducir archivos de tracker (formato `.mod`) de manera asíncrona, utilizando la `ptplay.library` o una rutina interna.
  - **Hoy: hecho, con rutina propia** (sin `ptplay.library`). `music_load`, `music_play`, `music_pause`,
    `music_resume`, `music_stop`, `music_volume`, `music_position`... Módulos ProTracker de 4 canales y 31
    instrumentos; suena con una interrupción de VBlank. Los efectos que hay están en `MANUAL_REFERENCIA.md`
    ("Música MOD").
- **RF3.2: Reproducción de Samples:** Soporte para cargar y reproducir sonidos (`.8svx` o `RAW`).
  - **Hoy: hecho para 8SVX sin comprimir** (`sound_load`, `sound_play`, `sound_loop`, `sound_volume`,
    `sound_period`...), con `audio.device` y sin esperar. RAW desde un fichero **no hay**; un sonido se puede
    hacer muestra a muestra (`sound_create`, `sound_sample`). También tonos (`tone_play`).
- **RF3.3: Conectividad de Red:** Acceso a la red con `bsdsocket.library` (cualquier pila: Roadshow, AmiTCP, MiamiDx), sin
  esconder el control al programa. Hoy hay: TCP como cliente (`net_connect`, también por pasos sin bloquear:
  `net_connect_start`/`net_connect_poll`) y como servidor (`net_listen`, `net_accept`); UDP con difusión
  (`net_udp_*`); TLS con AmiSSL que comprueba el certificado (`tls_*`, también por pasos y reanudando sesiones);
  `net_signal` para despertar el bucle de eventos con la red; la red en una tarea aparte (`task_start`); y
  consultas a la pila y a los drivers: interfaces de Roadshow con su estado y bytes, drivers SANA-II en uso con
  sus paquetes, bytes y la señal WiFi. HTTP no es un builtin: cada programa lo hace sobre TCP y TLS (Tachyon,
  `lib/http.dash`). Lo que falta: sockets raw (ICMP para un ping) y tramas en crudo del driver SANA-II (leer y
  escribir paquetes de cualquier protocolo); hoy, con `@native`. Detalle en `docs/MANUAL_REFERENCIA.md` ("Red").

## RF4: Gestión de Seguridad y Robustez (Safety Injections)
Para mejorar la estabilidad y evitar `Guru Meditations`, el transpilador de Dash inyectará código de seguridad de forma automática.

- **RF4.1: Verificación de Nulos (Null-Check):** Antes de utilizar cualquier puntero a ventana o librería, se verificará que no sea nulo.
  - **Hoy: hecho en lo que puede colgar el Amiga.** Las librerías se comprueban al abrirlas y las funciones de
    ventanas trabajan con números de ventana, no con punteros. Escribir un campo de un struct `nil` va a una
    zona de memoria aparte en vez de a la dirección 0; leerlo no se comprueba (lee memoria baja, sin daño).
    Comparar un texto con `nil` no lee la dirección 0. `./dash --memcheck` avisa de las lecturas y escrituras
    por `nil`.
- **RF4.2: Protección de Pila (Stack Protection):** El sistema calculará y definirá automáticamente un tamaño de pila adecuado para el programa, previniendo desbordamientos.
  - **Hoy: hecho de otra forma: no se calcula.** Cada programa pide una pila mínima al arrancar (16 KB; 32 KB
    con MUI; 64 KB con TLS) con el `swapstack` de libnix, porque el shell de 3.1 da 4 KB. Se cambia con
    `./dash --stack N` o `@stack N` en el programa. No se comprueba el desbordamiento mientras corre.
- **RF4.3: Guardia de Memoria (Memory Guard):** Se rastrearán todas las reservas de memoria para asegurar que se liberen correctamente al finalizar el programa, evitando fugas de memoria.
  - **Hoy: hecho.** Textos, listas y structs salen de un pool de exec que se borra entero al salir. Mientras
    corre, los temporales se liberan por vuelta de bucle y por función, y listas y structs llevan contador de
    referencias. `./dash --memcheck` avisa de dobles liberaciones y usos tras liberar, y dice lo que queda vivo
    al salir.
- **RF4.4: Verificación de Límites (Bounds Checking):** Se insertarán comprobaciones en accesos a arrays y operaciones de dibujo para asegurar que no se escriba fuera de los límites de memoria asignados.
  - **Hoy: a medias.** Las listas comprueban el índice: leer fuera da 0 y escribir fuera no hace nada (sin
    aviso). Los cortes (`l[a:b]`, `s[a:b]`) se ajustan a la longitud. El dibujo en una ventana lo recorta el
    sistema (sus capas). **No se comprueban** `buffer_*` ni `peek_*`/`poke_*`: escriben donde se les dice.
