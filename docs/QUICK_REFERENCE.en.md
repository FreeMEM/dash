# D.A.S.H. Language - Quick Reference Card

*English | [Castellano](QUICK_REFERENCE.md)*
> **D.A.S.H.** — *Development Amiga Synthesis Hub*

## Compile
```
./dash prog.dash -o prog            # gcc -O2, 68000, 16 KB stack minimum
./dash -O0 prog.dash -o prog        # no optimization (debugging)
./dash --small prog.dash -o prog    # gcc -Os: ~7% smaller, slower loops
./dash --profile ...                # at exit: calls and time (own, total) of each function
./dash --stack 32768 ...            # minimum stack (0: as the shell gives it)
                                    # @stack 262144 in a program or module: it needs at least that
                                    # @workbench_output "NIL:": from the Workbench, no console window
                                    # @catalog "X.catalog" 1 "español": tr(id, "texto") from locale.library's catalog
                                    # @version "Prog 1.2": $VER: (C:Version) with today's date; program_version()
./dash --fpu prog.dash -o prog      # 68020 + 68881/68882 FPU only
./dash --cpu 68040 prog.dash -o prog # 68020 code tuned for 68020/030/040/060
./dash --memcheck prog.dash -o prog # memory check: double frees, use after free, live at exit
./dash --debug ...                  # for gdb / VS Code: gcc -O0 -g, C lines mapped to .dash lines
./dash --multifile ...              # one C file per module instead of one for the whole program
./dash -q ...                       # quiet: only warnings, errors and the result (-v: verbose)
./dash --no-hunk ...                # skip the ELF to Hunk step (bebbo's gcc already writes Hunk)
DASH_TOOLCHAIN=/path ./dash ...     # bebbo's toolchain somewhere else than /opt/amiga
DASH_CFLAGS="-Os" ./dash ...        # extra gcc options
```
Programs need Kickstart 3.0+. A 68000 is enough, except for MUI 5 and AmiSSL (TLS), which need a 68020.

## Program Structure
```
import "lib/x.dash"         # Module (path relative to this file); "x.dashui": MUI windows
const NAME = value          # Constants
var total: Int = 0          # Global variable (type required); functions can read and change it
enum State IDLE,RUN end     # Enumerations (one line, or one value per line; = N optional)
struct Player x:Int end     # Structures
Window Win title "" end     # Windows
func name() end             # Functions
Main ... end                # Entry point
```

## Variables & Types
```
x = 42                      # Int
v = 1.5                     # Float (Int(v), Float(n), 7 significant digits)
d = Double(0.1)             # Double: 64 bits, 15-17 digits (Double(n), Double("2.5"), Int(d), Float(d))
h = sqrt(2.0)               # sqrt, pow, exp, log, sin, atan2, floor, round, fmod, abs, is_nan...: Double
f = Fixed(1.5)              # Fixed 16.16: fast decimals on 68000 (Int(f), fx_sqrt, fx_sin, fx_cos)
xs = [Fixed(0.5), 2]        # list of Fixed (numbers made Fixed); declared: var xs: [Fixed] = []
ds = [Double(0.1), 2]       # list of Double ([Double]); [1.5, 2] is a [Float]; var ds: [Double] = [1, 2]
mask = 0xFF                 # hex (also $DFF000), binary 0b1010
name = "Dash"               # String
active = true               # Bool: Print and "x " + b write true / false (a comparison too)
nums = [1,2,3]              # Array
player = Player(10,20)      # Struct instance
var lista: Nodo = nil       # nil: no struct/list/String (x == nil, x = nil)
```

## Operators
```
+  -  *  /  %               # Arithmetic
==  !=  <  >  <=  >=        # Comparison
and  or  not                # Logical
&  |  ^  ~  <<  >>          # Bits on Ints (^ xor, ~ complement, >> arithmetic); as in Python:
                            # shifts, &, ^, | between + - and the comparisons (a & 4 == 4)
const MASK = 1 << 4         # const: also an Int expression of numbers and earlier constants
+                           # String concatenation
"abc" < "abd"               # Strings: == != compare text, < > <= >= the order (strcmp)
```

