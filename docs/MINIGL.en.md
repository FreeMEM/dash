*English | [Castellano](MINIGL.md)*

# 3D with MiniGL

The `gl_*` functions draw in 3D with MiniGL, the Amiga's part of OpenGL 1.x. They work on both paths (`./dash` and
`./dash --gcc`), with and without `--fpu`. Asked for by the user (step 5.3 of Forja's `FORJA_LOOP`). Full list:
[BUILTINS.en.md](BUILTINS.en.md#3d-with-minigl).

## What is needed

- `minigl.library` 29 or newer. There are several, all with the same interface:
  - **MiniGL Classic** (Steffen Häuser, Aminet `util/libs/MiniGL_Library_Classic.lha`), over a Warp3D: classic 3D
    cards (CyberVision 64/3D, PCI Voodoo 3), QuarkTex in WinUAE or Wazp3D, which is Warp3D in software.
  - **PiStorm3D** (Aminet `util/libs/PiStorm3D.lha`): with the Raspberry Pi's GPU on a PiStorm32 with a Pi 4 or CM4.
  - **RadeonGL** (Aminet `driver/video/RadeonGL.lha`): Radeon R200 with Picasso96.
- A FPU. The libraries are built for one: without a FPU, `gl_open` gives `false` instead of hanging.
- An RTG screen for the window (`gl_open`); `gl_open_screen` opens a 16-bit screen of its own.

Dash does not need the MiniGL SDK: it calls the library through its table of functions (ABI 5 of
`libraries/minigl_dispatch.h`), with OpenGL's numbers.

## How to use it

```ruby
import "lib/amiga/gl.dash"      # GL_TRIANGLES, GL_DEPTH_TEST, GL_BLEND...

Main
    if not gl_open(320, 240)
        Print "minigl.library and a FPU are needed"
        program_exit(5)
    end
    gl_enable(GL_DEPTH_TEST)
    angle = 0.0
    while not gl_closed()
        gl_clear()
        gl_load_identity()
        gl_translate(0, 0, -4)
        gl_rotate(angle, 0, 1, 0)
        gl_begin(GL_TRIANGLES)
        gl_color(1, 0, 0)
        gl_vertex(0, 1, 0)
        gl_color(0, 1, 0)
        gl_vertex(-1, -1, 0)
        gl_color(0, 0, 1)
        gl_vertex(1, -1, 0)
        gl_end()
        gl_swap()
        angle = angle + 2.0
    end
end
```

- **Context:** `gl_open(width, height)` (a window on the Workbench) or `gl_open_screen(width, height)`, `gl_close`,
  `gl_swap`, `gl_vsync(on)`, `gl_closed()`, `gl_key()`. `gl_open` leaves a 60 degree perspective and the modelview
  matrix current. `gl_swap` waits for the screen's refresh; `gl_vsync(false)` takes the wait away.
- **State:** `gl_enable`/`gl_disable` with the constants of `lib/amiga/gl.dash`, `gl_clear_color`, `gl_clear`,
  `gl_viewport`, `gl_shade_model`, `gl_cull_face`, `gl_blend_func`.
- **Matrices:** `gl_matrix_mode`, `gl_load_identity`, `gl_push_matrix`, `gl_pop_matrix`, `gl_translate`,
  `gl_rotate`, `gl_scale`, `gl_perspective`, `gl_ortho`, `gl_look_at`.
- **Shapes:** `gl_begin(mode)` ... `gl_end()`, with `gl_vertex`, `gl_color`, `gl_color_alpha`, `gl_normal` and
  `gl_tex_coord`.
- **Textures:** `gl_texture(d)` from an `image_decode` image (PNG, JPEG, GIF, BMP, WebP), taken to powers of two up
  to 256 x 256; `gl_texture_bind(t)` (0: no texture), `gl_texture_free(t)`.
- **Lights:** `gl_light(n, x, y, z)` turns on light n from that direction, with `gl_color` as the material;
  `gl_light_color`, `gl_ambient`. Each face needs its `gl_normal`.
- **Fog:** `gl_fog(start, end, r, g, b)`; `gl_disable(GL_FOG)` takes it away.
- **Others:** `gl_read_pixel(x, y)` (the colour of a pixel before `gl_swap`, for tests) and `gl_error()`.

The numbers go to MiniGL as `float`: a `Float`, an `Int` or a `Double` is fine. Colours go from 0.0 to 1.0.

## Floating point

`gl_*` programs do not need `--fpu`: they work the same without it, because the runtime hands the numbers to the
library as C `float`. But the library does need a FPU, so the machine has one. With `--fpu` the program's own maths
(angles, `sin`, `cos`, its own matrices) use the FPU instead of software: that is the advice.

## Tried in the emulator

On the `coffin` machine (FS-UAE, 68040 with JIT, RTG), with MiniGL Classic 30.0 over the Wazp3D 57V that the CoffinOS
disk carries. The disk has no `minigl.library`: the tests put it in `LIBS:` of the disk's copy.

```bash
DASH_EMU_MINIGL=~/.cache/dash-emu/minigl/minigl.library python3 tests/run_tests.py test_gl --emu-coffin
tools/emu_run.py --machine coffin --lib ~/.cache/dash-emu/minigl/minigl.library examples/gl_cubo.dash
```

`examples/gl_cubo.dash` (a lit cube, 320 x 240) runs at 56 frames a second waiting for the refresh, and at about 300
without waiting (`RAPIDO=1`), the same on both paths and with or without `--fpu`. It is an emulated 68040 at full
speed: on a real Amiga with Wazp3D it will be much slower.

What Wazp3D, with its default settings, does not do (also from a C program, so it is not Dash's doing):

- The Z buffer has no effect: the last thing drawn wins. A convex object looks right with `GL_CULL_FACE`.
- A colour per corner comes out flat (the first corner's).
- Blending (`GL_BLEND`) mixes with black, not with what is below.
- There is no fog (it is off in its preferences, `SYS:Prefs/Wazp3D`).
- With a texture, the colour of `gl_color` does not tint it.

`gl_open` fixes two things of MiniGL Classic over Wazp3D: the first shape of a new context was not drawn, and
`GL_CULL_FACE` took away the front faces (the ones seen counterclockwise). It checks this when opening, by drawing
and reading the middle pixel, so with another library that gets it right nothing changes.

Not tried: PiStorm3D, RadeonGL, and MiniGL Classic with a 3D card or with QuarkTex.
