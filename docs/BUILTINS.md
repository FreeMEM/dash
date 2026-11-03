*[English](BUILTINS.en.md) | Castellano*

# Funciones built-in

> Generado por `tools/gen_builtins_doc.py` desde `compiler/amiga_builtins.py`. No editar a mano.

Las marcadas **sin implementar** están declaradas pero no tienen código C:
usarlas da el error `Builtin 'x' is declared but not implemented yet`.

Total: 882 funciones, 882 implementadas, 0 sin implementar.

## Gráficos básicos

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `gfx_pen(color)` | `void` | Pone el color (lápiz) de dibujo |  |
| `gfx_pen_bg(color)` | `void` | Pone el color de fondo |  |
| `gfx_pen_outline(color)` | `void` | Pone el color del borde de los rellenos |  |
| `gfx_mode(mode)` | `void` | Pone el modo de dibujo (JAM1, JAM2, COMPLEMENT, INVERSVID) |  |
| `gfx_pattern(pattern)` | `void` | Pone el patrón de las líneas (16 bits) |  |
| `gfx_rgb(index, r, g, b)` | `void` | Cambia un color de la paleta (componentes de 4 bits, 0-15) |  |
| `gfx_rgb8(index, r, g, b)` | `void` | Cambia un color de la paleta (componentes de 8 bits, AGA) |  |
| `gfx_move(x, y)` | `void` | Mueve el cursor de dibujo |  |
| `gfx_draw(x, y)` | `void` | Dibuja una línea del cursor al punto |  |
| `gfx_line(x1, y1, x2, y2)` | `void` | Dibuja una línea entre dos puntos |  |
| `gfx_pixel(x, y)` | `void` | Dibuja un píxel |  |
| `gfx_pixel_read(x, y)` | `LONG` | Lee el color de un píxel |  |
| `gfx_rect(x1, y1, x2, y2)` | `void` | Dibuja un rectángulo relleno |  |
| `gfx_box(x1, y1, x2, y2)` | `void` | Dibuja el contorno de un rectángulo |  |
| `gfx_ellipse(cx, cy, rx, ry)` | `void` | Dibuja el contorno de una elipse |  |
| `gfx_circle(cx, cy, r)` | `void` | Dibuja el contorno de un círculo |  |
| `gfx_ellipse_fill(cx, cy, rx, ry)` | `void` | Dibuja una elipse rellena |  |
| `gfx_circle_fill(cx, cy, r)` | `void` | Dibuja un círculo relleno |  |
| `gfx_flood(x, y, mode)` | `void` | Rellena un área (como un cubo de pintura) |  |
| `gfx_text(str)` | `void` | Escribe un texto en el cursor |  |
| `gfx_text_at(x, y, str)` | `void` | Escribe un texto en una posición |  |
| `gfx_text_len(str)` | `LONG` | El ancho de un texto en píxeles |  |
| `gfx_clear()` | `void` | Borra con el color 0 |  |
| `gfx_clear_color(color)` | `void` | Borra con un color |  |
| `gfx_scroll(dx, dy, x1, y1, x2, y2)` | `void` | Desplaza una zona |  |
| `gfx_poly_begin(x, y)` | `void` | Empieza un polígono en un punto |  |
| `gfx_poly_add(x, y)` | `void` | Añade un vértice al polígono |  |
| `gfx_poly_end()` | `void` | Cierra y rellena el polígono |  |
| `gfx_pens_draw(buffer, width, height, x, y, zoom)` | `void` | Dibuja una imagen de lápices (un byte por píxel, fila tras fila) en x, y, cada píxel de zoom x zoom: una imagen entera en una llamada (3.1: WriteChunkyPixels) |  |
| `gfx_copy(sx, sy, w, h, dx, dy)` | `void` | Copia una zona dentro de la ventana |  |

## Gráficos avanzados

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `sprite_load(id, filename)` | `BOOL` | Un sprite de una imagen (ILBM...): fotogramas de 16 píxeles uno al lado del otro, los colores 0-3 los suyos (el 0, transparente); FALSE si no se puede |  |
| `sprite_load_attached(id, filename)` | `BOOL` | Un sprite de 15 colores de una imagen: una pareja de sprites acoplados; los colores 1-15 de la imagen (0 transparente) son los 17-31 de la pantalla. Falso si no puede |  |
| `sprite_create(id, width, height)` | `BOOL` | Crea un sprite vacío |  |
| `sprite_pos(id, x, y)` | `void` | Pone la posición de un sprite |  |
| `sprite_show(id)` | `void` | Hace visible un sprite |  |
| `sprite_hide(id)` | `void` | Oculta un sprite |  |
| `sprite_color(id, index, r, g, b)` | `void` | Pone un color de un sprite, índice 0-2 (0-14 en una pareja acoplada; componentes de 0 a 15) |  |
| `sprite_load_colors(id, filename)` | `BOOL` | Los colores 1-3 (1-15 en una pareja acoplada) de la paleta (CMAP) de una imagen como los colores del sprite, con 8 bits; falso si el fichero no la tiene |  |
| `bob_load_colors(filename, first)` | `LONG` | Los colores de la paleta (CMAP) de una imagen en la paleta de la pantalla desde el color first: cuántos puso |  |
| `sprite_rgb8(id, index, r, g, b)` | `void` | Pone un color de un sprite, índice 0-2 (0-14 en una pareja acoplada), con componentes de 8 bits (0-255; exacto en AGA, 4 bits en ECS) |  |
| `sprite_frame(id, frame)` | `void` | Enseña el fotograma frame (0 el primero) de un sprite de sprite_load o sprite_load_attached |  |
| `sprite_free(id)` | `void` | Libera la memoria de un sprite |  |
| `sprite_collision(id1, id2)` | `BOOL` | Mira si chocan dos sprites |  |
| `sprite_set_row(id, row, plane0, plane1)` | `void` | Pone una fila de los datos de un sprite (2 planos de bits) |  |
| `soft_sprite_create(id, width, height, depth)` | `BOOL` | Crea un sprite por software (vale en RTG) |  |
| `soft_sprite_free(id)` | `void` | Libera un sprite por software |  |
| `soft_sprite_pixel(id, x, y, color)` | `void` | Pone un píxel de un sprite por software |  |
| `soft_sprite_clear(id, color)` | `void` | Borra un sprite por software con un color |  |
| `soft_sprite_row(id, row, plane0, plane1)` | `void` | Pone una fila del sprite (en el formato de los sprites de hardware) |  |
| `soft_sprite_show(id)` | `void` | Enseña un sprite por software |  |
| `soft_sprite_hide(id)` | `void` | Oculta un sprite por software |  |
| `soft_sprite_pos(id, x, y)` | `void` | Pone la posición de un sprite por software |  |
| `soft_sprite_x(id)` | `LONG` | La posición X de un sprite por software |  |
| `soft_sprite_y(id)` | `LONG` | La posición Y de un sprite por software |  |
| `bob_load(id, filename)` | `BOOL` | Carga un BOB de un fichero |  |
| `bob_create(id, width, height, depth)` | `BOOL` | Crea un BOB vacío |  |
| `bob_pos(id, x, y)` | `void` | Pone la posición de un BOB |  |
| `bob_draw(id)` | `void` | Dibuja un BOB |  |
| `bob_erase(id)` | `void` | Borra un BOB (deja el fondo como estaba) |  |
| `bob_frame(id, frame)` | `void` | Pone el fotograma de la animación de un BOB |  |
| `bob_frame_width(id, width)` | `void` | La imagen del BOB es una tira de fotogramas de ese ancho en píxeles (bob_load lo toma del trozo FRJA de Forja; si no, supone fotogramas cuadrados) |  |
| `bob_width(id)` | `LONG` | El ancho de un fotograma de un BOB (0 si no hay ese BOB) |  |
| `bob_height(id)` | `LONG` | El alto de un BOB |  |
| `bob_frames(id)` | `LONG` | Cuántos fotogramas tiene un BOB |  |
| `bob_paste(id, frame, x, y)` | `void` | Pinta un fotograma de un BOB en x, y con su máscara (el color 0, transparente), sin guardar lo que hay debajo: para juegos que pintan el fotograma entero cada vez (doble búfer) |  |
| `bob_free(id)` | `void` | Libera la memoria de un BOB |  |
| `tilemap_create(id, width, height, tile, layers)` | `BOOL` | Un mapa de tiles nuevo en id (el que hubiera se va): ancho x alto celdas (de 1 a 1024 cada lado), tiles cuadrados de 8, 16 o 32 píxeles y de 1 a 8 capas de celdas vacías |  |
| `tilemap_load(id, filename)` | `BOOL` | Carga en id un mapa de tiles (IFF FORM FMAP, el que guarda el editor de mapas de Forja); falso si no lo es |  |
| `tilemap_save(id, filename)` | `BOOL` | Guarda un mapa de tiles en IFF FORM FMAP; falso si no se puede |  |
| `tilemap_free(id)` | `void` | Libera un mapa de tiles |  |
| `tilemap_width(id)` | `LONG` | El ancho de un mapa de tiles en celdas (0 si no hay) |  |
| `tilemap_height(id)` | `LONG` | El alto de un mapa de tiles en celdas |  |
| `tilemap_tile_size(id)` | `LONG` | El lado de los tiles de un mapa en píxeles (8, 16 o 32) |  |
| `tilemap_layers(id)` | `LONG` | Cuántas capas tiene un mapa de tiles |  |
| `tilemap_get(id, layer, x, y)` | `LONG` | Una celda de una capa (0 la primera): el tile (1 el primer fotograma del tileset, 0 vacía) más 16384 si va en espejo de izquierda a derecha y 32768 si de arriba abajo; 0 fuera del mapa |  |
| `tilemap_set(id, layer, x, y, value)` | `void` | Pone una celda de una capa (como la da tilemap_get); nada fuera del mapa |  |
| `tilemap_tileset(id)` | `STRPTR` | El nombre del fichero del tileset del mapa, como va guardado en él ("" si no tiene) |  |
| `tilemap_set_tileset(id, filename)` | `void` | El nombre del fichero del tileset del mapa (un IFF del editor de sprites de Forja: un BOB con un fotograma por tile) |  |
| `tilemap_layer_name(id, layer)` | `STRPTR` | El nombre de una capa |  |
| `tilemap_layer_type(id, layer)` | `LONG` | El tipo de una capa (0 tiles; el editor usa otros para choques y objetos) |  |
| `tilemap_layer_visible(id, layer)` | `BOOL` | Si una capa se ve (para el editor) |  |
| `tilemap_layer_set(id, layer, name, type, visible)` | `void` | Nombre (hasta 31 caracteres), tipo y si se ve de una capa |  |
| `tilemap_layer_add(id)` | `LONG` | Una capa vacía nueva al final: su número, o -1 (como mucho hay 8) |  |
| `tilemap_layer_remove(id, layer)` | `BOOL` | Quita una capa (las de detrás bajan un puesto); falso si es la única |  |
| `tilemap_layer_move(id, from, to)` | `BOOL` | Mueve una capa a otro puesto (las de en medio se corren uno) |  |
| `tilemap_resize(id, width, height)` | `BOOL` | Tamaño nuevo en celdas: lo que cabe se queda, desde la esquina de arriba a la izquierda, y las celdas nuevas van vacías |  |
| `tilemap_draw(id, layer, bob, tx, ty, tw, th, x, y)` | `void` | Pinta tw x th celdas de una capa, desde la celda tx, ty, en x, y, con los fotogramas de un BOB (el tile n es el fotograma n - 1, en espejo si la celda lo dice; cada celda, del tamaño de un fotograma); las celdas vacías dejan ver lo de debajo. De una vez en la ventana |  |
| `tilemap_draw_masked(id, layer, bob, tx, ty, tw, th, x, y)` | `void` | Como tilemap_draw, pero el color 0 y las celdas vacías dejan ver lo de debajo (para las capas de delante) |  |
| `bob_collision(id1, id2)` | `BOOL` | Mira si chocan dos BOB |  |
| `copper_create(size)` | `BOOL` | Crea una lista del copper |  |
| `copper_wait(y, x)` | `void` | Añade una instrucción WAIT del copper |  |
| `copper_move(reg, value)` | `void` | Añade una instrucción MOVE del copper |  |
| `copper_color(index, rgb)` | `void` | Añade un cambio de color del copper |  |
| `copper_end()` | `void` | Termina la lista del copper |  |
| `copper_install()` | `void` | Pone en marcha la lista del copper |  |
| `copper_free()` | `void` | Libera la lista del copper |  |
| `bitmap_create(id, width, height, depth)` | `BOOL` | Crea un bitmap |  |
| `bitmap_load(id, filename)` | `BOOL` | Carga un bitmap IFF |  |
| `bitmap_save(id, filename)` | `BOOL` | Guarda un bitmap IFF |  |
| `bitmap_free(id)` | `void` | Libera un bitmap |  |
| `bitmap_blit(src_id, sx, sy, w, h, dx, dy)` | `void` | Copia de un bitmap a la pantalla |  |
| `bitmap_blit_mask(src_id, mask_id, sx, sy, w, h, dx, dy)` | `void` | Copia de un bitmap con máscara |  |
| `bitmap_draw_to(id)` | `void` | Dibuja en un bitmap desde ahora |  |
| `bitmap_draw_screen()` | `void` | Dibuja en la pantalla desde ahora |  |

## Entrada (teclado, ratón, joystick)

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `key_pressed()` | `BOOL` | Mira si hay una tecla pulsada esperando |  |
| `key_get()` | `LONG` | El código de la tecla |  |
| `key_wait()` | `LONG` | Espera una tecla y da su código |  |
| `key_raw()` | `LONG` | El código de tecla en bruto (sin traducir) |  |
| `key_down(code)` | `BOOL` | Si una tecla está pulsada ahora, por su código (0x45 Esc, 0x40 espacio, 0x4C arriba, 0x4D abajo, 0x4E derecha, 0x4F izquierda): para juegos, se pregunta en cada fotograma; no necesita ventana |  |
| `key_text(keycode)` | `STRPTR` | Pasa un código de tecla a texto |  |
| `mouse_x()` | `LONG` | La X del ratón dentro del interior de la ventana (0 sin ventana) |  |
| `mouse_y()` | `LONG` | La Y del ratón dentro del interior de la ventana (0 sin ventana) |  |
| `mouse_button(btn)` | `BOOL` | Mira un botón del ratón (0 izquierdo, 1 derecho) |  |
| `event_window()` | `LONG` | En un EventLoop: la ventana de la que vino el evento (window_create), 0 para la del propio bucle |  |
| `window_check_close()` | `BOOL` | Mira si se pulsó el botón de cerrar (sin esperar) |  |
| `close_window()` | `void` | Cierra la ventana actual |  |
| `screen_open_mode(mode, width, height, depth, title)` | `BOOL` | Abre una pantalla con un modo exacto (el de dialog_screen_mode, o uno conocido: 0x21000 es PAL de baja resolución y 0x29000 la de alta), tamaño y profundidad; falso si el modo no existe o no admite esa profundidad |  |
| `screen_clone_wb(name)` | `BOOL` | Abre una pantalla pública igual que la del Workbench (modo, tamaño, profundidad, lápices y fuente) con ese nombre, donde otros programas pueden abrir ventanas; falso si no se puede (o el nombre ya está). screen_close espera a que se cierren sus ventanas |  |
| `screen_visitors()` | `LONG` | Cuántos usos de la pantalla pública del programa hay: ventanas y bloqueos (LockPubScreen; una ventana de MUI puede contar dos); 0 si ninguno |  |
| `screen_make_default()` | `BOOL` | La pantalla pública del programa (screen_clone_wb) pasa a ser la pública por defecto: ahí se abren las ventanas que no dicen pantalla (los programas que lanza, las consolas); screen_close deja la de antes. Falso si no tiene pantalla pública |  |
| `screen_open(depth, title)` | `BOOL` | Abre una pantalla con el modo del Workbench y la profundidad que se diga |  |
| `screen_double_buffer()` | `BOOL` | Dos búferes para la pantalla propia del programa: se dibuja en el escondido y screen_flip lo enseña; falso sin pantalla propia (o si es pública) o antes de AmigaOS 3.0 |  |
| `screen_flip()` | `BOOL` | Enseña lo dibujado en el búfer escondido (screen_double_buffer) y pasa a dibujar en el otro; espera a la pantalla, un fotograma como mucho. Falso si ahora no pudo cambiarlo |  |
| `screen_open_custom(width, height, depth, title)` | `BOOL` | Abre una pantalla propia del tamaño y la profundidad que se digan |  |
| `screen_close()` | `void` | Cierra la pantalla |  |
| `screen_width()` | `LONG` | El ancho de la pantalla en píxeles |  |
| `screen_height()` | `LONG` | El alto de la pantalla en píxeles |  |
| `check_lmb()` | `BOOL` | Mira si está pulsado el botón izquierdo del ratón (hardware) |  |
| `check_rmb()` | `BOOL` | Mira si está pulsado el botón derecho del ratón (hardware) |  |
| `check_mouse()` | `BOOL` | Mira si está pulsado algún botón del ratón (hardware) |  |
| `check_esc()` | `BOOL` | Mira si está pulsada la tecla Esc (hardware) |  |
| `wait_click()` | `LONG` | Espera un clic del ratón (pulsar y soltar) |  |
| `wait_key()` | `LONG` | Espera una tecla y da su código |  |
| `joy_x(port)` | `LONG` | La dirección X del joystick (-1, 0, 1) |  |
| `joy_y(port)` | `LONG` | La dirección Y del joystick (-1, 0, 1) |  |
| `joy_button(port)` | `BOOL` | El estado del botón del joystick |  |
| `joy_up(port)` | `BOOL` | Joystick hacia arriba |  |
| `joy_down(port)` | `BOOL` | Joystick hacia abajo |  |
| `joy_left(port)` | `BOOL` | Joystick a la izquierda |  |
| `joy_right(port)` | `BOOL` | Joystick a la derecha |  |
| `joy_fire(port)` | `BOOL` | El botón de disparo del joystick |  |

