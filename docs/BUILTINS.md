# Funciones built-in

> Generado por `tools/gen_builtins_doc.py` desde `compiler/amiga_builtins.py`. No editar a mano.

Las marcadas **sin implementar** están declaradas pero no tienen código C:
usarlas da el error `Builtin 'x' is declared but not implemented yet`.

Total: 590 funciones, 590 implementadas, 0 sin implementar.

## Gráficos básicos

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `gfx_pen(color)` | `void` | Set foreground pen color |  |
| `gfx_pen_bg(color)` | `void` | Set background pen color |  |
| `gfx_pen_outline(color)` | `void` | Set outline pen color for area fills |  |
| `gfx_mode(mode)` | `void` | Set drawing mode (JAM1, JAM2, COMPLEMENT, INVERSVID) |  |
| `gfx_pattern(pattern)` | `void` | Set line pattern (16-bit) |  |
| `gfx_rgb(index, r, g, b)` | `void` | Set palette color (4-bit components 0-15) |  |
| `gfx_rgb8(index, r, g, b)` | `void` | Set palette color (8-bit components, AGA) |  |
| `gfx_move(x, y)` | `void` | Move graphics cursor |  |
| `gfx_draw(x, y)` | `void` | Draw line from cursor to point |  |
| `gfx_line(x1, y1, x2, y2)` | `void` | Draw line between two points |  |
| `gfx_pixel(x, y)` | `void` | Draw single pixel |  |
| `gfx_pixel_read(x, y)` | `LONG` | Read pixel color |  |
| `gfx_rect(x1, y1, x2, y2)` | `void` | Draw filled rectangle |  |
| `gfx_box(x1, y1, x2, y2)` | `void` | Draw rectangle outline |  |
| `gfx_ellipse(cx, cy, rx, ry)` | `void` | Draw ellipse outline |  |
| `gfx_circle(cx, cy, r)` | `void` | Draw circle outline |  |
| `gfx_ellipse_fill(cx, cy, rx, ry)` | `void` | Draw filled ellipse |  |
| `gfx_circle_fill(cx, cy, r)` | `void` | Draw filled circle |  |
| `gfx_flood(x, y, mode)` | `void` | Flood fill |  |
| `gfx_text(str)` | `void` | Draw text at cursor |  |
| `gfx_text_at(x, y, str)` | `void` | Draw text at position |  |
| `gfx_text_len(str)` | `LONG` | Get text width in pixels |  |
| `gfx_clear()` | `void` | Clear with color 0 |  |
| `gfx_clear_color(color)` | `void` | Clear with specified color |  |
| `gfx_scroll(dx, dy, x1, y1, x2, y2)` | `void` | Scroll region |  |
| `gfx_poly_begin(x, y)` | `void` | Begin polygon at point |  |
| `gfx_poly_add(x, y)` | `void` | Add polygon vertex |  |
| `gfx_poly_end()` | `void` | Close and fill polygon |  |
| `gfx_copy(sx, sy, w, h, dx, dy)` | `void` | Copy region within window |  |

## Gráficos avanzados

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `sprite_load(id, filename)` | `BOOL` | Sprite from a picture (ILBM...): 16-pixel frames side by side, pens 0-3 its colours (0 clear); FALSE if it cannot |  |
| `sprite_create(id, width, height)` | `BOOL` | Create empty sprite |  |
| `sprite_pos(id, x, y)` | `void` | Set sprite position |  |
| `sprite_show(id)` | `void` | Make sprite visible |  |
| `sprite_hide(id)` | `void` | Hide sprite |  |
| `sprite_color(id, index, r, g, b)` | `void` | Set sprite color |  |
| `sprite_frame(id, frame)` | `void` | Show frame number frame (0 the first) of a sprite from sprite_load |  |
| `sprite_free(id)` | `void` | Free sprite memory |  |
| `sprite_collision(id1, id2)` | `BOOL` | Check sprite collision |  |
| `sprite_set_row(id, row, plane0, plane1)` | `void` | Set sprite data row (2 bitplanes) |  |
| `soft_sprite_create(id, width, height, depth)` | `BOOL` | Create software sprite (RTG compatible) |  |
| `soft_sprite_free(id)` | `void` | Free software sprite |  |
| `soft_sprite_pixel(id, x, y, color)` | `void` | Set pixel in software sprite |  |
| `soft_sprite_clear(id, color)` | `void` | Clear software sprite with color |  |
| `soft_sprite_row(id, row, plane0, plane1)` | `void` | Set sprite row (hardware sprite format compatible) |  |
| `soft_sprite_show(id)` | `void` | Show software sprite |  |
| `soft_sprite_hide(id)` | `void` | Hide software sprite |  |
| `soft_sprite_pos(id, x, y)` | `void` | Set software sprite position |  |
| `soft_sprite_x(id)` | `LONG` | Get software sprite X position |  |
| `soft_sprite_y(id)` | `LONG` | Get software sprite Y position |  |
| `bob_load(id, filename)` | `BOOL` | Load BOB from file |  |
| `bob_create(id, width, height, depth)` | `BOOL` | Create empty BOB |  |
| `bob_pos(id, x, y)` | `void` | Set BOB position |  |
| `bob_draw(id)` | `void` | Draw BOB |  |
| `bob_erase(id)` | `void` | Erase BOB (restore background) |  |
| `bob_frame(id, frame)` | `void` | Set BOB animation frame |  |
| `bob_free(id)` | `void` | Free BOB memory |  |
| `bob_collision(id1, id2)` | `BOOL` | Check BOB collision |  |
| `copper_create(size)` | `BOOL` | Create copper list |  |
| `copper_wait(y, x)` | `void` | Add copper WAIT instruction |  |
| `copper_move(reg, value)` | `void` | Add copper MOVE instruction |  |
| `copper_color(index, rgb)` | `void` | Add copper color change |  |
| `copper_end()` | `void` | End copper list |  |
| `copper_install()` | `void` | Install copper list |  |
| `copper_free()` | `void` | Free copper list |  |
| `bitmap_create(id, width, height, depth)` | `BOOL` | Create bitmap |  |
| `bitmap_load(id, filename)` | `BOOL` | Load IFF bitmap |  |
| `bitmap_save(id, filename)` | `BOOL` | Save IFF bitmap |  |
| `bitmap_free(id)` | `void` | Free bitmap |  |
| `bitmap_blit(src_id, sx, sy, w, h, dx, dy)` | `void` | Blit from bitmap to screen |  |
| `bitmap_blit_mask(src_id, mask_id, sx, sy, w, h, dx, dy)` | `void` | Masked blit from bitmap |  |
| `bitmap_draw_to(id)` | `void` | Set bitmap as drawing target |  |
| `bitmap_draw_screen()` | `void` | Set screen as drawing target |  |

## Entrada (teclado, ratón, joystick)

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `key_pressed()` | `BOOL` | Check if key is available |  |
| `key_get()` | `LONG` | Get key code |  |
| `key_wait()` | `LONG` | Wait for and return key |  |
| `key_raw()` | `LONG` | Get raw key code (no translation) |  |
| `key_text(keycode)` | `STRPTR` | Convert keycode to text |  |
| `mouse_x()` | `LONG` | Mouse X position relative to window inner area |  |
| `mouse_y()` | `LONG` | Mouse Y position relative to window inner area |  |
| `mouse_button(btn)` | `BOOL` | Check mouse button (0=left, 1=right) |  |
| `event_window()` | `LONG` | In an EventLoop: handle of the window the event came from (window_create), 0 for the loop's own window |  |
| `window_check_close()` | `BOOL` | Check if close button was clicked (non-blocking) |  |
| `close_window()` | `void` | Close the current window |  |
| `screen_open(depth, title)` | `BOOL` | Open a screen cloning Workbench display mode with custom depth |  |
| `screen_open_custom(width, height, depth, title)` | `BOOL` | Open a custom screen with specific dimensions and depth |  |
| `screen_close()` | `void` | Close the screen |  |
| `screen_width()` | `LONG` | Get the screen width in pixels |  |
| `screen_height()` | `LONG` | Get the screen height in pixels |  |
| `check_lmb()` | `BOOL` | Check if left mouse button is pressed (hardware) |  |
| `check_rmb()` | `BOOL` | Check if right mouse button is pressed (hardware) |  |
| `check_mouse()` | `BOOL` | Check if any mouse button is pressed (hardware) |  |
| `check_esc()` | `BOOL` | Check if ESC key is pressed (hardware) |  |
| `wait_click()` | `LONG` | Wait for mouse click (press and release) |  |
| `wait_key()` | `LONG` | Wait for any key and return its code |  |
| `joy_x(port)` | `LONG` | Joystick X direction (-1, 0, 1) |  |
| `joy_y(port)` | `LONG` | Joystick Y direction (-1, 0, 1) |  |
| `joy_button(port)` | `BOOL` | Joystick button state |  |
| `joy_up(port)` | `BOOL` | Joystick up |  |
| `joy_down(port)` | `BOOL` | Joystick down |  |
| `joy_left(port)` | `BOOL` | Joystick left |  |
| `joy_right(port)` | `BOOL` | Joystick right |  |
| `joy_fire(port)` | `BOOL` | Joystick fire button |  |

