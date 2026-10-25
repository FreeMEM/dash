# Editor visual de MUI para VS Code (tarea 19 de `docs/MUI_LOOP.md`)

*[English](MUI_EDITOR.en.md) | Castellano*

Un "Glade para MUI": se monta la ventana con el ratón (grupos, botones, campos, listas...) dentro de VS Code y el
programa Dash la usa. Encaja con el perfil de desarrollo de AmiCachy (`dev_station`: VS Code + Amiberry, carpeta
`DEV:`; ver el `ARCHITECTURE.md` de AmiCachy, sección 5).

## Decisiones

1. **Formato propio, `.dashui` (JSON), como el `.ui` de Glade.** El usuario no recuerda el formato que se habló; este
   es el más simple de editar con una herramienta y de leer de vuelta sin perder nada (tarea 22): el fichero es la
   única fuente, no hay código generado que se pueda desincronizar.
2. **El compilador lo entiende directamente:** `import "ventana.dashui"` en un programa Dash. `compiler/main.py`, al
   resolver un import que acaba en `.dashui`, genera el código Dash (`compiler/dashui.py`) y lo compila como un módulo
   más. Ese código usa los builtins `mui_` (docs/MUI_DISEÑO.md); nada nuevo en el runtime.
3. **Lo que genera:** por cada ventana, un `struct` con un campo por objeto con nombre (más `window`) y una función
   `<Ventana>_create()` que la construye (el nombre del struct a secas sería su constructor):

   ```ruby
   # ventana.dashui con una ventana "Principal" y objetos "url", "ir", "pagina"
   import "ventana.dashui"

   Main
       mui_app_begin("Navegador", "NAVEGADOR")
       v = Principal_create()       # crea la ventana y sus objetos; v.url, v.ir, v.pagina...
       mui_on_press(v.ir, 1)
       mui_window_open(v.window)
       ...
   end
   ```

   Los eventos se pueden poner en el `.dashui` (número de evento por objeto) o en el programa, como hoy.
4. **Dónde vive:** carpeta `editor/vscode/` de este repo (extensión `dash-mui-editor`). Va con el lenguaje: si cambian
   los `mui_`, cambia el editor en el mismo commit. Se publica en este repo, como release (`vscode-0.2.1`).
5. **Vista previa en dos niveles:**
   - **Inmediata**, en el webview: un dibujo aproximado con HTML/CSS (cajas que se reparten como los grupos de MUI).
   - **Real**: botón "Ver en Amiga" del editor. Compila un programa mínimo que importa el `.dashui`, lo ejecuta en
     un Amiga emulado que se queda encendido (`tools/emu_preview.py`) y muestra la captura en el webview (unos 2 s;
     al principio era `tools/emu_run.py --screenshot`, unos 30 s). Detalle al final.
     Con la casilla "al cambiar" (`dash.emulator.previewOnChange`), vuelve a pedirla solo 1,2 s después del último
     cambio (una cada vez; las que llegan mientras tanto se juntan en una); si el emulador falla, se apaga sola.

## El formato `.dashui`

```json
{
  "dashui": 1,
  "windows": [
    {
      "name": "Principal",
      "title": "Navegador",
      "id": 1,
      "root": {
        "type": "vgroup",
        "children": [
          { "type": "hgroup", "children": [
              { "type": "button", "name": "atras", "label": "<", "event": 10 },
              { "type": "string", "name": "url", "text": "http://", "max": 1024, "ack": 11 }
          ]},
          { "type": "canvas", "name": "pagina", "min_width": 320, "min_height": 200, "weight": 300 },
          { "type": "text", "name": "estado", "text": "Listo" }
        ]
      },
      "menus": [
        { "title": "Proyecto", "items": [
            { "label": "Salir", "key": "Q", "event": 99 }
        ]}
      ]
    }
  ]
}
```

