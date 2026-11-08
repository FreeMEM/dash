"""Tareas, reloj, traducciones y escritorio (TASK_FUNCTIONS), segunda parte: el fondo del escritorio, los discos,
la red, la temperatura, el USB y el ratón."""

GROUPS = {}


def _f(es, en, see=()):
    return {"es": es, "en": en, "see": list(see)}


_CV_ES = "- `canvas`: la zona de `desktop_canvas`.\n"
_CV_EN = "- `canvas`: the area from `desktop_canvas`.\n"
_D_ES = "- `i`: el volumen, desde 0, del último `disks_read`.\n"
_D_EN = "- `i`: the volume, from 0, of the last `disks_read`.\n"
_N_ES = "- `i`: la interfaz, desde 0, del último `net_ifs_read`.\n"
_N_EN = "- `i`: the interface, from 0, of the last `net_ifs_read`.\n"
_U_ES = "- `i`: el dispositivo, desde 0, del último `usb_hid_read`.\n"
_U_EN = "- `i`: the device, from 0, of the last `usb_hid_read`.\n"
_DR_ES = "del último `net_driver_read`"
_DR_EN = "of the last `net_driver_read`"
_WR_ES = """\
Devuelve 0 si la leyó (`wifi_signal`, `wifi_noise`), 1 si no contestó a tiempo, 2 si el driver no lo dice y 3 si no
hay esa interfaz o ese driver.
"""
_WR_EN = """\
Returns 0 if it read it (`wifi_signal`, `wifi_noise`), 1 if it did not answer in time, 2 if the driver does not say
and 3 if there is no such interface or driver.
"""

