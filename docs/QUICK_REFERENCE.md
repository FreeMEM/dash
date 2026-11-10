# D.A.S.H. Language - Chuleta de referencia rápida

*[English](QUICK_REFERENCE.en.md) | Castellano*
> **D.A.S.H.** — *Development Amiga Synthesis Hub*

Una línea por cosa. Cada builtin explicado, con sus parámetros y ejemplos que se prueban: [BUILTINS.md](BUILTINS.md).

## Compilar
```
./dash prog.dash -o prog            # gcc -O2, 68000, pila mínima de 16 KB
./dash -O0 prog.dash -o prog        # sin optimizar (para depurar)
./dash --small prog.dash -o prog    # gcc -Os: un 7 % más pequeño, bucles más lentos
./dash --profile ...                # al salir: llamadas y tiempo (propio, total) de cada función
./dash --stack 32768 ...            # pila mínima (0: la que dé el shell)
                                    # @stack 262144 en un programa o módulo: necesita al menos eso
                                    # @workbench_output "NIL:": desde el Workbench, sin ventana de consola
                                    # @catalog "X.catalog" 1 "español": tr(id, "texto") del catálogo de locale.library
                                    # @version "Prog 1.2": $VER: (C:Version) con la fecha de hoy; program_version()
./dash --fpu prog.dash -o prog      # solo 68020 + FPU 68881/68882
./dash --cpu 68040 prog.dash -o prog # código de 68020 afinado para 68020/030/040/060
./dash --memcheck prog.dash -o prog # comprobación de memoria: dobles liberaciones, uso tras liberar, vivo al salir
./dash --debug ...                  # para gdb / VS Code: gcc -O0 -g, líneas de C unidas a las del .dash
./dash --multifile ...              # un fichero C por módulo en vez de uno para todo el programa
./dash -q ...                       # callado: solo avisos, errores y el resultado (-v: detallado)
./dash --no-hunk ...                # se salta el paso de ELF a Hunk (el gcc de bebbo ya escribe Hunk)
DASH_TOOLCHAIN=/ruta ./dash ...     # toolchain de bebbo en otro sitio que no sea /opt/amiga
DASH_CFLAGS="-Os" ./dash ...        # opciones extra de gcc
```
Los programas necesitan Kickstart 3.0 o superior. Basta un 68000, salvo para MUI 5 y AmiSSL (TLS), que piden un 68020.

## Estructura del programa
```
import "lib/x.dash"         # Módulo (ruta relativa a este fichero); "x.dashui": ventanas MUI
const NAME = value          # Constantes
var total: Int = 0          # Variable global (con su tipo); las funciones pueden leerla y cambiarla
enum State IDLE,RUN end     # Enumeraciones (en una línea, o un valor por línea; = N opcional)
struct Player x:Int end     # Estructuras
Window Win title "" end     # Ventanas
func name() end             # Funciones
Main ... end                # Punto de entrada
```

## Variables y tipos
```
x = 42                      # Int
v = 1.5                     # Float (Int(v), Float(n), 7 cifras significativas)
d = Double(0.1)             # Double: 64 bits, 15-17 cifras (Double(n), Double("2.5"), Int(d), Float(d))
h = sqrt(2.0)               # sqrt, pow, exp, log, sin, atan2, floor, round, fmod, abs, is_nan...: Double
f = Fixed(1.5)              # Fixed 16.16: decimales rápidos en 68000 (Int(f), fx_sqrt, fx_sin, fx_cos)
xs = [Fixed(0.5), 2]        # lista de Fixed (los números pasan a Fixed); declarada: var xs: [Fixed] = []
ds = [Double(0.1), 2]       # lista de Double ([Double]); [1.5, 2] es [Float]; var ds: [Double] = [1, 2]
mask = 0xFF                 # hexadecimal (también $DFF000), binario 0b1010
name = "Dash"               # String
active = true               # Bool: Print y "x " + b escriben true / false (una comparación también)
nums = [1,2,3]              # Array
player = Player(10,20)      # Instancia de struct
var lista: Nodo = nil       # nil: ningún struct/lista/String (x == nil, x = nil)
```

## Operadores
```
+  -  *  /  %               # Aritméticos
==  !=  <  >  <=  >=        # Comparación; encadenadas: 1 <= a <= 10
x in (1..10)  x in lista    # rango (con step), lista, texto o diccionario; x not in ...
and  or  not                # Lógicos
&  |  ^  ~  <<  >>          # Bits en Int (^ xor, ~ complemento, >> aritmético); como en Python:
                            # desplazamientos, &, ^, | entre + - y las comparaciones (a & 4 == 4)
const MASK = 1 << 4         # const: también una expresión Int de números y constantes anteriores
+                           # Concatenación de textos
"abc" < "abd"               # Textos: == != comparan el texto, < > <= >= el orden (strcmp)
```

