# Dash Language - API Completa de Amiga

*[English](AMIGA_API.en.md) | Castellano*

Catálogo de diseño de las funciones built-in para AmigaOS.

> **Ojo:** este documento es el diseño original (enero de 2026) y no dice lo que hay. La lista real, generada
> desde el código, está en [BUILTINS.md](BUILTINS.md): hoy 680 builtins, todos implementados.
> En las tablas, **No existe** marca los nombres que no están en Dash y **Hoy** lo que acabó distinto (otro
> nombre u otros argumentos). Muchos recursos van por número (`id`), no por un objeto devuelto. Las filas sin
> marca existen con ese nombre y esos argumentos.

---

## 1. GRAPHICS - Dibujo 2D

### 1.1 Colores y Modos
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `gfx_pen(color)` | `SetAPen()` | Color de dibujo principal (0-255) |
| `gfx_pen_bg(color)` | `SetBPen()` | Color de fondo |
| `gfx_pen_outline(color)` | `SetOPen()` | Color de contorno para áreas |
| `gfx_mode(mode)` | `SetDrMd()` | Modo: MODE_JAM1, MODE_JAM2, MODE_COMP, MODE_INV |
| `gfx_pattern(pattern)` | `SetDrPt()` | Patrón de línea (16 bits) |
| `gfx_rgb(index, r, g, b)` | `SetRGB4()` | Definir color en paleta (0-15 cada componente) |
| `gfx_rgb8(index, r, g, b)` | `SetRGB32()` | Definir color 24-bit (AGA) |

### 1.2 Primitivas Básicas
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `gfx_move(x, y)` | `Move()` | Mover cursor gráfico |
| `gfx_draw(x, y)` | `Draw()` | Línea desde cursor hasta punto |
| `gfx_line(x1, y1, x2, y2)` | `Move()+Draw()` | Línea entre dos puntos |
| `gfx_pixel(x, y)` | `WritePixel()` | Dibujar pixel |
| `gfx_pixel_read(x, y)` | `ReadPixel()` | Leer color de pixel |
| `gfx_rect(x1, y1, x2, y2)` | `RectFill()` | Rectángulo relleno |
| `gfx_box(x1, y1, x2, y2)` | `Move()+Draw()` | Rectángulo solo borde |
| `gfx_ellipse(cx, cy, rx, ry)` | `DrawEllipse()` | Elipse/círculo contorno |
| `gfx_ellipse_fill(cx, cy, rx, ry)` | `AreaEllipse()+AreaEnd()` | Elipse rellena |
| `gfx_circle(cx, cy, r)` | `DrawEllipse(r,r)` | Círculo contorno |
| `gfx_circle_fill(cx, cy, r)` | `AreaEllipse()+AreaEnd()` | Círculo relleno |
| `gfx_flood(x, y, mode)` | `Flood()` | Relleno por inundación |

### 1.3 Texto
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `gfx_text(str)` | `Text()` | Escribir texto en cursor |
| `gfx_text_at(x, y, str)` | `Move()+Text()` | Texto en posición |
| `gfx_text_len(str)` | `TextLength()` | Ancho en pixels |
| `gfx_font(name, size)` | `OpenFont()+SetFont()` | Cambiar fuente · **No existe.** Hoy: `font_open(nombre, tamaño)` y `font_use(f)` |

### 1.4 Limpieza y Scroll
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `gfx_clear()` | `SetRast(rp, 0)` | Limpiar con color 0 |
| `gfx_clear_color(color)` | `SetRast()` | Limpiar con color |
| `gfx_scroll(dx, dy, x1, y1, x2, y2)` | `ScrollRaster()` | Scroll región |

### 1.5 Áreas (Polígonos)
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `gfx_poly_begin(x, y)` | `AreaMove()` | Iniciar polígono |
| `gfx_poly_add(x, y)` | `AreaDraw()` | Añadir vértice |
| `gfx_poly_end()` | `AreaEnd()` | Cerrar y rellenar |

