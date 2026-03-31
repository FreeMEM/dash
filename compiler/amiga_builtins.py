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
        c_template="SetAPen(_dash_rp, ${color})",
        needs_gfx=True,
        description="Set foreground pen color"
    ),
    "gfx_pen_bg": BuiltinFunc(
        name="gfx_pen_bg",
        params=["color"],
        return_type="void",
        c_template="SetBPen(_dash_rp, ${color})",
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
        c_template="SetDrMd(_dash_rp, ${mode})",
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
        c_template="SetRGB32(&_dash_win->WScreen->ViewPort, ${index}, ${r}<<24, ${g}<<24, ${b}<<24)",
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
        c_template="AreaEllipse(_dash_rp, ${cx}, ${cy}, ${rx}, ${ry}); AreaEnd(_dash_rp)",
        needs_gfx=True,
        needs_area=True,
        description="Draw filled ellipse"
    ),
    "gfx_circle_fill": BuiltinFunc(
        name="gfx_circle_fill",
        params=["cx", "cy", "r"],
        return_type="void",
        c_template="AreaEllipse(_dash_rp, ${cx}, ${cy}, ${r}, ${r}); AreaEnd(_dash_rp)",
        needs_gfx=True,
        needs_area=True,
        description="Draw filled circle"
    ),
    "gfx_flood": BuiltinFunc(
        name="gfx_flood",
        params=["x", "y", "mode"],
        return_type="void",
        c_template="Flood(_dash_rp, ${mode}, ${x}, ${y})",
        needs_gfx=True,
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
        c_template="AreaMove(_dash_rp, ${x}, ${y})",
        needs_gfx=True,
        needs_area=True,
        description="Begin polygon at point"
    ),
    "gfx_poly_add": BuiltinFunc(
        name="gfx_poly_add",
        params=["x", "y"],
        return_type="void",
        c_template="AreaDraw(_dash_rp, ${x}, ${y})",
        needs_gfx=True,
        needs_area=True,
        description="Add polygon vertex"
    ),
    "gfx_poly_end": BuiltinFunc(
        name="gfx_poly_end",
        params=[],
        return_type="void",
        c_template="AreaEnd(_dash_rp)",
        needs_gfx=True,
        needs_area=True,
        description="Close and fill polygon"
    ),

    # Blitting
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
        c_template="_dash_sprite_load(${id}, ${filename})",
        needs_gfx=True,
        description="Load sprite from file"
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
        description="Set sprite color"
    ),
    "sprite_frame": BuiltinFunc(
        name="sprite_frame",
        params=["id", "frame"],
        return_type="void",
        c_template="_dash_sprite_frame(${id}, ${frame})",
        needs_gfx=True,
        description="Set sprite animation frame"
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
        description="Load BOB from file"
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
    "bob_free": BuiltinFunc(
        name="bob_free",
        params=["id"],
        return_type="void",
        c_template="_dash_bob_free(${id})",
        needs_gfx=True,
        description="Free BOB memory"
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
        description="Load IFF bitmap"
    ),
    "bitmap_save": BuiltinFunc(
        name="bitmap_save",
        params=["id", "filename"],
        return_type="BOOL",
        c_template="_dash_bitmap_save(${id}, ${filename})",
        needs_gfx=True,
        description="Save IFF bitmap"
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
        c_template="(_dash_win->MouseX - _dash_win->BorderLeft)",
        description="Mouse X position relative to window inner area"
    ),
    "mouse_y": BuiltinFunc(
        name="mouse_y",
        params=[],
        return_type="LONG",
        c_template="(_dash_win->MouseY - _dash_win->BorderTop)",
        description="Mouse Y position relative to window inner area"
    ),
    "mouse_button": BuiltinFunc(
        name="mouse_button",
        params=["btn"],
        return_type="BOOL",
        c_template="_dash_mouse_button(${btn})",
        description="Check mouse button (0=left, 1=right)"
    ),

    # Window events
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
        c_template="if (_dash_win) { CloseWindow(_dash_win); _dash_win = NULL; }",
        description="Close the current window"
    ),

    # Screen Support
    "screen_open": BuiltinFunc(
        name="screen_open",
        params=["depth", "title"],
        return_type="BOOL",
        c_template="_dash_open_screen(${depth}, ${title}) != NULL",
        needs_gfx=True,
        description="Open a screen cloning Workbench display mode with custom depth"
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
        description="Create ReAction window with layout"
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
        description="Close ReAction window and free resources"
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
        description="Get gadget numeric value (checkbox, slider, integer)"
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
        description="Set gadget value"
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
        description="No event code (0)"
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
}


# =============================================================================
# SYSTEM - Memory, Time, Random (10 functions)
# =============================================================================

