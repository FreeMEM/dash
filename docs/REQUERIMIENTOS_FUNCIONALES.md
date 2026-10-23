# Requisitos Funcionales de Dash
Versión: 2.0

> **Aviso:** estos son los requisitos originales del proyecto, no el estado actual. Lo que Dash hace hoy está en
> `ROADMAP.md`, `QUICK_REFERENCE.md` y `BUILTINS.md`. Lo que cambió: los programas piden AmigaOS 3.0 o superior
> (no 2.0) y funcionan en un 68000; no hay versión PPC; el gcc de bebbo genera Hunk directamente, sin `elf2hunk`.

Este documento detalla los requisitos funcionales para el lenguaje de programación Dash.

## RF1: Módulo de Sistema (Workbench/OS)
El lenguaje debe proporcionar una capa de abstracción de alto nivel para interactuar con el entorno de escritorio de AmigaOS.

- **RF1.1: Gestión de Librerías:** Apertura y cierre automático de librerías críticas como `intuition.library` y `graphics.library` sin intervención del programador.
- **RF1.2: Creación de Ventanas:** Soporte para la creación y gestión de ventanas de Intuition a través de un comando simple como `Window.open`.
- **RF1.3: Soporte de Gadgets:** Capacidad para definir y manejar gadgets estándar de AmigaOS, incluyendo `Button`, `Slider`, `Checkbox`, `String`, `ListView` y `Menu`.
- **RF1.4: Selector de Archivos:** Integración con la `asl.library` para permitir la selección de archivos mediante un comando como `System.request_file`.

## RF2: Módulo Bare Metal (Acceso Directo al Hardware)
Dash debe permitir a los desarrolladores tomar control total de la máquina para la creación de juegos y demos de alto rendimiento.

- **RF2.1: Control del Sistema:** Implementación de `System.takeover` para apagar de forma segura el sistema operativo y `System.restore` para devolver el control al Workbench.
- **RF2.2: Acceso a Registros:** Acceso directo a los registros del chipset Custom (Agnus, Denise, Paula) a través de un objeto global `Custom`, permitiendo la manipulación directa de hardware (e.g., `Custom.color00 = #F00`).
- **RF2.3: Control del Copper:** Sintaxis declarativa para generar `Copper lists`, permitiendo efectos de video que cambian en sincronía con el barrido de pantalla.
- **RF2.4: Sprites de Hardware:** Gestión completa de los 8 sprites de hardware nativos del Amiga, incluyendo su posición, datos de imagen y adjuntado (`attach`) para aumentar el número de colores.

## RF3: Sonido y Redes
El lenguaje debe incluir funcionalidades para multimedia y conectividad.

- **RF3.1: Reproducción de Módulos:** Motor de audio capaz de reproducir archivos de tracker (formato `.mod`) de manera asíncrona, utilizando la `ptplay.library` o una rutina interna.
- **RF3.2: Reproducción de Samples:** Soporte para cargar y reproducir sonidos (`.8svx` o `RAW`).
- **RF3.3: Conectividad de Red:** Acceso a la red con `bsdsocket.library` (cualquier pila: Roadshow, AmiTCP, MiamiDx), sin
  esconder el control al programa. Hoy hay: TCP como cliente (`net_connect`, también por pasos sin bloquear:
  `net_connect_start`/`net_connect_poll`) y como servidor (`net_listen`, `net_accept`); UDP con difusión
  (`net_udp_*`); TLS con AmiSSL que comprueba el certificado (`tls_*`, también por pasos y reanudando sesiones);
  `net_signal` para despertar el bucle de eventos con la red; la red en una tarea aparte (`task_start`); y
  consultas a la pila y a los drivers: interfaces de Roadshow con su estado y bytes, drivers SANA-II en uso con
  sus paquetes, bytes y la señal WiFi. HTTP no es un builtin: cada programa lo hace sobre TCP y TLS (Tachyon,
  `lib/http.dash`). Lo que falta: sockets raw (ICMP para un ping) y tramas en crudo del driver SANA-II (leer y
  escribir paquetes de cualquier protocolo); hoy, con `@native`. Detalle en `docs/MANUAL_REFERENCIA.md` ("Red").

## RF4: Gestión de Seguridad y Robustez (Safety Injections)
Para mejorar la estabilidad y evitar `Guru Meditations`, el transpilador de Dash inyectará código de seguridad de forma automática.

- **RF4.1: Verificación de Nulos (Null-Check):** Antes de utilizar cualquier puntero a ventana o librería, se verificará que no sea nulo.
- **RF4.2: Protección de Pila (Stack Protection):** El sistema calculará y definirá automáticamente un tamaño de pila adecuado para el programa, previniendo desbordamientos.
- **RF4.3: Guardia de Memoria (Memory Guard):** Se rastrearán todas las reservas de memoria para asegurar que se liberen correctamente al finalizar el programa, evitando fugas de memoria.
- **RF4.4: Verificación de Límites (Bounds Checking):** Se insertarán comprobaciones en accesos a arrays y operaciones de dibujo para asegurar que no se escriba fuera de los límites de memoria asignados.