### 1.6 Blitting
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `gfx_copy(sx, sy, w, h, dx, dy)` | `ClipBlit()` | Copiar región en ventana |
| `gfx_blit(bitmap, sx, sy, dx, dy, w, h)` | `BltBitMapRastPort()` | Blit desde bitmap · **No existe.** Hoy: `bitmap_blit(id, sx, sy, w, h, dx, dy)` |

---

## 2. GRAPHICS AVANZADO

### 2.1 Bitmaps
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `bitmap_create(w, h, depth)` | `AllocBitMap()` | Crear bitmap vacío · **Hoy:** `bitmap_create(id, w, h, depth)` (por número) |
| `bitmap_free(bm)` | `FreeBitMap()` | Liberar bitmap · **Hoy:** `bitmap_free(id)` |
| `bitmap_load(filename)` | `LoadIFF()` | Cargar imagen IFF/ILBM · **Hoy:** `bitmap_load(id, fichero)` |
| `bitmap_save(bm, filename)` | `SaveIFF()` | Guardar como IFF · **Hoy:** `bitmap_save(id, fichero)` |
| `bitmap_width(bm)` | `GetBitMapAttr()` | Ancho · **No existe.** (las imágenes de datatypes sí: `image_width`) |
| `bitmap_height(bm)` | `GetBitMapAttr()` | Alto · **No existe.** (las imágenes de datatypes sí: `image_height`) |
| `bitmap_depth(bm)` | `GetBitMapAttr()` | Profundidad · **No existe.** |

### 2.2 Sprites (Hardware)
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `sprite_create(height)` | `AllocSpriteData()` | Crear sprite · **Hoy:** `sprite_create(id, ancho, alto)` (por número); también `sprite_load(id, fichero)` |
| `sprite_free(spr)` | `FreeSpriteData()` | Liberar sprite · **Hoy:** `sprite_free(id)` |
| `sprite_get()` | `GetSprite()` | Obtener canal de sprite · **No existe.** Los sprites van por número (`id`) |
| `sprite_release(num)` | `FreeSprite()` | Liberar canal · **No existe.** Los sprites van por número (`id`) |
| `sprite_move(num, x, y)` | `MoveSprite()` | Mover sprite · **No existe.** Hoy: `sprite_pos(id, x, y)`, `sprite_show(id)`, `sprite_hide(id)` |
| `sprite_color(num, idx, r, g, b)` | `SetRGB4()` | Color de sprite · **Hoy:** `sprite_color(id, índice, r, g, b)` |
| `sprite_data(spr, line, word1, word2)` | Direct | Definir línea de sprite · **No existe.** Hoy: `sprite_set_row(id, fila, plano0, plano1)` |
| `sprite_attach(spr1, spr2)` | `ChangeSprite()` | Unir sprites (16 colores) · **No existe.** |

### 2.3 BOBs (Blitter Objects)
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `bob_create(w, h, depth)` | `AllocVSprite()` | Crear BOB · **Hoy:** `bob_create(id, w, h, depth)` (por número); también `bob_load(id, fichero)` |
| `bob_free(bob)` | `FreeVSprite()` | Liberar BOB · **Hoy:** `bob_free(id)` |
| `bob_image(bob, bitmap)` | Setup ImageData | Asignar imagen · **No existe.** Hoy: `bob_load(id, fichero)` y `bob_frame(id, marco)` |
| `bob_pos(bob, x, y)` | Set X, Y | Posicionar · **Hoy:** `bob_pos(id, x, y)` |
| `bob_add(bob)` | `AddBob()` | Añadir a lista · **No existe.** Hoy: `bob_draw(id)` |
| `bob_remove(bob)` | `RemBob()` | Quitar de lista · **No existe.** Hoy: `bob_erase(id)` (repone el fondo) |
| `bob_draw_all()` | `DrawGList()+SortGList()` | Dibujar todos · **No existe.** Cada BOB se dibuja con `bob_draw(id)` |
| `bob_collision(bob1, bob2)` | `DoCollision()` | Detectar colisión · **Hoy:** `bob_collision(id1, id2)` |