## Texto
```
s.length  s[i]  s[2:5]      # longitud, carácter, trozo
Int(s[i])  str_code(s, i)   # código del carácter (0-255)
str_char(65)                # "A"
str_find(s, "x")            # posición o -1; str_find_from(s, "x", inicio)
regex_match("D.", s, false)  # todo el texto, sintaxis ICU; regex_find(p, s, desde, icase) -1 / regex_length(); regex_error(); wildcard_match("*.ods", s, true)
str_starts(s, "a")  str_ends(s, "z")
str_lower(s)  str_upper(s)  str_trim(s)
Int("42")  str_to_int("ff", 16)  str_from_int(255, 16)
str_replace(s, "a", "b")
str_contains(s, "x")        # Bool
str_split("a,b,c", ",")     # ["a", "b", "c"]: un [String] nuevo; separador "" o no encontrado: [s]
"n=#{n} len #{v.length} #{f(x) + 1}"   # interpolación: cualquier expresión; comillas dentro como \"
s = s + "x"                 # añade en el sitio: montar un texto en un bucle es lineal
s = t.texto                 # copia el texto; f(t.texto) no lo copia si ningún código cambia ese campo
t = file_read_text("f.html")   # el fichero entero (nil si no está); file_write_text("f", t)
str_from_buffer(buf, 0, n)  str_to_buffer(s, buf, 0)
```

## Control de flujo
```
if cond                     while cond
    ...                         ...
end                         end

if cond                     for i in (1..10)
    ...                         ...
elif cond                   end
    ...
else                        for i in (10..1)       # hacia atrás
                            for i in (0..n step 2)
    ...                     for i in (10..0 step -2)   # hacia atrás con paso: negativo
                            for item in array
end                             ...
                            end

break / continue            # solo dentro de while/for
```

## Funciones
```
func add(a, b)              func typed(x: Int) -> Int   # Int Float String Bool Array Pointer Func Void, struct, enum, [T], {String: T}, {Int: T}
    return a + b                return x * 2
end                         end

doble = fn(x) -> x * 2      # lambda; también fn(x) ... return ... end
func aplica(f: Func, v: Int) -> Int   # una función como valor: aplica(doble, 4)
    return f(v)             # las lambdas no pueden usar variables locales de fuera (las globales sí)
end
```

Código C: `@native func f(x: Int) -> Int """ return x; """ end` (una función en C), `@extern("x.library")`,
`@native(borrow) func ...` (el C solo usa sus argumentos durante la llamada: no se guardan hasta
la salida), `@header "#include <x.h>"`, `@link "lib/x.c"` (un fuente C, objeto o librería que se enlaza con el programa; su
directorio va a `-I`), `@c """ ... """ end` (C a nivel superior, tras los prototipos de Dash: callbacks).

## Structs con métodos
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
boss.pos.x = 5              # structs anidados (pos: Punto); l[0].x = 5 (un campo de un elemento de lista)
d["k"].push(x)              # métodos de elementos también: l[0].mover(1), filas[i].clear()
# weak padre: Nodo          # campo que apunta sin retener (sin ciclos: punteros al padre)
```

## Interfaces
```
interface Orden             # solo métodos; sin campos, sin Orden()
    func deshacer() -> String
end
struct Escribir: Orden      # tiene sus métodos, con los mismos parámetros y retorno (struct C: Figura, Orden)
    ...
end
var pila: [Orden] = []      # cualquier struct que la tenga; o.deshacer() llama al de su struct (una tabla por tipo)
```

## Arrays
```
arr = [1, 2, 3, 4, 5]
arr[0]                      # Acceso: 1
arr[2] = 99                 # Cambio
arr.length                  # Longitud: 5
arr[1:3]                    # Trozo: [2, 3]
arr + [6, 7]                # Lista nueva con las dos (mismo tipo de elemento)
var l: [String] = []        # tipos de lista [T]: [Int] [String] [Nodo] [[Int]] (parámetros, retornos, campos)
for x in obj.lista          # for-each sobre cualquier expresión de lista
l.push(x)  l.pop()  l.insert(i, x)  l.remove(i)  l.clear()   # listas que crecen
l.sort(f)                   # estable; f(a, b) -> Bool (a antes que b) o Int (<0 antes, 0 igual, >0 después)
d = {"a": 1, "b": 2}        # diccionario {String: T}: d["c"] = 3, d["a"], d.has("a"),
d.remove("a")  d.keys()  d.clear()  d.length    # clave que no está: 0 / nil
d.get("c", 0)                # el valor, o el de por defecto si no está (una búsqueda; objetos: solo nil)
e = {1: "uno", 7: "siete"}   # claves Int: {Int: T} (var e: {Int: String} = {}), mismos métodos; keys() es [Int]
"Hola Dash"[5:]             # también en textos: "Dash"
```

## Ventanas y eventos
```
Window MyWin
    title "App"
    width 320
    height 200
