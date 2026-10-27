# Dash Language - Complete Amiga API

*English | [Castellano](AMIGA_API.md)*

Design catalog of the built-in functions for AmigaOS.

> **Note:** this document is the original design (January 2026) and does not describe what exists. The real list, generated
> from the code, is in [BUILTINS.md](BUILTINS.en.md): 685 builtins today, all implemented.
> In the tables, **Does not exist** marks names that are not in Dash and **Now** what ended up different (another
> name or other arguments). Many resources are referenced by number (`id`), not by a returned object. Rows without
> a mark exist with that name and those arguments.

---

## 1. GRAPHICS - 2D Drawing

### 1.1 Colors and Modes
| Dash | AmigaOS | Description |
|------|---------|-------------|
| `gfx_pen(color)` | `SetAPen()` | Main drawing color (0-255) |
| `gfx_pen_bg(color)` | `SetBPen()` | Background color |
| `gfx_pen_outline(color)` | `SetOPen()` | Outline color for areas |
| `gfx_mode(mode)` | `SetDrMd()` | Mode: MODE_JAM1, MODE_JAM2, MODE_COMP, MODE_INV |
| `gfx_pattern(pattern)` | `SetDrPt()` | Line pattern (16 bits) |
| `gfx_rgb(index, r, g, b)` | `SetRGB4()` | Set a palette color (0-15 per component) |
| `gfx_rgb8(index, r, g, b)` | `SetRGB32()` | Set a 24-bit color (AGA) |

### 1.2 Basic Primitives
| Dash | AmigaOS | Description |
|------|---------|-------------|
| `gfx_move(x, y)` | `Move()` | Move the graphics cursor |
| `gfx_draw(x, y)` | `Draw()` | Line from the cursor to a point |
| `gfx_line(x1, y1, x2, y2)` | `Move()+Draw()` | Line between two points |
| `gfx_pixel(x, y)` | `WritePixel()` | Draw a pixel |
| `gfx_pixel_read(x, y)` | `ReadPixel()` | Read a pixel's color |
| `gfx_rect(x1, y1, x2, y2)` | `RectFill()` | Filled rectangle |
| `gfx_box(x1, y1, x2, y2)` | `Move()+Draw()` | Rectangle outline only |
| `gfx_ellipse(cx, cy, rx, ry)` | `DrawEllipse()` | Ellipse/circle outline |
| `gfx_ellipse_fill(cx, cy, rx, ry)` | `AreaEllipse()+AreaEnd()` | Filled ellipse |
| `gfx_circle(cx, cy, r)` | `DrawEllipse(r,r)` | Circle outline |
| `gfx_circle_fill(cx, cy, r)` | `AreaEllipse()+AreaEnd()` | Filled circle |
| `gfx_flood(x, y, mode)` | `Flood()` | Flood fill |

### 1.3 Text
| Dash | AmigaOS | Description |
|------|---------|-------------|
| `gfx_text(str)` | `Text()` | Write text at the cursor |
| `gfx_text_at(x, y, str)` | `Move()+Text()` | Text at a position |
| `gfx_text_len(str)` | `TextLength()` | Width in pixels |
| `gfx_font(name, size)` | `OpenFont()+SetFont()` | Change font · **Does not exist.** Now: `font_open(nombre, tamaño)` and `font_use(f)` |

### 1.4 Clearing and Scrolling
| Dash | AmigaOS | Description |
|------|---------|-------------|
| `gfx_clear()` | `SetRast(rp, 0)` | Clear with color 0 |
| `gfx_clear_color(color)` | `SetRast()` | Clear with a color |
| `gfx_scroll(dx, dy, x1, y1, x2, y2)` | `ScrollRaster()` | Scroll a region |

### 1.5 Areas (Polygons)
| Dash | AmigaOS | Description |
|------|---------|-------------|
| `gfx_poly_begin(x, y)` | `AreaMove()` | Start a polygon |
| `gfx_poly_add(x, y)` | `AreaDraw()` | Add a vertex |
| `gfx_poly_end()` | `AreaEnd()` | Close and fill |