## GadTools

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `gt_init()` | `BOOL` | Initialize GadTools context (call after window open) |  |
| `gt_cleanup()` | `void` | Cleanup GadTools resources |  |
| `gt_attach()` | `void` | Attach gadgets to window (call after creating all gadgets) |  |
| `gt_button(x, y, w, h, label)` | `LONG` | Create a button gadget, returns gadget ID |  |
| `gt_checkbox(x, y, w, h, label, checked)` | `LONG` | Create a checkbox gadget |  |
| `gt_string(x, y, w, h, label, initial, maxchars)` | `LONG` | Create a string input gadget |  |
| `gt_integer(x, y, w, h, label, initial)` | `LONG` | Create an integer input gadget |  |
| `gt_slider(x, y, w, h, label, min, max, level)` | `LONG` | Create a slider gadget |  |
| `gt_palette(x, y, w, h, label, depth, color)` | `LONG` | Create a palette selector gadget |  |
| `gt_text(x, y, w, h, label, text)` | `LONG` | Create a static text gadget |  |
| `gt_get_value(gad_id)` | `LONG` | Get numeric value from gadget (slider, palette, etc.) |  |
| `gt_set_value(gad_id, value)` | `void` | Set numeric value of gadget |  |
| `gt_get_string(gad_id)` | `STRPTR` | Get string value from string gadget |  |
| `gt_event()` | `LONG` | Check for gadget event, returns gadget ID or -1 (none) or -2 (close) |  |
| `gt_wait_event()` | `LONG` | Wait for gadget event, returns gadget ID or -2 (close) |  |
| `gt_cycle(x, y, w, h, label, options)` | `LONG` | Create a cycle gadget; options separated by \| (gt_get_value: option) |  |
| `gt_enable(gad_id)` | `void` | Enable a gadget |  |
| `gt_disable(gad_id)` | `void` | Disable (ghost) a gadget |  |
| `gt_set_text(gad_id, text)` | `void` | Change the text of a gt_text or gt_string gadget |  |

## Menús

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `menu_title(label)` | `void` | Add a menu title |  |
| `menu_item(label, shortcut, id)` | `void` | Add a menu item with keyboard shortcut and ID |  |
| `menu_sub(label, shortcut, id)` | `void` | Add a submenu item |  |
| `menu_separator()` | `void` | Add a menu separator bar |  |
| `menu_attach()` | `BOOL` | Attach menus to window (call after defining all menus) |  |
| `menu_event()` | `LONG` | Check for menu event, returns menu item ID or -1/-2 |  |
| `menu_id()` | `LONG` | In an EventLoop's On Menu: id of the menu item chosen |  |
| `menu_check_item(label, shortcut, id)` | `void` | Add a menu item with a check mark that each choice toggles |  |
| `menu_checked(id)` | `LONG` | 1 if the check mark of that menu item is on |  |
| `menu_enable(id, enabled)` | `void` | Enable or disable (ghost) a menu item after menu_attach |  |

## Requesters ASL

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `file_open_dialog(title, pattern)` | `BOOL` | Show file open dialog, returns true if file selected |  |
| `file_save_dialog(title, pattern)` | `BOOL` | Show file save dialog, returns true if file selected |  |
| `file_get_path()` | `STRPTR` | Get selected directory path from last dialog |  |
| `file_get_name()` | `STRPTR` | Get selected filename from last dialog |  |
| `file_fullpath()` | `STRPTR` | Get full path (dir + filename) from last dialog |  |