SYSTEM_FUNCTIONS = {
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
        description="Total available memory"
    ),
    "peek_byte": BuiltinFunc(
        name="peek_byte",
        params=["addr"],
        return_type="LONG",
        c_template="(*((UBYTE *)(${addr})))",
        description="Read byte from memory address"
    ),
    "peek_word": BuiltinFunc(
        name="peek_word",
        params=["addr"],
        return_type="LONG",
        c_template="(*((UWORD *)(${addr})))",
        description="Read word from memory address"
    ),
    "peek_long": BuiltinFunc(
        name="peek_long",
        params=["addr"],
        return_type="LONG",
        c_template="(*((ULONG *)(${addr})))",
        description="Read long from memory address"
    ),
    "poke_byte": BuiltinFunc(
        name="poke_byte",
        params=["addr", "value"],
        return_type="void",
        c_template="*((UBYTE *)(${addr})) = (UBYTE)(${value})",
        description="Write byte to memory address"
    ),
    "poke_word": BuiltinFunc(
        name="poke_word",
        params=["addr", "value"],
        return_type="void",
        c_template="*((UWORD *)(${addr})) = (UWORD)(${value})",
        description="Write word to memory address"
    ),
    "poke_long": BuiltinFunc(
        name="poke_long",
        params=["addr", "value"],
        return_type="void",
        c_template="*((ULONG *)(${addr})) = (ULONG)(${value})",
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
        description="Open file (mode: MODE_OLDFILE, MODE_NEWFILE, MODE_READWRITE)"
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
        c_template="(FGetC(${handle}) == -1)",
        needs_dos=True,
        description="Check end of file"
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
        c_template="FPuts(${handle}, ${str})",
        needs_dos=True,
        description="Write string"
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
        description="Copy file"
    ),

    # Directories
    "dir_create": BuiltinFunc(
        name="dir_create",
        params=["path"],
        return_type="BOOL",
        c_template="(CreateDir(${path}) != 0)",
        needs_dos=True,
        description="Create directory"
    ),
    "dir_change": BuiltinFunc(
        name="dir_change",
        params=["path"],
        return_type="BOOL",
        c_template="_dash_dir_change(${path})",
        needs_dos=True,
        description="Change current directory"
    ),
    "dir_current": BuiltinFunc(
        name="dir_current",
        params=["buffer", "maxlen"],
        return_type="BOOL",
        c_template="_dash_dir_current(${buffer}, ${maxlen})",
        needs_dos=True,
        description="Get current directory"
    ),

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
        description="Load IFF 8SVX sound"
    ),
    "sound_create": BuiltinFunc(
        name="sound_create",
        params=["id", "length", "rate"],
        return_type="BOOL",
        c_template="_dash_sound_create(${id}, ${length}, ${rate})",
        needs_audio=True,
        description="Create empty sound buffer"
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
        description="Play sound on channel (0-3)"
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
        description="Play sound looped"
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
        description="Set channel period (pitch)"
    ),

    # Music (MOD/ProTracker)
    "music_load": BuiltinFunc(
        name="music_load",
        params=["filename"],
        return_type="BOOL",
        c_template="_dash_music_load(${filename})",
        needs_audio=True,
        description="Load MOD file"
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
        description="Play tone (frequency in Hz)"
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
        description="Create window (returns handle)"
    ),
    "window_close": BuiltinFunc(
        name="window_close",
        params=["handle"],
        return_type="void",
        c_template="_dash_window_close(${handle})",
        description="Close window"
    ),
    "window_title": BuiltinFunc(
        name="window_title",
        params=["handle", "title"],
        return_type="void",
        c_template="SetWindowTitles(_dash_windows[${handle}], ${title}, (UBYTE *)-1)",
        description="Set window title"
    ),
    "window_move": BuiltinFunc(
        name="window_move",
        params=["handle", "x", "y"],
        return_type="void",
        c_template="MoveWindow(_dash_windows[${handle}], ${x}, ${y})",
        description="Move window"
    ),
    "window_resize": BuiltinFunc(
        name="window_resize",
        params=["handle", "w", "h"],
        return_type="void",
        c_template="SizeWindow(_dash_windows[${handle}], ${w}, ${h})",
        description="Resize window"
    ),
    "window_to_front": BuiltinFunc(
        name="window_to_front",
        params=["handle"],
        return_type="void",
        c_template="WindowToFront(_dash_windows[${handle}])",
        description="Bring window to front"
    ),
    "window_to_back": BuiltinFunc(
        name="window_to_back",
        params=["handle"],
        return_type="void",
        c_template="WindowToBack(_dash_windows[${handle}])",
        description="Send window to back"
    ),
    "window_activate": BuiltinFunc(
        name="window_activate",
        params=["handle"],
        return_type="void",
        c_template="ActivateWindow(_dash_windows[${handle}])",
        description="Activate window"
    ),

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

    # Menus - see MENU_FUNCTIONS for simpler API

    # Dialogs (ASL)
    "dialog_file": BuiltinFunc(
        name="dialog_file",
        params=["title", "pattern", "save_mode"],
        return_type="STRPTR",
        c_template="_dash_dialog_file(${title}, ${pattern}, ${save_mode})",
        needs_asl=True,
        description="Show file requester"
    ),
    "dialog_color": BuiltinFunc(
        name="dialog_color",
        params=["title", "initial"],
        return_type="LONG",
        c_template="_dash_dialog_color(${title}, ${initial})",
        needs_asl=True,
        description="Show color requester"
    ),
    "dialog_font": BuiltinFunc(
        name="dialog_font",
        params=["title"],
        return_type="STRPTR",
        c_template="_dash_dialog_font(${title})",
        needs_asl=True,
        description="Show font requester"
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
        description="Get current screen bit depth"
    ),
    "rtg_get_width": BuiltinFunc(
        name="rtg_get_width",
        params=[],
        return_type="LONG",
        c_template="_dash_rtg_get_width()",
        needs_rtg=True,
        description="Get current screen width"
    ),
    "rtg_get_height": BuiltinFunc(
        name="rtg_get_height",
        params=[],
        return_type="LONG",
        c_template="_dash_rtg_get_height()",
        needs_rtg=True,
        description="Get current screen height"
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
# All built-in functions combined
# =============================================================================

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
    **AUDIO_FUNCTIONS,
    **INTUITION_EXPANDED,
    **RTG_FUNCTIONS,
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