end

Main
    MyWin.open
    EventLoop
        On Key "ESC"        # también "a", 0x4C, UP/DOWN/F1..., o sin tecla = cualquiera
            Stop
        end
        On Menu            # menu_title/menu_item/menu_attach; menu_id() = id de la opción
            Stop
        end
        On Click           # botón izquierdo en la ventana: click_x(), click_y() dentro de los bordes
        end
        On RightClick      # botón derecho, en una ventana con rmbtrap true (flag 16 de window_create)
        end
        On Inactive        # la ventana dejó de ser la activa; event_window(): cuál
        end
        On Timer 100       # cada 100 ms (un número o una variable)
        end
        On Gadget          # gadget_id(): el gadget usado; event_window(): su ventana (window_create)
        end
        On Close
            Stop
        end
    end
end
```

## Menús (Intuition)
```
menu_title("Project")       # monta la tira; menu_attach() la pone en la ventana actual
menu_item("Quit", "Q", 9)   # Amiga+Q; menu_separator(), menu_sub(label, key, id)
menu_check_item("Grid", "G", 10)   # con marca: menu_checked(10) 1 / 0
menu_attach()               # luego On Menu: menu_id(); menu_enable(id, false) apaga una opción
```

## MUI (68020+, MUI 3.8/5; SDK: tools/get_mui_sdk.sh)
```
app = mui_app_begin("App", "APP")       # 0 = sin MUI / 68000
win = mui_window_begin("Title", 1)      # grupo raíz vertical; 1 = recordar el sitio
    mui_menu_begin("Project")           # menús de esta ventana
        q = mui_menu_item("Quit", "Q", 9)   # mui_menu_separator()
        g = mui_menu_check("Grid", "G", 10, true)   # mui_get_value(g); mui_submenu_begin("Recent") ... mui_submenu_end()
        m = mui_context_menu_begin("Cells")   # opciones como arriba, mui_menu_end(); mui_set_context_menu(canvas, m): botón derecho
    mui_menu_end()
    tabs = mui_register_begin("A|B")    # páginas; valor = página. También mui_frame_begin("T", false),
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
mui_on_change(url, 2)                   # mui_on_ack(url, id): Return en un campo de texto
l = mui_list()                          # valor = línea elegida (-1); mui_on_double(l, id)
mui_list_add(l, "x")                    # _insert(l, pos, s) _remove(l, pos) _clear _count _get(l, pos) _quiet
c = mui_canvas(320, 200)                # zona de dibujo; sb = mui_scrollbar(true), mui_set_range(sb, total, vis)
mui_canvas_on_draw(c, paint)            # func paint(x, y, w, h) dibuja con gfx_; mui_canvas_redraw(c)
mui_canvas_on_input(c, 3)               # clic/rueda/tecla: mui_canvas_mouse_x/_y(c), mui_canvas_button/_wheel/_key(c)
mui_canvas_char(c)                      # la tecla como texto, con mayúsculas y el mapa de teclado ("" si no hay)
mui_canvas_qualifiers(c)                # teclas pulsadas en la última entrada: 1 Shift, 2 Ctrl, 4 Alt, 8 Amiga, sumadas
mui_canvas_on_drag(c, id)               # evento al arrastrar y al soltar: mui_canvas_drag(c) 1 moviendo, 2 soltado
mui_canvas_on_move(c, 4)                # el puntero encima (sin clic) o al salir: mui_canvas_pointer_x/_y/_inside(c)
mui_canvas_update(c)                    # dibujar otra vez sin borrar; mui_canvas_updating() true en paint
mui_canvas_update_area(c, x, y, w, h)   # lo mismo, solo en esa zona (recortado)
mui_canvas_buffered(c, true)            # dibujar en un bitmap propio, que se muestra de golpe al acabar
img = mui_image("Work:pic.png")         # datatypes; mui_width(obj), mui_height(obj) una vez abierta
b = mui_image_button("PROGDIR:atras.iff")   # botón con icono: mui_on_press; mui_help(b, "Atrás") ayuda en burbuja
mui_window_size(win, 90, 80)            # % de la pantalla visible al abrirse (antes de mui_window_open)
mui_window_fullscreen(win)              # toda la pantalla, sin bordes ni barra de título (antes de mui_window_open)
mui_window_own_screen(win)              # lo mismo en una pantalla nueva como la pública (false: no se abrió)
mui_on_press(ok, 1)                     # mui_on_close(win, id): por defecto -1
mui_window_open(win)                    # mui_window_active(win): 1 si está activa; mui_window_close(win)
ev = mui_wait_event()                   # 1, o -1 = cerrada; mui_poll_event, mui_press(ok)
mui_timer(500, 7)                       # en 500 ms mui_wait_event devuelve 7 (una vez; 0 ms lo anula)
ev = mui_wait_event_signals(mask)       # también devuelve 0 con una de esas señales; mui_signals()
mui_app_end()                           # también al salir
import "win.dashui"                     # fichero del editor visual: v = Main_create() (struct: v.window, objetos con nombre)
```

## Funciones gráficas
```
gfx_pen(color)              # Color de dibujo (0-31)
gfx_rgb(idx, r, g, b)       # Paleta (0-15 cada uno)

