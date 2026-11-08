"""
Dash Language - Amiga Built-in Functions
Defines all built-in functions for AmigaOS and their C code generation.
"""
from dataclasses import dataclass
from typing import List, Optional, Callable
from string import Template


@dataclass
class BuiltinFunc:
    """Definition of a built-in function."""
    name: str                    # Dash function name
    params: List[str]            # Parameter names
    return_type: str             # C return type (LONG, STRPTR, BOOL, void)
    c_template: str              # C code template
    needs_gfx: bool = False      # Needs graphics.library
    needs_dos: bool = False      # Needs dos.library
    needs_asl: bool = False      # Needs asl.library
    needs_fileio: bool = False   # Needs file I/O runtime
    needs_gadtools: bool = False # Needs gadtools.library
    needs_reaction: bool = False # Needs ReAction classes (AmigaOS 3.2+)
    needs_audio: bool = False    # Needs audio setup
    needs_area: bool = False     # Needs TmpRas/AreaInfo for area fill
    needs_rtg: bool = False      # Needs CyberGraphX/Picasso96 for RTG support
    reads_only: bool = False     # Only reads its String/object arguments during the call (no copy kept)
    list_of: Optional[str] = None  # Returns a new list of these ("String": a [String] it owns)
    needs_dashos: bool = False   # Only on DashOS (./dash --dashos): its kernel calls (A7); on the Amiga, an error
    description: str = ""        # Documentation


# =============================================================================
# GRAPHICS - Basic Drawing (28 functions)
# =============================================================================

GRAPHICS_BASIC = {
    # Colors and Modes
    "gfx_pen": BuiltinFunc(
        name="gfx_pen",
        params=["color"],
        return_type="void",
        # a library call only when the pen changes (drawing loops set it often)
        c_template="((UBYTE)_dash_rp->FgPen != (UBYTE)(${color}) ? SetAPen(_dash_rp, ${color}) : (void)0)",
        needs_gfx=True,
        description="Set foreground pen color"
    ),
    "gfx_pen_bg": BuiltinFunc(
        name="gfx_pen_bg",
        params=["color"],
        return_type="void",
        c_template="((UBYTE)_dash_rp->BgPen != (UBYTE)(${color}) ? SetBPen(_dash_rp, ${color}) : (void)0)",
        needs_gfx=True,
        description="Set background pen color"
    ),
    "gfx_pen_outline": BuiltinFunc(
        name="gfx_pen_outline",
        params=["color"],
        return_type="void",
        c_template="SetOPen(_dash_rp, ${color})",
        needs_gfx=True,
        description="Set outline pen color for area fills"
    ),
    "gfx_mode": BuiltinFunc(
        name="gfx_mode",
        params=["mode"],
        return_type="void",
        c_template="((UBYTE)_dash_rp->DrawMode != (UBYTE)(${mode}) ? SetDrMd(_dash_rp, ${mode}) : (void)0)",
        needs_gfx=True,
        description="Set drawing mode (JAM1, JAM2, COMPLEMENT, INVERSVID)"
    ),
    "gfx_pattern": BuiltinFunc(
        name="gfx_pattern",
        params=["pattern"],
        return_type="void",
        c_template="SetDrPt(_dash_rp, ${pattern})",
        needs_gfx=True,
        description="Set line pattern (16-bit)"
    ),
    "gfx_rgb": BuiltinFunc(
        name="gfx_rgb",
        params=["index", "r", "g", "b"],
        return_type="void",
        c_template="_dash_set_color(${index}, ${r}, ${g}, ${b})",
        needs_gfx=True,
        description="Set palette color (4-bit components 0-15)"
    ),
    "gfx_rgb8": BuiltinFunc(
        name="gfx_rgb8",
        params=["index", "r", "g", "b"],
        return_type="void",
        c_template="_dash_set_color8(${index}, ${r}, ${g}, ${b})",
        needs_gfx=True,
        description="Set palette color (8-bit components, AGA)"
    ),

    # Basic Primitives
    "gfx_move": BuiltinFunc(
        name="gfx_move",
        params=["x", "y"],
        return_type="void",
        c_template="Move(_dash_rp, ${x}, ${y})",
        needs_gfx=True,
        description="Move graphics cursor"
    ),
    "gfx_draw": BuiltinFunc(
        name="gfx_draw",
        params=["x", "y"],
        return_type="void",
        c_template="Draw(_dash_rp, ${x}, ${y})",
        needs_gfx=True,
        description="Draw line from cursor to point"
    ),
    "gfx_line": BuiltinFunc(
        name="gfx_line",
        params=["x1", "y1", "x2", "y2"],
        return_type="void",
        c_template="Move(_dash_rp, ${x1}, ${y1}); Draw(_dash_rp, ${x2}, ${y2})",
        needs_gfx=True,
        description="Draw line between two points"
    ),
    "gfx_pixel": BuiltinFunc(
        name="gfx_pixel",
        params=["x", "y"],
        return_type="void",
        c_template="WritePixel(_dash_rp, ${x}, ${y})",
        needs_gfx=True,
        description="Draw single pixel"
    ),
    "gfx_pixel_read": BuiltinFunc(
        name="gfx_pixel_read",
        params=["x", "y"],
        return_type="LONG",
        c_template="ReadPixel(_dash_rp, ${x}, ${y})",
        needs_gfx=True,
        description="Read pixel color"
    ),
    "gfx_rect": BuiltinFunc(
        name="gfx_rect",
        params=["x1", "y1", "x2", "y2"],
        return_type="void",
        c_template="RectFill(_dash_rp, ${x1}, ${y1}, ${x2}, ${y2})",
        needs_gfx=True,
        description="Draw filled rectangle"
    ),
    "gfx_box": BuiltinFunc(
        name="gfx_box",
        params=["x1", "y1", "x2", "y2"],
        return_type="void",
        c_template="Move(_dash_rp, ${x1}, ${y1}); Draw(_dash_rp, ${x2}, ${y1}); Draw(_dash_rp, ${x2}, ${y2}); Draw(_dash_rp, ${x1}, ${y2}); Draw(_dash_rp, ${x1}, ${y1})",
        needs_gfx=True,
        description="Draw rectangle outline"
    ),
    "gfx_ellipse": BuiltinFunc(
        name="gfx_ellipse",
        params=["cx", "cy", "rx", "ry"],
        return_type="void",
        c_template="DrawEllipse(_dash_rp, ${cx}, ${cy}, ${rx}, ${ry})",
        needs_gfx=True,
        description="Draw ellipse outline"
    ),
    "gfx_circle": BuiltinFunc(
        name="gfx_circle",
        params=["cx", "cy", "r"],
        return_type="void",
        c_template="DrawEllipse(_dash_rp, ${cx}, ${cy}, ${r}, ${r})",
        needs_gfx=True,
        description="Draw circle outline"
    ),
    "gfx_ellipse_fill": BuiltinFunc(
        name="gfx_ellipse_fill",
        params=["cx", "cy", "rx", "ry"],
        return_type="void",
        c_template="_dash_fill_ellipse(${cx}, ${cy}, ${rx}, ${ry})",
        needs_gfx=True,
        needs_area=True,
        description="Draw filled ellipse"
    ),
    "gfx_circle_fill": BuiltinFunc(
        name="gfx_circle_fill",
        params=["cx", "cy", "r"],
        return_type="void",
        c_template="_dash_fill_ellipse(${cx}, ${cy}, ${r}, ${r})",
        needs_gfx=True,
        needs_area=True,
        description="Draw filled circle"
    ),
    "gfx_flood": BuiltinFunc(
        name="gfx_flood",
        params=["x", "y", "mode"],
        return_type="void",
        c_template="_dash_flood(${x}, ${y}, ${mode})",
        needs_gfx=True,
        needs_area=True,
        description="Flood fill"
    ),

    # Text
    "gfx_text": BuiltinFunc(
        name="gfx_text",
        params=["str"],
        return_type="void",
        c_template="Text(_dash_rp, ${str}, strlen(${str}))",
        needs_gfx=True,
        description="Draw text at cursor"
    ),
    "gfx_text_at": BuiltinFunc(
        name="gfx_text_at",
        params=["x", "y", "str"],
        return_type="void",
        c_template="Move(_dash_rp, ${x}, ${y}); Text(_dash_rp, ${str}, strlen(${str}))",
        needs_gfx=True,
        description="Draw text at position"
    ),
    "gfx_text_len": BuiltinFunc(
        name="gfx_text_len",
        params=["str"],
        return_type="LONG",
        c_template="TextLength(_dash_rp, ${str}, strlen(${str}))",
        needs_gfx=True,
        description="Get text width in pixels"
    ),

    # Clear and Scroll
    "gfx_clear": BuiltinFunc(
        name="gfx_clear",
        params=[],
        return_type="void",
        c_template="SetRast(_dash_rp, 0)",
        needs_gfx=True,
        description="Clear with color 0"
    ),
    "gfx_clear_color": BuiltinFunc(
        name="gfx_clear_color",
        params=["color"],
        return_type="void",
        c_template="SetRast(_dash_rp, ${color})",
        needs_gfx=True,
        description="Clear with specified color"
    ),
    "gfx_scroll": BuiltinFunc(
        name="gfx_scroll",
        params=["dx", "dy", "x1", "y1", "x2", "y2"],
        return_type="void",
        c_template="ScrollRaster(_dash_rp, ${dx}, ${dy}, ${x1}, ${y1}, ${x2}, ${y2})",
        needs_gfx=True,
        description="Scroll region"
    ),

    # Polygons
    "gfx_poly_begin": BuiltinFunc(
        name="gfx_poly_begin",
        params=["x", "y"],
        return_type="void",
        c_template="_dash_poly_begin(${x}, ${y})",
        needs_gfx=True,
        needs_area=True,
        description="Begin polygon at point"
    ),
    "gfx_poly_add": BuiltinFunc(
        name="gfx_poly_add",
        params=["x", "y"],
        return_type="void",
        c_template="_dash_poly_add(${x}, ${y})",
        needs_gfx=True,
        needs_area=True,
        description="Add polygon vertex"
    ),
    "gfx_poly_end": BuiltinFunc(
        name="gfx_poly_end",
        params=[],
        return_type="void",
        c_template="_dash_poly_end()",
        needs_gfx=True,
        needs_area=True,
        description="Close and fill polygon"
    ),

    # Blitting
    "gfx_pens_draw": BuiltinFunc(
        name="gfx_pens_draw",
        params=["buffer", "width", "height", "x", "y", "zoom"],
        return_type="void",
        c_template="_dash_gfx_pens_draw(${buffer}, ${width}, ${height}, ${x}, ${y}, ${zoom})",
        needs_gfx=True,
        description="Draw an image of pens (a byte per pixel, row after row) at x, y, each pixel zoom x zoom: a whole picture in one call (3.1: WriteChunkyPixels)"
    ),
    "gfx_copy": BuiltinFunc(
        name="gfx_copy",
        params=["sx", "sy", "w", "h", "dx", "dy"],
        return_type="void",
        c_template="ClipBlit(_dash_rp, ${sx}, ${sy}, _dash_rp, ${dx}, ${dy}, ${w}, ${h}, 0xC0)",
        needs_gfx=True,
        description="Copy region within window"
    ),
}


# =============================================================================
# GRAPHICS ADVANCED - Sprites, BOBs, Copper, Bitmap (32 functions)
# =============================================================================

GRAPHICS_ADVANCED = {
    # Sprites
    "sprite_load": BuiltinFunc(
        name="sprite_load",
        params=["id", "filename"],
        return_type="BOOL",
        c_template="_dash_sprite_load_file(${id}, ${filename})",
        needs_gfx=True,
        description="Sprite from a picture (ILBM...): 16-pixel frames side by side, pens 0-3 its colours (0 clear); FALSE if it cannot"
    ),
    "sprite_load_attached": BuiltinFunc(
        name="sprite_load_attached",
        params=["id", "filename"],
        return_type="BOOL",
        c_template="_dash_sprite_load_attached(${id}, ${filename})",
        needs_gfx=True,
        reads_only=True, description="Sprite of 15 colours from a picture: an attached pair of hardware sprites, pens 1-15 (0 clear) are colours 17-31; FALSE if it cannot"
    ),
    "sprite_create": BuiltinFunc(
        name="sprite_create",
        params=["id", "width", "height"],
        return_type="BOOL",
        c_template="_dash_sprite_create(${id}, ${width}, ${height})",
        needs_gfx=True,
        description="Create empty sprite"
    ),
    "sprite_pos": BuiltinFunc(
        name="sprite_pos",
        params=["id", "x", "y"],
        return_type="void",
        c_template="_dash_sprite_pos(${id}, ${x}, ${y})",
        needs_gfx=True,
        description="Set sprite position"
    ),
    "sprite_show": BuiltinFunc(
        name="sprite_show",
        params=["id"],
        return_type="void",
        c_template="_dash_sprite_show(${id})",
        needs_gfx=True,
        description="Make sprite visible"
    ),
    "sprite_hide": BuiltinFunc(
        name="sprite_hide",
        params=["id"],
        return_type="void",
        c_template="_dash_sprite_hide(${id})",
        needs_gfx=True,
        description="Hide sprite"
    ),
    "sprite_color": BuiltinFunc(
        name="sprite_color",
        params=["id", "index", "r", "g", "b"],
        return_type="void",
        c_template="_dash_sprite_color(${id}, ${index}, ${r}, ${g}, ${b})",
        needs_gfx=True,
        description="Set a sprite colour, index 0-2 (0-14 for an attached pair; components 0-15)"
    ),
    "sprite_load_colors": BuiltinFunc(
        name="sprite_load_colors",
        params=["id", "filename"],
        return_type="BOOL",
        c_template="_dash_sprite_load_colors(${id}, ${filename})",
        needs_gfx=True,
        reads_only=True, description="Colours 1-3 (1-15 for an attached pair) of a picture's palette (CMAP) as the sprite's colours, 8 bits; false if the file has none"
    ),
    "bob_load_colors": BuiltinFunc(
        name="bob_load_colors",
        params=["filename", "first"],
        return_type="LONG",
        c_template="_dash_bob_load_colors(${filename}, ${first})",
        needs_gfx=True,
        reads_only=True, description="The colours of a picture's palette (CMAP) in the screen's palette from colour first on: how many"
    ),
    "sprite_rgb8": BuiltinFunc(
        name="sprite_rgb8",
        params=["id", "index", "r", "g", "b"],
        return_type="void",
        c_template="_dash_sprite_rgb8(${id}, ${index}, ${r}, ${g}, ${b})",
        needs_gfx=True,
        description="Set a sprite colour, index 0-2 (0-14 for an attached pair), with 8-bit components (0-255; exact on AGA, 4 bits on ECS)"
    ),
    "sprite_frame": BuiltinFunc(
        name="sprite_frame",
        params=["id", "frame"],
        return_type="void",
        c_template="_dash_sprite_frame(${id}, ${frame})",
        needs_gfx=True,
        description="Show frame number frame (0 the first) of a sprite from sprite_load or sprite_load_attached"
    ),
    "sprite_free": BuiltinFunc(
        name="sprite_free",
        params=["id"],
        return_type="void",
        c_template="_dash_sprite_free(${id})",
        needs_gfx=True,
        description="Free sprite memory"
    ),
    "sprite_collision": BuiltinFunc(
        name="sprite_collision",
        params=["id1", "id2"],
        return_type="BOOL",
        c_template="_dash_sprite_collision(${id1}, ${id2})",
        needs_gfx=True,
        description="Check sprite collision"
    ),
    "sprite_set_row": BuiltinFunc(
        name="sprite_set_row",
        params=["id", "row", "plane0", "plane1"],
        return_type="void",
        c_template="_dash_sprite_set_row(${id}, ${row}, ${plane0}, ${plane1})",
        needs_gfx=True,
        description="Set sprite data row (2 bitplanes)"
    ),

    # Software Sprites (RTG Compatible)
    "soft_sprite_create": BuiltinFunc(
        name="soft_sprite_create",
        params=["id", "width", "height", "depth"],
        return_type="BOOL",
        c_template="_dash_soft_sprite_create(${id}, ${width}, ${height}, ${depth})",
        needs_gfx=True,
        description="Create software sprite (RTG compatible)"
    ),
    "soft_sprite_free": BuiltinFunc(
        name="soft_sprite_free",
        params=["id"],
        return_type="void",
        c_template="_dash_soft_sprite_free(${id})",
        needs_gfx=True,
        description="Free software sprite"
    ),
    "soft_sprite_pixel": BuiltinFunc(
        name="soft_sprite_pixel",
        params=["id", "x", "y", "color"],
        return_type="void",
        c_template="_dash_soft_sprite_pixel(${id}, ${x}, ${y}, ${color})",
        needs_gfx=True,
        description="Set pixel in software sprite"
    ),
    "soft_sprite_clear": BuiltinFunc(
        name="soft_sprite_clear",
        params=["id", "color"],
        return_type="void",
        c_template="_dash_soft_sprite_clear(${id}, ${color})",
        needs_gfx=True,
        description="Clear software sprite with color"
    ),
    "soft_sprite_row": BuiltinFunc(
        name="soft_sprite_row",
        params=["id", "row", "plane0", "plane1"],
        return_type="void",
        c_template="_dash_soft_sprite_row(${id}, ${row}, ${plane0}, ${plane1})",
        needs_gfx=True,
        description="Set sprite row (hardware sprite format compatible)"
    ),
    "soft_sprite_show": BuiltinFunc(
        name="soft_sprite_show",
        params=["id"],
        return_type="void",
        c_template="_dash_soft_sprite_show(${id})",
        needs_gfx=True,
        description="Show software sprite"
    ),
    "soft_sprite_hide": BuiltinFunc(
        name="soft_sprite_hide",
        params=["id"],
        return_type="void",
        c_template="_dash_soft_sprite_hide(${id})",
        needs_gfx=True,
        description="Hide software sprite"
    ),
    "soft_sprite_pos": BuiltinFunc(
        name="soft_sprite_pos",
        params=["id", "x", "y"],
        return_type="void",
        c_template="_dash_soft_sprite_pos(${id}, ${x}, ${y})",
        needs_gfx=True,
        description="Set software sprite position"
    ),
    "soft_sprite_x": BuiltinFunc(
        name="soft_sprite_x",
        params=["id"],
        return_type="LONG",
        c_template="_dash_soft_sprite_x(${id})",
        needs_gfx=True,
        description="Get software sprite X position"
    ),
    "soft_sprite_y": BuiltinFunc(
        name="soft_sprite_y",
        params=["id"],
        return_type="LONG",
        c_template="_dash_soft_sprite_y(${id})",
        needs_gfx=True,
        description="Get software sprite Y position"
    ),

    # BOBs (Blitter Objects)
    "bob_load": BuiltinFunc(
        name="bob_load",
        params=["id", "filename"],
        return_type="BOOL",
        c_template="_dash_bob_load(${id}, ${filename})",
        needs_gfx=True,
        reads_only=True, description="Load BOB from file"
    ),
    "bob_create": BuiltinFunc(
        name="bob_create",
        params=["id", "width", "height", "depth"],
        return_type="BOOL",
        c_template="_dash_bob_create(${id}, ${width}, ${height}, ${depth})",
        needs_gfx=True,
        description="Create empty BOB"
    ),
    "bob_pos": BuiltinFunc(
        name="bob_pos",
        params=["id", "x", "y"],
        return_type="void",
        c_template="_dash_bob_pos(${id}, ${x}, ${y})",
        needs_gfx=True,
        description="Set BOB position"
    ),
    "bob_draw": BuiltinFunc(
        name="bob_draw",
        params=["id"],
        return_type="void",
        c_template="_dash_bob_draw(${id})",
        needs_gfx=True,
        description="Draw BOB"
    ),
    "bob_erase": BuiltinFunc(
        name="bob_erase",
        params=["id"],
        return_type="void",
        c_template="_dash_bob_erase(${id})",
        needs_gfx=True,
        description="Erase BOB (restore background)"
    ),
    "bob_frame": BuiltinFunc(
        name="bob_frame",
        params=["id", "frame"],
        return_type="void",
        c_template="_dash_bob_frame(${id}, ${frame})",
        needs_gfx=True,
        description="Set BOB animation frame"
    ),
    "bob_frame_width": BuiltinFunc(
        name="bob_frame_width",
        params=["id", "width"],
        return_type="void",
        c_template="_dash_bob_frame_width(${id}, ${width})",
        needs_gfx=True,
        description="The BOB's image is a strip of frames this many pixels wide (bob_load takes it from Forja's FRJA chunk, or else guesses square frames)"
    ),
    "bob_width": BuiltinFunc(
        name="bob_width",
        params=["id"],
        return_type="LONG",
        c_template="_dash_bob_info(${id}, 0)",
        needs_gfx=True,
        description="The width of a frame of a BOB (0 if there is no such BOB)"
    ),
    "bob_height": BuiltinFunc(
        name="bob_height",
        params=["id"],
        return_type="LONG",
        c_template="_dash_bob_info(${id}, 1)",
        needs_gfx=True,
        description="The height of a BOB"
    ),
    "bob_frames": BuiltinFunc(
        name="bob_frames",
        params=["id"],
        return_type="LONG",
        c_template="_dash_bob_info(${id}, 2)",
        needs_gfx=True,
        description="How many frames a BOB has"
    ),
    "bob_paste": BuiltinFunc(
        name="bob_paste",
        params=["id", "frame", "x", "y"],
        return_type="void",
        c_template="_dash_bob_paste(${id}, ${frame}, ${x}, ${y})",
        needs_gfx=True,
        description="Draw a frame of a BOB at x, y with its mask (colour 0 transparent), without saving what is under it: for games that draw the whole frame each time (double buffering)"
    ),
    "bob_free": BuiltinFunc(
        name="bob_free",
        params=["id"],
        return_type="void",
        c_template="_dash_bob_free(${id})",
        needs_gfx=True,
        description="Free BOB memory"
    ),
    "tilemap_create": BuiltinFunc(
        name="tilemap_create",
        params=["id", "width", "height", "tile", "layers"],
        return_type="BOOL",
        c_template="_dash_tilemap_create(${id}, ${width}, ${height}, ${tile}, ${layers})",
        needs_gfx=True,
        description="A new tile map in id (the old one goes): width x height cells (1 to 1024 each), square tiles of 8, 16 or 32 pixels, 1 to 8 layers of empty cells"
    ),
    "tilemap_load": BuiltinFunc(
        name="tilemap_load",
        params=["id", "filename"],
        return_type="BOOL",
        c_template="_dash_tilemap_load(${id}, ${filename})",
        needs_gfx=True,
        reads_only=True, description="Load a tile map (IFF FORM FMAP, the one Forja's map editor saves) into id; false if it is not one"
    ),
    "tilemap_save": BuiltinFunc(
        name="tilemap_save",
        params=["id", "filename"],
        return_type="BOOL",
        c_template="_dash_tilemap_save(${id}, ${filename})",
        needs_gfx=True,
        reads_only=True, description="Save a tile map as IFF FORM FMAP; false if it cannot"
    ),
    "tilemap_free": BuiltinFunc(
        name="tilemap_free",
        params=["id"],
        return_type="void",
        c_template="_dash_tilemap_free(${id})",
        needs_gfx=True,
        description="Free a tile map"
    ),
    "tilemap_width": BuiltinFunc(
        name="tilemap_width",
        params=["id"],
        return_type="LONG",
        c_template="_dash_tilemap_info(${id}, 0)",
        needs_gfx=True,
        description="Width of a tile map in cells (0 if there is none)"
    ),
    "tilemap_height": BuiltinFunc(
        name="tilemap_height",
        params=["id"],
        return_type="LONG",
        c_template="_dash_tilemap_info(${id}, 1)",
        needs_gfx=True,
        description="Height of a tile map in cells"
    ),
    "tilemap_tile_size": BuiltinFunc(
        name="tilemap_tile_size",
        params=["id"],
        return_type="LONG",
        c_template="_dash_tilemap_info(${id}, 2)",
        needs_gfx=True,
        description="The side of a tile map's tiles in pixels (8, 16 or 32)"
    ),
    "tilemap_layers": BuiltinFunc(
        name="tilemap_layers",
        params=["id"],
        return_type="LONG",
        c_template="_dash_tilemap_info(${id}, 3)",
        needs_gfx=True,
        description="How many layers a tile map has"
    ),
    "tilemap_get": BuiltinFunc(
        name="tilemap_get",
        params=["id", "layer", "x", "y"],
        return_type="LONG",
        c_template="_dash_tilemap_get_cell(${id}, ${layer}, ${x}, ${y})",
        needs_gfx=True,
        description="A cell of a layer (0 the first): the tile (1 the first frame of the tileset, 0 empty) plus 16384 if mirrored left to right and 32768 if top to bottom; 0 outside the map"
    ),
    "tilemap_set": BuiltinFunc(
        name="tilemap_set",
        params=["id", "layer", "x", "y", "value"],
        return_type="void",
        c_template="_dash_tilemap_set_cell(${id}, ${layer}, ${x}, ${y}, ${value})",
        needs_gfx=True,
        description="Set a cell of a layer (like tilemap_get gives it); nothing outside the map"
    ),
    "tilemap_tileset": BuiltinFunc(
        name="tilemap_tileset",
        params=["id"],
        return_type="STRPTR",
        c_template="_dash_tilemap_tileset(${id})",
        needs_gfx=True,
        description="The file name of the map's tileset, as saved in it (\"\" if none)"
    ),
    "tilemap_set_tileset": BuiltinFunc(
        name="tilemap_set_tileset",
        params=["id", "filename"],
        return_type="void",
        c_template="_dash_tilemap_set_tileset(${id}, ${filename})",
        needs_gfx=True,
        description="The file name of the map's tileset (an IFF of Forja's sprite editor, a BOB with one frame a tile)"
    ),
    "tilemap_layer_name": BuiltinFunc(
        name="tilemap_layer_name",
        params=["id", "layer"],
        return_type="STRPTR",
        c_template="_dash_tilemap_layer_name(${id}, ${layer})",
        needs_gfx=True,
        description="The name of a layer"
    ),
    "tilemap_layer_type": BuiltinFunc(
        name="tilemap_layer_type",
        params=["id", "layer"],
        return_type="LONG",
        c_template="_dash_tilemap_layer_info(${id}, ${layer}, 0)",
        needs_gfx=True,
        description="The type of a layer (0 tiles; the editor uses others for collisions and objects)"
    ),
    "tilemap_layer_visible": BuiltinFunc(
        name="tilemap_layer_visible",
        params=["id", "layer"],
        return_type="BOOL",
        c_template="_dash_tilemap_layer_info(${id}, ${layer}, 1)",
        needs_gfx=True,
        description="Whether a layer is shown (for the editor)"
    ),
    "tilemap_layer_set": BuiltinFunc(
        name="tilemap_layer_set",
        params=["id", "layer", "name", "type", "visible"],
        return_type="void",
        c_template="_dash_tilemap_layer_set(${id}, ${layer}, ${name}, ${type}, ${visible})",
        needs_gfx=True,
        description="Name (up to 31 characters), type and visibility of a layer"
    ),
    "tilemap_layer_add": BuiltinFunc(
        name="tilemap_layer_add",
        params=["id"],
        return_type="LONG",
        c_template="_dash_tilemap_layer_add(${id})",
        needs_gfx=True,
        description="A new empty layer at the end: its number, or -1 (there are 8 at most)"
    ),
    "tilemap_layer_remove": BuiltinFunc(
        name="tilemap_layer_remove",
        params=["id", "layer"],
        return_type="BOOL",
        c_template="_dash_tilemap_layer_remove(${id}, ${layer})",
        needs_gfx=True,
        description="Remove a layer (the ones after it move down one); false if it is the only one"
    ),
    "tilemap_layer_move": BuiltinFunc(
        name="tilemap_layer_move",
        params=["id", "from", "to"],
        return_type="BOOL",
        c_template="_dash_tilemap_layer_move(${id}, ${from}, ${to})",
        needs_gfx=True,
        description="Move a layer to another place (the ones in between move one)"
    ),
    "tilemap_resize": BuiltinFunc(
        name="tilemap_resize",
        params=["id", "width", "height"],
        return_type="BOOL",
        c_template="_dash_tilemap_resize(${id}, ${width}, ${height})",
        needs_gfx=True,
        description="New size in cells: what fits stays, from the top left corner, and the new cells are empty"
    ),
    "tilemap_draw": BuiltinFunc(
        name="tilemap_draw",
        params=["id", "layer", "bob", "tx", "ty", "tw", "th", "x", "y"],
        return_type="void",
        c_template="_dash_tilemap_draw(${id}, ${layer}, ${bob}, ${tx}, ${ty}, ${tw}, ${th}, ${x}, ${y}, FALSE)",
        needs_gfx=True,
        description="Draw tw x th cells of a layer, from cell tx, ty, at x, y, with the frames of a BOB (tile n is frame n - 1, mirrored as the cell says; each cell as big as a frame); empty cells let what is under them show. In one blit to the window"
    ),
    "tilemap_draw_masked": BuiltinFunc(
        name="tilemap_draw_masked",
        params=["id", "layer", "bob", "tx", "ty", "tw", "th", "x", "y"],
        return_type="void",
        c_template="_dash_tilemap_draw(${id}, ${layer}, ${bob}, ${tx}, ${ty}, ${tw}, ${th}, ${x}, ${y}, TRUE)",
        needs_gfx=True,
        description="Like tilemap_draw, but colour 0 and empty cells let what is under them show (for the layers in front)"
    ),
    "tilemap_objects": BuiltinFunc(
        name="tilemap_objects",
        params=["id"],
        return_type="LONG",
        c_template="_dash_tilemap_objects(${id})",
        needs_gfx=True,
        description="How many objects the map has"
    ),
    "tilemap_object_add": BuiltinFunc(
        name="tilemap_object_add",
        params=["id", "x", "y", "kind"],
        return_type="LONG",
        c_template="_dash_tilemap_object_add(${id}, ${x}, ${y}, ${kind})",
        needs_gfx=True,
        description="A new object of that kind (a text: \"player\", \"coin\"...) at x, y in pixels of the map: its number (0 the first), or -1 (256 at most)"
    ),
    "tilemap_object_remove": BuiltinFunc(
        name="tilemap_object_remove",
        params=["id", "object"],
        return_type="BOOL",
        c_template="_dash_tilemap_object_remove(${id}, ${object})",
        needs_gfx=True,
        description="Remove an object (the ones after it move down one)"
    ),
    "tilemap_object_x": BuiltinFunc(
        name="tilemap_object_x",
        params=["id", "object"],
        return_type="LONG",
        c_template="_dash_tilemap_object_pos(${id}, ${object}, 0)",
        needs_gfx=True,
        description="Where an object is: x in pixels of the map"
    ),
    "tilemap_object_y": BuiltinFunc(
        name="tilemap_object_y",
        params=["id", "object"],
        return_type="LONG",
        c_template="_dash_tilemap_object_pos(${id}, ${object}, 1)",
        needs_gfx=True,
        description="Where an object is: y in pixels of the map"
    ),
    "tilemap_object_move": BuiltinFunc(
        name="tilemap_object_move",
        params=["id", "object", "x", "y"],
        return_type="void",
        c_template="_dash_tilemap_object_move(${id}, ${object}, ${x}, ${y})",
        needs_gfx=True,
        description="Move an object to x, y"
    ),
    "tilemap_object_kind": BuiltinFunc(
        name="tilemap_object_kind",
        params=["id", "object"],
        return_type="STRPTR",
        c_template="_dash_tilemap_object_text(${id}, ${object}, 0)",
        needs_gfx=True,
        description="The kind of an object"
    ),
    "tilemap_object_name": BuiltinFunc(
        name="tilemap_object_name",
        params=["id", "object"],
        return_type="STRPTR",
        c_template="_dash_tilemap_object_text(${id}, ${object}, 1)",
        needs_gfx=True,
        description="The name of an object"
    ),
    "tilemap_object_sprite": BuiltinFunc(
        name="tilemap_object_sprite",
        params=["id", "object"],
        return_type="STRPTR",
        c_template="_dash_tilemap_object_text(${id}, ${object}, 2)",
        needs_gfx=True,
        description="The sprite file of an object (\"\" if none)"
    ),
    "tilemap_object_set": BuiltinFunc(
        name="tilemap_object_set",
        params=["id", "object", "kind", "name", "sprite"],
        return_type="void",
        c_template="_dash_tilemap_object_set(${id}, ${object}, ${kind}, ${name}, ${sprite})",
        needs_gfx=True,
        description="Kind, name (up to 31 characters each) and sprite file of an object"
    ),
    "tilemap_object_find": BuiltinFunc(
        name="tilemap_object_find",
        params=["id", "kind", "from"],
        return_type="LONG",
        c_template="_dash_tilemap_object_find(${id}, ${kind}, ${from})",
        needs_gfx=True,
        reads_only=True, description="The first object of that kind from number from on; -1 if there is none (to find the player, or go through the enemies)"
    ),
    "bob_collision": BuiltinFunc(
        name="bob_collision",
        params=["id1", "id2"],
        return_type="BOOL",
        c_template="_dash_bob_collision(${id1}, ${id2})",
        needs_gfx=True,
        description="Check BOB collision"
    ),

    # Copper
    "copper_create": BuiltinFunc(
        name="copper_create",
        params=["size"],
        return_type="BOOL",
        c_template="_dash_copper_create(${size})",
        needs_gfx=True,
        description="Create copper list"
    ),
    "copper_wait": BuiltinFunc(
        name="copper_wait",
        params=["y", "x"],
        return_type="void",
        c_template="_dash_copper_wait(${y}, ${x})",
        needs_gfx=True,
        description="Add copper WAIT instruction"
    ),
    "copper_move": BuiltinFunc(
        name="copper_move",
        params=["reg", "value"],
        return_type="void",
        c_template="_dash_copper_move(${reg}, ${value})",
        needs_gfx=True,
        description="Add copper MOVE instruction"
    ),
    "copper_color": BuiltinFunc(
        name="copper_color",
        params=["index", "rgb"],
        return_type="void",
        c_template="_dash_copper_color(${index}, ${rgb})",
        needs_gfx=True,
        description="Add copper color change"
    ),
    "copper_end": BuiltinFunc(
        name="copper_end",
        params=[],
        return_type="void",
        c_template="_dash_copper_end()",
        needs_gfx=True,
        description="End copper list"
    ),
    "copper_install": BuiltinFunc(
        name="copper_install",
        params=[],
        return_type="void",
        c_template="_dash_copper_install()",
        needs_gfx=True,
        description="Install copper list"
    ),
    "copper_free": BuiltinFunc(
        name="copper_free",
        params=[],
        return_type="void",
        c_template="_dash_copper_free()",
        needs_gfx=True,
        description="Free copper list"
    ),

    # Bitmap Operations
    "bitmap_create": BuiltinFunc(
        name="bitmap_create",
        params=["id", "width", "height", "depth"],
        return_type="BOOL",
        c_template="_dash_bitmap_create(${id}, ${width}, ${height}, ${depth})",
        needs_gfx=True,
        description="Create bitmap"
    ),
    "bitmap_load": BuiltinFunc(
        name="bitmap_load",
        params=["id", "filename"],
        return_type="BOOL",
        c_template="_dash_bitmap_load(${id}, ${filename})",
        needs_gfx=True,
        reads_only=True, description="Load IFF bitmap"
    ),
    "bitmap_save": BuiltinFunc(
        name="bitmap_save",
        params=["id", "filename"],
        return_type="BOOL",
        c_template="_dash_bitmap_save(${id}, ${filename})",
        needs_gfx=True,
        reads_only=True, description="Save IFF bitmap"
    ),
    "bitmap_free": BuiltinFunc(
        name="bitmap_free",
        params=["id"],
        return_type="void",
        c_template="_dash_bitmap_free(${id})",
        needs_gfx=True,
        description="Free bitmap"
    ),
    "bitmap_blit": BuiltinFunc(
        name="bitmap_blit",
        params=["src_id", "sx", "sy", "w", "h", "dx", "dy"],
        return_type="void",
        c_template="_dash_bitmap_blit(${src_id}, ${sx}, ${sy}, ${w}, ${h}, ${dx}, ${dy})",
        needs_gfx=True,
        description="Blit from bitmap to screen"
    ),
    "bitmap_blit_mask": BuiltinFunc(
        name="bitmap_blit_mask",
        params=["src_id", "mask_id", "sx", "sy", "w", "h", "dx", "dy"],
        return_type="void",
        c_template="_dash_bitmap_blit_mask(${src_id}, ${mask_id}, ${sx}, ${sy}, ${w}, ${h}, ${dx}, ${dy})",
        needs_gfx=True,
        description="Masked blit from bitmap"
    ),
    "bitmap_draw_to": BuiltinFunc(
        name="bitmap_draw_to",
        params=["id"],
        return_type="void",
        c_template="_dash_bitmap_draw_to(${id})",
        needs_gfx=True,
        description="Set bitmap as drawing target"
    ),
    "bitmap_draw_screen": BuiltinFunc(
        name="bitmap_draw_screen",
        params=[],
        return_type="void",
        c_template="_dash_bitmap_draw_screen()",
        needs_gfx=True,
        description="Set screen as drawing target"
    ),
}


