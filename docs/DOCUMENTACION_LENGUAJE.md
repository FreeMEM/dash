# Documentación Oficial de D.A.S.H.
Versión 2.0

## 1. Filosofía y Visión
**D.A.S.H.** (*Development Amiga Synthesis Hub*) es un lenguaje de programación de alto nivel diseñado para el desarrollo en la plataforma **Commodore Amiga**, pero desde la comodidad de un entorno de desarrollo moderno.

El objetivo principal es "liberar la mente" del programador de las complejidades del lenguaje C y Ensamblador, eliminando la gestión manual de memoria, los errores de punteros y otras dificultades comunes en el desarrollo retro. Dash combina la elegancia sintáctica de lenguajes como Ruby y Python con la capacidad de generar código nativo, rápido y optimizado para el hardware del Amiga.

El acrónimo D.A.S.H. refleja la esencia del proyecto:
- **D**evelopment — Una herramienta pura de creación.
- **A**miga — El ecosistema de los 80/90 que queremos revitalizar.
- **S**ynthesis — No es solo programar, es sintetizar una aplicación (interfaz, lógica y recursos) de forma automática y rápida.
- **H**ub — El centro de operaciones que conecta tu entorno moderno (VS Code en 2026) con el hardware real o emulado.

Además, la palabra *Dash* en inglés evoca velocidad instantánea y trazo rápido, capturando la filosofía de desarrollo ágil del lenguaje.

## 2. Arquitectura de Desarrollo Cruzado
Dash utiliza un modelo de **transpilación cruzada**. Esto significa que el código `.dash` que escribes en tu PC (Linux, macOS o Windows) no es interpretado en el Amiga, sino que se traduce a código C optimizado, el cual luego se compila para generar un binario nativo de Amiga (m68k).

El flujo de trabajo es el siguiente:
1.  **Frontend (Python)**: Un transpilador escrito en Python (usando Lark) analiza tu código `.dash`.
2.  **Generación de C**: El AST se transforma en código C optimizado para AmigaOS.
3.  **Backend (GCC Toolchain)**: Se utiliza `m68k-amigaos-gcc` para compilar el código C generado.
4.  **Runtime**: El resultado es un binario nativo AmigaOS en formato Hunk.

## 3. Compilando tu Código

```bash
./dash <archivo.dash> -o <ejecutable>
```

**Ejemplo:**
```bash
./dash examples/hola.dash -o bin/hola
```

Esto:
1. Transpila `hola.dash` a C (en `build/hola.c`)
2. Compila el C a ejecutable Amiga (en `bin/hola`)

### Opciones del CLI

| Opción | Descripción |
|--------|-------------|
| `-o FILE` | Archivo de salida (requerido) |
| `--no-hunk` | No convertir a formato Hunk (mantener ELF) |

## 4. Sintaxis del Lenguaje (Implementado)

### 4.1 Estructura de un Programa

Todo programa Dash tiene esta estructura básica:

```ruby
# Definiciones de ventanas (opcional)
Window NombreVentana
  title "Título"
  width 320
  height 200
end

# Punto de entrada principal (obligatorio)
Main
  # instrucciones
end
```

### 4.2 Comandos Disponibles

| Comando | Descripción | Ejemplo |
|---------|-------------|---------|
| `Window` | Define una ventana de Intuition | `Window App ... end` |
| `Main` | Punto de entrada del programa | `Main ... end` |
| `Print` | Imprime texto en consola | `Print "Hola"` |
| `Wait` | Pausa N segundos | `Wait 5` |
| `EventLoop` | Bucle de eventos IDCMP | `EventLoop ... end` |
| `On Close` | Maneja cierre de ventana | `On Close ... end` |
| `Stop` | Termina el programa/bucle | `Stop` |
| `#` | Comentario | `# esto es un comentario` |

### 4.3 Propiedades de Window

