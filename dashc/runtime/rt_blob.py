#!/usr/bin/env python3
"""Los dos runtimes como arrays de C dentro de dashc: el normal tal cual (descomprimirlo en cada compilación
costaba 4,5 s en un A1200) y el de --memcheck comprimido con zlib (se usa poco: main.c lo descomprime solo
entonces). Así el dashc del Amiga pasa de 1,4 MB a unos 900 KB.

    python3 runtime/rt_blob.py runtime/dashrt.o runtime/dashrt_mc.o > build/rt_blob.c"""
import sys
import zlib


def array(name, data):
    return f"const unsigned char {name}[] = {{{','.join(str(b) for b in data)}}};\n"


def main():
    a = open(sys.argv[1], "rb").read()
    b = open(sys.argv[2], "rb").read()
    z = zlib.compress(b, 9)
    sys.stdout.write(array("rt_normal", a) + f"const unsigned int rt_normal_len = {len(a)};\n" +
                     array("rt_mc_z", z) + f"const unsigned int rt_mc_zlen = {len(z)}, rt_mc_len = {len(b)};\n")


if __name__ == "__main__":
    main()