# =============================================================================
# INPUT - Keyboard, Mouse, Joystick (16 functions)
# =============================================================================

INPUT_FUNCTIONS = {
    # Keyboard
    "key_pressed": BuiltinFunc(
        name="key_pressed",
        params=[],
        return_type="BOOL",
        c_template="_dash_key_pressed()",
        description="Check if key is available"
    ),
    "key_get": BuiltinFunc(
        name="key_get",
        params=[],
        return_type="LONG",
        c_template="_dash_key_get()",
        description="Get key code"
    ),
    "key_wait": BuiltinFunc(
        name="key_wait",
        params=[],
        return_type="LONG",
        c_template="_dash_key_wait()",
        description="Wait for and return key"
    ),
    "key_raw": BuiltinFunc(
        name="key_raw",
        params=[],
        return_type="LONG",
        c_template="_dash_key_raw()",
        description="Get raw key code (no translation)"
    ),
    "key_down": BuiltinFunc(
        name="key_down",
        params=["code"],
        return_type="BOOL",
        c_template="_dash_key_down(${code})",
        description="Whether a key is held down now, by its raw code (0x45 Esc, 0x40 space, 0x4C up, 0x4D down, 0x4E right, 0x4F left): for games, asked in each frame; it needs no window"
    ),
    "key_text": BuiltinFunc(
        name="key_text",
        params=["keycode"],
        return_type="STRPTR",
        c_template="_dash_key_text(${keycode})",
        description="Convert keycode to text"
    ),

    # Mouse (coordinates relative to GimmeZeroZero inner area)
    "mouse_x": BuiltinFunc(
        name="mouse_x",
        params=[],
        return_type="LONG",
        c_template="(_dash_win ? _dash_win->MouseX - _dash_win->BorderLeft : 0)",
        description="Mouse X position relative to window inner area (0 without a window)"
    ),
    "mouse_y": BuiltinFunc(
        name="mouse_y",
        params=[],
        return_type="LONG",
        c_template="(_dash_win ? _dash_win->MouseY - _dash_win->BorderTop : 0)",
        description="Mouse Y position relative to window inner area (0 without a window)"
    ),
    "mouse_button": BuiltinFunc(
        name="mouse_button",
        params=["btn"],
        return_type="BOOL",
        c_template="_dash_mouse_button(${btn})",
        description="Check mouse button (0=left, 1=right)"
    ),

    # Window events
    "event_window": BuiltinFunc(
        name="event_window",
        params=[],
        return_type="LONG",
        c_template="_dash_event_window_handle()",
        description="In an EventLoop: handle of the window the event came from (window_create), 0 for the loop's own window"
    ),
    "window_check_close": BuiltinFunc(
        name="window_check_close",
        params=[],
        return_type="BOOL",
        c_template="_dash_check_close()",
        description="Check if close button was clicked (non-blocking)"
    ),
    "close_window": BuiltinFunc(
        name="close_window",
        params=[],
        return_type="void",
        c_template="_dash_close_window()",  # Generated per program: also clears win_<Name>
        description="Close the current window"
    ),

    # Screen Support
    "screen_open_mode": BuiltinFunc(
        name="screen_open_mode",
        params=["mode", "width", "height", "depth", "title"],
        return_type="BOOL",
        c_template="_dash_open_screen_mode(${mode}, ${width}, ${height}, ${depth}, ${title})",
        needs_gfx=True,
        description="Open a screen with an exact display mode (dialog_screen_mode's, or e.g. 0x21000 PAL low resolution, 0x29000 PAL high resolution), size and depth; false if the mode does not exist or cannot have that depth"
    ),
    "screen_clone_wb": BuiltinFunc(
        name="screen_clone_wb",
        params=["name"],
        return_type="BOOL",
        c_template="_dash_clone_wb(${name})",
        needs_gfx=True,
        description="Open a public screen like the Workbench's (mode, size, depth, pens, font) with that name, where other programs can open windows; false if it cannot (or the name is taken). screen_close waits for their windows to close"
    ),
    "screen_visitors": BuiltinFunc(
        name="screen_visitors",
        params=[],
        return_type="LONG",
        c_template="_dash_screen_visitors()",
        needs_gfx=True,
        description="How many uses of the program's public screen there are by others: windows and locks (LockPubScreen; a MUI window may count twice); 0 when none"
    ),
    "screen_make_default": BuiltinFunc(
        name="screen_make_default",
        params=[],
        return_type="BOOL",
        c_template="_dash_screen_make_default()",
        needs_gfx=True,
        description="The program's public screen (screen_clone_wb) becomes the default public screen: windows with no screen of their own open there (programs it starts, shells); screen_close puts the old one back. False if it has no public screen"
    ),
    "screen_open": BuiltinFunc(
        name="screen_open",
        params=["depth", "title"],
        return_type="BOOL",
        c_template="_dash_open_screen(${depth}, ${title}) != NULL",
        needs_gfx=True,
        description="Open a screen cloning Workbench display mode with custom depth"
    ),
    "screen_double_buffer": BuiltinFunc(
        name="screen_double_buffer",
        params=[],
        return_type="BOOL",
        c_template="_dash_screen_double_buffer()",
        needs_gfx=True,
        description="Two buffers for the program's own screen: drawing goes to the hidden one and screen_flip shows it; FALSE without an own screen (or a public one) or on AmigaOS before 3.0"
    ),
    "screen_flip": BuiltinFunc(
        name="screen_flip",
        params=[],
        return_type="BOOL",
        c_template="_dash_screen_flip()",
        needs_gfx=True,
        description="Show what was drawn in the hidden buffer (screen_double_buffer) and draw in the other one; waits for the display, a frame at most. FALSE if it could not change now"
    ),
    "screen_open_custom": BuiltinFunc(
        name="screen_open_custom",
        params=["width", "height", "depth", "title"],
        return_type="BOOL",
        c_template="_dash_open_screen_custom(${width}, ${height}, ${depth}, ${title}) != NULL",
        needs_gfx=True,
        description="Open a custom screen with specific dimensions and depth"
    ),
    "screen_close": BuiltinFunc(
        name="screen_close",
        params=[],
        return_type="void",
        c_template="_dash_close_screen()",
        needs_gfx=True,
        description="Close the screen"
    ),
    "screen_width": BuiltinFunc(
        name="screen_width",
        params=[],
        return_type="LONG",
        c_template="_dash_screen_width()",
        needs_gfx=True,
        description="Get the screen width in pixels"
    ),
    "screen_height": BuiltinFunc(
        name="screen_height",
        params=[],
        return_type="LONG",
        c_template="_dash_screen_height()",
        needs_gfx=True,
        description="Get the screen height in pixels"
    ),
    "check_lmb": BuiltinFunc(
        name="check_lmb",
        params=[],
        return_type="BOOL",
        c_template="_dash_check_lmb()",
        needs_gfx=True,
        description="Check if left mouse button is pressed (hardware)"
    ),
    "check_rmb": BuiltinFunc(
        name="check_rmb",
        params=[],
        return_type="BOOL",
        c_template="_dash_check_rmb()",
        needs_gfx=True,
        description="Check if right mouse button is pressed (hardware)"
    ),
    "check_mouse": BuiltinFunc(
        name="check_mouse",
        params=[],
        return_type="BOOL",
        c_template="_dash_check_any_mouse()",
        needs_gfx=True,
        description="Check if any mouse button is pressed (hardware)"
    ),
    "check_esc": BuiltinFunc(
        name="check_esc",
        params=[],
        return_type="BOOL",
        c_template="_dash_check_esc()",
        needs_gfx=True,
        description="Check if ESC key is pressed (hardware)"
    ),
    "wait_click": BuiltinFunc(
        name="wait_click",
        params=[],
        return_type="LONG",
        c_template="_dash_wait_click()",
        needs_gfx=True,
        description="Wait for mouse click (press and release)"
    ),
    "wait_key": BuiltinFunc(
        name="wait_key",
        params=[],
        return_type="LONG",
        c_template="_dash_wait_key()",
        needs_gfx=True,
        description="Wait for any key and return its code"
    ),

    # Joystick
    "joy_x": BuiltinFunc(
        name="joy_x",
        params=["port"],
        return_type="LONG",
        c_template="_dash_joy_x(${port})",
        description="Joystick X direction (-1, 0, 1)"
    ),
    "joy_y": BuiltinFunc(
        name="joy_y",
        params=["port"],
        return_type="LONG",
        c_template="_dash_joy_y(${port})",
        description="Joystick Y direction (-1, 0, 1)"
    ),
    "joy_button": BuiltinFunc(
        name="joy_button",
        params=["port"],
        return_type="BOOL",
        c_template="_dash_joy_button(${port})",
        description="Joystick button state"
    ),
    "joy_up": BuiltinFunc(
        name="joy_up",
        params=["port"],
        return_type="BOOL",
        c_template="(_dash_joy_y(${port}) < 0)",
        description="Joystick up"
    ),
    "joy_down": BuiltinFunc(
        name="joy_down",
        params=["port"],
        return_type="BOOL",
        c_template="(_dash_joy_y(${port}) > 0)",
        description="Joystick down"
    ),
    "joy_left": BuiltinFunc(
        name="joy_left",
        params=["port"],
        return_type="BOOL",
        c_template="(_dash_joy_x(${port}) < 0)",
        description="Joystick left"
    ),
    "joy_right": BuiltinFunc(
        name="joy_right",
        params=["port"],
        return_type="BOOL",
        c_template="(_dash_joy_x(${port}) > 0)",
        description="Joystick right"
    ),
    "joy_fire": BuiltinFunc(
        name="joy_fire",
        params=["port"],
        return_type="BOOL",
        c_template="_dash_joy_button(${port})",
        description="Joystick fire button"
    ),
}


# =============================================================================
# GADTOOLS - Native Workbench Gadgets
# =============================================================================

GADTOOLS_FUNCTIONS = {
    # Initialization
    "gt_init": BuiltinFunc(
        name="gt_init",
        params=[],
        return_type="BOOL",
        c_template="_dash_gt_init()",
        needs_gadtools=True,
        description="Initialize GadTools context (call after window open)"
    ),
    "gt_cleanup": BuiltinFunc(
        name="gt_cleanup",
        params=[],
        return_type="void",
        c_template="_dash_gt_cleanup()",
        needs_gadtools=True,
        description="Cleanup GadTools resources"
    ),
    "gt_attach": BuiltinFunc(
        name="gt_attach",
        params=[],
        return_type="void",
        c_template="_dash_gt_attach()",
        needs_gadtools=True,
        description="Attach gadgets to window (call after creating all gadgets)"
    ),

    # Gadget creation
    "gt_button": BuiltinFunc(
        name="gt_button",
        params=["x", "y", "w", "h", "label"],
        return_type="LONG",
        c_template="_dash_gt_button(${x}, ${y}, ${w}, ${h}, ${label})",
        needs_gadtools=True,
        description="Create a button gadget, returns gadget ID"
    ),
    "gt_checkbox": BuiltinFunc(
        name="gt_checkbox",
        params=["x", "y", "w", "h", "label", "checked"],
        return_type="LONG",
        c_template="_dash_gt_checkbox(${x}, ${y}, ${w}, ${h}, ${label}, ${checked})",
        needs_gadtools=True,
        description="Create a checkbox gadget"
    ),
    "gt_string": BuiltinFunc(
        name="gt_string",
        params=["x", "y", "w", "h", "label", "initial", "maxchars"],
        return_type="LONG",
        c_template="_dash_gt_string(${x}, ${y}, ${w}, ${h}, ${label}, ${initial}, ${maxchars})",
        needs_gadtools=True,
        description="Create a string input gadget"
    ),
    "gt_integer": BuiltinFunc(
        name="gt_integer",
        params=["x", "y", "w", "h", "label", "initial"],
        return_type="LONG",
        c_template="_dash_gt_integer(${x}, ${y}, ${w}, ${h}, ${label}, ${initial})",
        needs_gadtools=True,
        description="Create an integer input gadget"
    ),
    "gt_slider": BuiltinFunc(
        name="gt_slider",
        params=["x", "y", "w", "h", "label", "min", "max", "level"],
        return_type="LONG",
        c_template="_dash_gt_slider(${x}, ${y}, ${w}, ${h}, ${label}, ${min}, ${max}, ${level})",
        needs_gadtools=True,
        description="Create a slider gadget"
    ),
    "gt_palette": BuiltinFunc(
        name="gt_palette",
        params=["x", "y", "w", "h", "label", "depth", "color"],
        return_type="LONG",
        c_template="_dash_gt_palette(${x}, ${y}, ${w}, ${h}, ${label}, ${depth}, ${color})",
        needs_gadtools=True,
        description="Create a palette selector gadget"
    ),
    "gt_text": BuiltinFunc(
        name="gt_text",
        params=["x", "y", "w", "h", "label", "text"],
        return_type="LONG",
        c_template="_dash_gt_text(${x}, ${y}, ${w}, ${h}, ${label}, ${text})",
        needs_gadtools=True,
        description="Create a static text gadget"
    ),

    # Gadget value access
    "gt_get_value": BuiltinFunc(
        name="gt_get_value",
        params=["gad_id"],
        return_type="LONG",
        c_template="_dash_gt_get_value(${gad_id})",
        needs_gadtools=True,
        description="Get numeric value from gadget (slider, palette, etc.)"
    ),
    "gt_set_value": BuiltinFunc(
        name="gt_set_value",
        params=["gad_id", "value"],
        return_type="void",
        c_template="_dash_gt_set_value(${gad_id}, ${value})",
        needs_gadtools=True,
        description="Set numeric value of gadget"
    ),
    "gt_get_string": BuiltinFunc(
        name="gt_get_string",
        params=["gad_id"],
        return_type="STRPTR",
        c_template="_dash_gt_get_string(${gad_id})",
        needs_gadtools=True,
        description="Get string value from string gadget"
    ),

    # Event handling
    "gt_event": BuiltinFunc(
        name="gt_event",
        params=[],
        return_type="LONG",
        c_template="_dash_gt_event()",
        needs_gadtools=True,
        description="Check for gadget event, returns gadget ID or -1 (none) or -2 (close)"
    ),
    "gt_wait_event": BuiltinFunc(
        name="gt_wait_event",
        params=[],
        return_type="LONG",
        c_template="_dash_gt_wait_event()",
        needs_gadtools=True,
        description="Wait for gadget event, returns gadget ID or -2 (close)"
    ),
    "gt_cycle": BuiltinFunc(
        name="gt_cycle",
        params=["x", "y", "w", "h", "label", "options"],
        return_type="LONG",
        c_template="_dash_gt_cycle_str(${x}, ${y}, ${w}, ${h}, ${label}, ${options})",
        needs_gadtools=True,
        description="Create a cycle gadget; options separated by | (gt_get_value: option)"
    ),
    "gt_enable": BuiltinFunc(
        name="gt_enable",
        params=["gad_id"],
        return_type="void",
        c_template="_dash_gt_set_enabled(${gad_id}, 1)",
        needs_gadtools=True,
        description="Enable a gadget"
    ),
    "gt_disable": BuiltinFunc(
        name="gt_disable",
        params=["gad_id"],
        return_type="void",
        c_template="_dash_gt_set_enabled(${gad_id}, 0)",
        needs_gadtools=True,
        description="Disable (ghost) a gadget"
    ),
    "gt_set_text": BuiltinFunc(
        name="gt_set_text",
        params=["gad_id", "text"],
        return_type="void",
        c_template="_dash_gt_set_text(${gad_id}, ${text})",
        needs_gadtools=True,
        description="Change the text of a gt_text or gt_string gadget"
    ),
}


# =============================================================================
# MENU - Native Intuition Menus
# =============================================================================

MENU_FUNCTIONS = {
    "menu_title": BuiltinFunc(
        name="menu_title",
        params=["label"],
        return_type="void",
        c_template="_dash_menu_title(${label})",
        needs_gadtools=True,
        description="Add a menu title"
    ),
    "menu_item": BuiltinFunc(
        name="menu_item",
        params=["label", "shortcut", "id"],
        return_type="void",
        c_template="_dash_menu_item(${label}, ${shortcut}, ${id})",
        needs_gadtools=True,
        description="Add a menu item with keyboard shortcut and ID"
    ),
    "menu_sub": BuiltinFunc(
        name="menu_sub",
        params=["label", "shortcut", "id"],
        return_type="void",
        c_template="_dash_menu_sub(${label}, ${shortcut}, ${id})",
        needs_gadtools=True,
        description="Add a submenu item"
    ),
    "menu_separator": BuiltinFunc(
        name="menu_separator",
        params=[],
        return_type="void",
        c_template="_dash_menu_separator()",
        needs_gadtools=True,
        description="Add a menu separator bar"
    ),
    "menu_attach": BuiltinFunc(
        name="menu_attach",
        params=[],
        return_type="BOOL",
        c_template="_dash_menu_attach()",
        needs_gadtools=True,
        description="Attach menus to window (call after defining all menus)"
    ),
    "menu_event": BuiltinFunc(
        name="menu_event",
        params=[],
        return_type="LONG",
        c_template="_dash_menu_event()",
        needs_gadtools=True,
        description="Check for menu event, returns menu item ID or -1/-2"
    ),
    "menu_id": BuiltinFunc(
        name="menu_id",
        params=[],
        return_type="LONG",
        c_template="_dash_menu_id()",
        needs_gadtools=True,
        description="In an EventLoop's On Menu: id of the menu item chosen"
    ),
    "menu_check_item": BuiltinFunc(
        name="menu_check_item",
        params=["label", "shortcut", "id"],
        return_type="void",
        c_template="_dash_menu_check_item(${label}, ${shortcut}, ${id})",
        needs_gadtools=True,
        description="Add a menu item with a check mark that each choice toggles"
    ),
    "menu_checked": BuiltinFunc(
        name="menu_checked",
        params=["id"],
        return_type="LONG",
        c_template="_dash_menu_checked(${id})",
        needs_gadtools=True,
        description="1 if the check mark of that menu item is on"
    ),
    "menu_enable": BuiltinFunc(
        name="menu_enable",
        params=["id", "enabled"],
        return_type="void",
        c_template="_dash_menu_enable(${id}, ${enabled})",
        needs_gadtools=True,
        description="Enable or disable (ghost) a menu item after menu_attach"
    ),
}


# =============================================================================
# ASL - File Requesters
# =============================================================================

ASL_FUNCTIONS = {
    "file_open_dialog": BuiltinFunc(
        name="file_open_dialog",
        params=["title", "pattern"],
        return_type="BOOL",
        c_template="_dash_file_request(${title}, ${pattern}, FALSE)",
        needs_asl=True,
        needs_gadtools=True,
        description="Show file open dialog, returns true if file selected"
    ),
    "file_save_dialog": BuiltinFunc(
        name="file_save_dialog",
        params=["title", "pattern"],
        return_type="BOOL",
        c_template="_dash_file_request(${title}, ${pattern}, TRUE)",
        needs_asl=True,
        needs_gadtools=True,
        description="Show file save dialog, returns true if file selected"
    ),
    "file_get_path": BuiltinFunc(
        name="file_get_path",
        params=[],
        return_type="STRPTR",
        c_template="_dash_get_path()",
        needs_asl=True,
        needs_gadtools=True,
        description="Get selected directory path from last dialog"
    ),
    "file_get_name": BuiltinFunc(
        name="file_get_name",
        params=[],
        return_type="STRPTR",
        c_template="_dash_get_file()",
        needs_asl=True,
        needs_gadtools=True,
        description="Get selected filename from last dialog"
    ),
    "file_fullpath": BuiltinFunc(
        name="file_fullpath",
        params=[],
        return_type="STRPTR",
        c_template="_dash_file_fullpath()",
        needs_asl=True,
        needs_gadtools=True,
        description="Get full path (dir + filename) from last dialog"
    ),
}


# =============================================================================
# REACTION - Modern GUI (AmigaOS 3.2+ / 4.x) (20 functions)
# =============================================================================

REACTION_FUNCTIONS = {
    # Window Management
    "ra_window_create": BuiltinFunc(
        name="ra_window_create",
        params=["title", "width", "height"],
        return_type="LONG",
        c_template="ra_window_create(${title}, ${width}, ${height})",
        needs_reaction=True,
        description="Create a ReAction window with a layout; it becomes the current one. Its number (1-4), 0 on failure"
    ),
    "ra_window_use": BuiltinFunc(
        name="ra_window_use",
        params=["window"],
        return_type="void",
        c_template="ra_window_use(${window})",
        needs_reaction=True,
        description="Window the next ra_* calls work on (the number ra_window_create gave; up to 4 windows)"
    ),
    "ra_event_window": BuiltinFunc(
        name="ra_event_window",
        params=[],
        return_type="LONG",
        c_template="ra_event_window()",
        needs_reaction=True,
        description="Window of the last event (its number from ra_window_create)"
    ),
    "ra_window_open": BuiltinFunc(
        name="ra_window_open",
        params=[],
        return_type="LONG",
        c_template="ra_window_open()",
        needs_reaction=True,
        description="Open the ReAction window"
    ),
    "ra_window_close": BuiltinFunc(
        name="ra_window_close",
        params=[],
        return_type="void",
        c_template="ra_window_close()",
        needs_reaction=True,
        description="Close the current ReAction window and free its gadgets (another open one becomes current)"
    ),
    "ra_window_sigmask": BuiltinFunc(
        name="ra_window_sigmask",
        params=[],
        return_type="ULONG",
        c_template="ra_window_sigmask()",
        needs_reaction=True,
        description="Get window signal mask for Wait()"
    ),

    # Event Handling
    "ra_handle_events": BuiltinFunc(
        name="ra_handle_events",
        params=[],
        return_type="LONG",
        c_template="ra_handle_events()",
        needs_reaction=True,
        description="Handle window events (non-blocking), returns gadget ID or -1 for close"
    ),
    "ra_wait_event": BuiltinFunc(
        name="ra_wait_event",
        params=[],
        return_type="LONG",
        c_template="ra_wait_event()",
        needs_reaction=True,
        description="Wait for and handle window events, returns gadget ID or -1 for close"
    ),

    # Gadget Creation
    "ra_add_button": BuiltinFunc(
        name="ra_add_button",
        params=["id", "label"],
        return_type="LONG",
        c_template="ra_add_button(${id}, ${label})",
        needs_reaction=True,
        description="Add button gadget to layout"
    ),
    "ra_add_string": BuiltinFunc(
        name="ra_add_string",
        params=["id", "initial", "maxchars"],
        return_type="LONG",
        c_template="ra_add_string(${id}, ${initial}, ${maxchars})",
        needs_reaction=True,
        description="Add string input gadget"
    ),
    "ra_add_checkbox": BuiltinFunc(
        name="ra_add_checkbox",
        params=["id", "label", "checked"],
        return_type="LONG",
        c_template="ra_add_checkbox(${id}, ${label}, ${checked})",
        needs_reaction=True,
        description="Add checkbox gadget"
    ),
    "ra_add_slider": BuiltinFunc(
        name="ra_add_slider",
        params=["id", "min", "max", "initial"],
        return_type="LONG",
        c_template="ra_add_slider(${id}, ${min}, ${max}, ${initial})",
        needs_reaction=True,
        description="Add horizontal slider gadget"
    ),
    "ra_add_integer": BuiltinFunc(
        name="ra_add_integer",
        params=["id", "initial", "min", "max"],
        return_type="LONG",
        c_template="ra_add_integer(${id}, ${initial}, ${min}, ${max})",
        needs_reaction=True,
        description="Add integer input gadget"
    ),
    "ra_add_label": BuiltinFunc(
        name="ra_add_label",
        params=["text"],
        return_type="LONG",
        c_template="ra_add_label(${text})",
        needs_reaction=True,
        description="Add text label"
    ),

    # Gadget Value Access
    "ra_get_value": BuiltinFunc(
        name="ra_get_value",
        params=["id"],
        return_type="LONG",
        c_template="ra_get_value(${id})",
        needs_reaction=True,
        description="Get gadget value (checkbox 1/0, slider, integer, palette, chooser, scroller)"
    ),
    "ra_get_string": BuiltinFunc(
        name="ra_get_string",
        params=["id"],
        return_type="STRPTR",
        c_template="ra_get_string(${id})",
        needs_reaction=True,
        description="Get string gadget text"
    ),
    "ra_set_value": BuiltinFunc(
        name="ra_set_value",
        params=["id", "value"],
        return_type="void",
        c_template="ra_set_value(${id}, ${value})",
        needs_reaction=True,
        description="Set gadget value (same gadgets as ra_get_value)"
    ),
    "ra_refresh_layout": BuiltinFunc(
        name="ra_refresh_layout",
        params=[],
        return_type="void",
        c_template="ra_refresh_layout()",
        needs_reaction=True,
        description="Refresh window layout after adding gadgets"
    ),

    # Constants (as functions for Dash syntax)
    "RA_EVENT_CLOSE": BuiltinFunc(
        name="RA_EVENT_CLOSE",
        params=[],
        return_type="LONG",
        c_template="RA_EVENT_CLOSE",
        needs_reaction=True,
        description="Close window event code (-1)"
    ),
    "RA_EVENT_NONE": BuiltinFunc(
        name="RA_EVENT_NONE",
        params=[],
        return_type="LONG",
        c_template="RA_EVENT_NONE",
        needs_reaction=True,
        description="No event code (-3)"
    ),

    # Custom drawing support
    "ra_get_rastport": BuiltinFunc(
        name="ra_get_rastport",
        params=[],
        return_type="APTR",
        c_template="ra_get_rastport()",
        needs_reaction=True,
        needs_gfx=True,
        description="Get RastPort for custom drawing (also sets _dash_rp)"
    ),
    "ra_get_inner_left": BuiltinFunc(
        name="ra_get_inner_left",
        params=[],
        return_type="LONG",
        c_template="ra_get_inner_left()",
        needs_reaction=True,
        description="Get inner left border of window"
    ),
    "ra_get_inner_top": BuiltinFunc(
        name="ra_get_inner_top",
        params=[],
        return_type="LONG",
        c_template="ra_get_inner_top()",
        needs_reaction=True,
        description="Get inner top border of window"
    ),
    "ra_get_inner_width": BuiltinFunc(
        name="ra_get_inner_width",
        params=[],
        return_type="LONG",
        c_template="ra_get_inner_width()",
        needs_reaction=True,
        description="Get inner width of window"
    ),
    "ra_get_inner_height": BuiltinFunc(
        name="ra_get_inner_height",
        params=[],
        return_type="LONG",
        c_template="ra_get_inner_height()",
        needs_reaction=True,
        description="Get inner height of window"
    ),

    # Palette gadget
    "ra_add_palette": BuiltinFunc(
        name="ra_add_palette",
        params=["id", "depth", "initial_color"],
        return_type="LONG",
        c_template="ra_add_palette(${id}, ${depth}, ${initial_color})",
        needs_reaction=True,
        description="Add color palette gadget"
    ),
    "ra_get_palette_color": BuiltinFunc(
        name="ra_get_palette_color",
        params=["id"],
        return_type="LONG",
        c_template="ra_get_palette_color(${id})",
        needs_reaction=True,
        description="Get selected color from palette"
    ),
    "ra_set_palette_color": BuiltinFunc(
        name="ra_set_palette_color",
        params=["id", "color"],
        return_type="void",
        c_template="ra_set_palette_color(${id}, ${color})",
        needs_reaction=True,
        description="Set selected color in palette"
    ),

    # Chooser (dropdown) gadget
    "ra_add_chooser": BuiltinFunc(
        name="ra_add_chooser",
        params=["id"],
        return_type="LONG",
        c_template="ra_add_chooser(${id})",
        needs_reaction=True,
        description="Add dropdown/chooser gadget"
    ),
    "ra_chooser_add_item": BuiltinFunc(
        name="ra_chooser_add_item",
        params=["id", "label"],
        return_type="LONG",
        c_template="ra_chooser_add_item(${id}, ${label})",
        needs_reaction=True,
        description="Add item to chooser"
    ),
    "ra_get_chooser_selected": BuiltinFunc(
        name="ra_get_chooser_selected",
        params=["id"],
        return_type="LONG",
        c_template="ra_get_chooser_selected(${id})",
        needs_reaction=True,
        description="Get selected index from chooser"
    ),
    "ra_set_chooser_selected": BuiltinFunc(
        name="ra_set_chooser_selected",
        params=["id", "index"],
        return_type="void",
        c_template="ra_set_chooser_selected(${id}, ${index})",
        needs_reaction=True,
        description="Set selected index in chooser"
    ),

    # Scroller gadget
    "ra_add_scroller": BuiltinFunc(
        name="ra_add_scroller",
        params=["id", "min", "max", "visible", "initial"],
        return_type="LONG",
        c_template="ra_add_scroller(${id}, ${min}, ${max}, ${visible}, ${initial})",
        needs_reaction=True,
        description="Add horizontal scroller gadget"
    ),
    "ra_add_scroller_vert": BuiltinFunc(
        name="ra_add_scroller_vert",
        params=["id", "min", "max", "visible", "initial"],
        return_type="LONG",
        c_template="ra_add_scroller_vert(${id}, ${min}, ${max}, ${visible}, ${initial})",
        needs_reaction=True,
        description="Add vertical scroller gadget"
    ),
    "ra_get_scroller": BuiltinFunc(
        name="ra_get_scroller",
        params=["id"],
        return_type="LONG",
        c_template="ra_get_scroller(${id})",
        needs_reaction=True,
        description="Get scroller position"
    ),
    "ra_set_scroller": BuiltinFunc(
        name="ra_set_scroller",
        params=["id", "pos"],
        return_type="void",
        c_template="ra_set_scroller(${id}, ${pos})",
        needs_reaction=True,
        description="Set scroller position"
    ),

    # Enable/Disable gadgets
    "ra_enable_gadget": BuiltinFunc(
        name="ra_enable_gadget",
        params=["id"],
        return_type="void",
        c_template="ra_enable_gadget(${id})",
        needs_reaction=True,
        description="Enable a gadget"
    ),
    "ra_disable_gadget": BuiltinFunc(
        name="ra_disable_gadget",
        params=["id"],
        return_type="void",
        c_template="ra_disable_gadget(${id})",
        needs_reaction=True,
        description="Disable a gadget"
    ),

    # Set gadget properties
    "ra_set_string": BuiltinFunc(
        name="ra_set_string",
        params=["id", "text"],
        return_type="void",
        c_template="ra_set_string(${id}, ${text})",
        needs_reaction=True,
        description="Set string gadget text"
    ),
    "ra_set_text": BuiltinFunc(
        name="ra_set_text",
        params=["id", "text"],
        return_type="void",
        c_template="ra_set_text(${id}, ${text})",
        needs_reaction=True,
        description="Set button/label text"
    ),

    # Layout groups
    "ra_layout_hgroup_begin": BuiltinFunc(
        name="ra_layout_hgroup_begin",
        params=[],
        return_type="LONG",
        c_template="ra_layout_hgroup_begin()",
        needs_reaction=True,
        description="Begin horizontal layout group"
    ),
    "ra_layout_vgroup_begin": BuiltinFunc(
        name="ra_layout_vgroup_begin",
        params=[],
        return_type="LONG",
        c_template="ra_layout_vgroup_begin()",
        needs_reaction=True,
        description="Begin vertical layout group"
    ),
    "ra_layout_group_end": BuiltinFunc(
        name="ra_layout_group_end",
        params=[],
        return_type="LONG",
        c_template="ra_layout_group_end()",
        needs_reaction=True,
        description="End layout group"
    ),

    # Separators
    "ra_add_space": BuiltinFunc(
        name="ra_add_space",
        params=[],
        return_type="void",
        c_template="ra_add_space()",
        needs_reaction=True,
        description="Add horizontal separator"
    ),
    "ra_add_vspace": BuiltinFunc(
        name="ra_add_vspace",
        params=[],
        return_type="void",
        c_template="ra_add_vspace()",
        needs_reaction=True,
        description="Add vertical separator"
    ),

    # Weighted layout groups
    "ra_layout_hgroup_weighted": BuiltinFunc(
        name="ra_layout_hgroup_weighted",
        params=["weight"],
        return_type="LONG",
        c_template="ra_layout_hgroup_weighted(${weight})",
        needs_reaction=True,
        description="Begin horizontal layout group with weight hint"
    ),
    "ra_layout_vgroup_weighted": BuiltinFunc(
        name="ra_layout_vgroup_weighted",
        params=["weight"],
        return_type="LONG",
        c_template="ra_layout_vgroup_weighted(${weight})",
        needs_reaction=True,
        description="Begin vertical layout group with weight hint"
    ),
    "ra_layout_group_end_weighted": BuiltinFunc(
        name="ra_layout_group_end_weighted",
        params=[],
        return_type="LONG",
        c_template="ra_layout_group_end_weighted()",
        needs_reaction=True,
        description="End weighted layout group"
    ),

    # Drawing area
    "ra_add_drawing_area": BuiltinFunc(
        name="ra_add_drawing_area",
        params=["id", "min_width", "min_height"],
        return_type="LONG",
        c_template="ra_add_drawing_area(${id}, ${min_width}, ${min_height})",
        needs_reaction=True,
        description="Add Space gadget for custom drawing area"
    ),

    # Drawing area bounds
    "ra_get_drawing_bounds": BuiltinFunc(
        name="ra_get_drawing_bounds",
        params=["id"],
        return_type="LONG",
        c_template="ra_get_drawing_bounds(${id})",
        needs_reaction=True,
        description="Query Space gadget bounds (call after window open)"
    ),
    "ra_drawing_left": BuiltinFunc(
        name="ra_drawing_left",
        params=[],
        return_type="LONG",
        c_template="ra_drawing_left()",
        needs_reaction=True,
        description="Get drawing area left position"
    ),
    "ra_drawing_top": BuiltinFunc(
        name="ra_drawing_top",
        params=[],
        return_type="LONG",
        c_template="ra_drawing_top()",
        needs_reaction=True,
        description="Get drawing area top position"
    ),
    "ra_drawing_width": BuiltinFunc(
        name="ra_drawing_width",
        params=[],
        return_type="LONG",
        c_template="ra_drawing_width()",
        needs_reaction=True,
        description="Get drawing area width"
    ),
    "ra_drawing_height": BuiltinFunc(
        name="ra_drawing_height",
        params=[],
        return_type="LONG",
        c_template="ra_drawing_height()",
        needs_reaction=True,
        description="Get drawing area height"
    ),
    "ra_calc_drawing_area": BuiltinFunc(
        name="ra_calc_drawing_area",
        params=["toolbar_h", "timeline_h", "left_w", "right_w"],
        return_type="LONG",
        c_template="ra_calc_drawing_area(${toolbar_h}, ${timeline_h}, ${left_w}, ${right_w})",
        needs_reaction=True,
        description="Calculate drawing area from window dimensions (fallback)"
    ),
    "ra_refresh_canvas": BuiltinFunc(
        name="ra_refresh_canvas",
        params=["id"],
        return_type="void",
        c_template="ra_refresh_canvas(${id})",
        needs_reaction=True,
        description="Trigger canvas Space gadget refresh (calls render hook)"
    ),
    "ra_canvas_left": BuiltinFunc(
        name="ra_canvas_left",
        params=[],
        return_type="LONG",
        c_template="_ra_drawing_box.Left",
        needs_reaction=True,
        description="Get canvas left position from render hook"
    ),
    "ra_canvas_top": BuiltinFunc(
        name="ra_canvas_top",
        params=[],
        return_type="LONG",
        c_template="_ra_drawing_box.Top",
        needs_reaction=True,
        description="Get canvas top position from render hook"
    ),
    "ra_canvas_width": BuiltinFunc(
        name="ra_canvas_width",
        params=[],
        return_type="LONG",
        c_template="_ra_drawing_box.Width",
        needs_reaction=True,
        description="Get canvas width from render hook"
    ),
    "ra_canvas_height": BuiltinFunc(
        name="ra_canvas_height",
        params=[],
        return_type="LONG",
        c_template="_ra_drawing_box.Height",
        needs_reaction=True,
        description="Get canvas height from render hook"
    ),
    "ra_init_canvas_render": BuiltinFunc(
        name="ra_init_canvas_render",
        params=[],
        return_type="void",
        c_template="ra_init_canvas_render()",
        needs_reaction=True,
        description="Register render_canvas() as the canvas render callback"
    ),
    "ra_canvas_enable": BuiltinFunc(
        name="ra_canvas_enable",
        params=[],
        return_type="void",
        c_template="ra_canvas_enable()",
        needs_reaction=True,
        description="Enable canvas rendering (call after all init is done)"
    ),

    # Utility functions
    "ra_gadget_exists": BuiltinFunc(
        name="ra_gadget_exists",
        params=["id"],
        return_type="LONG",
        c_template="ra_gadget_exists(${id})",
        needs_reaction=True,
        description="Check if gadget exists"
    ),
    "ra_window_width": BuiltinFunc(
        name="ra_window_width",
        params=[],
        return_type="LONG",
        c_template="ra_window_width()",
        needs_reaction=True,
        description="Get window width"
    ),
    "ra_window_height": BuiltinFunc(
        name="ra_window_height",
        params=[],
        return_type="LONG",
        c_template="ra_window_height()",
        needs_reaction=True,
        description="Get window height"
    ),
    "ra_window_is_open": BuiltinFunc(
        name="ra_window_is_open",
        params=[],
        return_type="LONG",
        c_template="ra_window_is_open()",
        needs_reaction=True,
        description="Check if window is open"
    ),
    "ra_add_listbrowser": BuiltinFunc(
        name="ra_add_listbrowser",
        params=["id"],
        return_type="LONG",
        c_template="ra_add_listbrowser(${id})",
        needs_reaction=True,
        description="Add a list of text lines (value: selected line, -1 none)"
    ),
    "ra_listbrowser_add": BuiltinFunc(
        name="ra_listbrowser_add",
        params=["id", "text"],
        return_type="LONG",
        c_template="ra_listbrowser_add(${id}, ${text})",
        needs_reaction=True,
        description="Add a line at the end of a listbrowser"
    ),
    "ra_listbrowser_clear": BuiltinFunc(
        name="ra_listbrowser_clear",
        params=["id"],
        return_type="void",
        c_template="ra_listbrowser_clear(${id})",
        needs_reaction=True,
        description="Remove all lines of a listbrowser"
    ),
    "ra_listbrowser_count": BuiltinFunc(
        name="ra_listbrowser_count",
        params=["id"],
        return_type="LONG",
        c_template="ra_listbrowser_count(${id})",
        needs_reaction=True,
        description="Number of lines of a listbrowser"
    ),
    "ra_add_radio": BuiltinFunc(
        name="ra_add_radio",
        params=["id", "options"],
        return_type="LONG",
        c_template="ra_add_radio(${id}, ${options})",
        needs_reaction=True,
        description="Add radio buttons, options separated by | (value: option)"
    ),
    "ra_add_clicktab": BuiltinFunc(
        name="ra_add_clicktab",
        params=["id", "titles"],
        return_type="LONG",
        c_template="ra_add_clicktab(${id}, ${titles})",
        needs_reaction=True,
        description="Add tabs, titles separated by | (value: tab, from 0)"
    ),
    "ra_add_fuelgauge": BuiltinFunc(
        name="ra_add_fuelgauge",
        params=["id", "max"],
        return_type="LONG",
        c_template="ra_add_fuelgauge(${id}, ${max})",
        needs_reaction=True,
        description="Add a progress bar from 0 to max (value: level)"
    ),
    "ra_menu_title": BuiltinFunc(
        name="ra_menu_title",
        params=["label"],
        return_type="void",
        c_template="ra_menu_title(${label})",
        needs_reaction=True,
        description="Add a menu to the ReAction window (before ra_window_open)"
    ),
    "ra_menu_item": BuiltinFunc(
        name="ra_menu_item",
        params=["label", "key", "id"],
        return_type="void",
        c_template="ra_menu_item(${label}, ${key}, ${id})",
        needs_reaction=True,
        description="Add a menu item: key = letter for Amiga+key (\"\" none); events: RA_EVENT_MENU() and ra_menu_id()"
    ),
    "ra_menu_separator": BuiltinFunc(
        name="ra_menu_separator",
        params=[],
        return_type="void",
        c_template="ra_menu_separator()",
        needs_reaction=True,
        description="Add a separator line to the menu"
    ),
    "ra_menu_id": BuiltinFunc(
        name="ra_menu_id",
        params=[],
        return_type="LONG",
        c_template="ra_menu_id()",
        needs_reaction=True,
        description="Id of the menu item of the last RA_EVENT_MENU()"
    ),
    "RA_EVENT_MENU": BuiltinFunc(
        name="RA_EVENT_MENU",
        params=[],
        return_type="LONG",
        c_template="RA_EVENT_MENU",
        needs_reaction=True,
        description="Event: a menu item was chosen (ra_menu_id)"
    ),
    "ra_add_getfile": BuiltinFunc(
        name="ra_add_getfile",
        params=["id", "title"],
        return_type="LONG",
        c_template="ra_add_getfile(${id}, ${title})",
        needs_reaction=True,
        description="Add a button that opens a file requester; ra_get_string(id) gives the file chosen"
    ),
}