gfx_pixel(x, y)             # Dibuja un píxel
gfx_line(x1,y1, x2,y2)      # Dibuja una línea
gfx_rect(x1,y1, x2,y2)      # Rectángulo relleno
gfx_box(x1,y1, x2,y2)       # Contorno de rectángulo
gfx_circle(cx, cy, r)       # Contorno de círculo
gfx_circle_fill(cx, cy, r)  # Círculo relleno
gfx_ellipse(cx,cy, rx,ry)   # Contorno de elipse
gfx_ellipse_fill(cx,cy,rx,ry) # Elipse rellena

gfx_poly_begin(x, y)        # Empieza el polígono
gfx_poly_add(x, y)          # Añade un vértice
gfx_poly_end()              # Cierra y rellena

gfx_move(x, y)  gfx_draw(x, y)          # línea desde el cursor; gfx_text("t") en el cursor
gfx_pixel_read(x, y)        # pen de un píxel; gfx_flood(x, y, mode)
gfx_scroll(dx, dy, x1, y1, x2, y2)  gfx_copy(sx, sy, w, h, dx, dy)   # mueve o copia una zona
gfx_pen_bg(c)  gfx_pen_outline(c)  gfx_mode(m)  gfx_pattern(0xF0F0)  gfx_rgb8(idx, r, g, b)   # 0-255 (AGA)

gfx_text_at(x, y, "text")   # Dibuja texto
f = font_open("helvetica.font", 13) # font_use(f), font_style(2), font_text_width(s), font_height()
                            # font_size(f) (el tamaño que obtuvo), font_baseline(), font_close(f)
