# Dash Language - API Completa de Amiga

Catálogo completo de funciones built-in para AmigaOS.

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
| `gfx_font(name, size)` | `OpenFont()+SetFont()` | Cambiar fuente |

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
| `gfx_blit(bitmap, sx, sy, dx, dy, w, h)` | `BltBitMapRastPort()` | Blit desde bitmap |

---

## 2. GRAPHICS AVANZADO

### 2.1 Bitmaps
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `bitmap_create(w, h, depth)` | `AllocBitMap()` | Crear bitmap vacío |
| `bitmap_free(bm)` | `FreeBitMap()` | Liberar bitmap |
| `bitmap_load(filename)` | `LoadIFF()` | Cargar imagen IFF/ILBM |
| `bitmap_save(bm, filename)` | `SaveIFF()` | Guardar como IFF |
| `bitmap_width(bm)` | `GetBitMapAttr()` | Ancho |
| `bitmap_height(bm)` | `GetBitMapAttr()` | Alto |
| `bitmap_depth(bm)` | `GetBitMapAttr()` | Profundidad |

### 2.2 Sprites (Hardware)
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `sprite_create(height)` | `AllocSpriteData()` | Crear sprite |
| `sprite_free(spr)` | `FreeSpriteData()` | Liberar sprite |
| `sprite_get()` | `GetSprite()` | Obtener canal de sprite |
| `sprite_release(num)` | `FreeSprite()` | Liberar canal |
| `sprite_move(num, x, y)` | `MoveSprite()` | Mover sprite |
| `sprite_color(num, idx, r, g, b)` | `SetRGB4()` | Color de sprite |
| `sprite_data(spr, line, word1, word2)` | Direct | Definir línea de sprite |
| `sprite_attach(spr1, spr2)` | `ChangeSprite()` | Unir sprites (16 colores) |

### 2.3 BOBs (Blitter Objects)
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `bob_create(w, h, depth)` | `AllocVSprite()` | Crear BOB |
| `bob_free(bob)` | `FreeVSprite()` | Liberar BOB |
| `bob_image(bob, bitmap)` | Setup ImageData | Asignar imagen |
| `bob_pos(bob, x, y)` | Set X, Y | Posicionar |
| `bob_add(bob)` | `AddBob()` | Añadir a lista |
| `bob_remove(bob)` | `RemBob()` | Quitar de lista |
| `bob_draw_all()` | `DrawGList()+SortGList()` | Dibujar todos |
| `bob_collision(bob1, bob2)` | `DoCollision()` | Detectar colisión |

### 2.4 Double Buffering
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `gfx_buffer_create()` | `AllocDBufInfo()` | Crear doble buffer |
| `gfx_buffer_free(db)` | `FreeDBufInfo()` | Liberar |
| `gfx_flip()` | `ChangeVPBitMap()` | Intercambiar buffers |
| `gfx_wait_blit()` | `WaitBlit()` | Esperar fin de blit |
| `gfx_wait_tof()` | `WaitTOF()` | Esperar vertical blank |

### 2.5 Copper
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `copper_create(size)` | `UCopperListInit()` | Crear lista copper |
| `copper_free(cl)` | `FreeCopList()` | Liberar |
| `copper_wait(cl, x, y)` | `CWAIT()` | Esperar posición |
| `copper_move(cl, reg, value)` | `CMOVE()` | Escribir registro |
| `copper_end(cl)` | `CEND()` | Terminar lista |
| `copper_install(cl)` | viewport->UCopIns | Instalar |

---

## 3. DOS - Archivos y Sistema

### 3.1 Archivos
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `file_open(path, mode)` | `Open()` | Abrir archivo (MODE_READ, MODE_WRITE, MODE_APPEND) |
| `file_close(fh)` | `Close()` | Cerrar archivo |
| `file_read(fh, size)` | `Read()` | Leer bytes, retorna string |
| `file_read_line(fh)` | `FGets()` | Leer línea |
| `file_write(fh, data)` | `Write()` | Escribir datos |
| `file_write_line(fh, str)` | `FPuts()` | Escribir línea |
| `file_seek(fh, pos, mode)` | `Seek()` | Mover posición |
| `file_pos(fh)` | `Seek(0, OFFSET_CURRENT)` | Posición actual |
| `file_size(fh)` | `Seek()` trick | Tamaño de archivo |
| `file_eof(fh)` | Check | ¿Fin de archivo? |

### 3.2 Sistema de Archivos
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `file_exists(path)` | `Lock()+UnLock()` | ¿Existe archivo? |
| `file_delete(path)` | `DeleteFile()` | Borrar archivo |
| `file_rename(old, new)` | `Rename()` | Renombrar |
| `file_copy(src, dst)` | Read+Write | Copiar archivo |
| `dir_create(path)` | `CreateDir()` | Crear directorio |
| `dir_delete(path)` | `DeleteFile()` | Borrar directorio vacío |
| `dir_list(path)` | `Examine()+ExNext()` | Listar directorio → array |
| `dir_current()` | `GetCurrentDirName()` | Directorio actual |
| `dir_change(path)` | `CurrentDir()` | Cambiar directorio |

### 3.3 Consola/CLI
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `print(str)` | `Printf()` | Ya implementado |
| `input(prompt)` | `FGets(stdin)` | Leer entrada de usuario |
| `cls()` | `Printf("\033[2J")` | Limpiar consola |