# =============================================================================
# SYSTEM - Memory, Time, Random (10 functions)
# =============================================================================

SYSTEM_FUNCTIONS = {
    # Debugging: in UAE (FS-UAE, WinUAE) the emulated machine stops in the emulator's debugger
    # (uaelib function 15 at $F0FF60, see tools/emu_run.py --debug); on a real Amiga, or in
    # UAE without its boot ROM, nothing happens: $F0FF60 is only read once uae.resource exists.
    "debug_break": BuiltinFunc(
        name="debug_break",
        params=[],
        return_type="void",
        c_template="({ if (OpenResource((CONST_STRPTR)\"uae.resource\") && "
                   "(*(volatile UWORD *)0xF0FF60 & 0xF000) == 0xA000 && *(volatile UWORD *)0xF0FF62 == 0x4E75) "
                   "((ULONG (*)(ULONG))0xF0FF60)(15); })",
        description="Stop in the UAE emulator's debugger (nothing on a real Amiga; tools/emu_run.py --debug)"
    ),
    # Memory
    "mem_chip_free": BuiltinFunc(
        name="mem_chip_free",
        params=[],
        return_type="LONG",
        c_template="AvailMem(MEMF_CHIP)",
        description="Available chip RAM"
    ),
    "mem_fast_free": BuiltinFunc(
        name="mem_fast_free",
        params=[],
        return_type="LONG",
        c_template="AvailMem(MEMF_FAST)",
        description="Available fast RAM"
    ),
    "mem_total": BuiltinFunc(
        name="mem_total",
        params=[],
        return_type="LONG",
        c_template="AvailMem(MEMF_ANY)",
        description="Free memory, chip and fast (what is available: not the size of the RAM)"
    ),
    "mem_chip_total": BuiltinFunc(
        name="mem_chip_total",
        params=[],
        return_type="LONG",
        c_template="AvailMem(MEMF_CHIP | MEMF_TOTAL)",
        description="Size of the chip RAM, in bytes (free and in use: AvailMem with MEMF_TOTAL)"
    ),
    "mem_fast_total": BuiltinFunc(
        name="mem_fast_total",
        params=[],
        return_type="LONG",
        c_template="AvailMem(MEMF_FAST | MEMF_TOTAL)",
        description="Size of the fast RAM, in bytes (free and in use: AvailMem with MEMF_TOTAL)"
    ),
    "peek_byte": BuiltinFunc(
        name="peek_byte",
        params=["addr"],
        return_type="LONG",
        c_template="(*((UBYTE *)(_DashUP)(ULONG)(${addr})))",
        description="Read byte from memory address"
    ),
    "peek_word": BuiltinFunc(
        name="peek_word",
        params=["addr"],
        return_type="LONG",
        c_template="(*((UWORD *)(_DashUP)(ULONG)(${addr})))",
        description="Read word from memory address"
    ),
    "peek_long": BuiltinFunc(
        name="peek_long",
        params=["addr"],
        return_type="LONG",
        c_template="(*((ULONG *)(_DashUP)(ULONG)(${addr})))",
        description="Read long from memory address"
    ),
    "poke_byte": BuiltinFunc(
        name="poke_byte",
        params=["addr", "value"],
        return_type="void",
        c_template="*((UBYTE *)(_DashUP)(ULONG)(${addr})) = (UBYTE)(${value})",
        description="Write byte to memory address"
    ),
    "poke_word": BuiltinFunc(
        name="poke_word",
        params=["addr", "value"],
        return_type="void",
        c_template="*((UWORD *)(_DashUP)(ULONG)(${addr})) = (UWORD)(${value})",
        description="Write word to memory address"
    ),
    # @amiga struct (docs/AARCH64_LOOP.md, A6): memory for the structures of AmigaOS (on DashOS, of its Amiga box,
    # below 4 GB)
    "amiga_alloc": BuiltinFunc(
        name="amiga_alloc",
        params=["size"],
        return_type="LONG",
        c_template="_DASH_AMIGA_ALLOC(${size})",
        description="size bytes for AmigaOS structures (@amiga struct), cleared: AllocMem(MEMF_PUBLIC | MEMF_CLEAR) "
                    "on the Amiga, memory of the Amiga box (below 4 GB) on DashOS; 0 without memory"
    ),
    "amiga_free": BuiltinFunc(
        name="amiga_free",
        params=["addr", "size"],
        return_type="void",
        c_template="_DASH_AMIGA_FREE(${addr}, ${size})",
        description="Gives back what amiga_alloc gave (with the same size)"
    ),
    "poke_long": BuiltinFunc(
        name="poke_long",
        params=["addr", "value"],
        return_type="void",
        c_template="*((ULONG *)(_DashUP)(ULONG)(${addr})) = (ULONG)(${value})",
        description="Write long to memory address"
    ),

    # Time
    "time_delay": BuiltinFunc(
        name="time_delay",
        params=["ticks"],
        return_type="void",
        c_template="Delay(${ticks})",
        needs_dos=True,
        description="Delay in ticks (50 per second)"
    ),
    "time_delay_ms": BuiltinFunc(
        name="time_delay_ms",
        params=["ms"],
        return_type="void",
        c_template="Delay((${ms}) / 20)",
        needs_dos=True,
        description="Delay in milliseconds"
    ),

    # Random
    "random": BuiltinFunc(
        name="random",
        params=[],
        return_type="LONG",
        c_template="_dash_random()",
        description="Random number"
    ),
    "random_range": BuiltinFunc(
        name="random_range",
        params=["min", "max"],
        return_type="LONG",
        c_template="((${min}) + (_dash_random() % ((${max}) - (${min}) + 1)))",
        description="Random in range [min, max]"
    ),
    "random_seed": BuiltinFunc(
        name="random_seed",
        params=["seed"],
        return_type="void",
        c_template="_dash_random_seed = ${seed}",
        description="Set random seed"
    ),

    # Sync
    "wait_vblank": BuiltinFunc(
        name="wait_vblank",
        params=[],
        return_type="void",
        c_template="WaitTOF()",
        needs_gfx=True,
        description="Wait for vertical blank"
    ),
    "wait_blit": BuiltinFunc(
        name="wait_blit",
        params=[],
        return_type="void",
        c_template="WaitBlit()",
        needs_gfx=True,
        description="Wait for blitter"
    ),

    # Arena Allocator
    "arena_new": BuiltinFunc(
        name="arena_new",
        params=["size"],
        return_type="LONG",
        c_template="(LONG)_dash_arena_new(${size})",
        description="Create arena allocator with given size in bytes"
    ),
    "arena_alloc": BuiltinFunc(
        name="arena_alloc",
        params=["arena", "size"],
        return_type="LONG",
        c_template="(LONG)_dash_arena_alloc((_Dash_Arena *)(${arena}), ${size})",
        description="Allocate from arena (fast bump allocator)"
    ),
    "arena_reset": BuiltinFunc(
        name="arena_reset",
        params=["arena"],
        return_type="void",
        c_template="_dash_arena_reset((_Dash_Arena *)(${arena}))",
        description="Reset arena (reuse memory without freeing)"
    ),
    "arena_free": BuiltinFunc(
        name="arena_free",
        params=["arena"],
        return_type="void",
        c_template="_dash_arena_free((_Dash_Arena *)(${arena}))",
        description="Free arena and all its memory"
    ),
    "arena_used": BuiltinFunc(
        name="arena_used",
        params=["arena"],
        return_type="LONG",
        c_template="_dash_arena_used((_Dash_Arena *)(${arena}))",
        description="Get bytes used in arena"
    ),
    "arena_available": BuiltinFunc(
        name="arena_available",
        params=["arena"],
        return_type="LONG",
        c_template="_dash_arena_available((_Dash_Arena *)(${arena}))",
        description="Get bytes available in arena"
    ),

    # Reference Counting utilities
    "refcount": BuiltinFunc(
        name="refcount",
        params=["obj"],
        return_type="LONG",
        c_template="_dash_refcount((void *)(${obj}))",
        description="Get reference count of object"
    ),
    "retain": BuiltinFunc(
        name="retain",
        params=["obj"],
        return_type="void",
        c_template="_dash_retain((void *)(${obj}))",
        description="Manually increment reference count"
    ),
    "release": BuiltinFunc(
        name="release",
        params=["obj"],
        return_type="void",
        c_template="_dash_release((void *)(${obj}))",
        description="Manually decrement reference count (frees if 0)"
    ),
    # Tachyon D80: memory back to the system
    "mem_trim": BuiltinFunc(
        name="mem_trim",
        params=[],
        return_type="LONG",
        c_template="_dash_mem_trim()",
        description="Give the slabs of small blocks (up to 128 bytes) that are all free back to the system; bytes given back"
    ),
    "mem_puddle": BuiltinFunc(
        name="mem_puddle",
        params=["bytes"],
        return_type="BOOL",
        c_template="_dash_mem_puddle(${bytes})",
        description="Size of the memory pool's puddles (1 KB to 1 MB, 4 KB by default); only before the first allocation"
    ),
}


# =============================================================================
# DOS - File Operations (22 functions)
# =============================================================================

DOS_FUNCTIONS = {
    # File Open/Close
    "file_open": BuiltinFunc(
        name="file_open",
        params=["filename", "mode"],
        return_type="LONG",
        c_template="Open(${filename}, ${mode})",
        needs_dos=True,
        description="Open file (mode: 1005 read, 1006 new file, 1004 read and write; 0 if it fails)"
    ),
    "file_close": BuiltinFunc(
        name="file_close",
        params=["handle"],
        return_type="void",
        c_template="Close(${handle})",
        needs_dos=True,
        description="Close file"
    ),

    # Reading
    "file_read_byte": BuiltinFunc(
        name="file_read_byte",
        params=["handle"],
        return_type="LONG",
        c_template="FGetC(${handle})",
        needs_dos=True,
        description="Read single byte"
    ),
    "file_read_line": BuiltinFunc(
        name="file_read_line",
        params=["handle", "buffer", "maxlen"],
        return_type="STRPTR",
        c_template="FGets(${handle}, ${buffer}, ${maxlen})",
        needs_dos=True,
        description="Read line into buffer"
    ),
    "file_read": BuiltinFunc(
        name="file_read",
        params=["handle", "buffer", "length"],
        return_type="LONG",
        c_template="Read(${handle}, ${buffer}, ${length})",
        needs_dos=True,
        description="Read bytes into buffer"
    ),
    "file_eof": BuiltinFunc(
        name="file_eof",
        params=["handle"],
        return_type="BOOL",
        c_template="({ BPTR _fh = (BPTR)(${handle}); LONG _c = FGetC(_fh); _c == -1 ? TRUE : (UnGetC(_fh, _c), FALSE); })",
        needs_dos=True,
        description="True at the end of the file (looks at the next byte without consuming it)"
    ),

    # Writing
    "file_write_byte": BuiltinFunc(
        name="file_write_byte",
        params=["handle", "byte"],
        return_type="LONG",
        c_template="FPutC(${handle}, ${byte})",
        needs_dos=True,
        description="Write single byte"
    ),
    "file_write_line": BuiltinFunc(
        name="file_write_line",
        params=["handle", "str"],
        return_type="LONG",
        c_template="({ BPTR _fh = (BPTR)(${handle}); FPuts(_fh, ${str}) ? -1L : (FPutC(_fh, '\\n') < 0 ? -1L : 0L); })",
        needs_dos=True,
        description="Write string followed by a newline (0 = ok, -1 = error)"
    ),
    "file_write": BuiltinFunc(
        name="file_write",
        params=["handle", "buffer", "length"],
        return_type="LONG",
        c_template="Write(${handle}, ${buffer}, ${length})",
        needs_dos=True,
        description="Write bytes from buffer"
    ),
    "file_print": BuiltinFunc(
        name="file_print",
        params=["handle", "str"],
        return_type="void",
        c_template="FPuts(${handle}, ${str})",
        needs_dos=True,
        description="Print string to file"
    ),

    # Position
    "file_seek": BuiltinFunc(
        name="file_seek",
        params=["handle", "position", "mode"],
        return_type="LONG",
        c_template="Seek(${handle}, ${position}, ${mode})",
        needs_dos=True,
        description="Seek in file (mode: OFFSET_BEGINNING, OFFSET_CURRENT, OFFSET_END)"
    ),
    "file_pos": BuiltinFunc(
        name="file_pos",
        params=["handle"],
        return_type="LONG",
        c_template="Seek(${handle}, 0, OFFSET_CURRENT)",
        needs_dos=True,
        description="Get current position"
    ),
    "file_size": BuiltinFunc(
        name="file_size",
        params=["filename"],
        return_type="LONG",
        c_template="_dash_file_size(${filename})",
        needs_fileio=True,
        description="Get file size"
    ),

    # File System
    "file_exists": BuiltinFunc(
        name="file_exists",
        params=["filename"],
        return_type="BOOL",
        c_template="_dash_file_exists(${filename})",
        needs_fileio=True,
        description="Check if file exists"
    ),
    "file_delete": BuiltinFunc(
        name="file_delete",
        params=["filename"],
        return_type="BOOL",
        c_template="DeleteFile(${filename})",
        needs_dos=True,
        description="Delete file"
    ),
    "file_rename": BuiltinFunc(
        name="file_rename",
        params=["oldname", "newname"],
        return_type="BOOL",
        c_template="Rename(${oldname}, ${newname})",
        needs_dos=True,
        description="Rename file"
    ),
    "file_copy": BuiltinFunc(
        name="file_copy",
        params=["src", "dest"],
        return_type="BOOL",
        c_template="_dash_file_copy(${src}, ${dest})",
        needs_fileio=True,
        reads_only=True, description="Copy file"
    ),

    # Directories
    "dir_create": BuiltinFunc(
        name="dir_create",
        params=["path"],
        return_type="BOOL",
        c_template="_dash_dir_create(${path})",
        needs_dos=True,
        description="Create directory"
    ),
    "dir_change": BuiltinFunc(
        name="dir_change",
        params=["path"],
        return_type="BOOL",
        c_template="_dash_dir_change(${path})",
        needs_dos=True,
        reads_only=True, description="Change current directory"
    ),
    "dir_current": BuiltinFunc(
        name="dir_current",
        params=[],
        return_type="STRPTR",
        c_template="_dash_dir_current()",
        needs_dos=True,
        description="Full name of the current directory (\"Ram Disk:\" ...)"
    ),
    # Dash 2.0 (Inferencia, the IDE): what a directory holds
    "dir_read": BuiltinFunc(
        name="dir_read", params=["path"], return_type="LONG", c_template="_dash_dir_read(${path})",
        needs_dos=True, reads_only=True,
        description="Read what a directory holds, sorted by name (case does not count): the number of entries, "
                    "-1 if it is not a directory that can be read. dir_entry_name and the others read them, until "
                    "the next dir_read"),
    "dir_entry_name": BuiltinFunc(
        name="dir_entry_name", params=["i"], return_type="STRPTR", c_template="_dash_dir_entry_name(${i})",
        needs_dos=True, description="Name of entry i (from 0) of the last dir_read; \"\" past the end"),
    "dir_entry_size": BuiltinFunc(
        name="dir_entry_size", params=["i"], return_type="LONG", c_template="_dash_dir_entry_size(${i})",
        needs_dos=True, description="Size in bytes of entry i of the last dir_read (0 for a directory)"),
    "dir_entry_is_dir": BuiltinFunc(
        name="dir_entry_is_dir", params=["i"], return_type="BOOL", c_template="_dash_dir_entry_is_dir(${i})",
        needs_dos=True, description="True if entry i of the last dir_read is a directory"),
    "dir_entry_date": BuiltinFunc(
        name="dir_entry_date", params=["i"], return_type="LONG", c_template="_dash_dir_entry_date(${i})",
        needs_dos=True,
        description="Date of entry i of the last dir_read, as time_unix: seconds since 1 January 1970"),

    # Console I/O
    "console_read": BuiltinFunc(
        name="console_read",
        params=["buffer", "maxlen"],
        return_type="LONG",
        c_template="Read(Input(), ${buffer}, ${maxlen})",
        needs_dos=True,
        description="Read from console"
    ),
    "console_write": BuiltinFunc(
        name="console_write",
        params=["str"],
        return_type="void",
        c_template="Write(Output(), ${str}, strlen(${str}))",
        needs_dos=True,
        description="Write to console"
    ),

    # Binary File Operations
    "file_load": BuiltinFunc(
        name="file_load",
        params=["filename", "buffer", "maxsize"],
        return_type="LONG",
        c_template="_dash_file_load(${filename}, ${buffer}, ${maxsize})",
        needs_fileio=True,
        description="Load entire file into buffer, returns bytes read or -1"
    ),
    "file_save": BuiltinFunc(
        name="file_save",
        params=["filename", "buffer", "size"],
        return_type="LONG",
        c_template="_dash_file_save(${filename}, ${buffer}, ${size})",
        needs_fileio=True,
        description="Save buffer to file, returns bytes written"
    ),
}

# =============================================================================
# BUFFER - Memory Buffer Operations (12 functions)
# =============================================================================

BUFFER_FUNCTIONS = {
    # Buffer Allocation
    "buffer_alloc": BuiltinFunc(
        name="buffer_alloc",
        params=["size"],
        return_type="APTR",
        c_template="_dash_alloc_buffer(${size})",
        needs_fileio=True,
        description="Allocate memory buffer"
    ),
    "buffer_free": BuiltinFunc(
        name="buffer_free",
        params=["buffer"],
        return_type="void",
        c_template="_dash_free_buffer(${buffer})",
        needs_fileio=True,
        description="Free memory buffer"
    ),

    # Byte Access
    "buffer_get_byte": BuiltinFunc(
        name="buffer_get_byte",
        params=["buffer", "offset"],
        return_type="LONG",
        c_template="_dash_buffer_get_byte(${buffer}, ${offset})",
        needs_fileio=True,
        description="Get byte at offset"
    ),
    "buffer_set_byte": BuiltinFunc(
        name="buffer_set_byte",
        params=["buffer", "offset", "value"],
        return_type="void",
        c_template="_dash_buffer_set_byte(${buffer}, ${offset}, ${value})",
        needs_fileio=True,
        description="Set byte at offset"
    ),

    # Word Access (16-bit, big-endian)
    "buffer_get_word": BuiltinFunc(
        name="buffer_get_word",
        params=["buffer", "offset"],
        return_type="LONG",
        c_template="_dash_buffer_get_word(${buffer}, ${offset})",
        needs_fileio=True,
        description="Get 16-bit word at offset (big-endian)"
    ),
    "buffer_set_word": BuiltinFunc(
        name="buffer_set_word",
        params=["buffer", "offset", "value"],
        return_type="void",
        c_template="_dash_buffer_set_word(${buffer}, ${offset}, ${value})",
        needs_fileio=True,
        description="Set 16-bit word at offset (big-endian)"
    ),

    # Long Access (32-bit, big-endian)
    "buffer_get_long": BuiltinFunc(
        name="buffer_get_long",
        params=["buffer", "offset"],
        return_type="LONG",
        c_template="_dash_buffer_get_long(${buffer}, ${offset})",
        needs_fileio=True,
        description="Get 32-bit long at offset (big-endian)"
    ),
    "buffer_set_long": BuiltinFunc(
        name="buffer_set_long",
        params=["buffer", "offset", "value"],
        return_type="void",
        c_template="_dash_buffer_set_long(${buffer}, ${offset}, ${value})",
        needs_fileio=True,
        description="Set 32-bit long at offset (big-endian)"
    ),

    # Buffer Operations
    "buffer_copy": BuiltinFunc(
        name="buffer_copy",
        params=["dest", "dest_offset", "src", "src_offset", "length"],
        return_type="void",
        c_template="_dash_buffer_copy(${dest}, ${dest_offset}, ${src}, ${src_offset}, ${length})",
        needs_fileio=True,
        description="Copy bytes between buffers"
    ),
    "buffer_fill": BuiltinFunc(
        name="buffer_fill",
        params=["buffer", "offset", "length", "value"],
        return_type="void",
        c_template="_dash_buffer_fill(${buffer}, ${offset}, ${length}, ${value})",
        needs_fileio=True,
        description="Fill buffer region with byte value"
    ),
}


# =============================================================================
# AUDIO - Sound and Music (18 functions)
# =============================================================================

AUDIO_FUNCTIONS = {
    # Sound Loading
    "sound_load": BuiltinFunc(
        name="sound_load",
        params=["id", "filename"],
        return_type="BOOL",
        c_template="_dash_sound_load(${id}, ${filename})",
        needs_audio=True,
        reads_only=True, description="Load an IFF 8SVX sound (uncompressed)"
    ),
    "sound_sample": BuiltinFunc(
        name="sound_sample",
        params=["id", "index", "value"],
        return_type="void",
        c_template="_dash_sound_sample(${id}, ${index}, ${value})",
        needs_audio=True,
        description="Set one sample (-128..127) of a sound made with sound_create"
    ),
    "sound_create": BuiltinFunc(
        name="sound_create",
        params=["id", "length", "rate"],
        return_type="BOOL",
        c_template="_dash_sound_create(${id}, ${length}, ${rate})",
        needs_audio=True,
        description="Create a silent sound in chip memory: length in samples, rate in samples per second"
    ),
    "sound_free": BuiltinFunc(
        name="sound_free",
        params=["id"],
        return_type="void",
        c_template="_dash_sound_free(${id})",
        needs_audio=True,
        description="Free sound memory"
    ),

    # Playback
    "sound_play": BuiltinFunc(
        name="sound_play",
        params=["id", "channel"],
        return_type="void",
        c_template="_dash_sound_play(${id}, ${channel})",
        needs_audio=True,
        description="Play a sound once on a channel (0-3)"
    ),
    "sound_stop": BuiltinFunc(
        name="sound_stop",
        params=["channel"],
        return_type="void",
        c_template="_dash_sound_stop(${channel})",
        needs_audio=True,
        description="Stop channel"
    ),
    "sound_loop": BuiltinFunc(
        name="sound_loop",
        params=["id", "channel"],
        return_type="void",
        c_template="_dash_sound_loop(${id}, ${channel})",
        needs_audio=True,
        description="Play a sound looped on a channel (until sound_stop)"
    ),
    "sound_playing": BuiltinFunc(
        name="sound_playing",
        params=["channel"],
        return_type="BOOL",
        c_template="_dash_sound_playing(${channel})",
        needs_audio=True,
        description="Check if channel is playing"
    ),

    # Channel Control
    "sound_volume": BuiltinFunc(
        name="sound_volume",
        params=["channel", "vol"],
        return_type="void",
        c_template="_dash_sound_volume(${channel}, ${vol})",
        needs_audio=True,
        description="Set channel volume (0-64)"
    ),
    "sound_period": BuiltinFunc(
        name="sound_period",
        params=["channel", "period"],
        return_type="void",
        c_template="_dash_sound_period(${channel}, ${period})",
        needs_audio=True,
        description="Set the channel period (pitch: lower = higher)"
    ),

    # Music (MOD/ProTracker)
    "music_load": BuiltinFunc(
        name="music_load",
        params=["filename"],
        return_type="BOOL",
        c_template="_dash_music_load(${filename})",
        needs_audio=True,
        reads_only=True, description="Load MOD file"
    ),
    "music_play": BuiltinFunc(
        name="music_play",
        params=[],
        return_type="void",
        c_template="_dash_music_play()",
        needs_audio=True,
        description="Start music playback"
    ),
    "music_stop": BuiltinFunc(
        name="music_stop",
        params=[],
        return_type="void",
        c_template="_dash_music_stop()",
        needs_audio=True,
        description="Stop music"
    ),
    "music_pause": BuiltinFunc(
        name="music_pause",
        params=[],
        return_type="void",
        c_template="_dash_music_pause()",
        needs_audio=True,
        description="Pause music"
    ),
    "music_resume": BuiltinFunc(
        name="music_resume",
        params=[],
        return_type="void",
        c_template="_dash_music_resume()",
        needs_audio=True,
        description="Resume music"
    ),
    "music_volume": BuiltinFunc(
        name="music_volume",
        params=["vol"],
        return_type="void",
        c_template="_dash_music_volume(${vol})",
        needs_audio=True,
        description="Set music volume (0-64)"
    ),
    "music_position": BuiltinFunc(
        name="music_position",
        params=["pos"],
        return_type="void",
        c_template="_dash_music_position(${pos})",
        needs_audio=True,
        description="Set music position"
    ),
    "music_pos": BuiltinFunc(
        name="music_pos",
        params=[],
        return_type="LONG",
        c_template="_dash_music_pos()",
        needs_audio=True,
        description="Song position the music is playing (index in the order list)"
    ),
    "music_row": BuiltinFunc(
        name="music_row",
        params=[],
        return_type="LONG",
        c_template="_dash_music_row()",
        needs_audio=True,
        description="Pattern row the music is playing (0-63)"
    ),
    "music_free": BuiltinFunc(
        name="music_free",
        params=[],
        return_type="void",
        c_template="_dash_music_free()",
        needs_audio=True,
        description="Free music data"
    ),

    # Synthesis
    "tone_play": BuiltinFunc(
        name="tone_play",
        params=["channel", "freq", "vol", "duration"],
        return_type="void",
        c_template="_dash_tone_play(${channel}, ${freq}, ${vol}, ${duration})",
        needs_audio=True,
        description="Play a sine tone: frequency in Hz, volume 0-64, duration in milliseconds (returns at once)"
    ),
}


# =============================================================================
# INTUITION - UI Components (35 functions)
# =============================================================================

