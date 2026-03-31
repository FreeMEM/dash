# Especificación Técnica: Dash
"High-Level Elegance, Low-Level Power"

Autor: FreeMEM

Plataforma Host: Sistemas Modernos (Linux, macOS, Windows)

Plataforma Target: Commodore Amiga (M68k / PPC)

Estado: Fase de Arquitectura 2.0

## 1. Filosofía del Proyecto

Dash nace de la necesidad de programar para el Amiga utilizando paradigmas de desarrollo actuales. Mientras que C es propenso a errores de punteros y ASM es lento de escribir, Dash ofrece una sintaxis inspirada en Ruby/Python que se transpila a C optimizado y seguro.

El nombre "Dash" representa el estado mental de fluidez que el programador experimenta cuando puede concentrarse en la lógica de su programa sin fricciones técnicas.

## 2. Arquitectura de Desarrollo Cruzado (Cross-Development)

El flujo de trabajo está optimizado para que el desarrollador nunca tenga que salir de su entorno moderno hasta que el binario esté listo.

- **Frontend:** Transpilador escrito en Python que valida la sintaxis `.dash`.
- **Middle-end:** Inyector de seguridad (Bounds checking y Memory management).
- **Backend:** Cadena de herramientas GCC (BlitterStudio/m68k-amigaos-gcc).
- **Runtime:** Binario nativo ligero sin dependencias externas pesadas.

## 3. Especificaciones del Lenguaje

### 3.1 Estructuras de Control y Lógica

| Comando | Descripción |
|---------|-------------|
| `Main ... end` | Define el punto de entrada del programa. |
| `if / unless` | Condicionales (estilo Ruby). |
| `while / for / each` | Bucles de iteración y rangos. |
| `EventLoop` | Gestión nativa de mensajes de Intuition (IDCMP). |

### 3.2 Tipado Dinámico Inteligente

Dash detecta el tamaño necesario para los datos para optimizar la memoria:

- **Byte (8-bit):** Para valores 0…255.
- **Word (16-bit):** Para coordenadas de pantalla y contadores cortos.
- **Long (32-bit):** Para direcciones de memoria y punteros.
- **String:** Gestión automática de STRPTR con terminación nula.

### 3.3 Estructuras de Datos Modernas

- **Listas:** `mi_lista = ["Sprite1", "Sprite2"]` (Traducido a Arrays o Listas Exec).
- **Diccionarios:** `config = { "vol" => 64 }` (Traducido a tablas de búsqueda rápidas).

## 4. Requisitos Funcionales (Roadmap)

### RF1: Módulo de Sistema (Workbench/OS)
- Apertura automática de intuition.library y graphics.library.
- Creación de ventanas con Window.open.
- Soporte para Gadgets (Botones, Sliders, Checkboxes).
- Soporte para selectores de archivos ASL.

### RF2: Módulo Bare Metal (Hardware Directo)
- `System.takeover`: Apagado seguro del OS para juegos/demos.
- `Custom`: Acceso directo a registros de hardware ($DFF000).
- `Copper`: Creación de listas de instrucciones para el coprocesador de video.
- `Sprite[0-7]`: Control total de los 8 canales de sprites de hardware.

### RF3: Sonido y Redes
- `Tracker`: Motor de reproducción de archivos .mod.
- `Network`: Abstracción de bsdsocket.library para peticiones HTTP.

## 5. Gestión de Seguridad (Safety Injections)

Para evitar el Guru Meditation, el transpilador inyecta:

- **Null-Check:** Verifica cada ventana o librería antes de usarla.
- **Stack Protection:** Define automáticamente el tamaño de pila para evitar colapsos.
- **Memory Guard:** Rastrea las reservas de memoria para liberarlas al cerrar el programa (evita "leaks" de memoria).

## 6. Ejemplo de Código

```ruby
# Un reproductor simple en Dash

Window Player
  title "Dash Player"
  width 320, height 100
end

Main
  app = Player.open
  song = Tracker.load "music/stardust.mod", :chip

  EventLoop
    On Close
      song.stop
      Stop
    end

    On Key("p")
      song.play
    end
  end
end
```

## 7. Próximos Pasos Técnicos

1. Finalizar el Transpilador Python (Lark-based).
2. Crear el archivo `dash_core.h` (Wrappers de C para las funciones de Amiga).
3. Implementar el CLI `dash` para compilar con un solo comando: `dash build juego.dash`.
