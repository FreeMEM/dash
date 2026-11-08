"""Gráficos avanzados (GRAPHICS_ADVANCED): los mapas de tiles."""

GROUPS = {}


def _f(es, en, see=()):
    return {"es": es, "en": en, "see": list(see)}


_M_ES = "- `id`: el número del mapa, de 0 a 7.\n"
_M_EN = "- `id`: the map's number, 0 to 7.\n"
_L_ES = _M_ES + "- `layer`: la capa, desde 0.\n"
_L_EN = _M_EN + "- `layer`: the layer, from 0.\n"
_O_ES = _M_ES + "- `object`: el número del objeto, desde 0.\n"
_O_EN = _M_EN + "- `object`: the object's number, from 0.\n"

FUNCS = {
    "tilemap_create": _f(_M_ES + """\
- `width`, `height`: cuántas celdas de ancho y de alto, de 1 a 1024.
- `tile`: el lado de cada tile en píxeles: 8, 16 o 32.
- `layers`: cuántas capas, de 1 a 8.

Crea un mapa vacío en ese número; el que hubiera se libera. Devuelve `false` con medidas fuera de rango o sin
memoria.
""", _M_EN + """\
- `width`, `height`: how many cells wide and high, 1 to 1024.
- `tile`: each tile's side in pixels: 8, 16 or 32.
- `layers`: how many layers, 1 to 8.

Creates an empty map at that number; any map already there is freed. Returns `false` with sizes out of range or
without memory.
""", ["tilemap_set", "tilemap_draw", "tilemap_load"]),
    "tilemap_load": _f(_M_ES + """\
- `filename`: un fichero IFF FORM FMAP, el que guarda el editor de mapas de Forja o de la extensión de VS Code.

Lo carga con sus capas, sus objetos y el nombre de su tileset. Devuelve `false` si no es un mapa.
""", _M_EN + """\
- `filename`: an IFF FORM FMAP file, the one the map editor in Forja or the VS Code extension saves.

Loads it with its layers, its objects and its tileset's name. Returns `false` if it is not a map.
""", ["tilemap_save", "tilemap_tileset"]),
    "tilemap_save": _f(_M_ES + "- `filename`: el fichero.\n\nGuarda el mapa en IFF FORM FMAP. Devuelve `false` si no se puede escribir.\n",
                       _M_EN + "- `filename`: the file.\n\nSaves the map as IFF FORM FMAP. Returns `false` if it cannot be written.\n",
                       ["tilemap_load"]),
    "tilemap_free": _f(_M_ES + "\nLibera el mapa. Al acabar el programa se liberan solos.\n",
                       _M_EN + "\nFrees the map. They are freed on their own when the program ends.\n", []),
    "tilemap_width": _f(_M_ES + "\nDevuelve su ancho en celdas; 0 si no hay mapa.\n",
                        _M_EN + "\nReturns its width in cells; 0 if there is no map.\n", ["tilemap_height"]),
    "tilemap_height": _f(_M_ES + "\nDevuelve su alto en celdas; 0 si no hay mapa.\n",
                         _M_EN + "\nReturns its height in cells; 0 if there is no map.\n", ["tilemap_width"]),
    "tilemap_tile_size": _f(_M_ES + "\nDevuelve el lado de sus tiles en píxeles: 8, 16 o 32.\n",
                            _M_EN + "\nReturns its tiles' side in pixels: 8, 16 or 32.\n", []),
    "tilemap_layers": _f(_M_ES + "\nDevuelve cuántas capas tiene.\n", _M_EN + "\nReturns how many layers it has.\n",
                         ["tilemap_layer_add"]),
    "tilemap_get": _f(_L_ES + """\
- `x`, `y`: la celda, desde 0.

Devuelve lo que hay en la celda: 0 vacía; si no, el número del tile (1 es el primer fotograma del tileset), más
16384 si va en espejo de izquierda a derecha y 32768 si va de arriba abajo. El tile solo es `v & 16383`. Fuera
del mapa, 0. En las capas de choques, lo que no es 0 es sólido.
""", _L_EN + """\
- `x`, `y`: the cell, from 0.

Returns what is in the cell: 0 empty; otherwise the tile's number (1 is the tileset's first frame), plus 16384 if it
is mirrored left to right and 32768 if top to bottom. The tile alone is `v & 16383`. Outside the map, 0. In
collision layers, anything other than 0 is solid.
""", ["tilemap_set", "tilemap_tile_size"]),
    "tilemap_set": _f(_L_ES + """\
- `x`, `y`: la celda.
- `value`: lo que se pone, como lo da `tilemap_get`; 0 la vacía.

Fuera del mapa no hace nada.
""", _L_EN + """\
- `x`, `y`: the cell.
- `value`: what to put, as `tilemap_get` gives it; 0 empties it.

Outside the map it does nothing.
""", ["tilemap_get"]),
    "tilemap_tileset": _f(_M_ES + "\nDevuelve el nombre del fichero del tileset tal como va guardado en el mapa; `\"\"` si no tiene.\n",
                          _M_EN + "\nReturns the tileset file's name as stored in the map; `\"\"` if it has none.\n",
                          ["tilemap_set_tileset", "bob_load"]),
    "tilemap_set_tileset": _f(_M_ES + """\
- `filename`: el fichero del tileset: una imagen IFF con un fotograma por tile, como la del editor de sprites de
  Forja.

Guarda en el mapa el nombre de su tileset. No lo carga: se carga con `bob_load` y se pasa a `tilemap_draw`.
""", _M_EN + """\
- `filename`: the tileset file: an IFF picture with one frame per tile, like the one from Forja's sprite editor.

Stores the tileset's name in the map. It does not load it: load it with `bob_load` and pass it to `tilemap_draw`.
""", ["tilemap_tileset"]),
    "tilemap_layer_name": _f(_L_ES + "\nDevuelve el nombre de la capa.\n", _L_EN + "\nReturns the layer's name.\n",
                             ["tilemap_layer_set"]),
    "tilemap_layer_type": _f(_L_ES + """\
Devuelve su tipo: 0 tiles. El editor usa otros números para las capas de choques y de objetos.
""", _L_EN + """\
Returns its type: 0 tiles. The editor uses other numbers for collision and object layers.
""", ["tilemap_layer_set"]),
    "tilemap_layer_visible": _f(_L_ES + "\nDevuelve si la capa se ve en el editor. `tilemap_draw` no lo mira.\n",
                                _L_EN + "\nReturns whether the layer shows in the editor. `tilemap_draw` does not look at it.\n",
                                ["tilemap_layer_set"]),
    "tilemap_layer_set": _f(_L_ES + """\
- `name`: su nombre, hasta 31 letras.
- `type`: su tipo (0 tiles).
- `visible`: si se ve en el editor.
""", _L_EN + """\
- `name`: its name, up to 31 letters.
- `type`: its type (0 tiles).
- `visible`: whether it shows in the editor.
""", ["tilemap_layer_name"]),
    "tilemap_layer_add": _f(_M_ES + "\nAñade una capa vacía al final. Devuelve su número, o -1 si ya hay 8.\n",
                            _M_EN + "\nAdds an empty layer at the end. Returns its number, or -1 if there are already 8.\n",
                            ["tilemap_layer_remove"]),
    "tilemap_layer_remove": _f(_L_ES + "\nQuita la capa; las de detrás bajan un puesto. Devuelve `false` si es la única.\n",
                               _L_EN + "\nRemoves the layer; the ones behind move down one place. Returns `false` if it is the only one.\n",
                               ["tilemap_layer_add"]),
    "tilemap_layer_move": _f(_M_ES + """\
- `from`: la capa que se mueve.
- `to`: su puesto nuevo; las de en medio se corren uno.
""", _M_EN + """\
- `from`: the layer to move.
- `to`: its new place; the ones in between shift by one.
""", ["tilemap_layer_add"]),
    "tilemap_resize": _f(_M_ES + """\
- `width`, `height`: el tamaño nuevo en celdas.

Lo que cabe se queda, contando desde la esquina de arriba a la izquierda; las celdas nuevas van vacías. Devuelve
`false` sin memoria o con medidas fuera de rango.
""", _M_EN + """\
- `width`, `height`: the new size in cells.

What fits stays, counting from the top left corner; the new cells are empty. Returns `false` without memory or with
sizes out of range.
""", ["tilemap_create"]),
    "tilemap_draw": _f(_L_ES + """\
- `bob`: el BOB del tileset; el tile n es su fotograma n - 1, y cada celda mide lo que un fotograma.
- `tx`, `ty`: la primera celda que se pinta.
- `tw`, `th`: cuántas celdas de ancho y de alto.
- `x`, `y`: dónde va en el destino de los `gfx_*`.

Pinta ese trozo de la capa de una vez. Las celdas vacías dejan ver lo que había debajo. Para desplazar el nivel se
cambian `tx`, `ty` (de celda en celda) o `x`, `y`.
""", _L_EN + """\
- `bob`: the tileset BOB; tile n is its frame n - 1, and each cell is as big as a frame.
- `tx`, `ty`: the first cell painted.
- `tw`, `th`: how many cells wide and high.
- `x`, `y`: where it goes on the `gfx_*` target.

Paints that piece of the layer in one go. Empty cells let what was underneath show. To scroll the level, change
`tx`, `ty` (cell by cell) or `x`, `y`.
""", ["tilemap_draw_masked", "bob_load"]),
    "tilemap_draw_masked": _f(_L_ES + """\
- Lo demás, como en `tilemap_draw`.

Como `tilemap_draw`, pero además el color 0 de cada tile es transparente: para las capas de delante, que dejan ver
el fondo entre sus dibujos.
""", _L_EN + """\
- The rest, as in `tilemap_draw`.

Like `tilemap_draw`, but each tile's colour 0 is also transparent: for front layers, which let the background show
between their drawings.
""", ["tilemap_draw"]),
    "tilemap_objects": _f(_M_ES + "\nDevuelve cuántos objetos tiene el mapa.\n", _M_EN + "\nReturns how many objects the map has.\n",
                          ["tilemap_object_find"]),
    "tilemap_object_add": _f(_M_ES + """\
- `x`, `y`: dónde, en píxeles del mapa.
- `kind`: su clase, un texto: `"jugador"`, `"moneda"`.

Añade un objeto. Devuelve su número, o -1 si ya hay 256.
""", _M_EN + """\
- `x`, `y`: where, in map pixels.
- `kind`: its kind, a text: `"player"`, `"coin"`.

Adds an object. Returns its number, or -1 if there are already 256.
""", ["tilemap_object_find", "tilemap_object_set"]),
    "tilemap_object_remove": _f(_O_ES + "\nQuita el objeto; los de detrás bajan un puesto.\n",
                                _O_EN + "\nRemoves the object; the ones behind move down one place.\n",
                                ["tilemap_object_add"]),
    "tilemap_object_x": _f(_O_ES + "\nDevuelve su X en píxeles del mapa.\n", _O_EN + "\nReturns its X in map pixels.\n",
                           ["tilemap_object_y"]),
    "tilemap_object_y": _f(_O_ES + "\nDevuelve su Y en píxeles del mapa.\n", _O_EN + "\nReturns its Y in map pixels.\n",
                           ["tilemap_object_x"]),
    "tilemap_object_move": _f(_O_ES + "- `x`, `y`: el sitio nuevo, en píxeles del mapa.\n",
                              _O_EN + "- `x`, `y`: the new place, in map pixels.\n", ["tilemap_object_x"]),
    "tilemap_object_kind": _f(_O_ES + "\nDevuelve su clase.\n", _O_EN + "\nReturns its kind.\n", ["tilemap_object_find"]),
    "tilemap_object_name": _f(_O_ES + "\nDevuelve su nombre.\n", _O_EN + "\nReturns its name.\n", ["tilemap_object_set"]),
    "tilemap_object_sprite": _f(_O_ES + "\nDevuelve el fichero de su sprite; `\"\"` si no tiene.\n",
                                _O_EN + "\nReturns its sprite's file; `\"\"` if it has none.\n", ["tilemap_object_set"]),
    "tilemap_object_set": _f(_O_ES + """\
- `kind`, `name`: su clase y su nombre, hasta 31 letras cada uno.
- `sprite`: el fichero de su sprite; `""` ninguno.
""", _O_EN + """\
- `kind`, `name`: its kind and its name, up to 31 letters each.
- `sprite`: its sprite's file; `""` none.
""", ["tilemap_object_add"]),
    "tilemap_object_find": _f(_M_ES + """\
- `kind`: la clase que se busca.
- `from`: desde qué número de objeto.

Devuelve el primer objeto de esa clase desde `from`, o -1 si no hay. Para encontrar al jugador:
`tilemap_object_find(0, "jugador", 0)`. Para recorrer todos los enemigos, se vuelve a buscar desde el encontrado
más uno.
""", _M_EN + """\
- `kind`: the kind to look for.
- `from`: the object number to start at.

Returns the first object of that kind from `from` on, or -1 if there is none. To find the player:
`tilemap_object_find(0, "player", 0)`. To go through every enemy, search again from the one found plus one.
""", ["tilemap_object_add", "tilemap_objects"]),
}