## GadTools

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `gt_init()` | `BOOL` | Prepara GadTools (después de abrir la ventana) |  |
| `gt_cleanup()` | `void` | Libera lo de GadTools |  |
| `gt_attach()` | `void` | Pone los gadgets en la ventana (después de crearlos todos) |  |
| `gt_button(x, y, w, h, label)` | `LONG` | Crea un botón; da su número |  |
| `gt_checkbox(x, y, w, h, label, checked)` | `LONG` | Crea una casilla |  |
| `gt_string(x, y, w, h, label, initial, maxchars)` | `LONG` | Crea un campo de texto |  |
| `gt_integer(x, y, w, h, label, initial)` | `LONG` | Crea un campo de números |  |
| `gt_slider(x, y, w, h, label, min, max, level)` | `LONG` | Crea un deslizador |  |
| `gt_palette(x, y, w, h, label, depth, color)` | `LONG` | Crea un selector de color de la paleta |  |
| `gt_text(x, y, w, h, label, text)` | `LONG` | Crea un texto fijo |  |
| `gt_get_value(gad_id)` | `LONG` | El valor de un gadget (deslizador, paleta...) |  |
| `gt_set_value(gad_id, value)` | `void` | Cambia el valor de un gadget |  |
| `gt_get_string(gad_id)` | `STRPTR` | El texto de un campo de texto |  |
| `gt_event()` | `LONG` | Mira si hay un evento de gadget: su número, -1 (ninguno) o -2 (cerrar) |  |
| `gt_wait_event()` | `LONG` | Espera un evento de gadget: su número o -2 (cerrar) |  |
| `gt_cycle(x, y, w, h, label, options)` | `LONG` | Crea un gadget de opciones que cambian al pulsarlo; opciones separadas por \| (gt_get_value: la elegida) |  |
| `gt_enable(gad_id)` | `void` | Activa un gadget |  |
| `gt_disable(gad_id)` | `void` | Desactiva (en gris) un gadget |  |
| `gt_set_text(gad_id, text)` | `void` | Cambia el texto de un gt_text o un gt_string |  |

## Menús

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `menu_title(label)` | `void` | Añade el título de un menú |  |
| `menu_item(label, shortcut, id)` | `void` | Añade una opción de menú con su tecla y su número |  |
| `menu_sub(label, shortcut, id)` | `void` | Añade una opción de un submenú |  |
| `menu_separator()` | `void` | Añade una raya de separación al menú |  |
| `menu_attach()` | `BOOL` | Pone los menús en la ventana (después de definirlos todos) |  |
| `menu_event()` | `LONG` | Mira si hay un evento de menú: el número de la opción, o -1/-2 |  |
| `menu_id()` | `LONG` | En el On Menu de un EventLoop: el número de la opción elegida |  |
| `menu_check_item(label, shortcut, id)` | `void` | Añade una opción de menú con una marca que cambia cada vez que se elige |  |
| `menu_checked(id)` | `LONG` | 1 si está puesta la marca de esa opción |  |
| `menu_enable(id, enabled)` | `void` | Activa o desactiva (en gris) una opción de menú, después de menu_attach |  |

## Requesters ASL

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `file_open_dialog(title, pattern)` | `BOOL` | Enseña el diálogo de abrir fichero; true si se eligió uno |  |
| `file_save_dialog(title, pattern)` | `BOOL` | Enseña el diálogo de guardar fichero; true si se eligió uno |  |
| `file_get_path()` | `STRPTR` | El cajón elegido en el último diálogo |  |
| `file_get_name()` | `STRPTR` | El nombre de fichero elegido en el último diálogo |  |
| `file_fullpath()` | `STRPTR` | La ruta entera (cajón + fichero) del último diálogo |  |

## ReAction

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `ra_window_create(title, width, height)` | `LONG` | Crea una ventana ReAction con un layout; pasa a ser la actual. Su número (1-4), 0 si no se pudo |  |
| `ra_window_use(window)` | `void` | La ventana con la que trabajan las siguientes llamadas ra_* (el número que dio ra_window_create; hasta 4 ventanas) |  |
| `ra_event_window()` | `LONG` | La ventana del último evento (su número de ra_window_create) |  |
| `ra_window_open()` | `LONG` | Abre la ventana ReAction |  |
| `ra_window_close()` | `void` | Cierra la ventana ReAction actual y libera sus gadgets (otra abierta pasa a ser la actual) |  |
| `ra_window_sigmask()` | `ULONG` | La máscara de señal de la ventana, para Wait() |  |
| `ra_handle_events()` | `LONG` | Atiende los eventos de la ventana (sin esperar): el número del gadget, o -1 si se cerró |  |
| `ra_wait_event()` | `LONG` | Espera y atiende los eventos de la ventana: el número del gadget, o -1 si se cerró |  |
| `ra_add_button(id, label)` | `LONG` | Añade un botón al layout |  |
| `ra_add_string(id, initial, maxchars)` | `LONG` | Añade un campo de texto |  |
| `ra_add_checkbox(id, label, checked)` | `LONG` | Añade una casilla |  |
| `ra_add_slider(id, min, max, initial)` | `LONG` | Añade un deslizador horizontal |  |
| `ra_add_integer(id, initial, min, max)` | `LONG` | Añade un campo de números |  |
| `ra_add_label(text)` | `LONG` | Añade una etiqueta de texto |  |
| `ra_get_value(id)` | `LONG` | El valor de un gadget (casilla 1/0, deslizador, número, paleta, selector, barra de desplazamiento) |  |
| `ra_get_string(id)` | `STRPTR` | El texto de un campo de texto |  |
| `ra_set_value(id, value)` | `void` | Cambia el valor de un gadget (los mismos que ra_get_value) |  |
| `ra_refresh_layout()` | `void` | Rehace el layout de la ventana después de añadir gadgets |  |
| `RA_EVENT_CLOSE()` | `LONG` | El código del evento de cerrar la ventana (-1) |  |
| `RA_EVENT_NONE()` | `LONG` | El código de ningún evento (-3) |  |
| `ra_get_rastport()` | `APTR` | El RastPort para dibujar a mano (también pone _dash_rp) |  |
| `ra_get_inner_left()` | `LONG` | El borde izquierdo interior de la ventana |  |
| `ra_get_inner_top()` | `LONG` | El borde de arriba interior de la ventana |  |
| `ra_get_inner_width()` | `LONG` | El ancho interior de la ventana |  |
| `ra_get_inner_height()` | `LONG` | El alto interior de la ventana |  |
| `ra_add_palette(id, depth, initial_color)` | `LONG` | Añade un gadget de paleta de colores |  |
| `ra_get_palette_color(id)` | `LONG` | El color elegido en la paleta |  |
| `ra_set_palette_color(id, color)` | `void` | Elige un color de la paleta |  |
| `ra_add_chooser(id)` | `LONG` | Añade una lista desplegable (chooser) |  |
| `ra_chooser_add_item(id, label)` | `LONG` | Añade una opción a la lista desplegable |  |
| `ra_get_chooser_selected(id)` | `LONG` | La opción elegida de la lista desplegable |  |
| `ra_set_chooser_selected(id, index)` | `void` | Elige una opción de la lista desplegable |  |
| `ra_add_scroller(id, min, max, visible, initial)` | `LONG` | Añade una barra de desplazamiento horizontal |  |
| `ra_add_scroller_vert(id, min, max, visible, initial)` | `LONG` | Añade una barra de desplazamiento vertical |  |
| `ra_get_scroller(id)` | `LONG` | La posición de una barra de desplazamiento |  |
| `ra_set_scroller(id, pos)` | `void` | Cambia la posición de una barra de desplazamiento |  |
| `ra_enable_gadget(id)` | `void` | Activa un gadget |  |
| `ra_disable_gadget(id)` | `void` | Desactiva un gadget |  |
| `ra_set_string(id, text)` | `void` | Cambia el texto de un campo de texto |  |
| `ra_set_text(id, text)` | `void` | Cambia el texto de un botón o una etiqueta |  |
| `ra_layout_hgroup_begin()` | `LONG` | Empieza un grupo horizontal del layout |  |
| `ra_layout_vgroup_begin()` | `LONG` | Empieza un grupo vertical del layout |  |
| `ra_layout_group_end()` | `LONG` | Acaba un grupo del layout |  |
| `ra_add_space()` | `void` | Añade un separador horizontal |  |
| `ra_add_vspace()` | `void` | Añade un separador vertical |  |
| `ra_layout_hgroup_weighted(weight)` | `LONG` | Empieza un grupo horizontal con un peso (lo que ocupa respecto a los demás) |  |
| `ra_layout_vgroup_weighted(weight)` | `LONG` | Empieza un grupo vertical con un peso |  |
| `ra_layout_group_end_weighted()` | `LONG` | Acaba un grupo con peso |  |
| `ra_add_drawing_area(id, min_width, min_height)` | `LONG` | Añade un gadget Space para dibujar a mano |  |
| `ra_get_drawing_bounds(id)` | `LONG` | Mira dónde está el gadget Space (después de abrir la ventana) |  |
| `ra_drawing_left()` | `LONG` | La izquierda de la zona de dibujo |  |
| `ra_drawing_top()` | `LONG` | La parte de arriba de la zona de dibujo |  |
| `ra_drawing_width()` | `LONG` | El ancho de la zona de dibujo |  |
| `ra_drawing_height()` | `LONG` | El alto de la zona de dibujo |  |
| `ra_calc_drawing_area(toolbar_h, timeline_h, left_w, right_w)` | `LONG` | Calcula la zona de dibujo con las medidas de la ventana (si no hay otra forma) |  |
| `ra_refresh_canvas(id)` | `void` | Pide que se redibuje el lienzo del gadget Space (llama a su función de dibujo) |  |
| `ra_canvas_left()` | `LONG` | La izquierda del lienzo, desde su función de dibujo |  |
| `ra_canvas_top()` | `LONG` | La parte de arriba del lienzo, desde su función de dibujo |  |
| `ra_canvas_width()` | `LONG` | El ancho del lienzo, desde su función de dibujo |  |
| `ra_canvas_height()` | `LONG` | El alto del lienzo, desde su función de dibujo |  |
| `ra_init_canvas_render()` | `void` | Pone render_canvas() como la función de dibujo del lienzo |  |
| `ra_canvas_enable()` | `void` | Activa el dibujo del lienzo (cuando todo esté preparado) |  |
| `ra_gadget_exists(id)` | `LONG` | Mira si existe un gadget |  |
| `ra_window_width()` | `LONG` | El ancho de la ventana |  |
| `ra_window_height()` | `LONG` | El alto de la ventana |  |
| `ra_window_is_open()` | `LONG` | Mira si la ventana está abierta |  |
| `ra_add_listbrowser(id)` | `LONG` | Añade una lista de líneas de texto (valor: la línea elegida, -1 ninguna) |  |
| `ra_listbrowser_add(id, text)` | `LONG` | Añade una línea al final de una lista |  |
| `ra_listbrowser_clear(id)` | `void` | Quita todas las líneas de una lista |  |
| `ra_listbrowser_count(id)` | `LONG` | Cuántas líneas tiene una lista |  |
| `ra_add_radio(id, options)` | `LONG` | Añade botones de radio, opciones separadas por \| (valor: la opción) |  |
| `ra_add_clicktab(id, titles)` | `LONG` | Añade pestañas, títulos separados por \| (valor: la pestaña, desde 0) |  |
| `ra_add_fuelgauge(id, max)` | `LONG` | Añade una barra de progreso de 0 a max (valor: el nivel) |  |
| `ra_menu_title(label)` | `void` | Añade un menú a la ventana ReAction (antes de ra_window_open) |  |
| `ra_menu_item(label, key, id)` | `void` | Añade una opción de menú: key = la letra de Amiga+tecla ("" ninguna); eventos: RA_EVENT_MENU() y ra_menu_id() |  |
| `ra_menu_separator()` | `void` | Añade una raya de separación al menú |  |
| `ra_menu_id()` | `LONG` | El número de la opción de menú del último RA_EVENT_MENU() |  |
| `RA_EVENT_MENU()` | `LONG` | Evento: se eligió una opción de menú (ra_menu_id) |  |
| `ra_add_getfile(id, title)` | `LONG` | Añade un botón que abre un diálogo de ficheros; ra_get_string(id) da el fichero elegido |  |