color_pen(r, g, b)          # pen para un color RGB (0-255) en la pantalla donde se dibuja
gfx_blend_rect(x1, y1, x2, y2, 0xRRGGBB, alpha)        # mezclado con lo que hay (alpha 0-255)
gfx_gradient_rect(x1, y1, x2, y2, rgb1, a1, rgb2, a2, vertical)   # RTG: mezcla real; paleta: tramado 4x4
gfx_pixel_rgb(x, y)         # 0xRRGGBB de un píxel
gfx_rgb_draw(buf, w, h, x, y)              # buffer RGB24 (fotograma de vídeo); RTG: WritePixelArray
gfx_rgb_draw_scaled(buf, w, h, x, y, dw, dh)   # escalado, píxel más cercano
img = image_load("a.png")   # datatypes (0: no se puede leer); image_width/_height(img)
image_draw(img, x, y)       # image_draw_part(img, sx, sy, x, y, w, h), image_scale(img, w, h), image_free(img)
img = image_from_rgb(buf, w, h, alfa)   # píxeles RGB (o RGBA) en un buffer; picture.datatype V43 (3.5+), si no 0
gfx_clear()                 # Borra la pantalla; gfx_clear_color(c)
```

## Sprites, BOBs, Copper, Bitmaps
```
sprite_load(0, "nave.iff")  # sprite de hardware: fotogramas de 16 píxeles uno al lado de otro; sprite_frame(0, n)
sprite_pos(0, x, y)  sprite_show(0)  sprite_hide(0)  sprite_collision(0, 1)  sprite_free(0)
sprite_create(0, 16, h)  sprite_set_row(0, row, plane0, plane1)  sprite_color(0, i, r, g, b)
soft_sprite_create(1, w, h, depth)   # dibujado por software (también RTG): soft_sprite_pixel/_row/_pos/_show/_hide
bob_load(2, "bola.iff")     # bob_create(id, w, h, depth); bob_pos, bob_draw, bob_erase, bob_frame, bob_collision
copper_create(64)           # copper_wait(y, x), copper_move(reg, v), copper_color(0, 0xF00) (RGB de 12 bits),
copper_end()  copper_install()   # copper_free()
bitmap_load(3, "fondo.iff") # bitmap_create(id, w, h, depth), bitmap_save(id, "f"), bitmap_free(id)
bitmap_blit(3, sx, sy, w, h, dx, dy)   # a la pantalla; bitmap_blit_mask(src, mask, ...)
bitmap_draw_to(3) ... bitmap_draw_screen()   # gfx_ dibuja en el bitmap, y luego otra vez en la pantalla
```

## RTG (CyberGraphX / Picasso96)
```
rtg_available()  rtg_is_active()     # hay librería de tarjeta; la pantalla está en la tarjeta
rtg_open_screen(640, 480, 24, "T")   # rtg_best_mode(w, h, depth); rtg_get_width/_height/_depth()
rtg_write_pixel(x, y, 0xRRGGBB)  rtg_read_pixel(x, y)  rtg_fill_rect(x, y, w, h, rgb)
rtg_write_array(buf, bpr, x, y, w, h)   # buffer ARGB de 32 bits, bpr bytes por fila; rtg_read_array
bm = rtg_alloc_bitmap(w, h, 32)      # rtg_blit(bm, sx, sy, dx, dy, w, h), rtg_scale_blit, rtg_free_bitmap(bm)
rtg_rgb(r, g, b)  rtg_argb(a, r, g, b)  rtg_rgb_r/_g/_b(c)
```

## Pantallas, ventanas y gadgets (Intuition, GadTools)
```
screen_open(4, "Title")     # una pantalla como la del Workbench, 16 colores; screen_close()
screen_open_custom(w, h, depth, "Title")
screen_width()  screen_height()  screen_to_front()  screen_to_back()
v = window_create("T", x, y, w, h, 8)   # flag 8: w y h son el interior; window_border_top/bottom/left/right()
h = screen_font_height()    # la fuente de la pantalla (barras de título, gadgets gt_*); screen_font_text_width(text)
b = button_create(0, x, y, 0, 0, "_Save")   # w/h 0: medido con la fuente de la pantalla; "_": S lo pulsa
gadget_width(b)  gadget_height(b)           # su tamaño, para colocar el siguiente
window_move(v, x, y)  window_resize(v, w, h)  window_title(v, "T")  window_close(v)   # v 0: ventana actual
window_to_front(v)  window_to_back(v)  window_activate(v)
t = textfield_create(v, x, y, w, h, 80)     # textfield_get(t), textfield_set(t, s); button_enable/_disable(b)
# también checkbox_, slider_, listview_, cycle_, radio_, integer_, palette_, number_create, con _get/_set
f = dialog_file("Load", "#?.txt", false)    # ruta o "" (true: guardar); dialog_font(title), dialog_color(title, pen)
file_open_dialog("Load", "#?")              # ASL (también file_save_dialog); luego file_fullpath(), file_get_path(), file_get_name()
```
`gt_*` (una ventana, gadgets por id): `gt_init()` después de abrirla; `gt_button`, `gt_checkbox`, `gt_string`,
`gt_integer`, `gt_slider`, `gt_cycle`, `gt_palette`, `gt_text` (x, y, w, h, etiqueta, ...); `gt_attach()`;
`ev = gt_wait_event()` (id, -2 = cerrar; `gt_event()` sin esperar); `gt_get_value`, `gt_set_value`,
`gt_get_string`, `gt_set_text`, `gt_enable`, `gt_disable`; `gt_cleanup()`.

## ReAction (hasta 4 ventanas; window.class V44: OS 3.5+, probado en 3.2)
```
w = ra_window_create("T", 300, 200)  # 1-4 (0: falló), la actual; ra_window_use(w), ra_event_window()
ra_layout_hgroup_begin() ... ra_layout_group_end()   # también _vgroup_begin, _hgroup_weighted(n)
ra_add_button(1, "OK")  ra_add_string(2, "", 64)  ra_add_checkbox(3, "On", 0)  ra_add_slider(4, 0, 100, 50)
# también ra_add_integer, _label, _palette, _chooser, _scroller, _listbrowser, _radio, _clicktab, _fuelgauge, _getfile
ra_menu_title("Project")  ra_menu_item("Quit", "Q", 9)   # evento RA_EVENT_MENU(), luego ra_menu_id()
ra_window_open()
ev = ra_wait_event()                 # id del gadget o RA_EVENT_CLOSE(); ra_handle_events() no espera
ra_get_value(4)  ra_set_value(4, 10)  ra_get_string(2)  ra_set_string(2, "x")  ra_enable_gadget(1)
ra_window_close()
```

## Funciones de entrada
```
# Teclado
key_pressed()               # Bool: ¿hay tecla esperando? (solo mira; key_get la recoge)
key_get()                   # Código de tecla (0 si no hay)
key_wait()                  # Espera una tecla; wait_key() la devuelve
key_raw()  key_text(code)   # código en bruto; un código como texto
check_lmb()  check_rmb()  check_esc()   # directo del hardware, sin eventos; wait_click()