## Text
```
s.length  s[i]  s[2:5]      # length, character, slice
Int(s[i])  str_code(s, i)   # character code (0-255)
str_char(65)                # "A"
str_find(s, "x")            # position or -1; str_find_from(s, "x", start)
regex_match("D.", s, false)  # whole text, ICU syntax; regex_find(p, s, from, icase) -1 / regex_length(); regex_error(); wildcard_match("*.ods", s, true)
str_starts(s, "a")  str_ends(s, "z")
str_lower(s)  str_upper(s)  str_trim(s)
Int("42")  str_to_int("ff", 16)  str_from_int(255, 16)
str_replace(s, "a", "b")
str_contains(s, "x")        # Bool
str_split("a,b,c", ",")     # ["a", "b", "c"]: a new [String]; sep "" or not found: [s]
"n=#{n} len #{v.length} #{f(x) + 1}"   # interpolation: any expression; quotes inside as \"
s = s + "x"                 # appends in place: building a text in a loop is linear
s = t.texto                 # copies the text; f(t.texto) does not if no code sets that field
t = file_read_text("f.html")   # whole file (nil if missing); file_write_text("f", t)
str_from_buffer(buf, 0, n)  str_to_buffer(s, buf, 0)
```

## Control Flow
```
if cond                     while cond
    ...                         ...
end                         end

if cond                     for i in (1..10)
    ...                         ...
elif cond                   end
    ...
else                        for i in (10..1)       # down
                            for i in (0..n step 2)
    ...                     for i in (10..0 step -2)   # down with step: negative
                            for item in array
end                             ...
                            end

break / continue            # inside while/for only
```

## Functions
```
func add(a, b)              func typed(x: Int) -> Int   # Int Float String Bool Array Pointer Func Void, struct, enum, [T], {String: T}, {Int: T}
    return a + b                return x * 2
end                         end

doble = fn(x) -> x * 2      # lambda; also fn(x) ... return ... end
func aplica(f: Func, v: Int) -> Int   # a function as a value: aplica(doble, 4)
    return f(v)             # lambdas cannot use local variables from outside (globals yes)
end
```

C code: `@native func f(x: Int) -> Int """ return x; """ end` (a function in C), `@extern("x.library")`,
`@native(borrow) func ...` (the C only uses its arguments during the call: they are not kept until
exit), `@header "#include <x.h>"`, `@link "lib/x.c"` (a C source, object or library linked with the program; its
directory goes to `-I`), `@c """ ... """ end` (C at top level, after the Dash prototypes: callbacks).

## Structs with Methods
```
struct Enemy
    x: Int = 0
    health: Int = 100

    func move(dx)
        self.x = self.x + dx
    end
end

enemy = Enemy(10, 50)
enemy.move(5)
boss.pos.x = 5              # nested structs (pos: Punto); l[0].x = 5 (a field of a list element)
d["k"].push(x)              # methods of elements too: l[0].mover(1), filas[i].clear()
# weak padre: Nodo          # field that points without holding (no cycles: parent pointers)
```

## Interfaces
```
interface Orden             # methods only; no fields, no Orden()
    func deshacer() -> String
end
struct Escribir: Orden      # has its methods, same parameters and return (struct C: Figura, Orden)
    ...
end
var pila: [Orden] = []      # any struct that has it; o.deshacer() calls its struct's (a table per type)
```

## Arrays
```
arr = [1, 2, 3, 4, 5]
arr[0]                      # Access: 1
arr[2] = 99                 # Modify
arr.length                  # Length: 5
arr[1:3]                    # Slice: [2, 3]
arr + [6, 7]                # New list with both (same element type)
var l: [String] = []        # list types [T]: [Int] [String] [Nodo] [[Int]] (params, returns, fields)
for x in obj.lista          # for-each over any list expression
l.push(x)  l.pop()  l.insert(i, x)  l.remove(i)  l.clear()   # lists that grow
l.sort(f)                   # stable; f(a, b) -> Bool (a before b) or Int (<0 before, 0 equal, >0 after)
d = {"a": 1, "b": 2}        # dictionary {String: T}: d["c"] = 3, d["a"], d.has("a"),
d.remove("a")  d.keys()  d.clear()  d.length    # missing key: 0 / nil
d.get("c", 0)                # the value, or the default if missing (one lookup; objects: nil only)
e = {1: "uno", 7: "siete"}   # Int keys: {Int: T} (var e: {Int: String} = {}), same methods; keys() is [Int]
"Hola Dash"[5:]             # Strings too: "Dash"
```