| `type` | Builtin | Propiedades |
|---|---|---|
| `vgroup`, `hgroup` | `mui_vgroup_begin`/`mui_hgroup_begin` | `children` |
| `frame` | `mui_frame_begin` | `title`, `horizontal`, `children` |
| `columns` | `mui_columns_begin` | `columns`, `children` |
| `tabs` | `mui_register_begin` | `titles` ("A|B"), `children` (una página cada uno), `change` |
| `scroll` | `mui_scroll_begin` | `children` |
| `text`, `label` | `mui_text`, `mui_label` | `text` |
| `button` | `mui_button` | `label`, `event` |
| `string` | `mui_string` | `text`, `max`, `ack`, `change` |
| `checkbox` | `mui_checkbox` | `checked`, `change` |
| `cycle` | `mui_cycle` | `options` ("A|B"), `change` |
| `slider` | `mui_slider` | `min`, `max`, `value`, `change` |
| `gauge` | `mui_gauge` | `max` |
| `list` | `mui_list` | `change`, `double` |
| `canvas` | `mui_canvas` | `min_width`, `min_height` |
| `scrollbar` | `mui_scrollbar` | `vertical`, `change` |
| `image` | `mui_image` | `file` |
| `image_button` | `mui_image_button` | `file`, `event` |
| `space`, `balance` | `mui_space`, `mui_balance` | — |

Comunes: `name` (campo del struct; sin nombre el objeto no se guarda), `weight` (`mui_weight`), `disabled`
(`mui_set_enabled`), `hidden` (`mui_set_visible`), `help` (`mui_help`: ayuda en un globo). En la ventana, `"size": [ancho,
alto]` es su tamaño al abrirse en tanto por ciento de la pantalla (`mui_window_size`). `event`/`change`/`ack`/`double` = número de evento
(`mui_on_press`, `mui_on_change`, `mui_on_ack`, `mui_on_double`). `"dashui": 1` es la versión del formato.

Reglas que comprueba el compilador (`compiler/dashui.py`; el editor marca las mismas):

- **Nombres** de ventana y de objeto: letras sin acentos, cifras y `_`, sin empezar por cifra. No valen las palabras
  del lenguaje (`end`, `if`, `func`...) ni `window` (es el campo de la ventana). Sin repetir en la misma ventana. Un
  objeto solo es un campo del struct de su ventana (`v.descargas`): puede llamarse como una variable global del
  programa o de un módulo sin tocarla (dashweb D72).
- **Números enteros**: `event`, `change`, `ack`, `double`, `weight`, el `id` y el `close` de la ventana y el `event`
  de un menú. `"event": "uno"` o `true` es un error.
- **Textos**: no pueden llevar `#{` (en Dash sería una interpolación).
- **Eventos en cualquier objeto**: `event`, `change`, `ack` y `double` valen en todos los tipos, también en grupos;
  el compilador no los limita por tipo.
- **Ventana**: `"close": N` hace que el botón de cerrar devuelva `N` (`mui_on_close`). Sin él, cerrar la primera
  ventana es -1 (salir).
- **Menús**: cada elemento es `label`, `key` (letra para Amiga+tecla) y `event`, o `{ "separator": true }` (una línea).
- **Traducciones** (dashweb D71): `"tr": N` en un objeto, una ventana, un menú o un elemento de menú da al texto
  principal (`text`, `label`, `title`, `titles`, `options`) el número `N` del catálogo: el código lo pide con
  `tr(N, "texto")`. Para varios textos del mismo objeto, `"tr": { "label": 12, "help": 13 }`. Los saca
  `tools/catalogo.py cd` junto con los del programa (ver "Traducciones" en `docs/MANUAL_REFERENCIA.md`). El editor
  visual los conserva, pero todavía no los enseña ni los cambia: se ponen editando el fichero como texto.

## La extensión

- **Editor propio** (`CustomTextEditorProvider`) para `*.dashui`: el JSON queda en el documento de VS Code (deshacer,
  guardar y control de cambios normales); el webview es la vista.
- **Webview:** paleta de objetos a la izquierda, árbol de la ventana en el centro, propiedades del objeto elegido a
  la derecha, vista previa aproximada debajo. Pestañas por ventana y lista de menús. Arrastrar desde la paleta, el
  árbol o la vista: delante, detrás o dentro de un grupo, según dónde se suelte. Teclado en el árbol: flechas,
  Alt+flechas para mover, Supr, F2 (nombre), Intro (propiedades), Ctrl+D (duplicar); copiar, cortar y pegar
  (los nombres repetidos llevan un número); deshacer y rehacer, los del documento (y botones ↶ ↷).
- **Problemas y código:** los problemas del `.dashui` (JSON, tipos, nombres, números de evento) salen en Problemas en su
  línea. El botón → de un evento lleva a su código en el `.dash` que importa el fichero: una constante con ese número
  (`const ID_ACEPTAR = 3`) y `if ev == ID_ACEPTAR`; si no lo hay, lo crea (la constante y un `if` en el bucle de
  `mui_wait_event`).