# Ratón
mouse_x()                   # Posición X
mouse_y()                   # Posición Y
mouse_button(0)             # Botón izquierdo (0=izquierdo, 1=derecho)

# Joystick (puerto 0 o 1)
joy_x(1)                    # X: -1, 0 o 1
joy_y(1)                    # Y: -1, 0 o 1
joy_button(1)               # Botón de disparo (también joy_fire(1))
joy_up(1) joy_down(1)       # Direcciones como Bool
joy_left(1) joy_right(1)
```

## Funciones de audio
```
sound_load(id, "file.8svx") # Carga un sonido IFF 8SVX
sound_create(id, len, rate) # Sonido en silencio en chip RAM; sound_sample(id, i, v) lo rellena
sound_play(id, channel)     # Reproduce (canales 0-3)
sound_loop(id, channel)     # Reproduce en bucle
sound_stop(channel)         # Para el canal
sound_volume(channel, 0-64) # Volumen
tone_play(ch, hz, vol, ms)  # Tono senoidal, vuelve enseguida
sound_playing(ch)  sound_period(ch, p)  sound_free(id)

music_load("file.mod")      # Carga un MOD de ProTracker
music_play()                # Empieza a sonar
music_pause() music_resume()
music_volume(0-64)          # Volumen
music_stop()                # Para la música
music_pos()  music_row()    # por dónde va (lista de orden, fila 0-63); music_position(n), music_free()
```

## Funciones de ficheros
```
h = file_open("f", 1005)    # Abre para leer (0 si falla)
h = file_open("f", 1006)    # Fichero nuevo, para escribir
h = file_open("f", 1004)    # Leer y escribir
file_close(h)               # nombres: import "lib/amiga/dos.dash" (MODE_READ, MODE_WRITE, MODE_READWRITE)

file_read_byte(h)           # Lee un byte
file_write_byte(h, b)       # Escribe un byte
file_read_line(h, buf, max) # Lee una línea
file_write_line(h, "text")  # Escribe una línea
file_eof(h)                 # ¿Fin del fichero? (mira el siguiente byte, no lo recoge)

file_exists("name")         # ¿Existe el fichero?
file_size("name")           # Tamaño
file_delete("name")         # Borra el fichero
file_print(h, "t")  file_seek(h, pos, mode)  file_pos(h)   # mode -1 inicio, 0 actual, 1 final (SEEK_* en dos.dash)
file_rename("a", "b")  file_copy("a", "b")  dir_create("d")  dir_change("d")  dir_current()
n = file_load("f", buf, max)  file_save("f", buf, n)   # el fichero entero a/desde un buffer (-1: falló)
console_write("t")  console_read(buf, max)
```

## Buffers y memoria en bruto
```
b = buffer_alloc(1024)      # bytes a cero, no se liberan solos: buffer_free(b)
buffer_set_byte(b, 0, 65)  buffer_get_byte(b, 0)   # también _word y _long (big-endian)
buffer_copy(dst, 0, src, 0, n)  buffer_fill(b, 0, n, 0)
peek_byte(addr)  poke_byte(addr, v)   # también _word y _long: cualquier dirección
```

## Funciones del sistema
```
mem_chip_free()             # Chip RAM libre
mem_fast_free()             # Fast RAM libre; mem_total()

time_delay(ticks)           # Espera (50 ticks = 1 s)
time_delay_ms(ms)           # Espera milisegundos
time_ms()                   # Milisegundos desde que empezó el programa
wait_vblank()               # Espera al borrado vertical (vblank)

random()                    # Número aleatorio
random_range(min, max)      # Aleatorio en un rango; random_seed(n)
wait_blit()                 # Espera al blitter

debug_break()               # Para en el depurador del emulador UAE (tools/emu_run.py --debug)