## ReAction

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `ra_window_create(title, width, height)` | `LONG` | Create a ReAction window with a layout; it becomes the current one. Its number (1-4), 0 on failure |  |
| `ra_window_use(window)` | `void` | Window the next ra_* calls work on (the number ra_window_create gave; up to 4 windows) |  |
| `ra_event_window()` | `LONG` | Window of the last event (its number from ra_window_create) |  |
| `ra_window_open()` | `LONG` | Open the ReAction window |  |
| `ra_window_close()` | `void` | Close the current ReAction window and free its gadgets (another open one becomes current) |  |
| `ra_window_sigmask()` | `ULONG` | Get window signal mask for Wait() |  |
| `ra_handle_events()` | `LONG` | Handle window events (non-blocking), returns gadget ID or -1 for close |  |
| `ra_wait_event()` | `LONG` | Wait for and handle window events, returns gadget ID or -1 for close |  |
| `ra_add_button(id, label)` | `LONG` | Add button gadget to layout |  |
| `ra_add_string(id, initial, maxchars)` | `LONG` | Add string input gadget |  |
| `ra_add_checkbox(id, label, checked)` | `LONG` | Add checkbox gadget |  |
| `ra_add_slider(id, min, max, initial)` | `LONG` | Add horizontal slider gadget |  |
| `ra_add_integer(id, initial, min, max)` | `LONG` | Add integer input gadget |  |
| `ra_add_label(text)` | `LONG` | Add text label |  |
| `ra_get_value(id)` | `LONG` | Get gadget value (checkbox 1/0, slider, integer, palette, chooser, scroller) |  |
| `ra_get_string(id)` | `STRPTR` | Get string gadget text |  |
| `ra_set_value(id, value)` | `void` | Set gadget value (same gadgets as ra_get_value) |  |
| `ra_refresh_layout()` | `void` | Refresh window layout after adding gadgets |  |
| `RA_EVENT_CLOSE()` | `LONG` | Close window event code (-1) |  |
| `RA_EVENT_NONE()` | `LONG` | No event code (-3) |  |
| `ra_get_rastport()` | `APTR` | Get RastPort for custom drawing (also sets _dash_rp) |  |
| `ra_get_inner_left()` | `LONG` | Get inner left border of window |  |
| `ra_get_inner_top()` | `LONG` | Get inner top border of window |  |
| `ra_get_inner_width()` | `LONG` | Get inner width of window |  |
| `ra_get_inner_height()` | `LONG` | Get inner height of window |  |
| `ra_add_palette(id, depth, initial_color)` | `LONG` | Add color palette gadget |  |
| `ra_get_palette_color(id)` | `LONG` | Get selected color from palette |  |
| `ra_set_palette_color(id, color)` | `void` | Set selected color in palette |  |
| `ra_add_chooser(id)` | `LONG` | Add dropdown/chooser gadget |  |
| `ra_chooser_add_item(id, label)` | `LONG` | Add item to chooser |  |
| `ra_get_chooser_selected(id)` | `LONG` | Get selected index from chooser |  |
| `ra_set_chooser_selected(id, index)` | `void` | Set selected index in chooser |  |
| `ra_add_scroller(id, min, max, visible, initial)` | `LONG` | Add horizontal scroller gadget |  |
| `ra_add_scroller_vert(id, min, max, visible, initial)` | `LONG` | Add vertical scroller gadget |  |
| `ra_get_scroller(id)` | `LONG` | Get scroller position |  |
| `ra_set_scroller(id, pos)` | `void` | Set scroller position |  |
| `ra_enable_gadget(id)` | `void` | Enable a gadget |  |
| `ra_disable_gadget(id)` | `void` | Disable a gadget |  |
| `ra_set_string(id, text)` | `void` | Set string gadget text |  |
| `ra_set_text(id, text)` | `void` | Set button/label text |  |
| `ra_layout_hgroup_begin()` | `LONG` | Begin horizontal layout group |  |
| `ra_layout_vgroup_begin()` | `LONG` | Begin vertical layout group |  |
| `ra_layout_group_end()` | `LONG` | End layout group |  |
| `ra_add_space()` | `void` | Add horizontal separator |  |
| `ra_add_vspace()` | `void` | Add vertical separator |  |
| `ra_layout_hgroup_weighted(weight)` | `LONG` | Begin horizontal layout group with weight hint |  |
| `ra_layout_vgroup_weighted(weight)` | `LONG` | Begin vertical layout group with weight hint |  |
| `ra_layout_group_end_weighted()` | `LONG` | End weighted layout group |  |
| `ra_add_drawing_area(id, min_width, min_height)` | `LONG` | Add Space gadget for custom drawing area |  |
| `ra_get_drawing_bounds(id)` | `LONG` | Query Space gadget bounds (call after window open) |  |
| `ra_drawing_left()` | `LONG` | Get drawing area left position |  |
| `ra_drawing_top()` | `LONG` | Get drawing area top position |  |
| `ra_drawing_width()` | `LONG` | Get drawing area width |  |
| `ra_drawing_height()` | `LONG` | Get drawing area height |  |
| `ra_calc_drawing_area(toolbar_h, timeline_h, left_w, right_w)` | `LONG` | Calculate drawing area from window dimensions (fallback) |  |
| `ra_refresh_canvas(id)` | `void` | Trigger canvas Space gadget refresh (calls render hook) |  |
| `ra_canvas_left()` | `LONG` | Get canvas left position from render hook |  |
| `ra_canvas_top()` | `LONG` | Get canvas top position from render hook |  |
| `ra_canvas_width()` | `LONG` | Get canvas width from render hook |  |
| `ra_canvas_height()` | `LONG` | Get canvas height from render hook |  |
| `ra_init_canvas_render()` | `void` | Register render_canvas() as the canvas render callback |  |
| `ra_canvas_enable()` | `void` | Enable canvas rendering (call after all init is done) |  |
| `ra_gadget_exists(id)` | `LONG` | Check if gadget exists |  |
| `ra_window_width()` | `LONG` | Get window width |  |
| `ra_window_height()` | `LONG` | Get window height |  |
| `ra_window_is_open()` | `LONG` | Check if window is open |  |
| `ra_add_listbrowser(id)` | `LONG` | Add a list of text lines (value: selected line, -1 none) |  |
| `ra_listbrowser_add(id, text)` | `LONG` | Add a line at the end of a listbrowser |  |
| `ra_listbrowser_clear(id)` | `void` | Remove all lines of a listbrowser |  |
| `ra_listbrowser_count(id)` | `LONG` | Number of lines of a listbrowser |  |
| `ra_add_radio(id, options)` | `LONG` | Add radio buttons, options separated by \| (value: option) |  |
| `ra_add_clicktab(id, titles)` | `LONG` | Add tabs, titles separated by \| (value: tab, from 0) |  |
| `ra_add_fuelgauge(id, max)` | `LONG` | Add a progress bar from 0 to max (value: level) |  |
| `ra_menu_title(label)` | `void` | Add a menu to the ReAction window (before ra_window_open) |  |
| `ra_menu_item(label, key, id)` | `void` | Add a menu item: key = letter for Amiga+key ("" none); events: RA_EVENT_MENU() and ra_menu_id() |  |
| `ra_menu_separator()` | `void` | Add a separator line to the menu |  |
| `ra_menu_id()` | `LONG` | Id of the menu item of the last RA_EVENT_MENU() |  |
| `RA_EVENT_MENU()` | `LONG` | Event: a menu item was chosen (ra_menu_id) |  |
| `ra_add_getfile(id, title)` | `LONG` | Add a button that opens a file requester; ra_get_string(id) gives the file chosen |  |

## Sistema y memoria

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `debug_break()` | `void` | Stop in the UAE emulator's debugger (nothing on a real Amiga; tools/emu_run.py --debug) |  |
| `mem_chip_free()` | `LONG` | Available chip RAM |  |
| `mem_fast_free()` | `LONG` | Available fast RAM |  |
| `mem_total()` | `LONG` | Total available memory |  |
| `peek_byte(addr)` | `LONG` | Read byte from memory address |  |
| `peek_word(addr)` | `LONG` | Read word from memory address |  |
| `peek_long(addr)` | `LONG` | Read long from memory address |  |
| `poke_byte(addr, value)` | `void` | Write byte to memory address |  |
| `poke_word(addr, value)` | `void` | Write word to memory address |  |
| `poke_long(addr, value)` | `void` | Write long to memory address |  |
| `time_delay(ticks)` | `void` | Delay in ticks (50 per second) |  |
| `time_delay_ms(ms)` | `void` | Delay in milliseconds |  |
| `random()` | `LONG` | Random number |  |
| `random_range(min, max)` | `LONG` | Random in range [min, max] |  |
| `random_seed(seed)` | `void` | Set random seed |  |
| `wait_vblank()` | `void` | Wait for vertical blank |  |
| `wait_blit()` | `void` | Wait for blitter |  |
| `arena_new(size)` | `LONG` | Create arena allocator with given size in bytes |  |
| `arena_alloc(arena, size)` | `LONG` | Allocate from arena (fast bump allocator) |  |
| `arena_reset(arena)` | `void` | Reset arena (reuse memory without freeing) |  |
| `arena_free(arena)` | `void` | Free arena and all its memory |  |
| `arena_used(arena)` | `LONG` | Get bytes used in arena |  |
| `arena_available(arena)` | `LONG` | Get bytes available in arena |  |
| `refcount(obj)` | `LONG` | Get reference count of object |  |
| `retain(obj)` | `void` | Manually increment reference count |  |
| `release(obj)` | `void` | Manually decrement reference count (frees if 0) |  |

## Ficheros (DOS)

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `file_open(filename, mode)` | `LONG` | Open file (mode: 1005 read, 1006 new file, 1004 read and write; 0 if it fails) |  |
| `file_close(handle)` | `void` | Close file |  |
| `file_read_byte(handle)` | `LONG` | Read single byte |  |
| `file_read_line(handle, buffer, maxlen)` | `STRPTR` | Read line into buffer |  |
| `file_read(handle, buffer, length)` | `LONG` | Read bytes into buffer |  |
| `file_eof(handle)` | `BOOL` | True at the end of the file (looks at the next byte without consuming it) |  |
| `file_write_byte(handle, byte)` | `LONG` | Write single byte |  |
| `file_write_line(handle, str)` | `LONG` | Write string followed by a newline (0 = ok, -1 = error) |  |
| `file_write(handle, buffer, length)` | `LONG` | Write bytes from buffer |  |
| `file_print(handle, str)` | `void` | Print string to file |  |
| `file_seek(handle, position, mode)` | `LONG` | Seek in file (mode: OFFSET_BEGINNING, OFFSET_CURRENT, OFFSET_END) |  |
| `file_pos(handle)` | `LONG` | Get current position |  |
| `file_size(filename)` | `LONG` | Get file size |  |
| `file_exists(filename)` | `BOOL` | Check if file exists |  |
| `file_delete(filename)` | `BOOL` | Delete file |  |
| `file_rename(oldname, newname)` | `BOOL` | Rename file |  |
| `file_copy(src, dest)` | `BOOL` | Copy file |  |
| `dir_create(path)` | `BOOL` | Create directory |  |
| `dir_change(path)` | `BOOL` | Change current directory |  |
| `dir_current()` | `STRPTR` | Full name of the current directory ("Ram Disk:" ...) |  |
| `console_read(buffer, maxlen)` | `LONG` | Read from console |  |
| `console_write(str)` | `void` | Write to console |  |
| `file_load(filename, buffer, maxsize)` | `LONG` | Load entire file into buffer, returns bytes read or -1 |  |
| `file_save(filename, buffer, size)` | `LONG` | Save buffer to file, returns bytes written |  |