### 1.6 Blitting
| Dash | AmigaOS | Description |
|------|---------|-------------|
| `gfx_copy(sx, sy, w, h, dx, dy)` | `ClipBlit()` | Copy a region within the window |
| `gfx_blit(bitmap, sx, sy, dx, dy, w, h)` | `BltBitMapRastPort()` | Blit from a bitmap · **Does not exist.** Now: `bitmap_blit(id, sx, sy, w, h, dx, dy)` |

---

## 2. ADVANCED GRAPHICS

### 2.1 Bitmaps
| Dash | AmigaOS | Description |
|------|---------|-------------|
| `bitmap_create(w, h, depth)` | `AllocBitMap()` | Create an empty bitmap · **Now:** `bitmap_create(id, w, h, depth)` (by number) |
| `bitmap_free(bm)` | `FreeBitMap()` | Free a bitmap · **Now:** `bitmap_free(id)` |
| `bitmap_load(filename)` | `LoadIFF()` | Load an IFF/ILBM image · **Now:** `bitmap_load(id, fichero)` |
| `bitmap_save(bm, filename)` | `SaveIFF()` | Save as IFF · **Now:** `bitmap_save(id, fichero)` |
| `bitmap_width(bm)` | `GetBitMapAttr()` | Width · **Does not exist.** (datatypes images do: `image_width`) |
| `bitmap_height(bm)` | `GetBitMapAttr()` | Height · **Does not exist.** (datatypes images do: `image_height`) |
| `bitmap_depth(bm)` | `GetBitMapAttr()` | Depth · **Does not exist.** |

### 2.2 Sprites (Hardware)
| Dash | AmigaOS | Description |
|------|---------|-------------|
| `sprite_create(height)` | `AllocSpriteData()` | Create a sprite · **Now:** `sprite_create(id, ancho, alto)` (by number); also `sprite_load(id, fichero)` |
| `sprite_free(spr)` | `FreeSpriteData()` | Free a sprite · **Now:** `sprite_free(id)` |
| `sprite_get()` | `GetSprite()` | Get a sprite channel · **Does not exist.** Sprites are referenced by number (`id`) |
| `sprite_release(num)` | `FreeSprite()` | Release a channel · **Does not exist.** Sprites are referenced by number (`id`) |
| `sprite_move(num, x, y)` | `MoveSprite()` | Move a sprite · **Does not exist.** Now: `sprite_pos(id, x, y)`, `sprite_show(id)`, `sprite_hide(id)` |
| `sprite_color(num, idx, r, g, b)` | `SetRGB4()` | Sprite color · **Now:** `sprite_color(id, índice, r, g, b)` |
| `sprite_data(spr, line, word1, word2)` | Direct | Set a sprite line · **Does not exist.** Now: `sprite_set_row(id, fila, plano0, plano1)` |
| `sprite_attach(spr1, spr2)` | `ChangeSprite()` | Attach sprites (16 colors) · **Does not exist.** |

### 2.3 BOBs (Blitter Objects)
| Dash | AmigaOS | Description |
|------|---------|-------------|
| `bob_create(w, h, depth)` | `AllocVSprite()` | Create a BOB · **Now:** `bob_create(id, w, h, depth)` (by number); also `bob_load(id, fichero)` |
| `bob_free(bob)` | `FreeVSprite()` | Free a BOB · **Now:** `bob_free(id)` |
| `bob_image(bob, bitmap)` | Setup ImageData | Assign an image · **Does not exist.** Now: `bob_load(id, fichero)` and `bob_frame(id, marco)` |
| `bob_pos(bob, x, y)` | Set X, Y | Position · **Now:** `bob_pos(id, x, y)` |
| `bob_add(bob)` | `AddBob()` | Add to the list · **Does not exist.** Now: `bob_draw(id)` |
| `bob_remove(bob)` | `RemBob()` | Remove from the list · **Does not exist.** Now: `bob_erase(id)` (restores the background) |
| `bob_draw_all()` | `DrawGList()+SortGList()` | Draw all · **Does not exist.** Each BOB is drawn with `bob_draw(id)` |
| `bob_collision(bob1, bob2)` | `DoCollision()` | Detect a collision · **Now:** `bob_collision(id1, id2)` |