INTUITION_EXPANDED = {
    # Windows
    "window_create": BuiltinFunc(
        name="window_create",
        params=["title", "x", "y", "w", "h", "flags"],
        return_type="LONG",
        c_template="_dash_window_create(${title}, ${x}, ${y}, ${w}, ${h}, ${flags})",
        description="Open a window, returns its handle 1..16 (0 = failed); flags: 1 resizable, 2 borderless, 4 no close gadget, 8 w and h are the inside (without the borders). It becomes the current window"
    ),
    "window_border_top": BuiltinFunc(
        name="window_border_top", params=[], return_type="LONG", c_template="_dash_window_border(0)",
        description="The top border of the current window (title bar included); gadgets count from the inside, "
                    "without it"),
    "window_border_bottom": BuiltinFunc(
        name="window_border_bottom", params=[], return_type="LONG", c_template="_dash_window_border(1)",
        description="The bottom border of the current window"),
    "window_border_left": BuiltinFunc(
        name="window_border_left", params=[], return_type="LONG", c_template="_dash_window_border(2)",
        description="The left border of the current window"),
    "window_border_right": BuiltinFunc(
        name="window_border_right", params=[], return_type="LONG", c_template="_dash_window_border(3)",
        description="The right border of the current window"),
    "screen_font_height": BuiltinFunc(
        name="screen_font_height", params=[], return_type="LONG", c_template="_dash_screen_font_height()",
        description="The height of the screen's font (the program's screen, or the Workbench's): the one of title "
                    "bars and of GadTools gadgets"),
    "screen_font_text_width": BuiltinFunc(
        name="screen_font_text_width", params=["text"], return_type="LONG",
        c_template="_dash_screen_font_text_width(${text})",
        reads_only=True, description="The width of a text in the screen's font"),
    "window_close": BuiltinFunc(
        name="window_close",
        params=["handle"],
        return_type="void",
        c_template="_dash_window_close(${handle})",
        description="Close window (handle 0: current window)"
    ),
    "window_title": BuiltinFunc(
        name="window_title",
        params=["handle", "title"],
        return_type="void",
        c_template="_dash_window_title(${handle}, ${title})",
        description="Set window title (handle 0: current window)"
    ),
    "window_move": BuiltinFunc(
        name="window_move",
        params=["handle", "x", "y"],
        return_type="void",
        c_template="_dash_window_move(${handle}, ${x}, ${y})",
        description="Move window to x, y (absolute; handle 0: current window)"
    ),
    "window_resize": BuiltinFunc(
        name="window_resize",
        params=["handle", "w", "h"],
        return_type="void",
        c_template="_dash_window_resize(${handle}, ${w}, ${h})",
        description="Resize window to w x h (handle 0: current window)"
    ),
    "window_to_front": BuiltinFunc(
        name="window_to_front",
        params=["handle"],
        return_type="void",
        c_template="_dash_window_to_front(${handle})",
        description="Bring window to front (handle 0: current window)"
    ),
    "window_to_back": BuiltinFunc(
        name="window_to_back",
        params=["handle"],
        return_type="void",
        c_template="_dash_window_to_back(${handle})",
        description="Send window to back (handle 0: current window)"
    ),
    "window_activate": BuiltinFunc(
        name="window_activate",
        params=["handle"],
        return_type="void",
        c_template="_dash_window_activate(${handle})",
        description="Activate window (handle 0: current window)"
    ),
    "window_use": BuiltinFunc(
        name="window_use", params=["handle"], return_type="BOOL", c_template="_dash_window_use(${handle})",
        description="Makes a window the current one, the one gfx_ draws in: a handle of window_create, or 0 the "
                    "declared window (Window X ... end) opened last; false if it is not open"),

    # Screens (legacy - use screen_open/screen_close from INPUT_FUNCTIONS instead)
    "screen_to_front": BuiltinFunc(
        name="screen_to_front",
        params=[],
        return_type="void",
        c_template="if (_dash_screen) ScreenToFront(_dash_screen)",
        description="Bring custom screen to front"
    ),
    "screen_to_back": BuiltinFunc(
        name="screen_to_back",
        params=[],
        return_type="void",
        c_template="if (_dash_screen) ScreenToBack(_dash_screen)",
        description="Send custom screen to back"
    ),

    # Gadgets - Buttons
    "gadget_id": BuiltinFunc(
        name="gadget_id",
        params=[],
        return_type="LONG",
        c_template="_dash_gadget_id()",
        needs_gadtools=True,
        description="Handle of the last gadget used (for On Gadget in the EventLoop)"
    ),
    "gadget_width": BuiltinFunc(
        name="gadget_width",
        params=["gadget"],
        return_type="LONG",
        c_template="_dash_gadget_width(${gadget})",
        needs_gadtools=True,
        description="Width of a gadget in pixels (also when it was created with width 0)"
    ),
    "gadget_height": BuiltinFunc(
        name="gadget_height",
        params=["gadget"],
        return_type="LONG",
        c_template="_dash_gadget_height(${gadget})",
        needs_gadtools=True,
        description="Height of a gadget in pixels (also when it was created with height 0)"
    ),
    "button_create": BuiltinFunc(
        name="button_create",
        params=["win", "x", "y", "w", "h", "label"],
        return_type="LONG",
        c_template="_dash_button_create(${win}, ${x}, ${y}, ${w}, ${h}, ${label})",
        needs_gadtools=True,
        description="Create button gadget"
    ),
    "button_enable": BuiltinFunc(
        name="button_enable",
        params=["gad"],
        return_type="void",
        c_template="_dash_gadget_enable(${gad})",
        needs_gadtools=True,
        description="Enable button"
    ),
    "button_disable": BuiltinFunc(
        name="button_disable",
        params=["gad"],
        return_type="void",
        c_template="_dash_gadget_disable(${gad})",
        needs_gadtools=True,
        description="Disable button"
    ),

    # Gadgets - Text Input
    "textfield_create": BuiltinFunc(
        name="textfield_create",
        params=["win", "x", "y", "w", "h", "maxlen"],
        return_type="LONG",
        c_template="_dash_textfield_create(${win}, ${x}, ${y}, ${w}, ${h}, ${maxlen})",
        needs_gadtools=True,
        description="Create text input field"
    ),
    "textfield_get": BuiltinFunc(
        name="textfield_get",
        params=["gad"],
        return_type="STRPTR",
        c_template="_dash_textfield_get(${gad})",
        needs_gadtools=True,
        description="Get text field content"
    ),
    "textfield_set": BuiltinFunc(
        name="textfield_set",
        params=["gad", "text"],
        return_type="void",
        c_template="_dash_textfield_set(${gad}, ${text})",
        needs_gadtools=True,
        description="Set text field content"
    ),

    # Gadgets - Checkbox
    "checkbox_create": BuiltinFunc(
        name="checkbox_create",
        params=["win", "x", "y", "label"],
        return_type="LONG",
        c_template="_dash_checkbox_create(${win}, ${x}, ${y}, ${label})",
        needs_gadtools=True,
        description="Create checkbox"
    ),
    "checkbox_get": BuiltinFunc(
        name="checkbox_get",
        params=["gad"],
        return_type="BOOL",
        c_template="_dash_checkbox_get(${gad})",
        needs_gadtools=True,
        description="Get checkbox state"
    ),
    "checkbox_set": BuiltinFunc(
        name="checkbox_set",
        params=["gad", "state"],
        return_type="void",
        c_template="_dash_checkbox_set(${gad}, ${state})",
        needs_gadtools=True,
        description="Set checkbox state"
    ),

    # Gadgets - Slider
    "slider_create": BuiltinFunc(
        name="slider_create",
        params=["win", "x", "y", "w", "h", "min", "max", "value"],
        return_type="LONG",
        c_template="_dash_slider_create(${win}, ${x}, ${y}, ${w}, ${h}, ${min}, ${max}, ${value})",
        needs_gadtools=True,
        description="Create slider"
    ),
    "slider_get": BuiltinFunc(
        name="slider_get",
        params=["gad"],
        return_type="LONG",
        c_template="_dash_slider_get(${gad})",
        needs_gadtools=True,
        description="Get slider value"
    ),
    "slider_set": BuiltinFunc(
        name="slider_set",
        params=["gad", "value"],
        return_type="void",
        c_template="_dash_slider_set(${gad}, ${value})",
        needs_gadtools=True,
        description="Set slider value"
    ),

    # Gadgets - Listview
    "listview_create": BuiltinFunc(
        name="listview_create",
        params=["win", "x", "y", "w", "h"],
        return_type="LONG",
        c_template="_dash_listview_create(${win}, ${x}, ${y}, ${w}, ${h})",
        needs_gadtools=True,
        description="Create listview"
    ),
    "listview_add": BuiltinFunc(
        name="listview_add",
        params=["gad", "text"],
        return_type="void",
        c_template="_dash_listview_add(${gad}, ${text})",
        needs_gadtools=True,
        description="Add item to listview"
    ),
    "listview_clear": BuiltinFunc(
        name="listview_clear",
        params=["gad"],
        return_type="void",
        c_template="_dash_listview_clear(${gad})",
        needs_gadtools=True,
        description="Clear listview"
    ),
    "listview_selected": BuiltinFunc(
        name="listview_selected",
        params=["gad"],
        return_type="LONG",
        c_template="_dash_listview_selected(${gad})",
        needs_gadtools=True,
        description="Get selected index (-1 if none)"
    ),
    "cycle_create": BuiltinFunc(
        name="cycle_create",
        params=["win", "x", "y", "w", "h", "options"],
        return_type="LONG",
        c_template="_dash_cycle_create(${win}, ${x}, ${y}, ${w}, ${h}, ${options})",
        needs_gadtools=True,
        description="Create cycle gadget; options separated by | (value = option, from 0)"
    ),
    "cycle_get": BuiltinFunc(
        name="cycle_get",
        params=["gad"],
        return_type="LONG",
        c_template="_dash_gad_value(${gad}, _DASH_GK_CYCLE)",
        needs_gadtools=True,
        description="Get selected option of a cycle gadget"
    ),
    "cycle_set": BuiltinFunc(
        name="cycle_set",
        params=["gad", "index"],
        return_type="void",
        c_template="_dash_gad_set_value(${gad}, _DASH_GK_CYCLE, ${index})",
        needs_gadtools=True,
        description="Select an option of a cycle gadget"
    ),
    "radio_create": BuiltinFunc(
        name="radio_create",
        params=["win", "x", "y", "options"],
        return_type="LONG",
        c_template="_dash_radio_create(${win}, ${x}, ${y}, ${options})",
        needs_gadtools=True,
        description="Create radio buttons (one per option, separated by |)"
    ),
    "radio_get": BuiltinFunc(
        name="radio_get",
        params=["gad"],
        return_type="LONG",
        c_template="_dash_gad_value(${gad}, _DASH_GK_RADIO)",
        needs_gadtools=True,
        description="Get selected radio button"
    ),
    "radio_set": BuiltinFunc(
        name="radio_set",
        params=["gad", "index"],
        return_type="void",
        c_template="_dash_gad_set_value(${gad}, _DASH_GK_RADIO, ${index})",
        needs_gadtools=True,
        description="Select a radio button"
    ),
    "integer_create": BuiltinFunc(
        name="integer_create",
        params=["win", "x", "y", "w", "h", "value"],
        return_type="LONG",
        c_template="_dash_integer_create(${win}, ${x}, ${y}, ${w}, ${h}, ${value})",
        needs_gadtools=True,
        description="Create integer input field"
    ),
    "integer_get": BuiltinFunc(
        name="integer_get",
        params=["gad"],
        return_type="LONG",
        c_template="_dash_gad_value(${gad}, _DASH_GK_INTEGER)",
        needs_gadtools=True,
        description="Get integer field value"
    ),
    "integer_set": BuiltinFunc(
        name="integer_set",
        params=["gad", "value"],
        return_type="void",
        c_template="_dash_gad_set_value(${gad}, _DASH_GK_INTEGER, ${value})",
        needs_gadtools=True,
        description="Set integer field value"
    ),
    "palette_create": BuiltinFunc(
        name="palette_create",
        params=["win", "x", "y", "w", "h", "depth"],
        return_type="LONG",
        c_template="_dash_palette_create(${win}, ${x}, ${y}, ${w}, ${h}, ${depth})",
        needs_gadtools=True,
        description="Create colour palette gadget (2^depth colours)"
    ),
    "palette_get": BuiltinFunc(
        name="palette_get",
        params=["gad"],
        return_type="LONG",
        c_template="_dash_gad_value(${gad}, _DASH_GK_PALETTE)",
        needs_gadtools=True,
        description="Get selected colour"
    ),
    "palette_set": BuiltinFunc(
        name="palette_set",
        params=["gad", "color"],
        return_type="void",
        c_template="_dash_gad_set_value(${gad}, _DASH_GK_PALETTE, ${color})",
        needs_gadtools=True,
        description="Select a colour"
    ),
    "number_create": BuiltinFunc(
        name="number_create",
        params=["win", "x", "y", "w", "h", "value"],
        return_type="LONG",
        c_template="_dash_number_create(${win}, ${x}, ${y}, ${w}, ${h}, ${value})",
        needs_gadtools=True,
        description="Create a box that shows a number"
    ),
    "number_set": BuiltinFunc(
        name="number_set",
        params=["gad", "value"],
        return_type="void",
        c_template="_dash_gad_set_value(${gad}, _DASH_GK_NUMBER, ${value})",
        needs_gadtools=True,
        description="Change the number shown"
    ),

    # Menus - see MENU_FUNCTIONS for simpler API

    # Dialogs (ASL)
    "dialog_file": BuiltinFunc(
        name="dialog_file",
        params=["title", "pattern", "save_mode"],
        return_type="STRPTR",
        c_template="_dash_dialog_file(${title}, ${pattern}, ${save_mode})",
        needs_asl=True,
        description="File requester: full path of the chosen file, \"\" if cancelled (save_mode true: save requester)"
    ),
    "dialog_file_at": BuiltinFunc(
        name="dialog_file_at",
        params=["title", "pattern", "save_mode", "drawer", "file"],
        return_type="STRPTR",
        c_template="_dash_dialog_file_at(${title}, ${pattern}, ${save_mode}, ${drawer}, ${file})",
        needs_asl=True,
        reads_only=True,
        description="dialog_file opening in that drawer with that file name (\"\": as dialog_file does)"
    ),
    "dialog_color": BuiltinFunc(
        name="dialog_color",
        params=["title", "initial"],
        return_type="LONG",
        c_template="_dash_dialog_color(${title}, ${initial})",
        needs_asl=True,
        needs_gfx=True,
        description="Palette window: returns the chosen pen (click, or arrows + Return); Esc keeps initial"
    ),
    "dialog_screen_mode": BuiltinFunc(
        name="dialog_screen_mode",
        params=["title"],
        return_type="BOOL",
        c_template="_dash_dialog_screen_mode(${title})",
        needs_asl=True,
        description="Screen mode requester (mode, width, height, depth), starting on the Workbench's: true if one was chosen; screen_mode_id/_width/_height/_depth give it"
    ),
    "screen_mode_id": BuiltinFunc(name="screen_mode_id", params=[], return_type="LONG", c_template="_dash_screen_mode_get(0)",
                                  needs_asl=True, description="The display mode of the last dialog_screen_mode (for screen_open_mode)"),
    "screen_mode_width": BuiltinFunc(name="screen_mode_width", params=[], return_type="LONG", c_template="_dash_screen_mode_get(1)",
                                     needs_asl=True, description="The width chosen in the last dialog_screen_mode"),
    "screen_mode_height": BuiltinFunc(name="screen_mode_height", params=[], return_type="LONG", c_template="_dash_screen_mode_get(2)",
                                      needs_asl=True, description="The height chosen in the last dialog_screen_mode"),
    "screen_mode_depth": BuiltinFunc(name="screen_mode_depth", params=[], return_type="LONG", c_template="_dash_screen_mode_get(3)",
                                     needs_asl=True, description="The depth (planes) chosen in the last dialog_screen_mode"),
    "dialog_font": BuiltinFunc(
        name="dialog_font",
        params=["title"],
        return_type="STRPTR",
        c_template="_dash_dialog_font(${title})",
        needs_asl=True,
        description="Font requester: \"name.font/size\", \"\" if cancelled"
    ),
}


# =============================================================================
# RTG - Retargetable Graphics (CyberGraphX/Picasso96)
# =============================================================================

RTG_FUNCTIONS = {
    # Detection and Query
    "rtg_available": BuiltinFunc(
        name="rtg_available",
        params=[],
        return_type="BOOL",
        c_template="_dash_rtg_available()",
        needs_rtg=True,
        description="Check if CyberGraphX or Picasso96 is available"
    ),
    "rtg_is_active": BuiltinFunc(
        name="rtg_is_active",
        params=[],
        return_type="BOOL",
        c_template="_dash_rtg_is_active()",
        needs_rtg=True,
        description="Check if current screen is using RTG"
    ),
    "rtg_get_depth": BuiltinFunc(
        name="rtg_get_depth",
        params=[],
        return_type="LONG",
        c_template="_dash_rtg_get_depth()",
        needs_rtg=True,
        description="Get current screen bit depth (the program's, or else the Workbench's: outside the drawing of a desktop_canvas too)"
    ),
    "rtg_get_width": BuiltinFunc(
        name="rtg_get_width",
        params=[],
        return_type="LONG",
        c_template="_dash_rtg_get_width()",
        needs_rtg=True,
        description="Get current screen width (the program's, or else the Workbench's: outside the drawing of a desktop_canvas too)"
    ),
    "rtg_get_height": BuiltinFunc(
        name="rtg_get_height",
        params=[],
        return_type="LONG",
        c_template="_dash_rtg_get_height()",
        needs_rtg=True,
        description="Get current screen height (the program's, or else the Workbench's: outside the drawing of a desktop_canvas too)"
    ),

    # Bitmap Operations
    "rtg_alloc_bitmap": BuiltinFunc(
        name="rtg_alloc_bitmap",
        params=["width", "height", "depth"],
        return_type="APTR",
        c_template="_dash_rtg_alloc_bitmap(${width}, ${height}, ${depth})",
        needs_rtg=True,
        description="Allocate RTG-compatible bitmap"
    ),
    "rtg_free_bitmap": BuiltinFunc(
        name="rtg_free_bitmap",
        params=["bitmap"],
        return_type="void",
        c_template="_dash_rtg_free_bitmap((struct BitMap *)${bitmap})",
        needs_rtg=True,
        description="Free RTG bitmap"
    ),

    # 24-bit Pixel Operations
    "rtg_write_pixel": BuiltinFunc(
        name="rtg_write_pixel",
        params=["x", "y", "rgb"],
        return_type="void",
        c_template="_dash_rtg_write_pixel(${x}, ${y}, ${rgb})",
        needs_rtg=True,
        description="Write single pixel with 24-bit RGB color"
    ),
    "rtg_read_pixel": BuiltinFunc(
        name="rtg_read_pixel",
        params=["x", "y"],
        return_type="LONG",
        c_template="_dash_rtg_read_pixel(${x}, ${y})",
        needs_rtg=True,
        description="Read pixel, returns 24-bit RGB color"
    ),
    "rtg_fill_rect": BuiltinFunc(
        name="rtg_fill_rect",
        params=["x", "y", "w", "h", "rgb"],
        return_type="void",
        c_template="_dash_rtg_fill_rect(${x}, ${y}, ${w}, ${h}, ${rgb})",
        needs_rtg=True,
        description="Fill rectangle with 24-bit RGB color"
    ),

    # Bulk Pixel Operations
    "rtg_write_array": BuiltinFunc(
        name="rtg_write_array",
        params=["buffer", "bpr", "x", "y", "w", "h"],
        return_type="void",
        c_template="_dash_rtg_write_array((APTR)${buffer}, ${bpr}, ${x}, ${y}, ${w}, ${h})",
        needs_rtg=True,
        description="Write pixel array (buffer is ARGB 32-bit, bpr is bytes per row)"
    ),
    "rtg_read_array": BuiltinFunc(
        name="rtg_read_array",
        params=["buffer", "bpr", "x", "y", "w", "h"],
        return_type="void",
        c_template="_dash_rtg_read_array((APTR)${buffer}, ${bpr}, ${x}, ${y}, ${w}, ${h})",
        needs_rtg=True,
        description="Read pixel array from screen into buffer"
    ),

    # Color Conversion Helpers
    "rtg_rgb": BuiltinFunc(
        name="rtg_rgb",
        params=["r", "g", "b"],
        return_type="LONG",
        c_template="(((${r})<<16)|((${g})<<8)|(${b}))",
        needs_gfx=True,  # No RTG library needed, just a macro
        description="Create 24-bit RGB color value from components"
    ),
    "rtg_argb": BuiltinFunc(
        name="rtg_argb",
        params=["a", "r", "g", "b"],
        return_type="LONG",
        c_template="(((${a})<<24)|((${r})<<16)|((${g})<<8)|(${b}))",
        needs_gfx=True,
        description="Create 32-bit ARGB color value from components"
    ),
    "rtg_rgb_r": BuiltinFunc(
        name="rtg_rgb_r",
        params=["color"],
        return_type="LONG",
        c_template="(((${color})>>16)&0xFF)",
        needs_gfx=True,
        description="Extract red component from RGB color"
    ),
    "rtg_rgb_g": BuiltinFunc(
        name="rtg_rgb_g",
        params=["color"],
        return_type="LONG",
        c_template="(((${color})>>8)&0xFF)",
        needs_gfx=True,
        description="Extract green component from RGB color"
    ),
    "rtg_rgb_b": BuiltinFunc(
        name="rtg_rgb_b",
        params=["color"],
        return_type="LONG",
        c_template="((${color})&0xFF)",
        needs_gfx=True,
        description="Extract blue component from RGB color"
    ),

    # Screen Mode Functions
    "rtg_best_mode": BuiltinFunc(
        name="rtg_best_mode",
        params=["width", "height", "depth"],
        return_type="LONG",
        c_template="_dash_rtg_best_mode(${width}, ${height}, ${depth})",
        needs_rtg=True,
        description="Find best RTG display mode for given dimensions"
    ),
    "rtg_open_screen": BuiltinFunc(
        name="rtg_open_screen",
        params=["width", "height", "depth", "title"],
        return_type="BOOL",
        c_template="_dash_rtg_open_screen(${width}, ${height}, ${depth}, ${title})",
        needs_rtg=True,
        description="Open RTG screen with specified dimensions"
    ),

    # Blitting with Alpha
    "rtg_blit": BuiltinFunc(
        name="rtg_blit",
        params=["src", "sx", "sy", "dx", "dy", "w", "h"],
        return_type="void",
        c_template="_dash_rtg_blit((struct BitMap *)${src}, ${sx}, ${sy}, ${dx}, ${dy}, ${w}, ${h})",
        needs_rtg=True,
        description="Blit from bitmap to screen"
    ),
    "rtg_scale_blit": BuiltinFunc(
        name="rtg_scale_blit",
        params=["src", "sx", "sy", "sw", "sh", "dx", "dy", "dw", "dh"],
        return_type="void",
        c_template="_dash_rtg_scale_blit((struct BitMap *)${src}, ${sx}, ${sy}, ${sw}, ${sh}, ${dx}, ${dy}, ${dw}, ${dh})",
        needs_rtg=True,
        description="Scaled blit from bitmap to screen"
    ),
}


# =============================================================================
# MUI - MagicUserInterface 5 (68020+, muimaster.library); docs/MUI_DISEÑO.md
# =============================================================================