- **Comandos** (`editor/vscode/package.json`): "Dash: Compilar", "Ejecutar en emulador", "Ejecutar con comprobación
  de memoria", "Ejecutar con perfil", "Depurar en el Amiga", "Preparar para un Amiga real", "Elegir la máquina del
  emulador", "Nuevo proyecto", "Nuevo fichero de ventanas MUI (.dashui)", "Elegir la carpeta del compilador" y
  "Reiniciar el servidor de lenguaje". "Ir al código del evento" (el botón →) y "Nueva línea (con end)" (la tecla
  Intro) no salen en la paleta de comandos. "Ver en Amiga" no es un comando: es un botón del editor visual. La ruta de Dash y las variables del emulador van en los ajustes (`dash.path`, `dash.emulator.*`).
- **Resaltado de sintaxis** de `.dash` (gramática TextMate, `syntaxes/dash.tmLanguage.json`, generada con
  `tools/gen_tmgrammar.py`).
- **Comportamiento del editor:**
  - Se activa al abrir una carpeta que tiene algún `.dashui` (`workspaceContains:**/*.dashui`), además de al abrir
    un `.dash` o un `.dashui`.
  - Un `.dashui` que se da a VS Code al arrancar (`code carpeta ventana.dashui`) se abre en el editor visual, no
    como texto JSON.
  - En un panel estrecho (el editor al lado del `.dash`, media pantalla) las propiedades pasan debajo del resto.
  - Usa los colores del tema de VS Code.
- Una dependencia en tiempo de ejecución, `vscode-languageclient` (el cliente del servidor de lenguaje, va dentro
  del paquete con esbuild). Para empaquetar, `@vscode/vsce` en un `node_modules` local (no global).

## Plan (tareas 20-24)

- 20: esqueleto de la extensión (resaltado, comandos Compilar y Ejecutar) y `compiler/dashui.py` con `import
  ".dashui"` (con tests de generación sin VS Code).
- 21: editor en el webview (paleta, árbol, propiedades, vista aproximada), guardar y abrir.
- 22: ida y vuelta: abrir un `.dashui` escrito a mano o modificado fuera, y conservar lo que el editor no entiende
  (propiedades desconocidas se guardan tal cual).
- 23: "Ver en Amiga" con la captura.
- 24: la ventana del navegador (`examples/mui_navegador.dash`) rehecha con un `.dashui`; documentación.

## Estado

Hecho (tareas 20-24): `compiler/dashui.py` e `import ".dashui"`; extensión en `editor/vscode/` con resaltado de Dash,
comandos, editor visual (paleta, árbol, propiedades, menús, vista aproximada) y "Ver en Amiga". Ejemplo:
`examples/mui_navegador.dashui` + `examples/mui_navegador_editor.dash`. Después, el IDE (`docs/IDE_LOOP.md`):
servidor de lenguaje, depurador, copiar y pegar en el árbol.

Publicada en este repo: release [vscode-0.2.1](https://github.com/FreeMEM/dash/releases/tag/vscode-0.2.1) (PR #11),
con `dash-mui-editor-0.2.1.vsix`. Se instala con "Extensions: Install from VSIX..." (VS Code 1.86 o posterior); ver
`docs/INSTALACION.md`, paso 9. Lo hecho después (la casilla "al cambiar", el resaltado de los builtins nuevos) está
en `main` y en la sección "Unreleased" de `editor/vscode/CHANGELOG.md`, aún sin release.

Pendiente: no hay selección múltiple; la vista aproximada no reparte el espacio exactamente como MUI.

## Ver en Amiga (IDE, tarea 20)

Un Amiga emulado que se queda encendido entre vistas (se apaga tras 10 minutos sin usarlo):
`tools/emu_preview.py --machine a1200|a1200-32|rtg`. Con la máquina A500 la vista va al A1200 (MUI 5 pide 68020). Dentro, un
vigía espera `DH0:pide` y ejecuta `DH0:vista`, que abre la ventana, hace su propia captura con `C:dash_shot` en cuanto
está abierta y acaba. En pantallas planares la captura son los planos tal cual (`.dsh`, unos 40 KB en 4 colores) y el
PC hace el PNG (`emu_run.planar_to_png`). La extensión mantiene uno por máquina y no recompila una ventana que no ha
cambiado. Medido: arranque 2,5 s (A1200 3.1), 5 s (3.2) y 1,7 s (68040 RTG); cada vista, 2,4 s, 2,5 s y 1,8 s (antes,
unos 30 s cada una).