## Window & Events
```
Window MyWin
    title "App"
    width 320
    height 200
end

Main
    MyWin.open
    EventLoop
        On Key "ESC"        # also "a", 0x4C, UP/DOWN/F1..., or no key = any
            Stop
        end
        On Menu            # menu_title/menu_item/menu_attach; menu_id() = item id
            Stop
        end
        On Click           # left button in the window: click_x(), click_y() inside the borders
        end
        On Timer 100       # every 100 ms (a number or a variable)
        end
        On Gadget          # gadget_id(): the gadget used; event_window(): its window (window_create)
        end
        On Close
            Stop
        end
    end
end
```

## Menus (Intuition)
```
menu_title("Project")       # builds the strip; menu_attach() puts it on the current window
menu_item("Quit", "Q", 9)   # Amiga+Q; menu_separator(), menu_sub(label, key, id)
menu_check_item("Grid", "G", 10)   # with a check mark: menu_checked(10) 1 / 0
menu_attach()               # then On Menu: menu_id(); menu_enable(id, false) ghosts an item
```

## MUI (68020+, MUI 3.8/5; SDK: tools/get_mui_sdk.sh)
```
app = mui_app_begin("App", "APP")       # 0 = no MUI / 68000
win = mui_window_begin("Title", 1)      # vertical root group; 1 = remember place
    mui_menu_begin("Project")           # menus of this window
        q = mui_menu_item("Quit", "Q", 9)   # mui_menu_separator()
        g = mui_menu_check("Grid", "G", 10, true)   # mui_get_value(g); mui_submenu_begin("Recent") ... mui_submenu_end()
        m = mui_context_menu_begin("Cells")   # items as above, mui_menu_end(); mui_set_context_menu(canvas, m): right button
    mui_menu_end()
    tabs = mui_register_begin("A|B")    # pages; value = page. Also mui_frame_begin("T", false),
    ...                                 # mui_columns_begin(2), mui_scroll_begin(); mui_group_end()
    mui_space()                         # mui_balance(), mui_weight(obj, 30), mui_set_visible(obj, 0)
    mui_text("Hello")
    mui_hgroup_begin()                  # mui_vgroup_begin, mui_group_end
        ok = mui_button("_OK")
    mui_group_end()
mui_window_end()
url = mui_string("http://", 200)        # mui_label, mui_checkbox(0), mui_cycle("A|B"),
bar = mui_gauge(100)                    # mui_slider(min, max, v)
mui_set_value(bar, 40)                  # mui_get_value; mui_get_text/mui_set_text; mui_set_enabled
mui_on_change(url, 2)                   # mui_on_ack(url, id): Return in a text field
l = mui_list()                          # value = selected line (-1); mui_on_double(l, id)
mui_list_add(l, "x")                    # _insert(l, pos, s) _remove(l, pos) _clear _count _get(l, pos) _quiet
c = mui_canvas(320, 200)                # drawing area; sb = mui_scrollbar(true), mui_set_range(sb, total, vis)
mui_canvas_on_draw(c, paint)            # func paint(x, y, w, h) draws with gfx_; mui_canvas_redraw(c)
mui_canvas_on_input(c, 3)               # click/wheel/key: mui_canvas_mouse_x/_y(c), mui_canvas_button/_wheel/_key(c)
mui_canvas_char(c)                      # the key as text, with shift and the keymap ("" if none)
mui_canvas_qualifiers(c)                # keys held at the last input: 1 Shift, 2 Ctrl, 4 Alt, 8 Amiga, added up
mui_canvas_on_drag(c, id)               # event while dragging and when let go: mui_canvas_drag(c) 1 moving, 2 let go
mui_canvas_on_move(c, 4)                # the pointer over it (no click) or leaving: mui_canvas_pointer_x/_y/_inside(c)
mui_canvas_update(c)                    # draw again without clearing; mui_canvas_updating() true in paint
mui_canvas_update_area(c, x, y, w, h)   # the same, only that zone (clipped)
mui_canvas_buffered(c, true)            # draw in a bitmap of its own, shown at once when done
img = mui_image("Work:pic.png")         # datatypes; mui_width(obj), mui_height(obj) once open
b = mui_image_button("PROGDIR:atras.iff")   # icon button: mui_on_press; mui_help(b, "Atrás") bubble help
mui_window_size(win, 90, 80)            # % of the visible screen when it opens (before mui_window_open)
mui_window_fullscreen(win)              # whole screen, no borders or title bar (before mui_window_open)
mui_window_own_screen(win)              # the same on a new screen like the public one (false: not opened)
mui_on_press(ok, 1)                     # mui_on_close(win, id): default -1
mui_window_open(win)                    # mui_window_active(win): 1 if active; mui_window_close(win)
ev = mui_wait_event()                   # 1, or -1 = closed; mui_poll_event, mui_press(ok)
mui_timer(500, 7)                       # in 500 ms mui_wait_event returns 7 (once; 0 ms cancels)
ev = mui_wait_event_signals(mask)       # also returns 0 on one of those signals; mui_signals()
mui_app_end()                           # also at exit
import "win.dashui"                     # visual editor file: v = Main_create() (struct: v.window, named objects)
```