MUI_FUNCTIONS = {
    "mui_app_begin": BuiltinFunc(
        name="mui_app_begin",
        params=["title", "base"],
        return_type="APTR",
        c_template="_dash_mui_app_begin(${title}, ${base})",
        description="Open muimaster.library and create the MUI application (base: ARexx name); 0 if MUI is missing or the CPU is a 68000"
    ),
    "mui_text_editor": BuiltinFunc(
        name="mui_text_editor", params=["lines"], return_type="APTR", c_template="_dash_mui_text_editor(${lines})",
        description="A text field of several lines (MUI's Textinput), that many lines high, with a scroller: Return "
                    "starts a new line; mui_get_text and mui_set_text read and set it, mui_on_ack gives the event of "
                    "sending it (Amiga+Return in its window)"),
    "mui_window_open_back": BuiltinFunc(
        name="mui_window_open_back", params=["win"], return_type="LONG",
        c_template="_dash_mui_window_open_back(${win})",
        description="Open a window without making it the active one: the keyboard stays where it was; false if it "
                    "could not open"),
    "mui_window_activate": BuiltinFunc(
        name="mui_window_activate", params=["win"], return_type="void",
        c_template="_dash_mui_window_activate(${win})",
        description="Make a window the active one, in front of the others (it opens if it is closed)"),
    "mui_window_dispose": BuiltinFunc(
        name="mui_window_dispose", params=["window"], return_type="void",
        c_template="_dash_mui_window_dispose(${window})",
        description="Close a window, take it out of the application and free it with all its objects (and the context "
                    "menus made after it): for windows made again and again (a preview). Nothing for 0 or a window "
                    "already gone; its objects must not be used after"),
    # Dash 2.0 (Forja): asking the user
    "mui_request": BuiltinFunc(
        name="mui_request", params=["window", "title", "text", "buttons"], return_type="LONG",
        c_template="_dash_mui_request(${window}, ${title}, ${text}, ${buttons})", reads_only=True,
        description="Ask with MUI's requester over a window (0: over the application), its buttons separated by \"|\" "
                    "(\"_Guardar|_Descartar|_Cancelar\"); the application's windows wait. The button chosen: 1, 2... "
                    "from the left, 0 the last one (also Esc)"),
    # Dash 2.0 (Forja): colours without MUI's prefs
    "mui_set_background": BuiltinFunc(
        name="mui_set_background", params=["obj", "r", "g", "b"], return_type="void",
        c_template="_dash_mui_set_background(${obj}, ${r}, ${g}, ${b})",
        description="An RGB background (0-255 each) for an object: a group, a text, a label, a button, a list (and the "
                    "list inside it) or a window (its root group); the objects inside take it unless they have "
                    "their own"),
    "mui_set_text_pen": BuiltinFunc(
        name="mui_set_text_pen", params=["obj", "r", "g", "b"], return_type="void",
        c_template="_dash_mui_set_text_pen(${obj}, ${r}, ${g}, ${b})",
        description="The colour (RGB, 0-255 each) of the text of a text, label or button; mui_set_text keeps it"),
    "mui_app_field_colors": BuiltinFunc(
        name="mui_app_field_colors", params=["r", "g", "b", "active_r", "active_g", "active_b",
                                             "cursor_r", "cursor_g", "cursor_b"], return_type="void",
        c_template="_dash_mui_app_field_colors(${r}, ${g}, ${b}, ${active_r}, ${active_g}, ${active_b}, "
                   "${cursor_r}, ${cursor_g}, ${cursor_b})",
        description="The background (RGB, 0-255 each) of all the application's text fields (string, text_editor, "
                    "combo), inactive and active, and their cursor; the windows opened after it take them. The text "
                    "stays black: a grey where it still reads, like 96, 96, 104 and 120, 120, 128"),
    # Dash 2.0 (Inferencia): the application's own ARexx commands
    "mui_app_rexx": BuiltinFunc(
        name="mui_app_rexx", params=["app", "func"], return_type="void",
        c_template="_dash_mui_app_rexx(${app}, ${func})",
        description="Every ARexx command to the application's port (its base and \".1\": \"BASE.1\") that MUI does "
                    "not answer itself (QUIT, SHOW, HIDE, INFO...) calls f(command: String) -> String with the whole "
                    "command line: what it returns is the RESULT, and mui_rexx_fail during the call sets the RC. "
                    "It runs while mui_wait_event waits"),
    "mui_rexx_fail": BuiltinFunc(
        name="mui_rexx_fail", params=["rc"], return_type="void", c_template="_dash_mui_rexx_fail(${rc})",
        description="From mui_app_rexx's function: the command's RC (5 warning, 10 error, 20 failure; no RESULT then)"),
    "mui_app_end": BuiltinFunc(
        name="mui_app_end",
        params=[],
        return_type="void",
        c_template="_dash_mui_app_end()",
        description="Dispose the application with its windows and objects, close MUI (also done at exit)"
    ),
    "mui_window_begin": BuiltinFunc(
        name="mui_window_begin",
        params=["title", "id"],
        return_type="APTR",
        c_template="_dash_mui_window_begin(${title}, ${id})",
        description="Start a window (id 1-255: MUI remembers its size and place; 0 none) with a vertical root group"
    ),
    "mui_window_end": BuiltinFunc(
        name="mui_window_end",
        params=[],
        return_type="void",
        c_template="_dash_mui_window_end()",
        description="End the window started with mui_window_begin"
    ),
    "mui_window_open": BuiltinFunc(
        name="mui_window_open",
        params=["win"],
        return_type="LONG",
        c_template="_dash_mui_window_open(${win})",
        description="Open a window; false if it could not open"
    ),
    "mui_window_close": BuiltinFunc(
        name="mui_window_close",
        params=["win"],
        return_type="void",
        c_template="_dash_mui_window_close(${win})",
        description="Close a window (it still exists)"
    ),
    "mui_window_active": BuiltinFunc(
        name="mui_window_active",
        params=["win"],
        return_type="LONG",
        c_template="_dash_mui_window_active(${win})",
        description="1 if the window is the active one (several windows from one .dashui share event numbers; dashweb D32)"
    ),
    "mui_vgroup_begin": BuiltinFunc(
        name="mui_vgroup_begin",
        params=[],
        return_type="APTR",
        c_template="_dash_mui_group_begin(0)",
        description="Start a vertical group inside the open group"
    ),
    "mui_hgroup_begin": BuiltinFunc(
        name="mui_hgroup_begin",
        params=[],
        return_type="APTR",
        c_template="_dash_mui_group_begin(1)",
        description="Start a horizontal group inside the open group"
    ),
    "mui_group_end": BuiltinFunc(
        name="mui_group_end",
        params=[],
        return_type="void",
        c_template="_dash_mui_group_end()",
        description="End the open group"
    ),
    "mui_text": BuiltinFunc(
        name="mui_text",
        params=["text"],
        return_type="APTR",
        c_template="_dash_mui_text(${text})",
        description="Text object (MUI text codes allowed)"
    ),
    "mui_button": BuiltinFunc(
        name="mui_button",
        params=["label"],
        return_type="APTR",
        c_template="_dash_mui_button(${label})",
        description="Button (an underscore before a letter makes it the keyboard shortcut)"
    ),
    "mui_on_press": BuiltinFunc(
        name="mui_on_press",
        params=["obj", "id"],
        return_type="void",
        c_template="_dash_mui_on_press(${obj}, ${id})",
        description="mui_wait_event returns id when the button is pressed"
    ),
    "mui_on_close": BuiltinFunc(
        name="mui_on_close",
        params=["win", "id"],
        return_type="void",
        c_template="_dash_mui_on_close(${win}, ${id})",
        description="mui_wait_event returns id when the window's close gadget is clicked (default for the first window: -1)"
    ),
    "mui_on_drop": BuiltinFunc(
        name="mui_on_drop",
        params=["obj", "id"],
        return_type="void",
        c_template="_dash_mui_on_drop(${obj}, ${id})",
        description="mui_wait_event returns id when icons are dropped from the Workbench on that object (a window: "
                    "anywhere on it); app_drop gives their paths, app_drop_x/y where they fell"
    ),
    "mui_press": BuiltinFunc(
        name="mui_press",
        params=["obj"],
        return_type="void",
        c_template="_dash_mui_press(${obj})",
        description="Send the mui_on_press event of a button as if it were pressed"
    ),
    "mui_label": BuiltinFunc(
        name="mui_label",
        params=["text"],
        return_type="APTR",
        c_template="_dash_mui_label(${text})",
        description="Label for a form row (right-aligned)"
    ),
    "mui_string": BuiltinFunc(
        name="mui_string",
        params=["initial", "maxlen"],
        return_type="APTR",
        c_template="_dash_mui_string(${initial}, ${maxlen})",
        description="Text field with up to maxlen characters"
    ),
    "mui_checkbox": BuiltinFunc(
        name="mui_checkbox",
        params=["checked"],
        return_type="APTR",
        c_template="_dash_mui_checkbox(${checked})",
        description="Checkbox"
    ),
    "mui_cycle": BuiltinFunc(
        name="mui_cycle",
        params=["options"],
        return_type="APTR",
        c_template="_dash_mui_cycle(${options})",
        description="Cycle gadget; options separated by | (\"One|Two|Three\")"
    ),
    "mui_slider": BuiltinFunc(
        name="mui_slider",
        params=["min", "max", "value"],
        return_type="APTR",
        c_template="_dash_mui_slider(${min}, ${max}, ${value})",
        description="Horizontal slider"
    ),
    "mui_gauge": BuiltinFunc(
        name="mui_gauge",
        params=["max"],
        return_type="APTR",
        c_template="_dash_mui_gauge(${max})",
        description="Progress bar from 0 to max"
    ),
    "mui_get_value": BuiltinFunc(
        name="mui_get_value",
        params=["obj"],
        return_type="LONG",
        c_template="_dash_mui_get_value(${obj})",
        description="Value: checkbox 1/0, cycle option, slider level, progress, menu check mark 1/0"
    ),
    "mui_set_value": BuiltinFunc(
        name="mui_set_value",
        params=["obj", "value"],
        return_type="void",
        c_template="_dash_mui_set_value(${obj}, ${value})",
        description="Set the value (fires mui_on_change like the user would)"
    ),
    "mui_get_text": BuiltinFunc(
        name="mui_get_text",
        params=["obj"],
        return_type="STRPTR",
        c_template="_dash_mui_get_text(${obj})",
        description="Text of a text field, text, button or window title"
    ),
    "mui_set_text": BuiltinFunc(
        name="mui_set_text",
        params=["obj", "text"],
        return_type="void",
        c_template="_dash_mui_set_text(${obj}, ${text})",
        description="Change the text of a text field, text, button, menu item or window title"
    ),
    "mui_set_enabled": BuiltinFunc(
        name="mui_set_enabled",
        params=["obj", "enabled"],
        return_type="void",
        c_template="_dash_mui_set_enabled(${obj}, ${enabled})",
        description="Enable or disable (ghost) an object, a menu item or a whole menu"
    ),
    "mui_on_change": BuiltinFunc(
        name="mui_on_change",
        params=["obj", "id"],
        return_type="void",
        c_template="_dash_mui_on_change(${obj}, ${id})",
        description="mui_wait_event returns id when the value or text changes"
    ),
    "mui_on_ack": BuiltinFunc(
        name="mui_on_ack",
        params=["obj", "id"],
        return_type="void",
        c_template="_dash_mui_on_ack(${obj}, ${id})",
        description="mui_wait_event returns id when Return is pressed in a text field (in a mui_combo, also when a line is picked)"
    ),
    "mui_list": BuiltinFunc(
        name="mui_list",
        params=[],
        return_type="APTR",
        c_template="_dash_mui_list()",
        description="List of texts with scroller; its value is the selected line (-1 none)"
    ),
    "mui_list_add": BuiltinFunc(
        name="mui_list_add",
        params=["list", "text"],
        return_type="void",
        c_template="_dash_mui_list_insert(${list}, -1, ${text})",
        description="Add a line at the end"
    ),
    "mui_list_insert": BuiltinFunc(
        name="mui_list_insert",
        params=["list", "pos", "text"],
        return_type="void",
        c_template="_dash_mui_list_insert(${list}, ${pos}, ${text})",
        description="Insert a line at pos (0 = first)"
    ),
    "mui_list_remove": BuiltinFunc(
        name="mui_list_remove",
        params=["list", "pos"],
        return_type="void",
        c_template="_dash_mui_list_remove(${list}, ${pos})",
        description="Remove the line at pos"
    ),
    "mui_list_clear": BuiltinFunc(
        name="mui_list_clear",
        params=["list"],
        return_type="void",
        c_template="_dash_mui_list_clear(${list})",
        description="Remove all lines"
    ),
    "mui_list_count": BuiltinFunc(
        name="mui_list_count",
        params=["list"],
        return_type="LONG",
        c_template="_dash_mui_list_count(${list})",
        description="Number of lines"
    ),
    "mui_list_get": BuiltinFunc(
        name="mui_list_get",
        params=["list", "pos"],
        return_type="STRPTR",
        c_template="_dash_mui_list_get(${list}, ${pos})",
        description="Text of the line at pos (\"\" outside the list)"
    ),
    "mui_list_quiet": BuiltinFunc(
        name="mui_list_quiet",
        params=["list", "quiet"],
        return_type="void",
        c_template="_dash_mui_list_quiet(${list}, ${quiet})",
        description="While quiet the list is not redrawn (adding many lines)"
    ),
    "mui_on_double": BuiltinFunc(
        name="mui_on_double",
        params=["list", "id"],
        return_type="void",
        c_template="_dash_mui_on_double(${list}, ${id})",
        description="mui_wait_event returns id on a double click in the list"
    ),
    "mui_frame_begin": BuiltinFunc(
        name="mui_frame_begin",
        params=["title", "horizontal"],
        return_type="APTR",
        c_template="_dash_mui_frame_begin(${title}, ${horizontal})",
        description="Start a group with a frame and a title (\"\" = none)"
    ),
    "mui_columns_begin": BuiltinFunc(
        name="mui_columns_begin",
        params=["columns"],
        return_type="APTR",
        c_template="_dash_mui_columns_begin(${columns})",
        description="Start a grid group with that many columns (forms: label, field...)"
    ),
    "mui_register_begin": BuiltinFunc(
        name="mui_register_begin",
        params=["titles"],
        return_type="APTR",
        c_template="_dash_mui_register_begin(${titles})",
        description="Start tabs (\"One|Two\"); each child is a page; value = page shown"
    ),
    "mui_scroll_begin": BuiltinFunc(
        name="mui_scroll_begin",
        params=[],
        return_type="APTR",
        c_template="_dash_mui_scroll_begin()",
        description="Start an area with scrollbars (contents bigger than the window)"
    ),
    "mui_space": BuiltinFunc(
        name="mui_space",
        params=[],
        return_type="APTR",
        c_template="_dash_mui_space()",
        description="Empty space that takes what is left"
    ),
    "mui_balance": BuiltinFunc(
        name="mui_balance",
        params=[],
        return_type="APTR",
        c_template="_dash_mui_balance()",
        description="Bar the user drags to share the space between its neighbours"
    ),
    "mui_weight": BuiltinFunc(
        name="mui_weight",
        params=["obj", "weight"],
        return_type="void",
        c_template="_dash_mui_weight(${obj}, ${weight})",
        description="Share of the free space an object gets (100 by default)"
    ),
    "mui_set_visible": BuiltinFunc(
        name="mui_set_visible",
        params=["obj", "visible"],
        return_type="void",
        c_template="_dash_mui_set_visible(${obj}, ${visible})",
        description="Show or hide an object (the window relayouts)"
    ),
    "mui_menu_begin": BuiltinFunc(
        name="mui_menu_begin",
        params=["title"],
        return_type="APTR",
        c_template="_dash_mui_menu_begin(${title})",
        description="Start a menu of the window being built"
    ),
    "mui_menu_item": BuiltinFunc(
        name="mui_menu_item",
        params=["title", "key", "id"],
        return_type="APTR",
        c_template="_dash_mui_menu_item(${title}, ${key}, ${id})",
        description="Menu item: key = letter for Amiga+key (\"\" none); mui_wait_event returns id"
    ),
    "mui_menu_check": BuiltinFunc(
        name="mui_menu_check",
        params=["title", "key", "id", "checked"],
        return_type="APTR",
        reads_only=True,   # (it copies its texts: _dash_mui_keep, or MUI does)
        c_template="_dash_mui_menu_check(${title}, ${key}, ${id}, ${checked})",
        description="Menu item with a check mark: choosing it toggles the mark and mui_wait_event returns id; "
                    "mui_get_value / mui_set_value read and set the mark"
    ),
    "mui_submenu_begin": BuiltinFunc(
        name="mui_submenu_begin",
        params=["title"],
        return_type="APTR",
        reads_only=True,   # (it copies its texts: _dash_mui_keep, or MUI does)
        c_template="_dash_mui_submenu_begin(${title})",
        description="Start a submenu in the menu being built (one level): its items go in until mui_submenu_end"
    ),
    "mui_submenu_end": BuiltinFunc(
        name="mui_submenu_end",
        params=[],
        return_type="void",
        c_template="_dash_mui_submenu_end()",
        description="End the submenu"
    ),
    "mui_menu_separator": BuiltinFunc(
        name="mui_menu_separator",
        params=[],
        return_type="void",
        c_template="_dash_mui_menu_separator()",
        description="Separator line in the menu"
    ),
    "mui_context_menu_begin": BuiltinFunc(
        name="mui_context_menu_begin",
        params=["title"],
        return_type="APTR",
        reads_only=True,   # (it copies its texts: _dash_mui_keep, or MUI does)
        c_template="_dash_mui_context_menu_begin(${title})",
        description="Start a context menu (anywhere, not only in a window): its items as in a menu "
                    "(mui_menu_item, mui_menu_check, mui_submenu_begin...) until mui_menu_end; give it to an object "
                    "with mui_set_context_menu (Lorraine D15)"
    ),
    "mui_set_context_menu": BuiltinFunc(
        name="mui_set_context_menu",
        params=["object", "menu"],
        return_type="void",
        c_template="_dash_mui_set_context_menu(${object}, ${menu})",
        description="The right button over the object opens that context menu (0: none); its items give their "
                    "events; on a canvas, mui_canvas_mouse_x/_y say where it was pressed and mui_canvas_button is 2"
    ),
    "mui_menu_end": BuiltinFunc(
        name="mui_menu_end",
        params=[],
        return_type="void",
        c_template="_dash_mui_menu_end()",
        description="End the menu"
    ),
    "mui_canvas": BuiltinFunc(
        name="mui_canvas",
        params=["min_width", "min_height"],
        return_type="APTR",
        c_template="_dash_mui_canvas(${min_width}, ${min_height})",
        description="Drawing area (grows with the window); draw in it from mui_canvas_on_draw"
    ),
    "mui_canvas_on_draw": BuiltinFunc(
        name="mui_canvas_on_draw",
        params=["canvas", "func"],
        return_type="void",
        c_template="_dash_mui_canvas_on_draw(${canvas}, ${func})",
        description="Function f(x, y, width, height) that draws the area with gfx_ (MUI calls it when needed)"
    ),
    "mui_canvas_on_input": BuiltinFunc(
        name="mui_canvas_on_input",
        params=["canvas", "id"],
        return_type="void",
        c_template="_dash_mui_canvas_on_input(${canvas}, ${id})",
        description="mui_wait_event returns id on a click, wheel or key over the area (call before opening the window)"
    ),
    "mui_canvas_redraw": BuiltinFunc(
        name="mui_canvas_redraw",
        params=["canvas"],
        return_type="void",
        c_template="_dash_mui_canvas_redraw(${canvas})",
        description="Draw the area again now"
    ),
    "mui_canvas_buffered": BuiltinFunc(
        name="mui_canvas_buffered",
        params=["canvas", "on"],
        return_type="void",
        c_template="_dash_mui_canvas_buffered(${canvas}, ${on})",
        description="Draw the area in a bitmap of its own and show it at once when done (no half-drawn area; "
                    "the same coordinates; mui_canvas_update still draws on the window)"
    ),
    "mui_canvas_update": BuiltinFunc(
        name="mui_canvas_update",
        params=["canvas"],
        return_type="void",
        c_template="_dash_mui_canvas_update(${canvas})",
        description="Call the draw function now without clearing the area (it paints only what changed)"
    ),
    "mui_canvas_update_area": BuiltinFunc(
        name="mui_canvas_update_area",
        params=["canvas", "x", "y", "w", "h"],
        return_type="void",
        c_template="_dash_mui_canvas_update_area(${canvas}, ${x}, ${y}, ${w}, ${h})",
        description="Like mui_canvas_update, only the zone w x h at x, y of the area (from its corner): the drawing "
                    "is clipped to it and, with mui_canvas_buffered, only it goes from the buffer to the window"
    ),
    "mui_canvas_updating": BuiltinFunc(
        name="mui_canvas_updating",
        params=[],
        return_type="BOOL",
        c_template="_dash_mui_canvas_updating()",
        description="In the draw function: true if it runs for mui_canvas_update (the rest is still there)"
    ),
    "mui_canvas_on_move": BuiltinFunc(
        name="mui_canvas_on_move",
        params=["canvas", "id"],
        return_type="void",
        c_template="_dash_mui_canvas_on_move(${canvas}, ${id})",
        description="mui_wait_event returns id when the pointer moves over the area or leaves it, without a click "
                    "(the moves that come meanwhile make one; call before opening the window)"
    ),
    "mui_canvas_pointer_x": BuiltinFunc(
        name="mui_canvas_pointer_x",
        params=["canvas"],
        return_type="LONG",
        c_template="_dash_mui_canvas_pointer(${canvas}, 0)",
        description="X of the pointer now, from the area's left edge (clicked or not)"
    ),
    "mui_canvas_pointer_y": BuiltinFunc(
        name="mui_canvas_pointer_y",
        params=["canvas"],
        return_type="LONG",
        c_template="_dash_mui_canvas_pointer(${canvas}, 1)",
        description="Y of the pointer now, from the area's top edge (clicked or not)"
    ),
    "mui_canvas_pointer_inside": BuiltinFunc(
        name="mui_canvas_pointer_inside",
        params=["canvas"],
        return_type="BOOL",
        c_template="_dash_mui_canvas_pointer(${canvas}, 2)",
        description="True if the pointer is over the area now"
    ),
    "mui_canvas_set_pointer": BuiltinFunc(
        name="mui_canvas_set_pointer",
        params=["canvas", "shape"],
        return_type="void",
        c_template="_dash_mui_canvas_set_pointer(${canvas}, ${shape})",
        description="The pointer's shape over the area: 0 normal, 1 text (I), 2 resize left-right, 3 resize up-down, "
                    "4 busy; it changes now if the pointer is over the area (or dragging it) and goes back to "
                    "normal outside it (Lorraine D16)"
    ),
    "mui_canvas_take_tab": BuiltinFunc(
        name="mui_canvas_take_tab",
        params=["canvas", "on"],
        return_type="void",
        c_template="_dash_mui_canvas_take_tab(${canvas}, ${on})",
        description="With the pointer over the area, Tab and Shift+Tab are keys for it (mui_canvas_key 66, Shift in "
                    "mui_canvas_qualifiers; needs mui_canvas_on_input) and not the window's next and previous "
                    "gadget; away from it they move between gadgets as always (Lorraine D48)"
    ),
    "mui_canvas_mouse_x": BuiltinFunc(
        name="mui_canvas_mouse_x",
        params=["canvas"],
        return_type="LONG",
        c_template="_dash_mui_canvas_input(${canvas}, 0)",
        description="X of the last click or wheel, from the area's left edge"
    ),
    "mui_canvas_mouse_y": BuiltinFunc(
        name="mui_canvas_mouse_y",
        params=["canvas"],
        return_type="LONG",
        c_template="_dash_mui_canvas_input(${canvas}, 1)",
        description="Y of the last click or wheel, from the area's top edge"
    ),
    "mui_canvas_button": BuiltinFunc(
        name="mui_canvas_button",
        params=["canvas"],
        return_type="LONG",
        c_template="_dash_mui_canvas_input(${canvas}, 2)",
        description="1 if the last input was a left click, else 0"
    ),
    "mui_canvas_wheel": BuiltinFunc(
        name="mui_canvas_wheel",
        params=["canvas"],
        return_type="LONG",
        c_template="_dash_mui_canvas_input(${canvas}, 3)",
        description="+1 / -1 if the last input was the mouse wheel (up/down), else 0"
    ),
    "mui_canvas_key": BuiltinFunc(
        name="mui_canvas_key",
        params=["canvas"],
        return_type="LONG",
        c_template="_dash_mui_canvas_input(${canvas}, 4)",
        description="Raw key code of the last input, -1 if it was not a key"
    ),
    "mui_canvas_on_drag": BuiltinFunc(
        name="mui_canvas_on_drag",
        params=["canvas", "id"],
        return_type="void",
        c_template="_dash_mui_canvas_on_drag(${canvas}, ${id})",
        description="Event id when the area is dragged (moved with the left button down after pressing it on the "
                    "area) and when it is let go; mui_canvas_drag says which, mui_canvas_mouse_x/y where (maybe out "
                    "of the area). Call before opening the window"
    ),
    "mui_canvas_drag": BuiltinFunc(
        name="mui_canvas_drag",
        params=["canvas"],
        return_type="LONG",
        c_template="_dash_mui_canvas_input(${canvas}, 6)",
        description="The last drag event: 1 moving with the button down, 2 let go (0 before any)"
    ),
    "mui_canvas_qualifiers": BuiltinFunc(
        name="mui_canvas_qualifiers",
        params=["canvas"],
        return_type="LONG",
        c_template="_dash_mui_canvas_input(${canvas}, 5)",
        description="Keys held at the last key, click or wheel: 1 Shift, 2 Ctrl, 4 Alt, 8 Amiga, added up "
                    "(Shift + Ctrl = 3); q & 1 tells Shift"
    ),
    "mui_canvas_char": BuiltinFunc(
        name="mui_canvas_char",
        params=["canvas"],
        return_type="STRPTR",
        c_template="_dash_mui_canvas_char(${canvas})",
        description="Character of the last key in the area, with shift and the keymap (\"\" if none; dashweb D31)"
    ),
    "mui_scrollbar": BuiltinFunc(
        name="mui_scrollbar",
        params=["vertical"],
        return_type="APTR",
        c_template="_dash_mui_scrollbar(${vertical})",
        description="Scrollbar; its value is the first line shown"
    ),
    "mui_set_range": BuiltinFunc(
        name="mui_set_range",
        params=["scrollbar", "total", "visible"],
        return_type="void",
        c_template="_dash_mui_set_range(${scrollbar}, ${total}, ${visible})",
        description="Size of the document and of the part that fits"
    ),
    "mui_wait_event_signals": BuiltinFunc(
        name="mui_wait_event_signals",
        params=["mask"],
        return_type="LONG",
        c_template="_dash_mui_wait_event_signals(${mask})",
        description="Like mui_wait_event, but also returns 0 when one of the signals of mask arrives (sockets...); mui_signals says which"
    ),
    "mui_signals": BuiltinFunc(
        name="mui_signals",
        params=[],
        return_type="LONG",
        c_template="_dash_mui_signals()",
        description="Signals of the mask that woke the last mui_wait_event_signals"
    ),
    "mui_timer": BuiltinFunc(
        name="mui_timer",
        params=["ms", "id"],
        return_type="void",
        c_template="_dash_mui_timer(${ms}, ${id})",
        description="In ms milliseconds mui_wait_event returns id, once (again: call it again; 0 cancels)"
    ),
    "mui_image": BuiltinFunc(
        name="mui_image",
        params=["file"],
        return_type="APTR",
        c_template="_dash_mui_image(${file})",
        description="Picture from a file through datatypes (ILBM; PNG, JPEG, GIF if their datatypes are installed); mui_set_text changes the file"
    ),
    "mui_image_button": BuiltinFunc(
        name="mui_image_button",
        params=["file"],
        return_type="APTR",
        c_template="_dash_mui_image_button(${file})",
        description="Button with a picture (a toolbar icon; ILBM, or what the datatypes read): mui_on_press like a button, mui_set_text changes the picture"
    ),
    "mui_image_toggle": BuiltinFunc(
        name="mui_image_toggle",
        params=["file", "group", "selected"],
        return_type="APTR",
        c_template="_dash_mui_image_toggle(${file}, ${group}, ${selected})",
        description="Picture button that stays pressed (bold, italic): value 1/0 with mui_get_value / mui_set_value, "
                    "mui_on_change when it changes; group > 0: pressing one lets go the others of that group "
                    "(alignment), and mui_on_change only fires for the one pressed"
    ),
    "mui_combo": BuiltinFunc(
        name="mui_combo",
        params=["text", "options"],
        return_type="APTR",
        reads_only=True,   # (it copies its texts: _dash_mui_keep, or MUI does)
        c_template="_dash_mui_combo(${text}, ${options})",
        description="Text field with a list that drops down (font, size; options \"A|B\"): write or pick a line "
                    "(double click); mui_get_text / mui_set_text, mui_list_* change the lines, mui_on_ack on Return "
                    "or when a line is picked"
    ),
    "mui_help": BuiltinFunc(
        name="mui_help",
        params=["obj", "text"],
        return_type="void",
        c_template="_dash_mui_help(${obj}, ${text})",
        description="Bubble help shown when the pointer rests on the object"
    ),
    "mui_window_move": BuiltinFunc(
        name="mui_window_move",
        params=["win", "dx", "dy"],
        return_type="void",
        c_template="_dash_mui_window_move(${win}, ${dx}, ${dy})",
        description="Move an open window by dx, dy pixels (windows of one .dashui open in the same place)"
    ),
    "mui_set_active": BuiltinFunc(
        name="mui_set_active",
        params=["win", "obj"],
        return_type="void",
        c_template="_dash_mui_set_active(${win}, ${obj})",
        description="Make obj the window's active object: the cursor goes to that string gadget (Amiga-L)"
    ),
    "mui_window_size": BuiltinFunc(
        name="mui_window_size",
        params=["win", "width_pct", "height_pct"],
        return_type="void",
        c_template="_dash_mui_window_size(${win}, ${width_pct}, ${height_pct})",
        description="Size of the window when it opens, in percent of the visible screen, centred (before mui_window_open)"
    ),
    "mui_window_fullscreen": BuiltinFunc(
        name="mui_window_fullscreen",
        params=["win"],
        return_type="void",
        c_template="_dash_mui_window_fullscreen(${win})",
        description="The window over the whole screen: no borders, title bar or gadgets, active (before mui_window_open)"
    ),
    "mui_window_screen": BuiltinFunc(
        name="mui_window_screen",
        params=["win", "name"],
        return_type="BOOL",
        c_template="_dash_mui_window_screen(${win}, ${name})",
        description="The window opens as a normal window on the public screen with that name (screen_clone_wb's, or another program's); before mui_window_open; false if there is no such screen"
    ),
    "mui_window_own_screen": BuiltinFunc(
        name="mui_window_own_screen",
        params=["win"],
        return_type="BOOL",
        c_template="_dash_mui_window_own_screen(${win})",
        description="Full screen on a screen of its own, like the public one (before mui_window_open; false: on the public one)"
    ),
    "mui_width": BuiltinFunc(
        name="mui_width",
        params=["obj"],
        return_type="LONG",
        c_template="_dash_mui_size(${obj}, 0)",
        description="Width of an object on screen in pixels (0 before its window opens)"
    ),
    "mui_height": BuiltinFunc(
        name="mui_height",
        params=["obj"],
        return_type="LONG",
        c_template="_dash_mui_size(${obj}, 1)",
        description="Height of an object on screen in pixels (0 before its window opens)"
    ),
    "mui_wait_event": BuiltinFunc(
        name="mui_wait_event",
        params=[],
        return_type="LONG",
        c_template="_dash_mui_wait_event()",
        description="Wait for the next event and return its number; -1 to quit"
    ),
    "mui_poll_event": BuiltinFunc(
        name="mui_poll_event",
        params=[],
        return_type="LONG",
        c_template="_dash_mui_poll_event()",
        description="Like mui_wait_event without waiting: 0 when there is no event"
    ),
}


# =============================================================================
# Text (dashweb D2): searching, case, numbers. The results are new Strings.
# =============================================================================

def _text(name, params, ret, template, desc):
    return BuiltinFunc(name=name, params=params, return_type=ret, c_template=template, description=desc,
                       reads_only=True)


TEXT_FUNCTIONS = {
    "str_code": _text("str_code", ["s", "i"], "LONG", "_dash_str_code(${s}, ${i})",
                      "Code (0-255) of the character at position i, 0 outside the text"),
    "str_char": _text("str_char", ["code"], "STRPTR", "_dash_str_char(${code})",
                      "One-character String with that code"),
    "str_find": _text("str_find", ["s", "sub"], "LONG", "_dash_str_find(${s}, ${sub})",
                      "Position of the first sub in s, -1 if it is not there"),
    "str_find_from": _text("str_find_from", ["s", "sub", "start"], "LONG",
                           "_dash_str_find_from(${s}, ${sub}, ${start})",
                           "Position of the first sub in s from position start, -1 if none"),
    "str_starts": _text("str_starts", ["s", "prefix"], "BOOL", "_dash_str_starts(${s}, ${prefix})",
                        "Does s start with prefix?"),
    "str_ends": _text("str_ends", ["s", "suffix"], "BOOL", "_dash_str_ends(${s}, ${suffix})",
                      "Does s end with suffix?"),
    "str_lower": _text("str_lower", ["s"], "STRPTR", "_dash_str_lower(${s})",
                       "Lowercase copy (Latin-1: also accented letters)"),
    "str_upper": _text("str_upper", ["s"], "STRPTR", "_dash_str_upper(${s})",
                       "Uppercase copy (Latin-1: also accented letters)"),
    "str_trim": _text("str_trim", ["s"], "STRPTR", "_dash_str_trim(${s})",
                      "Copy without spaces, tabs and line ends at both ends"),
    "str_to_int": _text("str_to_int", ["s", "base"], "LONG", "_dash_str_to_int(${s}, ${base})",
                        "Number written in s in that base (2-36); Int(s) is base 10"),
    "str_from_int": _text("str_from_int", ["n", "base"], "STRPTR", "_dash_str_from_int(${n}, ${base})",
                          "n written in that base (2-36, lowercase letters)"),
    "str_replace": _text("str_replace", ["s", "from", "to"], "STRPTR", "_dash_str_replace(${s}, ${from}, ${to})",
                         "Copy with every from replaced by to"),
    "str_contains": _text("str_contains", ["s", "sub"], "BOOL", "_dash_str_contains(${s}, ${sub})",
                          "Whether sub is in s (\"\" is in every text)"),
    "str_split": BuiltinFunc(name="str_split", params=["s", "sep"], return_type="DashArrayLong *",
                             c_template="_dash_str_split(${s}, ${sep})", reads_only=True, list_of="String",
                             description="The pieces of s between each sep, as a new [String]; with sep \"\" or "
                                         "not found, [s]"),
    # dashweb D7: files and buffers as text
    "file_read_text": _text("file_read_text", ["filename"], "STRPTR", "_dash_file_read_text(${filename})",
                            "Whole file as a String (bytes 0 become spaces); nil if it cannot be read"),
    "file_write_text": _text("file_write_text", ["filename", "text"], "BOOL",
                             "_dash_file_write_text(${filename}, ${text})",
                             "Write the text as the whole file; true if it was all written"),
    "str_from_buffer": _text("str_from_buffer", ["buffer", "offset", "length"], "STRPTR",
                             "_dash_str_from_buffer(${buffer}, ${offset}, ${length})",
                             "String with length bytes of a buffer from offset (bytes 0 become spaces)"),
    "str_to_buffer": _text("str_to_buffer", ["s", "buffer", "offset"], "LONG",
                           "_dash_str_to_buffer(${s}, ${buffer}, ${offset})",
                           "Copy the bytes of s to buffer + offset; returns how many"),
}

# =============================================================================
# Network (dashweb D8): TCP over bsdsocket.library. Sockets are LONG (-1 = none).
# =============================================================================

NET_FUNCTIONS = {
    # Dash 2.0: connections in a task of their own (NETBG_RUNTIME), what Tachyon's lib/red.dash did with @native
    "net_bg_open": BuiltinFunc(
        name="net_bg_open", params=["host", "port", "timeout_ms"], return_type="LONG",
        c_template="_dash_net_bg_open(${host}, ${port}, ${timeout_ms})", reads_only=True,
        description="Ask for a TCP connection that a task of its own opens, sends and receives while the program "
                    "is busy (up to 48): its number, or -1. net_bg_state tells how it goes"),
    "net_bg_open_tls": BuiltinFunc(
        name="net_bg_open_tls", params=["host", "port", "timeout_ms"], return_type="LONG",
        c_template="_dash_net_bg_open_tls(${host}, ${port}, ${timeout_ms})", reads_only=True,
        description="net_bg_open with TLS (AmiSSL, its certificate checked)"),
    "net_bg_state": BuiltinFunc(
        name="net_bg_state", params=["c"], return_type="LONG", c_template="_dash_net_bg_state(${c})",
        description="1 asked, 2 connecting, 3 negotiating TLS, 4 open, 5 closed, 6 error (net_bg_error says why)"),
    "net_bg_stage": BuiltinFunc(
        name="net_bg_stage", params=["c"], return_type="LONG", c_template="_dash_net_bg_stage(${c})",
        description="While connecting, its stage, as net_connect_stage"),
    "net_bg_error": BuiltinFunc(
        name="net_bg_error", params=["c"], return_type="STRPTR", c_template="_dash_net_bg_error(${c})",
        description="Why a connection failed or closed, \"\" if it did not"),
    "net_bg_send": BuiltinFunc(
        name="net_bg_send", params=["c", "text"], return_type="BOOL", c_template="_dash_net_bg_send(${c}, ${text})",
        reads_only=True,
        description="Put text to send (the task sends it as soon as the connection is open); false without memory"),
    "net_bg_send_buffer": BuiltinFunc(
        name="net_bg_send_buffer", params=["c", "buffer", "n"], return_type="BOOL",
        c_template="_dash_net_bg_send_buffer(${c}, (APTR)${buffer}, ${n})",
        description="net_bg_send of n bytes of a buffer"),
    "net_bg_recv": BuiltinFunc(
        name="net_bg_recv", params=["c", "buffer", "max"], return_type="LONG",
        c_template="_dash_net_bg_recv(${c}, (APTR)${buffer}, ${max})",
        description="Up to max bytes of what has come, to a buffer, without waiting: how many (0: nothing yet), -1 "
                    "if it is closed and nothing is left. task_signal wakes the program when something comes"),
    "net_bg_pending": BuiltinFunc(
        name="net_bg_pending", params=["c"], return_type="LONG", c_template="_dash_net_bg_pending(${c})",
        description="How many bytes have come and are not read yet"),
    "net_bg_close": BuiltinFunc(
        name="net_bg_close", params=["c"], return_type="void", c_template="_dash_net_bg_close(${c})",
        description="Close a connection and free its number"),
    "net_bg_idle": BuiltinFunc(
        name="net_bg_idle", params=["ms"], return_type="void", c_template="_dash_net_bg_idle(${ms})",
        description="The task ends by itself after this many ms without traffic (2000; a connection the program keeps "
                    "reading, waiting for an answer, counts as traffic); another starts when needed"),
    "net_bg_stop": BuiltinFunc(
        name="net_bg_stop", params=[], return_type="void", c_template="_dash_net_bg_stop()",
        description="End the task now (it closes what is open) and wait for it; also done at the end of the program"),
    "net_connect": _text("net_connect", ["host", "port", "timeout_ms"], "LONG",
                         "_dash_net_connect(${host}, ${port}, ${timeout_ms})",
                         "TCP connection to host:port (name or address); the socket, or -1 (see net_error)"),
    "net_connect_start": _text("net_connect_start", ["host", "port", "timeout_ms"], "LONG",
                               "_dash_net_connect_start(${host}, ${port}, ${timeout_ms})",
                               "Start a TCP connection without waiting (the name is looked up in another "
                               "process); the socket, or -1 (see net_error)"),
    "net_connect_poll": _text("net_connect_poll", ["sock"], "LONG", "_dash_net_connect_poll(${sock})",
                              "Go on with net_connect_start without waiting: 1 connected, 0 not yet, "
                              "-1 failed (the socket is closed; see net_error)"),
    "net_connect_stage": _text("net_connect_stage", ["sock"], "LONG", "_dash_net_connect_stage(${sock})",
                               "What net_connect_start is doing: 0 looking the name up, 1 connecting, 2 done"),
    "net_send": _text("net_send", ["sock", "text"], "LONG", "_dash_net_send(${sock}, ${text})",
                      "Send the whole text; bytes sent or -1"),
    "net_send_buffer": _text("net_send_buffer", ["sock", "buffer", "length"], "LONG",
                             "_dash_net_send_buffer(${sock}, ${buffer}, ${length})",
                             "Send length bytes of a buffer; bytes sent or -1"),
    "net_recv": _text("net_recv", ["sock", "max", "timeout_ms"], "STRPTR",
                      "_dash_net_recv(${sock}, ${max}, ${timeout_ms})",
                      "Up to max bytes as text: \"\" if nothing came within timeout_ms (-1: wait), nil once closed"),
    "net_recv_buffer": _text("net_recv_buffer", ["sock", "buffer", "max", "timeout_ms"], "LONG",
                             "_dash_net_recv_buffer(${sock}, ${buffer}, ${max}, ${timeout_ms})",
                             "Up to max bytes into a buffer: the count, 0 on time out, -1 once closed"),
    "net_wait": _text("net_wait", ["sock", "timeout_ms"], "LONG", "_dash_net_select(${sock}, FALSE, ${timeout_ms})",
                      "Wait until there is something to read: 1 yes, 0 time out, -1 error"),
    "net_close": _text("net_close", ["sock"], "void", "_dash_net_close(${sock})", "Close the connection"),
    "net_resolve": _text("net_resolve", ["host"], "STRPTR", "_dash_net_resolve(${host})",
                         "IPv4 address of a host name (\"a.b.c.d\"), nil if unknown"),
    "net_error": _text("net_error", [], "STRPTR", "_dash_net_error()", "What went wrong in the last net_ call"),
    "net_listen": _text("net_listen", ["port"], "LONG", "_dash_net_listen(${port})",
                        "A TCP server on port (0: any free one, net_port says which): the listening socket, or -1 "
                        "(see net_error)"),
    "net_accept": _text("net_accept", ["sock", "timeout_ms"], "LONG", "_dash_net_accept(${sock}, ${timeout_ms})",
                        "The next connection to a net_listen server, waiting timeout_ms at most (-1: wait, 0: only "
                        "look): its socket (net_send, net_recv...), or -1 if none came"),
    "net_peer": _text("net_peer", ["sock"], "STRPTR", "_dash_net_peer(${sock})",
                      "The address (\"a.b.c.d\") of the other end of a TCP connection, nil if none"),
    "net_port": _text("net_port", ["sock"], "LONG", "_dash_net_port(${sock})",
                      "The local port of a socket (the one net_listen(0) or net_udp_open(0) got), -1 if none"),
    "net_udp_open": _text("net_udp_open", ["port"], "LONG", "_dash_net_udp_open(${port})",
                          "A UDP socket on port (0: any free one), broadcasts allowed: the socket, or -1 (net_close "
                          "closes it)"),
    "net_udp_send": _text("net_udp_send", ["sock", "host", "port", "text"], "LONG",
                          "_dash_net_udp_send(${sock}, ${host}, ${port}, ${text})",
                          "Send text as one datagram to host:port (\"255.255.255.255\": the whole local network); "
                          "bytes sent or -1"),
    "net_udp_send_buffer": _text("net_udp_send_buffer", ["sock", "host", "port", "buffer", "length"], "LONG",
                                 "_dash_net_udp_send_buffer(${sock}, ${host}, ${port}, ${buffer}, ${length})",
                                 "Send length bytes of a buffer as one datagram to host:port; bytes sent or -1"),
    "net_udp_recv": _text("net_udp_recv", ["sock", "max", "timeout_ms"], "STRPTR",
                          "_dash_net_udp_recv(${sock}, ${max}, ${timeout_ms})",
                          "The next datagram as text (up to max bytes): \"\" if none came within timeout_ms, nil on "
                          "error; who sent it: net_udp_from, net_udp_from_port"),
    "net_udp_recv_buffer": _text("net_udp_recv_buffer", ["sock", "buffer", "max", "timeout_ms"], "LONG",
                                 "_dash_net_udp_recv_buffer(${sock}, ${buffer}, ${max}, ${timeout_ms})",
                                 "The next datagram into a buffer: its length, 0 if none came in time, -1 on error"),
    "net_udp_from": _text("net_udp_from", [], "STRPTR", "_dash_net_udp_from()",
                          "The address (\"a.b.c.d\") of who sent the last datagram received"),
    "net_udp_from_port": _text("net_udp_from_port", [], "LONG", "_dash_net_udp_from_port()",
                               "The port of who sent the last datagram received (to answer it)"),
    "net_stack_running": _text("net_stack_running", [], "BOOL", "_dash_net_stack_running()",
                               "True if a TCP/IP stack is running (its bsdsocket.library is in memory); nothing is "
                               "loaded to know it. Roadshow's stays in memory after NetShutdown: that one is opened "
                               "and closed"),
    "net_release": _text("net_release", [], "void", "_dash_net_release()",
                         "Let the network go now: bsdsocket.library is closed, with the sockets, TLS connections and "
                         "name lookups still open; the next net_ call opens it again (the program's end does it too)"),
    "net_signal": _text("net_signal", [], "LONG", "_dash_net_signal()",
                        "Signal mask the sockets post on each event (connected, data, closed...), 0 if the TCP/IP "
                        "stack cannot: call it before each wait, mui_wait_event_signals(net_signal())"),
}

# =============================================================================
# TLS (dashweb D11): AmiSSL 5 over net_ sockets. Connections are LONG (-1 = none).
# =============================================================================

TLS_FUNCTIONS = {
    "tls_connect": _text("tls_connect", ["sock", "host"], "LONG", "_dash_tls_connect(${sock}, ${host})",
                         "TLS over a connected socket, verifying the certificate for host; -1 if not (net_error)"),
    "tls_connect_start": _text("tls_connect_start", ["sock", "host", "timeout_ms"], "LONG",
                               "_dash_tls_connect_start(${sock}, ${host}, ${timeout_ms})",
                               "TLS over a connected socket without waiting for the handshake; "
                               "the connection or -1 (see net_error)"),
    "tls_connect_poll": _text("tls_connect_poll", ["tls"], "LONG", "_dash_tls_connect_poll(${tls})",
                              "Go on with tls_connect_start: 1 done (certificate verified), 0 not yet, "
                              "-1 failed (the TLS connection is freed; see net_error)"),
    "tls_send": _text("tls_send", ["tls", "text"], "LONG", "_dash_tls_send(${tls}, ${text})",
                      "Send the whole text; bytes sent or -1"),
    "tls_send_buffer": _text("tls_send_buffer", ["tls", "buffer", "length"], "LONG",
                             "_dash_tls_send_buffer(${tls}, ${buffer}, ${length})",
                             "Send length bytes of a buffer; bytes sent or -1"),
    "tls_recv": _text("tls_recv", ["tls", "max", "timeout_ms"], "STRPTR",
                      "_dash_tls_recv(${tls}, ${max}, ${timeout_ms})",
                      "Like net_recv: \"\" if nothing came in time, nil once closed"),
    "tls_recv_buffer": _text("tls_recv_buffer", ["tls", "buffer", "max", "timeout_ms"], "LONG",
                             "_dash_tls_recv_buffer(${tls}, ${buffer}, ${max}, ${timeout_ms})",
                             "Like net_recv_buffer: the count, 0 on time out, -1 once closed"),
    "tls_close": _text("tls_close", ["tls"], "void", "_dash_tls_close(${tls})",
                       "End TLS on the connection (net_close the socket after)"),
    "tls_resumed": _text("tls_resumed", ["tls"], "BOOL", "_dash_tls_resumed(${tls})",
                         "True if the connection resumed an earlier session with the same server "
                         "(no key exchange)"),
}