### 2.4 Double Buffering
| Dash | AmigaOS | Description |
|------|---------|-------------|
| `gfx_buffer_create()` | `AllocDBufInfo()` | Create a double buffer · **Does not exist.** Double buffering lives in `lib/amiga/doublebuf.dash` (`dbuf_new`) |
| `gfx_buffer_free(db)` | `FreeDBufInfo()` | Free · **Does not exist.** Now: `dbuf_del` from `lib/amiga/doublebuf.dash` |
| `gfx_flip()` | `ChangeVPBitMap()` | Swap buffers · **Does not exist.** Now: `dbuf_swap` from `lib/amiga/doublebuf.dash` |
| `gfx_wait_blit()` | `WaitBlit()` | Wait for the blit to finish · **Does not exist.** Now: `wait_blit()` |
| `gfx_wait_tof()` | `WaitTOF()` | Wait for the vertical blank · **Does not exist.** Now: `wait_vblank()` |

### 2.5 Copper
| Dash | AmigaOS | Description |
|------|---------|-------------|
| `copper_create(size)` | `UCopperListInit()` | Create a copper list · **Now:** a single list, with no `cl` in the other functions |
| `copper_free(cl)` | `FreeCopList()` | Free · **Now:** `copper_free()` |
| `copper_wait(cl, x, y)` | `CWAIT()` | Wait for a position · **Now:** `copper_wait(y, x)` |
| `copper_move(cl, reg, value)` | `CMOVE()` | Write a register · **Now:** `copper_move(reg, valor)`; also `copper_color(índice, rgb)` |
| `copper_end(cl)` | `CEND()` | End the list · **Now:** `copper_end()` |
| `copper_install(cl)` | viewport->UCopIns | Install · **Now:** `copper_install()` |

---

## 3. DOS - Files and System

### 3.1 Files
| Dash | AmigaOS | Description |
|------|---------|-------------|
| `file_open(path, mode)` | `Open()` | Open a file (MODE_READ, MODE_WRITE, MODE_APPEND) · **Now:** modes 1005 (read), 1006 (new) and 1004 (read and write); `MODE_APPEND` does not exist |
| `file_close(fh)` | `Close()` | Close a file |
| `file_read(fh, size)` | `Read()` | Read bytes, returns a string · **Now:** `file_read(fh, buffer, n)`, into a buffer from `buffer_alloc`; a whole text file: `file_read_text(ruta)` |
| `file_read_line(fh)` | `FGets()` | Read a line · **Now:** `file_read_line(fh, buffer, max)` |
| `file_write(fh, data)` | `Write()` | Write data · **Now:** `file_write(fh, buffer, n)`; a string: `file_print(fh, texto)` or `file_write_text(ruta, texto)` |
| `file_write_line(fh, str)` | `FPuts()` | Write a line |
| `file_seek(fh, pos, mode)` | `Seek()` | Move the position |
| `file_pos(fh)` | `Seek(0, OFFSET_CURRENT)` | Current position |
| `file_size(fh)` | `Seek()` trick | File size · **Now:** `file_size(ruta)`, with the file name |
| `file_eof(fh)` | Check | End of file? |

### 3.2 File System
| Dash | AmigaOS | Description |
|------|---------|-------------|
| `file_exists(path)` | `Lock()+UnLock()` | Does the file exist? |
| `file_delete(path)` | `DeleteFile()` | Delete a file |
| `file_rename(old, new)` | `Rename()` | Rename |
| `file_copy(src, dst)` | Read+Write | Copy a file |
| `dir_create(path)` | `CreateDir()` | Create a directory |
| `dir_delete(path)` | `DeleteFile()` | Delete an empty directory · **Does not exist.** `file_delete(ruta)` uses `DeleteFile()`, which also deletes an empty directory |
| `dir_list(path)` | `Examine()+ExNext()` | List a directory → array · **Does not exist.** |
| `dir_current()` | `GetCurrentDirName()` | Current directory |
| `dir_change(path)` | `CurrentDir()` | Change directory |

