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
        description="Show frame number frame (0 the first) of a sprite from sprite_load"
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
        params=[],
        return_type="STRPTR",
        c_template="_dash_dir_current()",
        needs_dos=True,
        description="Full name of the current directory (\"Ram Disk:\" ...)"
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
        description="Load an IFF 8SVX sound (uncompressed)"
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
        description="The top border of the current window (title bar included); GadTools gadgets count from the "
                    "outer corner, so add it to their y"),
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
        description="The width of a text in the screen's font"),
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
    "dialog_color": BuiltinFunc(
        name="dialog_color",
        params=["title", "initial"],
        return_type="LONG",
        c_template="_dash_dialog_color(${title}, ${initial})",
        needs_asl=True,
        needs_gfx=True,
        description="Palette window: returns the chosen pen (click, or arrows + Return); Esc keeps initial"
    ),
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
        description="Value: checkbox 1/0, cycle option, slider level, progress"
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
        description="Change the text of a text field, text, button or window title"
    ),
    "mui_set_enabled": BuiltinFunc(
        name="mui_set_enabled",
        params=["obj", "enabled"],
        return_type="void",
        c_template="_dash_mui_set_enabled(${obj}, ${enabled})",
        description="Enable or disable (ghost) an object"
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
        description="mui_wait_event returns id when Return is pressed in a text field"
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
    "mui_menu_separator": BuiltinFunc(
        name="mui_menu_separator",
        params=[],
        return_type="void",
        c_template="_dash_mui_menu_separator()",
        description="Separator line in the menu"
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
    "mui_help": BuiltinFunc(
        name="mui_help",
        params=["obj", "text"],
        return_type="void",
        c_template="_dash_mui_help(${obj}, ${text})",
        description="Bubble help shown when the pointer rests on the object"
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
        description="Run an @native function f(arg: Int) -> Int in another process (C only: malloc/free yes, "
                    "Dash strings and lists no; 128 KB of stack, the program's priority): the task, or 0"),
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
                    "it is compared (the rest stays as it was)"),
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
        description="A tooltype of the program: from the Shell, the argument NAME=value (NAME=\"a b\" too); else (or "
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
    "wifi_read": BuiltinFunc(
        name="wifi_read", params=["interface", "ms"], return_type="LONG",
        c_template="_dash_wifi_read(${interface}, ${ms})",
        description="Asks the SANA-II driver of a Roadshow interface for its WiFi signal, waiting ms milliseconds at "
                    "most: 0 read (wifi_signal, wifi_noise), 1 no answer in time, 2 the driver does not tell, 3 no "
                    "such interface, 4 the driver gives an error (offline), 5 the stack has the driver only for "
                    "itself, -1 no Roadshow"),
    "wifi_read_device": BuiltinFunc(
        name="wifi_read_device", params=["driver", "unit", "ms"], return_type="LONG",
        c_template="_dash_wifi_read_device(${driver}, ${unit}, ${ms})",
        description="Like wifi_read, asking a SANA-II driver that is in use (\"wifipi.device\", unit 0) directly, "
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
        description="Asks a SANA-II driver in use for its packets in and out, waiting ms at most: the codes of "
                    "wifi_read_device (0 read: net_driver_packets_in, net_driver_packets_out)"),
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
                       "How many arguments the program got from the Shell (0 from the Workbench)"),
    "arg": _text("arg", ["i"], "STRPTR", "_dash_arg(${i})", "Argument i, from 0 (\"\" if there is none)"),
    # dashweb D27: where the last On Click was, inside the window's borders
    "click_x": _text("click_x", [], "LONG", "_dash_click_x", "X of the last On Click, in the window (inside its borders)"),
    "click_y": _text("click_y", [], "LONG", "_dash_click_y", "Y of the last On Click, in the window (inside its borders)"),
    # dashweb D20
    "time_ms": _text("time_ms", [], "LONG", "_dash_time_ms()",
                     "Milliseconds since the program started (EClock of timer.device)"),
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
    **TEXT_FUNCTIONS,          # dashweb D2
    **NET_FUNCTIONS,           # dashweb D8
    **TLS_FUNCTIONS,           # dashweb D11
    **FONT_FUNCTIONS,          # dashweb D9
    **BLEND_FUNCTIONS,
    **RGB_FUNCTIONS,
    **TASK_FUNCTIONS,          # dashweb D47
    **IMAGE_FUNCTIONS,         # dashweb D12
    **ARGS_FUNCTIONS,          # dashweb D19
    **AUDIO_FUNCTIONS,
    **INTUITION_EXPANDED,
    **RTG_FUNCTIONS,
    **MUI_FUNCTIONS,
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