# =============================================================================
# Fonts and colors (dashweb D9): disk fonts on the current RastPort, pens for RGB colors.
# =============================================================================

def _gfx(name, params, ret, template, desc):
    return BuiltinFunc(name=name, params=params, return_type=ret, c_template=template, description=desc,
                       needs_gfx=True, reads_only=True)


FONT_FUNCTIONS = {
    # Dash 2.0: TrueType fonts made by the program itself (runtime/fontweb), what Tachyon did with @native
    "font_from_ttf": BuiltinFunc(
        name="font_from_ttf", params=["file", "size", "width"], return_type="LONG",
        c_template="_dash_font_from_ttf(${file}, ${size}, ${width})", reads_only=True,
        description="A TrueType font (TTF, an OTF with TrueType outlines, or a WOFF or WOFF2 of them) at size pixels "
                    "of em and width % of its width (0: 100), its Latin-1 characters in one bit plane (stb_truetype): "
                    "a font for font_use, or 0. Free it with font_ttf_free, not font_close"),
    "font_ttf_icon": BuiltinFunc(
        name="font_ttf_icon", params=["file", "size", "code"], return_type="LONG",
        c_template="_dash_font_ttf_icon(${file}, ${size}, ${code})", reads_only=True,
        description="A font of the file whose \"A\" is the character code (an icon of a web font, in Unicode's "
                    "private area) at size pixels, the other letters empty: draw \"A\" with it; 0 if it cannot"),
    "font_ttf_free": BuiltinFunc(
        name="font_ttf_free", params=["font"], return_type="void", c_template="_dash_font_ttf_free(${font})",
        description="Free a font of font_from_ttf (not while a window still writes with it); the ones left are "
                    "freed at exit"),
    "font_ttf_forget": BuiltinFunc(
        name="font_ttf_forget", params=["file"], return_type="void", c_template="_dash_font_ttf_forget(${file})",
        reads_only=True,
        description="font_from_ttf keeps the last 8 files read for other sizes: read this one again next time"),
    "font_open": _gfx("font_open", ["name", "size"], "LONG", "_dash_font_open(${name}, ${size})",
                      "Open a font (\"helvetica.font\", size in pixels, at least 2): the font, or 0 if there is none"),
    "font_use": _gfx("font_use", ["font"], "void", "_dash_font_use(${font})", "Draw text with this font"),
    "font_close": _gfx("font_close", ["font"], "void", "_dash_font_close(${font})",
                       "Close a font (the open ones close at exit)"),
    "font_style": _gfx("font_style", ["style"], "void", "_dash_font_style(${style})",
                       "Text style: 0 plain, +1 underlined, +2 bold, +4 italic"),
    "font_height": _gfx("font_height", [], "LONG", "_dash_font_height()", "Height of the current font"),
    "font_baseline": _gfx("font_baseline", [], "LONG", "_dash_font_baseline()",
                          "Pixels from the top of the text to its baseline"),
    "font_text_width": _gfx("font_text_width", ["text"], "LONG", "_dash_font_text_width(${text})",
                            "Width of a text in pixels with the current font and style"),
    "font_size": _gfx("font_size", ["font"], "LONG", "_dash_font_size(${font})",
                      "Size the system gave for this font (the nearest it has)"),
    "color_pen": _gfx("color_pen", ["r", "g", "b"], "LONG", "_dash_color_pen(${r}, ${g}, ${b})",
                      "Pen with the color closest to r, g, b (0-255) on the screen drawn on; for gfx_pen"),
    "color_pen_free": _gfx("color_pen_free", ["pen"], "void", "_dash_color_pen_free(${pen})",
                           "One color_pen of this pen is no longer needed; when none is left it goes back to the screen"),
}

# =============================================================================
# Transparency: a colour mixed with what is drawn (RTG), or dithered (palette screens)
# =============================================================================

BLEND_FUNCTIONS = {
    "gfx_blend_rect": _gfx("gfx_blend_rect", ["x1", "y1", "x2", "y2", "rgb", "alpha"], "void",
                           "_dash_blend_rect(${x1}, ${y1}, ${x2}, ${y2}, ${rgb}, ${alpha})",
                           "Mix the color 0xRRGGBB with what is drawn, alpha 0-255 (palette screens: a 4x4 "
                           "dither of the closest pen)"),
    "gfx_gradient_rect": _gfx("gfx_gradient_rect", ["x1", "y1", "x2", "y2", "rgb1", "alpha1", "rgb2", "alpha2",
                                                    "vertical"], "void",
                              "_dash_gradient_rect(${x1}, ${y1}, ${x2}, ${y2}, ${rgb1}, ${alpha1}, ${rgb2}, "
                              "${alpha2}, ${vertical})",
                              "Gradient from (rgb1, alpha1) to (rgb2, alpha2), top to bottom if vertical, else left "
                              "to right, mixed with what is drawn"),
    "gfx_pixel_rgb": _gfx("gfx_pixel_rgb", ["x", "y"], "LONG", "_dash_pixel_rgb(${x}, ${y})",
                          "Color of a pixel as 0xRRGGBB (on a palette screen, its pen's color)"),
}

# =============================================================================
# RGB24 pictures from a buffer (video frames)
# =============================================================================

RGB_FUNCTIONS = {
    "gfx_rgb_draw": _gfx("gfx_rgb_draw", ["buffer", "width", "height", "x", "y"], "void",
                         "_dash_rgb_draw(${buffer}, ${width}, ${height}, ${x}, ${y})",
                         "Draw an RGB24 buffer (3 bytes a pixel, rows one after another) at x, y (RTG: in one "
                         "WritePixelArray; palette screens: the closest pens)"),
    "gfx_rgb_draw_scaled": _gfx("gfx_rgb_draw_scaled", ["buffer", "width", "height", "x", "y", "dest_width",
                                                        "dest_height"], "void",
                                "_dash_rgb_draw_scaled(${buffer}, ${width}, ${height}, ${x}, ${y}, ${dest_width}, "
                                "${dest_height})",
                                "Draw an RGB24 buffer at x, y as dest_width x dest_height (nearest pixel, row by row)"),
}

# =============================================================================
# C work in another process (dashweb D47)
# =============================================================================

TASK_FUNCTIONS = {
    "task_start": BuiltinFunc(
        name="task_start", params=["func", "arg"], return_type="LONG",
        c_template="_dash_task_start((APTR)${func}, ${arg})",
        description="Run a function f(arg: Int) -> Int in another process: a Dash one that only uses Int, Bool, "
                    "Float and builtins that give no texts or lists (the compiler checks it), or one of C (@extern, "
                    "@native: malloc/free yes, Dash strings and lists no); 128 KB of stack, the program's priority: "
                    "the task, or 0"),
    "task_start_with": BuiltinFunc(
        name="task_start_with", params=["func", "arg", "stack", "priority"], return_type="LONG",
        c_template="_dash_task_start_with((APTR)${func}, ${arg}, ${stack}, ${priority})",
        description="task_start with its stack in bytes (0: 128 KB) and its priority relative to the program's "
                    "(-1: it only runs when the program waits)"),
    "task_done": BuiltinFunc(
        name="task_done", params=["task"], return_type="BOOL",
        c_template="_dash_task_done(${task})",
        description="True once the function has returned (does not wait)"),
    # Trasfondo: drawing on the Workbench's background, behind its icons
    "desktop_canvas": BuiltinFunc(
        name="desktop_canvas", params=["x", "y", "width", "height"], return_type="APTR",
        c_template="_dash_desk_canvas(${x}, ${y}, ${width}, ${height})",
        description="An area of the Workbench's desktop (below the screen's title bar), behind the icons and "
                    "without clicks, in backdrop mode or not, planar or RTG; negative x or y: from the right or "
                    "bottom edge (-1 touches it). 0 if it cannot be"),
    "desktop_canvas_on_draw": BuiltinFunc(
        name="desktop_canvas_on_draw", params=["canvas", "func"], return_type="void",
        c_template="_dash_desk_on_draw(${canvas}, (APTR)${func})",
        description="Function f(x, y, width, height) that draws the area with gfx_ (from 0, 0), over the "
                    "wallpaper below it"),
    "desktop_canvas_update": BuiltinFunc(
        name="desktop_canvas_update", params=["canvas"], return_type="void",
        c_template="_dash_desk_update(${canvas})",
        description="Draw the area again now and show what changed, without touching the icons"),
    "desktop_canvas_update_area": BuiltinFunc(
        name="desktop_canvas_update_area", params=["canvas", "x", "y", "width", "height"], return_type="void",
        c_template="_dash_desk_update_area(${canvas}, ${x}, ${y}, ${width}, ${height})",
        description="desktop_canvas_update only in that part of the area: the drawing is clipped to it and only "
                    "it is compared (the rest stays as it was; where the desktop was repainted since, it draws "
                    "too)"),
    "desktop_canvas_veil": BuiltinFunc(
        name="desktop_canvas_veil", params=["canvas", "rgb", "alpha"], return_type="void",
        c_template="_dash_desk_veil(${canvas}, ${rgb}, ${alpha})",
        description="The wallpaper below the drawing mixed with rgb (0xRRGGBB) at alpha (0-255; 0: none), once "
                    "and again only where the desktop repaints it: as a gfx_blend_rect over the whole area in "
                    "each drawing, without its cost. Takes away the veils of desktop_canvas_veil_rect. Seen "
                    "from the next desktop_canvas_update"),
    "desktop_canvas_veil_rect": BuiltinFunc(
        name="desktop_canvas_veil_rect", params=["canvas", "x", "y", "width", "height", "rgb", "alpha"],
        return_type="BOOL",
        c_template="_dash_desk_veil_rect(${canvas}, ${x}, ${y}, ${width}, ${height}, ${rgb}, ${alpha})",
        description="One more veil, only in that rectangle, mixed once over desktop_canvas_veil's (which takes "
                    "them away: call it first): a box that is always there. Up to 16; false when full"),
    "desktop_canvas_drawing": BuiltinFunc(
        name="desktop_canvas_drawing", params=["x", "y", "width", "height"], return_type="BOOL",
        c_template="_dash_desk_drawing(${x}, ${y}, ${width}, ${height})",
        description="In the drawing function: true if that rectangle reaches the part being drawn (all the area, "
                    "or the one of desktop_canvas_update_area with what the desktop repainted), to skip what "
                    "would not show. Outside it, always true"),
    "desktop_canvas_free": BuiltinFunc(
        name="desktop_canvas_free", params=["canvas"], return_type="void",
        c_template="_dash_desk_free(${canvas})",
        description="The wallpaper back in the area (the program's end does it too)"),
    # Trasfondo: the CPU each task takes (exec's task switch hooks and the EClock, as PM)
    # Trasfondo: a program without a window that can be stopped
    "break_check": BuiltinFunc(
        name="break_check", params=[], return_type="BOOL",
        c_template="((SetSignal(0L, SIGBREAKF_CTRL_C) & SIGBREAKF_CTRL_C) != 0)",
        description="True if Ctrl-C came (\"Break\" in the Shell, or another copy: single_instance); it is cleared"),
    "single_instance": BuiltinFunc(
        name="single_instance", params=["name"], return_type="BOOL",
        c_template="_dash_single_instance(${name})",
        description="One copy at a time: false if another copy of the program (a public port with that name) "
                    "runs, which gets Ctrl-C; true otherwise (the port is the program's until it ends)"),
    # Trasfondo as a commodity: Exchange shows it and sends it commands
    "tooltype": BuiltinFunc(
        name="tooltype", params=["name", "default"], return_type="STRPTR",
        c_template="_dash_tooltype(${name}, ${default})",
        reads_only=True, description="A tooltype of the program: from the Shell, the argument NAME=value (NAME=\"a b\" too); else (or "
                    "from the Workbench) the tooltype of its icon; default if it is in neither"),
    "cx_broker": BuiltinFunc(
        name="cx_broker", params=["name", "title", "description", "priority"], return_type="BOOL",
        c_template="_dash_cx_broker_new(${name}, ${title}, ${description}, ${priority})",
        description="The program in Exchange as a commodity, with Show and Hide, enabled (name up to 23 letters, title "
                    "and description up to 39); false without commodities.library or with that name there. It goes "
                    "at the program's end"),
    "cx_hotkey": BuiltinFunc(
        name="cx_hotkey", params=["description"], return_type="BOOL",
        c_template="_dash_cx_hotkey(${description})",
        description="The commodity's hotkey, from its description (\"ctrl alt t\"): cx_command gives 6 when it is "
                    "pressed; false if the description is not valid (or there is no cx_broker); \"\" takes it away"),
    "cx_key_add": BuiltinFunc(
        name="cx_key_add", params=["description", "n"], return_type="BOOL",
        c_template="_dash_cx_key_add(${description}, ${n})",
        description="One more hotkey for the commodity (up to 32, n from 1 to 32; a mouse button too: \"rawmouse "
                    "lalt mouse_leftpress\"): cx_command gives 100 + n when it is pressed, and the event goes no "
                    "further; \"\" takes hotkey n away; false if the description is not valid (or there is no cx_broker)"),
    "cx_command": BuiltinFunc(
        name="cx_command", params=[], return_type="LONG",
        c_template="_dash_cx_command()",
        description="The next command from Exchange or the hotkey: 0 none, 1 hide, 2 show, 3 disable, 4 enable, "
                    "5 kill, 6 hotkey. Disable and enable switch the commodity off and on (the hotkey too)"),
    "cx_wait": BuiltinFunc(
        name="cx_wait", params=["ms"], return_type="LONG",
        c_template="_dash_cx_wait(${ms})",
        description="Waits, spending nothing, until a command comes (given as cx_command), Ctrl-C (-1, cleared) "
                    "or ms milliseconds pass (0)"),
    # Trasfondo 2.0: the windows of every program on the Workbench screen (TrasfondoVentanas)
    "wm_read": BuiltinFunc(
        name="wm_read", params=[], return_type="LONG", c_template="_dash_wm_read()",
        description="Read the windows of the Workbench screen, front to back (up to 64): how many, for wm_id, "
                    "wm_title, wm_task, wm_box and wm_flags, until the next wm_read"),
    "wm_id": BuiltinFunc(
        name="wm_id", params=["i"], return_type="LONG", c_template="_dash_wm_id(${i})",
        description="The id of window i of the last wm_read, for wm_set_box, wm_front... (0 outside the list)"),
    "wm_title": BuiltinFunc(
        name="wm_title", params=["i"], return_type="STRPTR", c_template="_dash_wm_title_of(${i})",
        description="The title of window i of the last wm_read (\"\" if it has none)"),
    "wm_task": BuiltinFunc(
        name="wm_task", params=["i"], return_type="STRPTR", c_template="_dash_wm_task_of(${i})",
        description="The program of window i: the command of a Shell process (without its path), else its task's "
                    "name (\"Workbench\")"),
    "wm_path": BuiltinFunc(
        name="wm_path", params=["i"], return_type="STRPTR", c_template="_dash_wm_path_of(${i})",
        description="The path of the program of window i (its directory, the one its process was loaded from, and "
                    "its name): \"\" if it is not a process's, or the window closed since wm_read"),
    "file_real_path": BuiltinFunc(
        name="file_real_path", params=["path"], return_type="STRPTR", c_template="_dash_file_real_path(${path})",
        reads_only=True,
        description="The real path of a file or drawer as its filesystem names it (\"SYS:Utilities/Clock\" gives "
                    "\"System:Utilities/Clock\"), to compare it with wm_path: \"\" if it is not there"),
    "app_window": BuiltinFunc(
        name="app_window", params=["handle"], return_type="BOOL", c_template="_dash_app_window(${handle})",
        description="The window (0 the current one, or a handle of window_create) takes icons dropped on it from the "
                    "Workbench (AppWindow): true if it does. app_drop gives them"),
    "app_drop": BuiltinFunc(
        name="app_drop", params=[], return_type="STRPTR", c_template="_dash_app_drop()",
        description="The path of the next icon dropped on an app_window, \"\" if none (poll it from On Timer); "
                    "app_drop_x and app_drop_y, where it fell"),
    "app_drop_x": BuiltinFunc(
        name="app_drop_x", params=[], return_type="LONG", c_template="_dash_app_drop_x()",
        description="Where the last icon of app_drop fell: x from the window's corner"),
    "app_drop_y": BuiltinFunc(
        name="app_drop_y", params=[], return_type="LONG", c_template="_dash_app_drop_y()",
        description="Where the last icon of app_drop fell: y from the window's corner"),
    "icon_load": BuiltinFunc(
        name="icon_load", params=["path"], return_type="LONG", c_template="_dash_icon_load(${path})",
        reads_only=True,
        description="The icon (.info) of a program, drawer or file (path without \".info\"), by icon.library, with "
                    "the colours of the window's screen (3.5+: colour and PNG icons, and the default one of its type "
                    "if it has none): a number for icon_draw, or 0"),
    "icon_draw": BuiltinFunc(
        name="icon_draw", params=["icon", "x", "y"], return_type="void", c_template="_dash_icon_draw(${icon}, ${x}, ${y})",
        needs_gfx=True,
        description="Draws an icon of icon_load with its top left corner at (x, y), as the Workbench does, without its "
                    "name or frame"),
    "icon_draw_size": BuiltinFunc(
        name="icon_draw_size", params=["icon", "x", "y", "width", "height"], return_type="void",
        c_template="_dash_icon_draw_size(${icon}, ${x}, ${y}, ${width}, ${height})", needs_gfx=True,
        description="Draws an icon of icon_load at (x, y) at width x height, smaller or bigger, with soft edges (on "
                    "a true colour screen; on others, at its size, centred in that box)"),
    "icon_width": BuiltinFunc(
        name="icon_width", params=["icon"], return_type="LONG", c_template="_dash_icon_size(${icon}, 0)",
        description="The width of an icon of icon_load as icon_draw draws it (0 without it)"),
    "icon_height": BuiltinFunc(
        name="icon_height", params=["icon"], return_type="LONG", c_template="_dash_icon_size(${icon}, 1)",
        description="The height of an icon of icon_load as icon_draw draws it (0 without it)"),
    "icon_free": BuiltinFunc(
        name="icon_free", params=["icon"], return_type="void", c_template="_dash_icon_free(${icon})",
        description="Frees an icon of icon_load (the ones left, at exit)"),
    "wm_box": BuiltinFunc(
        name="wm_box", params=["i", "what"], return_type="LONG", c_template="_dash_wm_box_of(${i}, ${what})",
        description="Of window i: 0 left, 1 top, 2 width, 3 height, 4 minimum width, 5 minimum height, 6 maximum "
                    "width, 7 maximum height (0 or 65535: no limit); -1 outside the list"),
    "wm_flags": BuiltinFunc(
        name="wm_flags", params=["i"], return_type="LONG", c_template="_dash_wm_flags(${i})",
        description="Of window i, added up: 1 it can be sized, 2 backdrop, 4 borderless, 8 active, 16 drag bar, "
                    "32 the program's own, 64 a Workbench drawer, 128 with a requester open"),
    "wm_set_box": BuiltinFunc(
        name="wm_set_box", params=["id", "x", "y", "width", "height"], return_type="BOOL",
        c_template="_dash_wm_set_box(${id}, ${x}, ${y}, ${width}, ${height})",
        description="Move and size a window by its id, within its limits and its screen (one without a size "
                    "gadget keeps its size); false if it is not open any more. Intuition does it right after"),
    "wm_front": BuiltinFunc(
        name="wm_front", params=["id"], return_type="BOOL", c_template="_dash_wm_do(${id}, 0)",
        description="A window in front of the others; false if it is not open any more"),
    "wm_back": BuiltinFunc(
        name="wm_back", params=["id"], return_type="BOOL", c_template="_dash_wm_do(${id}, 1)",
        description="A window behind the others; false if it is not open any more"),
    "wm_activate": BuiltinFunc(
        name="wm_activate", params=["id"], return_type="BOOL", c_template="_dash_wm_do(${id}, 2)",
        description="Make a window the active one (keys go to it); false if it is not open any more"),
    "wm_zip": BuiltinFunc(
        name="wm_zip", params=["id"], return_type="BOOL", c_template="_dash_wm_do(${id}, 3)",
        description="A window to its other size, as its zoom gadget does; false if it is not open any more"),
    "wm_active": BuiltinFunc(
        name="wm_active", params=[], return_type="LONG", c_template="_dash_wm_active()",
        description="The id of the active window, if it is on the Workbench screen; 0 if not"),
    "wm_at": BuiltinFunc(
        name="wm_at", params=["x", "y"], return_type="LONG", c_template="_dash_wm_at(${x}, ${y})",
        description="The id of the window at (x, y) of the Workbench screen, the one in front there; 0 if none"),
    "wm_pointer_x": BuiltinFunc(
        name="wm_pointer_x", params=[], return_type="LONG", c_template="_dash_wm_pointer(0)",
        description="Where the pointer is on the Workbench screen: x"),
    "wm_pointer_y": BuiltinFunc(
        name="wm_pointer_y", params=[], return_type="LONG", c_template="_dash_wm_pointer(1)",
        description="Where the pointer is on the Workbench screen: y"),
    "wm_bar_height": BuiltinFunc(
        name="wm_bar_height", params=[], return_type="LONG", c_template="_dash_wm_bar_height()",
        description="The height of the Workbench screen's title bar (where windows usually start)"),
    "wm_bar_gadgets": BuiltinFunc(
        name="wm_bar_gadgets", params=[], return_type="LONG", c_template="_dash_wm_bar_gadgets()",
        description="How far from the right edge of the Workbench screen's title bar its system gadgets start (the "
                    "depth gadget), asked to the screen; 0 if it cannot tell"),
    # Trasfondo: disks, network and WiFi for a meter; each reading afresh, none waits longer than its time
    "disks_read": BuiltinFunc(
        name="disks_read", params=["ms"], return_type="LONG",
        c_template="_dash_disks_read(${ms})",
        description="Reads the mounted volumes (with a disk in) and their size and free space, asked to all at once "
                    "and waiting ms milliseconds at most: how many there are. Nothing asks for a disk"),
    "disk_name": BuiltinFunc(
        name="disk_name", params=["i"], return_type="STRPTR",
        c_template="_dash_disk_name(${i})",
        description="The name of volume i (0 to disks_read() - 1) of the last disks_read, without the colon"),
    "disk_kb": BuiltinFunc(
        name="disk_kb", params=["i"], return_type="LONG",
        c_template="_dash_disk_kb(${i})",
        description="The size of volume i in KB (as Info shows it); -1 if it did not answer in time"),
    "disk_free_kb": BuiltinFunc(
        name="disk_free_kb", params=["i"], return_type="LONG",
        c_template="_dash_disk_free_kb(${i})",
        description="The free space of volume i in KB; -1 if it did not answer in time"),
    "net_ifs_read": BuiltinFunc(
        name="net_ifs_read", params=[], return_type="LONG",
        c_template="_dash_net_ifs_read()",
        description="Reads the network interfaces of Roadshow (lo0 included), their state and bytes: how many; -1 "
                    "without a TCP/IP stack or with one that does not tell (AmiTCP, Miami)"),
    "net_if_name": BuiltinFunc(
        name="net_if_name", params=["i"], return_type="STRPTR",
        c_template="_dash_net_if_name(${i})",
        description="The name of interface i (0 to net_ifs_read() - 1) of the last net_ifs_read"),
    "net_if_up": BuiltinFunc(
        name="net_if_up", params=["i"], return_type="BOOL",
        c_template="_dash_net_if_up(${i})",
        description="True if interface i is up (connected)"),
    "net_if_bytes_in": BuiltinFunc(
        name="net_if_bytes_in", params=["i"], return_type="LONG",
        c_template="_dash_net_if_bytes_in(${i})",
        description="The bytes received by interface i (the low 32 bits: the difference of two readings is the "
                    "bytes in between, even past 2 GB)"),
    "net_if_bytes_out": BuiltinFunc(
        name="net_if_bytes_out", params=["i"], return_type="LONG",
        c_template="_dash_net_if_bytes_out(${i})",
        description="The bytes sent by interface i (the low 32 bits, like net_if_bytes_in)"),
    "pistorm_temperature": BuiltinFunc(
        name="pistorm_temperature", params=[], return_type="LONG",
        c_template="_dash_pistorm_temperature()",
        description="Temperature of the Raspberry Pi of a PiStorm (Emu68), in tenths of a degree Celsius (523: "
                    "52.3), from its firmware through Emu68's mailbox.resource; -1 without Emu68"),
    "wifi_read": BuiltinFunc(
        name="wifi_read", params=["interface", "ms"], return_type="LONG",
        c_template="_dash_wifi_read(${interface}, ${ms})",
        reads_only=True, description="Asks the SANA-II driver of a Roadshow interface for its WiFi signal, waiting ms milliseconds at "
                    "most: 0 read (wifi_signal, wifi_noise), 1 no answer in time, 2 the driver does not tell, 3 no "
                    "such interface, 4 the driver gives an error (offline), 5 the stack has the driver only for "
                    "itself, -1 no Roadshow"),
    "wifi_read_device": BuiltinFunc(
        name="wifi_read_device", params=["driver", "unit", "ms"], return_type="LONG",
        c_template="_dash_wifi_read_device(${driver}, ${unit}, ${ms})",
        reads_only=True, description="Like wifi_read, asking a SANA-II driver that is in use (\"wifipi.device\", unit 0) directly, "
                    "with any TCP/IP stack: 0 read, 1 no answer in time, 2 the driver does not tell, 3 no such driver "
                    "in use, 4 offline, 5 the stack has it only for itself"),
    "net_drivers_read": BuiltinFunc(
        name="net_drivers_read", params=[], return_type="LONG",
        c_template="_dash_net_drivers_read()",
        description="Reads the SANA-II network drivers in use, with any TCP/IP stack (the ones of DEVS:Networks "
                    "that something has open): how many"),
    "net_driver_name": BuiltinFunc(
        name="net_driver_name", params=["i"], return_type="STRPTR",
        c_template="_dash_net_driver_name(${i})",
        description="The name of driver i (0 to net_drivers_read() - 1) of the last net_drivers_read "
                    "(\"wifipi.device\")"),
    "net_driver_read": BuiltinFunc(
        name="net_driver_read", params=["driver", "unit", "ms"], return_type="LONG",
        c_template="_dash_net_driver_read(${driver}, ${unit}, ${ms})",
        reads_only=True, description="Asks a SANA-II driver in use for its packets in and out, waiting ms at most: the codes of "
                    "wifi_read_device (0 read: net_driver_packets_in, net_driver_packets_out)"),
    "net_driver_has_bytes": BuiltinFunc(
        name="net_driver_has_bytes", params=[], return_type="BOOL",
        c_template="_dash_net_driver_has_bytes()",
        description="True if the driver of the last net_driver_read counts bytes (its IPv4, IPv6 and ARP packets): "
                    "net_driver_bytes_in and net_driver_bytes_out"),
    "net_driver_bytes_in": BuiltinFunc(
        name="net_driver_bytes_in", params=[], return_type="LONG",
        c_template="_dash_net_driver_bytes_in()",
        description="The bytes received by the driver of the last net_driver_read (the low 32 bits), if "
                    "net_driver_has_bytes"),
    "net_driver_bytes_out": BuiltinFunc(
        name="net_driver_bytes_out", params=[], return_type="LONG",
        c_template="_dash_net_driver_bytes_out()",
        description="The bytes sent by the driver of the last net_driver_read, if net_driver_has_bytes"),
    "net_driver_packets_in": BuiltinFunc(
        name="net_driver_packets_in", params=[], return_type="LONG",
        c_template="_dash_net_driver_packets_in()",
        description="The packets received by the driver of the last net_driver_read that gave 0"),
    "net_driver_packets_out": BuiltinFunc(
        name="net_driver_packets_out", params=[], return_type="LONG",
        c_template="_dash_net_driver_packets_out()",
        description="The packets sent by the driver of the last net_driver_read that gave 0"),
    "wifi_signal": BuiltinFunc(
        name="wifi_signal", params=[], return_type="LONG",
        c_template="_dash_wifi_signal()",
        description="The signal level of the last wifi_read that gave 0, in dBm (-30 very good, -90 very bad)"),
    "wifi_noise": BuiltinFunc(
        name="wifi_noise", params=[], return_type="LONG",
        c_template="_dash_wifi_noise_level()",
        description="The noise level of the last wifi_read that gave 0, in dBm"),
    # Ratonera: a curve for each mouse (the Amiga one, and each USB one of Poseidon's hid.class)
    "usb_hid_read": BuiltinFunc(
        name="usb_hid_read", params=[], return_type="LONG",
        c_template="_dash_usb_hid_read()",
        description="Reads the USB devices (each interface) that Poseidon's hid.class handles: how many; -1 without "
                    "poseidon.library 4"),
    "usb_hid_name": BuiltinFunc(
        name="usb_hid_name", params=["i"], return_type="STRPTR",
        c_template="_dash_usb_hid_name(${i})",
        description="The product name of USB device i (0 to usb_hid_read() - 1) of the last usb_hid_read"),
    "usb_hid_maker": BuiltinFunc(
        name="usb_hid_maker", params=["i"], return_type="STRPTR",
        c_template="_dash_usb_hid_maker(${i})",
        description="The manufacturer of USB device i"),
    "usb_hid_vendor": BuiltinFunc(
        name="usb_hid_vendor", params=["i"], return_type="LONG",
        c_template="_dash_usb_hid_vendor(${i})",
        description="The VendorID of USB device i"),
    "usb_hid_product": BuiltinFunc(
        name="usb_hid_product", params=["i"], return_type="LONG",
        c_template="_dash_usb_hid_product(${i})",
        description="The ProductID of USB device i"),
    "usb_hid_kind": BuiltinFunc(
        name="usb_hid_kind", params=["i"], return_type="LONG",
        c_template="_dash_usb_hid_kind(${i})",
        description="What USB device i is: 1 mouse, 2 keyboard, 0 other (many trackpads)"),
    "usb_hid_emitter": BuiltinFunc(
        name="usb_hid_emitter", params=["i"], return_type="LONG",
        c_template="_dash_usb_hid_emitter(${i})",
        description="The emitter of USB device i: the number of the hid.class task that sends its moves, for "
                    "mouse_curve"),
    "mouse_curve": BuiltinFunc(
        name="mouse_curve", params=["emitter", "factors"], return_type="BOOL",
        c_template="_dash_mouse_curve(${emitter}, ${factors})",
        description="The acceleration curve of a mouse: emitter 0 is the Amiga mouse (and every move not from a "
                    "USB mouse), else a usb_hid_emitter. factors: a list of hundredths (100 = as it comes), entry i "
                    "for a move of i units, the last one from there on (up to 32); [] takes it away. The fractions "
                    "left are kept. False if input.device does not open or there are 16 emitters already"),
    "mouse_curve_events": BuiltinFunc(
        name="mouse_curve_events", params=["emitter"], return_type="LONG",
        c_template="_dash_mouse_curve_events(${emitter})",
        description="How many moves an emitter's curve has scaled"),
    "mouse_curves_off": BuiltinFunc(
        name="mouse_curves_off", params=[], return_type="void",
        c_template="_dash_mouse_curves_off()",
        description="Takes the curves out of input.device now (the program's end does it too); a mouse_curve puts "
                    "them back. Under another program's patch, a stub that passes everything through stays"),
    "mouse_patch_left": BuiltinFunc(
        name="mouse_patch_left", params=[], return_type="LONG",
        c_template="_dash_mouse_patch_left()",
        description="How many stubs were left under another program's patch of input.device (they pass everything "
                    "through, for good)"),
    "mouse_prefs_ticks": BuiltinFunc(
        name="mouse_prefs_ticks", params=[], return_type="LONG",
        c_template="_dash_mouse_prefs_ticks()",
        description="The system's mouse speed (Input preferences): 1 fastest, 2, 4 slowest"),
    "mouse_prefs_accel": BuiltinFunc(
        name="mouse_prefs_accel", params=[], return_type="BOOL",
        c_template="_dash_mouse_prefs_accel()",
        description="True if the system's mouse acceleration (Input preferences) is on"),
    "mouse_prefs_set": BuiltinFunc(
        name="mouse_prefs_set", params=["ticks", "accel"], return_type="void",
        c_template="_dash_mouse_prefs_set(${ticks}, ${accel})",
        description="Sets the system's mouse speed and acceleration; they go back as they were at the program's end"),
    # dashweb D71: translations with locale.library's catalogs
    "tr": BuiltinFunc(
        name="tr", params=["id", "text"], return_type="STRPTR",
        c_template="_dash_tr(${id}, ${text})",
        description="The text number id of the program's catalog (@catalog) in the user's language; text (the "
                    "program's own) without a catalog, without that number or without locale.library"),
    "catalog_open": BuiltinFunc(
        name="catalog_open", params=["name", "version"], return_type="BOOL",
        c_template="_dash_catalog_open(${name}, ${version})",
        description="Opens another catalog (\"X.catalog\", version 0: any) in the user's languages instead of "
                    "the one in use; false if there is none (tr gives the program's own texts)"),
    "catalog_language": BuiltinFunc(
        name="catalog_language", params=[], return_type="STRPTR",
        c_template="_dash_catalog_language()",
        description="The language of the catalog in use (\"english\"), \"\" without one"),
    # Trasfondo 0.7: the clock, dates, and the program's version
    "clock_read": BuiltinFunc(
        name="clock_read", params=[], return_type="void", c_template="_dash_clock_read()",
        description="Takes the date and time of the system's clock: clock_year, clock_month... give its parts"),
    "clock_year": BuiltinFunc(
        name="clock_year", params=[], return_type="LONG", c_template="_dash_clock_part(0)",
        description="The year of the last clock_read (1978...)"),
    "clock_month": BuiltinFunc(
        name="clock_month", params=[], return_type="LONG", c_template="_dash_clock_part(1)",
        description="The month of the last clock_read (1 to 12)"),
    "clock_day": BuiltinFunc(
        name="clock_day", params=[], return_type="LONG", c_template="_dash_clock_part(2)",
        description="The day of the month of the last clock_read (1 to 31)"),
    "clock_weekday": BuiltinFunc(
        name="clock_weekday", params=[], return_type="LONG", c_template="_dash_clock_part(3)",
        description="The day of the week of the last clock_read: 0 Sunday, 1 Monday ... 6 Saturday"),
    "clock_hour": BuiltinFunc(
        name="clock_hour", params=[], return_type="LONG", c_template="_dash_clock_part(4)",
        description="The hour of the last clock_read (0 to 23)"),
    "clock_minute": BuiltinFunc(
        name="clock_minute", params=[], return_type="LONG", c_template="_dash_clock_part(5)",
        description="The minute of the last clock_read"),
    "clock_second": BuiltinFunc(
        name="clock_second", params=[], return_type="LONG", c_template="_dash_clock_part(6)",
        description="The second of the last clock_read"),
    "date_text": BuiltinFunc(
        name="date_text", params=["format"], return_type="STRPTR", c_template="_dash_date_text(${format})",
        reads_only=True, description="The date and time now as format says, with locale.library's FormatDate in the user's language "
                    "and country: %A day, %d-%m-%Y, %b month, %H:%M:%S... (in English without locale.library)"),
    # Lorraine D19: how numbers and dates are written in the user's language and country
    "locale_gmt_offset": BuiltinFunc(
        name="locale_gmt_offset", params=[], return_type="LONG", c_template="_dash_locale_gmt_offset()",
        description="How many minutes the Amiga's clock is ahead of GMT (60 in Spain in winter), from Locale; 0 "
                    "without locale.library. git keeps its times so (\"+0100\")"),
    "locale_decimal_point": BuiltinFunc(
        name="locale_decimal_point", params=[], return_type="STRPTR", c_template="_dash_locale_decimal_point()",
        description="What goes before the decimals in the user's country: \",\" in Spain, \".\" in English (also "
                    "without locale.library)"),
    "locale_group_separator": BuiltinFunc(
        name="locale_group_separator", params=[], return_type="STRPTR",
        c_template="_dash_locale_group_separator()",
        description="What separates the thousands in the user's country: \".\" in Spain (1.234,5), \",\" in "
                    "English (1,234.5); maybe \"\""),
    "locale_date_order": BuiltinFunc(
        name="locale_date_order", params=[], return_type="STRPTR", c_template="_dash_locale_date_order()",
        description="The order of day, month and year in the user's short date: \"DMY\", \"MDY\" or \"YMD\""),
    "program_version": BuiltinFunc(
        name="program_version", params=[], return_type="STRPTR", c_template="_dash_program_version()",
        description="The program's name and version of @version (\"Trasfondo 0.7\"); \"\" without it"),
    # Trasfondo 0.7: watching a file, running programs, relaunching itself
    "file_notify": BuiltinFunc(
        name="file_notify", params=["path"], return_type="LONG", c_template="_dash_file_notify(${path})",
        description="Watch a file (it may not be there yet): its number (1 to 8), 0 if it cannot be watched. "
                    "cx_wait gives 7 when it changes; file_changed(n) says whether it did"),
    "file_changed": BuiltinFunc(
        name="file_changed", params=["n"], return_type="BOOL", c_template="_dash_file_changed(${n})",
        description="True if the file watched with that number changed since the last file_changed"),
    "file_notify_end": BuiltinFunc(
        name="file_notify_end", params=["n"], return_type="void", c_template="_dash_file_notify_end(${n})",
        description="Stop watching that file (the program's end stops them all)"),
    "file_notify_signal": BuiltinFunc(
        name="file_notify_signal", params=[], return_type="LONG", c_template="_dash_file_notify_signal()",
        description="The signal of the watched files, for mui_wait_event_signals (0 before any file_notify)"),
    "run_program": BuiltinFunc(
        name="run_program", params=["command"], return_type="BOOL", c_template="_dash_run_program(${command})",
        description="Start a command line (\"SYS:Prefs/Font\", \"\\\"Work:My Prog\\\" arg\") in another process "
                    "without waiting, its input and output NIL:; false if it could not start"),
    "program_relaunch": BuiltinFunc(
        name="program_relaunch", params=[], return_type="void", c_template="_dash_program_relaunch()",
        description="When the program ends, start it again (after everything of its end, single_instance's port "
                    "too), as it started: from the Workbench (3.5+: with its icon) or from a Shell with its "
                    "arguments. For updating itself"),
    # Dash 2.0: what programs did with @native (docs/DASHC_NATIVE.md)
    "time_unix": BuiltinFunc(
        name="time_unix", params=[], return_type="LONG", c_template="_dash_time_unix()",
        description="The system's clock as seconds since 1 January 1970 (for HTTP dates and cookies)"),
    "clock_days": BuiltinFunc(
        name="clock_days", params=[], return_type="LONG", c_template="_dash_clock_days()",
        description="Days since 1 January 1978 by the system's clock (DateStamp's ds_Days)"),
    "mem_largest": BuiltinFunc(
        name="mem_largest", params=[], return_type="LONG", c_template="(LONG)AvailMem(MEMF_ANY | MEMF_LARGEST)",
        description="The largest free block of memory, chip or fast, in bytes"),
    "program_exit": BuiltinFunc(
        name="program_exit", params=["rc"], return_type="void", c_template="_dash_program_exit(${rc})",
        description="Ends the program now with that return code (5 warning, 10 error, 20 failure), after the usual "
                    "cleanup: windows, files and memory"),
    "run_command": BuiltinFunc(
        name="run_command", params=["command"], return_type="LONG", c_template="_dash_run_command(${command})",
        reads_only=True,
        description="Run a command line and wait for it to end, its output the program's own: its return code, "
                    "-1 if it could not start"),
    # Dash 2.0 (Inferencia, the IDE): running a command and taking its output; environment variables
    "run_capture": BuiltinFunc(
        name="run_capture", params=["command", "timeout_ms"], return_type="STRPTR",
        c_template="_dash_run_capture(${command}, ${timeout_ms})", reads_only=True,
        description="Run a command line and wait for it to end: what it wrote, its return code in run_rc(). With "
                    "timeout_ms over 0, when that time runs out the command gets Ctrl-C (and again every second until "
                    "it ends). Only its output: AmigaOS gives a command run this way no error channel (a C program's "
                    "stderr goes to the console; dashc writes its errors to its output on the Amiga)"),
    "run_start": BuiltinFunc(
        name="run_start", params=["command", "timeout_ms"], return_type="LONG",
        c_template="_dash_run_start(${command}, ${timeout_ms})", reads_only=True,
        description="run_capture without waiting: a number for run_ready, run_break and run_finish, 0 if it "
                    "could not start. The program waits at its end for the ones it did not finish"),
    "run_ready": BuiltinFunc(
        name="run_ready", params=["run"], return_type="BOOL", c_template="_dash_run_ready(${run})",
        description="True when a run_start has ended (it does not wait; it also applies the time limit)"),
    "run_break": BuiltinFunc(
        name="run_break", params=["run"], return_type="void", c_template="_dash_run_break(${run})",
        description="Send Ctrl-C to a run_start that is still running (again every second until it ends)"),
    "run_finish": BuiltinFunc(
        name="run_finish", params=["run"], return_type="STRPTR", c_template="_dash_run_finish(${run})",
        description="What a run_start wrote, as run_capture (it waits if it is still running), and forget it"),
    "run_rc": BuiltinFunc(
        name="run_rc", params=[], return_type="LONG", c_template="_dash_run_rc()",
        description="Return code of the last run_capture or run_finish: the command's, -1 if it could not "
                    "start, -2 if its time ran out"),
    "env_get": BuiltinFunc(
        name="env_get", params=["name"], return_type="STRPTR", c_template="_dash_env_get(${name})",
        reads_only=True,
        description="An environment variable (of the program's Shell, else of ENV:), up to its first line "
                    "end; \"\" if there is none"),
    "env_set": BuiltinFunc(
        name="env_set", params=["name", "value", "save"], return_type="BOOL",
        c_template="_dash_env_set(${name}, ${value}, ${save})", reads_only=True,
        description="Set a variable in ENV: (save true: also in ENVARC:, so that it stays after a reboot); "
                    "false if it could not"),
    # Dash 2.0 (Inferencia): ARexx as a client; ports, tasks and assigns
    "rexx_send": BuiltinFunc(
        name="rexx_send", params=["port", "command"], return_type="STRPTR",
        c_template="_dash_rexx_send(${port}, ${command})", reads_only=True,
        description="Send an ARexx command to a public port (\"MULTIVIEW.1\"; \"REXX\": run a script) and wait "
                    "for the answer: its RESULT (\"\" without one), the RC in rexx_rc(). Not to the program's own "
                    "port: it would wait for itself"),
    "rexx_rc": BuiltinFunc(
        name="rexx_rc", params=[], return_type="LONG", c_template="_dash_rexx_rc()",
        description="RC of the last rexx_send: 0 fine, 5, 10, 20... from the program; -1 no such port, -2 no "
                    "rexxsyslib.library"),
    "rexx_port": BuiltinFunc(
        name="rexx_port", params=["name"], return_type="BOOL", c_template="_dash_rexx_port(${name})",
        description="Opens the program's own ARexx port with that name (\"ADDRESS NAME\" from ARexx): false if "
                    "there is one already, or without rexxsyslib.library. Its commands, with rexx_get"),
    "rexx_get": BuiltinFunc(
        name="rexx_get", params=[], return_type="STRPTR", c_template="_dash_rexx_get()",
        description="The next command that came to the rexx_port (\"\" if none): it waits for rexx_reply (the "
                    "next rexx_get answers it with RC 0)"),
    "rexx_reply": BuiltinFunc(
        name="rexx_reply", params=["rc", "result"], return_type="void", c_template="_dash_rexx_reply(${rc}, ${result})",
        reads_only=True, description="Answers the command of rexx_get: rc (0 fine, 5, 10, 20) and, with 0, result as RESULT (\"\": "
                    "none)"),
    "notify": BuiltinFunc(
        name="notify", params=["title", "text"], return_type="BOOL", c_template="_dash_notify_send(${title}, ${text})",
        reads_only=True, description="A notification for the desktop, with the program's name: to Trasfondo's bar by ARexx "
                    "(port TRASFONDO) or, without it, into its list (ENV:Trasfondo.avisos), which it shows when it "
                    "starts. False if it got to neither"),
    "ports_read": BuiltinFunc(
        name="ports_read", params=[], return_type="LONG", c_template="_dash_ports_read()",
        description="Read the names of the public message ports open now (ARexx ports among them): how many, "
                    "for port_name, until the next ports_read"),
    "port_name": BuiltinFunc(
        name="port_name", params=["i"], return_type="STRPTR", c_template="_dash_port_name(${i})",
        description="Name of port i (from 0) of the last ports_read"),
    "tasks_read": BuiltinFunc(
        name="tasks_read", params=[], return_type="LONG", c_template="_dash_tasks_read()",
        description="Read the tasks and processes of the system (the program first): how many, for the "
                    "task_entry_ functions, until the next tasks_read"),
    "task_entry_name": BuiltinFunc(
        name="task_entry_name", params=["i"], return_type="STRPTR", c_template="_dash_task_entry_name(${i})",
        description="Name of task i of the last tasks_read (\"Shell Process\", \"input.device\"...)"),
    "task_entry_command": BuiltinFunc(
        name="task_entry_command", params=["i"], return_type="STRPTR",
        c_template="_dash_task_entry_command(${i})",
        description="The command a Shell process of the last tasks_read is running (\"\" if none)"),
    "task_entry_state": BuiltinFunc(
        name="task_entry_state", params=["i"], return_type="STRPTR", c_template="_dash_task_entry_state(${i})",
        description="State of task i: \"running\" (the program), \"ready\" or \"waiting\""),
    "task_entry_priority": BuiltinFunc(
        name="task_entry_priority", params=["i"], return_type="LONG",
        c_template="_dash_task_entry_priority(${i})", description="Priority of task i of the last tasks_read"),
    "task_entry_cli": BuiltinFunc(
        name="task_entry_cli", params=["i"], return_type="LONG", c_template="_dash_task_entry_cli(${i})",
        description="Shell number of task i (what Status shows, for Break), 0 if it is not a Shell process"),
    "assigns_read": BuiltinFunc(
        name="assigns_read", params=[], return_type="LONG", c_template="_dash_assigns_read()",
        description="Read the assigns (C:, LIBS:, those of Assign): how many, for assign_name and assign_path, "
                    "until the next assigns_read"),
    "assign_name": BuiltinFunc(
        name="assign_name", params=["i"], return_type="STRPTR", c_template="_dash_assign_name(${i})",
        description="Name of assign i of the last assigns_read, without the colon"),
    "assign_path": BuiltinFunc(
        name="assign_path", params=["i"], return_type="STRPTR", c_template="_dash_assign_path(${i})",
        description="Where assign i points: a directory (\"Workbench:C\"), several separated by \";\", or the name "
                    "a late or deferred one will look for"),
    "wb_open": BuiltinFunc(
        name="wb_open", params=["path"], return_type="BOOL", c_template="_dash_wb_open(${path})",
        reads_only=True,
        description="Open a drawer, a program or a project as a double click on its icon does (workbench.library "
                    "44, OS 3.5+); false if it could not"),
    "program_path": BuiltinFunc(
        name="program_path", params=[], return_type="STRPTR", c_template="_dash_program_path()",
        description="The program's full path (\"Work:Tachyon/Tachyon\"), from a Shell or from the Workbench"),
    "locale_language": BuiltinFunc(
        name="locale_language", params=[], return_type="STRPTR", c_template="_dash_locale_language()",
        description="The user's first preferred language in Locale prefs (\"español\"), \"\" without one"),
    "cpu_model": BuiltinFunc(
        name="cpu_model", params=[], return_type="LONG", c_template="_dash_cpu_model()",
        description="The processor: 68000, 68010, 68020, 68030, 68040 or 68060"),
    "fpu_model": BuiltinFunc(
        name="fpu_model", params=[], return_type="LONG", c_template="_dash_fpu_model()",
        description="The FPU: 68881, 68882, 68040 or 68060 (the one in the processor), 0 without one"),
    "library_version": BuiltinFunc(
        name="library_version", params=["name"], return_type="LONG", c_template="_dash_library_version(${name})",
        reads_only=True,
        description="The version of a library (\"muimaster.library\"), loading it if it is not in memory; -1 if "
                    "it is not there"),
    "library_revision": BuiltinFunc(
        name="library_revision", params=["name"], return_type="LONG", c_template="_dash_library_revision(${name})",
        reads_only=True,
        description="The revision of a library (the 3 of 47.3), as library_version; -1 if it is not there"),
    "resident_version": BuiltinFunc(
        name="resident_version", params=["name"], return_type="LONG", c_template="_dash_resident_version(${name})",
        reads_only=True,
        description="The version of a resident module of the system (FindResident: \"MorphOS\" says the program "
                    "runs on MorphOS); -1 if there is none"),
    "task_priority": BuiltinFunc(
        name="task_priority", params=["n"], return_type="LONG", c_template="_dash_task_priority(${n})",
        description="Set the program's priority (-128 to 127; the Shell gives 0): the one it had"),
    "build_date": BuiltinFunc(
        name="build_date", params=[], return_type="STRPTR", c_template="_dash_build_date()",
        description="The date the program was compiled, \"2026-10-28\""),
    "build_time": BuiltinFunc(
        name="build_time", params=[], return_type="STRPTR", c_template="(STRPTR)__TIME__",
        description="The time the program was compiled, \"20:45:10\""),
    "console_flush": BuiltinFunc(
        name="console_flush", params=[], return_type="void", c_template="_dash_console_flush()",
        description="Write out now what Print left in the output's buffer (a progress line without its end)"),
    # dashweb D68
    "dos_requesters": BuiltinFunc(
        name="dos_requesters", params=["on"], return_type="void",
        c_template="_dash_dos_requesters(${on})",
        description="false: no \"Insert volume\" or disk error requesters for this program (the call fails instead); "
                    "true: as before. The program's end puts them back"),
    "base64_to_file": BuiltinFunc(
        name="base64_to_file", params=["text", "file"], return_type="LONG",
        c_template="_dash_base64_to_file(${text}, ${file})",
        reads_only=True,      # only read during the call: variables keep (and free) their texts (D68b)
        description="Write the bytes of base64 text to a file (spaces and line ends skipped, = padding or not): "
                    "the bytes written, or -1 if the text is not base64 (no file then) or the file cannot be written"),
    "cpu_start": BuiltinFunc(
        name="cpu_start", params=[], return_type="BOOL",
        c_template="_dash_cpu_start()",
        description="Start counting the CPU of every task (exec's switch hooks; a task with hooks of another "
                    "program is not counted): false without EClock or before OS 2.04"),
    "cpu_sample": BuiltinFunc(
        name="cpu_sample", params=[], return_type="LONG",
        c_template="_dash_cpu_sample()",
        description="Take a sample: the number of tasks, with the CPU each took since the previous sample (or "
                    "cpu_start), most first; also hooks the tasks started since"),
    "cpu_task_name": BuiltinFunc(
        name="cpu_task_name", params=["i"], return_type="STRPTR",
        c_template="_dash_cpu_task(${i})",
        description="Name of task i of the last sample, from 0 (of a Shell process, its command)"),
    "cpu_task_load": BuiltinFunc(
        name="cpu_task_load", params=["i"], return_type="LONG",
        c_template="_dash_cpu_task_load(${i})",
        description="CPU of task i of the last sample, per thousand"),
    "cpu_total": BuiltinFunc(
        name="cpu_total", params=[], return_type="LONG",
        c_template="_dash_cpu_total()",
        description="CPU of all the counted tasks in the last sample, per thousand (the rest is idle)"),
    "cpu_stop": BuiltinFunc(
        name="cpu_stop", params=[], return_type="void",
        c_template="_dash_cpu_stop()",
        description="Take the hooks out of the tasks (the program's end does it too)"),
    "task_signal": BuiltinFunc(
        name="task_signal", params=[], return_type="LONG",
        c_template="_dash_task_signal()",
        description="Signal mask each task sends to the program when its function returns (for "
                    "mui_wait_event_signals), 0 if none is free"),
    "task_result": BuiltinFunc(
        name="task_result", params=["task"], return_type="LONG",
        c_template="_dash_task_result(${task})",
        description="What the function returned (waits for it if it has not finished)"),
    "task_free": BuiltinFunc(
        name="task_free", params=["task"], return_type="void",
        c_template="_dash_task_free(${task})",
        description="Forget the task (waits for it if it is still running); the program waits for any left at exit"),
}