## Graphics Functions
```
gfx_pen(color)              # Set draw color (0-31)
gfx_rgb(idx, r, g, b)       # Set palette (0-15 each)

gfx_pixel(x, y)             # Draw pixel
gfx_line(x1,y1, x2,y2)      # Draw line
gfx_rect(x1,y1, x2,y2)      # Filled rectangle
gfx_box(x1,y1, x2,y2)       # Rectangle outline
gfx_circle(cx, cy, r)       # Circle outline
gfx_circle_fill(cx, cy, r)  # Filled circle
gfx_ellipse(cx,cy, rx,ry)   # Ellipse outline
gfx_ellipse_fill(cx,cy,rx,ry) # Filled ellipse

gfx_poly_begin(x, y)        # Start polygon
gfx_poly_add(x, y)          # Add vertex
gfx_poly_end()              # Close & fill

gfx_move(x, y)  gfx_draw(x, y)          # line from the cursor; gfx_text("t") at the cursor
gfx_pixel_read(x, y)        # pen of a pixel; gfx_flood(x, y, mode)
gfx_scroll(dx, dy, x1, y1, x2, y2)  gfx_copy(sx, sy, w, h, dx, dy)   # move or copy an area
gfx_pen_bg(c)  gfx_pen_outline(c)  gfx_mode(m)  gfx_pattern(0xF0F0)  gfx_rgb8(idx, r, g, b)   # 0-255 (AGA)

gfx_text_at(x, y, "text")   # Draw text
f = font_open("helvetica.font", 13) # font_use(f), font_style(2), font_text_width(s), font_height()
                            # font_size(f) (the size it got), font_baseline(), font_close(f)
color_pen(r, g, b)          # pen for an RGB color (0-255) on the screen drawn on
gfx_blend_rect(x1, y1, x2, y2, 0xRRGGBB, alpha)        # mixed with what is there (alpha 0-255)
gfx_gradient_rect(x1, y1, x2, y2, rgb1, a1, rgb2, a2, vertical)   # RTG: real mix; palette: 4x4 dither
gfx_pixel_rgb(x, y)         # 0xRRGGBB of a pixel
gfx_rgb_draw(buf, w, h, x, y)              # RGB24 buffer (video frame); RTG: WritePixelArray
gfx_rgb_draw_scaled(buf, w, h, x, y, dw, dh)   # scaled, nearest pixel
img = image_load("a.png")   # datatypes (0: cannot read); image_width/_height(img)
image_draw(img, x, y)       # image_draw_part(img, sx, sy, x, y, w, h), image_scale(img, w, h), image_free(img)
img = image_from_rgb(buf, w, h, alfa)   # pixels RGB (or RGBA) in a buffer; picture.datatype V43 (3.5+), else 0
gfx_clear()                 # Clear screen; gfx_clear_color(c)
```

