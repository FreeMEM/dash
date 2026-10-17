# MUI en Dash: diseño (tarea 2 de `docs/MUI_LOOP.md`)

## Decisiones

1. **Builtins `mui_`**, sin sintaxis nueva por ahora. Los objetos MUI son valores que el programa
   guarda en variables (números, como los buffers y ficheros de Dash: el codegen convierte a puntero al llamar
   al runtime; tarea 3): hacen falta varias ventanas y muchos objetos (el navegador), cosa que la API de
   ReAction (`ra_`, un estado global y gadgets por número) no permite.
2. **El árbol se construye con una pila**, como `ra_layout_*`: `mui_vgroup_begin()` ... `mui_group_end()`.
   Cada objeto que se crea entra en el grupo abierto. Por dentro: cada grupo se crea vacío y los hijos se añaden
   con `OM_ADDMEMBER`; `mui_window_end()` crea la ventana con su grupo raíz y la añade a la aplicación.
3. **Eventos por número**, como `ra_wait_event`: `mui_on_press(boton, ID_ATRAS)` monta un `MUIM_Notify` que
   devuelve `ID_ATRAS` con `MUIV_Application_ReturnID`. `mui_wait_event()` espera y lo devuelve. -1 = salir.
4. **Zona de dibujo propia** con una clase MUI hecha en el runtime y una función Dash (`Func`) que pinta con
   los builtins `gfx_`. Es la pieza del navegador.
5. **Sintaxis declarativa: después**, como capa encima de estos builtins y como formato del editor visual
   (tarea 19). El usuario no recuerda el formato que se habló; la propuesta es que el editor lea y escriba un
   bloque Dash (`MuiWindow ... end`), sin fichero aparte. Se decide en la tarea 19, con los builtins ya probados.

## API

Tipos: objeto MUI = número (handle, como un buffer); `Int`; `String`. Los textos que MUI no copia (títulos de aplicación, ventana,
menús, ciclos, pestañas) los copia el runtime en su pool, y viven hasta `mui_app_end()`.

### Aplicación y ventanas

| Builtin | Qué hace |
|---|---|
| `mui_app_begin(titulo, base)` | Abre muimaster (versión 19+), comprueba 68020 y crea la aplicación (`base`: nombre ARexx, en mayúsculas). |
| `mui_window_begin(titulo, id)` | Empieza una ventana. `id` (1-255, 0 = ninguno) hace que MUI recuerde su tamaño y posición. Abre su grupo raíz vertical. |
| `mui_window_end()` | Cierra el grupo raíz, crea la ventana y la añade a la aplicación. |
| `mui_window_open(win) -> Bool` | Abre la ventana (false si no se pudo: pantalla pequeña, sin memoria). |
| `mui_window_close(win)` | La cierra (sigue existiendo). |
| `mui_app_end()` | `MUI_DisposeObject` de la aplicación (y todo su árbol), cierra muimaster, libera los textos. Se llama solo al salir si el programa no lo hace. |

### Grupos y disposición

| Builtin | Qué hace |
|---|---|
| `mui_vgroup_begin()`, `mui_hgroup_begin()` | Grupo vertical u horizontal. |
| `mui_group_begin_frame(titulo, horizontal)` | Grupo con marco y título. |
| `mui_columns_begin(n)` | Grupo en rejilla de `n` columnas (formularios con etiqueta + campo). |
| `mui_group_end()` | Cierra el grupo abierto. |
| `mui_space()`, `mui_hspace()`, `mui_vspace()` | Espacio que se estira. |
| `mui_balance()` | Separador que el usuario arrastra (`Balance`). |
| `mui_weight(obj, peso)` | Peso al repartir el espacio (100 por defecto). |
| `mui_register_begin(titulos)` | Pestañas (`Register`); `titulos` = textos separados por `|`. Cada hijo es una página. |

### Objetos

| Builtin | Clase MUI |
|---|---|
| `mui_text(texto)` | `Text` (admite los códigos de formato de MUI, `\33c` centrado...) |
| `mui_label(texto)` | `Label` (alineada para formularios) |
| `mui_button(texto)` | `SimpleButton` (`_` antes de una letra = atajo de teclado) |
| `mui_string(inicial, max)` | `String` |
| `mui_checkbox(marcado)` | `CheckMark` |
| `mui_cycle(opciones)` | `Cycle` (`"Uno|Dos|Tres"`) |
| `mui_slider(min, max, valor)` | `Slider` |
| `mui_gauge(max)` | `Gauge` horizontal (barra de progreso) |
| `mui_list()` | `Listview` + `List` de textos (el objeto devuelto es el `Listview`; el runtime usa su `List`) |
| `mui_scrollbar(vertical)` | `Scrollbar` (`Prop`) |
| `mui_canvas(ancho_min, alto_min)` | Clase propia de dibujo (abajo) |
| `mui_image(fichero)` | `Dtpic` (PNG, JPEG, GIF por datatypes) |

