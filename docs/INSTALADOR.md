# Documentación del Instalador de Dash
Versión: 2.0

Este documento describe el funcionamiento y las responsabilidades del script de instalación de Dash, `install_dash.py`.

## Visión General
El objetivo de `install_dash.py` es simplificar y automatizar la configuración del entorno de desarrollo de Dash. El script está diseñado para ejecutarse en sistemas operativos modernos (Linux, macOS, Windows con WSL) y asegurar que todas las dependencias y herramientas necesarias estén correctamente instaladas y accesibles.

## Funcionalidades del Instalador

El script `install_dash.py` realizará las siguientes acciones cuando sea ejecutado:

1.  **Verificación del Entorno Python:**
    -   Comprobará que `Python 3` (versión 3.10 o superior) está instalado y disponible en el `PATH` del sistema.
    -   Si no se encuentra una versión compatible, el script notificará al usuario y terminará la instalación.

2.  **Gestión de Dependencias de Python:**
    -   Verificará si la librería `lark` está instalada en el entorno de Python.
    -   Si la librería no está presente, intentará instalarla automáticamente usando `pip`.

3.  **Verificación del Cross-Compiler:**
    -   Buscará en el `PATH` del sistema la existencia del compilador cruzado para Amiga.
    -   Específicamente, buscará `m68k-amigaos-gcc`.
    -   Si no lo encuentra, mostrará un mensaje de advertencia indicando que la compilación no será posible y proporcionará un enlace a las [instrucciones de instalación de la toolchain](https://github.com/BlitterStudio/m68k-amigaos-gcc).

4.  **Creación de la Estructura de Directorios:**
    -   Creará un directorio de configuración y soporte en la carpeta de inicio del usuario: `~/.dash/`.
    -   Dentro de este directorio, creará una subcarpeta `libs/` destinada a albergar futuras librerías estándar y componentes del core de Dash.

## Uso
El script se ejecutará desde la terminal de la siguiente manera:
```bash
python3 install_dash.py
```
El instalador proporcionará información de estado a medida que completa cada paso del proceso.

## Estado Actual
Este script es parte del roadmap de desarrollo y todavía no está implementado. La configuración del entorno debe realizarse manualmente, tal como se describe en el documento `INSTALACION.md`.
