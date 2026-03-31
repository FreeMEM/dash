# Chuleta de Referencia Rápida: Dash
Versión: 2.0

Esta es una guía de referencia rápida ("cheatsheet") para Dash, diseñada para tener a mano todos los comandos y estructuras clave del lenguaje.

## Estructura Global y Control de Flujo

| Palabra Clave | Descripción | Ejemplo de Sintaxis |
| --- | --- | --- |
| `Main` | Punto de entrada principal del programa. | `Main ... end` |
| `EventLoop` | Bucle de escucha para eventos del sistema (OS) o de hardware. | `EventLoop ... end` |
| `if / else` | Estructura condicional básica. | `if condition ... else ... end` |
| `unless` | Condicional inverso (se ejecuta si la condición es falsa). | `unless condition ... end` |
| `while` | Bucle que se ejecuta mientras una condición sea verdadera. | `while condition ... end` |
| `for` | Bucle para iterar sobre un rango numérico. | `for i in (1..10) ... end` |
| `each` | Itera sobre los elementos de una Lista o Diccionario. | `mi_lista.each do \|item\| ... end` |
| `switch / case` | Permite evaluar múltiples condiciones para una variable. | `switch variable ... case valor ... end` |
| `end` | Cierre universal para todos los bloques de código. | (Obligatorio) |
| `Stop` | Finaliza la ejecución del programa o del bucle actual. | `Stop` |
| `break` | Sale inmediatamente de un bucle `while`, `for` o `each`. | `break` |
| `next` | Salta a la siguiente iteración de un bucle. | `next` |

## Estructuras de Datos

| Estructura | Descripción | Ejemplo de Sintaxis |
| --- | --- | --- |
| `Lista` | Colección ordenada de elementos. | `mi_lista = ["rojo", "verde", "azul"]` |
| `Diccionario` | Colección de pares clave-valor. | `config = { "ancho" => 320, "alto" => 200 }` |

## Interfaz de Usuario (Modo OS/Workbench)

| Palabra Clave | Función | Atributos Comunes |
| --- | --- | --- |
| `Window` | Define una ventana de Intuition. | `title`, `x`, `y`, `width`, `height` |
| `Screen` | Abre una pantalla personalizada (PAL/NTSC/RTG). | `mode: :hires`, `colors: 32` |
| `Canvas` | Área de dibujo con auto-escalado. | `resolution`, `scale`, `grid` |
| `Button` | Gadget de tipo botón. | `text`, `x`, `y` |
| `Menu` | Sistema de menús superiores para una ventana. | `Item "Abrir"` |
| `System.request_file` | Abre el selector de archivos nativo de AmigaOS. | `title: "Elige...", pattern: "#?.mod"` |

## Bajo Nivel y Hardware (Modo Bare Metal)

| Palabra Clave | Acción | Uso Típico |
| --- | --- | --- |
| `System.takeover` | Apaga AmigaOS para tomar control del hardware. | Inicio de un juego o demo. |
| `System.restore` | Devuelve el control al sistema operativo de forma segura. | Salida de un juego o demo. |
| `Custom` | Objeto para acceso directo a los registros del chipset. | `Custom.color00 = #000` |
| `Copper` | Control del co-procesador de video para efectos de color y pantalla. | `wait_line`, `set_color` |
| `Sprite[0-7]` | Acceso a uno de los 8 sprites de hardware. | `pos x, y`, `attach`, `data` |
| `Blitter` | Acceso al co-procesador para copia rápida de memoria gráfica. | `copy src, dest, size` |
| `wait_vblank` | Sincroniza el código con el refresco de pantalla (Vertical Blank). | Evitar parpadeo (flickering). |

## Sonido y Multimedia

| Palabra Clave | Función | Atributos Comunes |
| --- | --- | --- |
| `Palette` | Define la paleta de colores. | `index: 1`, `color: #F00` |
| `Sample` | Carga y gestiona sonidos en formato 8-bit (IFF/8SVX/RAW). | `file: "sonido.8svx"` |
| `Tracker.load` | Carga un módulo de música Protracker (`.mod`). | `file: "musica.mod", :chip` |
| `Tracker.play` | Reproduce el módulo cargado. | |
| `Tracker.stop` | Detiene la reproducción del módulo. | |
| `Audio.play_raw` | Reproduce una onda de sonido desde memoria. | `channel`, `period`, `length` |

## Redes (AmiNet / bsdsocket.library)

| Palabra Clave | Función | Ejemplo |
| --- | --- | --- |
| `Network.init` | Inicializa la pila de red (AmiTCP, Roadshow, etc.). | (Automático al usar red) |
| `Http.get` | Realiza una petición HTTP GET a una URL. | `Http.get "api.example.com/data"` |
| `Socket` | Permite conexiones TCP/UDP manuales de bajo nivel. | `Socket.open ip, port` |