## Buffers

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `buffer_alloc(size)` | `APTR` | Allocate memory buffer |  |
| `buffer_free(buffer)` | `void` | Free memory buffer |  |
| `buffer_get_byte(buffer, offset)` | `LONG` | Get byte at offset |  |
| `buffer_set_byte(buffer, offset, value)` | `void` | Set byte at offset |  |
| `buffer_get_word(buffer, offset)` | `LONG` | Get 16-bit word at offset (big-endian) |  |
| `buffer_set_word(buffer, offset, value)` | `void` | Set 16-bit word at offset (big-endian) |  |
| `buffer_get_long(buffer, offset)` | `LONG` | Get 32-bit long at offset (big-endian) |  |
| `buffer_set_long(buffer, offset, value)` | `void` | Set 32-bit long at offset (big-endian) |  |
| `buffer_copy(dest, dest_offset, src, src_offset, length)` | `void` | Copy bytes between buffers |  |
| `buffer_fill(buffer, offset, length, value)` | `void` | Fill buffer region with byte value |  |

## Texto

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `str_code(s, i)` | `LONG` | Code (0-255) of the character at position i, 0 outside the text |  |
| `str_char(code)` | `STRPTR` | One-character String with that code |  |
| `str_find(s, sub)` | `LONG` | Position of the first sub in s, -1 if it is not there |  |
| `str_find_from(s, sub, start)` | `LONG` | Position of the first sub in s from position start, -1 if none |  |
| `str_starts(s, prefix)` | `BOOL` | Does s start with prefix? |  |
| `str_ends(s, suffix)` | `BOOL` | Does s end with suffix? |  |
| `str_lower(s)` | `STRPTR` | Lowercase copy (Latin-1: also accented letters) |  |
| `str_upper(s)` | `STRPTR` | Uppercase copy (Latin-1: also accented letters) |  |
| `str_trim(s)` | `STRPTR` | Copy without spaces, tabs and line ends at both ends |  |
| `str_to_int(s, base)` | `LONG` | Number written in s in that base (2-36); Int(s) is base 10 |  |
| `str_from_int(n, base)` | `STRPTR` | n written in that base (2-36, lowercase letters) |  |
| `str_replace(s, from, to)` | `STRPTR` | Copy with every from replaced by to |  |
| `str_contains(s, sub)` | `BOOL` | Whether sub is in s ("" is in every text) |  |
| `str_split(s, sep)` | `DashArrayLong *` | The pieces of s between each sep, as a new [String]; with sep "" or not found, [s] |  |
| `file_read_text(filename)` | `STRPTR` | Whole file as a String (bytes 0 become spaces); nil if it cannot be read |  |
| `file_write_text(filename, text)` | `BOOL` | Write the text as the whole file; true if it was all written |  |
| `str_from_buffer(buffer, offset, length)` | `STRPTR` | String with length bytes of a buffer from offset (bytes 0 become spaces) |  |
| `str_to_buffer(s, buffer, offset)` | `LONG` | Copy the bytes of s to buffer + offset; returns how many |  |

## Red (TCP)

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `net_connect(host, port, timeout_ms)` | `LONG` | TCP connection to host:port (name or address); the socket, or -1 (see net_error) |  |
| `net_connect_start(host, port, timeout_ms)` | `LONG` | Start a TCP connection without waiting (the name is looked up in another process); the socket, or -1 (see net_error) |  |
| `net_connect_poll(sock)` | `LONG` | Go on with net_connect_start without waiting: 1 connected, 0 not yet, -1 failed (the socket is closed; see net_error) |  |
| `net_connect_stage(sock)` | `LONG` | What net_connect_start is doing: 0 looking the name up, 1 connecting, 2 done |  |
| `net_send(sock, text)` | `LONG` | Send the whole text; bytes sent or -1 |  |
| `net_send_buffer(sock, buffer, length)` | `LONG` | Send length bytes of a buffer; bytes sent or -1 |  |
| `net_recv(sock, max, timeout_ms)` | `STRPTR` | Up to max bytes as text: "" if nothing came within timeout_ms (-1: wait), nil once closed |  |
| `net_recv_buffer(sock, buffer, max, timeout_ms)` | `LONG` | Up to max bytes into a buffer: the count, 0 on time out, -1 once closed |  |
| `net_wait(sock, timeout_ms)` | `LONG` | Wait until there is something to read: 1 yes, 0 time out, -1 error |  |
| `net_close(sock)` | `void` | Close the connection |  |
| `net_resolve(host)` | `STRPTR` | IPv4 address of a host name ("a.b.c.d"), nil if unknown |  |
| `net_error()` | `STRPTR` | What went wrong in the last net_ call |  |
| `net_listen(port)` | `LONG` | A TCP server on port (0: any free one, net_port says which): the listening socket, or -1 (see net_error) |  |
| `net_accept(sock, timeout_ms)` | `LONG` | The next connection to a net_listen server, waiting timeout_ms at most (-1: wait, 0: only look): its socket (net_send, net_recv...), or -1 if none came |  |
| `net_peer(sock)` | `STRPTR` | The address ("a.b.c.d") of the other end of a TCP connection, nil if none |  |
| `net_port(sock)` | `LONG` | The local port of a socket (the one net_listen(0) or net_udp_open(0) got), -1 if none |  |
| `net_udp_open(port)` | `LONG` | A UDP socket on port (0: any free one), broadcasts allowed: the socket, or -1 (net_close closes it) |  |
| `net_udp_send(sock, host, port, text)` | `LONG` | Send text as one datagram to host:port ("255.255.255.255": the whole local network); bytes sent or -1 |  |
| `net_udp_send_buffer(sock, host, port, buffer, length)` | `LONG` | Send length bytes of a buffer as one datagram to host:port; bytes sent or -1 |  |
| `net_udp_recv(sock, max, timeout_ms)` | `STRPTR` | The next datagram as text (up to max bytes): "" if none came within timeout_ms, nil on error; who sent it: net_udp_from, net_udp_from_port |  |
| `net_udp_recv_buffer(sock, buffer, max, timeout_ms)` | `LONG` | The next datagram into a buffer: its length, 0 if none came in time, -1 on error |  |
| `net_udp_from()` | `STRPTR` | The address ("a.b.c.d") of who sent the last datagram received |  |
| `net_udp_from_port()` | `LONG` | The port of who sent the last datagram received (to answer it) |  |
| `net_signal()` | `LONG` | Signal mask the sockets post on each event (connected, data, closed...), 0 if the TCP/IP stack cannot: call it before each wait, mui_wait_event_signals(net_signal()) |  |

## TLS (AmiSSL)

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `tls_connect(sock, host)` | `LONG` | TLS over a connected socket, verifying the certificate for host; -1 if not (net_error) |  |
| `tls_connect_start(sock, host, timeout_ms)` | `LONG` | TLS over a connected socket without waiting for the handshake; the connection or -1 (see net_error) |  |
| `tls_connect_poll(tls)` | `LONG` | Go on with tls_connect_start: 1 done (certificate verified), 0 not yet, -1 failed (the TLS connection is freed; see net_error) |  |
| `tls_send(tls, text)` | `LONG` | Send the whole text; bytes sent or -1 |  |
| `tls_send_buffer(tls, buffer, length)` | `LONG` | Send length bytes of a buffer; bytes sent or -1 |  |
| `tls_recv(tls, max, timeout_ms)` | `STRPTR` | Like net_recv: "" if nothing came in time, nil once closed |  |
| `tls_recv_buffer(tls, buffer, max, timeout_ms)` | `LONG` | Like net_recv_buffer: the count, 0 on time out, -1 once closed |  |
| `tls_close(tls)` | `void` | End TLS on the connection (net_close the socket after) |  |
| `tls_resumed(tls)` | `BOOL` | True if the connection resumed an earlier session with the same server (no key exchange) |  |