# =============================================================================
# Pictures by datatypes (dashweb D12)
# =============================================================================

def _dec(name, params, ret, template, desc):
    """image_decode and its parts (Dash 2.0): no graphics, only memory and files"""
    return BuiltinFunc(name=name, params=params, return_type=ret, c_template=template, description=desc,
                       reads_only=True)


IMAGE_FUNCTIONS = {
    "image_load": _gfx("image_load", ["file"], "LONG", "_dash_image_load(${file})",
                       "Picture from a file by datatypes (ILBM; PNG, GIF, JPEG if the system has them), "
                       "with the colors of the screen drawn on: the image, or 0"),
    "image_width": _gfx("image_width", ["image"], "LONG", "_dash_image_width(${image})", "Width of an image"),
    "image_height": _gfx("image_height", ["image"], "LONG", "_dash_image_height(${image})", "Height of an image"),
    "image_draw": _gfx("image_draw", ["image", "x", "y"], "void", "_dash_image_draw(${image}, ${x}, ${y})",
                       "Draw an image at x, y (its transparent pixels are not drawn)"),
    "image_draw_part": _gfx("image_draw_part", ["image", "sx", "sy", "x", "y", "w", "h"], "void",
                            "_dash_image_draw_part(${image}, ${sx}, ${sy}, ${x}, ${y}, ${w}, ${h})",
                            "Draw the part w x h at sx, sy of an image at x, y"),
    "image_scale": _gfx("image_scale", ["image", "w", "h"], "LONG", "_dash_image_scale(${image}, ${w}, ${h})",
                        "A copy of an image at w x h pixels: a new image, or 0"),
    "image_free": _gfx("image_free", ["image"], "void", "_dash_image_free(${image})",
                       "Free an image (the ones left are freed at exit)"),
    # Dash 2.0: decoded by the program itself (runtime/imgdec), what Tachyon did with @native
    "image_decode": _dec("image_decode", ["file", "maxw", "maxh"], "LONG", "_dash_image_decode(${file}, ${maxw}, ${maxh})",
                         "Decode a JPEG (TJpgDec), WebP (libwebp; both already reduced while they decode), PNG, GIF, BMP (stb_image) or SVG "
                         "(nanosvg: drawn to cover maxw x maxh, RGBA) to "
                         "RGB or RGBA pixels, made smaller until it is not much bigger than maxw x maxh (0, 0: its "
                         "size; negative, a limit: an SVG then at its own size, smaller if it does not fit): the "
                         "decoded picture, or 0. Without datatypes, and it may run in a task_start"),
    "image_decode_start": _dec("image_decode_start", ["file", "maxw", "maxh"], "LONG",
                               "_dash_image_decode_start(${file}, ${maxw}, ${maxh})",
                               "image_decode in a process of its own, one below the program's priority, so the "
                               "window goes on answering: a number for image_decode_ready and image_decode_finish, "
                               "or 0 if it could not start"),
    "image_decode_ready": _dec("image_decode_ready", ["t"], "BOOL", "_dash_image_decode_ready(${t})",
                               "True when an image_decode_start has finished (it does not wait)"),
    "image_decode_finish": _dec("image_decode_finish", ["t"], "LONG", "_dash_image_decode_finish(${t})",
                                "What an image_decode_start decoded, as image_decode (0 if it could not); it waits "
                                "if it is still running, and frees its process"),
    "image_decoded_width": _dec("image_decoded_width", ["d"], "LONG", "_dash_image_decoded_width(${d})",
                                "Width of a decoded picture"),
    "image_decoded_height": _dec("image_decoded_height", ["d"], "LONG", "_dash_image_decoded_height(${d})",
                                 "Height of a decoded picture"),
    "image_decoded_alpha": _dec("image_decoded_alpha", ["d"], "BOOL", "_dash_image_decoded_alpha(${d})",
                                "True if a decoded picture has alpha (4 bytes per pixel, RGBA; else 3, RGB)"),
    "image_decoded_pixels": _dec("image_decoded_pixels", ["d"], "APTR", "_dash_image_decoded_pixels(${d})",
                                 "The pixels of a decoded picture, row after row: a buffer for buffer_get_byte or "
                                 "image_from_rgb"),
    "image_decoded_free": _dec("image_decoded_free", ["d"], "void", "_dash_image_decoded_free(${d})",
                               "Free a decoded picture"),
    "image_from_decoded_size": _gfx("image_from_decoded_size", ["d", "w", "h"], "LONG",
                                    "_dash_image_from_rgb_sized(_dash_image_decoded_pixels(${d}), "
                                    "_dash_image_decoded_width(${d}), _dash_image_decoded_height(${d}), "
                                    "_dash_image_decoded_alpha(${d}), ${w}, ${h})",
                                    "As image_from_decoded, made w x h first with smooth edges (each pixel the "
                                    "average of the ones it covers, alpha too); the decoded picture is still to be freed"),
    "image_from_decoded": _gfx("image_from_decoded", ["d"], "LONG",
                               "_dash_image_from_rgb(_dash_image_decoded_pixels(${d}), _dash_image_decoded_width(${d}), "
                               "_dash_image_decoded_height(${d}), _dash_image_decoded_alpha(${d}))",
                               "An image (as image_from_rgb) from a decoded picture, which is still to be freed"),
    "image_from_rgb": _gfx("image_from_rgb", ["buffer", "width", "height", "alpha"], "LONG",
                           "_dash_image_from_rgb((APTR)${buffer}, ${width}, ${height}, ${alpha})",
                           "An image from pixels in a buffer (RGB, or RGBA with alpha: mixed with what is under it on "
                           "RTG, drawn from 128 on a palette screen), with the colors of the screen: the image, or 0 "
                           "(needs picture.datatype V43, AmigaOS 3.5+, except on RTG screens)"),
}

# =============================================================================
# Program arguments (dashweb D19)
# =============================================================================

ARGS_FUNCTIONS = {
    "arg_count": _text("arg_count", [], "LONG", "_dash_arg_count()",
                       "How many arguments the program got from the Shell, or project icons from the Workbench "
                       "(a double click on a document, shift + click on several)"),
    "arg": _text("arg", ["i"], "STRPTR", "_dash_arg(${i})",
                 "Argument i, from 0 (\"\" if there is none); from the Workbench, the icon's full path"),
    # dashweb D27: where the last On Click was, inside the window's borders
    "click_x": _text("click_x", [], "LONG", "_dash_click_x", "X of the last On Click, in the window (inside its borders)"),
    "click_y": _text("click_y", [], "LONG", "_dash_click_y", "Y of the last On Click, in the window (inside its borders)"),
    # dashweb D20
    "time_ms": _text("time_ms", [], "LONG", "_dash_time_ms()",
                     "Milliseconds since the program started (EClock of timer.device)"),
}

# =============================================================================
# Compression (Lorraine D6): raw deflate, as in a ZIP, with zlib (compiler/clibs.py)
# =============================================================================

def _buf(name, params, ret, template, desc):
    return BuiltinFunc(name=name, params=params, return_type=ret, c_template=template, description=desc,
                       reads_only=True)


ZLIB_FUNCTIONS = {
    "inflate": _buf("inflate", ["src", "n", "dest", "max"], "LONG", "_dash_inflate(${src}, ${n}, ${dest}, ${max})",
                    "Uncompress n bytes of raw deflate (as in a ZIP) from buffer src into dest: the bytes written, "
                    "or -1 if the data is not raw deflate or is cut short, -2 if it does not fit in max, "
                    "-3 if there is no memory (zlib)"),
    "inflate_auto": _buf("inflate_auto", ["src", "n", "dest", "max"], "LONG",
                         "_dash_inflate_auto(${src}, ${n}, ${dest}, ${max})",
                         "inflate for gzip, zlib or raw deflate, told by its first bytes (an HTTP body with "
                         "Content-Encoding gzip or deflate): the bytes written, or as inflate"),
    "deflate": _buf("deflate", ["src", "n", "dest", "max", "level"], "LONG",
                    "_dash_deflate(${src}, ${n}, ${dest}, ${max}, ${level})",
                    "Compress n bytes of buffer src into dest as raw deflate, level 0 (stored) to 9 (smallest; "
                    "-1: 6): the bytes written, -2 if they do not fit in max, -3 if there is no memory (zlib; "
                    "about 260 KB while it works, at any level)"),
    "crc32": _buf("crc32", ["buffer", "n", "crc"], "LONG", "_dash_crc32(${buffer}, ${n}, ${crc})",
                  "CRC-32 (as in ZIP and PNG) of n bytes of a buffer, going on from crc (0 to start)"),
    "adler32": _buf("adler32", ["buffer", "n", "a"], "LONG", "_dash_adler32(${buffer}, ${n}, ${a})",
                    "Adler-32 (the checksum at the end of a zlib stream) of n bytes of a buffer, going on from a (1 to "
                    "start)"),
    "inflate_used": _buf("inflate_used", [], "LONG", "_dash_inflate_used()",
                         "The input bytes the last inflate or inflate_auto used (with a zlib wrapper, its adler32 "
                         "too): where the next object starts in a git pack"),
    "sha1": _buf("sha1", ["buffer", "n"], "STRPTR", "_dash_sha1(${buffer}, ${n})",
                 "SHA-1 of n bytes of a buffer, in 40 hex digits (git names its objects so)"),
    "sha1_text": _buf("sha1_text", ["s"], "STRPTR", "_dash_sha1_text(${s})", "SHA-1 of a text, in 40 hex digits"),
    "sha1_new": _buf("sha1_new", [], "LONG", "_dash_sha1_new()",
                     "A SHA-1 made bit by bit with sha1_add, sha1_add_text and sha1_add_byte: its number (1-8), 0 if "
                     "all are in use. sha1_hex or sha1_bytes end it"),
    "sha1_add": _buf("sha1_add", ["sha", "buffer", "n"], "void", "_dash_sha1_add(${sha}, ${buffer}, ${n})",
                     "Adds n bytes of a buffer to a SHA-1 of sha1_new"),
    "sha1_add_text": _buf("sha1_add_text", ["sha", "s"], "void", "_dash_sha1_add_text(${sha}, ${s})",
                          "Adds a text to a SHA-1 of sha1_new"),
    "sha1_add_byte": _buf("sha1_add_byte", ["sha", "b"], "void", "_dash_sha1_add_byte(${sha}, ${b})",
                          "Adds a byte (0-255) to a SHA-1 of sha1_new (the 0 after git's \"blob 6\")"),
    "sha1_hex": _buf("sha1_hex", ["sha"], "STRPTR", "_dash_sha1_hex(${sha})",
                     "Ends a SHA-1 of sha1_new: its 40 hex digits (\"\" if that number is not in use)"),
    "sha1_bytes": _buf("sha1_bytes", ["sha", "out"], "BOOL", "_dash_sha1_bytes(${sha}, ${out})",
                       "Ends a SHA-1 of sha1_new: its 20 bytes to a buffer (as git keeps them in trees and the "
                       "index); false if that number is not in use"),
}

# =============================================================================
# UTF-8 (Lorraine D5): texts as UTF-8. A byte that does not start a valid sequence is one character, U+FFFD.
# =============================================================================

UTF8_FUNCTIONS = {
    "utf8_next": _text("utf8_next", ["s", "i"], "LONG", "_dash_utf8_next(${s}, ${i})",
                       "Position of the UTF-8 character after the one at byte i (the length at the end)"),
    "utf8_prev": _text("utf8_prev", ["s", "i"], "LONG", "_dash_utf8_prev(${s}, ${i})",
                       "Position of the UTF-8 character before byte i (0 at the start)"),
    "utf8_code": _text("utf8_code", ["s", "i"], "LONG", "_dash_utf8_code(${s}, ${i})",
                       "Code point of the UTF-8 character at byte i (65533 for an invalid byte, 0 outside the text)"),
    "utf8_char": _text("utf8_char", ["code"], "STRPTR", "_dash_utf8_char(${code})",
                       "Text with the character of that code point in UTF-8 (\"\" for 0; U+FFFD if it is not one)"),
    "utf8_length": _text("utf8_length", ["s"], "LONG", "_dash_utf8_length(${s})",
                         "How many UTF-8 characters s has (each invalid byte counts as one)"),
    "utf8_to_latin1": _text("utf8_to_latin1", ["s"], "STRPTR", "_dash_utf8_to_latin1(${s})",
                            "UTF-8 text in Latin-1: what Latin-1 lacks becomes something like it (\u201c to \", "
                            "\u20ac to EUR, \u2026 to ...) or ?, as do invalid bytes"),
    "latin1_to_utf8": _text("latin1_to_utf8", ["s"], "STRPTR", "_dash_latin1_to_utf8(${s})",
                            "Latin-1 text in UTF-8 (bytes from 128 on take two)"),
    # D40
    "utf8_check": _text("utf8_check", ["buffer", "from", "to"], "LONG", "_dash_utf8_check(${buffer}, ${from}, ${to})",
                        "Position of the first byte from to to - 1 of a buffer that is not valid UTF-8 (or starts a "
                        "sequence cut by to), -1 if all are valid"),
}

# =============================================================================
# Comparing and searching in a buffer without making texts (Lorraine D38, D39)
# =============================================================================

BUFSEARCH_FUNCTIONS = {
    "buffer_equals": _text("buffer_equals", ["buffer", "offset", "n", "s"], "BOOL",
                           "_dash_buffer_equals(${buffer}, ${offset}, ${n}, ${s})",
                           "Whether the n bytes of a buffer at offset are the text s (and s has n bytes)"),
    "buffer_find_byte": _text("buffer_find_byte", ["buffer", "from", "to", "byte"], "LONG",
                              "_dash_buffer_find_byte(${buffer}, ${from}, ${to}, ${byte})",
                              "Position of the first byte equal to byte from from to to - 1, or -1"),
    "buffer_find_any": _text("buffer_find_any", ["buffer", "from", "to", "bytes"], "LONG",
                             "_dash_buffer_find_any(${buffer}, ${from}, ${to}, ${bytes})",
                             "Position of the first byte from from to to - 1 that is one of the bytes of the text "
                             "bytes, or -1"),
}

# =============================================================================
# Double to text and back (Lorraine D3)
# =============================================================================

DOUBLE_FUNCTIONS = {
    "str_from_double": _text("str_from_double", ["d", "decimals"], "STRPTR", "_dash_str_from_double(${d}, ${decimals})",
                             "A Double with that many decimals (0: none), its shortest decimal rounded half away "
                             "from zero (2.675 with 2 is 2.68); decimals < 0: the shortest that reads back the same"),
    "str_to_double": _text("str_to_double", ["s"], "double", "_dash_double_from_str(${s})",
                           "The Double at the start of the text, like Double(s): exact up to 17 significant "
                           "digits; 0.0 if there is no number"),
}

def _math(name, params, ret, desc):
    args = ", ".join("${%s}" % p for p in params)
    return BuiltinFunc(name=name, params=params, return_type=ret, c_template=f"_dash_m_{name}({args})",
                       description=desc, reads_only=True)


# Lorraine D4: with fdlibm (runtime/fdlibm). An Int or a Float goes in as a Double.
MATH_FUNCTIONS = {
    "sqrt": _math("sqrt", ["x"], "double", "Square root (nan for a negative)"),
    "pow": _math("pow", ["x", "y"], "double", "x to the power y"),
    "exp": _math("exp", ["x"], "double", "e to the power x"),
    "log": _math("log", ["x"], "double", "Natural logarithm (-inf for 0, nan for a negative)"),
    "log10": _math("log10", ["x"], "double", "Base 10 logarithm"),
    "sin": _math("sin", ["x"], "double", "Sine of x radians"),
    "cos": _math("cos", ["x"], "double", "Cosine of x radians"),
    "tan": _math("tan", ["x"], "double", "Tangent of x radians"),
    "asin": _math("asin", ["x"], "double", "Arc sine in radians, -pi/2 to pi/2 (nan outside -1..1)"),
    "acos": _math("acos", ["x"], "double", "Arc cosine in radians, 0 to pi (nan outside -1..1)"),
    "atan": _math("atan", ["x"], "double", "Arc tangent in radians, -pi/2 to pi/2"),
    "atan2": _math("atan2", ["y", "x"], "double", "Angle of the point (x, y) in radians, -pi to pi"),
    "floor": _math("floor", ["x"], "double", "The largest whole number not above x (a Double)"),
    "ceil": _math("ceil", ["x"], "double", "The smallest whole number not below x (a Double)"),
    "round": _math("round", ["x"], "double", "The nearest whole number, halves away from zero (2.5 is 3.0, -2.5 is -3.0)"),
    "trunc": _math("trunc", ["x"], "double", "The whole part, toward zero (-2.7 is -2.0)"),
    "fmod": _math("fmod", ["x", "y"], "double", "Remainder of x / y with the sign of x (nan if y is 0)"),
    "abs": _math("abs", ["x"], "double", "Absolute value, a Double"),
    "is_nan": _math("is_nan", ["x"], "BOOL", "True if x is nan (not a number: sqrt(-1.0), 0.0 / 0.0)"),
    "is_inf": _math("is_inf", ["x"], "BOOL", "True if x is inf or -inf"),
}