---

## 4. AUDIO - Sonido

### 4.1 Samples
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `sample_load(filename)` | LoadIFF 8SVX | Cargar sample IFF |
| `sample_free(smp)` | `FreeMem()` | Liberar sample |
| `sample_create(size)` | `AllocMem(CHIP)` | Crear buffer |
| `sample_data(smp, offset, value)` | Direct | Escribir dato |

### 4.2 Canales (Paula)
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `audio_play(channel, sample)` | audio.device | Reproducir en canal 0-3 |
| `audio_stop(channel)` | audio.device | Parar canal |
| `audio_volume(channel, vol)` | AUDxVOL | Volumen 0-64 |
| `audio_period(channel, period)` | AUDxPER | Frecuencia |
| `audio_loop(channel, enable)` | Setup | Loop on/off |
| `audio_wait(channel)` | Wait | Esperar fin |

### 4.3 Música (MOD)
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `mod_load(filename)` | ptplayer | Cargar módulo ProTracker |
| `mod_free(mod)` | ptplayer | Liberar |
| `mod_play(mod)` | ptplayer | Reproducir |
| `mod_stop()` | ptplayer | Parar |
| `mod_pause()` | ptplayer | Pausar |
| `mod_resume()` | ptplayer | Continuar |
| `mod_position(pos)` | ptplayer | Ir a posición |
| `mod_volume(vol)` | ptplayer | Volumen master |

---

## 5. INPUT - Entrada

### 5.1 Teclado
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `key_pressed()` | IDCMP_RAWKEY | ¿Hay tecla? → bool |
| `key_get()` | GetMsg | Obtener código de tecla |
| `key_wait()` | WaitPort | Esperar tecla |
| `key_state(keycode)` | Direct hardware | ¿Tecla presionada? |

### 5.2 Mouse
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `mouse_x()` | IntuiMessage | Posición X |
| `mouse_y()` | IntuiMessage | Posición Y |
| `mouse_button(btn)` | IntuiMessage | Estado botón (0=izq, 1=der, 2=medio) |
| `mouse_click()` | IDCMP_MOUSEBUTTONS | Esperar click |

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
| `win.title(str)` | `SetWindowTitles()` | Cambiar título |
| `win.size(w, h)` | `SizeWindow()` | Redimensionar |
| `win.move(x, y)` | `MoveWindow()` | Mover |
| `win.to_front()` | `WindowToFront()` | Traer al frente |
| `win.to_back()` | `WindowToBack()` | Enviar atrás |
| `win.activate()` | `ActivateWindow()` | Activar |

### 6.2 Requesters
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `alert(text)` | `EasyRequest()` | Alerta simple |
| `confirm(text)` | `EasyRequest()` | Sí/No → bool |
| `ask(text, options)` | `EasyRequest()` | Múltiples opciones |
| `file_requester(title, pattern)` | ASL | Selector de archivos |
| `dir_requester(title)` | ASL | Selector de directorio |
| `font_requester(title)` | ASL | Selector de fuente |
| `color_requester(title)` | ASL | Selector de color |

### 6.3 Menús
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `menu_create()` | `CreateMenus()` | Crear estructura |
| `menu_add(menu, title)` | Setup | Añadir menú |
| `menu_item(menu, label, shortcut)` | Setup | Añadir item |
| `menu_separator(menu)` | NM_BARLABEL | Separador |
| `menu_attach(win, menu)` | `SetMenuStrip()` | Asociar a ventana |
| `menu_remove(win)` | `ClearMenuStrip()` | Quitar |
| `menu_selected()` | IDCMP_MENUPICK | Item seleccionado |

### 6.4 Gadgets (Controles)
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `button_create(x, y, w, h, label)` | GadTools | Crear botón |
| `checkbox_create(x, y, label)` | GadTools | Checkbox |
| `checkbox_get(gad)` | GT_GetGadgetAttrs | Estado |
| `radio_create(x, y, labels[])` | GadTools | Radio buttons |
| `radio_get(gad)` | GT_GetGadgetAttrs | Seleccionado |
| `slider_create(x, y, w, min, max)` | GadTools | Slider |
| `slider_get(gad)` | GT_GetGadgetAttrs | Valor |
| `slider_set(gad, val)` | GT_SetGadgetAttrs | Establecer |
| `text_input_create(x, y, w, maxlen)` | GadTools | Campo de texto |
| `text_input_get(gad)` | GT_GetGadgetAttrs | Contenido |
| `text_input_set(gad, str)` | GT_SetGadgetAttrs | Establecer |
| `listview_create(x, y, w, h)` | GadTools | Lista |
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
| `time_ticks()` | `ReadEClock()` | Ticks de sistema |
| `time_delay(seconds)` | `Delay()` | Esperar segundos |
| `time_delay_ms(ms)` | `Delay()` | Esperar milisegundos |
| `time_date()` | `DateStamp()` | Fecha/hora actual |

### 7.3 Misc
| Dash | AmigaOS | Descripción |
|------|---------|-------------|
| `random()` | Custom | Número aleatorio |
| `random_range(min, max)` | Custom | Aleatorio en rango |
| `random_seed(seed)` | Custom | Semilla |
| `version_os()` | `SysBase->LibNode` | Versión AmigaOS |
| `version_cpu()` | `SysBase->AttnFlags` | Tipo de CPU |

---

## Constantes

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
