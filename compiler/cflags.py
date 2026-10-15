"""gcc options for the generated C, shared by ./dash and tests/run_tests.py."""

# -O2 by default: tested in FS-UAE (Kickstart 3.1) with the 30 examples and the
# emu tests, same output as -O0 and about half the size.
# -fomit-frame-pointer: no link/unlk in every function, one more address register.
# -fbbb without "e" and "r": bebbo's optimizer (run after GCC's own passes) gave
# wrong code twice, found by tools/fuzz_refcount.py in --memcheck builds on the A1200:
#   - "r" (register renaming) with "e": a value kept in a1 across calls that change
#     a1; the list literal [Punto(1, 1), L[2], L[0]] got L[0] as 0.
#   - "e" alone (remove dead assignments and "redundant" loads): a sum read a stale
#     value (139 instead of 144, seed 12).
# The default is "abcefhilmnprsz0"; without "e" and "r" the benchmarks keep their
# speed and size.
BBB = "-fbbb=abcfhilmnpsz0"
# Address 0 is readable memory on an Amiga, and nil is C NULL. Without these, GCC
# turns a read through a pointer it knows is NULL ("var n: Nodo = nil" then n.valor)
# into a trap instruction (the program crashes instead of reading garbage), and drops
# NULL checks that come after a dereference.
NULL_OK = ["-fno-isolate-erroneous-paths-dereference", "-fno-delete-null-pointer-checks"]
OPTIMIZE = ["-O2", "-fomit-frame-pointer", BBB] + NULL_OK
SMALL = ["-Os", "-fomit-frame-pointer", BBB] + NULL_OK
DEBUG = ["-O0"]


def opt_flags(no_optimize: bool = False, small: bool = False):
    return list(DEBUG if no_optimize else SMALL if small else OPTIMIZE)