# Lorraine D45: over UTF-8 texts; positions and lengths in bytes, as utf8_next
REGEX_FUNCTIONS = {
    "regex_match": _text("regex_match", ["pattern", "text", "ignore_case"], "BOOL",
                         "_dash_regex_match(${pattern}, ${text}, ${ignore_case})",
                         "True if the whole text fits the regular expression (ICU's common syntax: . * + ? {m,n} [] [^] "
                         "^ $ \\d \\w \\s \\b | groups); false also for a wrong pattern (regex_error says why)"),
    "regex_find": _text("regex_find", ["pattern", "text", "from", "ignore_case"], "LONG",
                        "_dash_regex_find(${pattern}, ${text}, ${from}, ${ignore_case})",
                        "Byte position where the first match from byte from starts, -1 if there is none (or the "
                        "pattern is wrong); regex_length gives its length"),
    "regex_length": _text("regex_length", [], "LONG", "_dash_regex_length()",
                          "Length in bytes of the last match of regex_find or regex_match (0 if none)"),
    "regex_error": _text("regex_error", [], "STRPTR", "_dash_regex_error()",
                         "Why the last pattern is wrong, \"\" if it is right"),
    "wildcard_match": _text("wildcard_match", ["pattern", "text", "ignore_case"], "BOOL",
                            "_dash_wildcard_match(${pattern}, ${text}, ${ignore_case})",
                            "True if the whole text fits Excel's wildcards: * any characters, ? one, ~ before a "
                            "character takes it as it is (~* ~? ~~)"),
}

# Lorraine D46: to test a program in the emulator from another one
SIMINPUT_FUNCTIONS = {
    "input_key": BuiltinFunc(
        name="input_key", params=["code", "qualifiers"], return_type="void",
        c_template="_dash_input_key(${code}, ${qualifiers})",
        description="Press and let go a raw key in the active window (0x44 Return, 0x45 Esc, 0x4C up, 0x4D down, "
                    "0x4E right, 0x4F left, 0x41 Backspace), with qualifiers 1 Shift, 2 Ctrl, 4 Alt, 8 Amiga "
                    "(added up) held around it"),
    "input_text": BuiltinFunc(
        name="input_text", params=["text"], return_type="void", c_template="_dash_input_text(${text})",
        reads_only=True, description="Type a text in the active window with the keyboard's keymap (\"=SUM(A1:A3)\"); a character "
                    "the keymap cannot type is left out"),
    "input_move": BuiltinFunc(
        name="input_move", params=["x", "y"], return_type="void", c_template="_dash_input_move(${x}, ${y})",
        description="Move the pointer to (x, y) from the corner of the active window"),
    "input_click": BuiltinFunc(
        name="input_click", params=["x", "y", "qualifiers"], return_type="void",
        c_template="_dash_input_click(${x}, ${y}, ${qualifiers})",
        description="Click with the left button at (x, y) from the corner of the active window, with qualifiers "
                    "1 Shift, 2 Ctrl, 4 Alt (Amiga + click is the system's)"),
    "input_button": BuiltinFunc(
        name="input_button", params=["button", "down"], return_type="void",
        c_template="_dash_input_mouse_button(${button}, ${down})",
        description="Press (down true) or let go a mouse button where the pointer is: 1 left, 2 right (menus, "
                    "a context menu), 3 middle"),
    "input_drag": BuiltinFunc(
        name="input_drag", params=["x1", "y1", "x2", "y2"], return_type="void",
        c_template="_dash_input_drag(${x1}, ${y1}, ${x2}, ${y2})",
        description="Press the left button at (x1, y1), move to (x2, y2) with it down and let go (from the corner "
                    "of the active window)"),
    "input_qualifiers": BuiltinFunc(
        name="input_qualifiers", params=[], return_type="LONG", c_template="_dash_input_qualifiers()",
        description="The keys held down now (input.device's PeekQualifier): 1, 2 Shift; 8 Ctrl; 16, 32 Alt; "
                    "64, 128 Amiga; 0 if input.device cannot be opened"),
    # Dash 2.0: for test programs (what Tachyon's clicar and Trasfondo's tests did with @native)
    "window_find": BuiltinFunc(
        name="window_find", params=["title"], return_type="LONG", c_template="_dash_window_find(${title})",
        reads_only=True,
        description="Another program's window (or the program's own) whose title starts with title, on any screen: "
                    "a number for window_found_* and gadget_*, 0 if none (not valid once it is closed)"),
    "window_found_activate": BuiltinFunc(
        name="window_found_activate", params=["win"], return_type="void",
        c_template="_dash_window_found_activate(${win})",
        description="A window of window_find in front, with its screen, and active (input_* go to the active window)"),
    "window_found_box": BuiltinFunc(
        name="window_found_box", params=["win", "what"], return_type="LONG",
        c_template="_dash_window_found_box(${win}, ${what})",
        description="Of a window of window_find: 0 left, 1 top (on its screen), 2 width, 3 height, 4 left border, "
                    "5 top border"),
    "gadget_index": BuiltinFunc(
        name="gadget_index", params=["win", "text"], return_type="LONG", c_template="_dash_gadget_index(${win}, ${text})",
        reads_only=True,
        description="The place (from 0, the window's own gadgets too) of the gadget whose text is text in a window of "
                    "window_find; -1 if none. GadTools' buttons do not keep their text: count from one next to them"),
    "gadget_x": BuiltinFunc(
        name="gadget_x", params=["win", "n"], return_type="LONG", c_template="_dash_gadget_xy(${win}, ${n}, 0)",
        description="x of the centre of the gadget at place n of a window of window_find, from its corner (as "
                    "input_click counts); -1 if there is none"),
    "gadget_y": BuiltinFunc(
        name="gadget_y", params=["win", "n"], return_type="LONG", c_template="_dash_gadget_xy(${win}, ${n}, 1)",
        description="y of the centre of that gadget, as gadget_x"),
    "gadget_selected": BuiltinFunc(
        name="gadget_selected", params=["win", "n"], return_type="BOOL", c_template="_dash_gadget_selected(${win}, ${n})",
        description="True if the gadget at place n (a checkbox) is selected"),
    "input_menu": BuiltinFunc(
        name="input_menu", params=["menu", "item", "hold"], return_type="BOOL",
        c_template="_dash_input_menu(${menu}, ${item}, ${hold})",
        description="Choose item (from 0, separators too) of menu (from 0) of the active window with the mouse, as "
                    "a user: the right button on its title, to the item, held hold ticks (1/50 s), let go; false if "
                    "there is no such item"),
    "input_move_screen": BuiltinFunc(
        name="input_move_screen", params=["x", "y", "buttons"], return_type="void",
        c_template="_dash_input_move_screen(${x}, ${y}, ${buttons})",
        description="The pointer to (x, y) of the screen in steps of a pixel with buttons held (1 left, 2 right, 0 "
                    "none): MUI's menus follow it"),
    "screen_pixel": BuiltinFunc(
        name="screen_pixel", params=["x", "y"], return_type="LONG", c_template="_dash_screen_pixel(${x}, ${y})",
        needs_gfx=True,
        description="The pen of the pixel (x, y) of the screen in front; -1 outside it"),
    "screen_pen_rgb": BuiltinFunc(
        name="screen_pen_rgb", params=["n"], return_type="LONG", c_template="_dash_screen_pen_rgb(${n})",
        needs_gfx=True, reads_only=True,
        description="The colour of pen n of the Workbench screen as 0xRRGGBB: 0 detail, 1 block, 2 text, 3 shine, "
                    "4 shadow, 5 fill (the active title bar), 6 fill text, 7 background, 8 highlight text, 9 bar "
                    "detail, 10 bar block, 11 bar trim; -1 if it has no such pen"),
    "screen_pixel_rgb": BuiltinFunc(
        name="screen_pixel_rgb", params=["x", "y"], return_type="LONG",
        c_template="_dash_screen_pixel_rgb(${x}, ${y})", needs_gfx=True, reads_only=True,
        description="The colour of the pixel (x, y) of the screen in front as 0xRRGGBB, whoever drew it; -1 outside "
                    "it. What is behind a window before it opens"),
    "cx_send": BuiltinFunc(
        name="cx_send", params=["name", "command"], return_type="LONG", c_template="_dash_cx_send(${name}, ${command})",
        reads_only=True,
        description="A command to a commodity by its name, as Exchange does (15 disable, 17 enable, 19 show, 21 "
                    "hide, 23 kill...): 0 done, -1 no such commodity, -2 it has no port, -99 no commodities.library"),
    "input_active_title": BuiltinFunc(
        name="input_active_title", params=[], return_type="STRPTR", c_template="_dash_input_active_title()",
        description="Title of the active window (\"\" if none): to wait for the window of the program to test"),
}

# Lorraine D7: sorting texts as the user's language does
COLLATE_FUNCTIONS = {
    "str_compare_locale": _text("str_compare_locale", ["a", "b", "ignore_case"], "LONG",
                                "_dash_str_compare_locale(${a}, ${b}, ${ignore_case})",
                                "Compare two UTF-8 texts in the order of the user's language (locale.library): "
                                "-1 if a goes first, 0 if they are equal, 1 if b does; accents and case count only "
                                "after the letters (\"árbol\" before \"barco\", \"apple\" before \"Banana\"), and "
                                "not at all with ignore_case. Without locale.library, by their Latin-1 bytes"),
}

# Lorraine D18: copy and paste with the other programs (text in unit 0) and with itself (a block of its own)
CLIP_FUNCTIONS = {
    "clip_write_text": _text("clip_write_text", ["s"], "BOOL", "_dash_clip_write_text(${s})",
                             "Copy a UTF-8 text to the clipboard (unit 0, IFF FTXT in Latin-1, as the other "
                             "programs read it): what Latin-1 lacks becomes something like it, as utf8_to_latin1 "
                             "(\u20ac to EUR); false if the clipboard cannot be written"),
    "clip_read_text": _text("clip_read_text", [], "STRPTR", "_dash_clip_read_text()",
                            "The text in the clipboard (unit 0) in UTF-8; \"\" if it is empty or holds no text"),
    "clip_write_block": _buf("clip_write_block", ["unit", "type", "buffer", "n"], "BOOL",
                             "_dash_clip_write_block(${unit}, ${type}, ${buffer}, ${n})",
                             "Copy n bytes of a buffer to clipboard unit 1-255 as a FORM of its own type (4 "
                             "characters, \"LCLC\"), after clip_write_text: it stays tied to that text, and "
                             "if something else is copied to unit 0 the block reads as missing"),
    "clip_block_size": _buf("clip_block_size", ["unit", "type"], "LONG", "_dash_clip_block_size(${unit}, ${type})",
                            "Bytes of the block of that type in a clipboard unit, -1 if there is none or "
                            "something else was copied after it"),
    "clip_read_block": _buf("clip_read_block", ["unit", "type", "dest", "max"], "LONG",
                            "_dash_clip_read_block(${unit}, ${type}, ${dest}, ${max})",
                            "Copy the block of that type in a clipboard unit to buffer dest: its bytes, -1 if "
                            "there is none or something else was copied after it, -2 if it does not fit in max"),
}

# Dash 2.0: JSON read in C for lib/json.dash (json_parse makes its tree of Json from these nodes)
JSON_FUNCTIONS = {
    "json_scan": BuiltinFunc(
        name="json_scan", params=["text"], return_type="LONG", c_template="_dash_json_scan(${text})", reads_only=True,
        description="Read a JSON text into a table of nodes in order, each followed by what it holds (lib/json.dash "
                    "makes its tree from it): how many, -1 if it is not JSON (json_scan_error says why and where)"),
    "json_scan_error": BuiltinFunc(
        name="json_scan_error", params=[], return_type="STRPTR", c_template="_dash_json_scan_error()",
        description="Why the last json_scan gave -1, and at which byte (\"unexpected end at byte 1\")"),
    "json_scan_kind": BuiltinFunc(
        name="json_scan_kind", params=["i"], return_type="LONG", c_template="_dash_json_scan_kind(${i})",
        description="Kind of node i: 0 null, 1 true or false, 2 number, 3 string, 4 array, 5 object"),
    "json_scan_count": BuiltinFunc(
        name="json_scan_count", params=["i"], return_type="LONG", c_template="_dash_json_scan_count(${i})",
        description="How many elements an array or object node holds (they follow it); 1 for true, 0 for false"),
    "json_scan_text": BuiltinFunc(
        name="json_scan_text", params=["i"], return_type="STRPTR", c_template="_dash_json_scan_text(${i})",
        description="The text of a string node (its escapes and \\uXXXX undone, in UTF-8) or a number node (as "
                    "written)"),
    "json_scan_name": BuiltinFunc(
        name="json_scan_name", params=["i"], return_type="STRPTR", c_template="_dash_json_scan_name(${i})",
        description="The name of node i inside its object (\"\" in an array or at the top)"),
}

# Dash 2.0 (Forja, the IDE): the debugger. The debugged program is built with dash --debug (dashc); the debugger
# with either Dash (docs/DEPURADOR_LOOP.md)
DEBUGGER_FUNCTIONS = {
    "dbg_start": BuiltinFunc(
        name="dbg_start", params=['program', 'args'], return_type="BOOL", c_template="((BOOL)_dash_dbg_start((LONG)(${program}), (LONG)(${args})))",
        reads_only=True, description='Load a program built with dash --debug and start it in a process of its own, paused before its first line (set breakpoints, then dbg_continue): false if it could not (dbg_error says why)'),
    "dbg_error": BuiltinFunc(
        name="dbg_error", params=[], return_type="STRPTR", c_template="((STRPTR)_dash_dbg_error())",
        reads_only=True, description='Why the last dbg_start failed'),
    "dbg_state": BuiltinFunc(
        name="dbg_state", params=[], return_type="LONG", c_template="((LONG)_dash_dbg_state())",
        reads_only=True, description='The debugged program: 0 none, 1 paused before starting, 2 running, 3 stopped at a line, 4 ended'),
    "dbg_signal": BuiltinFunc(
        name="dbg_signal", params=[], return_type="LONG", c_template="((LONG)_dash_dbg_signal())",
        reads_only=True, description='The signal the debugger gets when the program stops or ends (for mui_wait_event_signals)'),
    "dbg_wait": BuiltinFunc(
        name="dbg_wait", params=['ms'], return_type="LONG", c_template="((LONG)_dash_dbg_wait((LONG)(${ms})))",
        reads_only=True, description='Wait until the program stops or ends, ms at most (0: no limit): its state'),
    "dbg_break": BuiltinFunc(
        name="dbg_break", params=['file', 'line'], return_type="BOOL", c_template="((BOOL)_dash_dbg_break((LONG)(${file}), (LONG)(${line})))",
        reads_only=True, description='A breakpoint at that line of that file ("prog.dash": the end of its path): false if the line has no code'),
    "dbg_unbreak": BuiltinFunc(
        name="dbg_unbreak", params=['file', 'line'], return_type="BOOL", c_template="((BOOL)_dash_dbg_unbreak((LONG)(${file}), (LONG)(${line})))",
        reads_only=True, description='Take the breakpoint out of that line'),
    "dbg_continue": BuiltinFunc(
        name="dbg_continue", params=[], return_type="BOOL", c_template="((BOOL)_dash_dbg_continue())",
        reads_only=True, description='Go on (from the start or a stop) until a breakpoint or the end'),
    "dbg_step": BuiltinFunc(
        name="dbg_step", params=[], return_type="BOOL", c_template="((BOOL)_dash_dbg_step())",
        reads_only=True, description='Go on to the next line, into the functions it calls'),
    "dbg_next": BuiltinFunc(
        name="dbg_next", params=[], return_type="BOOL", c_template="((BOOL)_dash_dbg_next())",
        reads_only=True, description='Go on to the next line of this function (or of the one that called it)'),
    "dbg_out": BuiltinFunc(
        name="dbg_out", params=[], return_type="BOOL", c_template="((BOOL)_dash_dbg_out())",
        reads_only=True, description='Go on until the function returns: the next line of the one that called it'),
    "dbg_pause": BuiltinFunc(
        name="dbg_pause", params=[], return_type="BOOL", c_template="((BOOL)_dash_dbg_pause())",
        reads_only=True, description='Stop the running program at the next line it runs'),
    "dbg_end": BuiltinFunc(
        name="dbg_end", params=['ms'], return_type="BOOL", c_template="((BOOL)_dash_dbg_end((LONG)(${ms})))",
        reads_only=True, description='End the program (Ctrl-C, and at its next line its usual end): true if it ended within ms'),
    "dbg_rc": BuiltinFunc(
        name="dbg_rc", params=[], return_type="LONG", c_template="((LONG)_dash_dbg_rc())",
        reads_only=True, description='The return code of the ended program'),
    "dbg_file": BuiltinFunc(
        name="dbg_file", params=[], return_type="STRPTR", c_template="((STRPTR)_dash_dbg_file())",
        reads_only=True, description='The file of the line where the program stopped (its full path)'),
    "dbg_line": BuiltinFunc(
        name="dbg_line", params=[], return_type="LONG", c_template="((LONG)_dash_dbg_line())",
        reads_only=True, description='The line where the program stopped (0 if it is not stopped)'),
    "dbg_function": BuiltinFunc(
        name="dbg_function", params=[], return_type="STRPTR", c_template="((STRPTR)_dash_dbg_function())",
        reads_only=True, description='The function where the program stopped ("Main", "Punto.mover"...)'),
    "dbg_frames": BuiltinFunc(
        name="dbg_frames", params=[], return_type="LONG", c_template="((LONG)_dash_dbg_frames())",
        reads_only=True, description='How many calls are open where the program stopped: 1 in Main, 2 in a function Main called... (0 if it is not stopped)'),
    "dbg_frame_function": BuiltinFunc(
        name="dbg_frame_function", params=['i'], return_type="STRPTR", c_template="((STRPTR)_dash_dbg_frame_function((LONG)(${i})))",
        reads_only=True, description='The function of call i: 0 the one where it stopped, 1 the one that called it...'),
    "dbg_frame_line": BuiltinFunc(
        name="dbg_frame_line", params=['i'], return_type="LONG", c_template="((LONG)_dash_dbg_frame_line((LONG)(${i})))",
        reads_only=True, description='The line where call i is: 0 where it stopped, 1 the line of the call in the one that called it...'),
    "dbg_frame_file": BuiltinFunc(
        name="dbg_frame_file", params=['i'], return_type="STRPTR", c_template="((STRPTR)_dash_dbg_frame_file((LONG)(${i})))",
        reads_only=True, description='The file of call i (its full path)'),
    "dbg_vars": BuiltinFunc(
        name="dbg_vars", params=['i'], return_type="LONG", c_template="((LONG)_dash_dbg_vars((LONG)(${i})))",
        reads_only=True, description='How many variables call i sees: its parameters and the variables declared up to its line'),
    "dbg_var_name": BuiltinFunc(
        name="dbg_var_name", params=['i', 'k'], return_type="STRPTR", c_template="((STRPTR)_dash_dbg_var_name((LONG)(${i}), (LONG)(${k})))",
        reads_only=True, description='Name of variable k (from 0) of call i'),
    "dbg_var_type": BuiltinFunc(
        name="dbg_var_type", params=['i', 'k'], return_type="STRPTR", c_template="((STRPTR)_dash_dbg_var_type((LONG)(${i}), (LONG)(${k})))",
        reads_only=True, description='Type of variable k of call i, as in Dash ("Int", "[String]", "Punto")'),
    "dbg_globals": BuiltinFunc(
        name="dbg_globals", params=[], return_type="LONG", c_template="((LONG)_dash_dbg_globals())",
        reads_only=True, description='How many global variables the program has'),
    "dbg_global_name": BuiltinFunc(
        name="dbg_global_name", params=['g'], return_type="STRPTR", c_template="((STRPTR)_dash_dbg_global_name((LONG)(${g})))",
        reads_only=True, description='Name of global g (from 0)'),
    "dbg_value": BuiltinFunc(
        name="dbg_value", params=['i', 'expr'], return_type="STRPTR", c_template="((STRPTR)_dash_dbg_value((LONG)(${i}), (LONG)(${expr})))",
        reads_only=True, description='The value of expr in call i as text: a variable of that call or a global, with .field and [n] after it ("p.hijos[0].x"): 3, "hola", Punto(x: 3, y: 4), [1, 2], nil; "? " and why if it cannot'),
    "dbg_value_type": BuiltinFunc(
        name="dbg_value_type", params=['i', 'expr'], return_type="STRPTR", c_template="((STRPTR)_dash_dbg_value_type((LONG)(${i}), (LONG)(${expr})))",
        reads_only=True, description='The type of expr in call i ("" if it cannot)'),
    "dbg_reg": BuiltinFunc(
        name="dbg_reg", params=['n'], return_type="LONG", c_template="((LONG)_dash_dbg_reg((LONG)(${n})))",
        reads_only=True, description='A register of the stopped program: 0-7 d0-d7, 8-15 a0-a7, 16 the PC'),
    "dbg_peek": BuiltinFunc(
        name="dbg_peek", params=['addr', 'size'], return_type="LONG", c_template="((LONG)_dash_dbg_peek((LONG)(${addr}), (LONG)(${size})))",
        reads_only=True, description='1, 2 or 4 bytes of memory at addr, without sign'),
    "dbg_output": BuiltinFunc(
        name="dbg_output", params=[], return_type="STRPTR", c_template="((STRPTR)_dash_dbg_output())",
        reads_only=True, description='What the program has written so far (output and error output)'),
}

# =============================================================================
# All built-in functions combined
# =============================================================================

# Dash 2.0: what programs did with @native (docs/DASHC_NATIVE.md), in groups of their own for docs/BUILTINS.md
def _move(src, names):
    return {n: src.pop(n) for n in names}


SYSPROG_FUNCTIONS = _move(TASK_FUNCTIONS, [
    "time_unix", "clock_days", "mem_largest", "program_exit", "run_command", "wb_open", "program_path", "locale_language",
    "cpu_model", "fpu_model", "library_version", "library_revision", "resident_version", "task_priority",
    "build_date", "build_time", "console_flush", "run_capture", "run_start", "run_ready", "run_break",
    "run_finish", "run_rc", "env_get", "env_set", "rexx_send", "rexx_rc", "rexx_port", "rexx_get", "rexx_reply", "notify", "ports_read", "port_name", "tasks_read",
    "task_entry_name", "task_entry_command", "task_entry_state", "task_entry_priority", "task_entry_cli",
    "assigns_read", "assign_name", "assign_path"])
IMGDEC_FUNCTIONS = _move(IMAGE_FUNCTIONS, [
    "image_decode", "image_decode_start", "image_decode_ready", "image_decode_finish", "image_decoded_width",
    "image_decoded_height", "image_decoded_alpha", "image_decoded_pixels",
    "image_decoded_free", "image_from_decoded", "image_from_decoded_size"])
WM_FUNCTIONS = _move(TASK_FUNCTIONS, [
    "wm_read", "wm_id", "wm_title", "wm_task", "wm_path", "wm_box", "wm_flags", "wm_set_box", "wm_front", "wm_back",
    "wm_activate", "wm_zip", "wm_active", "wm_at", "wm_pointer_x", "wm_pointer_y", "wm_bar_height", "wm_bar_gadgets", "file_real_path", "app_window",
    "app_drop", "app_drop_x", "app_drop_y", "icon_load", "icon_draw", "icon_draw_size", "icon_width", "icon_height", "icon_free"])
TTF_FUNCTIONS = _move(FONT_FUNCTIONS, ["font_from_ttf", "font_ttf_icon", "font_ttf_free", "font_ttf_forget"])
NETBG_FUNCTIONS = _move(NET_FUNCTIONS, [n for n in list(NET_FUNCTIONS) if n.startswith("net_bg_")])
OTHERWIN_FUNCTIONS = _move(SIMINPUT_FUNCTIONS, [
    "window_find", "window_found_activate", "window_found_box", "gadget_index", "gadget_x", "gadget_y",
    "gadget_selected", "screen_pixel", "screen_pixel_rgb", "screen_pen_rgb", "cx_send"])

# =============================================================================
# DashOS (docs/AARCH64_LOOP.md, A7): channels, handles, timers, memory objects, processes and groups of the
# DashOS kernel. Only with ./dash --dashos; on the Amiga they are a compile error. Handles are numbers (> 0);
# errors, negative numbers (dashos_error_text says which).
# =============================================================================

def _os(name, params, ret, template, desc, reads_only=False):
    return BuiltinFunc(name=name, params=params, return_type=ret, c_template=template, description=desc,
                       needs_dashos=True, reads_only=reads_only)


DASHOS_FUNCTIONS = {
    "channel_create": _os("channel_create", [], "LONG", "_dash_channel_create()",
                          "A new channel: one of its two ends (the other, channel_other); a negative error"),
    "channel_other": _os("channel_other", [], "LONG", "_dash_channel_other()",
                         "The other end of the last channel_create (what is written on one end is read on the other)"),
    "channel_pass": _os("channel_pass", ["handle"], "LONG", "_dash_channel_pass(${handle})",
                        "Puts a handle (with the right to pass it) in the next channel_send: it leaves this program; "
                        "up to 8 per message; 0, or -1 if there are 8 already"),
    "channel_send": _os("channel_send", ["handle", "text"], "LONG", "_dash_channel_send(${handle}, ${text})",
                        "Sends a text (up to 256 bytes) to the other end of the channel, without waiting: 0 or a "
                        "negative error", reads_only=True),
    "channel_send_buffer": _os("channel_send_buffer", ["handle", "buffer", "length"], "LONG",
                               "_dash_channel_send_buffer(${handle}, ${buffer}, ${length})",
                               "Sends length bytes (up to 256) of a buffer: 0 or a negative error"),
    "channel_receive": _os("channel_receive", ["handle"], "STRPTR", "_dash_channel_receive(${handle})",
                           "Waits for the next message of the channel and gives it as text; nil on error "
                           "(channel_error); its handles: channel_handles, channel_handle; who sent it: channel_mark"),
    "channel_receive_buffer": _os("channel_receive_buffer", ["handle", "buffer", "max"], "LONG",
                                  "_dash_channel_receive_buffer(${handle}, ${buffer}, ${max})",
                                  "Waits for the next message and copies it to a buffer (max bytes, 256 is enough): "
                                  "its length or a negative error"),
    "channel_handles": _os("channel_handles", [], "LONG", "_dash_channel_handles()",
                           "How many handles came with the last message received"),
    "channel_handle": _os("channel_handle", ["i"], "LONG", "_dash_channel_handle(${i})",
                          "Handle i (from 0) of the last message received; 0 if there is none"),
    "channel_mark": _os("channel_mark", [], "LONG", "_dash_channel_mark()",
                        "The mark of the handle that wrote the last message received (handle_copy): who sent it; 0 "
                        "unmarked or the kernel (timers)"),
    "channel_error": _os("channel_error", [], "LONG", "_dash_channel_error()",
                         "The error of the last channel_receive (0: none; -4: the other end closed)"),
    "handle_copy": _os("handle_copy", ["handle", "rights", "mark"], "LONG",
                       "_dash_handle_copy(${handle}, ${rights}, ${mark})",
                       "A copy of a handle with these rights or fewer (1 read, 2 write, 4 pass; added up) and a "
                       "mark if it had none (0: keep its own): the new handle or a negative error"),
    "handle_close": _os("handle_close", ["handle"], "LONG", "_dash_handle_close(${handle})",
                        "Closes a handle (the last one of a channel end closes that end): 0 or a negative error"),
    "handle_revocable": _os("handle_revocable", ["handle"], "LONG", "_dash_handle_revocable(${handle})",
                            "A copy of a handle that can be taken back (its revoker: handle_revoker): the copy or a "
                            "negative error"),
    "handle_revoker": _os("handle_revoker", [], "LONG", "_dash_handle_revoker()",
                          "The revoker of the last handle_revocable"),
    "handle_revoke": _os("handle_revoke", ["revoker"], "LONG", "_dash_handle_revoke(${revoker})",
                         "Revokes the handle of a revoker and the copies made from it: from then on they are worth "
                         "nothing: 0 or a negative error"),
    "timer_create": _os("timer_create", ["handle", "first_ms", "period_ms"], "LONG",
                        "_dash_timer_create(${handle}, ${first_ms}, ${period_ms})",
                        "A timer that sends a message to the other end of the channel after first_ms, and then "
                        "every period_ms (0: once); 10 ms steps; it stops when its handle is closed: the handle or a "
                        "negative error"),
    "memory_create": _os("memory_create", ["size"], "LONG", "_dash_memory_create(${size})",
                         "A memory object of size bytes (up to 4 MB), all zero; it can be passed to another program "
                         "(shared memory): its handle or a negative error"),
    "memory_map": _os("memory_map", ["handle", "writable"], "APTR", "_dash_memory_map(${handle}, ${writable})",
                      "Maps a memory object in this program, for buffer_* (writable: true to write in it): the "
                      "buffer, or 0"),
    "memory_unmap": _os("memory_unmap", ["buffer"], "LONG", "_dash_memory_unmap(${buffer})",
                        "Unmaps what memory_map gave (the object lives on while it has handles): 0 or a negative "
                        "error"),
    "process_give": _os("process_give", ["handle"], "LONG", "_dash_process_give(${handle})",
                        "A handle for the next process_start: the new program gets them as handles 1, 2... in "
                        "this order; up to 16; 0, or -1 if there are 16 already"),
    "process_group": _os("process_group", ["group"], "void", "_dash_process_group(${group})",
                         "The group of the next processes started (0: this program's own)"),
    "process_start": _os("process_start", ["memory", "size"], "LONG", "_dash_process_start(${memory}, ${size})",
                         "Starts a program from the ELF in a memory object (its first size bytes), with the handles "
                         "of process_give: the process or a negative error"),
    "process_start_buffer": _os("process_start_buffer", ["buffer", "length"], "LONG",
                                "_dash_process_start_buffer(${buffer}, ${length})",
                                "process_start with an ELF in a buffer (copied to a new memory object, up to 4 MB)"),
    "process_kill": _os("process_kill", ["process"], "LONG", "_dash_process_kill(${process})",
                        "Ends a process: 0 or a negative error"),
    "process_wait": _os("process_wait", ["process"], "LONG", "_dash_process_wait(${process})",
                        "Waits for a process to end: its exit code (how it ended: process_end), or a negative error"),
    "process_end": _os("process_end", [], "LONG", "_dash_process_end()",
                       "How the process of the last process_wait ended: 0 it exited, 1 it was killed, 2 it failed"),
    "group_create": _os("group_create", ["bytes"], "LONG", "_dash_group_create(${bytes})",
                        "A group with a memory budget taken from this program's: what its processes create is "
                        "charged to it: the group or a negative error"),
    "group_kill": _os("group_kill", ["group"], "LONG", "_dash_group_kill(${group})",
                      "Ends every process of a group and frees all it had: 0 or a negative error"),
    "group_used": _os("group_used", ["group"], "LONG", "_dash_group_used(${group})",
                      "The bytes a group has used (0: this program's group), or a negative error"),
    "group_limit": _os("group_limit", ["group"], "LONG", "_dash_group_limit(${group})",
                       "The budget of a group in bytes (0: this program's group), or a negative error"),
    "dashos_error_text": _os("dashos_error_text", ["code"], "STRPTR", "_dash_dashos_error_text(${code})",
                             "What a negative error of DashOS means, as text"),
}


# On DashOS some builtins have another C (A7): their own runtime there is AmigaOS's (SYSINFO_RUNTIME...)
DASHOS_TEMPLATES = {
    "program_exit": "_dash_exit((int)(${rc}))",
}

ALL_BUILTINS = {
    **GRAPHICS_BASIC,
    **GRAPHICS_ADVANCED,
    **INPUT_FUNCTIONS,
    **GADTOOLS_FUNCTIONS,
    **MENU_FUNCTIONS,
    **ASL_FUNCTIONS,
    **REACTION_FUNCTIONS,
    **SYSTEM_FUNCTIONS,
    **DOS_FUNCTIONS,
    **BUFFER_FUNCTIONS,
    **TEXT_FUNCTIONS,          # dashweb D2
    **NET_FUNCTIONS,           # dashweb D8
    **TLS_FUNCTIONS,           # dashweb D11
    **FONT_FUNCTIONS,          # dashweb D9
    **BLEND_FUNCTIONS,
    **RGB_FUNCTIONS,
    **TASK_FUNCTIONS,          # dashweb D47
    **IMAGE_FUNCTIONS,         # dashweb D12
    **ARGS_FUNCTIONS,          # dashweb D19
    **ZLIB_FUNCTIONS,          # Lorraine D6
    **UTF8_FUNCTIONS,          # Lorraine D5
    **BUFSEARCH_FUNCTIONS,     # Lorraine D38, D39
    **DOUBLE_FUNCTIONS,        # Lorraine D3
    **MATH_FUNCTIONS,          # Lorraine D4
    **REGEX_FUNCTIONS,         # Lorraine D45
    **SIMINPUT_FUNCTIONS,      # Lorraine D46
    **CLIP_FUNCTIONS,          # Lorraine D18
    **COLLATE_FUNCTIONS,       # Lorraine D7
    **SYSPROG_FUNCTIONS,       # Dash 2.0
    **DEBUGGER_FUNCTIONS,      # Dash 2.0: Forja
    **JSON_FUNCTIONS,          # Dash 2.0: lib/json.dash
    **IMGDEC_FUNCTIONS,
    **TTF_FUNCTIONS,
    **NETBG_FUNCTIONS,
    **OTHERWIN_FUNCTIONS,
    **WM_FUNCTIONS,
    **AUDIO_FUNCTIONS,
    **INTUITION_EXPANDED,
    **RTG_FUNCTIONS,
    **MUI_FUNCTIONS,
    **DASHOS_FUNCTIONS,        # A7
}


def get_builtin(name: str) -> Optional[BuiltinFunc]:
    """Get a built-in function by name."""
    return ALL_BUILTINS.get(name)


def is_builtin(name: str) -> bool:
    """Check if a function name is a built-in."""
    return name in ALL_BUILTINS


def get_all_builtins() -> dict:
    """Get all built-in functions."""
    return ALL_BUILTINS
