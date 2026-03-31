# Especificación Técnica: Dash
"High-Level Elegance, Low-Level Power"

Autor: FreeMEM

Plataforma Host: Sistemas Modernos (Linux, macOS, Windows)

Plataforma Target: Commodore Amiga (M68k / PPC)

Estado: Fase de Desarrollo Activo (29 tests pasando)

## 1. Filosofía del Proyecto

Dash nace de la necesidad de programar para el Amiga utilizando paradigmas de desarrollo actuales. Mientras que C es propenso a errores de punteros y ASM es lento de escribir, Dash ofrece una sintaxis inspirada en Ruby/Python que se transpila a C optimizado y seguro.

**D.A.S.H.** significa *Development Amiga Synthesis Hub* — el centro de operaciones que conecta un entorno de desarrollo moderno con el ecosistema Amiga.

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

Dash infiere los tipos automáticamente en la primera asignación:

- **LONG (32-bit):** Todos los valores enteros y punteros.
- **STRPTR:** Cadenas de texto con terminación nula.
- **BOOL:** Valores booleanos (`true`/`false`).

### 3.3 Estructuras de Datos Modernas

- **Arrays:** `numeros = [1, 2, 3]` (Traducido a runtime DashArrayLong con bounds checking).
  - Acceso: `numeros[0]`, asignación: `numeros[2] = 100`, longitud: `numeros.length`
- **Diccionarios:** No implementado (planificado para fases futuras).

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
# Aplicación Dash con ventana y arrays

Window MiApp
    title "Dash Demo"
    width 320
    height 200
end

func factorial(n)
    if n <= 1
        return 1
    end
    return n * factorial(n - 1)
end

Main
    MiApp.open

    nombres = ["Amiga", "Dash", "Flow"]
    for nombre in nombres
        Print nombre
    end

    resultado = factorial(5)
    Print resultado

    EventLoop
        On Close
            Print "Cerrando"
            Stop
        end
    end
end
```

## 7. Próximos Pasos Técnicos

1. Implementar `unless` y `switch/case` como estructuras de control adicionales.
2. Añadir diccionarios como estructura de datos nativa.
3. Expandir módulos Amiga built-in (Graphics, DOS, Input de alto nivel).
4. Soporte de red via abstracción de `bsdsocket.library`.
5. Garbage collection o gestión automática de memoria con helpers.