## Sistema y memoria

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `debug_break()` | `void` | Para en el depurador del emulador UAE (en un Amiga de verdad no hace nada; tools/emu_run.py --debug) |  |
| `mem_chip_free()` | `LONG` | La memoria chip libre |  |
| `mem_fast_free()` | `LONG` | La memoria fast libre |  |
| `mem_total()` | `LONG` | La memoria libre, chip y fast (la que queda, no el tamaño de la RAM) |  |
| `mem_chip_total()` | `LONG` | El tamaño de la memoria chip en bytes (libre y en uso: AvailMem con MEMF_TOTAL) |  |
| `mem_fast_total()` | `LONG` | El tamaño de la memoria fast en bytes (libre y en uso: AvailMem con MEMF_TOTAL) |  |
| `peek_byte(addr)` | `LONG` | Lee un byte de una dirección de memoria |  |
| `peek_word(addr)` | `LONG` | Lee un word (16 bits) de una dirección de memoria |  |
| `peek_long(addr)` | `LONG` | Lee un long (32 bits) de una dirección de memoria |  |
| `poke_byte(addr, value)` | `void` | Escribe un byte en una dirección de memoria |  |
| `poke_word(addr, value)` | `void` | Escribe un word (16 bits) en una dirección de memoria |  |
| `poke_long(addr, value)` | `void` | Escribe un long (32 bits) en una dirección de memoria |  |
| `time_delay(ticks)` | `void` | Espera tics (50 por segundo) |  |
| `time_delay_ms(ms)` | `void` | Espera milisegundos (de 20 en 20: lo que dura un tic) |  |
| `random()` | `LONG` | Un número al azar |  |
| `random_range(min, max)` | `LONG` | Un número al azar entre min y max (los dos incluidos) |  |
| `random_seed(seed)` | `void` | Pone la semilla de los números al azar |  |
| `wait_vblank()` | `void` | Espera al retrazado vertical |  |
| `wait_blit()` | `void` | Espera a que acabe el blitter |  |
| `arena_new(size)` | `LONG` | Crea una arena (memoria que se reparte por orden) de ese tamaño en bytes |  |
| `arena_alloc(arena, size)` | `LONG` | Pide memoria de una arena (muy rápido) |  |
| `arena_reset(arena)` | `void` | Vacía una arena (reusa la memoria sin liberarla) |  |
| `arena_free(arena)` | `void` | Libera una arena y toda su memoria |  |
| `arena_used(arena)` | `LONG` | Los bytes usados de una arena |  |
| `arena_available(arena)` | `LONG` | Los bytes libres de una arena |  |
| `refcount(obj)` | `LONG` | El contador de referencias de un objeto |  |
| `retain(obj)` | `void` | Suma una referencia a mano |  |
| `release(obj)` | `void` | Quita una referencia a mano (libera el objeto si llega a 0) |  |
| `mem_trim()` | `LONG` | Devuelve al sistema los charcos de bloques pequeños (hasta 128 bytes) que están del todo libres; los bytes devueltos |  |
| `mem_puddle(bytes)` | `BOOL` | El tamaño de los charcos del pool de memoria (de 1 KB a 1 MB; 4 KB si no); solo antes de pedir memoria |  |

## Ficheros (DOS)

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `file_open(filename, mode)` | `LONG` | Abre un fichero (modo: 1005 leer, 1006 nuevo, 1004 leer y escribir; 0 si no se puede) |  |
| `file_close(handle)` | `void` | Cierra un fichero |  |
| `file_read_byte(handle)` | `LONG` | Lee un byte |  |
| `file_read_line(handle, buffer, maxlen)` | `STRPTR` | Lee una línea en un búfer |  |
| `file_read(handle, buffer, length)` | `LONG` | Lee bytes en un búfer |  |
| `file_eof(handle)` | `BOOL` | True al final del fichero (mira el byte siguiente sin gastarlo) |  |
| `file_write_byte(handle, byte)` | `LONG` | Escribe un byte |  |
| `file_write_line(handle, str)` | `LONG` | Escribe un texto y un salto de línea (0 bien, -1 error) |  |
| `file_write(handle, buffer, length)` | `LONG` | Escribe bytes de un búfer |  |
| `file_print(handle, str)` | `void` | Escribe un texto en un fichero |  |
| `file_seek(handle, position, mode)` | `LONG` | Va a un sitio del fichero (modo: OFFSET_BEGINNING, OFFSET_CURRENT, OFFSET_END) |  |
| `file_pos(handle)` | `LONG` | El sitio actual en el fichero |  |
| `file_size(filename)` | `LONG` | El tamaño de un fichero |  |
| `file_exists(filename)` | `BOOL` | Mira si existe un fichero |  |
| `file_delete(filename)` | `BOOL` | Borra un fichero |  |
| `file_rename(oldname, newname)` | `BOOL` | Cambia el nombre de un fichero |  |
| `file_copy(src, dest)` | `BOOL` | Copia un fichero |  |
| `dir_create(path)` | `BOOL` | Crea un cajón |  |
| `dir_change(path)` | `BOOL` | Cambia el cajón actual |  |
| `dir_current()` | `STRPTR` | El nombre entero del cajón actual ("Ram Disk:"...) |  |
| `dir_read(path)` | `LONG` | Lee lo que hay en un cajón, por orden de nombre (sin mirar mayúsculas): cuántas entradas, -1 si no es un cajón que se pueda leer. dir_entry_name y las demás las leen, hasta el siguiente dir_read |  |
| `dir_entry_name(i)` | `STRPTR` | El nombre de la entrada i (desde 0) del último dir_read; "" si no la hay |  |
| `dir_entry_size(i)` | `LONG` | El tamaño en bytes de la entrada i del último dir_read (0 si es un cajón) |  |
| `dir_entry_is_dir(i)` | `BOOL` | Verdadero si la entrada i del último dir_read es un cajón |  |
| `dir_entry_date(i)` | `LONG` | La fecha de la entrada i del último dir_read, como time_unix: segundos desde el 1 de enero de 1970 |  |
| `console_read(buffer, maxlen)` | `LONG` | Lee de la consola |  |
| `console_write(str)` | `void` | Escribe en la consola (sin búfer) |  |
| `file_load(filename, buffer, maxsize)` | `LONG` | Carga un fichero entero en un búfer: los bytes leídos, o -1 |  |
| `file_save(filename, buffer, size)` | `LONG` | Guarda un búfer en un fichero: los bytes escritos |  |

## Buffers

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `buffer_alloc(size)` | `APTR` | Pide un búfer de memoria |  |
| `buffer_free(buffer)` | `void` | Libera un búfer |  |
| `buffer_get_byte(buffer, offset)` | `LONG` | El byte en una posición |  |
| `buffer_set_byte(buffer, offset, value)` | `void` | Pone el byte de una posición |  |
| `buffer_get_word(buffer, offset)` | `LONG` | El word de 16 bits en una posición (big-endian) |  |
| `buffer_set_word(buffer, offset, value)` | `void` | Pone el word de 16 bits de una posición (big-endian) |  |
| `buffer_get_long(buffer, offset)` | `LONG` | El long de 32 bits en una posición (big-endian) |  |
| `buffer_set_long(buffer, offset, value)` | `void` | Pone el long de 32 bits de una posición (big-endian) |  |
| `buffer_copy(dest, dest_offset, src, src_offset, length)` | `void` | Copia bytes de un búfer a otro |  |
| `buffer_fill(buffer, offset, length, value)` | `void` | Llena una zona de un búfer con un byte |  |

## Texto

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `str_code(s, i)` | `LONG` | El código (0-255) del carácter en la posición i; 0 fuera del texto |  |
| `str_char(code)` | `STRPTR` | Un texto de un carácter con ese código |  |
| `str_find(s, sub)` | `LONG` | La posición del primer sub en s; -1 si no está |  |
| `str_find_from(s, sub, start)` | `LONG` | La posición del primer sub en s desde start; -1 si no está |  |
| `str_starts(s, prefix)` | `BOOL` | ¿Empieza s por prefix? |  |
| `str_ends(s, suffix)` | `BOOL` | ¿Acaba s en suffix? |  |
| `str_lower(s)` | `STRPTR` | Una copia en minúsculas (Latin-1: también las letras con acento) |  |
| `str_upper(s)` | `STRPTR` | Una copia en mayúsculas (Latin-1: también las letras con acento) |  |
| `str_trim(s)` | `STRPTR` | Una copia sin espacios, tabuladores ni saltos de línea a los lados |  |
| `str_to_int(s, base)` | `LONG` | El número escrito en s en esa base (2-36); Int(s) es en base 10 |  |
| `str_from_int(n, base)` | `STRPTR` | n escrito en esa base (2-36, letras en minúscula) |  |
| `str_replace(s, from, to)` | `STRPTR` | Una copia con cada from cambiado por to |  |
| `str_contains(s, sub)` | `BOOL` | Si sub está en s ("" está en todos) |  |
| `str_split(s, sep)` | `DashArrayLong *` | Los trozos de s entre cada sep, en una [String] nueva; con sep "" o si no está, [s] |  |
| `file_read_text(filename)` | `STRPTR` | El fichero entero como texto (los bytes 0 pasan a espacios); nil si no se puede leer |  |
| `file_write_text(filename, text)` | `BOOL` | Escribe el texto como el fichero entero; true si se escribió todo |  |
| `str_from_buffer(buffer, offset, length)` | `STRPTR` | Un texto con length bytes de un búfer desde offset (los bytes 0 pasan a espacios) |  |
| `str_to_buffer(s, buffer, offset)` | `LONG` | Copia los bytes de s a buffer + offset; da cuántos |  |

## Red (TCP)

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `net_connect(host, port, timeout_ms)` | `LONG` | Una conexión TCP a host:port (nombre o dirección): el socket, o -1 (ver net_error) |  |
| `net_connect_start(host, port, timeout_ms)` | `LONG` | Empieza una conexión TCP sin esperar (el nombre se busca en otro proceso): el socket, o -1 (ver net_error) |  |
| `net_connect_poll(sock)` | `LONG` | Sigue con net_connect_start sin esperar: 1 conectada, 0 aún no, -1 falló (el socket se cierra; ver net_error) |  |
| `net_connect_stage(sock)` | `LONG` | Qué está haciendo net_connect_start: 0 buscando el nombre, 1 conectando, 2 hecho |  |
| `net_send(sock, text)` | `LONG` | Envía el texto entero; los bytes enviados o -1 |  |
| `net_send_buffer(sock, buffer, length)` | `LONG` | Envía length bytes de un búfer; los bytes enviados o -1 |  |
| `net_recv(sock, max, timeout_ms)` | `STRPTR` | Hasta max bytes como texto: "" si no llegó nada en timeout_ms (-1: esperar), nil al cerrarse |  |
| `net_recv_buffer(sock, buffer, max, timeout_ms)` | `LONG` | Hasta max bytes en un búfer: cuántos, 0 si se acabó el tiempo, -1 al cerrarse |  |
| `net_wait(sock, timeout_ms)` | `LONG` | Espera a que haya algo que leer: 1 sí, 0 se acabó el tiempo, -1 error |  |
| `net_close(sock)` | `void` | Cierra la conexión |  |
| `net_resolve(host)` | `STRPTR` | La dirección IPv4 de un nombre ("a.b.c.d"); nil si no se conoce |  |
| `net_error()` | `STRPTR` | Qué falló en la última llamada net_ |  |
| `net_listen(port)` | `LONG` | Un servidor TCP en un puerto (0: uno libre cualquiera, net_port dice cuál): el socket que escucha, o -1 (ver net_error) |  |
| `net_accept(sock, timeout_ms)` | `LONG` | La siguiente conexión a un servidor de net_listen, esperando como mucho timeout_ms (-1: esperar, 0: solo mirar): su socket (net_send, net_recv...), o -1 si no llegó ninguna |  |
| `net_peer(sock)` | `STRPTR` | La dirección ("a.b.c.d") del otro lado de una conexión TCP; nil si no hay |  |
| `net_port(sock)` | `LONG` | El puerto local de un socket (el que tocó con net_listen(0) o net_udp_open(0)); -1 si no hay |  |
| `net_udp_open(port)` | `LONG` | Un socket UDP en un puerto (0: uno libre cualquiera), con difusión: el socket, o -1 (se cierra con net_close) |  |
| `net_udp_send(sock, host, port, text)` | `LONG` | Envía el texto como un datagrama a host:port ("255.255.255.255": toda la red local); los bytes enviados o -1 |  |
| `net_udp_send_buffer(sock, host, port, buffer, length)` | `LONG` | Envía length bytes de un búfer como un datagrama a host:port; los bytes enviados o -1 |  |
| `net_udp_recv(sock, max, timeout_ms)` | `STRPTR` | El siguiente datagrama como texto (hasta max bytes): "" si no llegó ninguno en timeout_ms, nil si hubo un error; quién lo envió: net_udp_from, net_udp_from_port |  |
| `net_udp_recv_buffer(sock, buffer, max, timeout_ms)` | `LONG` | El siguiente datagrama en un búfer: su largo, 0 si no llegó a tiempo, -1 si hubo un error |  |
| `net_udp_from()` | `STRPTR` | La dirección ("a.b.c.d") de quien envió el último datagrama recibido |  |
| `net_udp_from_port()` | `LONG` | El puerto de quien envió el último datagrama recibido (para contestarle) |  |
| `net_stack_running()` | `BOOL` | True si hay una pila TCP/IP en marcha (su bsdsocket.library está en memoria), sin cargar nada para saberlo. La de Roadshow sigue en memoria tras NetShutdown: esa se abre y se cierra |  |
| `net_release()` | `void` | Suelta la red ya: se cierra bsdsocket.library, con los sockets, las conexiones TLS y las búsquedas de nombres abiertos; la siguiente llamada net_ la abre otra vez (al acabar el programa también) |  |
| `net_signal()` | `LONG` | La máscara de señal que dan los sockets con cada evento (conectado, datos, cerrado...), 0 si la pila TCP/IP no puede: llamarla antes de cada espera, mui_wait_event_signals(net_signal()) |  |

## TLS (AmiSSL)

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `tls_connect(sock, host)` | `LONG` | TLS sobre un socket conectado, comprobando el certificado de host; -1 si no (net_error) |  |
| `tls_connect_start(sock, host, timeout_ms)` | `LONG` | TLS sobre un socket conectado sin esperar al saludo: la conexión, o -1 (ver net_error) |  |
| `tls_connect_poll(tls)` | `LONG` | Sigue con tls_connect_start: 1 hecho (certificado comprobado), 0 aún no, -1 falló (la conexión TLS se libera; ver net_error) |  |
| `tls_send(tls, text)` | `LONG` | Envía el texto entero; los bytes enviados o -1 |  |
| `tls_send_buffer(tls, buffer, length)` | `LONG` | Envía length bytes de un búfer; los bytes enviados o -1 |  |
| `tls_recv(tls, max, timeout_ms)` | `STRPTR` | Como net_recv: "" si no llegó nada a tiempo, nil al cerrarse |  |
| `tls_recv_buffer(tls, buffer, max, timeout_ms)` | `LONG` | Como net_recv_buffer: cuántos, 0 si se acabó el tiempo, -1 al cerrarse |  |
| `tls_close(tls)` | `void` | Acaba la TLS de la conexión (después, net_close del socket) |  |
| `tls_resumed(tls)` | `BOOL` | True si la conexión retomó una sesión anterior con el mismo servidor (sin intercambiar claves) |  |

## Fuentes y colores

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `font_open(name, size)` | `LONG` | Abre una fuente ("helvetica.font", tamaño en píxeles, 2 como poco): la fuente, o 0 si no hay |  |
| `font_use(font)` | `void` | Escribe con esta fuente |  |
| `font_close(font)` | `void` | Cierra una fuente (las abiertas se cierran al acabar) |  |
| `font_style(style)` | `void` | El estilo del texto: 0 normal, +1 subrayado, +2 negrita, +4 cursiva |  |
| `font_height()` | `LONG` | El alto de la fuente actual |  |
| `font_baseline()` | `LONG` | Los píxeles de arriba del texto a su línea base |  |
| `font_text_width(text)` | `LONG` | El ancho de un texto en píxeles con la fuente y el estilo actuales |  |
| `font_size(font)` | `LONG` | El tamaño que dio el sistema para esta fuente (el más cercano que tiene) |  |
| `color_pen(r, g, b)` | `LONG` | El color de la pantalla en la que se dibuja más parecido a r, g, b (0-255); para gfx_pen |  |
| `color_pen_free(pen)` | `void` | Un color_pen de ese lápiz ya no hace falta; cuando no queda ninguno, vuelve a la pantalla (ReleasePen) |  |

## Transparencia y degradados

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `gfx_blend_rect(x1, y1, x2, y2, rgb, alpha)` | `void` | Mezcla el color 0xRRGGBB con lo dibujado, alfa 0-255 (pantallas de paleta: un tramado 4x4 del color más cercano) |  |
| `gfx_gradient_rect(x1, y1, x2, y2, rgb1, alpha1, rgb2, alpha2, vertical)` | `void` | Un degradado de (rgb1, alpha1) a (rgb2, alpha2), de arriba abajo si vertical, si no de izquierda a derecha, mezclado con lo dibujado |  |
| `gfx_pixel_rgb(x, y)` | `LONG` | El color de un píxel como 0xRRGGBB (en una pantalla de paleta, el de su color) |  |