### 2.4 Double Buffering
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `gfx_buffer_create()` | `AllocDBufInfo()` | Crear doble buffer · **No existe.** El doble buffer está en `lib/amiga/doublebuf.dash` (`dbuf_new`) |
| `gfx_buffer_free(db)` | `FreeDBufInfo()` | Liberar · **No existe.** Hoy: `dbuf_del` de `lib/amiga/doublebuf.dash` |
| `gfx_flip()` | `ChangeVPBitMap()` | Intercambiar buffers · **No existe.** Hoy: `dbuf_swap` de `lib/amiga/doublebuf.dash` |
| `gfx_wait_blit()` | `WaitBlit()` | Esperar fin de blit · **No existe.** Hoy: `wait_blit()` |
| `gfx_wait_tof()` | `WaitTOF()` | Esperar vertical blank · **No existe.** Hoy: `wait_vblank()` |

### 2.5 Copper
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `copper_create(size)` | `UCopperListInit()` | Crear lista copper · **Hoy:** una sola lista, sin `cl` en las demás funciones |
| `copper_free(cl)` | `FreeCopList()` | Liberar · **Hoy:** `copper_free()` |
| `copper_wait(cl, x, y)` | `CWAIT()` | Esperar posición · **Hoy:** `copper_wait(y, x)` |
| `copper_move(cl, reg, value)` | `CMOVE()` | Escribir registro · **Hoy:** `copper_move(reg, valor)`; también `copper_color(índice, rgb)` |
| `copper_end(cl)` | `CEND()` | Terminar lista · **Hoy:** `copper_end()` |
| `copper_install(cl)` | viewport->UCopIns | Instalar · **Hoy:** `copper_install()` |

---

## 3. DOS - Archivos y Sistema

### 3.1 Archivos
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `file_open(path, mode)` | `Open()` | Abrir archivo (MODE_READ, MODE_WRITE, MODE_APPEND) · **Hoy:** modos 1005 (leer), 1006 (nuevo) y 1004 (leer y escribir); `MODE_APPEND` no existe |
| `file_close(fh)` | `Close()` | Cerrar archivo |
| `file_read(fh, size)` | `Read()` | Leer bytes, retorna string · **Hoy:** `file_read(fh, buffer, n)`, a un buffer de `buffer_alloc`; un fichero de texto entero: `file_read_text(ruta)` |
| `file_read_line(fh)` | `FGets()` | Leer línea · **Hoy:** `file_read_line(fh, buffer, max)` |
| `file_write(fh, data)` | `Write()` | Escribir datos · **Hoy:** `file_write(fh, buffer, n)`; un texto: `file_print(fh, texto)` o `file_write_text(ruta, texto)` |
| `file_write_line(fh, str)` | `FPuts()` | Escribir línea |
| `file_seek(fh, pos, mode)` | `Seek()` | Mover posición |
| `file_pos(fh)` | `Seek(0, OFFSET_CURRENT)` | Posición actual |
| `file_size(fh)` | `Seek()` trick | Tamaño de archivo · **Hoy:** `file_size(ruta)`, con el nombre del fichero |
| `file_eof(fh)` | Check | ¿Fin de archivo? |

### 3.2 Sistema de Archivos
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `file_exists(path)` | `Lock()+UnLock()` | ¿Existe archivo? |
| `file_delete(path)` | `DeleteFile()` | Borrar archivo |
| `file_rename(old, new)` | `Rename()` | Renombrar |
| `file_copy(src, dst)` | Read+Write | Copiar archivo |
| `dir_create(path)` | `CreateDir()` | Crear directorio |
| `dir_delete(path)` | `DeleteFile()` | Borrar directorio vacío · **No existe.** `file_delete(ruta)` usa `DeleteFile()`, que también borra un directorio vacío |
| `dir_list(path)` | `Examine()+ExNext()` | Listar directorio → array · **No existe.** |
| `dir_current()` | `GetCurrentDirName()` | Directorio actual |
| `dir_change(path)` | `CurrentDir()` | Cambiar directorio |

