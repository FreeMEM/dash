# Editor visual de MUI para VS Code (tarea 19 de `docs/MUI_LOOP.md`)

Un "Glade para MUI": se monta la ventana con el ratón (grupos, botones, campos, listas...) dentro de VS Code y el
programa Dash la usa. Encaja con el perfil de desarrollo de AmiCachy (`dev_station`: VS Code + Amiberry, carpeta
`DEV:`; ver `~/Projects/AmiCachy/ARCHITECTURE.md`, sección 5).

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
   los `mui_`, cambia el editor en el mismo commit. Se puede sacar a un repo propio cuando se publique.
5. **Vista previa en dos niveles:**
   - **Inmediata**, en el webview: un dibujo aproximado con HTML/CSS (cajas que se reparten como los grupos de MUI).
   - **Real**: botón "Ver en Amiga" que compila un programa mínimo que importa el `.dashui`, lo ejecuta en FS-UAE
     (`tools/emu_run.py --autoclose --screenshot`) y muestra la captura en el webview (unos 30 s).

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
- **Comandos:** "Dash: Compilar" (`./dash` del fichero activo), "Dash: Ejecutar en emulador" (`tools/emu_run.py`),
  "Dash: Ver en Amiga" (captura de la ventana del `.dashui`). La ruta de Dash, la toolchain y las variables del
  emulador se configuran en los ajustes de la extensión (`dash.path`, `dash.emulator.*`).
- **Resaltado de sintaxis** de `.dash` (gramática TextMate), que hoy no existe.
- Sin dependencias en tiempo de ejecución; para empaquetar, `@vscode/vsce` en un `node_modules` local (no global).

## Plan (tareas 20-24)

- 20: esqueleto de la extensión (resaltado, comandos Compilar y Ejecutar) y `compiler/dashui.py` con `import
  ".dashui"` (con tests de generación sin VS Code).
- 21: editor en el webview (paleta, árbol, propiedades, vista aproximada), guardar y abrir.
- 22: ida y vuelta: abrir un `.dashui` escrito a mano o modificado fuera, y conservar lo que el editor no entiende
  (propiedades desconocidas se guardan tal cual).
- 23: "Ver en Amiga" con la captura.
- 24: la ventana del navegador (`examples/mui_navegador.dash`) rehecha con un `.dashui`; documentación.

## Estado (2026-10-16)

Hecho (tareas 20-24): `compiler/dashui.py` e `import ".dashui"`; extensión en `editor/vscode/` con resaltado de Dash,
comandos Compilar y Ejecutar en emulador, editor visual (paleta, árbol, propiedades, menús, vista aproximada) y "Ver en
Amiga" (captura de la ventana en FS-UAE). Ejemplo: `examples/mui_navegador.dashui` + `examples/mui_navegador_editor.dash`.

Instalar en VS Code: `cd editor/vscode && npm install && npm run package`, luego
`code --install-extension dash-mui-editor-0.1.0.vsix`. No se ha probado dentro de VS Code de verdad: los tests corren
la gramática, el modelo y los comandos en Node, y el webview en Chromium con un `vscode` simulado.

Pendiente: deshacer dentro del propio editor ya lo da VS Code (el texto es suyo), pero no hay copiar/pegar de objetos ni
selección múltiple; la vista aproximada no reparte el espacio exactamente como MUI.
