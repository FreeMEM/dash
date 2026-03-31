# D.A.S.H. Language - Quick Reference Card
> **D.A.S.H.** — *Development Amiga Synthesis Hub*

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
name = "Dash"               # String
active = true               # Bool
nums = [1,2,3]              # Array
player = Player(10,20)      # Struct instance
```

## Operators
```
+  -  *  /  %               # Arithmetic
==  !=  <  >  <=  >=        # Comparison
and  or  not                # Logical
+                           # String concatenation
```

## Control de Flujo
```
if cond                     while cond
    ...                         ...
end                         end

if cond                     for i in (1..10)
    ...                         ...
else                        end
    ...
end                         for item in array
                                ...
                            end
```

## Functions
```
func add(a, b)              func typed(x: Int) -> Int
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
```

## Arrays
```
arr = [1, 2, 3, 4, 5]
arr[0]                      # Access: 1
arr[2] = 99                 # Modify
arr.length                  # Length: 5
arr[1:3]                    # Slice: [2, 3]
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
        On Close
            Stop
        end
    end
end
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
sound_load(id, "file.8svx") # Load sound
sound_play(id, channel)     # Play (channels 0-3)
sound_loop(id, channel)     # Play looped
sound_stop(channel)         # Stop channel
sound_volume(channel, 0-64) # Set volume

music_load("file.mod")      # Load MOD
music_play()                # Start playback
music_stop()                # Stop playback
music_volume(0-64)          # Set volume
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

## Memory Management
> **Nota:** Estas funciones están planificadas pero aún no implementadas.

```
# Reference Counting (automatic for structs)
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