### 3.3 Console/CLI
| Dash | AmigaOS | Description |
|------|---------|-------------|
| `print(str)` | `Printf()` | Already implemented · **Does not exist.** as a function: it is the `Print x` statement |
| `input(prompt)` | `FGets(stdin)` | Read user input · **Does not exist.** Now: `console_read(buffer, max)` |
| `cls()` | `Printf("\033[2J")` | Clear the console · **Does not exist.** |

---

## 4. AUDIO - Sound

### 4.1 Samples
| Dash | AmigaOS | Description |
|------|---------|-------------|
| `sample_load(filename)` | LoadIFF 8SVX | Load an IFF sample · **Does not exist.** Now: `sound_load(id, fichero)` |
| `sample_free(smp)` | `FreeMem()` | Free a sample · **Does not exist.** Now: `sound_free(id)` |
| `sample_create(size)` | `AllocMem(CHIP)` | Create a buffer · **Does not exist.** Now: `sound_create(id, muestras, frecuencia)` |
| `sample_data(smp, offset, value)` | Direct | Write a value · **Does not exist.** Now: `sound_sample(id, i, valor)` |

### 4.2 Channels (Paula)
| Dash | AmigaOS | Description |
|------|---------|-------------|
| `audio_play(channel, sample)` | audio.device | Play on channel 0-3 · **Does not exist.** Now: `sound_play(id, canal)` |
| `audio_stop(channel)` | audio.device | Stop a channel · **Does not exist.** Now: `sound_stop(canal)` |
| `audio_volume(channel, vol)` | AUDxVOL | Volume 0-64 · **Does not exist.** Now: `sound_volume(canal, vol)` |
| `audio_period(channel, period)` | AUDxPER | Frequency · **Does not exist.** Now: `sound_period(canal, periodo)` |
| `audio_loop(channel, enable)` | Setup | Loop on/off · **Does not exist.** Now: `sound_loop(id, canal)` |
| `audio_wait(channel)` | Wait | Wait until finished · **Does not exist.** `sound_playing(canal)` tells whether it is still playing |

### 4.3 Music (MOD)
| Dash | AmigaOS | Description |
|------|---------|-------------|
| `mod_load(filename)` | ptplayer | Load a ProTracker module · **Does not exist.** Now: `music_load(fichero)` |
| `mod_free(mod)` | ptplayer | Free · **Does not exist.** Now: `music_free()` |
| `mod_play(mod)` | ptplayer | Play · **Does not exist.** Now: `music_play()` |
| `mod_stop()` | ptplayer | Stop · **Does not exist.** Now: `music_stop()` |
| `mod_pause()` | ptplayer | Pause · **Does not exist.** Now: `music_pause()` |
| `mod_resume()` | ptplayer | Resume · **Does not exist.** Now: `music_resume()` |
| `mod_position(pos)` | ptplayer | Jump to a position · **Does not exist.** Now: `music_position(pos)` |
| `mod_volume(vol)` | ptplayer | Master volume · **Does not exist.** Now: `music_volume(vol)` |

---

## 5. INPUT

### 5.1 Keyboard
| Dash | AmigaOS | Description |
|------|---------|-------------|
| `key_pressed()` | IDCMP_RAWKEY | Is a key available? → bool |
| `key_get()` | GetMsg | Get the key code |
| `key_wait()` | WaitPort | Wait for a key |
| `key_state(keycode)` | Direct hardware | Is the key pressed? · **Does not exist.** |

### 5.2 Mouse
| Dash | AmigaOS | Description |
|------|---------|-------------|
| `mouse_x()` | IntuiMessage | X position |
| `mouse_y()` | IntuiMessage | Y position |
| `mouse_button(btn)` | IntuiMessage | Button state (0=left, 1=right, 2=middle) · **Now:** 0 = left, 1 = right |
| `mouse_click()` | IDCMP_MOUSEBUTTONS | Wait for a click · **Does not exist.** Now: `wait_click()`, or `On Click` in an `EventLoop` |

### 5.3 Joystick
| Dash | AmigaOS | Description |
|------|---------|-------------|
| `joy_x(port)` | gameport/hardware | X direction (-1, 0, 1) |
| `joy_y(port)` | gameport/hardware | Y direction (-1, 0, 1) |
| `joy_button(port)` | hardware | Button pressed |
| `joy_up(port)` | hardware | Up |
| `joy_down(port)` | hardware | Down |
| `joy_left(port)` | hardware | Left |
| `joy_right(port)` | hardware | Right |
| `joy_fire(port)` | hardware | Fire |