### Valores

| Builtin | Qué hace |
|---|---|
| `mui_get_text(obj) -> String` | Texto de `String` o `Text` (copia nueva para Dash). |
| `mui_set_text(obj, texto)` | Cambia el texto (`String`, `Text`, botón; ventana: título copiado). |
| `mui_get_value(obj) -> Int` | Según la clase: marcado, nivel del deslizador, opción del ciclo, valor de la barra, línea activa de la lista (-1 = ninguna), pestaña, posición de la barra de desplazamiento. |
| `mui_set_value(obj, v)` | Lo mismo para escribir. Dispara las notificaciones como si lo hiciera el usuario. |
| `mui_set_enabled(obj, si)` | `MUIA_Disabled`. |
| `mui_set_visible(obj, si)` | `MUIA_ShowMe` (la ventana se recoloca). |
| `mui_set_range(barra, total, visible)` | Barra de desplazamiento: tamaño del documento y de lo visible. |

### Listas

`mui_list_add(lista, texto)`, `mui_list_insert(lista, pos, texto)`, `mui_list_remove(lista, pos)`,
`mui_list_clear(lista)`, `mui_list_count(lista) -> Int`, `mui_list_get(lista, pos) -> String`.
Los textos los copia MUI (`MUIV_List_ConstructHook_String`). Para muchas líneas: `mui_list_quiet(lista, si)`.

### Eventos

| Builtin | Notificación |
|---|---|
| `mui_on_press(obj, id)` | botón pulsado (`MUIA_Pressed` → FALSE) |
| `mui_on_change(obj, id)` | cambia el valor (marcado, nivel, ciclo, línea activa, pestaña, texto) |
| `mui_on_ack(string, id)` | Intro en un campo de texto (`MUIA_String_Acknowledge`) |
| `mui_on_double(lista, id)` | doble clic en una lista |
| `mui_on_close(win, id)` | botón de cerrar de la ventana. Sin llamarla, cerrar la primera ventana = -1 (salir). |
| `mui_menu_begin(titulo)`, `mui_menu_item(texto, tecla, id)`, `mui_menu_separator()`, `mui_menu_end()` | menú de la ventana abierta (`Menustrip`) |
| `mui_wait_event() -> Int` | Espera y devuelve el número de un evento, o -1 para salir. |
| `mui_poll_event() -> Int` | Igual sin esperar: 0 si no hay nada. |
| `mui_wait_event_signals(mascara) -> Int` | Espera también otras señales (red, temporizador). Devuelve 0 cuando llega una de ellas; `mui_signals()` dice cuáles. |
| `mui_press(obj)` | Lanza el evento de `mui_on_press` de ese objeto como si se pulsara (atajos, tests). |

Los números de evento son del programa (`const ID_ATRAS = 1`), mayores que 0.

### Zona de dibujo

```ruby
func pinta(x: Int, y: Int, ancho: Int, alto: Int)
    gfx_pen(2)
    gfx_rect(x, y, x + ancho - 1, y + alto - 1)
end

pagina = mui_canvas(320, 200)
mui_canvas_on_draw(pagina, pinta)      # MUIM_Draw: _dash_rp = el RastPort del objeto, recortado a él
mui_canvas_on_input(pagina, ID_RATON)  # clic, rueda y teclas dentro de la zona
...
mui_canvas_redraw(pagina)              # pide repintar (desde la tarea principal, nunca desde otra)
mui_canvas_update(pagina)              # MUI_Redraw con MADF_DRAWUPDATE: sin borrar; mui_canvas_updating() = true
mui_canvas_buffered(pagina, true)      # D48: dibujo en un BitMap amigo con su capa; un BltBitMapRastPort al acabar
x = mui_canvas_mouse_x(pagina)         # tras ID_RATON: posición relativa, botón, rueda (+1/-1), tecla
```