| Propiedad | Descripción | Ejemplo |
|-----------|-------------|---------|
| `title` | Título de la ventana | `title "Mi App"` |
| `width` | Ancho en píxeles | `width 320` |
| `height` | Alto en píxeles | `height 200` |

### 4.4 Abrir una Ventana

Para abrir una ventana definida, usa `NombreVentana.open` dentro de `Main`:

```ruby
Window MiVentana
  title "Hola Dash"
  width 400
  height 150
end

Main
  MiVentana.open
  Wait 3
end
```

## 5. Ejemplos Funcionales

### 5.1 Hola Mundo con Ventana

```ruby
# examples/hola.dash
Window MiVentana
  title "Hola Dash"
  width 400
  height 150
end

Main
  Print "Starting Dash..."
  MiVentana.open
  Print "Window opened."
  Wait 5
  Print "Closing..."
end
```

### 5.2 Ventana con Event Loop

```ruby
# examples/event_loop_test.dash
Window MyWindow
  title "Event Loop Test"
  width 400
  height 100
end

Main
  Print "Opening window..."
  MyWindow.open

  EventLoop
    On Close
      Print "Close clicked. Exiting."
      Stop
    end
  end

  Print "Program finished."
end
```

## 6. Características de Seguridad (Implementadas)

El código C generado incluye automáticamente:

- **Apertura segura de librerías**: `intuition.library` y `dos.library` se abren con verificación de errores.
- **Null-Check en ventanas**: Se verifica que la ventana se abra correctamente antes de usarla.
- **Limpieza automática**: Las librerías se cierran al salir del programa.
- **Manejo de IDCMP**: El EventLoop gestiona correctamente los mensajes de Intuition.

## 7. Funcionalidades Futuras

> **Nota:** Para ver todo lo implementado, consulta el Manual de Referencia y la API de Amiga. Flow ya incluye control de flujo completo (if/else, while, for), funciones, arrays, strings, structs, enums, imports, FFI, screens, GadTools, ReAction y 161 funciones built-in de Amiga (graphics, sprites, copper, blitter, audio, input, gadgets, etc.).

Las siguientes funcionalidades están planificadas pero **aún no implementadas**:

### 7.1 Control de Flujo Adicional
- `unless / end` - Condicional inverso
- `switch / case` - Selección múltiple
- `break` / `next` - Control dentro de bucles

### 7.2 Estructuras de Datos
- Diccionarios (key-value maps)

### 7.3 Módulo Bare Metal
- `System.takeover` / `System.restore` - Apagado del OS para control total del hardware

### 7.4 Redes
- Soporte de `bsdsocket.library` - Network / HTTP

### 7.5 Gestión de Memoria
- Garbage collection / limpieza automática de memoria

### 7.6 Herramientas
- `install_dash.py` - Script de instalación

## 8. Código C Generado

Para entender qué genera Dash, aquí un ejemplo del C producido:

**Entrada Dash:**
```ruby
Window Test
  title "Test"
  width 320
  height 200
end

Main
  Test.open
  Wait 2
end
```

**Salida C (simplificada):**
```c
/* Generated by Dash Language Compiler */
#include <proto/exec.h>
#include <proto/intuition.h>
#include <proto/dos.h>

struct Window *win_Test = NULL;

int main() {
    IntuitionBase = (struct IntuitionBase *)OpenLibrary("intuition.library", 37);
    DOSBase = (struct DosLibrary *)OpenLibrary("dos.library", 37);

    if (!IntuitionBase || !DOSBase) {
        // cleanup and exit
        return 10;
    }

    win_Test = OpenWindowTags(NULL,
        WA_Width, 320, WA_Height, 200,
        WA_Title, (ULONG)"Test",
        WA_CloseGadget, TRUE,
        WA_IDCMP, IDCMP_CLOSEWINDOW,
        TAG_DONE);

    if (!win_Test) {
        // cleanup and exit
        return 20;
    }

    Delay(2 * 50);

    CloseLibrary((struct Library *)DOSBase);
    CloseLibrary((struct Library *)IntuitionBase);
    return 0;
}
```