### 3.3 Consola/CLI
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `print(str)` | `Printf()` | Ya implementado · **No existe.** como función: es la instrucción `Print x` |
| `input(prompt)` | `FGets(stdin)` | Leer entrada de usuario · **No existe.** Hoy: `console_read(buffer, max)` |
| `cls()` | `Printf("\033[2J")` | Limpiar consola · **No existe.** |

---

## 4. AUDIO - Sonido

### 4.1 Samples
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `sample_load(filename)` | LoadIFF 8SVX | Cargar sample IFF · **No existe.** Hoy: `sound_load(id, fichero)` |
| `sample_free(smp)` | `FreeMem()` | Liberar sample · **No existe.** Hoy: `sound_free(id)` |
| `sample_create(size)` | `AllocMem(CHIP)` | Crear buffer · **No existe.** Hoy: `sound_create(id, muestras, frecuencia)` |
| `sample_data(smp, offset, value)` | Direct | Escribir dato · **No existe.** Hoy: `sound_sample(id, i, valor)` |

### 4.2 Canales (Paula)
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `audio_play(channel, sample)` | audio.device | Reproducir en canal 0-3 · **No existe.** Hoy: `sound_play(id, canal)` |
| `audio_stop(channel)` | audio.device | Parar canal · **No existe.** Hoy: `sound_stop(canal)` |
| `audio_volume(channel, vol)` | AUDxVOL | Volumen 0-64 · **No existe.** Hoy: `sound_volume(canal, vol)` |
| `audio_period(channel, period)` | AUDxPER | Frecuencia · **No existe.** Hoy: `sound_period(canal, periodo)` |
| `audio_loop(channel, enable)` | Setup | Loop on/off · **No existe.** Hoy: `sound_loop(id, canal)` |
| `audio_wait(channel)` | Wait | Esperar fin · **No existe.** `sound_playing(canal)` dice si aún suena |

### 4.3 Música (MOD)
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `mod_load(filename)` | ptplayer | Cargar módulo ProTracker · **No existe.** Hoy: `music_load(fichero)` |
| `mod_free(mod)` | ptplayer | Liberar · **No existe.** Hoy: `music_free()` |
| `mod_play(mod)` | ptplayer | Reproducir · **No existe.** Hoy: `music_play()` |
| `mod_stop()` | ptplayer | Parar · **No existe.** Hoy: `music_stop()` |
| `mod_pause()` | ptplayer | Pausar · **No existe.** Hoy: `music_pause()` |
| `mod_resume()` | ptplayer | Continuar · **No existe.** Hoy: `music_resume()` |
| `mod_position(pos)` | ptplayer | Ir a posición · **No existe.** Hoy: `music_position(pos)` |
| `mod_volume(vol)` | ptplayer | Volumen master · **No existe.** Hoy: `music_volume(vol)` |

---

## 5. INPUT - Entrada

### 5.1 Teclado
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `key_pressed()` | IDCMP_RAWKEY | ¿Hay tecla? → bool |
| `key_get()` | GetMsg | Obtener código de tecla |
| `key_wait()` | WaitPort | Esperar tecla |
| `key_state(keycode)` | Direct hardware | ¿Tecla presionada? · **No existe.** |

### 5.2 Mouse
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `mouse_x()` | IntuiMessage | Posición X |
| `mouse_y()` | IntuiMessage | Posición Y |
| `mouse_button(btn)` | IntuiMessage | Estado botón (0=izq, 1=der, 2=medio) · **Hoy:** 0 = izquierdo, 1 = derecho |
| `mouse_click()` | IDCMP_MOUSEBUTTONS | Esperar click · **No existe.** Hoy: `wait_click()`, o `On Click` en un `EventLoop` |

### 5.3 Joystick
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `joy_x(port)` | gameport/hardware | Dirección X (-1, 0, 1) |
| `joy_y(port)` | gameport/hardware | Dirección Y (-1, 0, 1) |
| `joy_button(port)` | hardware | Botón presionado |
| `joy_up(port)` | hardware | Arriba |
| `joy_down(port)` | hardware | Abajo |
| `joy_left(port)` | hardware | Izquierda |
| `joy_right(port)` | hardware | Derecha |
| `joy_fire(port)` | hardware | Disparo |