---

## 6. INTUITION - Extended GUI

### 6.1 Windows (extended)
| Dash | AmigaOS | Description |
|------|---------|-------------|
| `win.open` | Already implemented | Open a window |
| `win.close` | `CloseWindow()` | Close a window |
| `win.title(str)` | `SetWindowTitles()` | Change the title · **Does not exist.** Now: `window_title(h, texto)` (h 0: the current window) |
| `win.size(w, h)` | `SizeWindow()` | Resize · **Does not exist.** Now: `window_resize(h, w, alto)` |
| `win.move(x, y)` | `MoveWindow()` | Move · **Does not exist.** Now: `window_move(h, x, y)` |
| `win.to_front()` | `WindowToFront()` | Bring to front · **Does not exist.** Now: `window_to_front(h)` |
| `win.to_back()` | `WindowToBack()` | Send to back · **Does not exist.** Now: `window_to_back(h)` |
| `win.activate()` | `ActivateWindow()` | Activate · **Does not exist.** Now: `window_activate(h)` |

### 6.2 Requesters
| Dash | AmigaOS | Description |
|------|---------|-------------|
| `alert(text)` | `EasyRequest()` | Simple alert · Not a builtin: `alert(título, texto)` from `lib/amiga/intuition.dash` |
| `confirm(text)` | `EasyRequest()` | Yes/No → bool · Not a builtin: `confirm(título, texto)` from `lib/amiga/intuition.dash` |
| `ask(text, options)` | `EasyRequest()` | Multiple options · Not a builtin: `ask(título, texto, botones)` from `lib/amiga/intuition.dash` |
| `file_requester(title, pattern)` | ASL | File requester · **Does not exist.** Now: `dialog_file(título, patrón, guardar)` |
| `dir_requester(title)` | ASL | Directory requester · **Does not exist.** |
| `font_requester(title)` | ASL | Font requester · **Does not exist.** Now: `dialog_font(título)` |
| `color_requester(title)` | ASL | Color requester · **Does not exist.** Now: `dialog_color(título, inicial)` (its own palette, not ASL) |

### 6.3 Menus
| Dash | AmigaOS | Description |
|------|---------|-------------|
| `menu_create()` | `CreateMenus()` | Create the structure · **Does not exist.** Now: `menu_title(texto)` and `menu_item(...)` in order |
| `menu_add(menu, title)` | Setup | Add a menu · **Does not exist.** Now: `menu_title(texto)` |
| `menu_item(menu, label, shortcut)` | Setup | Add an item · **Now:** `menu_item(texto, atajo, id)`; submenus with `menu_sub` |
| `menu_separator(menu)` | NM_BARLABEL | Separator · **Now:** `menu_separator()` |
| `menu_attach(win, menu)` | `SetMenuStrip()` | Attach to a window · **Now:** `menu_attach()`, after defining the menus |
| `menu_remove(win)` | `ClearMenuStrip()` | Remove · **Does not exist.** |
| `menu_selected()` | IDCMP_MENUPICK | Selected item · **Does not exist.** Now: `menu_id()` in `On Menu`, or `menu_event()` |