## Imágenes RGB desde un buffer (vídeo)

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `gfx_rgb_draw(buffer, width, height, x, y)` | `void` | Dibuja un búfer RGB24 (3 bytes por píxel, filas una tras otra) en x, y (RTG: con un WritePixelArray; pantallas de paleta: los colores más cercanos) |  |
| `gfx_rgb_draw_scaled(buffer, width, height, x, y, dest_width, dest_height)` | `void` | Dibuja un búfer RGB24 en x, y a dest_width x dest_height (el píxel más cercano, fila a fila) |  |

## Tareas, reloj, traducciones y escritorio

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `task_start(func, arg)` | `LONG` | Ejecuta una función f(arg: Int) -> Int en otro proceso: una de Dash que solo use Int, Bool, Float y builtins que no den textos ni listas (el compilador lo comprueba), o una de C (@extern, @native: malloc/free sí, textos y listas de Dash no); 128 KB de pila, la prioridad del programa: la tarea, o 0 |  |
| `task_start_with(func, arg, stack, priority)` | `LONG` | task_start con su pila en bytes (0: 128 KB) y su prioridad respecto a la del programa (-1: solo corre cuando el programa espera) |  |
| `task_done(task)` | `BOOL` | True cuando la función ha acabado (no espera) |  |
| `desktop_canvas(x, y, width, height)` | `APTR` | Una zona del escritorio del Workbench (debajo de la barra de título de la pantalla), detrás de los iconos y sin clics, en modo fondo o no, planar o RTG; x o y negativas: desde el borde derecho o el de abajo (-1 lo toca). 0 si no se puede |  |
| `desktop_canvas_on_draw(canvas, func)` | `void` | La función f(x, y, ancho, alto) que dibuja la zona con gfx_ (desde 0, 0), sobre el fondo de escritorio que hay debajo |  |
| `desktop_canvas_update(canvas)` | `void` | Dibuja otra vez la zona ya y enseña lo que cambió, sin tocar los iconos |  |
| `desktop_canvas_update_area(canvas, x, y, width, height)` | `void` | desktop_canvas_update solo en esa parte de la zona: el dibujo se recorta a ella y solo se compara ella (lo demás se queda como estaba; donde el escritorio se repintó entretanto, también se dibuja) |  |
| `desktop_canvas_veil(canvas, rgb, alpha)` | `void` | El fondo de debajo del dibujo mezclado con rgb (0xRRGGBB) con alpha (0-255; 0: ninguno), una vez y otra solo donde el escritorio lo repinta: como un gfx_blend_rect sobre toda la zona en cada dibujo, sin su coste. Quita los velos de desktop_canvas_veil_rect. Se ve desde el siguiente desktop_canvas_update |  |
| `desktop_canvas_veil_rect(canvas, x, y, width, height, rgb, alpha)` | `BOOL` | Un velo más, solo en ese rectángulo, mezclado una vez sobre el de desktop_canvas_veil (que los quita: llamarlo antes): una caja que siempre está. Hasta 16; false si no caben más |  |
| `desktop_canvas_drawing(x, y, width, height)` | `BOOL` | Dentro de la función de dibujo: true si ese rectángulo llega a la parte que se dibuja (toda la zona, o la de desktop_canvas_update_area con lo que repintó el escritorio), para saltarse lo que no se vería. Fuera de ella, siempre true |  |
| `desktop_canvas_free(canvas)` | `void` | Vuelve a poner el fondo de escritorio en la zona (al acabar el programa también) |  |
| `break_check()` | `BOOL` | True si llegó un Ctrl-C ("Break" en el Shell, u otra copia: single_instance); se borra |  |
| `single_instance(name)` | `BOOL` | Una sola copia a la vez: false si corre otra copia del programa (un puerto público con ese nombre), que recibe un Ctrl-C; si no, true (el puerto es del programa hasta que acaba) |  |
| `tooltype(name, default)` | `STRPTR` | Un tooltype del programa: desde el Shell, el argumento NOMBRE=valor (también NOMBRE="a b"); si no (o desde el Workbench), el tooltype de su icono; default si no está en ninguno |  |
| `cx_broker(name, title, description, priority)` | `BOOL` | El programa en Exchange como commodity, con Mostrar y Ocultar, activado (nombre de hasta 23 letras, título y descripción de hasta 39); false sin commodities.library o si ya hay uno con ese nombre. Se quita al acabar el programa |  |
| `cx_hotkey(description)` | `BOOL` | La tecla rápida de la commodity, según su descripción ("ctrl alt t"): cx_command da 6 al pulsarla; false si la descripción no vale (o no hay cx_broker); "" la quita |  |
| `cx_key_add(description, n)` | `BOOL` | Una tecla rápida más para la commodity (hasta 32, n de 1 a 32; también un botón del ratón: "rawmouse lalt mouse_leftpress"): cx_command da 100 + n al pulsarla, y el evento no sigue; "" quita la tecla n; false si la descripción no vale (o no hay cx_broker) |  |
| `cx_command()` | `LONG` | La siguiente orden de Exchange o de la tecla rápida: 0 ninguna, 1 ocultar, 2 mostrar, 3 desactivar, 4 activar, 5 quitar, 6 tecla rápida. Desactivar y activar apagan y encienden la commodity (y su tecla) |  |
| `cx_wait(ms)` | `LONG` | Espera, sin gastar nada, hasta que llegue una orden (la da como cx_command), un Ctrl-C (-1, se borra) o pasen ms milisegundos (0) |  |
| `disks_read(ms)` | `LONG` | Lee los volúmenes montados (con disco dentro), su tamaño y su espacio libre, preguntando a todos a la vez y esperando como mucho ms milisegundos: cuántos hay. No pide ningún disco |  |
| `disk_name(i)` | `STRPTR` | El nombre del volumen i (de 0 a disks_read() - 1) del último disks_read, sin los dos puntos |  |
| `disk_kb(i)` | `LONG` | El tamaño del volumen i en KB (como lo enseña Info); -1 si no contestó a tiempo |  |
| `disk_free_kb(i)` | `LONG` | El espacio libre del volumen i en KB; -1 si no contestó a tiempo |  |
| `net_ifs_read()` | `LONG` | Lee las interfaces de red de Roadshow (también lo0), su estado y sus bytes: cuántas hay; -1 sin pila TCP/IP o con una que no lo dice (AmiTCP, Miami) |  |
| `net_if_name(i)` | `STRPTR` | El nombre de la interfaz i (de 0 a net_ifs_read() - 1) del último net_ifs_read |  |
| `net_if_up(i)` | `BOOL` | True si la interfaz i está levantada (conectada) |  |
| `net_if_bytes_in(i)` | `LONG` | Los bytes recibidos por la interfaz i (los 32 bits bajos: la diferencia entre dos lecturas son los bytes de entretanto, aunque pase de 2 GB) |  |
| `net_if_bytes_out(i)` | `LONG` | Los bytes enviados por la interfaz i (los 32 bits bajos, como net_if_bytes_in) |  |
| `pistorm_temperature()` | `LONG` | La temperatura de la Raspberry Pi de una PiStorm (Emu68), en décimas de grado Celsius (523: 52,3), de su firmware por el mailbox.resource de Emu68; -1 sin Emu68 |  |
| `wifi_read(interface, ms)` | `LONG` | Pide al driver SANA-II de una interfaz de Roadshow su señal WiFi, esperando como mucho ms milisegundos: 0 leída (wifi_signal, wifi_noise), 1 no contestó a tiempo, 2 el driver no lo dice, 3 no hay esa interfaz, 4 el driver da un error (desconectado), 5 la pila tiene el driver solo para ella, -1 sin Roadshow |  |
| `wifi_read_device(driver, unit, ms)` | `LONG` | Como wifi_read, preguntando directamente a un driver SANA-II en uso ("wifipi.device", unidad 0), con cualquier pila TCP/IP: 0 leída, 1 no contestó a tiempo, 2 el driver no lo dice, 3 no hay ese driver en uso, 4 desconectado, 5 la pila lo tiene solo para ella |  |
| `net_drivers_read()` | `LONG` | Lee los drivers de red SANA-II en uso, con cualquier pila TCP/IP (los de DEVS:Networks que algo tiene abiertos): cuántos |  |
| `net_driver_name(i)` | `STRPTR` | El nombre del driver i (de 0 a net_drivers_read() - 1) del último net_drivers_read ("wifipi.device") |  |
| `net_driver_read(driver, unit, ms)` | `LONG` | Pide a un driver SANA-II en uso sus paquetes de entrada y salida, esperando como mucho ms: los códigos de wifi_read_device (0 leído: net_driver_packets_in, net_driver_packets_out) |  |
| `net_driver_has_bytes()` | `BOOL` | True si el driver del último net_driver_read cuenta bytes (sus paquetes IPv4, IPv6 y ARP): net_driver_bytes_in y net_driver_bytes_out |  |
| `net_driver_bytes_in()` | `LONG` | Los bytes recibidos por el driver del último net_driver_read (los 32 bits bajos), si net_driver_has_bytes |  |
| `net_driver_bytes_out()` | `LONG` | Los bytes enviados por el driver del último net_driver_read, si net_driver_has_bytes |  |
| `net_driver_packets_in()` | `LONG` | Los paquetes recibidos por el driver del último net_driver_read que dio 0 |  |
| `net_driver_packets_out()` | `LONG` | Los paquetes enviados por el driver del último net_driver_read que dio 0 |  |
| `wifi_signal()` | `LONG` | El nivel de señal del último wifi_read que dio 0, en dBm (-30 muy bueno, -90 muy malo) |  |
| `wifi_noise()` | `LONG` | El nivel de ruido del último wifi_read que dio 0, en dBm |  |
| `usb_hid_read()` | `LONG` | Lee los dispositivos USB (cada interfaz) que lleva la hid.class de Poseidon: cuántos; -1 sin poseidon.library 4 |  |
| `usb_hid_name(i)` | `STRPTR` | El nombre del producto del dispositivo USB i (de 0 a usb_hid_read() - 1) del último usb_hid_read |  |
| `usb_hid_maker(i)` | `STRPTR` | El fabricante del dispositivo USB i |  |
| `usb_hid_vendor(i)` | `LONG` | El VendorID del dispositivo USB i |  |
| `usb_hid_product(i)` | `LONG` | El ProductID del dispositivo USB i |  |
| `usb_hid_kind(i)` | `LONG` | Qué es el dispositivo USB i: 1 ratón, 2 teclado, 0 otra cosa (muchos trackpads) |  |
| `usb_hid_emitter(i)` | `LONG` | El emisor del dispositivo USB i: el número de la tarea de hid.class que envía sus movimientos, para mouse_curve |  |
| `mouse_curve(emitter, factors)` | `BOOL` | La curva de aceleración de un ratón: el emisor 0 es el ratón del Amiga (y todo movimiento que no venga de un ratón USB); si no, uno de usb_hid_emitter. factors: una lista de centésimas (100 = tal cual), la entrada i para un movimiento de i unidades, la última desde ahí (hasta 32); [] la quita. Las fracciones que sobran se guardan. False si input.device no se abre o ya hay 16 emisores |  |
| `mouse_curve_events(emitter)` | `LONG` | Cuántos movimientos ha escalado la curva de un emisor |  |
| `mouse_curves_off()` | `void` | Quita ya las curvas de input.device (al acabar el programa también); un mouse_curve las vuelve a poner. Bajo el parche de otro programa queda un puente que lo deja pasar todo |  |
| `mouse_patch_left()` | `LONG` | Cuántos puentes quedaron bajo el parche de otro programa en input.device (lo dejan pasar todo, para siempre) |  |
| `mouse_prefs_ticks()` | `LONG` | La velocidad del ratón del sistema (preferencias de Input): 1 la más rápida, 2, 4 la más lenta |  |
| `mouse_prefs_accel()` | `BOOL` | True si está puesta la aceleración del ratón del sistema (preferencias de Input) |  |
| `mouse_prefs_set(ticks, accel)` | `void` | Pone la velocidad y la aceleración del ratón del sistema; vuelven a ser como eran al acabar el programa |  |
| `tr(id, text)` | `STRPTR` | El texto número id del catálogo del programa (@catalog) en el idioma del usuario; text (el del propio programa) sin catálogo, sin ese número o sin locale.library |  |
| `catalog_open(name, version)` | `BOOL` | Abre otro catálogo ("X.catalog", versión 0: cualquiera) en los idiomas del usuario en vez del que se usa; false si no hay (tr da los textos del propio programa) |  |
| `catalog_language()` | `STRPTR` | El idioma del catálogo que se usa ("english"); "" si no hay |  |
| `clock_read()` | `void` | Toma la fecha y la hora del reloj del sistema: clock_year, clock_month... dan sus partes |  |
| `clock_year()` | `LONG` | El año del último clock_read (1978...) |  |
| `clock_month()` | `LONG` | El mes del último clock_read (1 a 12) |  |
| `clock_day()` | `LONG` | El día del mes del último clock_read (1 a 31) |  |
| `clock_weekday()` | `LONG` | El día de la semana del último clock_read: 0 domingo, 1 lunes ... 6 sábado |  |
| `clock_hour()` | `LONG` | La hora del último clock_read (0 a 23) |  |
| `clock_minute()` | `LONG` | El minuto del último clock_read |  |
| `clock_second()` | `LONG` | El segundo del último clock_read |  |
| `date_text(format)` | `STRPTR` | La fecha y la hora de ahora como dice format, con el FormatDate de locale.library en el idioma y el país del usuario: %A día, %d-%m-%Y, %b mes, %H:%M:%S... (en inglés sin locale.library) |  |
| `locale_decimal_point()` | `STRPTR` | Lo que va antes de los decimales en el país del usuario: "," en España, "." en inglés (también sin locale.library) |  |
| `locale_group_separator()` | `STRPTR` | Lo que separa los miles en el país del usuario: "." en España (1.234,5), "," en inglés (1,234.5); puede ser "" |  |
| `locale_date_order()` | `STRPTR` | El orden de día, mes y año en la fecha corta del usuario: "DMY", "MDY" o "YMD" |  |
| `program_version()` | `STRPTR` | El nombre y la versión del programa de @version ("Trasfondo 0.7"); "" sin ella |  |
| `file_notify(path)` | `LONG` | Vigila un fichero (puede no existir aún): su número (1 a 8), 0 si no se puede vigilar. cx_wait da 7 cuando cambia; file_changed(n) dice si cambió |  |
| `file_changed(n)` | `BOOL` | True si el fichero vigilado con ese número cambió desde el último file_changed |  |
| `file_notify_end(n)` | `void` | Deja de vigilar ese fichero (al acabar el programa se dejan todos) |  |
| `file_notify_signal()` | `LONG` | La señal de los ficheros vigilados, para mui_wait_event_signals (0 antes de un file_notify) |  |
| `run_program(command)` | `BOOL` | Empieza una orden ("SYS:Prefs/Font", "\"Work:Mi Prog\" arg") en otro proceso sin esperar, con su entrada y su salida en NIL:; false si no pudo empezar |  |
| `program_relaunch()` | `void` | Al acabar el programa, lo vuelve a empezar (después de todo lo de su final, también el puerto de single_instance) como empezó: desde el Workbench (3.5+: con su icono) o desde un Shell con sus argumentos. Para actualizarse |  |
| `dos_requesters(on)` | `void` | false: sin requesters de "Inserta el volumen" ni de errores de disco para este programa (la llamada falla en su lugar); true: como antes. Al acabar el programa vuelven |  |
| `base64_to_file(text, file)` | `LONG` | Escribe en un fichero los bytes de un texto en base64 (sin mirar espacios ni saltos de línea, con relleno = o sin él): los bytes escritos, o -1 si el texto no es base64 (y entonces no hay fichero) o no se puede escribir |  |
| `cpu_start()` | `BOOL` | Empieza a contar la CPU de cada tarea (los ganchos de cambio de tarea de exec; una tarea con ganchos de otro programa no se cuenta): false sin EClock o antes del OS 2.04 |  |
| `cpu_sample()` | `LONG` | Toma una muestra: el número de tareas, con la CPU que gastó cada una desde la muestra anterior (o cpu_start), de más a menos; también engancha las tareas empezadas desde entonces |  |
| `cpu_task_name(i)` | `STRPTR` | El nombre de la tarea i de la última muestra, desde 0 (de un proceso de Shell, su orden) |  |
| `cpu_task_load(i)` | `LONG` | La CPU de la tarea i de la última muestra, en tanto por mil |  |
| `cpu_total()` | `LONG` | La CPU de todas las tareas contadas en la última muestra, en tanto por mil (lo demás es reposo) |  |
| `cpu_stop()` | `void` | Quita los ganchos de las tareas (al acabar el programa también) |  |
| `task_signal()` | `LONG` | La máscara de señal que cada tarea envía al programa cuando acaba su función (para mui_wait_event_signals); 0 si no queda ninguna libre |  |
| `task_result(task)` | `LONG` | Lo que devolvió la función (la espera si no ha acabado) |  |
| `task_free(task)` | `void` | Olvida la tarea (la espera si sigue en marcha); al acabar, el programa espera a las que queden |  |