## Sprites, BOBs, Copper, Bitmaps
```
sprite_load(0, "nave.iff")  # hardware sprite: 16-pixel frames side by side; sprite_frame(0, n)
sprite_pos(0, x, y)  sprite_show(0)  sprite_hide(0)  sprite_collision(0, 1)  sprite_free(0)
sprite_create(0, 16, h)  sprite_set_row(0, row, plane0, plane1)  sprite_color(0, i, r, g, b)
soft_sprite_create(1, w, h, depth)   # drawn by software (also RTG): soft_sprite_pixel/_row/_pos/_show/_hide
bob_load(2, "bola.iff")     # bob_create(id, w, h, depth); bob_pos, bob_draw, bob_erase, bob_frame, bob_collision
copper_create(64)           # copper_wait(y, x), copper_move(reg, v), copper_color(0, 0xF00) (12-bit RGB),
copper_end()  copper_install()   # copper_free()
bitmap_load(3, "fondo.iff") # bitmap_create(id, w, h, depth), bitmap_save(id, "f"), bitmap_free(id)
bitmap_blit(3, sx, sy, w, h, dx, dy)   # to the screen; bitmap_blit_mask(src, mask, ...)
bitmap_draw_to(3) ... bitmap_draw_screen()   # gfx_ draws into the bitmap, then on the screen again
```

## RTG (CyberGraphX / Picasso96)
```
rtg_available()  rtg_is_active()     # a card library is there; the screen is on the card
rtg_open_screen(640, 480, 24, "T")   # rtg_best_mode(w, h, depth); rtg_get_width/_height/_depth()
rtg_write_pixel(x, y, 0xRRGGBB)  rtg_read_pixel(x, y)  rtg_fill_rect(x, y, w, h, rgb)
rtg_write_array(buf, bpr, x, y, w, h)   # ARGB 32-bit buffer, bpr bytes a row; rtg_read_array
bm = rtg_alloc_bitmap(w, h, 32)      # rtg_blit(bm, sx, sy, dx, dy, w, h), rtg_scale_blit, rtg_free_bitmap(bm)
rtg_rgb(r, g, b)  rtg_argb(a, r, g, b)  rtg_rgb_r/_g/_b(c)
```

## Screens, Windows and Gadgets (Intuition, GadTools)
```
screen_open(4, "Title")     # a screen like the Workbench's, 16 colors; screen_close()
screen_open_custom(w, h, depth, "Title")
screen_width()  screen_height()  screen_to_front()  screen_to_back()
v = window_create("T", x, y, w, h, 8)   # flag 8: w and h are the inside; window_border_top/bottom/left/right()
h = screen_font_height()    # the screen's font (title bars, gt_* gadgets); screen_font_text_width(text)
b = button_create(0, x, y, 0, 0, "_Save")   # w/h 0: measured with the screen font; "_": S presses it
gadget_width(b)  gadget_height(b)           # its size, to place the next one
window_move(v, x, y)  window_resize(v, w, h)  window_title(v, "T")  window_close(v)   # v 0: current window
window_to_front(v)  window_to_back(v)  window_activate(v)
t = textfield_create(v, x, y, w, h, 80)     # textfield_get(t), textfield_set(t, s); button_enable/_disable(b)
# also checkbox_, slider_, listview_, cycle_, radio_, integer_, palette_, number_create, with _get/_set
f = dialog_file("Load", "#?.txt", false)    # path or "" (true: save); dialog_font(title), dialog_color(title, pen)
file_open_dialog("Load", "#?")              # ASL (file_save_dialog too); then file_fullpath(), file_get_path(), file_get_name()
```
`gt_*` (one window, gadgets by id): `gt_init()` after opening it; `gt_button`, `gt_checkbox`, `gt_string`,
`gt_integer`, `gt_slider`, `gt_cycle`, `gt_palette`, `gt_text` (x, y, w, h, label, ...); `gt_attach()`;
`ev = gt_wait_event()` (id, -2 = close; `gt_event()` without waiting); `gt_get_value`, `gt_set_value`,
`gt_get_string`, `gt_set_text`, `gt_enable`, `gt_disable`; `gt_cleanup()`.

## ReAction (up to 4 windows; window.class V44: OS 3.5+, tested on 3.2)
```
w = ra_window_create("T", 300, 200)  # 1-4 (0: failed), the current one; ra_window_use(w), ra_event_window()
ra_layout_hgroup_begin() ... ra_layout_group_end()   # also _vgroup_begin, _hgroup_weighted(n)
ra_add_button(1, "OK")  ra_add_string(2, "", 64)  ra_add_checkbox(3, "On", 0)  ra_add_slider(4, 0, 100, 50)
# also ra_add_integer, _label, _palette, _chooser, _scroller, _listbrowser, _radio, _clicktab, _fuelgauge, _getfile
ra_menu_title("Project")  ra_menu_item("Quit", "Q", 9)   # event RA_EVENT_MENU(), then ra_menu_id()
ra_window_open()
ev = ra_wait_event()                 # gadget id or RA_EVENT_CLOSE(); ra_handle_events() does not wait
ra_get_value(4)  ra_set_value(4, 10)  ra_get_string(2)  ra_set_string(2, "x")  ra_enable_gadget(1)
ra_window_close()
```

