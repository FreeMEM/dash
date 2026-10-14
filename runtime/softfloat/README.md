# Software floating point for Dash `Float`

`fp-bit.c` and `fp-bit.h` come unchanged from GCC's libgcc (the GCC 6 sources of the
m68k-amigaos toolchain). Compiled with `-DFLOAT -DFLOAT_ONLY` they provide the
single-precision routines GCC calls on a CPU without FPU (`__addsf3`, `__mulsf3`,
`__divsf3`, comparisons and int conversions). `stub/` holds empty versions of the
GCC build headers the file includes.

Why not libnix's `libm` (`-lm`)? Its routines call `mathieeesingbas.library` from the
ROM. In FS-UAE with the original Kickstart 3.1 (40.68, CRC32 1483A091) and no FPU,
`IEEESPMul` never returns (it works with Kickstart 3.2.3, with AROS and with an FPU).
These routines are plain C, so a Dash program behaves the same on every Kickstart.

License: GPL v3 with the GCC Runtime Library Exception (`COPYING.RUNTIME`), which
allows linking them into programs under any license.

`compiler/softfloat.py` compiles this file once per toolchain into `build/` and the
CLI and the test runner link it when a program uses `Float`.