break_check()               # true si llegó Ctrl-C (Break en el Shell); se borra
single_instance("MiProg")   # false si ya corre otra copia (a esa le llega Ctrl-C)
tooltype("CX_POPKEY", "")   # NOMBRE=valor del Shell, si no del icono del programa, si no el de por defecto
cx_broker("MiProg", "Título", "Descripción", 0)   # una commodity en Exchange (mostrar/ocultar activo)
cx_hotkey("ctrl alt t")     # false si no vale; cx_command(): 1 ocultar 2 mostrar 3 desactivar 4 activar 5 quitar 6 tecla
cx_wait(1000)               # una orden, -1 Ctrl-C o 0 cuando pasa el tiempo (no gasta nada mientras)
n = disks_read(500)         # volúmenes montados (preguntados a la vez, 500 ms como mucho): disk_name(i), disk_kb(i), disk_free_kb(i) (-1: sin respuesta)
m = net_ifs_read()          # interfaces de Roadshow (-1 sin él): net_if_name(i), net_if_up(i), net_if_bytes_in(i), net_if_bytes_out(i)
wifi_read("wlan0", 500)     # 0: wifi_signal(), wifi_noise() en dBm; 1 sin respuesta, 2 no lo dice, 3 sin interfaz, 4 desconectada, 5 ocupada, -1 sin Roadshow
d = net_drivers_read()      # drivers SANA-II en uso, con cualquier pila: net_driver_name(i) ("wifipi.device")
wifi_read_device("wifipi.device", 0, 500)   # como wifi_read, preguntando al driver; net_driver_read(driver, unit, ms): net_driver_packets_in/out()
net_driver_has_bytes()      # el driver cuenta también bytes: net_driver_bytes_in(), net_driver_bytes_out()
h = file_notify("ENV:X.prefs")   # vigila un fichero: cx_wait da 7, file_changed(h); file_notify_signal() para MUI
file_notify_end(h)          # deja de vigilarlo (al acabar el programa se paran todos)
run_program("SYS:Prefs/Font")    # lanza una línea de órdenes, sin esperar; program_relaunch(): arrancar de nuevo al acabar
input_text("=SUM(A1:A3)")        # teclea/pulsa en la ventana activa (tests): input_key(0x44, 1), input_click(x, y, q), input_button(2, true), input_drag, input_active_title()
clip_write_text(t); t = clip_read_text()   # portapapeles (unidad 0, FTXT); datos propios: clip_write_block(1, "LCLC", buf, n), clip_block_size, clip_read_block
clock_read()                # clock_year/month/day/weekday(0 dom)/hour/minute/second(); date_text("%A %d-%b-%Y %H:%M") (locale)
locale_decimal_point()      # "," o "." según escriba el país del usuario; locale_group_separator(), locale_date_order() ("DMY"...)
str_compare_locale(a, b, false)   # -1/0/1 en el orden del idioma del usuario (acentos y mayúsculas detrás de las letras); l.sort(f)
t = tr(1, "Hola")           # el texto número 1 del catálogo (@catalog), si no "Hola"; catalog_open(name, version), catalog_language()
mouse_curve(0, [100, 150, 200])      # aceleración del ratón: emisor 0 = ratón del Amiga; factores en centésimas según la velocidad
mouse_curves_off()          # quita ya las curvas de input.device (también al acabar); mouse_curve_events(emitter)
n = usb_hid_read()          # dispositivos hid.class de Poseidon (-1 ninguno): usb_hid_name/maker/vendor/product/kind(i), usb_hid_emitter(i)
mouse_prefs_set(1, false)   # velocidad y aceleración del sistema (vuelven al acabar); mouse_prefs_ticks(), mouse_prefs_accel()
dos_requesters(false)       # sin requesters de "Insert volume"/error de disco: la llamada falla (true: vuelven)
base64_to_file(texto, "T:x.png")   # bytes en base64 a un fichero: bytes escritos, -1 si no es base64