## Input Functions
```
# Keyboard
key_pressed()               # Bool: key waiting? (only looks; key_get takes it)
key_get()                   # Get key code (0 if none)
key_wait()                  # Wait for key; wait_key() returns it
key_raw()  key_text(code)   # raw code; a code as text
check_lmb()  check_rmb()  check_esc()   # straight from the hardware, no events; wait_click()

# Mouse
mouse_x()                   # X position
mouse_y()                   # Y position
mouse_button(0)             # Left button (0=left, 1=right)

# Joystick (port 0 or 1)
joy_x(0)                    # X: -1, 0, or 1
joy_y(0)                    # Y: -1, 0, or 1
joy_button(0)               # Fire button (joy_fire(0) too)
joy_up(0) joy_down(0)       # Direction bools
joy_left(0) joy_right(0)
```

## Audio Functions
```
sound_load(id, "file.8svx") # Load an IFF 8SVX sound
sound_create(id, len, rate) # Silent sound in chip RAM; sound_sample(id, i, v) fills it
sound_play(id, channel)     # Play (channels 0-3)
sound_loop(id, channel)     # Play looped
sound_stop(channel)         # Stop channel
sound_volume(channel, 0-64) # Set volume
tone_play(ch, hz, vol, ms)  # Sine tone, returns at once
sound_playing(ch)  sound_period(ch, p)  sound_free(id)

music_load("file.mod")      # Load a ProTracker MOD
music_play()                # Start playback
music_pause() music_resume()
music_volume(0-64)          # Set volume
music_stop()                # Stop playback
music_pos()  music_row()    # where it plays (order list, row 0-63); music_position(n), music_free()
```

## File Functions
```
h = file_open("f", 1005)    # Open for read (0 if it fails)
h = file_open("f", 1006)    # New file, for write
h = file_open("f", 1004)    # Read and write
file_close(h)               # names: import "lib/amiga/dos.dash" (MODE_READ, MODE_WRITE, MODE_READWRITE)

file_read_byte(h)           # Read byte
file_write_byte(h, b)       # Write byte
file_read_line(h, buf, max) # Read line
file_write_line(h, "text")  # Write line
file_eof(h)                 # End of file? (looks at the next byte, does not take it)

file_exists("name")         # File exists?
file_size("name")           # Get size
file_delete("name")         # Delete file
file_print(h, "t")  file_seek(h, pos, mode)  file_pos(h)   # mode -1 start, 0 current, 1 end (SEEK_* in dos.dash)
file_rename("a", "b")  file_copy("a", "b")  dir_create("d")  dir_change("d")  dir_current()
n = file_load("f", buf, max)  file_save("f", buf, n)   # whole file to/from a buffer (-1: failed)
console_write("t")  console_read(buf, max)
```

## Buffers and Raw Memory
```
b = buffer_alloc(1024)      # zeroed bytes, not freed by themselves: buffer_free(b)
buffer_set_byte(b, 0, 65)  buffer_get_byte(b, 0)   # also _word and _long (big-endian)
buffer_copy(dst, 0, src, 0, n)  buffer_fill(b, 0, n, 0)
peek_byte(addr)  poke_byte(addr, v)   # also _word and _long: any address
```

