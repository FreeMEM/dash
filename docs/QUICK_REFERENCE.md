# D.A.S.H. Language - Quick Reference Card
> **D.A.S.H.** — *Development Amiga Synthesis Hub*

## Compile
```
./dash prog.dash -o prog            # gcc -O2, 68000, 16 KB stack minimum
./dash -O0 prog.dash -o prog        # no optimization (debugging)
./dash --small prog.dash -o prog    # gcc -Os: ~7% smaller, slower loops
./dash --stack 32768 ...            # minimum stack (0: as the shell gives it)
./dash --fpu prog.dash -o prog      # 68020 + 68881/68882 FPU only
./dash --memcheck prog.dash -o prog # memory check: double frees, use after free, live at exit
```
Programs need Kickstart 3.0+.

## Program Structure
```
const NAME = value          # Constants
enum State IDLE,RUN end     # Enumerations
struct Player x:Int end     # Structures
Window Win title "" end     # Windows
func name() end             # Functions
Main ... end                # Entry point
```

## Variables & Types
```
x = 42                      # Int
v = 1.5                     # Float (Int(v), Float(n), 7 significant digits)
f = Fixed(1.5)              # Fixed 16.16: fast decimals on 68000 (Int(f), fx_sqrt, fx_sin, fx_cos)
mask = 0xFF                 # hex (also $DFF000), binary 0b1010
name = "Dash"               # String
active = true               # Bool
nums = [1,2,3]              # Array
player = Player(10,20)      # Struct instance
var lista: Nodo = nil       # nil: no struct/list/String (x == nil, x = nil)
```

## Operators
```
+  -  *  /  %               # Arithmetic
==  !=  <  >  <=  >=        # Comparison
and  or  not                # Logical
+                           # String concatenation
"abc" < "abd"               # Strings: == != compare text, < > <= >= the order (strcmp)
```

## Text
```
s.length  s[i]  s[2:5]      # length, character, slice
Int(s[i])  str_code(s, i)   # character code (0-255)
str_char(65)                # "A"
str_find(s, "x")            # position or -1; str_find_from(s, "x", start)
str_starts(s, "a")  str_ends(s, "z")
str_lower(s)  str_upper(s)  str_trim(s)
Int("42")  str_to_int("ff", 16)  str_from_int(255, 16)
str_replace(s, "a", "b")
s = s + "x"                 # appends in place: building a text in a loop is linear
t = file_read_text("f.html")   # whole file (nil if missing); file_write_text("f", t)
str_from_buffer(buf, 0, n)  str_to_buffer(s, buf, 0)
```

## Control de Flujo
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
    ...                     for item in array
end                             ...
                            end

break / continue            # inside while/for only
```

## Functions
```
func add(a, b)              func typed(x: Int) -> Int   # Int Float String Bool Array Pointer Func Void, struct, enum, [T], {String: T}
    return a + b                return x * 2
end                         end
```

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
boss.pos.x = 5              # nested structs (pos: Punto)
# weak padre: Nodo          # field that points without holding (no cycles: parent pointers)
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
d = {"a": 1, "b": 2}        # dictionary {String: T}: d["c"] = 3, d["a"], d.has("a"),
d.remove("a")  d.keys()  d.clear()  d.length    # missing key: 0 / nil
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
        On Close
            Stop
        end
    end
end
```

## MUI (68020+, MUI 3.8/5; SDK: tools/get_mui_sdk.sh)
```
app = mui_app_begin("App", "APP")       # 0 = no MUI / 68000
win = mui_window_begin("Title", 1)      # vertical root group; 1 = remember place
    mui_menu_begin("Project")           # menus of this window
        q = mui_menu_item("Quit", "Q", 9)   # mui_menu_separator()
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
mui_canvas_on_input(c, 3)               # click/wheel/key: mui_canvas_mouse_x/_y/_button/_wheel/_key(c)
img = mui_image("Work:pic.png")         # datatypes; mui_width(obj), mui_height(obj) once open
mui_on_press(ok, 1)                     # mui_on_close(win, id): default -1
mui_window_open(win)
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

gfx_text_at(x, y, "text")   # Draw text
f = font_open("helvetica.font", 13) # font_use(f), font_style(2), font_text_width(s), font_height()
color_pen(r, g, b)          # pen for an RGB color (0-255) on the screen drawn on
gfx_clear()                 # Clear screen
```

## Input Functions
```
# Keyboard
key_pressed()               # Bool: key available?
key_get()                   # Get key code
key_wait()                  # Wait for key

# Mouse
mouse_x()                   # X position
mouse_y()                   # Y position
mouse_button(0)             # Left button (0=left, 1=right)

# Joystick (port 0 or 1)
joy_x(0)                    # X: -1, 0, or 1
joy_y(0)                    # Y: -1, 0, or 1
joy_button(0)               # Fire button
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

music_load("file.mod")      # Load a ProTracker MOD
music_play()                # Start playback
music_pause() music_resume()
music_volume(0-64)          # Set volume
music_stop()                # Stop playback
```

## File Functions
```
h = file_open("f", MODE_OLDFILE)  # Open for read
h = file_open("f", MODE_NEWFILE)  # Open for write
file_close(h)

file_read_byte(h)           # Read byte
file_write_byte(h, b)       # Write byte
file_read_line(h, buf, max) # Read line
file_write_line(h, "text")  # Write line
file_eof(h)                 # End of file?

file_exists("name")         # File exists?
file_size("name")           # Get size
file_delete("name")         # Delete file
```

## System Functions
```
mem_chip_free()             # Available chip RAM
mem_fast_free()             # Available fast RAM

time_delay(ticks)           # Wait (50 ticks = 1 sec)
time_delay_ms(ms)           # Wait milliseconds
wait_vblank()               # Wait vertical blank

random()                    # Random number
random_range(min, max)      # Random in range
```

## Network (TCP, bsdsocket.library)
```
s = net_connect("host", 80, 10000)   # socket or -1 (net_error() says why)
net_send(s, "GET / HTTP/1.0\r\n\r\n")
t = net_recv(s, 4096, 10000)         # "" = nothing yet, nil = closed
net_wait(s, ms)  net_close(s)  net_resolve("host")
net_send_buffer(s, buf, n)  net_recv_buffer(s, buf, max, ms)
t = tls_connect(s, "host")           # TLS (AmiSSL 5, 68020+): tls_send, tls_recv, tls_close
```

## Program Arguments
```
arg_count()                 # arguments from the Shell (0 from the Workbench)
arg(0)                      # the first one ("" if missing)
```

## Memory Management
> Strings: se liberan solos (cada variable es dueña de su texto; los temporales se
> liberan en cada vuelta de bucle/EventLoop y al salir de una función).
> Arrays y structs: conteo de referencias automático (se liberan cuando nadie los usa).
> Las listas de structs, textos o listas sueltan sus elementos; un struct en una lista de
> enteros, lo dado a C y los ciclos, al salir. `./dash --memcheck` avisa de fallos y fugas.
> Estas funciones son para casos avanzados.

```
# Reference Counting (automatic; manual calls only for advanced cases)
refcount(obj)               # Get count
retain(obj)                 # Increment
release(obj)                # Decrement (frees at 0)

# Arena Allocator (fast temporary allocation)
a = arena_new(size)         # Create arena
ptr = arena_alloc(a, size)  # Allocate
arena_reset(a)              # Reset all
arena_free(a)               # Free arena
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
h = file_open("data.txt", MODE_OLDFILE)
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
