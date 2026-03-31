# Chuleta de Referencia Rápida: Dash
Versión: 2.0

Esta es una guía de referencia rápida ("cheatsheet") para Dash, diseñada para tener a mano todos los comandos y estructuras clave del lenguaje.

## Estructura Global y Control de Flujo

| Palabra Clave | Descripción | Ejemplo de Sintaxis |
| --- | --- | --- |
| `Main` | Punto de entrada principal del programa. | `Main ... end` |
| `EventLoop` | Bucle de escucha para eventos del sistema (OS) o de hardware. | `EventLoop ... end` |
| `if / else` | Estructura condicional básica. | `if condition ... else ... end` |
| `unless` | Condicional inverso (se ejecuta si la condición es falsa). **(pendiente)** | `unless condition ... end` |
| `while` | Bucle que se ejecuta mientras una condición sea verdadera. | `while condition ... end` |
| `for` | Bucle para iterar sobre un rango numérico. | `for i in (1..10) ... end` |
| `for ... in` | Itera sobre los elementos de un array. | `for item in mi_lista ... end` |
| `switch / case` | Permite evaluar múltiples condiciones para una variable. **(pendiente)** | `switch variable ... case valor ... end` |
| `end` | Cierre universal para todos los bloques de código. | (Obligatorio) |
| `Stop` | Finaliza la ejecución del programa o del bucle actual. | `Stop` |
| `break` | Sale inmediatamente de un bucle `while`, `for` o `each`. **(pendiente)** | `break` |
| `next` | Salta a la siguiente iteración de un bucle. **(pendiente)** | `next` |

## Estructuras de Datos

| Estructura | Descripción | Ejemplo de Sintaxis |
| --- | --- | --- |
| Array | Colección ordenada de elementos (sintaxis literal). | `mi_lista = ["rojo", "verde", "azul"]` |
| `Diccionario` | Colección de pares clave-valor. **(pendiente)** | `config = { "ancho" => 320, "alto" => 200 }` |

## Interfaz de Usuario (Modo OS/Workbench)

| Palabra Clave | Función | Atributos Comunes |
| --- | --- | --- |
| `Window` | Define una ventana de Intuition. | `title`, `x`, `y`, `width`, `height` |
| `Screen` | Abre una pantalla personalizada (PAL/NTSC/RTG). | `mode: :hires`, `colors: 32` |
| `Canvas` | Área de dibujo con auto-escalado. **(pendiente)** | `resolution`, `scale`, `grid` |
| `Button` | Gadget de tipo botón. | `text`, `x`, `y` |
| `Menu` | Sistema de menús superiores para una ventana. **(pendiente)** | `Item "Abrir"` |
| `System.request_file` | Abre el selector de archivos nativo de AmigaOS. **(pendiente)** | `title: "Elige...", pattern: "#?.mod"` |

## Bajo Nivel y Hardware (Modo Bare Metal)

| Palabra Clave | Acción | Uso Típico |
| --- | --- | --- |
| `System.takeover` | Apaga AmigaOS para tomar control del hardware. **(pendiente)** | Inicio de un juego o demo. |
| `System.restore` | Devuelve el control al sistema operativo de forma segura. **(pendiente)** | Salida de un juego o demo. |
| `Custom` | Objeto para acceso directo a los registros del chipset. **(pendiente)** | `Custom.color00 = #000` |
| `Copper` | Control del co-procesador de video para efectos de color y pantalla. | `wait_line`, `set_color` |
| `Sprite[0-7]` | Acceso a uno de los 8 sprites de hardware. | `pos x, y`, `attach`, `data` |
| `Blitter` | Acceso al co-procesador para copia rápida de memoria gráfica. | `copy src, dest, size` |
| `wait_vblank` | Sincroniza el código con el refresco de pantalla (Vertical Blank). | Evitar parpadeo (flickering). |

## Sonido y Multimedia

| Palabra Clave | Función | Atributos Comunes |
| --- | --- | --- |
| `gfx_rgb()` | Define colores de la paleta (builtin implementado). | `gfx_rgb(indice, r, g, b)` |
| `Sample` | Carga y gestiona sonidos en formato 8-bit (IFF/8SVX/RAW). **(pendiente)** | `file: "sonido.8svx"` |
| `tone_play` / `music_play` | Reproduce tonos o musica (builtins implementados). | `tone_play(freq, dur, vol)` / `music_play(file)` |
| `Audio.play_raw` | Reproduce una onda de sonido desde memoria. **(pendiente)** | `channel`, `period`, `length` |

## Redes (AmiNet / bsdsocket.library) - **(toda la seccion pendiente)**

| Palabra Clave | Función | Ejemplo |
| --- | --- | --- |
| `Network.init` | Inicializa la pila de red (AmiTCP, Roadshow, etc.). **(pendiente)** | (Automático al usar red) |
| `Http.get` | Realiza una petición HTTP GET a una URL. **(pendiente)** | `Http.get "api.example.com/data"` |
| `Socket` | Permite conexiones TCP/UDP manuales de bajo nivel. **(pendiente)** | `Socket.open ip, port` |