La clase propia (`MUI_CreateCustomClass` sobre `Area`) implementa `MUIM_AskMinMax`, `MUIM_Draw`, `MUIM_Setup`/
`MUIM_Cleanup` (manejador de eventos con `MUIM_Window_AddEventHandler`) y `MUIM_HandleEvent`. El desplazamiento lo
lleva el programa con una `mui_scrollbar` al lado: el navegador pinta desde la línea que diga la barra. Es más
rápido y más simple que meter la zona en un `Virtgroup`.

## Ejemplo: la ventana del navegador

```ruby
const ID_ATRAS = 1
const ID_ADELANTE = 2
const ID_RECARGAR = 3
const ID_IR = 4
const ID_SCROLL = 5
const ID_SALIR = 6

func pinta(x: Int, y: Int, ancho: Int, alto: Int)
    gfx_pen(0)
    gfx_rect(x, y, x + ancho - 1, y + alto - 1)
    gfx_pen(1)
    gfx_text_at(x + 4, y + 12, "Página de prueba")
end

Main
    mui_app_begin("dashweb", "DASHWEB")
    win = mui_window_begin("dashweb", 1)
        mui_menu_begin("Proyecto")
            mui_menu_item("Salir", "Q", ID_SALIR)
        mui_menu_end()
        mui_hgroup_begin()
            atras = mui_button("<")
            adelante = mui_button(">")
            recargar = mui_button("_Recargar")
            url = mui_string("http://aminet.net/", 1024)
        mui_group_end()
        mui_hgroup_begin()
            pagina = mui_canvas(320, 160)
            barra = mui_scrollbar(true)
        mui_group_end()
        mui_hgroup_begin()
            estado = mui_text("Listo")
            progreso = mui_gauge(100)
            mui_weight(progreso, 30)
        mui_group_end()
    mui_window_end()

    mui_on_press(atras, ID_ATRAS)
    mui_on_press(adelante, ID_ADELANTE)
    mui_on_press(recargar, ID_RECARGAR)
    mui_on_ack(url, ID_IR)
    mui_on_change(barra, ID_SCROLL)
    mui_canvas_on_draw(pagina, pinta)
    mui_set_enabled(adelante, false)

    mui_window_open(win)
    while true
        ev = mui_wait_event()
        if ev == -1 or ev == ID_SALIR
            break
        end
        if ev == ID_IR
            mui_set_text(estado, "Cargando " + mui_get_text(url))
            mui_set_value(progreso, 50)
        end
        if ev == ID_SCROLL
            mui_canvas_redraw(pagina)
        end
    end
    mui_app_end()
end
```

## Por dentro

- **Cabeceras:** el runtime define `NO_INLINE_STDARG` antes de `proto/muimaster.h` y usa macros propias con
  array (`MUI_NewObject`, `DoMethod`), porque la función en línea del SDK pierde las etiquetas con `-O2`
  (bitácora, tarea 1). `IPTR` = `ULONG` si el NDK no lo trae.
- **Compilar:** el runtime MUI solo se emite si el programa usa algún `mui_`. Entonces `./dash` y el runner añaden
  `-I $DASH_MUI_SDK/C/include` (por defecto `~/.cache/dash-mui/x/SDK/MUI`), en `compiler/cflags.py`. Sin el SDK:
  error claro ("MUI SDK not found: run tools/get_mui_sdk.sh or set DASH_MUI_SDK").
- **Pila:** 32 KB por defecto en programas con MUI (hecho en la tarea 1).
- **CPU:** MUI 5 para OS3 es de 68020. `mui_app_begin` lo comprueba (`SysBase->AttnFlags`) y sale con un mensaje
  en un 68000, en vez de colgarse.
- **Memoria:** MUI es dueño de los objetos; los handles no llevan contador de referencias y dejan de valer tras
  `mui_app_end()`. Los textos que se pasan a `mui_text`, `mui_string`, `mui_list_add`... los copia MUI, así que los
  temporales de Dash se pueden liberar al acabar la vuelta. `--memcheck` debe acabar sin nada vivo.
- **Tests en el emulador:** sin ratón. Se prueba con `mui_set_value` (dispara `on_change`), `mui_press`,
  `mui_get_*` y `mui_window_open`; los programas acaban solos con `--autoclose` (`mui_wait_event` devuelve -1).
- **Cadena de errores:** sin muimaster, ventana que no abre o 68000 → mensaje por la salida estándar y
  `mui_app_begin` devuelve 0; el programa decide.
