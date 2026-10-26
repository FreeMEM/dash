# zlib for `inflate`, `deflate` and `crc32`

The `.c` and `.h` files of zlib 1.3.1 (https://zlib.net, `zlib-1.3.1.tar.gz`, SHA-256
`9a93b2b7dfdac77ceba5a558a580e74667dd6fede4585b91eefb60f03b72df23`) come unchanged: only the ones raw
deflate needs. `gzguts.h` is there because `zutil.c` includes it; the gz* files are not compiled.

`dash_inflate.c`, `dash_deflate.c` and `dash_crc32.c` (Dash's own, with `dash_zlib.h`) are what the
generated C calls: one buffer to another in one call, raw deflate (no zlib or gzip wrapper, what a ZIP
holds), zlib's memory from exec and back before returning. One file each, so a program that only
inflates does not link deflate.

`compiler/zlib.py` compiles them once for each set of CPU options (`--cpu`, `--fpu`) into a library in
`build/`, with `-DZ_PREFIX` (zlib's names start with `z_`: a program may have its own `crc32`),
`-DNO_GZIP` and `-DZ_TESTW=0` (crc32 with one table of 1 KB, not the 20 KB of the "braided" one, which
is for 64-bit machines). The CLI and the test runner link it when a program uses those builtins.

Size in the executable (68000, -O2): `inflate` alone about 15 KB, the three about 39 KB.
On a 68030 with FPU (FS-UAE, about 50 MHz), `inflate` of 1 MB of XML takes about 0.75 s;
`deflate` at level 6, about 9 s.

License: zlib's (`LICENSE`), which allows linking it into programs under any license.