## Fuentes y colores

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `font_open(name, size)` | `LONG` | Open a font ("helvetica.font", size in pixels, at least 2): the font, or 0 if there is none |  |
| `font_use(font)` | `void` | Draw text with this font |  |
| `font_close(font)` | `void` | Close a font (the open ones close at exit) |  |
| `font_style(style)` | `void` | Text style: 0 plain, +1 underlined, +2 bold, +4 italic |  |
| `font_height()` | `LONG` | Height of the current font |  |
| `font_baseline()` | `LONG` | Pixels from the top of the text to its baseline |  |
| `font_text_width(text)` | `LONG` | Width of a text in pixels with the current font and style |  |
| `font_size(font)` | `LONG` | Size the system gave for this font (the nearest it has) |  |
| `color_pen(r, g, b)` | `LONG` | Pen with the color closest to r, g, b (0-255) on the screen drawn on; for gfx_pen |  |

## Transparencia y degradados

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `gfx_blend_rect(x1, y1, x2, y2, rgb, alpha)` | `void` | Mix the color 0xRRGGBB with what is drawn, alpha 0-255 (palette screens: a 4x4 dither of the closest pen) |  |
| `gfx_gradient_rect(x1, y1, x2, y2, rgb1, alpha1, rgb2, alpha2, vertical)` | `void` | Gradient from (rgb1, alpha1) to (rgb2, alpha2), top to bottom if vertical, else left to right, mixed with what is drawn |  |
| `gfx_pixel_rgb(x, y)` | `LONG` | Color of a pixel as 0xRRGGBB (on a palette screen, its pen's color) |  |

## Imágenes RGB desde un buffer (vídeo)

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `gfx_rgb_draw(buffer, width, height, x, y)` | `void` | Draw an RGB24 buffer (3 bytes a pixel, rows one after another) at x, y (RTG: in one WritePixelArray; palette screens: the closest pens) |  |
| `gfx_rgb_draw_scaled(buffer, width, height, x, y, dest_width, dest_height)` | `void` | Draw an RGB24 buffer at x, y as dest_width x dest_height (nearest pixel, row by row) |  |

## Tareas (C en otro proceso)

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `task_start(func, arg)` | `LONG` | Run an @native function f(arg: Int) -> Int in another process (C only: malloc/free yes, Dash strings and lists no; 128 KB of stack, the program's priority): the task, or 0 |  |
| `task_start_with(func, arg, stack, priority)` | `LONG` | task_start with its stack in bytes (0: 128 KB) and its priority relative to the program's (-1: it only runs when the program waits) |  |
| `task_done(task)` | `BOOL` | True once the function has returned (does not wait) |  |
| `desktop_canvas(x, y, width, height)` | `APTR` | An area of the Workbench's desktop (below the screen's title bar), behind the icons and without clicks, in backdrop mode or not, planar or RTG; negative x or y: from the right or bottom edge (-1 touches it). 0 if it cannot be |  |
| `desktop_canvas_on_draw(canvas, func)` | `void` | Function f(x, y, width, height) that draws the area with gfx_ (from 0, 0), over the wallpaper below it |  |
| `desktop_canvas_update(canvas)` | `void` | Draw the area again now and show what changed, without touching the icons |  |
| `desktop_canvas_update_area(canvas, x, y, width, height)` | `void` | desktop_canvas_update only in that part of the area: the drawing is clipped to it and only it is compared (the rest stays as it was) |  |
| `desktop_canvas_free(canvas)` | `void` | The wallpaper back in the area (the program's end does it too) |  |
| `break_check()` | `BOOL` | True if Ctrl-C came ("Break" in the Shell, or another copy: single_instance); it is cleared |  |
| `single_instance(name)` | `BOOL` | One copy at a time: false if another copy of the program (a public port with that name) runs, which gets Ctrl-C; true otherwise (the port is the program's until it ends) |  |
| `tooltype(name, default)` | `STRPTR` | A tooltype of the program: from the Shell, the argument NAME=value (NAME="a b" too); else (or from the Workbench) the tooltype of its icon; default if it is in neither |  |
| `cx_broker(name, title, description, priority)` | `BOOL` | The program in Exchange as a commodity, with Show and Hide, enabled (name up to 23 letters, title and description up to 39); false without commodities.library or with that name there. It goes at the program's end |  |
| `cx_hotkey(description)` | `BOOL` | The commodity's hotkey, from its description ("ctrl alt t"): cx_command gives 6 when it is pressed; false if the description is not valid (or there is no cx_broker); "" takes it away |  |
| `cx_command()` | `LONG` | The next command from Exchange or the hotkey: 0 none, 1 hide, 2 show, 3 disable, 4 enable, 5 kill, 6 hotkey. Disable and enable switch the commodity off and on (the hotkey too) |  |
| `cx_wait(ms)` | `LONG` | Waits, spending nothing, until a command comes (given as cx_command), Ctrl-C (-1, cleared) or ms milliseconds pass (0) |  |
| `disks_read(ms)` | `LONG` | Reads the mounted volumes (with a disk in) and their size and free space, asked to all at once and waiting ms milliseconds at most: how many there are. Nothing asks for a disk |  |
| `disk_name(i)` | `STRPTR` | The name of volume i (0 to disks_read() - 1) of the last disks_read, without the colon |  |
| `disk_kb(i)` | `LONG` | The size of volume i in KB (as Info shows it); -1 if it did not answer in time |  |
| `disk_free_kb(i)` | `LONG` | The free space of volume i in KB; -1 if it did not answer in time |  |
| `net_ifs_read()` | `LONG` | Reads the network interfaces of Roadshow (lo0 included), their state and bytes: how many; -1 without a TCP/IP stack or with one that does not tell (AmiTCP, Miami) |  |
| `net_if_name(i)` | `STRPTR` | The name of interface i (0 to net_ifs_read() - 1) of the last net_ifs_read |  |
| `net_if_up(i)` | `BOOL` | True if interface i is up (connected) |  |
| `net_if_bytes_in(i)` | `LONG` | The bytes received by interface i (the low 32 bits: the difference of two readings is the bytes in between, even past 2 GB) |  |
| `net_if_bytes_out(i)` | `LONG` | The bytes sent by interface i (the low 32 bits, like net_if_bytes_in) |  |
| `wifi_read(interface, ms)` | `LONG` | Asks the SANA-II driver of a Roadshow interface for its WiFi signal, waiting ms milliseconds at most: 0 read (wifi_signal, wifi_noise), 1 no answer in time, 2 the driver does not tell, 3 no such interface, 4 the driver gives an error (offline), 5 the stack has the driver only for itself, -1 no Roadshow |  |
| `wifi_read_device(driver, unit, ms)` | `LONG` | Like wifi_read, asking a SANA-II driver that is in use ("wifipi.device", unit 0) directly, with any TCP/IP stack: 0 read, 1 no answer in time, 2 the driver does not tell, 3 no such driver in use, 4 offline, 5 the stack has it only for itself |  |
| `net_drivers_read()` | `LONG` | Reads the SANA-II network drivers in use, with any TCP/IP stack (the ones of DEVS:Networks that something has open): how many |  |
| `net_driver_name(i)` | `STRPTR` | The name of driver i (0 to net_drivers_read() - 1) of the last net_drivers_read ("wifipi.device") |  |
| `net_driver_read(driver, unit, ms)` | `LONG` | Asks a SANA-II driver in use for its packets in and out, waiting ms at most: the codes of wifi_read_device (0 read: net_driver_packets_in, net_driver_packets_out) |  |
| `net_driver_packets_in()` | `LONG` | The packets received by the driver of the last net_driver_read that gave 0 |  |
| `net_driver_packets_out()` | `LONG` | The packets sent by the driver of the last net_driver_read that gave 0 |  |
| `wifi_signal()` | `LONG` | The signal level of the last wifi_read that gave 0, in dBm (-30 very good, -90 very bad) |  |
| `wifi_noise()` | `LONG` | The noise level of the last wifi_read that gave 0, in dBm |  |
| `usb_hid_read()` | `LONG` | Reads the USB devices (each interface) that Poseidon's hid.class handles: how many; -1 without poseidon.library 4 |  |
| `usb_hid_name(i)` | `STRPTR` | The product name of USB device i (0 to usb_hid_read() - 1) of the last usb_hid_read |  |
| `usb_hid_maker(i)` | `STRPTR` | The manufacturer of USB device i |  |
| `usb_hid_vendor(i)` | `LONG` | The VendorID of USB device i |  |
| `usb_hid_product(i)` | `LONG` | The ProductID of USB device i |  |
| `usb_hid_kind(i)` | `LONG` | What USB device i is: 1 mouse, 2 keyboard, 0 other (many trackpads) |  |
| `usb_hid_emitter(i)` | `LONG` | The emitter of USB device i: the number of the hid.class task that sends its moves, for mouse_curve |  |
| `mouse_curve(emitter, factors)` | `BOOL` | The acceleration curve of a mouse: emitter 0 is the Amiga mouse (and every move not from a USB mouse), else a usb_hid_emitter. factors: a list of hundredths (100 = as it comes), entry i for a move of i units, the last one from there on (up to 32); [] takes it away. The fractions left are kept. False if input.device does not open or there are 16 emitters already |  |
| `mouse_curve_events(emitter)` | `LONG` | How many moves an emitter's curve has scaled |  |
| `mouse_curves_off()` | `void` | Takes the curves out of input.device now (the program's end does it too); a mouse_curve puts them back. Under another program's patch, a stub that passes everything through stays |  |
| `mouse_patch_left()` | `LONG` | How many stubs were left under another program's patch of input.device (they pass everything through, for good) |  |
| `mouse_prefs_ticks()` | `LONG` | The system's mouse speed (Input preferences): 1 fastest, 2, 4 slowest |  |
| `mouse_prefs_accel()` | `BOOL` | True if the system's mouse acceleration (Input preferences) is on |  |
| `mouse_prefs_set(ticks, accel)` | `void` | Sets the system's mouse speed and acceleration; they go back as they were at the program's end |  |
| `tr(id, text)` | `STRPTR` | The text number id of the program's catalog (@catalog) in the user's language; text (the program's own) without a catalog, without that number or without locale.library |  |
| `catalog_open(name, version)` | `BOOL` | Opens another catalog ("X.catalog", version 0: any) in the user's languages instead of the one in use; false if there is none (tr gives the program's own texts) |  |
| `catalog_language()` | `STRPTR` | The language of the catalog in use ("english"), "" without one |  |
| `dos_requesters(on)` | `void` | false: no "Insert volume" or disk error requesters for this program (the call fails instead); true: as before. The program's end puts them back |  |
| `base64_to_file(text, file)` | `LONG` | Write the bytes of base64 text to a file (spaces and line ends skipped, = padding or not): the bytes written, or -1 if the text is not base64 (no file then) or the file cannot be written |  |
| `cpu_start()` | `BOOL` | Start counting the CPU of every task (exec's switch hooks; a task with hooks of another program is not counted): false without EClock or before OS 2.04 |  |
| `cpu_sample()` | `LONG` | Take a sample: the number of tasks, with the CPU each took since the previous sample (or cpu_start), most first; also hooks the tasks started since |  |
| `cpu_task_name(i)` | `STRPTR` | Name of task i of the last sample, from 0 (of a Shell process, its command) |  |
| `cpu_task_load(i)` | `LONG` | CPU of task i of the last sample, per thousand |  |
| `cpu_total()` | `LONG` | CPU of all the counted tasks in the last sample, per thousand (the rest is idle) |  |
| `cpu_stop()` | `void` | Take the hooks out of the tasks (the program's end does it too) |  |
| `task_signal()` | `LONG` | Signal mask each task sends to the program when its function returns (for mui_wait_event_signals), 0 if none is free |  |
| `task_result(task)` | `LONG` | What the function returned (waits for it if it has not finished) |  |
| `task_free(task)` | `void` | Forget the task (waits for it if it is still running); the program waits for any left at exit |  |

## Imágenes (datatypes)

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `image_load(file)` | `LONG` | Picture from a file by datatypes (ILBM; PNG, GIF, JPEG if the system has them), with the colors of the screen drawn on: the image, or 0 |  |
| `image_width(image)` | `LONG` | Width of an image |  |
| `image_height(image)` | `LONG` | Height of an image |  |
| `image_draw(image, x, y)` | `void` | Draw an image at x, y (its transparent pixels are not drawn) |  |
| `image_draw_part(image, sx, sy, x, y, w, h)` | `void` | Draw the part w x h at sx, sy of an image at x, y |  |
| `image_scale(image, w, h)` | `LONG` | A copy of an image at w x h pixels: a new image, or 0 |  |
| `image_free(image)` | `void` | Free an image (the ones left are freed at exit) |  |
| `image_from_rgb(buffer, width, height, alpha)` | `LONG` | An image from pixels in a buffer (RGB, or RGBA with alpha: mixed with what is under it on RTG, drawn from 128 on a palette screen), with the colors of the screen: the image, or 0 (needs picture.datatype V43, AmigaOS 3.5+, except on RTG screens) |  |

## Argumentos

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `arg_count()` | `LONG` | How many arguments the program got from the Shell (0 from the Workbench) |  |
| `arg(i)` | `STRPTR` | Argument i, from 0 ("" if there is none) |  |
| `click_x()` | `LONG` | X of the last On Click, in the window (inside its borders) |  |
| `click_y()` | `LONG` | Y of the last On Click, in the window (inside its borders) |  |
| `time_ms()` | `LONG` | Milliseconds since the program started (EClock of timer.device) |  |

## Audio

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `sound_load(id, filename)` | `BOOL` | Load an IFF 8SVX sound (uncompressed) |  |
| `sound_sample(id, index, value)` | `void` | Set one sample (-128..127) of a sound made with sound_create |  |
| `sound_create(id, length, rate)` | `BOOL` | Create a silent sound in chip memory: length in samples, rate in samples per second |  |
| `sound_free(id)` | `void` | Free sound memory |  |
| `sound_play(id, channel)` | `void` | Play a sound once on a channel (0-3) |  |
| `sound_stop(channel)` | `void` | Stop channel |  |
| `sound_loop(id, channel)` | `void` | Play a sound looped on a channel (until sound_stop) |  |
| `sound_playing(channel)` | `BOOL` | Check if channel is playing |  |
| `sound_volume(channel, vol)` | `void` | Set channel volume (0-64) |  |
| `sound_period(channel, period)` | `void` | Set the channel period (pitch: lower = higher) |  |
| `music_load(filename)` | `BOOL` | Load MOD file |  |
| `music_play()` | `void` | Start music playback |  |
| `music_stop()` | `void` | Stop music |  |
| `music_pause()` | `void` | Pause music |  |
| `music_resume()` | `void` | Resume music |  |
| `music_volume(vol)` | `void` | Set music volume (0-64) |  |
| `music_position(pos)` | `void` | Set music position |  |
| `music_pos()` | `LONG` | Song position the music is playing (index in the order list) |  |
| `music_row()` | `LONG` | Pattern row the music is playing (0-63) |  |
| `music_free()` | `void` | Free music data |  |
| `tone_play(channel, freq, vol, duration)` | `void` | Play a sine tone: frequency in Hz, volume 0-64, duration in milliseconds (returns at once) |  |

## Intuition

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `window_create(title, x, y, w, h, flags)` | `LONG` | Open a window, returns its handle 1..16 (0 = failed); flags: 1 resizable, 2 borderless, 4 no close gadget, 8 w and h are the inside (without the borders). It becomes the current window |  |
| `window_border_top()` | `LONG` | The top border of the current window (title bar included); gadgets count from the inside, without it |  |
| `window_border_bottom()` | `LONG` | The bottom border of the current window |  |
| `window_border_left()` | `LONG` | The left border of the current window |  |
| `window_border_right()` | `LONG` | The right border of the current window |  |
| `screen_font_height()` | `LONG` | The height of the screen's font (the program's screen, or the Workbench's): the one of title bars and of GadTools gadgets |  |
| `screen_font_text_width(text)` | `LONG` | The width of a text in the screen's font |  |
| `window_close(handle)` | `void` | Close window (handle 0: current window) |  |
| `window_title(handle, title)` | `void` | Set window title (handle 0: current window) |  |
| `window_move(handle, x, y)` | `void` | Move window to x, y (absolute; handle 0: current window) |  |
| `window_resize(handle, w, h)` | `void` | Resize window to w x h (handle 0: current window) |  |
| `window_to_front(handle)` | `void` | Bring window to front (handle 0: current window) |  |
| `window_to_back(handle)` | `void` | Send window to back (handle 0: current window) |  |
| `window_activate(handle)` | `void` | Activate window (handle 0: current window) |  |
| `screen_to_front()` | `void` | Bring custom screen to front |  |
| `screen_to_back()` | `void` | Send custom screen to back |  |
| `gadget_id()` | `LONG` | Handle of the last gadget used (for On Gadget in the EventLoop) |  |
| `gadget_width(gadget)` | `LONG` | Width of a gadget in pixels (also when it was created with width 0) |  |
| `gadget_height(gadget)` | `LONG` | Height of a gadget in pixels (also when it was created with height 0) |  |
| `button_create(win, x, y, w, h, label)` | `LONG` | Create button gadget |  |
| `button_enable(gad)` | `void` | Enable button |  |
| `button_disable(gad)` | `void` | Disable button |  |
| `textfield_create(win, x, y, w, h, maxlen)` | `LONG` | Create text input field |  |
| `textfield_get(gad)` | `STRPTR` | Get text field content |  |
| `textfield_set(gad, text)` | `void` | Set text field content |  |
| `checkbox_create(win, x, y, label)` | `LONG` | Create checkbox |  |
| `checkbox_get(gad)` | `BOOL` | Get checkbox state |  |
| `checkbox_set(gad, state)` | `void` | Set checkbox state |  |
| `slider_create(win, x, y, w, h, min, max, value)` | `LONG` | Create slider |  |
| `slider_get(gad)` | `LONG` | Get slider value |  |
| `slider_set(gad, value)` | `void` | Set slider value |  |
| `listview_create(win, x, y, w, h)` | `LONG` | Create listview |  |
| `listview_add(gad, text)` | `void` | Add item to listview |  |
| `listview_clear(gad)` | `void` | Clear listview |  |
| `listview_selected(gad)` | `LONG` | Get selected index (-1 if none) |  |
| `cycle_create(win, x, y, w, h, options)` | `LONG` | Create cycle gadget; options separated by \| (value = option, from 0) |  |
| `cycle_get(gad)` | `LONG` | Get selected option of a cycle gadget |  |
| `cycle_set(gad, index)` | `void` | Select an option of a cycle gadget |  |
| `radio_create(win, x, y, options)` | `LONG` | Create radio buttons (one per option, separated by \|) |  |
| `radio_get(gad)` | `LONG` | Get selected radio button |  |
| `radio_set(gad, index)` | `void` | Select a radio button |  |
| `integer_create(win, x, y, w, h, value)` | `LONG` | Create integer input field |  |
| `integer_get(gad)` | `LONG` | Get integer field value |  |
| `integer_set(gad, value)` | `void` | Set integer field value |  |
| `palette_create(win, x, y, w, h, depth)` | `LONG` | Create colour palette gadget (2^depth colours) |  |
| `palette_get(gad)` | `LONG` | Get selected colour |  |
| `palette_set(gad, color)` | `void` | Select a colour |  |
| `number_create(win, x, y, w, h, value)` | `LONG` | Create a box that shows a number |  |
| `number_set(gad, value)` | `void` | Change the number shown |  |
| `dialog_file(title, pattern, save_mode)` | `STRPTR` | File requester: full path of the chosen file, "" if cancelled (save_mode true: save requester) |  |
| `dialog_color(title, initial)` | `LONG` | Palette window: returns the chosen pen (click, or arrows + Return); Esc keeps initial |  |
| `dialog_font(title)` | `STRPTR` | Font requester: "name.font/size", "" if cancelled |  |

## RTG (CyberGraphX / Picasso96)

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `rtg_available()` | `BOOL` | Check if CyberGraphX or Picasso96 is available |  |
| `rtg_is_active()` | `BOOL` | Check if current screen is using RTG |  |
| `rtg_get_depth()` | `LONG` | Get current screen bit depth |  |
| `rtg_get_width()` | `LONG` | Get current screen width |  |
| `rtg_get_height()` | `LONG` | Get current screen height |  |
| `rtg_alloc_bitmap(width, height, depth)` | `APTR` | Allocate RTG-compatible bitmap |  |
| `rtg_free_bitmap(bitmap)` | `void` | Free RTG bitmap |  |
| `rtg_write_pixel(x, y, rgb)` | `void` | Write single pixel with 24-bit RGB color |  |
| `rtg_read_pixel(x, y)` | `LONG` | Read pixel, returns 24-bit RGB color |  |
| `rtg_fill_rect(x, y, w, h, rgb)` | `void` | Fill rectangle with 24-bit RGB color |  |
| `rtg_write_array(buffer, bpr, x, y, w, h)` | `void` | Write pixel array (buffer is ARGB 32-bit, bpr is bytes per row) |  |
| `rtg_read_array(buffer, bpr, x, y, w, h)` | `void` | Read pixel array from screen into buffer |  |
| `rtg_rgb(r, g, b)` | `LONG` | Create 24-bit RGB color value from components |  |
| `rtg_argb(a, r, g, b)` | `LONG` | Create 32-bit ARGB color value from components |  |
| `rtg_rgb_r(color)` | `LONG` | Extract red component from RGB color |  |
| `rtg_rgb_g(color)` | `LONG` | Extract green component from RGB color |  |
| `rtg_rgb_b(color)` | `LONG` | Extract blue component from RGB color |  |
| `rtg_best_mode(width, height, depth)` | `LONG` | Find best RTG display mode for given dimensions |  |
| `rtg_open_screen(width, height, depth, title)` | `BOOL` | Open RTG screen with specified dimensions |  |
| `rtg_blit(src, sx, sy, dx, dy, w, h)` | `void` | Blit from bitmap to screen |  |
| `rtg_scale_blit(src, sx, sy, sw, sh, dx, dy, dw, dh)` | `void` | Scaled blit from bitmap to screen |  |

## MUI

| Función | Devuelve | Descripción | Estado |
|---|---|---|---|
| `mui_app_begin(title, base)` | `APTR` | Open muimaster.library and create the MUI application (base: ARexx name); 0 if MUI is missing or the CPU is a 68000 |  |
| `mui_app_end()` | `void` | Dispose the application with its windows and objects, close MUI (also done at exit) |  |
| `mui_window_begin(title, id)` | `APTR` | Start a window (id 1-255: MUI remembers its size and place; 0 none) with a vertical root group |  |
| `mui_window_end()` | `void` | End the window started with mui_window_begin |  |
| `mui_window_open(win)` | `LONG` | Open a window; false if it could not open |  |
| `mui_window_close(win)` | `void` | Close a window (it still exists) |  |
| `mui_window_active(win)` | `LONG` | 1 if the window is the active one (several windows from one .dashui share event numbers; dashweb D32) |  |
| `mui_vgroup_begin()` | `APTR` | Start a vertical group inside the open group |  |
| `mui_hgroup_begin()` | `APTR` | Start a horizontal group inside the open group |  |
| `mui_group_end()` | `void` | End the open group |  |
| `mui_text(text)` | `APTR` | Text object (MUI text codes allowed) |  |
| `mui_button(label)` | `APTR` | Button (an underscore before a letter makes it the keyboard shortcut) |  |
| `mui_on_press(obj, id)` | `void` | mui_wait_event returns id when the button is pressed |  |
| `mui_on_close(win, id)` | `void` | mui_wait_event returns id when the window's close gadget is clicked (default for the first window: -1) |  |
| `mui_press(obj)` | `void` | Send the mui_on_press event of a button as if it were pressed |  |
| `mui_label(text)` | `APTR` | Label for a form row (right-aligned) |  |
| `mui_string(initial, maxlen)` | `APTR` | Text field with up to maxlen characters |  |
| `mui_checkbox(checked)` | `APTR` | Checkbox |  |
| `mui_cycle(options)` | `APTR` | Cycle gadget; options separated by \| ("One\|Two\|Three") |  |
| `mui_slider(min, max, value)` | `APTR` | Horizontal slider |  |
| `mui_gauge(max)` | `APTR` | Progress bar from 0 to max |  |
| `mui_get_value(obj)` | `LONG` | Value: checkbox 1/0, cycle option, slider level, progress |  |
| `mui_set_value(obj, value)` | `void` | Set the value (fires mui_on_change like the user would) |  |
| `mui_get_text(obj)` | `STRPTR` | Text of a text field, text, button or window title |  |
| `mui_set_text(obj, text)` | `void` | Change the text of a text field, text, button or window title |  |
| `mui_set_enabled(obj, enabled)` | `void` | Enable or disable (ghost) an object |  |
| `mui_on_change(obj, id)` | `void` | mui_wait_event returns id when the value or text changes |  |
| `mui_on_ack(obj, id)` | `void` | mui_wait_event returns id when Return is pressed in a text field |  |
| `mui_list()` | `APTR` | List of texts with scroller; its value is the selected line (-1 none) |  |
| `mui_list_add(list, text)` | `void` | Add a line at the end |  |
| `mui_list_insert(list, pos, text)` | `void` | Insert a line at pos (0 = first) |  |
| `mui_list_remove(list, pos)` | `void` | Remove the line at pos |  |
| `mui_list_clear(list)` | `void` | Remove all lines |  |
| `mui_list_count(list)` | `LONG` | Number of lines |  |
| `mui_list_get(list, pos)` | `STRPTR` | Text of the line at pos ("" outside the list) |  |
| `mui_list_quiet(list, quiet)` | `void` | While quiet the list is not redrawn (adding many lines) |  |
| `mui_on_double(list, id)` | `void` | mui_wait_event returns id on a double click in the list |  |
| `mui_frame_begin(title, horizontal)` | `APTR` | Start a group with a frame and a title ("" = none) |  |
| `mui_columns_begin(columns)` | `APTR` | Start a grid group with that many columns (forms: label, field...) |  |
| `mui_register_begin(titles)` | `APTR` | Start tabs ("One\|Two"); each child is a page; value = page shown |  |
| `mui_scroll_begin()` | `APTR` | Start an area with scrollbars (contents bigger than the window) |  |
| `mui_space()` | `APTR` | Empty space that takes what is left |  |
| `mui_balance()` | `APTR` | Bar the user drags to share the space between its neighbours |  |
| `mui_weight(obj, weight)` | `void` | Share of the free space an object gets (100 by default) |  |
| `mui_set_visible(obj, visible)` | `void` | Show or hide an object (the window relayouts) |  |
| `mui_menu_begin(title)` | `APTR` | Start a menu of the window being built |  |
| `mui_menu_item(title, key, id)` | `APTR` | Menu item: key = letter for Amiga+key ("" none); mui_wait_event returns id |  |
| `mui_menu_separator()` | `void` | Separator line in the menu |  |
| `mui_menu_end()` | `void` | End the menu |  |
| `mui_canvas(min_width, min_height)` | `APTR` | Drawing area (grows with the window); draw in it from mui_canvas_on_draw |  |
| `mui_canvas_on_draw(canvas, func)` | `void` | Function f(x, y, width, height) that draws the area with gfx_ (MUI calls it when needed) |  |
| `mui_canvas_on_input(canvas, id)` | `void` | mui_wait_event returns id on a click, wheel or key over the area (call before opening the window) |  |
| `mui_canvas_redraw(canvas)` | `void` | Draw the area again now |  |
| `mui_canvas_buffered(canvas, on)` | `void` | Draw the area in a bitmap of its own and show it at once when done (no half-drawn area; the same coordinates; mui_canvas_update still draws on the window) |  |
| `mui_canvas_update(canvas)` | `void` | Call the draw function now without clearing the area (it paints only what changed) |  |
| `mui_canvas_update_area(canvas, x, y, w, h)` | `void` | Like mui_canvas_update, only the zone w x h at x, y of the area (from its corner): the drawing is clipped to it and, with mui_canvas_buffered, only it goes from the buffer to the window |  |
| `mui_canvas_updating()` | `BOOL` | In the draw function: true if it runs for mui_canvas_update (the rest is still there) |  |
| `mui_canvas_on_move(canvas, id)` | `void` | mui_wait_event returns id when the pointer moves over the area or leaves it, without a click (the moves that come meanwhile make one; call before opening the window) |  |
| `mui_canvas_pointer_x(canvas)` | `LONG` | X of the pointer now, from the area's left edge (clicked or not) |  |
| `mui_canvas_pointer_y(canvas)` | `LONG` | Y of the pointer now, from the area's top edge (clicked or not) |  |
| `mui_canvas_pointer_inside(canvas)` | `BOOL` | True if the pointer is over the area now |  |
| `mui_canvas_mouse_x(canvas)` | `LONG` | X of the last click or wheel, from the area's left edge |  |
| `mui_canvas_mouse_y(canvas)` | `LONG` | Y of the last click or wheel, from the area's top edge |  |
| `mui_canvas_button(canvas)` | `LONG` | 1 if the last input was a left click, else 0 |  |
| `mui_canvas_wheel(canvas)` | `LONG` | +1 / -1 if the last input was the mouse wheel (up/down), else 0 |  |
| `mui_canvas_key(canvas)` | `LONG` | Raw key code of the last input, -1 if it was not a key |  |
| `mui_canvas_char(canvas)` | `STRPTR` | Character of the last key in the area, with shift and the keymap ("" if none; dashweb D31) |  |
| `mui_scrollbar(vertical)` | `APTR` | Scrollbar; its value is the first line shown |  |
| `mui_set_range(scrollbar, total, visible)` | `void` | Size of the document and of the part that fits |  |
| `mui_wait_event_signals(mask)` | `LONG` | Like mui_wait_event, but also returns 0 when one of the signals of mask arrives (sockets...); mui_signals says which |  |
| `mui_signals()` | `LONG` | Signals of the mask that woke the last mui_wait_event_signals |  |
| `mui_timer(ms, id)` | `void` | In ms milliseconds mui_wait_event returns id, once (again: call it again; 0 cancels) |  |
| `mui_image(file)` | `APTR` | Picture from a file through datatypes (ILBM; PNG, JPEG, GIF if their datatypes are installed); mui_set_text changes the file |  |
| `mui_image_button(file)` | `APTR` | Button with a picture (a toolbar icon; ILBM, or what the datatypes read): mui_on_press like a button, mui_set_text changes the picture |  |
| `mui_help(obj, text)` | `void` | Bubble help shown when the pointer rests on the object |  |
| `mui_window_size(win, width_pct, height_pct)` | `void` | Size of the window when it opens, in percent of the visible screen, centred (before mui_window_open) |  |
| `mui_window_fullscreen(win)` | `void` | The window over the whole screen: no borders, title bar or gadgets, active (before mui_window_open) |  |
| `mui_window_own_screen(win)` | `BOOL` | Full screen on a screen of its own, like the public one (before mui_window_open; false: on the public one) |  |
| `mui_width(obj)` | `LONG` | Width of an object on screen in pixels (0 before its window opens) |  |
| `mui_height(obj)` | `LONG` | Height of an object on screen in pixels (0 before its window opens) |  |
| `mui_wait_event()` | `LONG` | Wait for the next event and return its number; -1 to quit |  |
| `mui_poll_event()` | `LONG` | Like mui_wait_event without waiting: 0 when there is no event |  |
