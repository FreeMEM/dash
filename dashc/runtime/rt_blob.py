#!/usr/bin/env python3
"""Los dos runtimes preparados (dashc --preparar, "DRT1") como arrays de C dentro de dashc. El normal pasa a
"DRT2": los datos de cada hunk comprimidos aparte (deflate crudo), y hunk.c descomprime solo los de los hunks que
van en el programa (descomprimirlo entero en cada compilación costaba 4,5 s en un A1200). El de --memcheck,
comprimido entero con zlib (se usa poco: main.c lo descomprime solo entonces).

    python3 runtime/rt_blob.py runtime/dashrt.o runtime/dashrt_mc.o > build/rt_blob.c"""
import struct
import sys
import zlib


def drt2(b):
    """DRT1 -> DRT2: tras las referencias, una tabla con el tamaño comprimido de cada hunk (0: va tal cual), y
    los datos de cada uno comprimidos si así ocupan menos"""
    L = lambda o: struct.unpack_from(">I", b, o)[0]
    nh, ns, nr, nrel, stl, dl = (L(4 * i) for i in range(1, 7))
    hp = 28
    fp_end = hp + nh * 28 + nrel * 8 + ns * 12 + nr * 12
    strs = b[fp_end:fp_end + stl]
    data = b[fp_end + stl:fp_end + stl + dl]
    table = bytearray(b[hp:hp + nh * 28])
    zl, out = [], bytearray()
    for i in range(nh):
        size, off = L(hp + i * 28 + 4), L(hp + i * 28 + 16)
        if off == 0xFFFFFFFF:
            zl.append(0)
            continue
        raw = data[off:off + size]
        c = zlib.compressobj(9, zlib.DEFLATED, -15)
        z = c.compress(raw) + c.flush()
        struct.pack_into(">I", table, i * 28 + 16, len(out))
        if len(z) + 8 < len(raw):
            out += z
            zl.append(len(z))
        else:
            out += raw
            zl.append(0)
        while len(out) & 3:
            out.append(0)
    head = b"DRT2" + struct.pack(">6I", nh, ns, nr, nrel, stl, len(out))
    return (head + bytes(table) + b[hp + nh * 28:fp_end] + struct.pack(f">{nh}I", *zl) + strs + bytes(out))


def array(name, data):
    return f"const unsigned char {name}[] = {{{','.join(str(b) for b in data)}}};\n"


def main():
    a = drt2(open(sys.argv[1], "rb").read())
    b = open(sys.argv[2], "rb").read()
    z = zlib.compress(b, 9)
    sys.stdout.write(array("rt_normal", a) + f"const unsigned int rt_normal_len = {len(a)};\n" +
                     array("rt_mc_z", z) + f"const unsigned int rt_mc_zlen = {len(z)}, rt_mc_len = {len(b)};\n")


if __name__ == "__main__":
    main()