FUNCS = {
    # ------------------------------------------------------------ escritorio
    "desktop_canvas": _f("""\
- `x`, `y`: la esquina en el escritorio del Workbench, bajo la barra de la pantalla. Negativas cuentan desde el
  borde derecho o el de abajo.
- `width`, `height`: el tamaño.

Una zona del fondo del escritorio, detrás de los iconos y sin clics, donde el programa dibuja (un reloj, un
monitor). Devuelve la zona, o 0. Se dibuja desde `desktop_canvas_on_draw`.
""", """\
- `x`, `y`: the corner on the Workbench desktop, below the screen's bar. Negative values count from the right or the
  bottom edge.
- `width`, `height`: the size.

An area of the desktop background, behind the icons and without clicks, where the program draws (a clock, a
monitor). Returns the area, or 0. Drawing happens from `desktop_canvas_on_draw`.
""", ["desktop_canvas_on_draw", "desktop_canvas_update", "desktop_canvas_free"]),
    "desktop_canvas_on_draw": _f(_CV_ES + """\
- `func`: una función `f(x, y, ancho, alto)` que dibuja con los `gfx_*` desde 0, 0.

Se dibuja sobre el fondo de escritorio que hay debajo, así que lo que no se pinta deja verlo.
""", _CV_EN + """\
- `func`: a function `f(x, y, width, height)` that draws with the `gfx_*` functions from 0, 0.

It draws over the desktop background underneath, so what is not painted lets it show.
""", ["desktop_canvas_update"]),
    "desktop_canvas_update": _f(_CV_ES + "\nLa dibuja otra vez ya y enseña lo que cambió, sin tocar los iconos.\n",
                                _CV_EN + "\nDraws it again now and shows what changed, without touching the icons.\n",
                                ["desktop_canvas_update_area"]),
    "desktop_canvas_update_area": _f(_CV_ES + "- `x`, `y`, `width`, `height`: la parte.\n\nComo `desktop_canvas_update`, solo en esa parte (y donde el escritorio se repintó entretanto).\n",
                                     _CV_EN + "- `x`, `y`, `width`, `height`: the part.\n\nLike `desktop_canvas_update`, only in that part (and wherever the desktop was repainted meanwhile).\n",
                                     ["desktop_canvas_drawing"]),
    "desktop_canvas_veil": _f(_CV_ES + """\
- `rgb`: el color, `0xRRGGBB`.
- `alpha`: cuánto tapa, de 0 (nada) a 255.

Un velo de ese color sobre el fondo, debajo del dibujo, para que el texto se lea sobre cualquier imagen de fondo.
""", _CV_EN + """\
- `rgb`: the colour, `0xRRGGBB`.
- `alpha`: how much it covers, 0 (nothing) to 255.

A veil of that colour over the background, under the drawing, so text reads over any background picture.
""", ["desktop_canvas_veil_rect"]),
    "desktop_canvas_veil_rect": _f(_CV_ES + """\
- `x`, `y`, `width`, `height`: el rectángulo.
- `rgb`, `alpha`: como en `desktop_canvas_veil`.

Un velo más, solo ahí, sobre el de `desktop_canvas_veil` (que los quita: va antes). Hasta 16; `false` si no caben.
""", _CV_EN + """\
- `x`, `y`, `width`, `height`: the rectangle.
- `rgb`, `alpha`: as in `desktop_canvas_veil`.

One more veil, only there, on top of the `desktop_canvas_veil` one (which removes them: it goes first). Up to 16;
`false` if no more fit.
""", ["desktop_canvas_veil"]),
    "desktop_canvas_drawing": _f("- `x`, `y`, `width`, `height`: un rectángulo.\n\nDentro de la función de dibujo, devuelve `true` si llega a la parte que se está dibujando: para saltarse lo que no se ve.\n",
                                 "- `x`, `y`, `width`, `height`: a rectangle.\n\nInside the drawing function, returns `true` if it reaches the part being drawn: to skip what is not seen.\n",
                                 ["desktop_canvas_update_area"]),
    "desktop_canvas_free": _f(_CV_ES + "\nVuelve a poner el fondo de escritorio en la zona. Al acabar el programa se hace solo.\n",
                              _CV_EN + "\nPuts the desktop background back in the area. It happens on its own when the program ends.\n",
                              ["desktop_canvas"]),
    # ------------------------------------------------------------ discos
    "disks_read": _f("""\
- `ms`: cuánto esperar como mucho las respuestas.

Lee los volúmenes montados con disco dentro, su tamaño y su espacio libre, preguntando a todos a la vez. Devuelve
cuántos hay. No pide ningún disco.
""", """\
- `ms`: the longest to wait for the answers.

Reads the mounted volumes with a disk inside, their size and free space, asking them all at once. Returns how many
there are. It never asks for a disk.
""", ["disk_name", "disk_free_kb"]),
    "disk_name": _f(_D_ES + "\nDevuelve su nombre, sin los dos puntos.\n", _D_EN + "\nReturns its name, without the colon.\n", ["disks_read"]),
    "disk_kb": _f(_D_ES + "\nDevuelve su tamaño en KB, como `Info`; -1 si no contestó a tiempo.\n", _D_EN + "\nReturns its size in KB, like `Info`; -1 if it did not answer in time.\n", ["disk_free_kb"]),
    "disk_free_kb": _f(_D_ES + "\nDevuelve su espacio libre en KB; -1 si no contestó a tiempo.\n", _D_EN + "\nReturns its free space in KB; -1 if it did not answer in time.\n", ["disk_kb"]),
    # ------------------------------------------------------------ red
    "net_ifs_read": _f("Lee las interfaces de red de Roadshow (también `lo0`), su estado y sus bytes, y devuelve cuántas hay; -1 sin pila TCP/IP o con una que no lo dice (AmiTCP, Miami).\n",
                       "Reads Roadshow's network interfaces (`lo0` too), their state and bytes, and returns how many there are; -1 without a TCP/IP stack or with one that does not say (AmiTCP, Miami).\n",
                       ["net_if_name", "net_drivers_read"]),
    "net_if_name": _f(_N_ES + "\nDevuelve su nombre.\n", _N_EN + "\nReturns its name.\n", ["net_ifs_read"]),
    "net_if_up": _f(_N_ES + "\nDevuelve `true` si está levantada.\n", _N_EN + "\nReturns `true` if it is up.\n", ["net_ifs_read"]),
    "net_if_bytes_in": _f(_N_ES + "\nDevuelve los bytes recibidos (los 32 bits bajos: la resta entre dos lecturas da lo de entretanto).\n",
                          _N_EN + "\nReturns the bytes received (the low 32 bits: subtracting two readings gives what came in between).\n",
                          ["net_if_bytes_out"]),
    "net_if_bytes_out": _f(_N_ES + "\nDevuelve los bytes enviados, como `net_if_bytes_in`.\n", _N_EN + "\nReturns the bytes sent, like `net_if_bytes_in`.\n", ["net_if_bytes_in"]),
    "pistorm_temperature": _f("Devuelve la temperatura de la Raspberry Pi de una PiStorm con Emu68, en décimas de grado (523 son 52,3); -1 sin Emu68.\n",
                              "Returns the temperature of a PiStorm's Raspberry Pi running Emu68, in tenths of a degree (523 is 52.3); -1 without Emu68.\n", []),
    "wifi_read": _f("- `interface`: la interfaz de Roadshow.\n- `ms`: cuánto esperar como mucho.\n\nPide al driver su señal WiFi. " + _WR_ES,
                    "- `interface`: the Roadshow interface.\n- `ms`: the longest to wait.\n\nAsks the driver for its WiFi signal. " + _WR_EN,
                    ["wifi_signal", "wifi_read_device"]),
    "wifi_read_device": _f("- `driver`: el driver SANA-II: `\"wifipi.device\"`.\n- `unit`: su unidad.\n- `ms`: cuánto esperar.\n\nComo `wifi_read`, preguntando al driver directamente, con cualquier pila TCP/IP. " + _WR_ES,
                           "- `driver`: the SANA-II driver: `\"wifipi.device\"`.\n- `unit`: its unit.\n- `ms`: how long to wait.\n\nLike `wifi_read`, asking the driver directly, with any TCP/IP stack. " + _WR_EN,
                           ["wifi_read"]),
    "net_drivers_read": _f("Lee los drivers de red SANA-II en uso (los de `DEVS:Networks` que algo tiene abiertos), con cualquier pila, y devuelve cuántos.\n",
                           "Reads the SANA-II network drivers in use (those in `DEVS:Networks` something has open), with any stack, and returns how many.\n",
                           ["net_driver_name", "net_driver_read"]),
    "net_driver_name": _f("- `i`: el driver, desde 0.\n\nDevuelve su nombre: `\"wifipi.device\"`.\n", "- `i`: the driver, from 0.\n\nReturns its name: `\"wifipi.device\"`.\n", ["net_drivers_read"]),
    "net_driver_read": _f("- `driver`, `unit`, `ms`: como en `wifi_read_device`.\n\nPide sus contadores de paquetes. Devuelve los mismos códigos que `wifi_read_device` (0 leídos).\n",
                          "- `driver`, `unit`, `ms`: as in `wifi_read_device`.\n\nAsks for its packet counters. Returns the same codes as `wifi_read_device` (0 read).\n",
                          ["net_driver_packets_in", "net_driver_has_bytes"]),
    "net_driver_has_bytes": _f(f"Devuelve `true` si el driver {_DR_ES} cuenta también bytes.\n", f"Returns `true` if the driver {_DR_EN} also counts bytes.\n", ["net_driver_bytes_in"]),
    "net_driver_bytes_in": _f(f"Devuelve los bytes recibidos por el driver {_DR_ES} (32 bits bajos).\n", f"Returns the bytes received by the driver {_DR_EN} (low 32 bits).\n", ["net_driver_bytes_out"]),
    "net_driver_bytes_out": _f(f"Devuelve los bytes enviados por el driver {_DR_ES}.\n", f"Returns the bytes sent by the driver {_DR_EN}.\n", ["net_driver_bytes_in"]),
    "net_driver_packets_in": _f(f"Devuelve los paquetes recibidos por el driver {_DR_ES}.\n", f"Returns the packets received by the driver {_DR_EN}.\n", ["net_driver_packets_out"]),
    "net_driver_packets_out": _f(f"Devuelve los paquetes enviados por el driver {_DR_ES}.\n", f"Returns the packets sent by the driver {_DR_EN}.\n", ["net_driver_packets_in"]),
    "wifi_signal": _f("Devuelve la señal del último `wifi_read` que dio 0, en dBm: -30 muy buena, -90 muy mala.\n",
                      "Returns the signal of the last `wifi_read` that gave 0, in dBm: -30 very good, -90 very poor.\n", ["wifi_noise"]),
    "wifi_noise": _f("Devuelve el ruido del último `wifi_read` que dio 0, en dBm.\n", "Returns the noise of the last `wifi_read` that gave 0, in dBm.\n", ["wifi_signal"]),
    # ------------------------------------------------------------ USB y ratón
    "usb_hid_read": _f("Lee los dispositivos USB que lleva la `hid.class` de Poseidon y devuelve cuántos; -1 sin `poseidon.library` 4.\n",
                       "Reads the USB devices handled by Poseidon's `hid.class` and returns how many; -1 without `poseidon.library` 4.\n",
                       ["usb_hid_name", "usb_hid_kind"]),
    "usb_hid_name": _f(_U_ES + "\nDevuelve el nombre del producto.\n", _U_EN + "\nReturns the product's name.\n", ["usb_hid_maker"]),
    "usb_hid_maker": _f(_U_ES + "\nDevuelve el fabricante.\n", _U_EN + "\nReturns the maker.\n", ["usb_hid_name"]),
    "usb_hid_vendor": _f(_U_ES + "\nDevuelve su VendorID.\n", _U_EN + "\nReturns its VendorID.\n", ["usb_hid_product"]),
    "usb_hid_product": _f(_U_ES + "\nDevuelve su ProductID.\n", _U_EN + "\nReturns its ProductID.\n", ["usb_hid_vendor"]),
    "usb_hid_kind": _f(_U_ES + "\nDevuelve qué es: 1 ratón, 2 teclado, 0 otra cosa (muchos trackpads salen así).\n", _U_EN + "\nReturns what it is: 1 mouse, 2 keyboard, 0 something else (many trackpads show up so).\n", ["usb_hid_emitter"]),
    "usb_hid_emitter": _f(_U_ES + "\nDevuelve su emisor, para `mouse_curve`.\n", _U_EN + "\nReturns its emitter, for `mouse_curve`.\n", ["mouse_curve"]),
    "mouse_curve": _f("""\
- `emitter`: 0 el ratón del Amiga (y todo movimiento que no venga de un ratón USB); si no, uno de `usb_hid_emitter`.
- `factors`: una lista de centésimas por velocidad (100 = tal cual, 200 = el doble).

Pone una curva de aceleración a ese ratón. Devuelve `false` si no pudo. Se quita al acabar el programa.
""", """\
- `emitter`: 0 the Amiga mouse (and every movement not from a USB mouse); otherwise one from `usb_hid_emitter`.
- `factors`: a list of hundredths per speed (100 = as is, 200 = double).

Puts an acceleration curve on that mouse. Returns `false` if it could not. It is removed when the program ends.
""", ["mouse_curves_off", "usb_hid_emitter"]),
    "mouse_curve_events": _f("- `emitter`: el emisor.\n\nDevuelve cuántos movimientos ha escalado su curva.\n", "- `emitter`: the emitter.\n\nReturns how many movements its curve has scaled.\n", ["mouse_curve"]),
    "mouse_curves_off": _f("Quita ya las curvas (al acabar el programa también); otro `mouse_curve` las vuelve a poner.\n",
                           "Removes the curves now (also when the program ends); another `mouse_curve` puts them back.\n", ["mouse_curve"]),
    "mouse_patch_left": _f("Devuelve cuántos puentes quedaron en `input.device` bajo el parche de otro programa: dejan pasar todo, para siempre.\n",
                           "Returns how many bridges were left in `input.device` under another program's patch: they let everything through, for good.\n",
                           ["mouse_curves_off"]),
    "mouse_prefs_ticks": _f("Devuelve la velocidad del ratón de las preferencias de Input: 1 la más rápida, 2, 4 la más lenta.\n",
                            "Returns the mouse speed from the Input preferences: 1 the fastest, 2, 4 the slowest.\n", ["mouse_prefs_set"]),
    "mouse_prefs_accel": _f("Devuelve `true` si está puesta la aceleración del ratón de las preferencias de Input.\n",
                            "Returns `true` if the Input preferences' mouse acceleration is on.\n", ["mouse_prefs_set"]),
    "mouse_prefs_set": _f("- `ticks`: 1, 2 o 4, como `mouse_prefs_ticks`.\n- `accel`: la aceleración.\n\nLas pone; vuelven a como estaban al acabar el programa.\n",
                          "- `ticks`: 1, 2 or 4, like `mouse_prefs_ticks`.\n- `accel`: the acceleration.\n\nSets them; they go back to how they were when the program ends.\n",
                          ["mouse_prefs_ticks"]),
}
