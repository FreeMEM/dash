"""Las descripciones de los builtins en castellano, para docs/BUILTINS.md (tools/gen_builtins_doc.py). Las de
docs/BUILTINS.en.md son las de compiler/amiga_builtins.py, en inglés. Un builtin nuevo necesita su línea aquí:
la comprobación de la documentación (tests/run_tests.py, docs/builtins) falla si falta alguna."""

DESC_ES = {
    # Gráficos básicos
    "gfx_pen": "Pone el color (lápiz) de dibujo",
    "gfx_pen_bg": "Pone el color de fondo",
    "gfx_pen_outline": "Pone el color del borde de los rellenos",
    "gfx_mode": "Pone el modo de dibujo (JAM1, JAM2, COMPLEMENT, INVERSVID)",
    "gfx_pattern": "Pone el patrón de las líneas (16 bits)",
    "gfx_rgb": "Cambia un color de la paleta (componentes de 4 bits, 0-15)",
    "gfx_rgb8": "Cambia un color de la paleta (componentes de 8 bits, AGA)",
    "gfx_move": "Mueve el cursor de dibujo",
    "gfx_draw": "Dibuja una línea del cursor al punto",
    "gfx_line": "Dibuja una línea entre dos puntos",
    "gfx_pixel": "Dibuja un píxel",
    "gfx_pixel_read": "Lee el color de un píxel",
    "gfx_rect": "Dibuja un rectángulo relleno",
    "gfx_box": "Dibuja el contorno de un rectángulo",
    "gfx_ellipse": "Dibuja el contorno de una elipse",
    "gfx_circle": "Dibuja el contorno de un círculo",
    "gfx_ellipse_fill": "Dibuja una elipse rellena",
    "gfx_circle_fill": "Dibuja un círculo relleno",
    "gfx_flood": "Rellena un área (como un cubo de pintura)",
    "gfx_text": "Escribe un texto en el cursor",
    "gfx_text_at": "Escribe un texto en una posición",
    "gfx_text_len": "El ancho de un texto en píxeles",
    "gfx_clear": "Borra con el color 0",
    "gfx_clear_color": "Borra con un color",
    "gfx_scroll": "Desplaza una zona",
    "gfx_poly_begin": "Empieza un polígono en un punto",
    "gfx_poly_add": "Añade un vértice al polígono",
    "gfx_poly_end": "Cierra y rellena el polígono",
    "gfx_pens_draw": "Dibuja una imagen de lápices (un byte por píxel, fila tras fila) en x, y, cada píxel de zoom x zoom: una imagen entera en una llamada (3.1: WriteChunkyPixels)",
    "gfx_copy": "Copia una zona dentro de la ventana",
    # Gráficos avanzados
    "sprite_load": "Un sprite de una imagen (ILBM...): fotogramas de 16 píxeles uno al lado del otro, los colores 0-3 "
                   "los suyos (el 0, transparente); FALSE si no se puede",
    "sprite_create": "Crea un sprite vacío",
    "sprite_pos": "Pone la posición de un sprite",
    "sprite_show": "Hace visible un sprite",
    "sprite_hide": "Oculta un sprite",
    "sprite_color": "Pone un color de un sprite, índice 0-2 (0-14 en una pareja acoplada; componentes de 0 a 15)",
    "sprite_load_attached": "Un sprite de 15 colores de una imagen: una pareja de sprites acoplados; los colores 1-15 de la imagen (0 transparente) son los 17-31 de la pantalla. Falso si no puede",
    "sprite_load_colors": "Los colores 1-3 (1-15 en una pareja acoplada) de la paleta (CMAP) de una imagen como los colores del sprite, con 8 bits; falso si el fichero no la tiene",
    "bob_load_colors": "Los colores de la paleta (CMAP) de una imagen en la paleta de la pantalla desde el color first: cuántos puso",
    "sprite_rgb8": "Pone un color de un sprite, índice 0-2 (0-14 en una pareja acoplada), con componentes de 8 bits (0-255; exacto en AGA, 4 bits en ECS)",
    "sprite_frame": "Enseña el fotograma frame (0 el primero) de un sprite de sprite_load o sprite_load_attached",
    "sprite_free": "Libera la memoria de un sprite",
    "sprite_collision": "Mira si chocan dos sprites",
    "sprite_set_row": "Pone una fila de los datos de un sprite (2 planos de bits)",
    "soft_sprite_create": "Crea un sprite por software (vale en RTG)",
    "soft_sprite_free": "Libera un sprite por software",
    "soft_sprite_pixel": "Pone un píxel de un sprite por software",
    "soft_sprite_clear": "Borra un sprite por software con un color",
    "soft_sprite_row": "Pone una fila del sprite (en el formato de los sprites de hardware)",
    "soft_sprite_show": "Enseña un sprite por software",
    "soft_sprite_hide": "Oculta un sprite por software",
    "soft_sprite_pos": "Pone la posición de un sprite por software",
    "soft_sprite_x": "La posición X de un sprite por software",
    "soft_sprite_y": "La posición Y de un sprite por software",
    "bob_load": "Carga un BOB de un fichero",
    "bob_create": "Crea un BOB vacío",
    "bob_pos": "Pone la posición de un BOB",
    "bob_draw": "Dibuja un BOB",
    "bob_erase": "Borra un BOB (deja el fondo como estaba)",
    "bob_frame": "Pone el fotograma de la animación de un BOB",
    "bob_frame_width": "La imagen del BOB es una tira de fotogramas de ese ancho en píxeles (bob_load lo toma del trozo FRJA de Forja; si no, supone fotogramas cuadrados)",
    "bob_free": "Libera la memoria de un BOB",
    "bob_collision": "Mira si chocan dos BOB",
    "copper_create": "Crea una lista del copper",
    "copper_wait": "Añade una instrucción WAIT del copper",
    "copper_move": "Añade una instrucción MOVE del copper",
    "copper_color": "Añade un cambio de color del copper",
    "copper_end": "Termina la lista del copper",
    "copper_install": "Pone en marcha la lista del copper",
    "copper_free": "Libera la lista del copper",
    "bitmap_create": "Crea un bitmap",
    "bitmap_load": "Carga un bitmap IFF",
    "bitmap_save": "Guarda un bitmap IFF",
    "bitmap_free": "Libera un bitmap",
    "bitmap_blit": "Copia de un bitmap a la pantalla",
    "bitmap_blit_mask": "Copia de un bitmap con máscara",
    "bitmap_draw_to": "Dibuja en un bitmap desde ahora",
    "bitmap_draw_screen": "Dibuja en la pantalla desde ahora",
    # Entrada
    "key_pressed": "Mira si hay una tecla pulsada esperando",
    "key_get": "El código de la tecla",
    "key_wait": "Espera una tecla y da su código",
    "key_raw": "El código de tecla en bruto (sin traducir)",
    "key_text": "Pasa un código de tecla a texto",
    "mouse_x": "La X del ratón dentro del interior de la ventana (0 sin ventana)",
    "mouse_y": "La Y del ratón dentro del interior de la ventana (0 sin ventana)",
    "mouse_button": "Mira un botón del ratón (0 izquierdo, 1 derecho)",
    "event_window": "En un EventLoop: la ventana de la que vino el evento (window_create), 0 para la del propio bucle",
    "window_check_close": "Mira si se pulsó el botón de cerrar (sin esperar)",
    "close_window": "Cierra la ventana actual",
    "screen_open_mode": "Abre una pantalla con un modo exacto (el de dialog_screen_mode, o uno conocido: 0x21000 es PAL de baja resolución y 0x29000 la de alta), tamaño y profundidad; falso si el modo no existe o no admite esa profundidad",
    "screen_clone_wb": "Abre una pantalla pública igual que la del Workbench (modo, tamaño, profundidad, lápices y fuente) con ese nombre, donde otros programas pueden abrir ventanas; falso si no se puede (o el nombre ya está). screen_close espera a que se cierren sus ventanas",
    "screen_visitors": "Cuántos usos de la pantalla pública del programa hay: ventanas y bloqueos (LockPubScreen; una ventana de MUI puede contar dos); 0 si ninguno",
    "screen_open": "Abre una pantalla con el modo del Workbench y la profundidad que se diga",
    "screen_double_buffer": "Dos búferes para la pantalla propia del programa: se dibuja en el escondido y screen_flip lo enseña; falso sin pantalla propia (o si es pública) o antes de AmigaOS 3.0",
    "screen_flip": "Enseña lo dibujado en el búfer escondido (screen_double_buffer) y pasa a dibujar en el otro; espera a la pantalla, un fotograma como mucho. Falso si ahora no pudo cambiarlo",
    "screen_open_custom": "Abre una pantalla propia del tamaño y la profundidad que se digan",
    "screen_close": "Cierra la pantalla",
    "screen_width": "El ancho de la pantalla en píxeles",
    "screen_height": "El alto de la pantalla en píxeles",
    "check_lmb": "Mira si está pulsado el botón izquierdo del ratón (hardware)",
    "check_rmb": "Mira si está pulsado el botón derecho del ratón (hardware)",
    "check_mouse": "Mira si está pulsado algún botón del ratón (hardware)",
    "check_esc": "Mira si está pulsada la tecla Esc (hardware)",
    "wait_click": "Espera un clic del ratón (pulsar y soltar)",
    "wait_key": "Espera una tecla y da su código",
    "joy_x": "La dirección X del joystick (-1, 0, 1)",
    "joy_y": "La dirección Y del joystick (-1, 0, 1)",
    "joy_button": "El estado del botón del joystick",
    "joy_up": "Joystick hacia arriba",
    "joy_down": "Joystick hacia abajo",
    "joy_left": "Joystick a la izquierda",
    "joy_right": "Joystick a la derecha",
    "joy_fire": "El botón de disparo del joystick",
    # GadTools
    "gt_init": "Prepara GadTools (después de abrir la ventana)",
    "gt_cleanup": "Libera lo de GadTools",
    "gt_attach": "Pone los gadgets en la ventana (después de crearlos todos)",
    "gt_button": "Crea un botón; da su número",
    "gt_checkbox": "Crea una casilla",
    "gt_string": "Crea un campo de texto",
    "gt_integer": "Crea un campo de números",
    "gt_slider": "Crea un deslizador",
    "gt_palette": "Crea un selector de color de la paleta",
    "gt_text": "Crea un texto fijo",
    "gt_get_value": "El valor de un gadget (deslizador, paleta...)",
    "gt_set_value": "Cambia el valor de un gadget",
    "gt_get_string": "El texto de un campo de texto",
    "gt_event": "Mira si hay un evento de gadget: su número, -1 (ninguno) o -2 (cerrar)",
    "gt_wait_event": "Espera un evento de gadget: su número o -2 (cerrar)",
    "gt_cycle": "Crea un gadget de opciones que cambian al pulsarlo; opciones separadas por | (gt_get_value: la "
                "elegida)",
    "gt_enable": "Activa un gadget",
    "gt_disable": "Desactiva (en gris) un gadget",
    "gt_set_text": "Cambia el texto de un gt_text o un gt_string",
    # Menús
    "menu_title": "Añade el título de un menú",
    "menu_item": "Añade una opción de menú con su tecla y su número",
    "menu_sub": "Añade una opción de un submenú",
    "menu_separator": "Añade una raya de separación al menú",
    "menu_attach": "Pone los menús en la ventana (después de definirlos todos)",
    "menu_event": "Mira si hay un evento de menú: el número de la opción, o -1/-2",
    "menu_id": "En el On Menu de un EventLoop: el número de la opción elegida",
    "menu_check_item": "Añade una opción de menú con una marca que cambia cada vez que se elige",
    "menu_checked": "1 si está puesta la marca de esa opción",
    "menu_enable": "Activa o desactiva (en gris) una opción de menú, después de menu_attach",
    # Requesters ASL
    "file_open_dialog": "Enseña el diálogo de abrir fichero; true si se eligió uno",
    "file_save_dialog": "Enseña el diálogo de guardar fichero; true si se eligió uno",
    "file_get_path": "El cajón elegido en el último diálogo",
    "file_get_name": "El nombre de fichero elegido en el último diálogo",
    "file_fullpath": "La ruta entera (cajón + fichero) del último diálogo",
    # Sistema y memoria
    "debug_break": "Para en el depurador del emulador UAE (en un Amiga de verdad no hace nada; tools/emu_run.py "
                   "--debug)",
    "mem_chip_free": "La memoria chip libre",
    "mem_fast_free": "La memoria fast libre",
    "mem_total": "La memoria libre, chip y fast (la que queda, no el tamaño de la RAM)",
    "mem_chip_total": "El tamaño de la memoria chip en bytes (libre y en uso: AvailMem con MEMF_TOTAL)",
    "mem_fast_total": "El tamaño de la memoria fast en bytes (libre y en uso: AvailMem con MEMF_TOTAL)",
    "peek_byte": "Lee un byte de una dirección de memoria",
    "peek_word": "Lee un word (16 bits) de una dirección de memoria",
    "peek_long": "Lee un long (32 bits) de una dirección de memoria",
    "poke_byte": "Escribe un byte en una dirección de memoria",
    "poke_word": "Escribe un word (16 bits) en una dirección de memoria",
    "poke_long": "Escribe un long (32 bits) en una dirección de memoria",
    "time_delay": "Espera tics (50 por segundo)",
    "time_delay_ms": "Espera milisegundos (de 20 en 20: lo que dura un tic)",
    "random": "Un número al azar",
    "random_range": "Un número al azar entre min y max (los dos incluidos)",
    "random_seed": "Pone la semilla de los números al azar",
    "wait_vblank": "Espera al retrazado vertical",
    "wait_blit": "Espera a que acabe el blitter",
    "arena_new": "Crea una arena (memoria que se reparte por orden) de ese tamaño en bytes",
    "arena_alloc": "Pide memoria de una arena (muy rápido)",
    "arena_reset": "Vacía una arena (reusa la memoria sin liberarla)",
    "arena_free": "Libera una arena y toda su memoria",
    "arena_used": "Los bytes usados de una arena",
    "arena_available": "Los bytes libres de una arena",
    "refcount": "El contador de referencias de un objeto",
    "mem_trim": "Devuelve al sistema los charcos de bloques pequeños (hasta 128 bytes) que están del todo libres; los bytes devueltos",
    "mem_puddle": "El tamaño de los charcos del pool de memoria (de 1 KB a 1 MB; 4 KB si no); solo antes de pedir memoria",
    "retain": "Suma una referencia a mano",
    "release": "Quita una referencia a mano (libera el objeto si llega a 0)",
    # Ficheros (DOS)
    "file_open": "Abre un fichero (modo: 1005 leer, 1006 nuevo, 1004 leer y escribir; 0 si no se puede)",
    "file_close": "Cierra un fichero",
    "file_read_byte": "Lee un byte",
    "file_read_line": "Lee una línea en un búfer",
    "file_read": "Lee bytes en un búfer",
    "file_eof": "True al final del fichero (mira el byte siguiente sin gastarlo)",
    "file_write_byte": "Escribe un byte",
    "file_write_line": "Escribe un texto y un salto de línea (0 bien, -1 error)",
    "file_write": "Escribe bytes de un búfer",
    "file_print": "Escribe un texto en un fichero",
    "file_seek": "Va a un sitio del fichero (modo: OFFSET_BEGINNING, OFFSET_CURRENT, OFFSET_END)",
    "file_pos": "El sitio actual en el fichero",
    "file_size": "El tamaño de un fichero",
    "file_exists": "Mira si existe un fichero",
    "file_delete": "Borra un fichero",
    "file_rename": "Cambia el nombre de un fichero",
    "file_copy": "Copia un fichero",
    "dir_create": "Crea un cajón",
    "dir_change": "Cambia el cajón actual",
    "dir_current": "El nombre entero del cajón actual (\"Ram Disk:\"...)",
    "dir_read": "Lee lo que hay en un cajón, por orden de nombre (sin mirar mayúsculas): cuántas entradas, -1 si no es "
                "un cajón que se pueda leer. dir_entry_name y las demás las leen, hasta el siguiente dir_read",
    "dir_entry_name": "El nombre de la entrada i (desde 0) del último dir_read; \"\" si no la hay",
    "dir_entry_size": "El tamaño en bytes de la entrada i del último dir_read (0 si es un cajón)",
    "dir_entry_is_dir": "Verdadero si la entrada i del último dir_read es un cajón",
    "dir_entry_date": "La fecha de la entrada i del último dir_read, como time_unix: segundos desde el 1 de enero de 1970",
    "console_read": "Lee de la consola",
    "console_write": "Escribe en la consola (sin búfer)",
    "file_load": "Carga un fichero entero en un búfer: los bytes leídos, o -1",
    "file_save": "Guarda un búfer en un fichero: los bytes escritos",
    # Buffers
    "buffer_alloc": "Pide un búfer de memoria",
    "buffer_free": "Libera un búfer",
    "buffer_get_byte": "El byte en una posición",
    "buffer_set_byte": "Pone el byte de una posición",
    "buffer_get_word": "El word de 16 bits en una posición (big-endian)",
    "buffer_set_word": "Pone el word de 16 bits de una posición (big-endian)",
    "buffer_get_long": "El long de 32 bits en una posición (big-endian)",
    "buffer_set_long": "Pone el long de 32 bits de una posición (big-endian)",
    "buffer_copy": "Copia bytes de un búfer a otro",
    "buffer_fill": "Llena una zona de un búfer con un byte",
    # Texto
    "str_code": "El código (0-255) del carácter en la posición i; 0 fuera del texto",
    "str_char": "Un texto de un carácter con ese código",
    "str_find": "La posición del primer sub en s; -1 si no está",
    "str_find_from": "La posición del primer sub en s desde start; -1 si no está",
    "str_starts": "¿Empieza s por prefix?",
    "str_ends": "¿Acaba s en suffix?",
    "str_lower": "Una copia en minúsculas (Latin-1: también las letras con acento)",
    "str_upper": "Una copia en mayúsculas (Latin-1: también las letras con acento)",
    "str_trim": "Una copia sin espacios, tabuladores ni saltos de línea a los lados",
    "str_to_int": "El número escrito en s en esa base (2-36); Int(s) es en base 10",
    "str_from_int": "n escrito en esa base (2-36, letras en minúscula)",
    "str_replace": "Una copia con cada from cambiado por to",
    "str_contains": "Si sub está en s (\"\" está en todos)",
    "str_split": "Los trozos de s entre cada sep, en una [String] nueva; con sep \"\" o si no está, [s]",
    "file_read_text": "El fichero entero como texto (los bytes 0 pasan a espacios); nil si no se puede leer",
    "file_write_text": "Escribe el texto como el fichero entero; true si se escribió todo",
    "str_from_buffer": "Un texto con length bytes de un búfer desde offset (los bytes 0 pasan a espacios)",
    "str_to_buffer": "Copia los bytes de s a buffer + offset; da cuántos",
    # Red (TCP)
    "net_connect": "Una conexión TCP a host:port (nombre o dirección): el socket, o -1 (ver net_error)",
    "net_connect_start": "Empieza una conexión TCP sin esperar (el nombre se busca en otro proceso): el socket, o -1 "
                         "(ver net_error)",
    "net_connect_poll": "Sigue con net_connect_start sin esperar: 1 conectada, 0 aún no, -1 falló (el socket se "
                        "cierra; ver net_error)",
    "net_connect_stage": "Qué está haciendo net_connect_start: 0 buscando el nombre, 1 conectando, 2 hecho",
    "net_send": "Envía el texto entero; los bytes enviados o -1",
    "net_send_buffer": "Envía length bytes de un búfer; los bytes enviados o -1",
    "net_recv": "Hasta max bytes como texto: \"\" si no llegó nada en timeout_ms (-1: esperar), nil al cerrarse",
    "net_recv_buffer": "Hasta max bytes en un búfer: cuántos, 0 si se acabó el tiempo, -1 al cerrarse",
    "net_wait": "Espera a que haya algo que leer: 1 sí, 0 se acabó el tiempo, -1 error",
    "net_close": "Cierra la conexión",
    "net_resolve": "La dirección IPv4 de un nombre (\"a.b.c.d\"); nil si no se conoce",
    "net_error": "Qué falló en la última llamada net_",
    "net_listen": "Un servidor TCP en un puerto (0: uno libre cualquiera, net_port dice cuál): el socket que escucha, "
                  "o -1 (ver net_error)",
    "net_accept": "La siguiente conexión a un servidor de net_listen, esperando como mucho timeout_ms (-1: esperar, 0: "
                  "solo mirar): su socket (net_send, net_recv...), o -1 si no llegó ninguna",
    "net_peer": "La dirección (\"a.b.c.d\") del otro lado de una conexión TCP; nil si no hay",
    "net_port": "El puerto local de un socket (el que tocó con net_listen(0) o net_udp_open(0)); -1 si no hay",
    "net_udp_open": "Un socket UDP en un puerto (0: uno libre cualquiera), con difusión: el socket, o -1 (se cierra "
                    "con net_close)",
    "net_udp_send": "Envía el texto como un datagrama a host:port (\"255.255.255.255\": toda la red local); los bytes "
                    "enviados o -1",
    "net_udp_send_buffer": "Envía length bytes de un búfer como un datagrama a host:port; los bytes enviados o -1",
    "net_udp_recv": "El siguiente datagrama como texto (hasta max bytes): \"\" si no llegó ninguno en timeout_ms, nil "
                    "si hubo un error; quién lo envió: net_udp_from, net_udp_from_port",
    "net_udp_recv_buffer": "El siguiente datagrama en un búfer: su largo, 0 si no llegó a tiempo, -1 si hubo un error",
    "net_udp_from": "La dirección (\"a.b.c.d\") de quien envió el último datagrama recibido",
    "net_udp_from_port": "El puerto de quien envió el último datagrama recibido (para contestarle)",
    "net_stack_running": "True si hay una pila TCP/IP en marcha (su bsdsocket.library está en memoria), sin cargar nada "
                         "para saberlo. La de Roadshow sigue en memoria tras NetShutdown: esa se abre y se cierra",
    "net_release": "Suelta la red ya: se cierra bsdsocket.library, con los sockets, las conexiones TLS y las búsquedas "
                   "de nombres abiertos; la siguiente llamada net_ la abre otra vez (al acabar el programa también)",
    "net_signal": "La máscara de señal que dan los sockets con cada evento (conectado, datos, cerrado...), 0 si la "
                  "pila TCP/IP no puede: llamarla antes de cada espera, mui_wait_event_signals(net_signal())",
    # TLS (AmiSSL)
    "tls_connect": "TLS sobre un socket conectado, comprobando el certificado de host; -1 si no (net_error)",
    "tls_connect_start": "TLS sobre un socket conectado sin esperar al saludo: la conexión, o -1 (ver net_error)",
    "tls_connect_poll": "Sigue con tls_connect_start: 1 hecho (certificado comprobado), 0 aún no, -1 falló (la "
                        "conexión TLS se libera; ver net_error)",
    "tls_send": "Envía el texto entero; los bytes enviados o -1",
    "tls_send_buffer": "Envía length bytes de un búfer; los bytes enviados o -1",
    "tls_recv": "Como net_recv: \"\" si no llegó nada a tiempo, nil al cerrarse",
    "tls_recv_buffer": "Como net_recv_buffer: cuántos, 0 si se acabó el tiempo, -1 al cerrarse",
    "tls_close": "Acaba la TLS de la conexión (después, net_close del socket)",
    "tls_resumed": "True si la conexión retomó una sesión anterior con el mismo servidor (sin intercambiar claves)",
    # Fuentes y colores
    "font_open": "Abre una fuente (\"helvetica.font\", tamaño en píxeles, 2 como poco): la fuente, o 0 si no hay",
    "font_use": "Escribe con esta fuente",
    "font_close": "Cierra una fuente (las abiertas se cierran al acabar)",
    "font_style": "El estilo del texto: 0 normal, +1 subrayado, +2 negrita, +4 cursiva",
    "font_height": "El alto de la fuente actual",
    "font_baseline": "Los píxeles de arriba del texto a su línea base",
    "font_text_width": "El ancho de un texto en píxeles con la fuente y el estilo actuales",
    "font_size": "El tamaño que dio el sistema para esta fuente (el más cercano que tiene)",
    "color_pen": "El color de la pantalla en la que se dibuja más parecido a r, g, b (0-255); para gfx_pen",
    "color_pen_free": "Un color_pen de ese lápiz ya no hace falta; cuando no queda ninguno, vuelve a la pantalla (ReleasePen)",
    # Transparencia y degradados
    "gfx_blend_rect": "Mezcla el color 0xRRGGBB con lo dibujado, alfa 0-255 (pantallas de paleta: un tramado 4x4 del "
                      "color más cercano)",
    "gfx_gradient_rect": "Un degradado de (rgb1, alpha1) a (rgb2, alpha2), de arriba abajo si vertical, si no de "
                         "izquierda a derecha, mezclado con lo dibujado",
    "gfx_pixel_rgb": "El color de un píxel como 0xRRGGBB (en una pantalla de paleta, el de su color)",
    # Imágenes RGB desde un búfer
    "gfx_rgb_draw": "Dibuja un búfer RGB24 (3 bytes por píxel, filas una tras otra) en x, y (RTG: con un "
                    "WritePixelArray; pantallas de paleta: los colores más cercanos)",
    "gfx_rgb_draw_scaled": "Dibuja un búfer RGB24 en x, y a dest_width x dest_height (el píxel más cercano, fila a fila)",
    # Imágenes (datatypes)
    "image_load": "Una imagen de un fichero con los datatypes (ILBM; PNG, GIF, JPEG si el sistema los tiene), con los "
                  "colores de la pantalla en la que se dibuja: la imagen, o 0",
    "image_width": "El ancho de una imagen",
    "image_height": "El alto de una imagen",
    "image_draw": "Dibuja una imagen en x, y (sus píxeles transparentes no se dibujan)",
    "image_draw_part": "Dibuja la parte w x h de una imagen que empieza en sx, sy, en x, y",
    "image_scale": "Una copia de una imagen a w x h píxeles: una imagen nueva, o 0",
    "image_free": "Libera una imagen (las que queden se liberan al acabar)",
    "image_from_rgb": "Una imagen con los píxeles de un búfer (RGB, o RGBA con alfa: mezclado con lo de debajo en RTG, "
                      "dibujado desde 128 en una pantalla de paleta), con los colores de la pantalla: la imagen, o 0 "
                      "(necesita picture.datatype V43, AmigaOS 3.5+, salvo en pantallas RTG)",
    # Argumentos
    "arg_count": "Cuántos argumentos recibió el programa del Shell, o iconos de proyecto del Workbench (un doble clic "
                 "en un documento, mayúsculas + clic en varios)",
    "arg": "El argumento i, desde 0 (\"\" si no hay); desde el Workbench, la ruta entera del icono",
    "click_x": "La X del último On Click, en la ventana (dentro de sus bordes)",
    "click_y": "La Y del último On Click, en la ventana (dentro de sus bordes)",
    "time_ms": "Los milisegundos desde que empezó el programa (EClock de timer.device)",
    # Compresión (zlib)
    "inflate": "Descomprime n bytes de deflate sin cabecera (como en un ZIP) del búfer src a dest: los bytes "
               "escritos, o -1 si no es deflate o está cortado, -2 si no cabe en max, -3 si no hay memoria (zlib)",
    "inflate_auto": "inflate para gzip, zlib o deflate sin cabecera, según sus primeros bytes (un cuerpo HTTP con "
                    "Content-Encoding gzip o deflate): los bytes escritos, o lo mismo que inflate",
    "deflate": "Comprime n bytes del búfer src a dest como deflate sin cabecera, nivel 0 (sin comprimir) a 9 (lo más "
               "pequeño; -1: 6): los bytes escritos, -2 si no caben en max, -3 si no hay memoria (zlib; unos 260 KB "
               "mientras trabaja, con cualquier nivel)",
    "crc32": "El CRC-32 (como en ZIP y PNG) de n bytes de un búfer, siguiendo desde crc (0 para empezar)",
    # UTF-8
    "utf8_next": "La posición del carácter UTF-8 que sigue al del byte i (el largo, al final)",
    "utf8_prev": "La posición del carácter UTF-8 anterior al byte i (0 al principio)",
    "utf8_code": "El punto de código del carácter UTF-8 en el byte i (65533 para un byte no válido, 0 fuera del "
                 "texto)",
    "utf8_char": "Un texto con el carácter de ese punto de código en UTF-8 (\"\" para 0; U+FFFD si no es uno)",
    "utf8_length": "Cuántos caracteres UTF-8 tiene s (cada byte no válido cuenta como uno)",
    "utf8_to_latin1": "Un texto UTF-8 en Latin-1: lo que Latin-1 no tiene pasa a algo parecido (“ a \", € a EUR, … a "
                      "...) o a ?, igual que los bytes no válidos",
    "latin1_to_utf8": "Un texto Latin-1 en UTF-8 (los bytes desde 128 ocupan dos)",
    "utf8_check": "La posición del primer byte, de from a to - 1 de un búfer, que no es UTF-8 válido (o empieza una "
                  "secuencia cortada por to); -1 si todos lo son",
    # Comparar y buscar en un búfer
    "buffer_equals": "Si los n bytes de un búfer en offset son el texto s (y s tiene n bytes)",
    "buffer_find_byte": "La posición del primer byte igual a byte, de from a to - 1; o -1",
    "buffer_find_any": "La posición del primer byte, de from a to - 1, que es uno de los bytes del texto bytes; o -1",
    # Double y texto
    "str_from_double": "Un Double con tantos decimales (0: ninguno), su decimal más corto redondeado alejándose del "
                       "cero (2.675 con 2 da 2.68); decimales < 0: el más corto que se lee igual",
    "str_to_double": "El Double del principio del texto, como Double(s): exacto hasta 17 cifras significativas; 0.0 "
                     "si no hay número",
    # Matemáticas de Double
    "sqrt": "La raíz cuadrada (nan para un negativo)",
    "pow": "x elevado a y",
    "exp": "e elevado a x",
    "log": "El logaritmo neperiano (-inf para 0, nan para un negativo)",
    "log10": "El logaritmo en base 10",
    "sin": "El seno de x radianes",
    "cos": "El coseno de x radianes",
    "tan": "La tangente de x radianes",
    "asin": "El arcoseno en radianes, de -pi/2 a pi/2 (nan fuera de -1..1)",
    "acos": "El arcocoseno en radianes, de 0 a pi (nan fuera de -1..1)",
    "atan": "El arcotangente en radianes, de -pi/2 a pi/2",
    "atan2": "El ángulo del punto (x, y) en radianes, de -pi a pi",
    "floor": "El mayor número entero que no pasa de x (un Double)",
    "ceil": "El menor número entero que no es menor que x (un Double)",
    "round": "El número entero más cercano, las mitades alejándose del cero (2.5 da 3.0, -2.5 da -3.0)",
    "trunc": "La parte entera, hacia el cero (-2.7 da -2.0)",
    "fmod": "El resto de x / y con el signo de x (nan si y es 0)",
    "abs": "El valor absoluto, un Double",
    "is_nan": "True si x es nan (no es un número: sqrt(-1.0), 0.0 / 0.0)",
    "is_inf": "True si x es inf o -inf",
    # Expresiones regulares y comodines
    "regex_match": "True si el texto entero encaja con la expresión regular (la sintaxis común de ICU: . * + ? {m,n} [] "
                   "[^] ^ $ \\d \\w \\s \\b | grupos); false también si el patrón está mal (regex_error dice por "
                   "qué)",
    "regex_find": "La posición en bytes donde empieza lo primero que encaja desde el byte from; -1 si no hay (o el "
                  "patrón está mal); regex_length da su largo",
    "regex_length": "El largo en bytes de lo último que encajó con regex_find o regex_match (0 si nada)",
    "regex_error": "Por qué está mal el último patrón; \"\" si está bien",
    "wildcard_match": "True si el texto entero encaja con los comodines de Excel: * cualquier cosa, ? un carácter, ~ "
                      "delante de un carácter lo toma tal cual (~* ~? ~~)",
    # Simular teclado y ratón
    "input_key": "Pulsa y suelta una tecla en bruto en la ventana activa (0x44 Return, 0x45 Esc, 0x4C arriba, 0x4D "
                 "abajo, 0x4E derecha, 0x4F izquierda, 0x41 Retroceso), con las teclas 1 Mayúsculas, 2 Ctrl, 4 Alt, 8 "
                 "Amiga (sumadas) pulsadas alrededor",
    "input_text": "Escribe un texto en la ventana activa con el mapa de teclado (\"=SUM(A1:A3)\"); lo que el mapa no "
                  "puede escribir se queda fuera",
    "input_move": "Lleva el puntero a (x, y) desde la esquina de la ventana activa",
    "input_click": "Clic con el botón izquierdo en (x, y) desde la esquina de la ventana activa, con las teclas 1 "
                   "Mayúsculas, 2 Ctrl, 4 Alt (Amiga + clic es del sistema)",
    "input_button": "Pulsa (down true) o suelta un botón del ratón donde está el puntero: 1 izquierdo, 2 derecho (menús, "
                    "un menú contextual), 3 central",
    "input_drag": "Pulsa el botón izquierdo en (x1, y1), lo lleva pulsado a (x2, y2) y lo suelta (desde la esquina de "
                  "la ventana activa)",
    "input_qualifiers": "Las teclas pulsadas ahora (PeekQualifier de input.device): 1, 2 Mayúsculas; 8 Ctrl; 16, 32 "
                        "Alt; 64, 128 Amiga; 0 si no se puede abrir input.device",
    "input_menu": "Elige con el ratón, como un usuario, la opción item (desde 0, separadores incluidos) del menú menu "
                  "(desde 0) de la ventana activa: el botón derecho en su título, hasta la opción, hold tics (1/50 s) "
                  "pulsado, y suelta; false si no hay esa opción",
    "input_move_screen": "Lleva el puntero a (x, y) de la pantalla de píxel en píxel con botones pulsados (1 izquierdo, "
                         "2 derecho, 0 ninguno): los menús de MUI lo siguen",
    "input_active_title": "El título de la ventana activa (\"\" si no hay): para esperar a la del programa que se "
                          "prueba",
    # Portapapeles
    "clip_write_text": "Copia un texto UTF-8 al portapapeles (unidad 0, IFF FTXT en Latin-1, como lo leen los demás "
                       "programas): lo que Latin-1 no tiene pasa a algo parecido, como utf8_to_latin1 (€ a EUR); false "
                       "si no se puede escribir",
    "clip_read_text": "El texto del portapapeles (unidad 0) en UTF-8; \"\" si está vacío o no tiene texto",
    "clip_write_block": "Copia n bytes de un búfer a la unidad 1-255 del portapapeles como un FORM de un tipo propio (4 "
                        "caracteres, \"LCLC\"), después de clip_write_text: queda unido a ese texto, y si se copia "
                        "otra cosa a la unidad 0, el bloque se da por perdido",
    "clip_block_size": "Los bytes del bloque de ese tipo en una unidad del portapapeles; -1 si no hay o se copió otra "
                       "cosa después",
    "clip_read_block": "Copia el bloque de ese tipo de una unidad del portapapeles al búfer dest: sus bytes, -1 si no "
                       "hay o se copió otra cosa después, -2 si no cabe en max",
    # Ordenar textos según el idioma
    "str_compare_locale": "Compara dos textos UTF-8 en el orden del idioma del usuario (locale.library): -1 si a va "
                          "antes, 0 si son iguales, 1 si va antes b; los acentos y las mayúsculas cuentan solo después "
                          "de las letras (\"árbol\" antes que \"barco\", \"apple\" antes que \"Banana\"), y nada con "
                          "ignore_case. Sin locale.library, por sus bytes Latin-1",
    # Sistema y programa
    "time_unix": "El reloj del sistema en segundos desde el 1 de enero de 1970 (para fechas de HTTP y cookies)",
    "clock_days": "Los días desde el 1 de enero de 1978 según el reloj del sistema (el ds_Days de DateStamp)",
    "mem_largest": "El bloque de memoria libre más grande, chip o fast, en bytes",
    "json_scan": "Lee un texto JSON a una tabla de nodos en orden, cada uno seguido de lo que contiene (lib/json.dash hace "
                 "su árbol con ella): cuántos, -1 si no es JSON (json_scan_error dice por qué y dónde)",
    "json_scan_error": "Por qué el último json_scan dio -1, y en qué byte (\"unexpected end at byte 1\")",
    "json_scan_kind": "El tipo del nodo i: 0 null, 1 true o false, 2 número, 3 texto, 4 lista, 5 objeto",
    "json_scan_count": "Cuántos elementos tiene un nodo de lista u objeto (van detrás); 1 si es true, 0 si es false",
    "json_scan_text": "El texto de un nodo de texto (sin sus escapes, \\uXXXX en UTF-8) o de número (como está escrito)",
    "json_scan_name": "El nombre del nodo i dentro de su objeto (\"\" en una lista o arriba del todo)",
    "dbg_start": "Carga un programa compilado con dash --debug y lo lanza en un proceso propio, en pausa antes de su primera línea (se ponen los puntos de parada y luego dbg_continue): falso si no pudo (dbg_error dice por qué)",
    "dbg_error": "Por qué falló el último dbg_start",
    "dbg_state": "El programa depurado: 0 ninguno, 1 en pausa antes de empezar, 2 corriendo, 3 parado en una línea, 4 acabado",
    "dbg_signal": "La señal que recibe el depurador cuando el programa para o acaba (para mui_wait_event_signals)",
    "dbg_wait": "Espera a que el programa pare o acabe, como mucho ms (0: sin tope): su estado",
    "dbg_break": "Un punto de parada en esa línea de ese fichero (\"prog.dash\": el final de su ruta): falso si la línea no tiene código",
    "dbg_unbreak": "Quita el punto de parada de esa línea",
    "dbg_continue": "Sigue (desde el principio o una parada) hasta un punto de parada o el final",
    "dbg_step": "Sigue hasta la línea siguiente, entrando en las funciones a las que llama",
    "dbg_next": "Sigue hasta la línea siguiente de esta función (o de la que la llamó)",
    "dbg_out": "Sigue hasta que la función vuelve: la línea siguiente de la que la llamó",
    "dbg_pause": "Para el programa que corre en la siguiente línea que ejecute",
    "dbg_end": "Acaba el programa (Ctrl-C y, en su siguiente línea, su final de siempre): verdadero si acabó en ms",
    "dbg_rc": "El código de retorno del programa acabado",
    "dbg_file": "El fichero de la línea donde paró el programa (su ruta entera)",
    "dbg_line": "La línea donde paró el programa (0 si no está parado)",
    "dbg_function": "La función donde paró el programa (\"Main\", \"Punto.mover\"...)",
    "dbg_frames": "Cuántas llamadas hay abiertas donde paró: 1 en Main, 2 en una función que llamó Main... (0 si no está parado)",
    "dbg_frame_function": "La función de la llamada i: 0 donde paró, 1 la que la llamó...",
    "dbg_frame_line": "La línea donde está la llamada i: 0 donde paró, 1 la de la llamada en la que la llamó...",
    "dbg_frame_file": "El fichero de la llamada i (su ruta entera)",
    "dbg_vars": "Cuántas variables ve la llamada i: sus parámetros y las variables declaradas antes de su línea",
    "dbg_var_name": "El nombre de la variable k (desde 0) de la llamada i",
    "dbg_var_type": "El tipo de la variable k de la llamada i, como en Dash (\"Int\", \"[String]\", \"Punto\")",
    "dbg_globals": "Cuántas variables globales tiene el programa",
    "dbg_global_name": "El nombre de la global g (desde 0)",
    "dbg_value": "El valor de expr en la llamada i, como texto: una variable de esa llamada o una global, con .campo y [n] detrás (\"p.hijos[0].x\"): 3, \"hola\", Punto(x: 3, y: 4), [1, 2], nil; \"? \" y el porqué si no se puede",
    "dbg_value_type": "El tipo de expr en la llamada i (\"\" si no se puede)",
    "dbg_reg": "Un registro del programa parado: 0-7 d0-d7, 8-15 a0-a7, 16 el PC",
    "dbg_peek": "1, 2 o 4 bytes de memoria en addr, sin signo",
    "dbg_output": "Lo que ha escrito el programa hasta ahora (salida y salida de errores)",
    "rexx_send": "Manda una orden ARexx al puerto público de otro programa (\"MULTIVIEW.1\"; \"REXX\": ejecutar un "
                 "script) y espera la respuesta: su RESULT (\"\" si no hay), el RC en rexx_rc(). No al puerto del "
                 "propio programa: se esperaría a sí mismo",
    "rexx_rc": "El RC del último rexx_send: 0 bien, 5, 10, 20... los del programa; -1 si no existe el puerto, -2 sin "
               "rexxsyslib.library",
    "ports_read": "Lee los nombres de los puertos públicos abiertos (los de ARexx entre ellos): cuántos, para port_name, "
                  "hasta el siguiente ports_read",
    "port_name": "El nombre del puerto i (desde 0) del último ports_read",
    "tasks_read": "Lee las tareas y procesos del sistema (el programa, el primero): cuántos, para las task_entry_, "
                  "hasta el siguiente tasks_read",
    "task_entry_name": "El nombre de la tarea i del último tasks_read (\"Shell Process\", \"input.device\"...)",
    "task_entry_command": "La orden que ejecuta un proceso de Shell del último tasks_read (\"\" si ninguna)",
    "task_entry_state": "El estado de la tarea i: \"running\" (el programa), \"ready\" o \"waiting\"",
    "task_entry_priority": "La prioridad de la tarea i del último tasks_read",
    "task_entry_cli": "El número de Shell de la tarea i (el que da Status, para Break), 0 si no es un proceso de Shell",
    "assigns_read": "Lee las asignaciones (C:, LIBS:, las de Assign): cuántas, para assign_name y assign_path, hasta "
                    "el siguiente assigns_read",
    "assign_name": "El nombre de la asignación i del último assigns_read, sin los dos puntos",
    "assign_path": "Adónde apunta la asignación i: un cajón (\"Workbench:C\"), varios separados por \";\", o el "
                   "nombre que buscará una diferida o no ligada",
    "run_capture": "Ejecuta una orden y espera a que acabe: lo que escribió, con su código de retorno en run_rc(). Con "
                   "timeout_ms mayor que 0, al pasar ese tiempo la orden recibe Ctrl-C (y otra vez cada segundo hasta "
                   "que acaba). Solo su salida: AmigaOS no da canal de errores a una orden lanzada así (el stderr de un "
                   "programa en C va a la consola; dashc escribe sus errores por su salida en el Amiga)",
    "run_start": "run_capture sin esperar: un número para run_ready, run_break y run_finish, 0 si no pudo empezar. El "
                 "programa espera al acabar a las que no terminó",
    "run_ready": "Verdadero cuando un run_start ha acabado (no espera; también aplica el tope de tiempo)",
    "run_break": "Manda Ctrl-C a un run_start que sigue en marcha (y otra vez cada segundo hasta que acaba)",
    "run_finish": "Lo que escribió un run_start, como run_capture (espera si sigue en marcha), y lo olvida",
    "run_rc": "El código de retorno del último run_capture o run_finish: el de la orden, -1 si no pudo empezar, -2 si "
              "se le acabó el tiempo",
    "env_get": "Una variable de entorno (de la Shell del programa y si no, de ENV:), hasta su primer fin de línea; \"\" "
               "si no existe",
    "env_set": "Pone una variable en ENV: (con save verdadero, también en ENVARC:, para que siga tras reiniciar); falso "
               "si no pudo",
    "run_command": "Ejecuta una orden y espera a que acabe, con su salida en la del programa: su código de retorno, -1 "
                   "si no pudo empezar",
    "wb_open": "Abre un cajón, un programa o un proyecto como un doble clic en su icono (workbench.library 44, OS "
               "3.5+); false si no pudo",
    "program_path": "La ruta entera del programa (\"Work:Tachyon/Tachyon\"), desde un Shell o desde el Workbench",
    "locale_language": "El primer idioma preferido del usuario en las preferencias de Locale (\"español\"); \"\" si no "
                       "hay",
    "cpu_model": "El procesador: 68000, 68010, 68020, 68030, 68040 o 68060",
    "fpu_model": "La FPU: 68881, 68882, 68040 o 68060 (la del procesador); 0 si no hay",
    "library_version": "La versión de una librería (\"muimaster.library\"), cargándola si no está en memoria; -1 si no "
                       "está",
    "library_revision": "La revisión de una librería (el 3 de 47.3), como library_version; -1 si no está",
    "resident_version": "La versión de un módulo residente del sistema (FindResident: \"MorphOS\" dice que el programa corre en MorphOS); -1 si no hay",
    "task_priority": "Pone la prioridad del programa (-128 a 127; el Shell da 0): la que tenía",
    "build_date": "La fecha en que se compiló el programa, \"2026-10-28\"",
    "build_time": "La hora en que se compiló el programa, \"20:45:10\"",
    "console_flush": "Saca ya lo que Print dejó en el búfer de la salida (una línea de progreso sin su final)",
    # Imágenes decodificadas por el programa
    "image_decode": "Decodifica un JPEG (TJpgDec), WebP (libwebp; los dos ya reducidos al decodificar), PNG, GIF, BMP "
                    "(stb_image) o SVG (nanosvg: dibujado para cubrir maxw x maxh, RGBA) a píxeles RGB o RGBA, "
                    "reducidos hasta que no pasen mucho de maxw x maxh (0, 0: su tamaño; negativos, un tope: un SVG va "
                    "entonces a su tamaño, más pequeño si no cabe): la imagen decodificada, o 0. "
                    "Sin datatypes, y vale dentro de un task_start",
    "image_decode_start": "image_decode en un proceso aparte, uno por debajo de la prioridad del programa, para que la ventana siga respondiendo: un número para image_decode_ready e image_decode_finish, o 0 si no pudo empezar",
    "image_decode_ready": "Cierto cuando un image_decode_start ha terminado (no espera)",
    "image_decode_finish": "Lo que decodificó un image_decode_start, como image_decode (0 si no pudo); espera si aún no ha acabado y libera su proceso",
    "image_decoded_width": "El ancho de una imagen decodificada",
    "image_decoded_height": "El alto de una imagen decodificada",
    "image_decoded_alpha": "True si una imagen decodificada tiene alfa (4 bytes por píxel, RGBA; si no, 3, RGB)",
    "image_decoded_pixels": "Los píxeles de una imagen decodificada, fila tras fila: un búfer para buffer_get_byte o "
                            "image_from_rgb",
    "image_decoded_free": "Libera una imagen decodificada",
    "image_from_decoded": "Una imagen (como image_from_rgb) de una imagen decodificada, que hay que liberar después",
    # Fuentes TrueType
    "font_from_ttf": "Una fuente TrueType (TTF, un OTF con contornos TrueType, o un WOFF o WOFF2 de ellos) a size "
                     "píxeles de em y al width % de su ancho (0: 100), sus caracteres Latin-1 en un plano de 1 bit "
                     "(stb_truetype): una fuente para font_use, o 0. Se libera con font_ttf_free, no con font_close",
    "font_ttf_icon": "Una fuente del fichero cuya \"A\" es el carácter code (un icono de una fuente web, en la zona privada de Unicode) a size píxeles, con las demás letras vacías: se dibuja \"A\" con ella; 0 si no se puede",
    "font_ttf_free": "Libera una fuente de font_from_ttf (no mientras una ventana siga escribiendo con ella); las que "
                     "queden se liberan al acabar",
    "font_ttf_forget": "font_from_ttf guarda los 8 últimos ficheros leídos para otros tamaños: este se lee otra vez la "
                       "próxima",
    # Red en una tarea aparte
    "net_bg_open": "Pide una conexión TCP que una tarea propia abre, por la que envía y recibe mientras el programa "
                   "está ocupado (hasta 48): su número, o -1. net_bg_state dice cómo va",
    "net_bg_open_tls": "net_bg_open con TLS (AmiSSL, comprobando su certificado)",
    "net_bg_state": "1 pedida, 2 conectando, 3 negociando la TLS, 4 abierta, 5 cerrada, 6 error (net_bg_error dice por "
                    "qué)",
    "net_bg_stage": "Mientras conecta, en qué fase está, como net_connect_stage",
    "net_bg_error": "Por qué falló o se cerró una conexión; \"\" si no",
    "net_bg_send": "Deja un texto para enviar (la tarea lo envía en cuanto la conexión esté abierta); false si no hay "
                   "memoria",
    "net_bg_send_buffer": "net_bg_send de n bytes de un búfer",
    "net_bg_recv": "Hasta max bytes de lo que ha llegado, a un búfer, sin esperar: cuántos (0: nada aún), -1 si está "
                   "cerrada y no queda nada. task_signal despierta al programa cuando llega algo",
    "net_bg_pending": "Cuántos bytes han llegado y no se han leído",
    "net_bg_close": "Cierra una conexión y deja libre su número",
    "net_bg_idle": "La tarea acaba sola tras tantos ms sin tráfico (2000; una conexión que el programa sigue leyendo, "
                   "esperando la respuesta, cuenta como tráfico); cuando hace falta empieza otra",
    "net_bg_stop": "Acaba la tarea ya (cierra lo que esté abierto) y la espera; también al acabar el programa",
    # Ventanas de otros programas
    "window_find": "La ventana de otro programa (o la del propio) cuyo título empieza por title, en cualquier pantalla: "
                   "un número para window_found_* y gadget_*, 0 si no hay (no vale cuando se cierra)",
    "window_found_activate": "Una ventana de window_find delante, con su pantalla, y activa (los input_* van a la "
                             "ventana activa)",
    "window_found_box": "De una ventana de window_find: 0 izquierda, 1 arriba (en su pantalla), 2 ancho, 3 alto, 4 borde "
                        "izquierdo, 5 borde de arriba",
    "gadget_index": "El sitio (desde 0, también los gadgets de la propia ventana) del gadget cuyo texto es text en una "
                    "ventana de window_find; -1 si no hay. Los botones de GadTools no guardan su texto: se cuentan "
                    "desde uno de al lado",
    "gadget_x": "La x del centro del gadget del sitio n de una ventana de window_find, desde su esquina (como cuenta "
                "input_click); -1 si no hay",
    "gadget_y": "La y del centro de ese gadget, como gadget_x",
    "gadget_selected": "True si el gadget del sitio n (una casilla) está marcado",
    "screen_pixel": "El color del píxel (x, y) de la pantalla de delante; -1 fuera de ella",
    "cx_send": "Una orden a una commodity por su nombre, como hace Exchange (15 desactivar, 17 activar, 19 enseñar, 21 "
               "ocultar, 23 quitar...): 0 hecho, -1 no hay esa commodity, -2 no tiene puerto, -99 no hay "
               "commodities.library",
    # Audio
    "sound_load": "Carga un sonido IFF 8SVX (sin comprimir)",
    "sound_sample": "Pone una muestra (-128..127) de un sonido de sound_create",
    "sound_create": "Crea un sonido en silencio en memoria chip: largo en muestras, frecuencia en muestras por segundo",
    "sound_free": "Libera la memoria de un sonido",
    "sound_play": "Toca un sonido una vez en un canal (0-3)",
    "sound_stop": "Para un canal",
    "sound_loop": "Toca un sonido en bucle en un canal (hasta sound_stop)",
    "sound_playing": "Mira si un canal está sonando",
    "sound_volume": "Pone el volumen de un canal (0-64)",
    "sound_period": "Pone el periodo de un canal (el tono: cuanto más bajo, más agudo)",
    "music_load": "Carga un fichero MOD",
    "music_play": "Empieza a tocar la música",
    "music_stop": "Para la música",
    "music_pause": "Pausa la música",
    "music_resume": "Sigue con la música",
    "music_volume": "Pone el volumen de la música (0-64)",
    "music_position": "Pone la posición de la música",
    "music_pos": "La posición de la canción que suena (en la lista de orden)",
    "music_row": "La fila del patrón que suena (0-63)",
    "music_free": "Libera los datos de la música",
    "tone_play": "Toca un tono senoidal: frecuencia en Hz, volumen 0-64, duración en milisegundos (vuelve en seguida)",
    # Tareas, reloj, traducciones y escritorio
    "task_start": "Ejecuta una función f(arg: Int) -> Int en otro proceso: una de Dash que solo use Int, Bool, Float y "
                  "builtins que no den textos ni listas (el compilador lo comprueba), o una de C (@extern, @native: "
                  "malloc/free sí, textos y listas de Dash no); 128 KB de pila, la prioridad del programa: la tarea, o 0",
    "task_start_with": "task_start con su pila en bytes (0: 128 KB) y su prioridad respecto a la del programa (-1: solo "
                       "corre cuando el programa espera)",
    "task_done": "True cuando la función ha acabado (no espera)",
    "desktop_canvas": "Una zona del escritorio del Workbench (debajo de la barra de título de la pantalla), detrás de "
                      "los iconos y sin clics, en modo fondo o no, planar o RTG; x o y negativas: desde el borde derecho "
                      "o el de abajo (-1 lo toca). 0 si no se puede",
    "desktop_canvas_on_draw": "La función f(x, y, ancho, alto) que dibuja la zona con gfx_ (desde 0, 0), sobre el fondo "
                              "de escritorio que hay debajo",
    "desktop_canvas_update": "Dibuja otra vez la zona ya y enseña lo que cambió, sin tocar los iconos",
    "desktop_canvas_update_area": "desktop_canvas_update solo en esa parte de la zona: el dibujo se recorta a ella y "
                                  "solo se compara ella (lo demás se queda como estaba; donde el escritorio se repintó "
                                  "entretanto, también se dibuja)",
    "desktop_canvas_veil": "El fondo de debajo del dibujo mezclado con rgb (0xRRGGBB) con alpha (0-255; 0: ninguno), "
                           "una vez y otra solo donde el escritorio lo repinta: como un gfx_blend_rect sobre toda la zona "
                           "en cada dibujo, sin su coste. Quita los velos de desktop_canvas_veil_rect. Se ve desde el "
                           "siguiente desktop_canvas_update",
    "desktop_canvas_veil_rect": "Un velo más, solo en ese rectángulo, mezclado una vez sobre el de desktop_canvas_veil "
                                "(que los quita: llamarlo antes): una caja que siempre está. Hasta 16; false si no "
                                "caben más",
    "desktop_canvas_drawing": "Dentro de la función de dibujo: true si ese rectángulo llega a la parte que se dibuja "
                              "(toda la zona, o la de desktop_canvas_update_area con lo que repintó el escritorio), "
                              "para saltarse lo que no se vería. Fuera de ella, siempre true",
    "desktop_canvas_free": "Vuelve a poner el fondo de escritorio en la zona (al acabar el programa también)",
    "break_check": "True si llegó un Ctrl-C (\"Break\" en el Shell, u otra copia: single_instance); se borra",
    "single_instance": "Una sola copia a la vez: false si corre otra copia del programa (un puerto público con ese "
                       "nombre), que recibe un Ctrl-C; si no, true (el puerto es del programa hasta que acaba)",
    "tooltype": "Un tooltype del programa: desde el Shell, el argumento NOMBRE=valor (también NOMBRE=\"a b\"); si no "
                "(o desde el Workbench), el tooltype de su icono; default si no está en ninguno",
    "cx_broker": "El programa en Exchange como commodity, con Mostrar y Ocultar, activado (nombre de hasta 23 letras, "
                 "título y descripción de hasta 39); false sin commodities.library o si ya hay uno con ese nombre. Se "
                 "quita al acabar el programa",
    "cx_key_add": "Una tecla rápida más para la commodity (hasta 32, n de 1 a 32; también un botón del ratón: "
                  "\"rawmouse lalt mouse_leftpress\"): cx_command da 100 + n al pulsarla, y el evento no sigue; "
                  "\"\" quita la tecla n; false si la descripción no vale (o no hay cx_broker)",
    "wm_read": "Lee las ventanas de la pantalla del Workbench, de delante atrás (hasta 64): cuántas, para wm_id, "
               "wm_title, wm_task, wm_box y wm_flags, hasta el siguiente wm_read",
    "wm_id": "El id de la ventana i del último wm_read, para wm_set_box, wm_front... (0 fuera de la lista)",
    "wm_title": "El título de la ventana i del último wm_read (\"\" si no tiene)",
    "wm_task": "El programa de la ventana i: la orden de un proceso de Shell (sin su ruta), o el nombre de su tarea "
               "(\"Workbench\")",
    "wm_box": "De la ventana i: 0 izquierda, 1 arriba, 2 ancho, 3 alto, 4 ancho mínimo, 5 alto mínimo, 6 ancho máximo, "
              "7 alto máximo (0 o 65535: sin límite); -1 fuera de la lista",
    "wm_flags": "De la ventana i, sumados: 1 se puede redimensionar, 2 de fondo (backdrop), 4 sin bordes, 8 activa, "
                "16 con barra de arrastre, 32 del propio programa, 64 un cajón del Workbench, 128 con un requester",
    "wm_set_box": "Mueve y redimensiona una ventana por su id, dentro de sus límites y de su pantalla (la que no tiene "
                  "botón de tamaño se queda con el suyo); false si ya no está abierta. Intuition lo hace justo después",
    "wm_front": "Una ventana delante de las demás; false si ya no está abierta",
    "wm_back": "Una ventana detrás de las demás; false si ya no está abierta",
    "wm_activate": "Hace activa una ventana (las teclas van a ella); false si ya no está abierta",
    "wm_zip": "Una ventana a su otro tamaño, como su botón de zoom; false si ya no está abierta",
    "wm_active": "El id de la ventana activa, si está en la pantalla del Workbench; 0 si no",
    "wm_at": "El id de la ventana que hay en (x, y) de la pantalla del Workbench, la de delante; 0 si ninguna",
    "wm_pointer_x": "Dónde está el puntero en la pantalla del Workbench: la x",
    "wm_pointer_y": "Dónde está el puntero en la pantalla del Workbench: la y",
    "wm_bar_height": "El alto de la barra de título de la pantalla del Workbench (donde suelen empezar las ventanas)",
    "cx_hotkey": "La tecla rápida de la commodity, según su descripción (\"ctrl alt t\"): cx_command da 6 al pulsarla; "
                 "false si la descripción no vale (o no hay cx_broker); \"\" la quita",
    "cx_command": "La siguiente orden de Exchange o de la tecla rápida: 0 ninguna, 1 ocultar, 2 mostrar, 3 desactivar, "
                  "4 activar, 5 quitar, 6 tecla rápida. Desactivar y activar apagan y encienden la commodity (y su "
                  "tecla)",
    "cx_wait": "Espera, sin gastar nada, hasta que llegue una orden (la da como cx_command), un Ctrl-C (-1, se borra) o "
               "pasen ms milisegundos (0)",
    "disks_read": "Lee los volúmenes montados (con disco dentro), su tamaño y su espacio libre, preguntando a todos a "
                  "la vez y esperando como mucho ms milisegundos: cuántos hay. No pide ningún disco",
    "disk_name": "El nombre del volumen i (de 0 a disks_read() - 1) del último disks_read, sin los dos puntos",
    "disk_kb": "El tamaño del volumen i en KB (como lo enseña Info); -1 si no contestó a tiempo",
    "disk_free_kb": "El espacio libre del volumen i en KB; -1 si no contestó a tiempo",
    "net_ifs_read": "Lee las interfaces de red de Roadshow (también lo0), su estado y sus bytes: cuántas hay; -1 sin "
                    "pila TCP/IP o con una que no lo dice (AmiTCP, Miami)",
    "net_if_name": "El nombre de la interfaz i (de 0 a net_ifs_read() - 1) del último net_ifs_read",
    "net_if_up": "True si la interfaz i está levantada (conectada)",
    "net_if_bytes_in": "Los bytes recibidos por la interfaz i (los 32 bits bajos: la diferencia entre dos lecturas son "
                       "los bytes de entretanto, aunque pase de 2 GB)",
    "net_if_bytes_out": "Los bytes enviados por la interfaz i (los 32 bits bajos, como net_if_bytes_in)",
    "pistorm_temperature": "La temperatura de la Raspberry Pi de una PiStorm (Emu68), en décimas de grado Celsius (523: "
                           "52,3), de su firmware por el mailbox.resource de Emu68; -1 sin Emu68",
    "wifi_read": "Pide al driver SANA-II de una interfaz de Roadshow su señal WiFi, esperando como mucho ms "
                 "milisegundos: 0 leída (wifi_signal, wifi_noise), 1 no contestó a tiempo, 2 el driver no lo dice, 3 no "
                 "hay esa interfaz, 4 el driver da un error (desconectado), 5 la pila tiene el driver solo para ella, -1 "
                 "sin Roadshow",
    "wifi_read_device": "Como wifi_read, preguntando directamente a un driver SANA-II en uso (\"wifipi.device\", unidad "
                        "0), con cualquier pila TCP/IP: 0 leída, 1 no contestó a tiempo, 2 el driver no lo dice, 3 no "
                        "hay ese driver en uso, 4 desconectado, 5 la pila lo tiene solo para ella",
    "net_drivers_read": "Lee los drivers de red SANA-II en uso, con cualquier pila TCP/IP (los de DEVS:Networks que "
                        "algo tiene abiertos): cuántos",
    "net_driver_name": "El nombre del driver i (de 0 a net_drivers_read() - 1) del último net_drivers_read "
                       "(\"wifipi.device\")",
    "net_driver_read": "Pide a un driver SANA-II en uso sus paquetes de entrada y salida, esperando como mucho ms: los "
                       "códigos de wifi_read_device (0 leído: net_driver_packets_in, net_driver_packets_out)",
    "net_driver_has_bytes": "True si el driver del último net_driver_read cuenta bytes (sus paquetes IPv4, IPv6 y "
                            "ARP): net_driver_bytes_in y net_driver_bytes_out",
    "net_driver_bytes_in": "Los bytes recibidos por el driver del último net_driver_read (los 32 bits bajos), si "
                           "net_driver_has_bytes",
    "net_driver_bytes_out": "Los bytes enviados por el driver del último net_driver_read, si net_driver_has_bytes",
    "net_driver_packets_in": "Los paquetes recibidos por el driver del último net_driver_read que dio 0",
    "net_driver_packets_out": "Los paquetes enviados por el driver del último net_driver_read que dio 0",
    "wifi_signal": "El nivel de señal del último wifi_read que dio 0, en dBm (-30 muy bueno, -90 muy malo)",
    "wifi_noise": "El nivel de ruido del último wifi_read que dio 0, en dBm",
    "usb_hid_read": "Lee los dispositivos USB (cada interfaz) que lleva la hid.class de Poseidon: cuántos; -1 sin "
                    "poseidon.library 4",
    "usb_hid_name": "El nombre del producto del dispositivo USB i (de 0 a usb_hid_read() - 1) del último usb_hid_read",
    "usb_hid_maker": "El fabricante del dispositivo USB i",
    "usb_hid_vendor": "El VendorID del dispositivo USB i",
    "usb_hid_product": "El ProductID del dispositivo USB i",
    "usb_hid_kind": "Qué es el dispositivo USB i: 1 ratón, 2 teclado, 0 otra cosa (muchos trackpads)",
    "usb_hid_emitter": "El emisor del dispositivo USB i: el número de la tarea de hid.class que envía sus movimientos, "
                       "para mouse_curve",
    "mouse_curve": "La curva de aceleración de un ratón: el emisor 0 es el ratón del Amiga (y todo movimiento que no "
                   "venga de un ratón USB); si no, uno de usb_hid_emitter. factors: una lista de centésimas (100 = tal "
                   "cual), la entrada i para un movimiento de i unidades, la última desde ahí (hasta 32); [] la quita. "
                   "Las fracciones que sobran se guardan. False si input.device no se abre o ya hay 16 emisores",
    "mouse_curve_events": "Cuántos movimientos ha escalado la curva de un emisor",
    "mouse_curves_off": "Quita ya las curvas de input.device (al acabar el programa también); un mouse_curve las vuelve "
                        "a poner. Bajo el parche de otro programa queda un puente que lo deja pasar todo",
    "mouse_patch_left": "Cuántos puentes quedaron bajo el parche de otro programa en input.device (lo dejan pasar todo, "
                        "para siempre)",
    "mouse_prefs_ticks": "La velocidad del ratón del sistema (preferencias de Input): 1 la más rápida, 2, 4 la más lenta",
    "mouse_prefs_accel": "True si está puesta la aceleración del ratón del sistema (preferencias de Input)",
    "mouse_prefs_set": "Pone la velocidad y la aceleración del ratón del sistema; vuelven a ser como eran al acabar el "
                       "programa",
    "tr": "El texto número id del catálogo del programa (@catalog) en el idioma del usuario; text (el del propio "
          "programa) sin catálogo, sin ese número o sin locale.library",
    "catalog_open": "Abre otro catálogo (\"X.catalog\", versión 0: cualquiera) en los idiomas del usuario en vez del que "
                    "se usa; false si no hay (tr da los textos del propio programa)",
    "catalog_language": "El idioma del catálogo que se usa (\"english\"); \"\" si no hay",
    "clock_read": "Toma la fecha y la hora del reloj del sistema: clock_year, clock_month... dan sus partes",
    "clock_year": "El año del último clock_read (1978...)",
    "clock_month": "El mes del último clock_read (1 a 12)",
    "clock_day": "El día del mes del último clock_read (1 a 31)",
    "clock_weekday": "El día de la semana del último clock_read: 0 domingo, 1 lunes ... 6 sábado",
    "clock_hour": "La hora del último clock_read (0 a 23)",
    "clock_minute": "El minuto del último clock_read",
    "clock_second": "El segundo del último clock_read",
    "date_text": "La fecha y la hora de ahora como dice format, con el FormatDate de locale.library en el idioma y el "
                 "país del usuario: %A día, %d-%m-%Y, %b mes, %H:%M:%S... (en inglés sin locale.library)",
    "locale_decimal_point": "Lo que va antes de los decimales en el país del usuario: \",\" en España, \".\" en inglés "
                            "(también sin locale.library)",
    "locale_group_separator": "Lo que separa los miles en el país del usuario: \".\" en España (1.234,5), \",\" en "
                              "inglés (1,234.5); puede ser \"\"",
    "locale_date_order": "El orden de día, mes y año en la fecha corta del usuario: \"DMY\", \"MDY\" o \"YMD\"",
    "program_version": "El nombre y la versión del programa de @version (\"Trasfondo 0.7\"); \"\" sin ella",
    "file_notify": "Vigila un fichero (puede no existir aún): su número (1 a 8), 0 si no se puede vigilar. cx_wait da 7 "
                   "cuando cambia; file_changed(n) dice si cambió",
    "file_changed": "True si el fichero vigilado con ese número cambió desde el último file_changed",
    "file_notify_end": "Deja de vigilar ese fichero (al acabar el programa se dejan todos)",
    "file_notify_signal": "La señal de los ficheros vigilados, para mui_wait_event_signals (0 antes de un file_notify)",
    "run_program": "Empieza una orden (\"SYS:Prefs/Font\", \"\\\"Work:Mi Prog\\\" arg\") en otro proceso sin esperar, "
                   "con su entrada y su salida en NIL:; false si no pudo empezar",
    "program_relaunch": "Al acabar el programa, lo vuelve a empezar (después de todo lo de su final, también el puerto "
                        "de single_instance) como empezó: desde el Workbench (3.5+: con su icono) o desde un Shell con "
                        "sus argumentos. Para actualizarse",
    "dos_requesters": "false: sin requesters de \"Inserta el volumen\" ni de errores de disco para este programa (la "
                      "llamada falla en su lugar); true: como antes. Al acabar el programa vuelven",
    "base64_to_file": "Escribe en un fichero los bytes de un texto en base64 (sin mirar espacios ni saltos de línea, "
                      "con relleno = o sin él): los bytes escritos, o -1 si el texto no es base64 (y entonces no hay "
                      "fichero) o no se puede escribir",
    "cpu_start": "Empieza a contar la CPU de cada tarea (los ganchos de cambio de tarea de exec; una tarea con ganchos "
                 "de otro programa no se cuenta): false sin EClock o antes del OS 2.04",
    "cpu_sample": "Toma una muestra: el número de tareas, con la CPU que gastó cada una desde la muestra anterior (o "
                  "cpu_start), de más a menos; también engancha las tareas empezadas desde entonces",
    "cpu_task_name": "El nombre de la tarea i de la última muestra, desde 0 (de un proceso de Shell, su orden)",
    "cpu_task_load": "La CPU de la tarea i de la última muestra, en tanto por mil",
    "cpu_total": "La CPU de todas las tareas contadas en la última muestra, en tanto por mil (lo demás es reposo)",
    "cpu_stop": "Quita los ganchos de las tareas (al acabar el programa también)",
    "task_signal": "La máscara de señal que cada tarea envía al programa cuando acaba su función (para "
                   "mui_wait_event_signals); 0 si no queda ninguna libre",
    "task_result": "Lo que devolvió la función (la espera si no ha acabado)",
    "task_free": "Olvida la tarea (la espera si sigue en marcha); al acabar, el programa espera a las que queden",
    # Intuition
    "window_create": "Abre una ventana; da su número 1..16 (0: no se pudo); flags: 1 se puede cambiar de tamaño, 2 sin "
                     "bordes, 4 sin botón de cerrar, 8 w y h son el interior (sin los bordes). Pasa a ser la ventana "
                     "actual",
    "window_border_top": "El borde de arriba de la ventana actual (con la barra de título); los gadgets cuentan desde "
                         "dentro, sin él",
    "window_border_bottom": "El borde de abajo de la ventana actual",
    "window_border_left": "El borde izquierdo de la ventana actual",
    "window_border_right": "El borde derecho de la ventana actual",
    "screen_font_height": "El alto de la fuente de la pantalla (la del programa, o la del Workbench): la de las barras "
                          "de título y la de los gadgets de GadTools",
    "screen_font_text_width": "El ancho de un texto con la fuente de la pantalla",
    "window_close": "Cierra una ventana (número 0: la actual)",
    "window_title": "Cambia el título de una ventana (número 0: la actual)",
    "window_move": "Lleva una ventana a x, y (absolutas; número 0: la actual)",
    "window_resize": "Cambia el tamaño de una ventana a w x h (número 0: la actual)",
    "window_to_front": "Pone una ventana delante (número 0: la actual)",
    "window_to_back": "Pone una ventana detrás (número 0: la actual)",
    "window_activate": "Activa una ventana (número 0: la actual)",
    "screen_to_front": "Pone delante la pantalla propia",
    "screen_to_back": "Pone detrás la pantalla propia",
    "gadget_id": "El número del último gadget usado (para el On Gadget del EventLoop)",
    "gadget_width": "El ancho de un gadget en píxeles (también si se creó con ancho 0)",
    "gadget_height": "El alto de un gadget en píxeles (también si se creó con alto 0)",
    "button_create": "Crea un botón",
    "button_enable": "Activa un botón",
    "button_disable": "Desactiva un botón",
    "textfield_create": "Crea un campo de texto",
    "textfield_get": "El texto de un campo de texto",
    "textfield_set": "Cambia el texto de un campo de texto",
    "checkbox_create": "Crea una casilla",
    "checkbox_get": "Si la casilla está marcada",
    "checkbox_set": "Marca o desmarca una casilla",
    "slider_create": "Crea un deslizador",
    "slider_get": "El valor de un deslizador",
    "slider_set": "Cambia el valor de un deslizador",
    "listview_create": "Crea una lista",
    "listview_add": "Añade una línea a una lista",
    "listview_clear": "Vacía una lista",
    "listview_selected": "La línea elegida (-1 si ninguna)",
    "cycle_create": "Crea un gadget de opciones que cambian al pulsarlo; opciones separadas por | (el valor es la "
                    "opción, desde 0)",
    "cycle_get": "La opción elegida de un gadget de opciones",
    "cycle_set": "Elige una opción de un gadget de opciones",
    "radio_create": "Crea botones de radio (uno por opción, separadas por |)",
    "radio_get": "El botón de radio elegido",
    "radio_set": "Elige un botón de radio",
    "integer_create": "Crea un campo de números enteros",
    "integer_get": "El valor de un campo de números",
    "integer_set": "Cambia el valor de un campo de números",
    "palette_create": "Crea un gadget de paleta de colores (2^depth colores)",
    "palette_get": "El color elegido",
    "palette_set": "Elige un color",
    "number_create": "Crea una caja que enseña un número",
    "number_set": "Cambia el número que se enseña",
    "dialog_file": "Diálogo de ficheros: la ruta entera del fichero elegido, \"\" si se canceló (save_mode true: "
                   "diálogo de guardar)",
    "dialog_file_at": "dialog_file abriéndose en ese cajón con ese nombre de fichero (\"\": como dialog_file)",
    "dialog_color": "Ventana con la paleta: da el color elegido (con un clic, o con las flechas + Return); Esc deja el "
                    "inicial",
    "dialog_screen_mode": "Petición de modo de pantalla (modo, ancho, alto y profundidad), empezando en el del Workbench: cierto si se eligió uno; screen_mode_id, _width, _height y _depth lo dan",
    "screen_mode_id": "El modo del último dialog_screen_mode (para screen_open_mode)",
    "screen_mode_width": "El ancho elegido en el último dialog_screen_mode",
    "screen_mode_height": "El alto elegido en el último dialog_screen_mode",
    "screen_mode_depth": "La profundidad (planos) elegida en el último dialog_screen_mode",
    "dialog_font": "Diálogo de fuentes: \"nombre.font/tamaño\", \"\" si se canceló",
    # RTG
    "rtg_available": "Mira si hay CyberGraphX o Picasso96",
    "rtg_is_active": "Mira si la pantalla actual es RTG",
    "rtg_get_depth": "La profundidad en bits de la pantalla actual (la del programa, o si no la del Workbench: también "
                     "fuera del dibujo de un desktop_canvas)",
    "rtg_get_width": "El ancho de la pantalla actual (la del programa, o si no la del Workbench: también fuera del "
                     "dibujo de un desktop_canvas)",
    "rtg_get_height": "El alto de la pantalla actual (la del programa, o si no la del Workbench: también fuera del "
                      "dibujo de un desktop_canvas)",
    "rtg_alloc_bitmap": "Pide un bitmap que vale para RTG",
    "rtg_free_bitmap": "Libera un bitmap RTG",
    "rtg_write_pixel": "Escribe un píxel con un color RGB de 24 bits",
    "rtg_read_pixel": "Lee un píxel: su color RGB de 24 bits",
    "rtg_fill_rect": "Rellena un rectángulo con un color RGB de 24 bits",
    "rtg_write_array": "Escribe un bloque de píxeles (el búfer es ARGB de 32 bits; bpr, los bytes por fila)",
    "rtg_read_array": "Lee un bloque de píxeles de la pantalla a un búfer",
    "rtg_rgb": "Un color RGB de 24 bits a partir de sus componentes",
    "rtg_argb": "Un color ARGB de 32 bits a partir de sus componentes",
    "rtg_rgb_r": "El componente rojo de un color RGB",
    "rtg_rgb_g": "El componente verde de un color RGB",
    "rtg_rgb_b": "El componente azul de un color RGB",
    "rtg_best_mode": "El mejor modo de pantalla RTG para ese tamaño",
    "rtg_open_screen": "Abre una pantalla RTG del tamaño que se diga",
    "rtg_blit": "Copia de un bitmap a la pantalla",
    "rtg_scale_blit": "Copia de un bitmap a la pantalla cambiando el tamaño",
    # ReAction
    "ra_window_create": "Crea una ventana ReAction con un layout; pasa a ser la actual. Su número (1-4), 0 si no se "
                        "pudo",
    "ra_window_use": "La ventana con la que trabajan las siguientes llamadas ra_* (el número que dio "
                     "ra_window_create; hasta 4 ventanas)",
    "ra_event_window": "La ventana del último evento (su número de ra_window_create)",
    "ra_window_open": "Abre la ventana ReAction",
    "ra_window_close": "Cierra la ventana ReAction actual y libera sus gadgets (otra abierta pasa a ser la actual)",
    "ra_window_sigmask": "La máscara de señal de la ventana, para Wait()",
    "ra_handle_events": "Atiende los eventos de la ventana (sin esperar): el número del gadget, o -1 si se cerró",
    "ra_wait_event": "Espera y atiende los eventos de la ventana: el número del gadget, o -1 si se cerró",
    "ra_add_button": "Añade un botón al layout",
    "ra_add_string": "Añade un campo de texto",
    "ra_add_checkbox": "Añade una casilla",
    "ra_add_slider": "Añade un deslizador horizontal",
    "ra_add_integer": "Añade un campo de números",
    "ra_add_label": "Añade una etiqueta de texto",
    "ra_get_value": "El valor de un gadget (casilla 1/0, deslizador, número, paleta, selector, barra de desplazamiento)",
    "ra_get_string": "El texto de un campo de texto",
    "ra_set_value": "Cambia el valor de un gadget (los mismos que ra_get_value)",
    "ra_refresh_layout": "Rehace el layout de la ventana después de añadir gadgets",
    "RA_EVENT_CLOSE": "El código del evento de cerrar la ventana (-1)",
    "RA_EVENT_NONE": "El código de ningún evento (-3)",
    "ra_get_rastport": "El RastPort para dibujar a mano (también pone _dash_rp)",
    "ra_get_inner_left": "El borde izquierdo interior de la ventana",
    "ra_get_inner_top": "El borde de arriba interior de la ventana",
    "ra_get_inner_width": "El ancho interior de la ventana",
    "ra_get_inner_height": "El alto interior de la ventana",
    "ra_add_palette": "Añade un gadget de paleta de colores",
    "ra_get_palette_color": "El color elegido en la paleta",
    "ra_set_palette_color": "Elige un color de la paleta",
    "ra_add_chooser": "Añade una lista desplegable (chooser)",
    "ra_chooser_add_item": "Añade una opción a la lista desplegable",
    "ra_get_chooser_selected": "La opción elegida de la lista desplegable",
    "ra_set_chooser_selected": "Elige una opción de la lista desplegable",
    "ra_add_scroller": "Añade una barra de desplazamiento horizontal",
    "ra_add_scroller_vert": "Añade una barra de desplazamiento vertical",
    "ra_get_scroller": "La posición de una barra de desplazamiento",
    "ra_set_scroller": "Cambia la posición de una barra de desplazamiento",
    "ra_enable_gadget": "Activa un gadget",
    "ra_disable_gadget": "Desactiva un gadget",
    "ra_set_string": "Cambia el texto de un campo de texto",
    "ra_set_text": "Cambia el texto de un botón o una etiqueta",
    "ra_layout_hgroup_begin": "Empieza un grupo horizontal del layout",
    "ra_layout_vgroup_begin": "Empieza un grupo vertical del layout",
    "ra_layout_group_end": "Acaba un grupo del layout",
    "ra_add_space": "Añade un separador horizontal",
    "ra_add_vspace": "Añade un separador vertical",
    "ra_layout_hgroup_weighted": "Empieza un grupo horizontal con un peso (lo que ocupa respecto a los demás)",
    "ra_layout_vgroup_weighted": "Empieza un grupo vertical con un peso",
    "ra_layout_group_end_weighted": "Acaba un grupo con peso",
    "ra_add_drawing_area": "Añade un gadget Space para dibujar a mano",
    "ra_get_drawing_bounds": "Mira dónde está el gadget Space (después de abrir la ventana)",
    "ra_drawing_left": "La izquierda de la zona de dibujo",
    "ra_drawing_top": "La parte de arriba de la zona de dibujo",
    "ra_drawing_width": "El ancho de la zona de dibujo",
    "ra_drawing_height": "El alto de la zona de dibujo",
    "ra_calc_drawing_area": "Calcula la zona de dibujo con las medidas de la ventana (si no hay otra forma)",
    "ra_refresh_canvas": "Pide que se redibuje el lienzo del gadget Space (llama a su función de dibujo)",
    "ra_canvas_left": "La izquierda del lienzo, desde su función de dibujo",
    "ra_canvas_top": "La parte de arriba del lienzo, desde su función de dibujo",
    "ra_canvas_width": "El ancho del lienzo, desde su función de dibujo",
    "ra_canvas_height": "El alto del lienzo, desde su función de dibujo",
    "ra_init_canvas_render": "Pone render_canvas() como la función de dibujo del lienzo",
    "ra_canvas_enable": "Activa el dibujo del lienzo (cuando todo esté preparado)",
    "ra_gadget_exists": "Mira si existe un gadget",
    "ra_window_width": "El ancho de la ventana",
    "ra_window_height": "El alto de la ventana",
    "ra_window_is_open": "Mira si la ventana está abierta",
    "ra_add_listbrowser": "Añade una lista de líneas de texto (valor: la línea elegida, -1 ninguna)",
    "ra_listbrowser_add": "Añade una línea al final de una lista",
    "ra_listbrowser_clear": "Quita todas las líneas de una lista",
    "ra_listbrowser_count": "Cuántas líneas tiene una lista",
    "ra_add_radio": "Añade botones de radio, opciones separadas por | (valor: la opción)",
    "ra_add_clicktab": "Añade pestañas, títulos separados por | (valor: la pestaña, desde 0)",
    "ra_add_fuelgauge": "Añade una barra de progreso de 0 a max (valor: el nivel)",
    "ra_menu_title": "Añade un menú a la ventana ReAction (antes de ra_window_open)",
    "ra_menu_item": "Añade una opción de menú: key = la letra de Amiga+tecla (\"\" ninguna); eventos: RA_EVENT_MENU() y "
                    "ra_menu_id()",
    "ra_menu_separator": "Añade una raya de separación al menú",
    "ra_menu_id": "El número de la opción de menú del último RA_EVENT_MENU()",
    "RA_EVENT_MENU": "Evento: se eligió una opción de menú (ra_menu_id)",
    "ra_add_getfile": "Añade un botón que abre un diálogo de ficheros; ra_get_string(id) da el fichero elegido",
    # MUI
    "mui_text_editor": "Un campo de texto de varias líneas (el Textinput de MUI), de ese número de líneas de alto, con su "
                       "barra: Return empieza otra línea; mui_get_text y mui_set_text lo leen y lo cambian, mui_on_ack da el "
                       "evento de mandarlo (Amiga+Return en su ventana)",
    "mui_window_open_back": "Abre una ventana sin hacerla la activa: el teclado se queda donde estaba; falso si no pudo "
                            "abrirse",
    "mui_window_activate": "Hace activa una ventana, delante de las demás (si está cerrada, la abre)",
    "mui_window_dispose": "Cierra una ventana, la quita de la aplicación y la libera con todos sus objetos (y los menús "
                          "contextuales hechos tras ella): para ventanas que se hacen una y otra vez (una vista previa). "
                          "Nada con 0 o con una ventana que ya no está; sus objetos no se pueden usar después",
    "mui_request": "Pregunta con la petición de MUI sobre una ventana (0: sobre la aplicación), con sus botones separados "
                   "por \"|\" (\"_Guardar|_Descartar|_Cancelar\"); las ventanas de la aplicación esperan. El botón elegido: "
                   "1, 2... desde la izquierda, 0 el último (también Esc)",
    "mui_set_background": "Un fondo RGB (0-255 cada uno) para un objeto: un grupo, un texto, una etiqueta, un botón, una "
                          "lista (y la lista de dentro) o una ventana (su grupo raíz); los objetos de dentro lo toman si "
                          "no tienen el suyo",
    "mui_set_text_pen": "El color (RGB, 0-255 cada uno) del texto de un texto, una etiqueta o un botón; mui_set_text lo "
                        "mantiene",
    "mui_app_field_colors": "El fondo (RGB, 0-255 cada uno) de todos los campos de texto de la aplicación (string, "
                            "text_editor, combo), sin el cursor y con él, y el color del cursor; lo toman las ventanas "
                            "que se abran después. El texto sigue negro: un gris en el que aún se lea, como 96, 96, "
                            "104 y 120, 120, 128",
    "mui_app_rexx": "Cada orden ARexx al puerto de la aplicación (su base y \".1\": \"BASE.1\") que MUI no contesta "
                    "por sí mismo (QUIT, SHOW, HIDE, INFO...) llama a f(orden: String) -> String con la línea entera: "
                    "lo que devuelve es el RESULT, y mui_rexx_fail durante la llamada pone el RC. Se ejecuta mientras "
                    "mui_wait_event espera",
    "mui_rexx_fail": "Desde la función de mui_app_rexx: el RC de la orden (5 aviso, 10 error, 20 fallo; entonces sin "
                     "RESULT)",
    "mui_app_begin": "Abre muimaster.library y crea la aplicación MUI (base: el nombre ARexx); 0 si no hay MUI o la CPU "
                     "es un 68000",
    "mui_app_end": "Deshace la aplicación con sus ventanas y objetos, y cierra MUI (también al acabar)",
    "mui_window_begin": "Empieza una ventana (id 1-255: MUI recuerda su tamaño y su sitio; 0 ninguno) con un grupo raíz "
                        "vertical",
    "mui_window_end": "Acaba la ventana empezada con mui_window_begin",
    "mui_window_open": "Abre una ventana; false si no se pudo",
    "mui_window_close": "Cierra una ventana (sigue existiendo)",
    "mui_window_active": "1 si la ventana es la activa (varias ventanas de un .dashui comparten números de evento; "
                         "dashweb D32)",
    "mui_vgroup_begin": "Empieza un grupo vertical dentro del grupo abierto",
    "mui_hgroup_begin": "Empieza un grupo horizontal dentro del grupo abierto",
    "mui_group_end": "Acaba el grupo abierto",
    "mui_text": "Un texto (con los códigos de texto de MUI)",
    "mui_button": "Un botón (un guion bajo delante de una letra la hace su atajo de teclado)",
    "mui_on_press": "mui_wait_event da id cuando se pulsa el botón",
    "mui_on_close": "mui_wait_event da id cuando se pulsa el botón de cerrar de la ventana (en la primera ventana, por "
                    "defecto: -1)",
    "mui_press": "Envía el evento mui_on_press de un botón como si se hubiera pulsado",
    "mui_label": "La etiqueta de una fila de un formulario (alineada a la derecha)",
    "mui_string": "Un campo de texto de hasta maxlen caracteres",
    "mui_checkbox": "Una casilla",
    "mui_cycle": "Un gadget de opciones que cambian al pulsarlo; opciones separadas por | (\"Uno|Dos|Tres\")",
    "mui_slider": "Un deslizador horizontal",
    "mui_gauge": "Una barra de progreso de 0 a max",
    "mui_get_value": "El valor: casilla 1/0, opción elegida, nivel del deslizador, progreso, marca de menú 1/0",
    "mui_set_value": "Cambia el valor (dispara mui_on_change como lo haría el usuario)",
    "mui_get_text": "El texto de un campo de texto, un texto, un botón o el título de una ventana",
    "mui_set_text": "Cambia el texto de un campo de texto, un texto, un botón, una opción de menú o el título de una "
                    "ventana",
    "mui_set_enabled": "Activa o desactiva (en gris) un objeto, una opción de menú o un menú entero",
    "mui_on_change": "mui_wait_event da id cuando cambia el valor o el texto",
    "mui_on_ack": "mui_wait_event da id cuando se pulsa Return en un campo de texto (en un mui_combo, también al elegir "
                  "una línea)",
    "mui_list": "Una lista de textos con barra de desplazamiento; su valor es la línea elegida (-1 ninguna)",
    "mui_list_add": "Añade una línea al final",
    "mui_list_insert": "Mete una línea en pos (0 = la primera)",
    "mui_list_remove": "Quita la línea de pos",
    "mui_list_clear": "Quita todas las líneas",
    "mui_list_count": "Cuántas líneas hay",
    "mui_list_get": "El texto de la línea de pos (\"\" fuera de la lista)",
    "mui_list_quiet": "Mientras está callada, la lista no se redibuja (para añadir muchas líneas)",
    "mui_on_double": "mui_wait_event da id con un doble clic en la lista",
    "mui_frame_begin": "Empieza un grupo con marco y un título (\"\" = ninguno)",
    "mui_columns_begin": "Empieza un grupo en rejilla con tantas columnas (formularios: etiqueta, campo...)",
    "mui_register_begin": "Empieza unas pestañas (\"Una|Dos\"); cada hijo es una página; valor = la página que se ve",
    "mui_scroll_begin": "Empieza una zona con barras de desplazamiento (contenido más grande que la ventana)",
    "mui_space": "Un espacio vacío que ocupa lo que sobra",
    "mui_balance": "Una barra que el usuario arrastra para repartir el sitio entre sus vecinos",
    "mui_weight": "La parte del espacio libre que se lleva un objeto (100 por defecto)",
    "mui_set_visible": "Enseña u oculta un objeto (la ventana se recoloca)",
    "mui_menu_begin": "Empieza un menú de la ventana que se está haciendo",
    "mui_menu_item": "Una opción de menú: key = la letra de Amiga+tecla (\"\" ninguna); mui_wait_event da id",
    "mui_menu_check": "Una opción de menú con marca: elegirla cambia la marca y mui_wait_event da id; mui_get_value / "
                      "mui_set_value leen y ponen la marca",
    "mui_submenu_begin": "Empieza un submenú en el menú que se está haciendo (un nivel): sus opciones van dentro hasta "
                         "mui_submenu_end",
    "mui_submenu_end": "Acaba el submenú",
    "mui_menu_separator": "Una raya de separación en el menú",
    "mui_context_menu_begin": "Empieza un menú contextual (en cualquier sitio, no solo en una ventana): sus opciones como "
                              "en un menú (mui_menu_item, mui_menu_check, mui_submenu_begin...) hasta mui_menu_end; se da "
                              "a un objeto con mui_set_context_menu (Lorraine D15)",
    "mui_set_context_menu": "El botón derecho sobre el objeto abre ese menú contextual (0: ninguno); sus opciones dan "
                            "sus eventos; en un lienzo, mui_canvas_mouse_x/_y dicen dónde se pulsó y mui_canvas_button "
                            "es 2",
    "mui_menu_end": "Acaba el menú",
    "mui_canvas": "Una zona de dibujo (crece con la ventana); se dibuja desde mui_canvas_on_draw",
    "mui_canvas_on_draw": "La función f(x, y, ancho, alto) que dibuja la zona con gfx_ (MUI la llama cuando hace falta)",
    "mui_canvas_on_input": "mui_wait_event da id con un clic, la rueda o una tecla sobre la zona (llamarla antes de "
                           "abrir la ventana)",
    "mui_canvas_redraw": "Dibuja otra vez la zona ya",
    "mui_canvas_buffered": "Dibuja la zona en un bitmap propio y la enseña de golpe al acabar (sin zona a medio dibujar; "
                           "las mismas coordenadas; mui_canvas_update sigue dibujando en la ventana)",
    "mui_canvas_update": "Llama ya a la función de dibujo sin borrar la zona (pinta solo lo que cambió)",
    "mui_canvas_update_area": "Como mui_canvas_update, solo en la parte w x h en x, y de la zona (desde su esquina): el "
                              "dibujo se recorta a ella y, con mui_canvas_buffered, solo ella pasa del búfer a la ventana",
    "mui_canvas_updating": "En la función de dibujo: true si corre por un mui_canvas_update (lo demás sigue ahí)",
    "mui_canvas_on_move": "mui_wait_event da id cuando el puntero se mueve sobre la zona o sale de ella, sin clic (los "
                          "movimientos que lleguen entretanto hacen uno; llamarla antes de abrir la ventana)",
    "mui_canvas_pointer_x": "La X del puntero ahora, desde el borde izquierdo de la zona (con clic o sin él)",
    "mui_canvas_pointer_y": "La Y del puntero ahora, desde el borde de arriba de la zona (con clic o sin él)",
    "mui_canvas_pointer_inside": "True si el puntero está ahora sobre la zona",
    "mui_canvas_set_pointer": "La forma del puntero sobre la zona: 0 normal, 1 texto (I), 2 cambiar de tamaño a los "
                              "lados, 3 arriba y abajo, 4 ocupado; cambia ya si el puntero está sobre la zona (o "
                              "arrastrándola) y vuelve a la normal fuera de ella (Lorraine D16)",
    "mui_canvas_take_tab": "Con el puntero sobre la zona, Tab y Mayúsculas+Tab son teclas para ella (mui_canvas_key 66, "
                           "Mayúsculas en mui_canvas_qualifiers; necesita mui_canvas_on_input) y no el gadget siguiente "
                           "y anterior de la ventana; fuera de ella pasan de gadget en gadget como siempre (Lorraine D48)",
    "mui_canvas_mouse_x": "La X del último clic o de la rueda, desde el borde izquierdo de la zona",
    "mui_canvas_mouse_y": "La Y del último clic o de la rueda, desde el borde de arriba de la zona",
    "mui_canvas_button": "1 si lo último fue un clic izquierdo; si no, 0",
    "mui_canvas_wheel": "+1 / -1 si lo último fue la rueda del ratón (arriba/abajo); si no, 0",
    "mui_canvas_key": "El código en bruto de la última tecla; -1 si lo último no fue una tecla",
    "mui_canvas_on_drag": "El id del evento cuando se arrastra la zona (moverse con el botón izquierdo pulsado tras "
                          "pulsarlo en ella) y cuando se suelta; mui_canvas_drag dice cuál, mui_canvas_mouse_x/y dónde "
                          "(puede ser fuera de la zona). Llamarla antes de abrir la ventana",
    "mui_canvas_drag": "El último evento de arrastre: 1 moviéndose con el botón pulsado, 2 soltado (0 antes de ninguno)",
    "mui_canvas_qualifiers": "Las teclas pulsadas en la última tecla, clic o rueda: 1 Mayúsculas, 2 Ctrl, 4 Alt, 8 "
                             "Amiga, sumadas (Mayúsculas + Ctrl = 3); q & 1 dice si había Mayúsculas",
    "mui_canvas_char": "El carácter de la última tecla en la zona, con las mayúsculas y el mapa de teclado (\"\" si no "
                       "hay; dashweb D31)",
    "mui_scrollbar": "Una barra de desplazamiento; su valor es la primera línea que se ve",
    "mui_set_range": "El tamaño del documento y de la parte que cabe",
    "mui_wait_event_signals": "Como mui_wait_event, pero también da 0 cuando llega una de las señales de mask "
                              "(sockets...); mui_signals dice cuál",
    "mui_signals": "Las señales de la máscara que despertaron al último mui_wait_event_signals",
    "mui_timer": "Dentro de ms milisegundos mui_wait_event da id, una vez (otra: llamarla otra vez; 0 la cancela)",
    "mui_image": "Una imagen de un fichero con los datatypes (ILBM; PNG, JPEG, GIF si están sus datatypes); "
                 "mui_set_text cambia el fichero",
    "mui_image_button": "Un botón con una imagen (un icono de barra de herramientas; ILBM, o lo que lean los datatypes): "
                        "mui_on_press como un botón, mui_set_text cambia la imagen",
    "mui_image_toggle": "Un botón con imagen que se queda pulsado (negrita, cursiva): valor 1/0 con mui_get_value / "
                        "mui_set_value, mui_on_change cuando cambia; group > 0: pulsar uno suelta los demás de ese grupo "
                        "(alineación), y mui_on_change solo salta en el pulsado",
    "mui_combo": "Un campo de texto con una lista que se despliega (fuente, tamaño; opciones \"A|B\"): se escribe o se "
                 "elige una línea (doble clic); mui_get_text / mui_set_text, mui_list_* cambian las líneas, mui_on_ack "
                 "con Return o al elegir una línea",
    "mui_help": "Una ayuda en burbuja que sale cuando el puntero se para sobre el objeto",
    "mui_window_move": "Mueve una ventana abierta dx, dy píxeles (las ventanas de un .dashui se abren en el mismo sitio)",
    "mui_set_active": "Hace de obj el objeto activo de la ventana: el cursor va a ese campo de texto (Amiga-L)",
    "mui_window_size": "El tamaño de la ventana al abrirse, en tanto por ciento de la pantalla visible, centrada (antes "
                       "de mui_window_open)",
    "mui_window_fullscreen": "La ventana ocupa toda la pantalla: sin bordes, barra de título ni gadgets, y activa (antes "
                             "de mui_window_open)",
    "mui_window_screen": "La ventana se abre como una ventana normal en la pantalla pública con ese nombre (la de screen_clone_wb, o la de otro programa); antes de mui_window_open; falso si no existe esa pantalla",
    "mui_window_own_screen": "Pantalla completa en una pantalla propia, como la pública (antes de mui_window_open; false: "
                             "en la pública)",
    "mui_width": "El ancho de un objeto en la pantalla en píxeles (0 antes de abrirse su ventana)",
    "mui_height": "El alto de un objeto en la pantalla en píxeles (0 antes de abrirse su ventana)",
    "mui_wait_event": "Espera el siguiente evento y da su número; -1 para salir",
    "mui_poll_event": "Como mui_wait_event sin esperar: 0 si no hay evento",
}