## System Functions
```
mem_chip_free()             # Available chip RAM
mem_fast_free()             # Available fast RAM; mem_total()

time_delay(ticks)           # Wait (50 ticks = 1 sec)
time_delay_ms(ms)           # Wait milliseconds
time_ms()                   # Milliseconds since the program started
wait_vblank()               # Wait vertical blank

random()                    # Random number
random_range(min, max)      # Random in range; random_seed(n)
wait_blit()                 # Wait for the blitter

debug_break()               # Stop in the UAE emulator's debugger (tools/emu_run.py --debug)

break_check()               # true if Ctrl-C came (Break in the Shell); it is cleared
single_instance("MiProg")   # false if another copy runs (that one gets Ctrl-C)
tooltype("CX_POPKEY", "")   # NAME=value from the Shell, else the program's icon, else the default
cx_broker("MiProg", "Título", "Descripción", 0)   # a commodity in Exchange (show/hide on)
cx_hotkey("ctrl alt t")     # false if not valid; cx_command(): 1 hide 2 show 3 disable 4 enable 5 kill 6 key
cx_wait(1000)               # a command, -1 Ctrl-C or 0 when the time passes (spends nothing meanwhile)
n = disks_read(500)         # mounted volumes (asked at once, 500 ms at most): disk_name(i), disk_kb(i), disk_free_kb(i) (-1: no answer)
m = net_ifs_read()          # Roadshow's interfaces (-1 without): net_if_name(i), net_if_up(i), net_if_bytes_in(i), net_if_bytes_out(i)
wifi_read("wlan0", 500)     # 0: wifi_signal(), wifi_noise() in dBm; 1 no answer, 2 not told, 3 no interface, 4 offline, 5 busy, -1 no Roadshow
d = net_drivers_read()      # SANA-II drivers in use, any stack: net_driver_name(i) ("wifipi.device")
wifi_read_device("wifipi.device", 0, 500)   # as wifi_read, asking the driver; net_driver_read(driver, unit, ms): net_driver_packets_in/out()
net_driver_has_bytes()      # the driver counts bytes too: net_driver_bytes_in(), net_driver_bytes_out()
h = file_notify("ENV:X.prefs")   # watch a file: cx_wait gives 7, file_changed(h); file_notify_signal() for MUI
file_notify_end(h)          # stop watching it (the program's end stops them all)
run_program("SYS:Prefs/Font")    # start a command line, not waiting; program_relaunch(): start again at the end
input_text("=SUM(A1:A3)")        # type/click in the active window (tests): input_key(0x44, 1), input_click(x, y, q), input_button(2, true), input_drag, input_active_title()
clip_write_text(t); t = clip_read_text()   # clipboard (unit 0, FTXT); own data: clip_write_block(1, "LCLC", buf, n), clip_block_size, clip_read_block
clock_read()                # clock_year/month/day/weekday(0 Sun)/hour/minute/second(); date_text("%A %d-%b-%Y %H:%M") (locale)
locale_decimal_point()      # "," or "." as the user's country writes; locale_group_separator(), locale_date_order() ("DMY"...)
t = tr(1, "Hola")           # the text of number 1 in the catalog (@catalog), else "Hola"; catalog_open(name, version), catalog_language()
mouse_curve(0, [100, 150, 200])      # mouse acceleration: emitter 0 = Amiga mouse; factors in hundredths by speed
mouse_curves_off()          # the curves out of input.device now (also at the end); mouse_curve_events(emitter)
n = usb_hid_read()          # Poseidon's hid.class devices (-1 none): usb_hid_name/maker/vendor/product/kind(i), usb_hid_emitter(i)
mouse_prefs_set(1, false)   # system speed and acceleration (back at the end); mouse_prefs_ticks(), mouse_prefs_accel()
dos_requesters(false)       # no "Insert volume"/disk error requesters: the call fails (true: back)
base64_to_file(texto, "T:x.png")   # base64 bytes to a file: bytes written, -1 if not base64

cpu_start()                 # count the CPU of every task (false: no EClock or OS < 2.04)
n = cpu_sample()            # tasks since the last sample, most first: cpu_task_name(i), cpu_task_load(i)
cpu_total()                 # per thousand, all tasks (the rest is idle); cpu_stop()
```

## Tasks (C in another process)
```
t = task_start(f, arg)      # @native func f(arg: Int) -> Int in another process (C only); 0 = failed
task_start_with(f, arg, stack, pri)   # stack in bytes (0: 128 KB), priority relative to the program
task_done(t)                # true once it returned (does not wait)
task_result(t)              # what it returned (waits)
task_free(t)                # forget it (waits); task_signal(): mask for mui_wait_event_signals
# in a task's C: _dash_task_wake() wakes the program (task_signal); the network belongs to one process at a time
# (the first to use it, until its task ends): _dash_net_connect_start/poll, _send_buffer/_recv_buffer, _dash_tls_*_buffer...
```