## Imágenes (datatypes)

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `image_load(file)` | `LONG` | Una imagen de un fichero con los datatypes (ILBM; PNG, GIF, JPEG si el sistema los tiene), con los colores de la pantalla en la que se dibuja: la imagen, o 0 |  |
| `image_width(image)` | `LONG` | El ancho de una imagen |  |
| `image_height(image)` | `LONG` | El alto de una imagen |  |
| `image_draw(image, x, y)` | `void` | Dibuja una imagen en x, y (sus píxeles transparentes no se dibujan) |  |
| `image_draw_part(image, sx, sy, x, y, w, h)` | `void` | Dibuja la parte w x h de una imagen que empieza en sx, sy, en x, y |  |
| `image_scale(image, w, h)` | `LONG` | Una copia de una imagen a w x h píxeles: una imagen nueva, o 0 |  |
| `image_free(image)` | `void` | Libera una imagen (las que queden se liberan al acabar) |  |
| `image_from_rgb(buffer, width, height, alpha)` | `LONG` | Una imagen con los píxeles de un búfer (RGB, o RGBA con alfa: mezclado con lo de debajo en RTG, dibujado desde 128 en una pantalla de paleta), con los colores de la pantalla: la imagen, o 0 (necesita picture.datatype V43, AmigaOS 3.5+, salvo en pantallas RTG) |  |

## Argumentos

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `arg_count()` | `LONG` | Cuántos argumentos recibió el programa del Shell, o iconos de proyecto del Workbench (un doble clic en un documento, mayúsculas + clic en varios) |  |
| `arg(i)` | `STRPTR` | El argumento i, desde 0 ("" si no hay); desde el Workbench, la ruta entera del icono |  |
| `click_x()` | `LONG` | La X del último On Click, en la ventana (dentro de sus bordes) |  |
| `click_y()` | `LONG` | La Y del último On Click, en la ventana (dentro de sus bordes) |  |
| `time_ms()` | `LONG` | Los milisegundos desde que empezó el programa (EClock de timer.device) |  |

## Compresión (zlib)

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `inflate(src, n, dest, max)` | `LONG` | Descomprime n bytes de deflate sin cabecera (como en un ZIP) del búfer src a dest: los bytes escritos, o -1 si no es deflate o está cortado, -2 si no cabe en max, -3 si no hay memoria (zlib) |  |
| `inflate_auto(src, n, dest, max)` | `LONG` | inflate para gzip, zlib o deflate sin cabecera, según sus primeros bytes (un cuerpo HTTP con Content-Encoding gzip o deflate): los bytes escritos, o lo mismo que inflate |  |
| `deflate(src, n, dest, max, level)` | `LONG` | Comprime n bytes del búfer src a dest como deflate sin cabecera, nivel 0 (sin comprimir) a 9 (lo más pequeño; -1: 6): los bytes escritos, -2 si no caben en max, -3 si no hay memoria (zlib; unos 260 KB mientras trabaja, con cualquier nivel) |  |
| `crc32(buffer, n, crc)` | `LONG` | El CRC-32 (como en ZIP y PNG) de n bytes de un búfer, siguiendo desde crc (0 para empezar) |  |