---

## 6. INTUITION - GUI Ampliado

### 6.1 Ventanas (extendido)
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `win.open` | Ya implementado | Abrir ventana |
| `win.close` | `CloseWindow()` | Cerrar ventana |
| `win.title(str)` | `SetWindowTitles()` | Cambiar título · **No existe.** Hoy: `window_title(h, texto)` (h 0: la ventana actual) |
| `win.size(w, h)` | `SizeWindow()` | Redimensionar · **No existe.** Hoy: `window_resize(h, w, alto)` |
| `win.move(x, y)` | `MoveWindow()` | Mover · **No existe.** Hoy: `window_move(h, x, y)` |
| `win.to_front()` | `WindowToFront()` | Traer al frente · **No existe.** Hoy: `window_to_front(h)` |
| `win.to_back()` | `WindowToBack()` | Enviar atrás · **No existe.** Hoy: `window_to_back(h)` |
| `win.activate()` | `ActivateWindow()` | Activar · **No existe.** Hoy: `window_activate(h)` |

### 6.2 Requesters
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `alert(text)` | `EasyRequest()` | Alerta simple · No es builtin: `alert(título, texto)` de `lib/amiga/intuition.dash` |
| `confirm(text)` | `EasyRequest()` | Sí/No → bool · No es builtin: `confirm(título, texto)` de `lib/amiga/intuition.dash` |
| `ask(text, options)` | `EasyRequest()` | Múltiples opciones · No es builtin: `ask(título, texto, botones)` de `lib/amiga/intuition.dash` |
| `file_requester(title, pattern)` | ASL | Selector de archivos · **No existe.** Hoy: `dialog_file(título, patrón, guardar)` |
| `dir_requester(title)` | ASL | Selector de directorio · **No existe.** |
| `font_requester(title)` | ASL | Selector de fuente · **No existe.** Hoy: `dialog_font(título)` |
| `color_requester(title)` | ASL | Selector de color · **No existe.** Hoy: `dialog_color(título, inicial)` (una paleta propia, no ASL) |

### 6.3 Menús
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `menu_create()` | `CreateMenus()` | Crear estructura · **No existe.** Hoy: `menu_title(texto)` y `menu_item(...)` en orden |
| `menu_add(menu, title)` | Setup | Añadir menú · **No existe.** Hoy: `menu_title(texto)` |
| `menu_item(menu, label, shortcut)` | Setup | Añadir item · **Hoy:** `menu_item(texto, atajo, id)`; submenús con `menu_sub` |
| `menu_separator(menu)` | NM_BARLABEL | Separador · **Hoy:** `menu_separator()` |
| `menu_attach(win, menu)` | `SetMenuStrip()` | Asociar a ventana · **Hoy:** `menu_attach()`, tras definir los menús |
| `menu_remove(win)` | `ClearMenuStrip()` | Quitar · **No existe.** |
| `menu_selected()` | IDCMP_MENUPICK | Item seleccionado · **No existe.** Hoy: `menu_id()` en `On Menu`, o `menu_event()` |

### 6.4 Gadgets (Controles)
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `button_create(x, y, w, h, label)` | GadTools | Crear botón · **Hoy:** `button_create(win, x, y, w, h, texto)`: la ventana delante; el gadget es un número (`On Gadget`) |
| `checkbox_create(x, y, label)` | GadTools | Checkbox · **Hoy:** `checkbox_create(win, x, y, texto)` |
| `checkbox_get(gad)` | GT_GetGadgetAttrs | Estado |
| `radio_create(x, y, labels[])` | GadTools | Radio buttons · **Hoy:** `radio_create(win, x, y, "a|b|c")` |
| `radio_get(gad)` | GT_GetGadgetAttrs | Seleccionado |
| `slider_create(x, y, w, min, max)` | GadTools | Slider · **Hoy:** `slider_create(win, x, y, w, h, min, max, valor)` |
| `slider_get(gad)` | GT_GetGadgetAttrs | Valor |
| `slider_set(gad, val)` | GT_SetGadgetAttrs | Establecer |
| `text_input_create(x, y, w, maxlen)` | GadTools | Campo de texto · **No existe.** Hoy: `gt_string(x, y, w, h, etiqueta, inicial, max)` (o `mui_string`) |
| `text_input_get(gad)` | GT_GetGadgetAttrs | Contenido · **No existe.** Hoy: `gt_get_string(id)` |
| `text_input_set(gad, str)` | GT_SetGadgetAttrs | Establecer · **No existe.** |
| `listview_create(x, y, w, h)` | GadTools | Lista · **Hoy:** `listview_create(win, x, y, w, h)` |
| `listview_add(gad, item)` | GT_SetGadgetAttrs | Añadir item |
| `listview_clear(gad)` | GT_SetGadgetAttrs | Limpiar |
| `listview_selected(gad)` | GT_GetGadgetAttrs | Item seleccionado |