cpu_start()                 # cuenta la CPU de cada tarea (false: sin EClock u OS < 2.04)
n = cpu_sample()            # tareas desde la última muestra, de más a menos: cpu_task_name(i), cpu_task_load(i)
cpu_total()                 # por mil, todas las tareas (el resto es reposo); cpu_stop()
```

## Tareas (C en otro proceso)
```
t = task_start(f, arg)      # @native func f(arg: Int) -> Int en otro proceso (solo C); 0 = falló
task_start_with(f, arg, stack, pri)   # pila en bytes (0: 128 KB), prioridad relativa a la del programa
task_done(t)                # true cuando ya ha vuelto (no espera)
task_result(t)              # lo que devolvió (espera)
task_free(t)                # la olvida (espera); task_signal(): máscara para mui_wait_event_signals
# en el C de una tarea: _dash_task_wake() despierta al programa (task_signal); la red es de un proceso a la vez
# (el primero que la usa, hasta que acaba su tarea): _dash_net_connect_start/poll, _send_buffer/_recv_buffer, _dash_tls_*_buffer...
```

## Lienzo del escritorio (fondo del Workbench)
```
d = desktop_canvas(x, y, w, h)          # una zona del escritorio, detrás de los iconos (negativo: desde la derecha/abajo)
desktop_canvas_on_draw(d, paint)        # func paint(x, y, w, h) dibuja con gfx_
desktop_canvas_update(d)                # dibujar otra vez; desktop_canvas_update_area(d, x, y, w, h): solo esa parte
desktop_canvas_free(d)                  # vuelve el fondo de pantalla (también al salir)
```

## Red (TCP y UDP, bsdsocket.library)
```
s = net_connect("host", 80, 10000)   # socket o -1 (net_error() dice por qué)
net_send(s, "GET / HTTP/1.0\r\n\r\n")
t = net_recv(s, 4096, 10000)         # "" = aún nada, nil = cerrado
net_wait(s, ms)  net_close(s)  net_resolve("host")
net_send_buffer(s, buf, n)  net_recv_buffer(s, buf, max, ms)
t = tls_connect(s, "host")           # TLS (AmiSSL 5.1+, 68020+): tls_send, tls_recv, tls_close; también _buffer
s = net_connect_start("host", 80, 10000)  # sin esperar: net_connect_poll(s) 1 / 0 / -1,
t = tls_connect_start(s, "host", 10000)   # net_connect_stage(s); tls_connect_poll(t) 1 / 0 / -1
ev = mui_wait_event_signals(net_signal())   # despierta con eventos del socket (0: la pila no puede, sondear)
tls_resumed(t)                       # true si reutilizó una sesión anterior con ese servidor
srv = net_listen(8080)               # servidor TCP (0: cualquier puerto libre, net_port(srv)); -1 si está ocupado
c = net_accept(srv, 1000)            # siguiente conexión o -1 (0: solo mirar); net_peer(c) = "a.b.c.d"
u = net_udp_open(5000)               # UDP (0: cualquier puerto libre); net_close(u)
net_udp_send(u, "host", 5000, "hi")  # un datagrama ("255.255.255.255": toda la red local); también _buffer
m = net_udp_recv(u, 1500, 1000)      # "" = nada a tiempo, nil = error; net_udp_from(), net_udp_from_port()
```
No hay builtin de HTTP: el programa habla HTTP él mismo sobre `net_`/`tls_`. No hay sockets en bruto ni tramas SANA-II en bruto.

## Argumentos del programa
```
arg_count()                 # argumentos del Shell; desde el Workbench, los iconos de proyecto (arg(i): ruta completa)
arg(0)                      # el primero ("" si no hay)
```

## Gestión de memoria
> Strings: se liberan solos (cada variable es dueña de su texto; los temporales se
> liberan en cada vuelta de bucle/EventLoop y al salir de una función).
> Arrays y structs: conteo de referencias automático (se liberan cuando nadie los usa).
> Las listas de structs, textos o listas sueltan sus elementos; un struct en una lista de
> enteros, lo dado a C y los ciclos, al salir. `./dash --memcheck` avisa de fallos y fugas.
> Estas funciones son para casos avanzados.

```
# Conteo de referencias (automático; llamadas a mano solo para casos avanzados)
refcount(obj)               # Cuenta actual
retain(obj)                 # Suma uno
release(obj)                # Resta uno (libera al llegar a 0)

# Arena (reserva temporal rápida)
a = arena_new(size)         # Crea la arena
ptr = arena_alloc(a, size)  # Reserva
arena_reset(a)              # Vacía todo
arena_free(a)               # Libera la arena; arena_used(a), arena_available(a)
```

## Patrones habituales

### Bucle de juego
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

### Texto centrado
```
text = "Hola"
w = gfx_text_len(text)
x = (320 - w) / 2
gfx_text_at(x, 100, text)
```

### Movimiento con joystick
```
x = x + joy_x(1) * speed
y = y + joy_y(1) * speed
```

### Bucle de lectura de fichero
```
h = file_open("data.txt", 1005)
while not file_eof(h)
    b = file_read_byte(h)
end
file_close(h)
```

## Códigos de tecla
| Tecla | Código | Tecla | Código |
|-------|--------|-------|--------|
| ESC | 69 | SPACE | 64 |
| RETURN | 68 | UP | 76 |
| LEFT | 79 | DOWN | 77 |
| RIGHT | 78 | F1-F10 | 80-89 |

## Colores estándar
| Índice | Uso habitual |
|--------|--------------|
| 0 | Fondo |
| 1 | Texto/primer plano |
| 2 | Resalte |
| 3 | Sombra |