## UTF-8

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `utf8_next(s, i)` | `LONG` | La posición del carácter UTF-8 que sigue al del byte i (el largo, al final) |  |
| `utf8_prev(s, i)` | `LONG` | La posición del carácter UTF-8 anterior al byte i (0 al principio) |  |
| `utf8_code(s, i)` | `LONG` | El punto de código del carácter UTF-8 en el byte i (65533 para un byte no válido, 0 fuera del texto) |  |
| `utf8_char(code)` | `STRPTR` | Un texto con el carácter de ese punto de código en UTF-8 ("" para 0; U+FFFD si no es uno) |  |
| `utf8_length(s)` | `LONG` | Cuántos caracteres UTF-8 tiene s (cada byte no válido cuenta como uno) |  |
| `utf8_to_latin1(s)` | `STRPTR` | Un texto UTF-8 en Latin-1: lo que Latin-1 no tiene pasa a algo parecido (“ a ", € a EUR, … a ...) o a ?, igual que los bytes no válidos |  |
| `latin1_to_utf8(s)` | `STRPTR` | Un texto Latin-1 en UTF-8 (los bytes desde 128 ocupan dos) |  |
| `utf8_check(buffer, from, to)` | `LONG` | La posición del primer byte, de from a to - 1 de un búfer, que no es UTF-8 válido (o empieza una secuencia cortada por to); -1 si todos lo son |  |

## Comparar y buscar en un búfer

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `buffer_equals(buffer, offset, n, s)` | `BOOL` | Si los n bytes de un búfer en offset son el texto s (y s tiene n bytes) |  |
| `buffer_find_byte(buffer, from, to, byte)` | `LONG` | La posición del primer byte igual a byte, de from a to - 1; o -1 |  |
| `buffer_find_any(buffer, from, to, bytes)` | `LONG` | La posición del primer byte, de from a to - 1, que es uno de los bytes del texto bytes; o -1 |  |

## Double y texto

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `str_from_double(d, decimals)` | `STRPTR` | Un Double con tantos decimales (0: ninguno), su decimal más corto redondeado alejándose del cero (2.675 con 2 da 2.68); decimales < 0: el más corto que se lee igual |  |
| `str_to_double(s)` | `double` | El Double del principio del texto, como Double(s): exacto hasta 17 cifras significativas; 0.0 si no hay número |  |

## Matemáticas de Double

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `sqrt(x)` | `double` | La raíz cuadrada (nan para un negativo) |  |
| `pow(x, y)` | `double` | x elevado a y |  |
| `exp(x)` | `double` | e elevado a x |  |
| `log(x)` | `double` | El logaritmo neperiano (-inf para 0, nan para un negativo) |  |
| `log10(x)` | `double` | El logaritmo en base 10 |  |
| `sin(x)` | `double` | El seno de x radianes |  |
| `cos(x)` | `double` | El coseno de x radianes |  |
| `tan(x)` | `double` | La tangente de x radianes |  |
| `asin(x)` | `double` | El arcoseno en radianes, de -pi/2 a pi/2 (nan fuera de -1..1) |  |
| `acos(x)` | `double` | El arcocoseno en radianes, de 0 a pi (nan fuera de -1..1) |  |
| `atan(x)` | `double` | El arcotangente en radianes, de -pi/2 a pi/2 |  |
| `atan2(y, x)` | `double` | El ángulo del punto (x, y) en radianes, de -pi a pi |  |
| `floor(x)` | `double` | El mayor número entero que no pasa de x (un Double) |  |
| `ceil(x)` | `double` | El menor número entero que no es menor que x (un Double) |  |
| `round(x)` | `double` | El número entero más cercano, las mitades alejándose del cero (2.5 da 3.0, -2.5 da -3.0) |  |
| `trunc(x)` | `double` | La parte entera, hacia el cero (-2.7 da -2.0) |  |
| `fmod(x, y)` | `double` | El resto de x / y con el signo de x (nan si y es 0) |  |
| `abs(x)` | `double` | El valor absoluto, un Double |  |
| `is_nan(x)` | `BOOL` | True si x es nan (no es un número: sqrt(-1.0), 0.0 / 0.0) |  |
| `is_inf(x)` | `BOOL` | True si x es inf o -inf |  |

## Expresiones regulares y comodines

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `regex_match(pattern, text, ignore_case)` | `BOOL` | True si el texto entero encaja con la expresión regular (la sintaxis común de ICU: . * + ? {m,n} [] [^] ^ $ \d \w \s \b \| grupos); false también si el patrón está mal (regex_error dice por qué) |  |
| `regex_find(pattern, text, from, ignore_case)` | `LONG` | La posición en bytes donde empieza lo primero que encaja desde el byte from; -1 si no hay (o el patrón está mal); regex_length da su largo |  |
| `regex_length()` | `LONG` | El largo en bytes de lo último que encajó con regex_find o regex_match (0 si nada) |  |
| `regex_error()` | `STRPTR` | Por qué está mal el último patrón; "" si está bien |  |
| `wildcard_match(pattern, text, ignore_case)` | `BOOL` | True si el texto entero encaja con los comodines de Excel: * cualquier cosa, ? un carácter, ~ delante de un carácter lo toma tal cual (~* ~? ~~) |  |

## Simular teclado y ratón

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `input_key(code, qualifiers)` | `void` | Pulsa y suelta una tecla en bruto en la ventana activa (0x44 Return, 0x45 Esc, 0x4C arriba, 0x4D abajo, 0x4E derecha, 0x4F izquierda, 0x41 Retroceso), con las teclas 1 Mayúsculas, 2 Ctrl, 4 Alt, 8 Amiga (sumadas) pulsadas alrededor |  |
| `input_text(text)` | `void` | Escribe un texto en la ventana activa con el mapa de teclado ("=SUM(A1:A3)"); lo que el mapa no puede escribir se queda fuera |  |
| `input_move(x, y)` | `void` | Lleva el puntero a (x, y) desde la esquina de la ventana activa |  |
| `input_click(x, y, qualifiers)` | `void` | Clic con el botón izquierdo en (x, y) desde la esquina de la ventana activa, con las teclas 1 Mayúsculas, 2 Ctrl, 4 Alt (Amiga + clic es del sistema) |  |
| `input_button(button, down)` | `void` | Pulsa (down true) o suelta un botón del ratón donde está el puntero: 1 izquierdo, 2 derecho (menús, un menú contextual), 3 central |  |
| `input_drag(x1, y1, x2, y2)` | `void` | Pulsa el botón izquierdo en (x1, y1), lo lleva pulsado a (x2, y2) y lo suelta (desde la esquina de la ventana activa) |  |
| `input_qualifiers()` | `LONG` | Las teclas pulsadas ahora (PeekQualifier de input.device): 1, 2 Mayúsculas; 8 Ctrl; 16, 32 Alt; 64, 128 Amiga; 0 si no se puede abrir input.device |  |
| `input_menu(menu, item, hold)` | `BOOL` | Elige con el ratón, como un usuario, la opción item (desde 0, separadores incluidos) del menú menu (desde 0) de la ventana activa: el botón derecho en su título, hasta la opción, hold tics (1/50 s) pulsado, y suelta; false si no hay esa opción |  |
| `input_move_screen(x, y, buttons)` | `void` | Lleva el puntero a (x, y) de la pantalla de píxel en píxel con botones pulsados (1 izquierdo, 2 derecho, 0 ninguno): los menús de MUI lo siguen |  |
| `input_active_title()` | `STRPTR` | El título de la ventana activa ("" si no hay): para esperar a la del programa que se prueba |  |

## Portapapeles

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `clip_write_text(s)` | `BOOL` | Copia un texto UTF-8 al portapapeles (unidad 0, IFF FTXT en Latin-1, como lo leen los demás programas): lo que Latin-1 no tiene pasa a algo parecido, como utf8_to_latin1 (€ a EUR); false si no se puede escribir |  |
| `clip_read_text()` | `STRPTR` | El texto del portapapeles (unidad 0) en UTF-8; "" si está vacío o no tiene texto |  |
| `clip_write_block(unit, type, buffer, n)` | `BOOL` | Copia n bytes de un búfer a la unidad 1-255 del portapapeles como un FORM de un tipo propio (4 caracteres, "LCLC"), después de clip_write_text: queda unido a ese texto, y si se copia otra cosa a la unidad 0, el bloque se da por perdido |  |
| `clip_block_size(unit, type)` | `LONG` | Los bytes del bloque de ese tipo en una unidad del portapapeles; -1 si no hay o se copió otra cosa después |  |
| `clip_read_block(unit, type, dest, max)` | `LONG` | Copia el bloque de ese tipo de una unidad del portapapeles al búfer dest: sus bytes, -1 si no hay o se copió otra cosa después, -2 si no cabe en max |  |

## Ordenar textos según el idioma

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `str_compare_locale(a, b, ignore_case)` | `LONG` | Compara dos textos UTF-8 en el orden del idioma del usuario (locale.library): -1 si a va antes, 0 si son iguales, 1 si va antes b; los acentos y las mayúsculas cuentan solo después de las letras ("árbol" antes que "barco", "apple" antes que "Banana"), y nada con ignore_case. Sin locale.library, por sus bytes Latin-1 |  |

## Sistema y programa

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `time_unix()` | `LONG` | El reloj del sistema en segundos desde el 1 de enero de 1970 (para fechas de HTTP y cookies) |  |
| `clock_days()` | `LONG` | Los días desde el 1 de enero de 1978 según el reloj del sistema (el ds_Days de DateStamp) |  |
| `mem_largest()` | `LONG` | El bloque de memoria libre más grande, chip o fast, en bytes |  |
| `run_command(command)` | `LONG` | Ejecuta una orden y espera a que acabe, con su salida en la del programa: su código de retorno, -1 si no pudo empezar |  |
| `wb_open(path)` | `BOOL` | Abre un cajón, un programa o un proyecto como un doble clic en su icono (workbench.library 44, OS 3.5+); false si no pudo |  |
| `program_path()` | `STRPTR` | La ruta entera del programa ("Work:Tachyon/Tachyon"), desde un Shell o desde el Workbench |  |
| `locale_language()` | `STRPTR` | El primer idioma preferido del usuario en las preferencias de Locale ("español"); "" si no hay |  |
| `cpu_model()` | `LONG` | El procesador: 68000, 68010, 68020, 68030, 68040 o 68060 |  |
| `fpu_model()` | `LONG` | La FPU: 68881, 68882, 68040 o 68060 (la del procesador); 0 si no hay |  |
| `library_version(name)` | `LONG` | La versión de una librería ("muimaster.library"), cargándola si no está en memoria; -1 si no está |  |
| `library_revision(name)` | `LONG` | La revisión de una librería (el 3 de 47.3), como library_version; -1 si no está |  |
| `resident_version(name)` | `LONG` | La versión de un módulo residente del sistema (FindResident: "MorphOS" dice que el programa corre en MorphOS); -1 si no hay |  |
| `task_priority(n)` | `LONG` | Pone la prioridad del programa (-128 a 127; el Shell da 0): la que tenía |  |
| `build_date()` | `STRPTR` | La fecha en que se compiló el programa, "2026-10-28" |  |
| `build_time()` | `STRPTR` | La hora en que se compiló el programa, "20:45:10" |  |
| `console_flush()` | `void` | Saca ya lo que Print dejó en el búfer de la salida (una línea de progreso sin su final) |  |
| `run_capture(command, timeout_ms)` | `STRPTR` | Ejecuta una orden y espera a que acabe: lo que escribió, con su código de retorno en run_rc(). Con timeout_ms mayor que 0, al pasar ese tiempo la orden recibe Ctrl-C (y otra vez cada segundo hasta que acaba). Solo su salida: AmigaOS no da canal de errores a una orden lanzada así (el stderr de un programa en C va a la consola; dashc escribe sus errores por su salida en el Amiga) |  |
| `run_start(command, timeout_ms)` | `LONG` | run_capture sin esperar: un número para run_ready, run_break y run_finish, 0 si no pudo empezar. El programa espera al acabar a las que no terminó |  |
| `run_ready(run)` | `BOOL` | Verdadero cuando un run_start ha acabado (no espera; también aplica el tope de tiempo) |  |
| `run_break(run)` | `void` | Manda Ctrl-C a un run_start que sigue en marcha (y otra vez cada segundo hasta que acaba) |  |
| `run_finish(run)` | `STRPTR` | Lo que escribió un run_start, como run_capture (espera si sigue en marcha), y lo olvida |  |
| `run_rc()` | `LONG` | El código de retorno del último run_capture o run_finish: el de la orden, -1 si no pudo empezar, -2 si se le acabó el tiempo |  |
| `env_get(name)` | `STRPTR` | Una variable de entorno (de la Shell del programa y si no, de ENV:), hasta su primer fin de línea; "" si no existe |  |
| `env_set(name, value, save)` | `BOOL` | Pone una variable en ENV: (con save verdadero, también en ENVARC:, para que siga tras reiniciar); falso si no pudo |  |
| `rexx_send(port, command)` | `STRPTR` | Manda una orden ARexx al puerto público de otro programa ("MULTIVIEW.1"; "REXX": ejecutar un script) y espera la respuesta: su RESULT ("" si no hay), el RC en rexx_rc(). No al puerto del propio programa: se esperaría a sí mismo |  |
| `rexx_rc()` | `LONG` | El RC del último rexx_send: 0 bien, 5, 10, 20... los del programa; -1 si no existe el puerto, -2 sin rexxsyslib.library |  |
| `ports_read()` | `LONG` | Lee los nombres de los puertos públicos abiertos (los de ARexx entre ellos): cuántos, para port_name, hasta el siguiente ports_read |  |
| `port_name(i)` | `STRPTR` | El nombre del puerto i (desde 0) del último ports_read |  |
| `tasks_read()` | `LONG` | Lee las tareas y procesos del sistema (el programa, el primero): cuántos, para las task_entry_, hasta el siguiente tasks_read |  |
| `task_entry_name(i)` | `STRPTR` | El nombre de la tarea i del último tasks_read ("Shell Process", "input.device"...) |  |
| `task_entry_command(i)` | `STRPTR` | La orden que ejecuta un proceso de Shell del último tasks_read ("" si ninguna) |  |
| `task_entry_state(i)` | `STRPTR` | El estado de la tarea i: "running" (el programa), "ready" o "waiting" |  |
| `task_entry_priority(i)` | `LONG` | La prioridad de la tarea i del último tasks_read |  |
| `task_entry_cli(i)` | `LONG` | El número de Shell de la tarea i (el que da Status, para Break), 0 si no es un proceso de Shell |  |
| `assigns_read()` | `LONG` | Lee las asignaciones (C:, LIBS:, las de Assign): cuántas, para assign_name y assign_path, hasta el siguiente assigns_read |  |
| `assign_name(i)` | `STRPTR` | El nombre de la asignación i del último assigns_read, sin los dos puntos |  |
| `assign_path(i)` | `STRPTR` | Adónde apunta la asignación i: un cajón ("Workbench:C"), varios separados por ";", o el nombre que buscará una diferida o no ligada |  |

## JSON leído en C (para lib/json.dash)

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `json_scan(text)` | `LONG` | Lee un texto JSON a una tabla de nodos en orden, cada uno seguido de lo que contiene (lib/json.dash hace su árbol con ella): cuántos, -1 si no es JSON (json_scan_error dice por qué y dónde) |  |
| `json_scan_error()` | `STRPTR` | Por qué el último json_scan dio -1, y en qué byte ("unexpected end at byte 1") |  |
| `json_scan_kind(i)` | `LONG` | El tipo del nodo i: 0 null, 1 true o false, 2 número, 3 texto, 4 lista, 5 objeto |  |
| `json_scan_count(i)` | `LONG` | Cuántos elementos tiene un nodo de lista u objeto (van detrás); 1 si es true, 0 si es false |  |
| `json_scan_text(i)` | `STRPTR` | El texto de un nodo de texto (sin sus escapes, \uXXXX en UTF-8) o de número (como está escrito) |  |
| `json_scan_name(i)` | `STRPTR` | El nombre del nodo i dentro de su objeto ("" en una lista o arriba del todo) |  |

## Depurador (el programa depurado, con dash --debug)

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `dbg_start(program, args)` | `BOOL` | Carga un programa compilado con dash --debug y lo lanza en un proceso propio, en pausa antes de su primera línea (se ponen los puntos de parada y luego dbg_continue): falso si no pudo (dbg_error dice por qué) |  |
| `dbg_error()` | `STRPTR` | Por qué falló el último dbg_start |  |
| `dbg_state()` | `LONG` | El programa depurado: 0 ninguno, 1 en pausa antes de empezar, 2 corriendo, 3 parado en una línea, 4 acabado |  |
| `dbg_signal()` | `LONG` | La señal que recibe el depurador cuando el programa para o acaba (para mui_wait_event_signals) |  |
| `dbg_wait(ms)` | `LONG` | Espera a que el programa pare o acabe, como mucho ms (0: sin tope): su estado |  |
| `dbg_break(file, line)` | `BOOL` | Un punto de parada en esa línea de ese fichero ("prog.dash": el final de su ruta): falso si la línea no tiene código |  |
| `dbg_unbreak(file, line)` | `BOOL` | Quita el punto de parada de esa línea |  |
| `dbg_continue()` | `BOOL` | Sigue (desde el principio o una parada) hasta un punto de parada o el final |  |
| `dbg_step()` | `BOOL` | Sigue hasta la línea siguiente, entrando en las funciones a las que llama |  |
| `dbg_next()` | `BOOL` | Sigue hasta la línea siguiente de esta función (o de la que la llamó) |  |
| `dbg_out()` | `BOOL` | Sigue hasta que la función vuelve: la línea siguiente de la que la llamó |  |
| `dbg_pause()` | `BOOL` | Para el programa que corre en la siguiente línea que ejecute |  |
| `dbg_end(ms)` | `BOOL` | Acaba el programa (Ctrl-C y, en su siguiente línea, su final de siempre): verdadero si acabó en ms |  |
| `dbg_rc()` | `LONG` | El código de retorno del programa acabado |  |
| `dbg_file()` | `STRPTR` | El fichero de la línea donde paró el programa (su ruta entera) |  |
| `dbg_line()` | `LONG` | La línea donde paró el programa (0 si no está parado) |  |
| `dbg_function()` | `STRPTR` | La función donde paró el programa ("Main", "Punto.mover"...) |  |
| `dbg_frames()` | `LONG` | Cuántas llamadas hay abiertas donde paró: 1 en Main, 2 en una función que llamó Main... (0 si no está parado) |  |
| `dbg_frame_function(i)` | `STRPTR` | La función de la llamada i: 0 donde paró, 1 la que la llamó... |  |
| `dbg_frame_line(i)` | `LONG` | La línea donde está la llamada i: 0 donde paró, 1 la de la llamada en la que la llamó... |  |
| `dbg_frame_file(i)` | `STRPTR` | El fichero de la llamada i (su ruta entera) |  |
| `dbg_vars(i)` | `LONG` | Cuántas variables ve la llamada i: sus parámetros y las variables declaradas antes de su línea |  |
| `dbg_var_name(i, k)` | `STRPTR` | El nombre de la variable k (desde 0) de la llamada i |  |
| `dbg_var_type(i, k)` | `STRPTR` | El tipo de la variable k de la llamada i, como en Dash ("Int", "[String]", "Punto") |  |
| `dbg_globals()` | `LONG` | Cuántas variables globales tiene el programa |  |
| `dbg_global_name(g)` | `STRPTR` | El nombre de la global g (desde 0) |  |
| `dbg_value(i, expr)` | `STRPTR` | El valor de expr en la llamada i, como texto: una variable de esa llamada o una global, con .campo y [n] detrás ("p.hijos[0].x"): 3, "hola", Punto(x: 3, y: 4), [1, 2], nil; "? " y el porqué si no se puede |  |
| `dbg_value_type(i, expr)` | `STRPTR` | El tipo de expr en la llamada i ("" si no se puede) |  |
| `dbg_reg(n)` | `LONG` | Un registro del programa parado: 0-7 d0-d7, 8-15 a0-a7, 16 el PC |  |
| `dbg_peek(addr, size)` | `LONG` | 1, 2 o 4 bytes de memoria en addr, sin signo |  |
| `dbg_output()` | `STRPTR` | Lo que ha escrito el programa hasta ahora (salida y salida de errores) |  |

## Imágenes decodificadas por el programa (sin datatypes)

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `image_decode(file, maxw, maxh)` | `LONG` | Decodifica un JPEG (TJpgDec), WebP (libwebp; los dos ya reducidos al decodificar), PNG, GIF, BMP (stb_image) o SVG (nanosvg: dibujado para cubrir maxw x maxh, RGBA) a píxeles RGB o RGBA, reducidos hasta que no pasen mucho de maxw x maxh (0, 0: su tamaño; negativos, un tope: un SVG va entonces a su tamaño, más pequeño si no cabe): la imagen decodificada, o 0. Sin datatypes, y vale dentro de un task_start |  |
| `image_decode_start(file, maxw, maxh)` | `LONG` | image_decode en un proceso aparte, uno por debajo de la prioridad del programa, para que la ventana siga respondiendo: un número para image_decode_ready e image_decode_finish, o 0 si no pudo empezar |  |
| `image_decode_ready(t)` | `BOOL` | Cierto cuando un image_decode_start ha terminado (no espera) |  |
| `image_decode_finish(t)` | `LONG` | Lo que decodificó un image_decode_start, como image_decode (0 si no pudo); espera si aún no ha acabado y libera su proceso |  |
| `image_decoded_width(d)` | `LONG` | El ancho de una imagen decodificada |  |
| `image_decoded_height(d)` | `LONG` | El alto de una imagen decodificada |  |
| `image_decoded_alpha(d)` | `BOOL` | True si una imagen decodificada tiene alfa (4 bytes por píxel, RGBA; si no, 3, RGB) |  |
| `image_decoded_pixels(d)` | `APTR` | Los píxeles de una imagen decodificada, fila tras fila: un búfer para buffer_get_byte o image_from_rgb |  |
| `image_decoded_free(d)` | `void` | Libera una imagen decodificada |  |
| `image_from_decoded(d)` | `LONG` | Una imagen (como image_from_rgb) de una imagen decodificada, que hay que liberar después |  |

## Fuentes TrueType, WOFF y WOFF2

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `font_from_ttf(file, size, width)` | `LONG` | Una fuente TrueType (TTF, un OTF con contornos TrueType, o un WOFF o WOFF2 de ellos) a size píxeles de em y al width % de su ancho (0: 100), sus caracteres Latin-1 en un plano de 1 bit (stb_truetype): una fuente para font_use, o 0. Se libera con font_ttf_free, no con font_close |  |
| `font_ttf_icon(file, size, code)` | `LONG` | Una fuente del fichero cuya "A" es el carácter code (un icono de una fuente web, en la zona privada de Unicode) a size píxeles, con las demás letras vacías: se dibuja "A" con ella; 0 si no se puede |  |
| `font_ttf_free(font)` | `void` | Libera una fuente de font_from_ttf (no mientras una ventana siga escribiendo con ella); las que queden se liberan al acabar |  |
| `font_ttf_forget(file)` | `void` | font_from_ttf guarda los 8 últimos ficheros leídos para otros tamaños: este se lee otra vez la próxima |  |

## Red en una tarea aparte

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `net_bg_open(host, port, timeout_ms)` | `LONG` | Pide una conexión TCP que una tarea propia abre, por la que envía y recibe mientras el programa está ocupado (hasta 48): su número, o -1. net_bg_state dice cómo va |  |
| `net_bg_open_tls(host, port, timeout_ms)` | `LONG` | net_bg_open con TLS (AmiSSL, comprobando su certificado) |  |
| `net_bg_state(c)` | `LONG` | 1 pedida, 2 conectando, 3 negociando la TLS, 4 abierta, 5 cerrada, 6 error (net_bg_error dice por qué) |  |
| `net_bg_stage(c)` | `LONG` | Mientras conecta, en qué fase está, como net_connect_stage |  |
| `net_bg_error(c)` | `STRPTR` | Por qué falló o se cerró una conexión; "" si no |  |
| `net_bg_send(c, text)` | `BOOL` | Deja un texto para enviar (la tarea lo envía en cuanto la conexión esté abierta); false si no hay memoria |  |
| `net_bg_send_buffer(c, buffer, n)` | `BOOL` | net_bg_send de n bytes de un búfer |  |
| `net_bg_recv(c, buffer, max)` | `LONG` | Hasta max bytes de lo que ha llegado, a un búfer, sin esperar: cuántos (0: nada aún), -1 si está cerrada y no queda nada. task_signal despierta al programa cuando llega algo |  |
| `net_bg_pending(c)` | `LONG` | Cuántos bytes han llegado y no se han leído |  |
| `net_bg_close(c)` | `void` | Cierra una conexión y deja libre su número |  |
| `net_bg_idle(ms)` | `void` | La tarea acaba sola tras tantos ms sin tráfico (2000; una conexión que el programa sigue leyendo, esperando la respuesta, cuenta como tráfico); cuando hace falta empieza otra |  |
| `net_bg_stop()` | `void` | Acaba la tarea ya (cierra lo que esté abierto) y la espera; también al acabar el programa |  |

## Ventanas de otros programas (pruebas)

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `window_find(title)` | `LONG` | La ventana de otro programa (o la del propio) cuyo título empieza por title, en cualquier pantalla: un número para window_found_* y gadget_*, 0 si no hay (no vale cuando se cierra) |  |
| `window_found_activate(win)` | `void` | Una ventana de window_find delante, con su pantalla, y activa (los input_* van a la ventana activa) |  |
| `window_found_box(win, what)` | `LONG` | De una ventana de window_find: 0 izquierda, 1 arriba (en su pantalla), 2 ancho, 3 alto, 4 borde izquierdo, 5 borde de arriba |  |
| `gadget_index(win, text)` | `LONG` | El sitio (desde 0, también los gadgets de la propia ventana) del gadget cuyo texto es text en una ventana de window_find; -1 si no hay. Los botones de GadTools no guardan su texto: se cuentan desde uno de al lado |  |
| `gadget_x(win, n)` | `LONG` | La x del centro del gadget del sitio n de una ventana de window_find, desde su esquina (como cuenta input_click); -1 si no hay |  |
| `gadget_y(win, n)` | `LONG` | La y del centro de ese gadget, como gadget_x |  |
| `gadget_selected(win, n)` | `BOOL` | True si el gadget del sitio n (una casilla) está marcado |  |
| `screen_pixel(x, y)` | `LONG` | El color del píxel (x, y) de la pantalla de delante; -1 fuera de ella |  |
| `cx_send(name, command)` | `LONG` | Una orden a una commodity por su nombre, como hace Exchange (15 desactivar, 17 activar, 19 enseñar, 21 ocultar, 23 quitar...): 0 hecho, -1 no hay esa commodity, -2 no tiene puerto, -99 no hay commodities.library |  |

## Gestor de ventanas (las de todos los programas)

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `wm_read()` | `LONG` | Lee las ventanas de la pantalla del Workbench, de delante atrás (hasta 64): cuántas, para wm_id, wm_title, wm_task, wm_box y wm_flags, hasta el siguiente wm_read |  |
| `wm_id(i)` | `LONG` | El id de la ventana i del último wm_read, para wm_set_box, wm_front... (0 fuera de la lista) |  |
| `wm_title(i)` | `STRPTR` | El título de la ventana i del último wm_read ("" si no tiene) |  |
| `wm_task(i)` | `STRPTR` | El programa de la ventana i: la orden de un proceso de Shell (sin su ruta), o el nombre de su tarea ("Workbench") |  |
| `wm_box(i, what)` | `LONG` | De la ventana i: 0 izquierda, 1 arriba, 2 ancho, 3 alto, 4 ancho mínimo, 5 alto mínimo, 6 ancho máximo, 7 alto máximo (0 o 65535: sin límite); -1 fuera de la lista |  |
| `wm_flags(i)` | `LONG` | De la ventana i, sumados: 1 se puede redimensionar, 2 de fondo (backdrop), 4 sin bordes, 8 activa, 16 con barra de arrastre, 32 del propio programa, 64 un cajón del Workbench, 128 con un requester |  |
| `wm_set_box(id, x, y, width, height)` | `BOOL` | Mueve y redimensiona una ventana por su id, dentro de sus límites y de su pantalla (la que no tiene botón de tamaño se queda con el suyo); false si ya no está abierta. Intuition lo hace justo después |  |
| `wm_front(id)` | `BOOL` | Una ventana delante de las demás; false si ya no está abierta |  |
| `wm_back(id)` | `BOOL` | Una ventana detrás de las demás; false si ya no está abierta |  |
| `wm_activate(id)` | `BOOL` | Hace activa una ventana (las teclas van a ella); false si ya no está abierta |  |
| `wm_zip(id)` | `BOOL` | Una ventana a su otro tamaño, como su botón de zoom; false si ya no está abierta |  |
| `wm_active()` | `LONG` | El id de la ventana activa, si está en la pantalla del Workbench; 0 si no |  |
| `wm_at(x, y)` | `LONG` | El id de la ventana que hay en (x, y) de la pantalla del Workbench, la de delante; 0 si ninguna |  |
| `wm_pointer_x()` | `LONG` | Dónde está el puntero en la pantalla del Workbench: la x |  |
| `wm_pointer_y()` | `LONG` | Dónde está el puntero en la pantalla del Workbench: la y |  |
| `wm_bar_height()` | `LONG` | El alto de la barra de título de la pantalla del Workbench (donde suelen empezar las ventanas) |  |

## Audio

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `sound_load(id, filename)` | `BOOL` | Carga un sonido IFF 8SVX (sin comprimir) |  |
| `sound_sample(id, index, value)` | `void` | Pone una muestra (-128..127) de un sonido de sound_create |  |
| `sound_create(id, length, rate)` | `BOOL` | Crea un sonido en silencio en memoria chip: largo en muestras, frecuencia en muestras por segundo |  |
| `sound_free(id)` | `void` | Libera la memoria de un sonido |  |
| `sound_play(id, channel)` | `void` | Toca un sonido una vez en un canal (0-3) |  |
| `sound_stop(channel)` | `void` | Para un canal |  |
| `sound_loop(id, channel)` | `void` | Toca un sonido en bucle en un canal (hasta sound_stop) |  |
| `sound_playing(channel)` | `BOOL` | Mira si un canal está sonando |  |
| `sound_volume(channel, vol)` | `void` | Pone el volumen de un canal (0-64) |  |
| `sound_period(channel, period)` | `void` | Pone el periodo de un canal (el tono: cuanto más bajo, más agudo) |  |
| `music_load(filename)` | `BOOL` | Carga un fichero MOD |  |
| `music_play()` | `void` | Empieza a tocar la música |  |
| `music_stop()` | `void` | Para la música |  |
| `music_pause()` | `void` | Pausa la música |  |
| `music_resume()` | `void` | Sigue con la música |  |
| `music_volume(vol)` | `void` | Pone el volumen de la música (0-64) |  |
| `music_position(pos)` | `void` | Pone la posición de la música |  |
| `music_pos()` | `LONG` | La posición de la canción que suena (en la lista de orden) |  |
| `music_row()` | `LONG` | La fila del patrón que suena (0-63) |  |
| `music_free()` | `void` | Libera los datos de la música |  |
| `tone_play(channel, freq, vol, duration)` | `void` | Toca un tono senoidal: frecuencia en Hz, volumen 0-64, duración en milisegundos (vuelve en seguida) |  |

## Intuition

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `window_create(title, x, y, w, h, flags)` | `LONG` | Abre una ventana; da su número 1..16 (0: no se pudo); flags: 1 se puede cambiar de tamaño, 2 sin bordes, 4 sin botón de cerrar, 8 w y h son el interior (sin los bordes). Pasa a ser la ventana actual |  |
| `window_border_top()` | `LONG` | El borde de arriba de la ventana actual (con la barra de título); los gadgets cuentan desde dentro, sin él |  |
| `window_border_bottom()` | `LONG` | El borde de abajo de la ventana actual |  |
| `window_border_left()` | `LONG` | El borde izquierdo de la ventana actual |  |
| `window_border_right()` | `LONG` | El borde derecho de la ventana actual |  |
| `screen_font_height()` | `LONG` | El alto de la fuente de la pantalla (la del programa, o la del Workbench): la de las barras de título y la de los gadgets de GadTools |  |
| `screen_font_text_width(text)` | `LONG` | El ancho de un texto con la fuente de la pantalla |  |
| `window_close(handle)` | `void` | Cierra una ventana (número 0: la actual) |  |
| `window_title(handle, title)` | `void` | Cambia el título de una ventana (número 0: la actual) |  |
| `window_move(handle, x, y)` | `void` | Lleva una ventana a x, y (absolutas; número 0: la actual) |  |
| `window_resize(handle, w, h)` | `void` | Cambia el tamaño de una ventana a w x h (número 0: la actual) |  |
| `window_to_front(handle)` | `void` | Pone una ventana delante (número 0: la actual) |  |
| `window_to_back(handle)` | `void` | Pone una ventana detrás (número 0: la actual) |  |
| `window_activate(handle)` | `void` | Activa una ventana (número 0: la actual) |  |
| `screen_to_front()` | `void` | Pone delante la pantalla propia |  |
| `screen_to_back()` | `void` | Pone detrás la pantalla propia |  |
| `gadget_id()` | `LONG` | El número del último gadget usado (para el On Gadget del EventLoop) |  |
| `gadget_width(gadget)` | `LONG` | El ancho de un gadget en píxeles (también si se creó con ancho 0) |  |
| `gadget_height(gadget)` | `LONG` | El alto de un gadget en píxeles (también si se creó con alto 0) |  |
| `button_create(win, x, y, w, h, label)` | `LONG` | Crea un botón |  |
| `button_enable(gad)` | `void` | Activa un botón |  |
| `button_disable(gad)` | `void` | Desactiva un botón |  |
| `textfield_create(win, x, y, w, h, maxlen)` | `LONG` | Crea un campo de texto |  |
| `textfield_get(gad)` | `STRPTR` | El texto de un campo de texto |  |
| `textfield_set(gad, text)` | `void` | Cambia el texto de un campo de texto |  |
| `checkbox_create(win, x, y, label)` | `LONG` | Crea una casilla |  |
| `checkbox_get(gad)` | `BOOL` | Si la casilla está marcada |  |
| `checkbox_set(gad, state)` | `void` | Marca o desmarca una casilla |  |
| `slider_create(win, x, y, w, h, min, max, value)` | `LONG` | Crea un deslizador |  |
| `slider_get(gad)` | `LONG` | El valor de un deslizador |  |
| `slider_set(gad, value)` | `void` | Cambia el valor de un deslizador |  |
| `listview_create(win, x, y, w, h)` | `LONG` | Crea una lista |  |
| `listview_add(gad, text)` | `void` | Añade una línea a una lista |  |
| `listview_clear(gad)` | `void` | Vacía una lista |  |
| `listview_selected(gad)` | `LONG` | La línea elegida (-1 si ninguna) |  |
| `cycle_create(win, x, y, w, h, options)` | `LONG` | Crea un gadget de opciones que cambian al pulsarlo; opciones separadas por \| (el valor es la opción, desde 0) |  |
| `cycle_get(gad)` | `LONG` | La opción elegida de un gadget de opciones |  |
| `cycle_set(gad, index)` | `void` | Elige una opción de un gadget de opciones |  |
| `radio_create(win, x, y, options)` | `LONG` | Crea botones de radio (uno por opción, separadas por \|) |  |
| `radio_get(gad)` | `LONG` | El botón de radio elegido |  |
| `radio_set(gad, index)` | `void` | Elige un botón de radio |  |
| `integer_create(win, x, y, w, h, value)` | `LONG` | Crea un campo de números enteros |  |
| `integer_get(gad)` | `LONG` | El valor de un campo de números |  |
| `integer_set(gad, value)` | `void` | Cambia el valor de un campo de números |  |
| `palette_create(win, x, y, w, h, depth)` | `LONG` | Crea un gadget de paleta de colores (2^depth colores) |  |
| `palette_get(gad)` | `LONG` | El color elegido |  |
| `palette_set(gad, color)` | `void` | Elige un color |  |
| `number_create(win, x, y, w, h, value)` | `LONG` | Crea una caja que enseña un número |  |
| `number_set(gad, value)` | `void` | Cambia el número que se enseña |  |
| `dialog_file(title, pattern, save_mode)` | `STRPTR` | Diálogo de ficheros: la ruta entera del fichero elegido, "" si se canceló (save_mode true: diálogo de guardar) |  |
| `dialog_file_at(title, pattern, save_mode, drawer, file)` | `STRPTR` | dialog_file abriéndose en ese cajón con ese nombre de fichero ("": como dialog_file) |  |
| `dialog_color(title, initial)` | `LONG` | Ventana con la paleta: da el color elegido (con un clic, o con las flechas + Return); Esc deja el inicial |  |
| `dialog_screen_mode(title)` | `BOOL` | Petición de modo de pantalla (modo, ancho, alto y profundidad), empezando en el del Workbench: cierto si se eligió uno; screen_mode_id, _width, _height y _depth lo dan |  |
| `screen_mode_id()` | `LONG` | El modo del último dialog_screen_mode (para screen_open_mode) |  |
| `screen_mode_width()` | `LONG` | El ancho elegido en el último dialog_screen_mode |  |
| `screen_mode_height()` | `LONG` | El alto elegido en el último dialog_screen_mode |  |
| `screen_mode_depth()` | `LONG` | La profundidad (planos) elegida en el último dialog_screen_mode |  |
| `dialog_font(title)` | `STRPTR` | Diálogo de fuentes: "nombre.font/tamaño", "" si se canceló |  |

## RTG (CyberGraphX / Picasso96)

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `rtg_available()` | `BOOL` | Mira si hay CyberGraphX o Picasso96 |  |
| `rtg_is_active()` | `BOOL` | Mira si la pantalla actual es RTG |  |
| `rtg_get_depth()` | `LONG` | La profundidad en bits de la pantalla actual (la del programa, o si no la del Workbench: también fuera del dibujo de un desktop_canvas) |  |
| `rtg_get_width()` | `LONG` | El ancho de la pantalla actual (la del programa, o si no la del Workbench: también fuera del dibujo de un desktop_canvas) |  |
| `rtg_get_height()` | `LONG` | El alto de la pantalla actual (la del programa, o si no la del Workbench: también fuera del dibujo de un desktop_canvas) |  |
| `rtg_alloc_bitmap(width, height, depth)` | `APTR` | Pide un bitmap que vale para RTG |  |
| `rtg_free_bitmap(bitmap)` | `void` | Libera un bitmap RTG |  |
| `rtg_write_pixel(x, y, rgb)` | `void` | Escribe un píxel con un color RGB de 24 bits |  |
| `rtg_read_pixel(x, y)` | `LONG` | Lee un píxel: su color RGB de 24 bits |  |
| `rtg_fill_rect(x, y, w, h, rgb)` | `void` | Rellena un rectángulo con un color RGB de 24 bits |  |
| `rtg_write_array(buffer, bpr, x, y, w, h)` | `void` | Escribe un bloque de píxeles (el búfer es ARGB de 32 bits; bpr, los bytes por fila) |  |
| `rtg_read_array(buffer, bpr, x, y, w, h)` | `void` | Lee un bloque de píxeles de la pantalla a un búfer |  |
| `rtg_rgb(r, g, b)` | `LONG` | Un color RGB de 24 bits a partir de sus componentes |  |
| `rtg_argb(a, r, g, b)` | `LONG` | Un color ARGB de 32 bits a partir de sus componentes |  |
| `rtg_rgb_r(color)` | `LONG` | El componente rojo de un color RGB |  |
| `rtg_rgb_g(color)` | `LONG` | El componente verde de un color RGB |  |
| `rtg_rgb_b(color)` | `LONG` | El componente azul de un color RGB |  |
| `rtg_best_mode(width, height, depth)` | `LONG` | El mejor modo de pantalla RTG para ese tamaño |  |
| `rtg_open_screen(width, height, depth, title)` | `BOOL` | Abre una pantalla RTG del tamaño que se diga |  |
| `rtg_blit(src, sx, sy, dx, dy, w, h)` | `void` | Copia de un bitmap a la pantalla |  |
| `rtg_scale_blit(src, sx, sy, sw, sh, dx, dy, dw, dh)` | `void` | Copia de un bitmap a la pantalla cambiando el tamaño |  |

## MUI

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `mui_app_begin(title, base)` | `APTR` | Abre muimaster.library y crea la aplicación MUI (base: el nombre ARexx); 0 si no hay MUI o la CPU es un 68000 |  |
| `mui_text_editor(lines)` | `APTR` | Un campo de texto de varias líneas (el Textinput de MUI), de ese número de líneas de alto, con su barra: Return empieza otra línea; mui_get_text y mui_set_text lo leen y lo cambian, mui_on_ack da el evento de mandarlo (Amiga+Return en su ventana) |  |
| `mui_window_open_back(win)` | `LONG` | Abre una ventana sin hacerla la activa: el teclado se queda donde estaba; falso si no pudo abrirse |  |
| `mui_window_activate(win)` | `void` | Hace activa una ventana, delante de las demás (si está cerrada, la abre) |  |
| `mui_window_dispose(window)` | `void` | Cierra una ventana, la quita de la aplicación y la libera con todos sus objetos (y los menús contextuales hechos tras ella): para ventanas que se hacen una y otra vez (una vista previa). Nada con 0 o con una ventana que ya no está; sus objetos no se pueden usar después |  |
| `mui_request(window, title, text, buttons)` | `LONG` | Pregunta con la petición de MUI sobre una ventana (0: sobre la aplicación), con sus botones separados por "\|" ("_Guardar\|_Descartar\|_Cancelar"); las ventanas de la aplicación esperan. El botón elegido: 1, 2... desde la izquierda, 0 el último (también Esc) |  |
| `mui_set_background(obj, r, g, b)` | `void` | Un fondo RGB (0-255 cada uno) para un objeto: un grupo, un texto, una etiqueta, un botón, una lista (y la lista de dentro) o una ventana (su grupo raíz); los objetos de dentro lo toman si no tienen el suyo |  |
| `mui_set_text_pen(obj, r, g, b)` | `void` | El color (RGB, 0-255 cada uno) del texto de un texto, una etiqueta o un botón; mui_set_text lo mantiene |  |
| `mui_app_field_colors(r, g, b, active_r, active_g, active_b, cursor_r, cursor_g, cursor_b)` | `void` | El fondo (RGB, 0-255 cada uno) de todos los campos de texto de la aplicación (string, text_editor, combo), sin el cursor y con él, y el color del cursor; lo toman las ventanas que se abran después. El texto sigue negro: un gris en el que aún se lea, como 96, 96, 104 y 120, 120, 128 |  |
| `mui_app_rexx(app, func)` | `void` | Cada orden ARexx al puerto de la aplicación (su base y ".1": "BASE.1") que MUI no contesta por sí mismo (QUIT, SHOW, HIDE, INFO...) llama a f(orden: String) -> String con la línea entera: lo que devuelve es el RESULT, y mui_rexx_fail durante la llamada pone el RC. Se ejecuta mientras mui_wait_event espera |  |
| `mui_rexx_fail(rc)` | `void` | Desde la función de mui_app_rexx: el RC de la orden (5 aviso, 10 error, 20 fallo; entonces sin RESULT) |  |
| `mui_app_end()` | `void` | Deshace la aplicación con sus ventanas y objetos, y cierra MUI (también al acabar) |  |
| `mui_window_begin(title, id)` | `APTR` | Empieza una ventana (id 1-255: MUI recuerda su tamaño y su sitio; 0 ninguno) con un grupo raíz vertical |  |
| `mui_window_end()` | `void` | Acaba la ventana empezada con mui_window_begin |  |
| `mui_window_open(win)` | `LONG` | Abre una ventana; false si no se pudo |  |
| `mui_window_close(win)` | `void` | Cierra una ventana (sigue existiendo) |  |
| `mui_window_active(win)` | `LONG` | 1 si la ventana es la activa (varias ventanas de un .dashui comparten números de evento; dashweb D32) |  |
| `mui_vgroup_begin()` | `APTR` | Empieza un grupo vertical dentro del grupo abierto |  |
| `mui_hgroup_begin()` | `APTR` | Empieza un grupo horizontal dentro del grupo abierto |  |
| `mui_group_end()` | `void` | Acaba el grupo abierto |  |
| `mui_text(text)` | `APTR` | Un texto (con los códigos de texto de MUI) |  |
| `mui_button(label)` | `APTR` | Un botón (un guion bajo delante de una letra la hace su atajo de teclado) |  |
| `mui_on_press(obj, id)` | `void` | mui_wait_event da id cuando se pulsa el botón |  |
| `mui_on_close(win, id)` | `void` | mui_wait_event da id cuando se pulsa el botón de cerrar de la ventana (en la primera ventana, por defecto: -1) |  |
| `mui_press(obj)` | `void` | Envía el evento mui_on_press de un botón como si se hubiera pulsado |  |
| `mui_label(text)` | `APTR` | La etiqueta de una fila de un formulario (alineada a la derecha) |  |
| `mui_string(initial, maxlen)` | `APTR` | Un campo de texto de hasta maxlen caracteres |  |
| `mui_checkbox(checked)` | `APTR` | Una casilla |  |
| `mui_cycle(options)` | `APTR` | Un gadget de opciones que cambian al pulsarlo; opciones separadas por \| ("Uno\|Dos\|Tres") |  |
| `mui_slider(min, max, value)` | `APTR` | Un deslizador horizontal |  |
| `mui_gauge(max)` | `APTR` | Una barra de progreso de 0 a max |  |
| `mui_get_value(obj)` | `LONG` | El valor: casilla 1/0, opción elegida, nivel del deslizador, progreso, marca de menú 1/0 |  |
| `mui_set_value(obj, value)` | `void` | Cambia el valor (dispara mui_on_change como lo haría el usuario) |  |
| `mui_get_text(obj)` | `STRPTR` | El texto de un campo de texto, un texto, un botón o el título de una ventana |  |
| `mui_set_text(obj, text)` | `void` | Cambia el texto de un campo de texto, un texto, un botón, una opción de menú o el título de una ventana |  |
| `mui_set_enabled(obj, enabled)` | `void` | Activa o desactiva (en gris) un objeto, una opción de menú o un menú entero |  |
| `mui_on_change(obj, id)` | `void` | mui_wait_event da id cuando cambia el valor o el texto |  |
| `mui_on_ack(obj, id)` | `void` | mui_wait_event da id cuando se pulsa Return en un campo de texto (en un mui_combo, también al elegir una línea) |  |
| `mui_list()` | `APTR` | Una lista de textos con barra de desplazamiento; su valor es la línea elegida (-1 ninguna) |  |
| `mui_list_add(list, text)` | `void` | Añade una línea al final |  |
| `mui_list_insert(list, pos, text)` | `void` | Mete una línea en pos (0 = la primera) |  |
| `mui_list_remove(list, pos)` | `void` | Quita la línea de pos |  |
| `mui_list_clear(list)` | `void` | Quita todas las líneas |  |
| `mui_list_count(list)` | `LONG` | Cuántas líneas hay |  |
| `mui_list_get(list, pos)` | `STRPTR` | El texto de la línea de pos ("" fuera de la lista) |  |
| `mui_list_quiet(list, quiet)` | `void` | Mientras está callada, la lista no se redibuja (para añadir muchas líneas) |  |
| `mui_on_double(list, id)` | `void` | mui_wait_event da id con un doble clic en la lista |  |
| `mui_frame_begin(title, horizontal)` | `APTR` | Empieza un grupo con marco y un título ("" = ninguno) |  |
| `mui_columns_begin(columns)` | `APTR` | Empieza un grupo en rejilla con tantas columnas (formularios: etiqueta, campo...) |  |
| `mui_register_begin(titles)` | `APTR` | Empieza unas pestañas ("Una\|Dos"); cada hijo es una página; valor = la página que se ve |  |
| `mui_scroll_begin()` | `APTR` | Empieza una zona con barras de desplazamiento (contenido más grande que la ventana) |  |
| `mui_space()` | `APTR` | Un espacio vacío que ocupa lo que sobra |  |
| `mui_balance()` | `APTR` | Una barra que el usuario arrastra para repartir el sitio entre sus vecinos |  |
| `mui_weight(obj, weight)` | `void` | La parte del espacio libre que se lleva un objeto (100 por defecto) |  |
| `mui_set_visible(obj, visible)` | `void` | Enseña u oculta un objeto (la ventana se recoloca) |  |
| `mui_menu_begin(title)` | `APTR` | Empieza un menú de la ventana que se está haciendo |  |
| `mui_menu_item(title, key, id)` | `APTR` | Una opción de menú: key = la letra de Amiga+tecla ("" ninguna); mui_wait_event da id |  |
| `mui_menu_check(title, key, id, checked)` | `APTR` | Una opción de menú con marca: elegirla cambia la marca y mui_wait_event da id; mui_get_value / mui_set_value leen y ponen la marca |  |
| `mui_submenu_begin(title)` | `APTR` | Empieza un submenú en el menú que se está haciendo (un nivel): sus opciones van dentro hasta mui_submenu_end |  |
| `mui_submenu_end()` | `void` | Acaba el submenú |  |
| `mui_menu_separator()` | `void` | Una raya de separación en el menú |  |
| `mui_context_menu_begin(title)` | `APTR` | Empieza un menú contextual (en cualquier sitio, no solo en una ventana): sus opciones como en un menú (mui_menu_item, mui_menu_check, mui_submenu_begin...) hasta mui_menu_end; se da a un objeto con mui_set_context_menu (Lorraine D15) |  |
| `mui_set_context_menu(object, menu)` | `void` | El botón derecho sobre el objeto abre ese menú contextual (0: ninguno); sus opciones dan sus eventos; en un lienzo, mui_canvas_mouse_x/_y dicen dónde se pulsó y mui_canvas_button es 2 |  |
| `mui_menu_end()` | `void` | Acaba el menú |  |
| `mui_canvas(min_width, min_height)` | `APTR` | Una zona de dibujo (crece con la ventana); se dibuja desde mui_canvas_on_draw |  |
| `mui_canvas_on_draw(canvas, func)` | `void` | La función f(x, y, ancho, alto) que dibuja la zona con gfx_ (MUI la llama cuando hace falta) |  |
| `mui_canvas_on_input(canvas, id)` | `void` | mui_wait_event da id con un clic, la rueda o una tecla sobre la zona (llamarla antes de abrir la ventana) |  |
| `mui_canvas_redraw(canvas)` | `void` | Dibuja otra vez la zona ya |  |
| `mui_canvas_buffered(canvas, on)` | `void` | Dibuja la zona en un bitmap propio y la enseña de golpe al acabar (sin zona a medio dibujar; las mismas coordenadas; mui_canvas_update sigue dibujando en la ventana) |  |
| `mui_canvas_update(canvas)` | `void` | Llama ya a la función de dibujo sin borrar la zona (pinta solo lo que cambió) |  |
| `mui_canvas_update_area(canvas, x, y, w, h)` | `void` | Como mui_canvas_update, solo en la parte w x h en x, y de la zona (desde su esquina): el dibujo se recorta a ella y, con mui_canvas_buffered, solo ella pasa del búfer a la ventana |  |
| `mui_canvas_updating()` | `BOOL` | En la función de dibujo: true si corre por un mui_canvas_update (lo demás sigue ahí) |  |
| `mui_canvas_on_move(canvas, id)` | `void` | mui_wait_event da id cuando el puntero se mueve sobre la zona o sale de ella, sin clic (los movimientos que lleguen entretanto hacen uno; llamarla antes de abrir la ventana) |  |
| `mui_canvas_pointer_x(canvas)` | `LONG` | La X del puntero ahora, desde el borde izquierdo de la zona (con clic o sin él) |  |
| `mui_canvas_pointer_y(canvas)` | `LONG` | La Y del puntero ahora, desde el borde de arriba de la zona (con clic o sin él) |  |
| `mui_canvas_pointer_inside(canvas)` | `BOOL` | True si el puntero está ahora sobre la zona |  |
| `mui_canvas_set_pointer(canvas, shape)` | `void` | La forma del puntero sobre la zona: 0 normal, 1 texto (I), 2 cambiar de tamaño a los lados, 3 arriba y abajo, 4 ocupado; cambia ya si el puntero está sobre la zona (o arrastrándola) y vuelve a la normal fuera de ella (Lorraine D16) |  |
| `mui_canvas_take_tab(canvas, on)` | `void` | Con el puntero sobre la zona, Tab y Mayúsculas+Tab son teclas para ella (mui_canvas_key 66, Mayúsculas en mui_canvas_qualifiers; necesita mui_canvas_on_input) y no el gadget siguiente y anterior de la ventana; fuera de ella pasan de gadget en gadget como siempre (Lorraine D48) |  |
| `mui_canvas_mouse_x(canvas)` | `LONG` | La X del último clic o de la rueda, desde el borde izquierdo de la zona |  |
| `mui_canvas_mouse_y(canvas)` | `LONG` | La Y del último clic o de la rueda, desde el borde de arriba de la zona |  |
| `mui_canvas_button(canvas)` | `LONG` | 1 si lo último fue un clic izquierdo; si no, 0 |  |
| `mui_canvas_wheel(canvas)` | `LONG` | +1 / -1 si lo último fue la rueda del ratón (arriba/abajo); si no, 0 |  |
| `mui_canvas_key(canvas)` | `LONG` | El código en bruto de la última tecla; -1 si lo último no fue una tecla |  |
| `mui_canvas_on_drag(canvas, id)` | `void` | El id del evento cuando se arrastra la zona (moverse con el botón izquierdo pulsado tras pulsarlo en ella) y cuando se suelta; mui_canvas_drag dice cuál, mui_canvas_mouse_x/y dónde (puede ser fuera de la zona). Llamarla antes de abrir la ventana |  |
| `mui_canvas_drag(canvas)` | `LONG` | El último evento de arrastre: 1 moviéndose con el botón pulsado, 2 soltado (0 antes de ninguno) |  |
| `mui_canvas_qualifiers(canvas)` | `LONG` | Las teclas pulsadas en la última tecla, clic o rueda: 1 Mayúsculas, 2 Ctrl, 4 Alt, 8 Amiga, sumadas (Mayúsculas + Ctrl = 3); q & 1 dice si había Mayúsculas |  |
| `mui_canvas_char(canvas)` | `STRPTR` | El carácter de la última tecla en la zona, con las mayúsculas y el mapa de teclado ("" si no hay; dashweb D31) |  |
| `mui_scrollbar(vertical)` | `APTR` | Una barra de desplazamiento; su valor es la primera línea que se ve |  |
| `mui_set_range(scrollbar, total, visible)` | `void` | El tamaño del documento y de la parte que cabe |  |
| `mui_wait_event_signals(mask)` | `LONG` | Como mui_wait_event, pero también da 0 cuando llega una de las señales de mask (sockets...); mui_signals dice cuál |  |
| `mui_signals()` | `LONG` | Las señales de la máscara que despertaron al último mui_wait_event_signals |  |
| `mui_timer(ms, id)` | `void` | Dentro de ms milisegundos mui_wait_event da id, una vez (otra: llamarla otra vez; 0 la cancela) |  |
| `mui_image(file)` | `APTR` | Una imagen de un fichero con los datatypes (ILBM; PNG, JPEG, GIF si están sus datatypes); mui_set_text cambia el fichero |  |
| `mui_image_button(file)` | `APTR` | Un botón con una imagen (un icono de barra de herramientas; ILBM, o lo que lean los datatypes): mui_on_press como un botón, mui_set_text cambia la imagen |  |
| `mui_image_toggle(file, group, selected)` | `APTR` | Un botón con imagen que se queda pulsado (negrita, cursiva): valor 1/0 con mui_get_value / mui_set_value, mui_on_change cuando cambia; group > 0: pulsar uno suelta los demás de ese grupo (alineación), y mui_on_change solo salta en el pulsado |  |
| `mui_combo(text, options)` | `APTR` | Un campo de texto con una lista que se despliega (fuente, tamaño; opciones "A\|B"): se escribe o se elige una línea (doble clic); mui_get_text / mui_set_text, mui_list_* cambian las líneas, mui_on_ack con Return o al elegir una línea |  |
| `mui_help(obj, text)` | `void` | Una ayuda en burbuja que sale cuando el puntero se para sobre el objeto |  |
| `mui_window_move(win, dx, dy)` | `void` | Mueve una ventana abierta dx, dy píxeles (las ventanas de un .dashui se abren en el mismo sitio) |  |
| `mui_set_active(win, obj)` | `void` | Hace de obj el objeto activo de la ventana: el cursor va a ese campo de texto (Amiga-L) |  |
| `mui_window_size(win, width_pct, height_pct)` | `void` | El tamaño de la ventana al abrirse, en tanto por ciento de la pantalla visible, centrada (antes de mui_window_open) |  |
| `mui_window_fullscreen(win)` | `void` | La ventana ocupa toda la pantalla: sin bordes, barra de título ni gadgets, y activa (antes de mui_window_open) |  |
| `mui_window_screen(win, name)` | `BOOL` | La ventana se abre como una ventana normal en la pantalla pública con ese nombre (la de screen_clone_wb, o la de otro programa); antes de mui_window_open; falso si no existe esa pantalla |  |
| `mui_window_own_screen(win)` | `BOOL` | Pantalla completa en una pantalla propia, como la pública (antes de mui_window_open; false: en la pública) |  |
| `mui_width(obj)` | `LONG` | El ancho de un objeto en la pantalla en píxeles (0 antes de abrirse su ventana) |  |
| `mui_height(obj)` | `LONG` | El alto de un objeto en la pantalla en píxeles (0 antes de abrirse su ventana) |  |
| `mui_wait_event()` | `LONG` | Espera el siguiente evento y da su número; -1 para salir |  |
| `mui_poll_event()` | `LONG` | Como mui_wait_event sin esperar: 0 si no hay evento |  |