## Desktop Canvas (Workbench backdrop)
```
d = desktop_canvas(x, y, w, h)          # an area of the desktop, behind the icons (negative: from right/bottom)
desktop_canvas_on_draw(d, paint)        # func paint(x, y, w, h) draws with gfx_
desktop_canvas_update(d)                # draw again; desktop_canvas_update_area(d, x, y, w, h): only that part
desktop_canvas_free(d)                  # the wallpaper back (also at exit)
```

## Network (TCP and UDP, bsdsocket.library)
```
s = net_connect("host", 80, 10000)   # socket or -1 (net_error() says why)
net_send(s, "GET / HTTP/1.0\r\n\r\n")
t = net_recv(s, 4096, 10000)         # "" = nothing yet, nil = closed
net_wait(s, ms)  net_close(s)  net_resolve("host")
net_send_buffer(s, buf, n)  net_recv_buffer(s, buf, max, ms)
t = tls_connect(s, "host")           # TLS (AmiSSL 5.1+, 68020+): tls_send, tls_recv, tls_close; _buffer too
s = net_connect_start("host", 80, 10000)  # without waiting: net_connect_poll(s) 1 / 0 / -1,
t = tls_connect_start(s, "host", 10000)   # net_connect_stage(s); tls_connect_poll(t) 1 / 0 / -1
ev = mui_wait_event_signals(net_signal())   # wakes on socket events (0: the stack cannot, poll)
tls_resumed(t)                       # true if it reused an earlier session with that server
srv = net_listen(8080)               # TCP server (0: any free port, net_port(srv)); -1 if taken
c = net_accept(srv, 1000)            # next connection or -1 (0: only look); net_peer(c) = "a.b.c.d"
u = net_udp_open(5000)               # UDP (0: any free port); net_close(u)
net_udp_send(u, "host", 5000, "hi")  # one datagram ("255.255.255.255": whole local network); _buffer too
m = net_udp_recv(u, 1500, 1000)      # "" = none in time, nil = error; net_udp_from(), net_udp_from_port()
```
No HTTP builtin: a program speaks HTTP itself over `net_`/`tls_`. No raw sockets or raw SANA-II frames.

## Program Arguments
```
arg_count()                 # arguments from the Shell; from the Workbench, the project icons (arg(i): full path)
arg(0)                      # the first one ("" if missing)
```

## Memory Management
> Strings: freed automatically (each variable owns its text; temporaries are
> freed on each loop/EventLoop iteration and when leaving a function).
> Arrays and structs: automatic reference counting (freed when nothing uses them).
> Lists of structs, strings or lists release their elements; a struct in a list of
> integers, anything handed to C and cycles, at exit. `./dash --memcheck` reports errors and leaks.
> These functions are for advanced cases.

```
# Reference Counting (automatic; manual calls only for advanced cases)
refcount(obj)               # Get count
retain(obj)                 # Increment
release(obj)                # Decrement (frees at 0)

# Arena Allocator (fast temporary allocation)
a = arena_new(size)         # Create arena
ptr = arena_alloc(a, size)  # Allocate
arena_reset(a)              # Reset all
arena_free(a)               # Free arena; arena_used(a), arena_available(a)
```

## Common Patterns

### Game Loop
```
Main
    GameWin.open
    while running
        handle_input()
        update()
        draw()
        wait_vblank()
    end
end
```

### Draw Centered Text
```
text = "Hello"
w = gfx_text_len(text)
x = (320 - w) / 2
gfx_text_at(x, 100, text)
```

### Joystick Movement
```
x = x + joy_x(0) * speed
y = y + joy_y(0) * speed
```

### File Read Loop
```
h = file_open("data.txt", 1005)
while not file_eof(h)
    b = file_read_byte(h)
end
file_close(h)
```

## Key Codes
| Key | Code | Key | Code |
|-----|------|-----|------|
| ESC | 69 | SPACE | 64 |
| RETURN | 68 | UP | 76 |
| LEFT | 79 | DOWN | 77 |
| RIGHT | 78 | F1-F10 | 80-89 |

## Standard Colors
| Index | Typical Use |
|-------|-------------|
| 0 | Background |
| 1 | Text/Foreground |
| 2 | Highlight |
| 3 | Shadow |
