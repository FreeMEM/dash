# D.A.S.H. Language - Manual de Referencia del Programador

**Version 1.1** | **D.A.S.H.** (*Development Amiga Synthesis Hub*) — Lenguaje de alto nivel para Amiga que compila a C

*Actualizado: Enero 2026 - Incluye Screens, GadTools y ReAction*

---

## Tabla de Contenidos

1. [Introduccion](#1-introduccion)
2. [Estructura del Programa](#2-estructura-del-programa)
3. [Variables y Tipos de Datos](#3-variables-y-tipos-de-datos)
4. [Constantes](#4-constantes)
5. [Operadores](#5-operadores)
6. [Estructuras de Control](#6-estructuras-de-control)
7. [Funciones](#7-funciones)
8. [Estructuras (Structs)](#8-estructuras-structs)
9. [Enumeraciones](#9-enumeraciones)
10. [Arrays](#10-arrays)
11. [Screens (Pantallas)](#11-screens-pantallas)
12. [Ventanas y Eventos](#12-ventanas-y-eventos)
13. [Graficos](#13-graficos)
14. [Entrada (Teclado, Raton, Joystick)](#14-entrada-teclado-raton-joystick)
15. [Audio y Musica](#15-audio-y-musica)
16. [Sistema de Archivos](#16-sistema-de-archivos)
17. [Gestion de Memoria](#17-gestion-de-memoria)
18. [Funciones del Sistema](#18-funciones-del-sistema)
19. [Interfaz de Usuario - GadTools](#19-interfaz-de-usuario---gadtools)
20. [Interfaz de Usuario - ReAction](#20-interfaz-de-usuario---reaction)
21. [Modulos e Imports](#21-modulos-e-imports)
22. [Ejemplos Completos](#22-ejemplos-completos)
23. [Referencia Rapida](#23-referencia-rapida)

---

## 1. Introduccion

Dash es un lenguaje de programacion de alto nivel disenado para crear aplicaciones y juegos para Amiga. El compilador traduce codigo Dash a C optimizado que puede compilarse con cualquier compilador C para Amiga.

### Caracteristicas Principales

- Sintaxis clara y moderna inspirada en Ruby y Python
- Integracion nativa con AmigaOS (Intuition, Graphics, DOS)
- Sistema de ventanas y graficos simplificado
- 240+ funciones built-in para graficos, audio, archivos, GUI y mas
- Structs con metodos (programacion orientada a objetos ligera)
- Gestion automatica de memoria con Reference Counting
- Arena Allocators para rendimiento maximo

### Hola Mundo

```
Main
    Print "Hola Amiga!"
end
```

### Compilacion

```bash
./dash programa.dash -o programa
```

---

## 2. Estructura del Programa

### Estructura Basica

```
# Imports (opcional)
import "lib/utils.dash"

# Constantes (opcional)
const MAX_ENEMIES = 10
const TITLE = "Mi Juego"

# Enumeraciones (opcional)
enum GameState
    MENU
    PLAYING
    PAUSED
end

# Estructuras (opcional)
struct Player
    x: Int
    y: Int
end

# Definicion de Ventanas (opcional)
Window MainWindow
    title "Mi Aplicacion"
    width 320
    height 200
end

# Funciones (opcional)
func calculate(a, b)
    return a + b
end

# Bloque Principal (requerido)
Main
    # Codigo del programa
    Print "Iniciando..."
end
```

### Comentarios

```
# Esto es un comentario de una linea
x = 10  # Comentario al final de linea
```

---

## 3. Variables y Tipos de Datos

### Declaracion de Variables

Las variables se declaran implicitamente en su primera asignacion:

```
# Enteros
edad = 25
puntuacion = -100
hex_value = 0xFF

# Strings
nombre = "Amiga"
mensaje = "Hola Mundo"

# Booleanos
activo = true
pausado = false

# Arrays
numeros = [1, 2, 3, 4, 5]
vacio = []
```

### Tipos de Datos

| Tipo | Descripcion | Ejemplo |
|------|-------------|---------|
| Int | Entero 32-bit con signo | `42`, `-100`, `0xFF` |
| String | Cadena de texto | `"Hola"` |
| Bool | Valor booleano | `true`, `false` |
| Array | Coleccion de elementos | `[1, 2, 3]` |
| Struct | Tipo compuesto definido por usuario | `Player(10, 20)` |

### Inferencia de Tipos

El tipo se infiere automaticamente:

```
x = 10          # Int
name = "Dash"   # String
flag = true     # Bool
nums = [1,2,3]  # Array de Int
```

---

## 4. Constantes

Las constantes se definen con `const` y no pueden modificarse:

```
const MAX_VIDAS = 3
const SCREEN_WIDTH = 320
const SCREEN_HEIGHT = 200
const GAME_TITLE = "Space Invaders"
const DEBUG_MODE = true
```

### Uso de Constantes

```
Main
    Print GAME_TITLE

    for i in (1..MAX_VIDAS)
        Print "Vida: "
        Print i
    end

    if DEBUG_MODE
        Print "Modo debug activo"
    end
end
```

---

## 5. Operadores

### Operadores Aritmeticos

| Operador | Operacion | Ejemplo |
|----------|-----------|---------|
| `+` | Suma | `a + b` |
| `-` | Resta | `a - b` |
| `*` | Multiplicacion | `a * b` |
| `/` | Division | `a / b` |
| `%` | Modulo | `a % b` |
| `-` | Negacion (unario) | `-x` |

```
resultado = (10 + 5) * 2    # 30
resto = 17 % 5              # 2
negativo = -valor
```

### Operadores de Comparacion

| Operador | Significado |
|----------|-------------|
| `==` | Igual a |
| `!=` | Diferente de |
| `<` | Menor que |
| `>` | Mayor que |
| `<=` | Menor o igual |
| `>=` | Mayor o igual |

### Operadores Logicos

| Operador | Significado |
|----------|-------------|
| `and` | Y logico |
| `or` | O logico |
| `not` | Negacion |

```
if x > 0 and x < 100
    Print "En rango"
end

if not activo or pausado
    Print "Detenido"
end
```

### Concatenacion de Strings

```
saludo = "Hola " + nombre + "!"
Print saludo
```

### Precedencia de Operadores

1. `-`, `not` (unarios)
2. `*`, `/`, `%`
3. `+`, `-`
4. `==`, `!=`, `<`, `>`, `<=`, `>=`
5. `and`
6. `or`

---

## 6. Estructuras de Control

### If / Else

```
if condicion
    # codigo si verdadero
end

if edad >= 18
    Print "Adulto"
else
    Print "Menor"
end
```

### If Anidados

```
if puntos >= 1000
    Print "Experto"
else
    if puntos >= 500
        Print "Intermedio"
    else
        Print "Principiante"
    end
end
```

### While

```
contador = 10
while contador > 0
    Print contador
    contador = contador - 1
end
Print "Despegue!"
```

### For con Rango

Itera desde `inicio` hasta `fin` (ambos incluidos):

```
# Imprime 1, 2, 3, 4, 5
for i in (1..5)
    Print i
end

# Cuenta regresiva usando variable
for i in (1..n)
    Print n - i + 1
end
```

### For Each (Iteracion de Arrays)

```
enemigos = [enemy1, enemy2, enemy3]

for enemigo in enemigos
    enemigo.mover(1, 0)
end
```

### Comandos de Control

| Comando | Efecto |
|---------|--------|
| `Stop` | Sale del EventLoop y termina programa |
| `return valor` | Retorna de una funcion con valor |
| `return` | Retorna de una funcion sin valor |

---

## 7. Funciones

### Definicion Basica

```
func saludar()
    Print "Hola!"
end

func duplicar(n)
    return n * 2
end
```

### Con Anotaciones de Tipo

```
func sumar(a: Int, b: Int) -> Int
    return a + b
end

func crear_mensaje(nombre: String) -> String
    return "Bienvenido " + nombre
end
```

### Llamada a Funciones

```
saludar()
resultado = duplicar(21)
suma = sumar(10, 20)
```

### Funciones Recursivas

```
func factorial(n)
    if n <= 1
        return 1
    end
    return n * factorial(n - 1)
end
```

---

## 8. Estructuras (Structs)

### Definicion

```
struct Enemigo
    x: Int
    y: Int
    vida: Int = 100     # Valor por defecto
    nombre: String
end
```

### Creacion de Instancias

```
# Constructor con todos los campos
e1 = Enemigo(100, 50, 100, "Alien")

# Acceso a campos
Print e1.x
Print e1.nombre
e1.vida = e1.vida - 10
```

### Metodos

```
struct Jugador
    x: Int = 0
    y: Int = 0
    velocidad: Int = 5

    func mover(dx, dy)
        self.x = self.x + dx * self.velocidad
        self.y = self.y + dy * self.velocidad
    end

    func dibujar()
        gfx_rect(self.x, self.y, self.x + 16, self.y + 16)
    end

    func reset()
        self.x = 160
        self.y = 100
    end
end

Main
    player = Jugador(160, 100, 5)
    player.mover(1, 0)      # Mueve a la derecha
    player.dibujar()
end
```

---

## 9. Enumeraciones

### Definicion

```
enum Estado
    MENU
    JUGANDO
    PAUSADO
    GAME_OVER
end

enum Direccion
    ARRIBA = 0
    ABAJO = 1
    IZQUIERDA = 2
    DERECHA = 3
end
```

### Uso

```
estado_actual = Estado.MENU

if estado_actual == Estado.JUGANDO
    actualizar_juego()
end

direccion = Direccion.ARRIBA
```

---

## 10. Arrays

### Creacion

```
numeros = [1, 2, 3, 4, 5]
nombres = ["Ana", "Bob", "Carlos"]
vacio = []
```

### Acceso y Modificacion

```
primero = numeros[0]      # Acceso (indice 0)
numeros[2] = 100          # Modificacion
```

### Propiedades

```
longitud = numeros.length
```

### Slicing (Rebanado)

```
arr = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

sub1 = arr[2:5]     # [2, 3, 4]
sub2 = arr[:3]      # [0, 1, 2]
sub3 = arr[7:]      # [7, 8, 9]
```

### Iteracion

```
for num in numeros
    Print num
end
```

---

## 11. Screens (Pantallas)

Las screens en Amiga son superficies de dibujo independientes que pueden tener su propia resolucion, profundidad de color y paleta. Dash proporciona funciones para crear screens que clonan el Workbench o screens personalizadas.

### Clonar Workbench

La funcion `screen_open()` clona el modo de display del Workbench, incluyendo resolucion, modo de video y pens del sistema:

```
# Abrir screen clonando Workbench con 16 colores (4 bitplanes)
screen_open(4, "Mi Aplicacion")

# Con 32 colores (5 bitplanes)
screen_open(5, "Juego 32 colores")
```

Esta funcion:
- Bloquea el Workbench para leer sus propiedades
- Obtiene el ModeID del ViewPort
- Copia los DrawInfo pens para consistencia visual
- Crea una screen con el mismo modo de display

### Screen Personalizada

Para screens con dimensiones especificas, usa `screen_open_custom()`:

```
# Screen 320x256 con 32 colores
screen_open_custom(320, 256, 5, "Juego Retro")

# Screen 640x480 con 256 colores (para RTG)
screen_open_custom(640, 480, 8, "Aplicacion HiRes")

# Screen 1280x720 para monitores modernos
screen_open_custom(1280, 720, 8, "App Moderna")
```

Esta funcion usa `BestModeID()` para encontrar el mejor modo de display que soporte las dimensiones solicitadas. Si no encuentra uno especifico, usa el modo del Workbench como fallback.

### Cerrar Screen

```
screen_close()
```

Cierra la screen abierta y libera recursos.

### Ejemplo Completo

```
Window MiVentana
    title "Demo Screen"
    width 300
    height 200
    left 10
    top 20
end

Main
    # Abrir screen clonando Workbench
    screen_open(4, "Demo Dash")

    # Abrir ventana en la screen
    MiVentana.open

    # Configurar paleta personalizada
    gfx_rgb(0, 0, 0, 8)      # Fondo azul oscuro
    gfx_rgb(1, 15, 15, 15)   # Blanco
    gfx_rgb(2, 15, 0, 0)     # Rojo
    gfx_rgb(3, 0, 15, 0)     # Verde

    # Dibujar
    gfx_pen(1)
    gfx_text_at(50, 100, "Hola desde Dash!")

    # Esperar tecla
    key_wait()

    # Cerrar todo
    close_window()
    screen_close()
end
```

### Funciones de Screen

| Funcion | Descripcion |
|---------|-------------|
| `screen_open(depth, title)` | Clona Workbench con profundidad especificada |
| `screen_open_custom(w, h, depth, title)` | Screen con dimensiones personalizadas |
| `screen_close()` | Cierra la screen actual |

### Notas Importantes

- Las ventanas abiertas despues de `screen_open()` se abren automaticamente en esa screen
- La profundidad (depth) determina el numero de colores: 4=16, 5=32, 6=64, 8=256
- En sistemas RTG, `screen_open_custom()` puede usar resoluciones no nativas
- Siempre cierra la screen al terminar para liberar recursos

---

## 12. Ventanas y Eventos

### Definicion de Ventana

```
Window MiVentana
    title "Mi Aplicacion"
    width 400
    height 300
    left 50
    top 50
    closegadget true
    dragbar true
    depthgadget true
    sizegadget false
end
```

### Propiedades de Ventana

| Propiedad | Descripcion | Tipo |
|-----------|-------------|------|
| `title` | Titulo de la ventana | String |
| `width` | Ancho en pixeles | Int |
| `height` | Alto en pixeles | Int |
| `left` | Posicion X inicial | Int |
| `top` | Posicion Y inicial | Int |
| `closegadget` | Boton de cerrar | Bool |
| `dragbar` | Barra para arrastrar | Bool |
| `depthgadget` | Gadget de profundidad | Bool |
| `sizegadget` | Permite redimensionar | Bool |

### Abrir y Cerrar

```
MiVentana.open      # Abre la ventana
MiVentana.close     # Cierra la ventana
```

### Event Loop

```
Main
    MiVentana.open

    EventLoop
        On Close
            Print "Cerrando..."
            Stop
        end
    end
end
```

### Ejemplo Completo

```
Window GameWindow
    title "Space Game"
    width 320
    height 256
end

Main
    Print "Iniciando juego..."
    GameWindow.open

    # Dibujar contenido inicial
    gfx_pen(1)
    gfx_text_at(100, 128, "Pulsa para jugar")

    EventLoop
        On Close
            Stop
        end
    end

    Print "Juego terminado"
end
```

---

## 13. Graficos

### Configuracion de Color

```
gfx_pen(color)                  # Color de dibujo (0-31)
gfx_pen_bg(color)               # Color de fondo
gfx_pen_outline(color)          # Color de contorno

# Definir colores RGB (0-15 cada componente)
gfx_rgb(0, 0, 0, 0)             # Color 0 = Negro
gfx_rgb(1, 15, 15, 15)          # Color 1 = Blanco
gfx_rgb(2, 15, 0, 0)            # Color 2 = Rojo
gfx_rgb(3, 0, 15, 0)            # Color 3 = Verde
gfx_rgb(4, 0, 0, 15)            # Color 4 = Azul
```

### Primitivas Basicas

```
# Pixel
gfx_pixel(x, y)
color = gfx_pixel_read(x, y)

# Lineas
gfx_move(x, y)                  # Mover cursor
gfx_draw(x, y)                  # Linea hasta punto
gfx_line(x1, y1, x2, y2)        # Linea directa

# Rectangulos
gfx_rect(x1, y1, x2, y2)        # Rectangulo relleno
gfx_box(x1, y1, x2, y2)         # Rectangulo contorno

# Circulos y Elipses
gfx_circle(cx, cy, radio)              # Circulo contorno
gfx_circle_fill(cx, cy, radio)         # Circulo relleno
gfx_ellipse(cx, cy, rx, ry)            # Elipse contorno
gfx_ellipse_fill(cx, cy, rx, ry)       # Elipse rellena
```

### Poligonos

```
gfx_pen(3)
gfx_poly_begin(100, 50)         # Primer vertice
gfx_poly_add(150, 100)          # Segundo vertice
gfx_poly_add(50, 100)           # Tercer vertice
gfx_poly_end()                  # Cierra y rellena
```

### Texto

```
gfx_text_at(x, y, "Texto")      # Texto en posicion
gfx_text("Mas texto")           # Texto en cursor
ancho = gfx_text_len("Hola")    # Ancho en pixeles
```

### Pantalla

```
gfx_clear()                     # Limpiar con color 0
gfx_clear_color(color)          # Limpiar con color
gfx_scroll(dx, dy, x1, y1, x2, y2)  # Scroll de region
```

### Ejemplo de Graficos

```
Window GfxDemo
    title "Demo Graficos"
    width 320
    height 200
end

Main
    GfxDemo.open

    # Definir paleta
    gfx_rgb(1, 15, 15, 15)      # Blanco
    gfx_rgb(2, 15, 0, 0)        # Rojo
    gfx_rgb(3, 0, 15, 0)        # Verde

    # Dibujar formas
    gfx_pen(1)
    gfx_box(10, 10, 310, 190)   # Marco

    gfx_pen(2)
    gfx_circle_fill(160, 100, 40)

    gfx_pen(3)
    gfx_line(0, 100, 320, 100)

    gfx_pen(1)
    gfx_text_at(120, 180, "Demo!")

    EventLoop
        On Close
            Stop
        end
    end
end
```

---

## 14. Entrada (Teclado, Raton, Joystick)

### Teclado

```
# Verificar si hay tecla disponible
if key_pressed()
    tecla = key_get()
    Print tecla
end

# Esperar tecla (bloqueante)
tecla = key_wait()

# Obtener codigo raw
raw = key_raw()

# Convertir a texto
texto = key_text(tecla)
```

### Raton

```
x = mouse_x()
y = mouse_y()

# Botones: 0 = izquierdo, 1 = derecho
if mouse_button(0)
    Print "Click izquierdo"
end
```

### Joystick

```
# Puertos: 0 o 1
dx = joy_x(0)       # -1, 0, o 1
dy = joy_y(0)       # -1, 0, o 1

if joy_button(0)
    Print "Disparo!"
end

# Funciones de direccion (devuelven Bool)
if joy_up(0)
    y = y - 1
end
if joy_down(0)
    y = y + 1
end
if joy_left(0)
    x = x - 1
end
if joy_right(0)
    x = x + 1
end
if joy_fire(0)
    disparar()
end
```

---

## 15. Audio y Musica

### Cargar y Reproducir Sonidos

```
# Cargar sonido IFF 8SVX
sound_load(0, "disparo.8svx")
sound_load(1, "explosion.8svx")

# Reproducir en canal (0-3)
sound_play(0, 0)        # Sonido 0 en canal 0

# Reproducir en loop
sound_loop(1, 1)        # Sonido 1 en canal 1, loop

# Detener canal
sound_stop(0)

# Volumen (0-64)
sound_volume(0, 48)
```

### Musica MOD

```
# Cargar modulo
music_load("intro.mod")

# Control de reproduccion
music_play()
music_pause()
music_resume()
music_stop()

# Volumen (0-64)
music_volume(64)

# Posicion
music_position(0)       # Ir al inicio

# Liberar
music_free()
```

### Tonos Sintetizados

```
# tone_play(canal, frecuencia_hz, volumen, duracion_ticks)
tone_play(0, 440, 64, 50)   # La 440Hz
tone_play(1, 523, 48, 25)   # Do
```

---

## 16. Sistema de Archivos

### Abrir y Cerrar Archivos

```
# Modos: MODE_OLDFILE (lectura), MODE_NEWFILE (escritura), MODE_READWRITE
handle = file_open("datos.txt", MODE_OLDFILE)

if handle
    # Usar archivo...
    file_close(handle)
end
```

### Lectura

```
handle = file_open("config.txt", MODE_OLDFILE)

while not file_eof(handle)
    byte = file_read_byte(handle)
    # o leer linea completa:
    # linea = file_read_line(handle, buffer, 256)
end

file_close(handle)
```

### Escritura

```
handle = file_open("salida.txt", MODE_NEWFILE)

file_write_line(handle, "Primera linea")
file_print(handle, "Texto sin salto")
file_write_byte(handle, 65)     # 'A'

file_close(handle)
```

### Posicion en Archivo

```
file_seek(handle, 0, OFFSET_BEGINNING)  # Al inicio
file_seek(handle, -10, OFFSET_END)      # 10 bytes antes del final
pos = file_pos(handle)                   # Posicion actual
```

### Sistema de Archivos

```
if file_exists("config.dat")
    Print "Archivo encontrado"
end

tamano = file_size("datos.bin")

file_delete("temp.tmp")
file_rename("viejo.txt", "nuevo.txt")
file_copy("original.dat", "backup.dat")
```

### Directorios

```
dir_create("saves")
dir_change("work:")
dir_current(buffer, 256)    # Obtener directorio actual
```

---

## 17. Gestion de Memoria

### Reference Counting (Automatico)

Dash usa conteo de referencias para structs y arrays:

```
struct Objeto
    valor: Int
end

Main
    obj = Objeto(42)        # refcount = 1

    # Verificar contador
    Print refcount(obj)     # Imprime: 1

    # Compartir referencia
    otro = obj
    retain(otro)            # refcount = 2

    # Liberar referencia
    release(otro)           # refcount = 1
end
# Al salir de Main, obj se libera automaticamente
```

### Arena Allocator (Manual)

Para asignaciones temporales de alto rendimiento:

```
# Crear arena de 64KB
arena = arena_new(65536)

# Asignar rapidamente (sin overhead)
ptr1 = arena_alloc(arena, 100)
ptr2 = arena_alloc(arena, 200)
ptr3 = arena_alloc(arena, 50)

# Ver uso
Print arena_used(arena)         # Bytes usados
Print arena_available(arena)    # Bytes disponibles

# Resetear todo de una vez (instantaneo)
arena_reset(arena)

# Liberar arena completa
arena_free(arena)
```

### Cuando Usar Cada Uno

| Escenario | Metodo |
|-----------|--------|
| Objetos de larga vida | Reference Counting (automatico) |
| Objetos temporales por frame | Arena Allocator |
| Pools de enemigos/balas | Arena Allocator |
| Datos de juego persistentes | Reference Counting |

---

## 18. Funciones del Sistema

### Memoria del Sistema

```
chip = mem_chip_free()      # RAM Chip disponible
fast = mem_fast_free()      # RAM Fast disponible
total = mem_total()         # Total disponible
```

### Tiempo y Espera

```
time_delay(50)              # Esperar 50 ticks (1 segundo)
time_delay_ms(500)          # Esperar 500 milisegundos
wait_vblank()               # Esperar vertical blank
wait_blit()                 # Esperar que termine el blitter
```

### Numeros Aleatorios

```
n = random()                        # Numero aleatorio
dado = random_range(1, 6)           # Entre 1 y 6
random_seed(12345)                  # Establecer semilla
```

---

## 19. Interfaz de Usuario - GadTools

GadTools es el sistema de gadgets nativo de AmigaOS 2.0+. Es ideal para aplicaciones que necesitan combinar gadgets con dibujo personalizado (como editores graficos).

### Inicializacion

```
gt_init()       # Inicializar GadTools (despues de abrir ventana)
gt_attach()     # Adjuntar gadgets a la ventana
gt_cleanup()    # Limpiar al cerrar
```

### Botones

```
# gt_button(x, y, width, height, label) -> gadget_id
btn_ok = gt_button(10, 10, 80, 20, "OK")
btn_cancel = gt_button(100, 10, 80, 20, "Cancel")
```

### Paleta de Colores

```
# gt_palette(x, y, width, height, label, color_inicial, depth) -> gadget_id
pal = gt_palette(10, 40, 100, 80, "Color", 1, 4)

# Obtener color seleccionado
color = gt_get_value(pal)
```

### Slider

```
# gt_slider(x, y, width, height, label, min, max, initial) -> gadget_id
slider = gt_slider(10, 130, 150, 20, "Volumen", 0, 100, 50)

# Obtener/establecer valor
valor = gt_get_value(slider)
gt_set_value(slider, 75)
```

### Checkbox

```
# gt_checkbox(x, y, width, height, label, checked) -> gadget_id
check = gt_checkbox(10, 160, 150, 20, "Activar", false)

# Obtener estado
activo = gt_get_value(check)
```

### Eventos de Gadgets

```
# En el loop principal:
event = gt_event()

if event == -2          # Ventana cerrada
    running = false
end

if event == btn_ok
    Print "OK pulsado"
end

if event == slider
    valor = gt_get_value(slider)
end
```

### Menus

```
# Crear estructura de menus
menu_title("Archivo")
menu_item("Nuevo", "N", MENU_NEW)
menu_item("Abrir...", "O", MENU_OPEN)
menu_item("Guardar...", "S", MENU_SAVE)
menu_separator()
menu_item("Salir", "Q", MENU_QUIT)

menu_title("Ayuda")
menu_item("Acerca de...", "?", MENU_ABOUT)

# Adjuntar menus a la ventana
menu_attach()

# En el loop:
menu_ev = menu_event()
if menu_ev == MENU_QUIT
    running = false
end
```

### Dialogos ASL

```
# Selector de archivo para abrir
if file_open_dialog("Abrir Sprite", "#?.iff")
    # El usuario selecciono un archivo
end

# Selector de archivo para guardar
if file_save_dialog("Guardar Como", "#?.iff")
    # El usuario eligio donde guardar
end
```

### Ejemplo Completo con GadTools

```
Window EditorWin
    title "Editor"
    width 320
    height 220
end

const BTN_CLEAR = 1
const BTN_SAVE = 2

Main
    screen_open(4, "Mi Editor")
    EditorWin.open

    gt_init()

    # Crear gadgets
    pal = gt_palette(10, 40, 70, 80, "Color", 1, 4)
    btn_clear = gt_button(10, 130, 70, 20, "Limpiar")
    btn_save = gt_button(10, 155, 70, 20, "Guardar")

    gt_attach()

    # Dibujar area de trabajo
    gfx_pen(1)
    gfx_box(90, 40, 300, 200)

    running = true
    while running
        event = gt_event()

        if event == -2
            running = false
        end

        if event == btn_clear
            gfx_pen(0)
            gfx_rect(91, 41, 299, 199)
        end

        if event == pal
            color = gt_get_value(pal)
            gfx_pen(color)
        end

        wait_vblank()
    end

    gt_cleanup()
    close_window()
    screen_close()
end
```

### Funciones GadTools

| Funcion | Descripcion |
|---------|-------------|
| `gt_init()` | Inicializar GadTools |
| `gt_attach()` | Adjuntar gadgets a ventana |
| `gt_cleanup()` | Limpiar recursos |
| `gt_button(x,y,w,h,label)` | Crear boton |
| `gt_palette(x,y,w,h,label,color,depth)` | Crear selector de paleta |
| `gt_slider(x,y,w,h,label,min,max,init)` | Crear slider |
| `gt_checkbox(x,y,w,h,label,checked)` | Crear checkbox |
| `gt_event()` | Obtener evento de gadget |
| `gt_get_value(gadget)` | Obtener valor de gadget |
| `gt_set_value(gadget,value)` | Establecer valor de gadget |
| `menu_title(name)` | Crear titulo de menu |
| `menu_item(name,shortcut,id)` | Crear item de menu |
| `menu_separator()` | Crear separador |
| `menu_attach()` | Adjuntar menus |
| `menu_event()` | Obtener evento de menu |

---

## 20. Interfaz de Usuario - ReAction

ReAction es el sistema de GUI moderno de AmigaOS 3.2+ basado en BOOPSI. Usa un sistema de layout automatico que gestiona el posicionamiento de gadgets.

**Nota:** ReAction es ideal para dialogos y formularios. Para aplicaciones con dibujo personalizado extenso (como editores de pixels), usa GadTools.

### Crear Ventana ReAction

```
# ra_window_create(titulo, ancho, alto)
ra_window_create("Mi Aplicacion", 300, 200)

# Abrir la ventana
ra_window_open()

# Cerrar al terminar
ra_window_close()
```

### Gadgets Disponibles

```
# Etiqueta de texto
ra_add_label("Titulo:")

# Boton
# ra_add_button(id, label)
ra_add_button(1, "Aceptar")
ra_add_button(2, "Cancelar")

# Campo de texto
# ra_add_string(id, texto_inicial, max_chars)
ra_add_string(3, "Nombre", 64)

# Checkbox
# ra_add_checkbox(id, label, checked)
ra_add_checkbox(4, "Activar opcion", false)

# Slider
# ra_add_slider(id, min, max, initial)
ra_add_slider(5, 0, 100, 50)

# Entero
# ra_add_integer(id, initial, min, max)
ra_add_integer(6, 0, 0, 999)

# Paleta de colores (selector de color)
# ra_add_palette(id, depth, initial_color)
ra_add_palette(7, 4, 1)   # 4 bits = 16 colores, color inicial 1

# Chooser (dropdown/menu desplegable)
# ra_add_chooser(id) - crea el chooser vacio
ra_add_chooser(8)
ra_chooser_add_item(8, "Opcion 1")
ra_chooser_add_item(8, "Opcion 2")
ra_chooser_add_item(8, "Opcion 3")

# Scroller (horizontal)
# ra_add_scroller(id, min, max, visible, initial)
ra_add_scroller(9, 0, 100, 10, 0)

# Scroller vertical
# ra_add_scroller_vert(id, min, max, visible, initial)
ra_add_scroller_vert(10, 0, 100, 10, 0)
```

### Layout con Grupos

ReAction permite organizar gadgets en grupos horizontales y verticales:

```
# Crear un grupo horizontal
ra_layout_hgroup_begin()
    ra_add_button(1, "Izq")
    ra_add_button(2, "Centro")
    ra_add_button(3, "Der")
ra_layout_group_end()

# Crear un grupo vertical
ra_layout_vgroup_begin()
    ra_add_label("Seccion 1")
    ra_add_string(4, "", 32)
    ra_add_label("Seccion 2")
    ra_add_string(5, "", 32)
ra_layout_group_end()

# Espaciadores
ra_add_space()   # Espacio horizontal
ra_add_vspace()  # Espacio vertical
```

### Obtener y Establecer Valores

```
# Obtener valor numerico (slider, checkbox, integer, scroller)
valor = ra_get_value(gadget_id)

# Obtener texto (string gadget)
texto = ra_get_string(gadget_id)

# Establecer valor numerico
ra_set_value(gadget_id, nuevo_valor)

# Establecer texto en string gadget
ra_set_string(gadget_id, "nuevo texto")

# Establecer texto en label
ra_set_text(gadget_id, "Nuevo titulo")

# Para Palette
color = ra_get_palette_color(palette_id)

# Para Chooser (dropdown)
indice = ra_get_chooser_selected(chooser_id)
ra_set_chooser_selected(chooser_id, nuevo_indice)
```

### Control de Gadgets

```
# Activar/desactivar gadgets
ra_disable_gadget(gadget_id)  # Deshabilitar (gris)
ra_enable_gadget(gadget_id)   # Habilitar de nuevo

# Verificar si gadget existe
if ra_gadget_exists(gadget_id)
    valor = ra_get_value(gadget_id)
end
```

### Utilidades de Ventana

```
# Obtener dimensiones de la ventana
ancho = ra_window_width()
alto = ra_window_height()

# Verificar si ventana esta abierta
if ra_window_is_open()
    # La ventana existe
end
```

### Manejo de Eventos

```
# Esperar y obtener evento
event = ra_wait_event()

# Constantes de eventos
# RA_EVENT_CLOSE() - Ventana cerrada
# RA_EVENT_NONE()  - Sin evento

if event == RA_EVENT_CLOSE()
    running = false
end

if event == 1  # ID del boton Aceptar
    Print "Aceptar pulsado"
end
```

### Dibujo Personalizado en ReAction

Para dibujar en una ventana ReAction:

```
# Obtener RastPort despues de abrir ventana
ra_get_rastport()

# Ahora puedes usar funciones gfx_*
gfx_pen(1)
gfx_rect(10, 100, 200, 150)
```

**Advertencia:** El layout automatico de ReAction puede sobrescribir dibujos personalizados al redimensionar. Para aplicaciones con mucho dibujo, usa GadTools.

### Ejemplo: Dialogo de Configuracion

```
const BTN_OK = 1
const BTN_CANCEL = 2
const CHK_SOUND = 3
const SLD_VOLUME = 4
const STR_NAME = 5

Main
    ra_window_create("Configuracion", 250, 180)

    ra_add_label("Nombre del jugador:")
    ra_add_string(STR_NAME, "Player1", 32)

    ra_add_checkbox(CHK_SOUND, "Activar sonido", true)

    ra_add_label("Volumen:")
    ra_add_slider(SLD_VOLUME, 0, 100, 75)

    ra_add_label("---")
    ra_add_button(BTN_OK, "Aceptar")
    ra_add_button(BTN_CANCEL, "Cancelar")

    ra_window_open()

    running = true
    while running
        event = ra_wait_event()

        if event == RA_EVENT_CLOSE()
            running = false
        end

        if event == BTN_OK
            nombre = ra_get_string(STR_NAME)
            sonido = ra_get_value(CHK_SOUND)
            volumen = ra_get_value(SLD_VOLUME)
            # Guardar configuracion...
            running = false
        end

        if event == BTN_CANCEL
            running = false
        end
    end

    ra_window_close()
end
```

### ReAction con Screen Personalizada

```
Main
    # Abrir screen primero
    screen_open(4, "Mi App")

    # La ventana ReAction se abrira en esa screen
    ra_window_create("Opciones", 200, 150)
    ra_add_button(1, "OK")
    ra_window_open()

    # ...

    ra_window_close()
    screen_close()
end
```

### Funciones ReAction

#### Ventana
| Funcion | Descripcion |
|---------|-------------|
| `ra_window_create(title,w,h)` | Crear ventana ReAction |
| `ra_window_open()` | Abrir ventana |
| `ra_window_close()` | Cerrar ventana |
| `ra_window_width()` | Obtener ancho de ventana |
| `ra_window_height()` | Obtener alto de ventana |
| `ra_window_is_open()` | Verificar si ventana esta abierta |
| `ra_get_rastport()` | Obtener RastPort para dibujo |

#### Gadgets Basicos
| Funcion | Descripcion |
|---------|-------------|
| `ra_add_label(text)` | Anadir etiqueta |
| `ra_add_button(id,label)` | Anadir boton |
| `ra_add_string(id,text,max)` | Anadir campo de texto |
| `ra_add_checkbox(id,label,checked)` | Anadir checkbox |
| `ra_add_slider(id,min,max,init)` | Anadir slider |
| `ra_add_integer(id,init,min,max)` | Anadir campo numerico |

#### Gadgets Avanzados
| Funcion | Descripcion |
|---------|-------------|
| `ra_add_palette(id,depth,init)` | Selector de color (depth=bits) |
| `ra_add_chooser(id)` | Crear dropdown vacio |
| `ra_chooser_add_item(id,label)` | Anadir item a dropdown |
| `ra_add_scroller(id,min,max,vis,init)` | Scroller horizontal |
| `ra_add_scroller_vert(id,min,max,vis,init)` | Scroller vertical |

#### Layout
| Funcion | Descripcion |
|---------|-------------|
| `ra_layout_hgroup_begin()` | Iniciar grupo horizontal |
| `ra_layout_vgroup_begin()` | Iniciar grupo vertical |
| `ra_layout_group_end()` | Cerrar grupo |
| `ra_add_space()` | Espacio horizontal |
| `ra_add_vspace()` | Espacio vertical |

#### Obtener/Establecer Valores
| Funcion | Descripcion |
|---------|-------------|
| `ra_get_value(id)` | Obtener valor numerico |
| `ra_set_value(id,value)` | Establecer valor numerico |
| `ra_get_string(id)` | Obtener texto |
| `ra_set_string(id,text)` | Establecer texto en string gadget |
| `ra_set_text(id,text)` | Establecer texto en label |
| `ra_get_palette_color(id)` | Obtener color de paleta |
| `ra_get_chooser_selected(id)` | Obtener indice de dropdown |
| `ra_set_chooser_selected(id,idx)` | Establecer seleccion dropdown |

#### Control de Gadgets
| Funcion | Descripcion |
|---------|-------------|
| `ra_enable_gadget(id)` | Habilitar gadget |
| `ra_disable_gadget(id)` | Deshabilitar gadget |
| `ra_gadget_exists(id)` | Verificar si gadget existe |

#### Eventos
| Funcion | Descripcion |
|---------|-------------|
| `ra_wait_event()` | Esperar evento |
| `RA_EVENT_CLOSE()` | Constante: ventana cerrada |
| `RA_EVENT_NONE()` | Constante: sin evento |

### GadTools vs ReAction

| Caracteristica | GadTools | ReAction |
|----------------|----------|----------|
| Posicionamiento | Manual (absoluto) | Automatico (layout) |
| Compatibilidad | AmigaOS 2.0+ | AmigaOS 3.2+ |
| Dibujo custom | Excelente | Limitado |
| Redimensionar | Sin problemas | Layout recalcula |
| Ideal para | Editores, juegos | Dialogos, formularios |
| Estilo visual | Clasico | Moderno |

---

## 21. Modulos e Imports

### Importar Modulo

```
import "lib/matematicas.dash"
import "utils/helpers.dash"
```

### Crear un Modulo

Archivo `lib/matematicas.dash`:
```
func cuadrado(n)
    return n * n
end

func cubo(n)
    return n * n * n
end

func maximo(a, b)
    if a > b
        return a
    end
    return b
end
```

### Usar el Modulo

```
import "lib/matematicas.dash"

Main
    x = cuadrado(5)         # 25
    y = cubo(3)             # 27
    z = maximo(10, 20)      # 20
    Print z
end
```

---

## 22. Ejemplos Completos

### Ejemplo 1: Hola Mundo con Ventana

```
Window HelloWin
    title "Hola Mundo"
    width 300
    height 100
end

Main
    HelloWin.open

    gfx_pen(1)
    gfx_text_at(100, 50, "Hola Amiga!")

    EventLoop
        On Close
            Stop
        end
    end
end
```

### Ejemplo 2: Contador Interactivo

```
Window CounterWin
    title "Contador"
    width 200
    height 100
end

const MAX_COUNT = 100

Main
    CounterWin.open

    count = 0

    while count < MAX_COUNT
        gfx_clear()
        gfx_pen(1)
        gfx_text_at(80, 50, "Contador:")
        # Mostrar numero requiere conversion

        count = count + 1
        time_delay(25)      # Medio segundo
    end

    EventLoop
        On Close
            Stop
        end
    end
end
```

### Ejemplo 3: Movimiento con Joystick

```
Window GameWin
    title "Joystick Demo"
    width 320
    height 200
end

struct Player
    x: Int = 160
    y: Int = 100
    size: Int = 10

    func update()
        dx = joy_x(0)
        dy = joy_y(0)
        self.x = self.x + dx * 2
        self.y = self.y + dy * 2

        # Limites de pantalla
        if self.x < 0
            self.x = 0
        end
        if self.x > 310
            self.x = 310
        end
        if self.y < 0
            self.y = 0
        end
        if self.y > 190
            self.y = 190
        end
    end

    func draw()
        gfx_pen(2)
        gfx_rect(self.x, self.y, self.x + self.size, self.y + self.size)
    end
end

Main
    GameWin.open

    gfx_rgb(2, 0, 15, 0)    # Verde para jugador

    player = Player(160, 100, 10)

    running = true
    while running
        gfx_clear()

        player.update()
        player.draw()

        wait_vblank()

        # Verificar cierre de ventana seria aqui
        # (simplificado para el ejemplo)
    end
end
```

### Ejemplo 4: Dibujo de Graficos

```
Window ArtWin
    title "Arte Amiga"
    width 320
    height 256
end

Main
    ArtWin.open

    # Configurar paleta
    gfx_rgb(0, 0, 0, 4)         # Fondo azul oscuro
    gfx_rgb(1, 15, 15, 15)      # Blanco
    gfx_rgb(2, 15, 8, 0)        # Naranja
    gfx_rgb(3, 15, 0, 0)        # Rojo
    gfx_rgb(4, 0, 15, 0)        # Verde

    gfx_clear()

    # Marco
    gfx_pen(1)
    gfx_box(5, 5, 315, 251)

    # Sol
    gfx_pen(2)
    gfx_circle_fill(260, 50, 30)

    # Montanas
    gfx_pen(4)
    gfx_poly_begin(0, 200)
    gfx_poly_add(80, 120)
    gfx_poly_add(160, 200)
    gfx_poly_end()

    gfx_poly_begin(100, 200)
    gfx_poly_add(200, 100)
    gfx_poly_add(300, 200)
    gfx_poly_end()

    # Texto
    gfx_pen(1)
    gfx_text_at(110, 240, "Amiga Forever!")

    EventLoop
        On Close
            Stop
        end
    end
end
```

### Ejemplo 5: Sistema de Archivos

```
Main
    # Escribir archivo
    handle = file_open("RAM:test.txt", MODE_NEWFILE)
    if handle
        file_write_line(handle, "Linea 1")
        file_write_line(handle, "Linea 2")
        file_write_line(handle, "Linea 3")
        file_close(handle)
        Print "Archivo escrito"
    end

    # Leer archivo
    handle = file_open("RAM:test.txt", MODE_OLDFILE)
    if handle
        Print "Contenido:"
        while not file_eof(handle)
            byte = file_read_byte(handle)
            # Procesar byte...
        end
        file_close(handle)
    end

    # Verificar existencia
    if file_exists("RAM:test.txt")
        tamano = file_size("RAM:test.txt")
        Print "Tamano del archivo:"
        Print tamano
    end
end
```

### Ejemplo 6: Sonido y Musica

```
Window SoundWin
    title "Demo Audio"
    width 200
    height 100
end

Main
    SoundWin.open

    # Cargar sonidos
    sound_load(0, "sounds/beep.8svx")
    sound_load(1, "sounds/boom.8svx")

    # Cargar musica
    music_load("mods/intro.mod")
    music_volume(48)
    music_play()

    gfx_pen(1)
    gfx_text_at(50, 50, "Musica sonando...")

    EventLoop
        On Close
            music_stop()
            music_free()
            Stop
        end
    end
end
```

---

## 23. Referencia Rapida

### Sintaxis Basica

| Construccion | Sintaxis |
|--------------|----------|
| Variable | `nombre = valor` |
| Constante | `const NOMBRE = valor` |
| Funcion | `func nombre(params) ... end` |
| Struct | `struct Nombre ... end` |
| Enum | `enum Nombre ... end` |
| If | `if cond ... end` |
| If/Else | `if cond ... else ... end` |
| While | `while cond ... end` |
| For Range | `for i in (a..b) ... end` |
| For Each | `for x in array ... end` |
| Ventana | `Window Nombre ... end` |
| Main | `Main ... end` |
| EventLoop | `EventLoop ... end` |
| On Close | `On Close ... end` |
| Comentario | `# comentario` |

### Funciones por Categoria

| Categoria | Cantidad | Ejemplos |
|-----------|----------|----------|
| Graficos Basicos | 28 | `gfx_pen`, `gfx_line`, `gfx_rect`, `gfx_circle` |
| Graficos Avanzados | 32 | `sprite_*`, `bob_*`, `copper_*`, `bitmap_*` |
| Entrada | 16 | `key_*`, `mouse_*`, `joy_*` |
| Sistema | 18 | `mem_*`, `time_*`, `random_*`, `arena_*` |
| Archivos | 22 | `file_*`, `dir_*`, `console_*` |
| Audio | 18 | `sound_*`, `music_*`, `tone_*` |
| Screens | 3 | `screen_open`, `screen_open_custom`, `screen_close` |
| GadTools | 15 | `gt_init`, `gt_button`, `gt_palette`, `menu_*` |
| ReAction | 16 | `ra_window_*`, `ra_add_*`, `ra_get_*` |
| UI/Dialogos | 6 | `file_open_dialog`, `file_save_dialog` |
| **Total** | **170+** | |

### Colores Estandar Amiga

| Indice | Color Tipico |
|--------|--------------|
| 0 | Fondo (negro/gris) |
| 1 | Texto (blanco) |
| 2 | Resaltado |
| 3 | Sombra |

### Codigos de Tecla Comunes

| Tecla | Codigo |
|-------|--------|
| ESC | 69 |
| RETURN | 68 |
| SPACE | 64 |
| UP | 76 |
| DOWN | 77 |
| LEFT | 79 |
| RIGHT | 78 |

---

## Apendice: Errores Comunes

### Error: Variable no definida
```
# Mal
Print x     # x no existe

# Bien
x = 10
Print x
```

### Error: Falta 'end'
```
# Mal
if x > 0
    Print "positivo"
# Falta end

# Bien
if x > 0
    Print "positivo"
end
```

### Error: Tipo incorrecto
```
# Mal
x = "hola" + 5      # No se puede sumar string + int

# Bien
x = "hola" + "5"    # Concatenar strings
```

---

**Dash Language** - Creado para revivir la magia de programar en Amiga.