### 6.4 Gadgets (Controls)
| Dash | AmigaOS | Description |
|------|---------|-------------|
| `button_create(x, y, w, h, label)` | GadTools | Create a button · **Now:** `button_create(win, x, y, w, h, texto)`: the window first; the gadget is a number (`On Gadget`) |
| `checkbox_create(x, y, label)` | GadTools | Checkbox · **Now:** `checkbox_create(win, x, y, texto)` |
| `checkbox_get(gad)` | GT_GetGadgetAttrs | State |
| `radio_create(x, y, labels[])` | GadTools | Radio buttons · **Now:** `radio_create(win, x, y, "a|b|c")` |
| `radio_get(gad)` | GT_GetGadgetAttrs | Selected |
| `slider_create(x, y, w, min, max)` | GadTools | Slider · **Now:** `slider_create(win, x, y, w, h, min, max, valor)` |
| `slider_get(gad)` | GT_GetGadgetAttrs | Value |
| `slider_set(gad, val)` | GT_SetGadgetAttrs | Set |
| `text_input_create(x, y, w, maxlen)` | GadTools | Text field · **Does not exist.** Now: `gt_string(x, y, w, h, etiqueta, inicial, max)` (or `mui_string`) |
| `text_input_get(gad)` | GT_GetGadgetAttrs | Contents · **Does not exist.** Now: `gt_get_string(id)` |
| `text_input_set(gad, str)` | GT_SetGadgetAttrs | Set · **Does not exist.** |
| `listview_create(x, y, w, h)` | GadTools | List · **Now:** `listview_create(win, x, y, w, h)` |
| `listview_add(gad, item)` | GT_SetGadgetAttrs | Add an item |
| `listview_clear(gad)` | GT_SetGadgetAttrs | Clear |
| `listview_selected(gad)` | GT_GetGadgetAttrs | Selected item |

---

## 7. SYSTEM

### 7.1 Memory
| Dash | AmigaOS | Description |
|------|---------|-------------|
| `mem_chip_free()` | `AvailMem(CHIP)` | Free Chip RAM |
| `mem_fast_free()` | `AvailMem(FAST)` | Free Fast RAM |
| `mem_total()` | `AvailMem(TOTAL)` | Total available |

### 7.2 Time
| Dash | AmigaOS | Description |
|------|---------|-------------|
| `time_ticks()` | `ReadEClock()` | System ticks · **Does not exist.** Now: `time_ms()` (milliseconds since the program started) |
| `time_delay(seconds)` | `Delay()` | Wait seconds · **Now:** in ticks (50 per second) |
| `time_delay_ms(ms)` | `Delay()` | Wait milliseconds |
| `time_date()` | `DateStamp()` | Current date/time · **Does not exist.** Now: `clock_read()`, `clock_year()`... and `date_text(formato)` |

### 7.3 Misc
| Dash | AmigaOS | Description |
|------|---------|-------------|
| `random()` | Custom | Random number |
| `random_range(min, max)` | Custom | Random number in a range |
| `random_seed(seed)` | Custom | Seed |
| `version_os()` | `SysBase->LibNode` | AmigaOS version · **Does not exist.** |
| `version_cpu()` | `SysBase->AttnFlags` | CPU type · **Does not exist.** |

---

## Constants

> **Note:** Dash does not ship these constants. Only `MODE_READ` (1005), `MODE_WRITE` (1006) and
> `MODE_READWRITE` (1004) exist, with `import "lib/amiga/dos.dash"`; `MODE_APPEND` does not exist. Everything else is written
> as its number (for example `file_open("f", 1005)`). In `On Key`, keys go by name: `On Key "ESC"`.

```ruby
# Drawing modes
MODE_JAM1 = 0
MODE_JAM2 = 1
MODE_COMP = 2
MODE_INV = 4

# File modes
MODE_READ = 1005
MODE_WRITE = 1006
MODE_APPEND = 1007

# Special keys
KEY_UP = 76
KEY_DOWN = 77
KEY_LEFT = 79
KEY_RIGHT = 78
KEY_SPACE = 64
KEY_RETURN = 68
KEY_ESC = 69
KEY_F1 = 80
# ... etc

# Joystick ports
JOY_PORT1 = 0
JOY_PORT2 = 1
```

---

## Summary

| Module | Functions |
|--------|-----------|
| Basic graphics | 28 |
| Advanced graphics | 32 |
| DOS | 22 |
| Audio | 18 |
| Input | 16 |
| Intuition | 35 |
| System | 10 |
| **TOTAL** | **~161 functions** |

That was the plan. Today Dash has **685 builtins**, all implemented; 93 of them are for MUI. There is more than this
design anticipated: GadTools, ReAction and MUI, networking (TCP client and server, UDP, TLS with AmiSSL, SANA-II drivers),
images via datatypes, fonts, RTG, tasks, commodities, language catalogs, date and time... The real list,
with what each one does, is in [BUILTINS.md](BUILTINS.en.md).