---

## 7. SISTEMA

### 7.1 Memoria
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `mem_chip_free()` | `AvailMem(CHIP)` | Chip RAM libre |
| `mem_fast_free()` | `AvailMem(FAST)` | Fast RAM libre |
| `mem_total()` | `AvailMem(TOTAL)` | Total disponible |

### 7.2 Tiempo
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `time_ticks()` | `ReadEClock()` | Ticks de sistema · **No existe.** Hoy: `time_ms()` (milisegundos desde que arrancó el programa) |
| `time_delay(seconds)` | `Delay()` | Esperar segundos · **Hoy:** en ticks (50 por segundo) |
| `time_delay_ms(ms)` | `Delay()` | Esperar milisegundos |
| `time_date()` | `DateStamp()` | Fecha/hora actual · **No existe.** Hoy: `clock_read()`, `clock_year()`... y `date_text(formato)` |

### 7.3 Misc
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `random()` | Custom | Número aleatorio |
| `random_range(min, max)` | Custom | Aleatorio en rango |
| `random_seed(seed)` | Custom | Semilla |
| `version_os()` | `SysBase->LibNode` | Versión AmigaOS · **No existe.** |
| `version_cpu()` | `SysBase->AttnFlags` | Tipo de CPU · **No existe.** |

---

## Constantes

> **Ojo:** Dash no trae estas constantes. Solo existen `MODE_READ` (1005), `MODE_WRITE` (1006) y
> `MODE_READWRITE` (1004), con `import "lib/amiga/dos.dash"`; `MODE_APPEND` no existe. Lo demás se escribe
> con su número (por ejemplo `file_open("f", 1005)`). En `On Key` las teclas van por nombre: `On Key "ESC"`.

```ruby
# Modos de dibujo
MODE_JAM1 = 0
MODE_JAM2 = 1
MODE_COMP = 2
MODE_INV = 4

# Modos de archivo
MODE_READ = 1005
MODE_WRITE = 1006
MODE_APPEND = 1007

# Teclas especiales
KEY_UP = 76
KEY_DOWN = 77
KEY_LEFT = 79
KEY_RIGHT = 78
KEY_SPACE = 64
KEY_RETURN = 68
KEY_ESC = 69
KEY_F1 = 80
# ... etc

# Puertos de joystick
JOY_PORT1 = 0
JOY_PORT2 = 1
```

---

## Resumen

| Módulo | Funciones |
|--------|-----------|
| Graphics básico | 28 |
| Graphics avanzado | 32 |
| DOS | 22 |
| Audio | 18 |
| Input | 16 |
| Intuition | 35 |
| Sistema | 10 |
| **TOTAL** | **~161 funciones** |

Eso era el plan. Hoy Dash tiene **680 builtins**, todos implementados; 90 son de MUI. Hay más de lo que preveía
este diseño: GadTools, ReAction y MUI, red (TCP cliente y servidor, UDP, TLS con AmiSSL, drivers SANA-II),
imágenes por datatypes, fuentes, RTG, tareas, commodities, catálogos de idioma, fecha y hora... La lista real,
con lo que hace cada una, está en [BUILTINS.md](BUILTINS.md).
