#!/usr/bin/env python3
"""Iconos de Workbench para los paquetes del Amiga (el de Dash, tools/paquete_amiga.py): ficheros .info clásicos
(DiskObject, 4 colores del Workbench: gris, negro, blanco, azul), que lee cualquier Workbench de 3.0 a 3.2.
Los mismos que usa el paquete de Tachyon (su tools/iconos_wb.py).

    python3 tools/iconos_wb.py DIR        # (el main de Tachyon: escribe en DIR los .info de su paquete)
"""

import struct
import sys
from pathlib import Path

GRIS, NEGRO, BLANCO, AZUL = 0, 1, 2, 3
WBDISK, WBDRAWER, WBTOOL, WBPROJECT = 1, 2, 3, 4
SIN_SITIO = 0x80000000


class Lienzo:
    def __init__(self, ancho, alto):
        self.ancho, self.alto = ancho, alto
        self.p = [[GRIS] * ancho for _ in range(alto)]

    def punto(self, x, y, c):
        if 0 <= x < self.ancho and 0 <= y < self.alto:
            self.p[y][x] = c

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.punto(x, y, c)

    def marco(self, x0, y0, x1, y1, c):
        for x in range(x0, x1 + 1):
            self.punto(x, y0, c)
            self.punto(x, y1, c)
        for y in range(y0, y1 + 1):
            self.punto(x0, y, c)
            self.punto(x1, y, c)

    def linea(self, x0, y0, x1, y1, c):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            self.punto(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n), c)

    def elipse(self, cx, cy, rx, ry, c, llena=False):
        for y in range(cy - ry, cy + ry + 1):
            for x in range(cx - rx, cx + rx + 1):
                d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                if (llena and d <= 1.0) or (not llena and 0.75 <= d <= 1.15):
                    self.punto(x, y, c)

    def planos(self):
        """Los dos planos de bits (fila a fila, palabras de 16 bits)"""
        palabras = (self.ancho + 15) // 16
        r = b""
        for plano in range(2):
            for fila in self.p:
                bits = 0
                for x, c in enumerate(fila):
                    if (c >> plano) & 1:
                        bits |= 1 << (palabras * 16 - 1 - x)
                r += bits.to_bytes(palabras * 2, "big")
        return r


def cajon():
    l = Lienzo(40, 20)
    l.rect(2, 4, 37, 18, BLANCO)
    l.marco(2, 4, 37, 18, NEGRO)
    l.rect(4, 6, 35, 9, AZUL)
    l.rect(4, 12, 35, 16, AZUL)
    l.rect(16, 7, 23, 8, NEGRO)
    l.rect(16, 13, 23, 14, NEGRO)
    l.linea(2, 4, 6, 1, NEGRO)
    l.linea(37, 4, 33, 1, NEGRO)
    l.linea(6, 1, 33, 1, NEGRO)
    return l


# El logo de Tachyon (docs/logo/tachyon_marca.svg) en 54x23 y 4 colores (. gris, N negro, A azul, B blanco): la esfera
# con sus dos cortes y el anillo plano. Lo saca tools/logo_tachyon.py --icono; los píxeles se cuentan 1,35 veces más
# altos que anchos (entre los de hires 640x256 y los cuadrados de RTG): se ve redonda en los dos. Se puede retocar a mano.
ICONO_TACHYON = [
    "......................................................",
    "........................AAAAAA........................",
    "....................AAAAAAAAAAAAAA....................",
    "..................AAAAAAAAAAAAAAAAAA..................",
    ".................AAAAAAAAAAAAAAAAAAAA.................",
    "..................AAAAAAAAAAAAAAAAAAAA..NNNNNNNNN.....",
    "..........................AAAAAAAAAAAAA..NNNNNNNNNN...",
    "..............AAAAAAAAAAAAAAAAAAAAAAAAAA..NNNNNNNNNN..",
    "..............AAAAAAAAAAAAAAAAAAAAAAAAAA...NNNNNNNNN..",
    "..........NN..AAAAAAAAAAAAAAAAAAA..AAAAAA..NNNNNNNN...",
    "........NNNN....AAAAAAAAAAAA....AAAAAAAA...NNNNNNN....",
    "......NNNNN.................AAAAAAAAAA...NNNNNNNN.....",
    "....NNNNNNN..AAA......AAAAAAAAAAAAA....NNNNNNNN.......",
    "...NNNNNNNN...AAAAAAAAAAAAAAAAA.....NNNNNNNN..........",
    "..NNNNNNNNN...AAAAAAAAAA.........NNNNNNNN.............",
    "..NNNNNNNNNN...............NNNNNNNNNNN................",
    "...NNNNNNNNNNNNNNNNNNNNNNNNNNNNNN.....................",
    ".....NNNNNNNNNNNNNNNNNNNNNNN.......AAA................",
    ".............NNN..............AAAAAAA.................",
    ".......................AAAAAAAAAAAAA..................",
    "....................AAAAAAAAAAAAAA....................",
    ".......................AAAAAAAA.......................",
    "......................................................",
]


def navegador():
    filas = ICONO_TACHYON
    l = Lienzo(len(filas[0]), len(filas))
    for y, fila in enumerate(filas):
        for x, c in enumerate(fila):
            l.punto(x, y, {".": GRIS, "N": NEGRO, "A": AZUL, "B": BLANCO}[c])
    return l


def documento():
    l = Lienzo(30, 22)
    l.rect(4, 1, 25, 20, BLANCO)
    l.marco(4, 1, 25, 20, NEGRO)
    l.rect(20, 1, 25, 6, GRIS)
    l.linea(20, 1, 25, 6, NEGRO)
    l.linea(20, 1, 20, 6, NEGRO)
    l.linea(20, 6, 25, 6, NEGRO)
    for y in (8, 11, 14, 17):
        l.linea(7, y, 22, y, AZUL)
    return l


def instalador():
    l = Lienzo(34, 22)
    l.rect(4, 11, 29, 20, AZUL)
    l.marco(4, 11, 29, 20, NEGRO)
    l.linea(4, 11, 9, 7, NEGRO)
    l.linea(29, 11, 24, 7, NEGRO)
    l.rect(14, 0, 19, 7, BLANCO)
    l.marco(14, 0, 19, 7, NEGRO)
    for i in range(6):
        l.linea(11 + i, 8 + i, 22 - i, 8 + i, BLANCO)
    l.linea(10, 8, 16, 14, NEGRO)
    l.linea(23, 8, 17, 14, NEGRO)
    return l


def texto_bcpl(s):
    b = s.encode("latin-1") + b"\0"
    return struct.pack(">I", len(b)) + b


def info(lienzo, tipo, herramienta=None, tooltypes=None, pila=0, ventana=(60, 40, 360, 140)):
    """ventana: x, y, ancho y alto de la ventana de un cajón al abrirse"""
    w, h = lienzo.ancho, lienzo.alto
    gadget = struct.pack(">IhhhhHHHIIIIIHI", 0, 0, 0, w, h + 1, 0x0004, 0x0003, 0x0001,
                         1, 0, 0, 0, 0, 0, 1)
    cajonero = tipo in (WBDISK, WBDRAWER)
    disk = struct.pack(">HH", 0xE310, 1) + gadget + struct.pack(
        ">BBIIIIIII", tipo, 0, 1 if herramienta else 0, 1 if tooltypes else 0, SIN_SITIO, SIN_SITIO,
        1 if cajonero else 0, 0, pila)
    r = disk
    if cajonero:
        # NewWindow (48) + CurrentX/Y del cajón abierto
        r += struct.pack(">hhhhbbIIIIIIIhhHHH", *ventana, -1, -1, 0, 0, 0, 0, 0, 0, 0,
                         90, 40, 0xFFFF, 0xFFFF, 1) + struct.pack(">ii", 0, 0)
    r += struct.pack(">hhhhhIBBI", 0, 0, w, h, 2, 1, 3, 0, 0) + lienzo.planos()
    if herramienta:
        r += texto_bcpl(herramienta)
    if tooltypes:
        r += struct.pack(">I", (len(tooltypes) + 1) * 4)
        for t in tooltypes:
            r += texto_bcpl(t)
    if cajonero:
        r += struct.pack(">IH", 0, 0)       # DrawerData de 2.x: dd_Flags y dd_ViewModes (por iconos)
    return r


def main():
    dest = Path(sys.argv[1] if len(sys.argv) > 1 else "build/paquete")
    (dest / "Tachyon").mkdir(parents=True, exist_ok=True)
    (dest / "Tachyon.info").write_bytes(info(cajon(), WBDRAWER))
    (dest / "Tachyon" / "Tachyon.info").write_bytes(info(navegador(), WBTOOL, pila=65536))
    (dest / "Tachyon" / "LEEME.info").write_bytes(info(documento(), WBPROJECT, herramienta="SYS:Utilities/MultiView"))
    (dest / "Tachyon" / "Instalar.info").write_bytes(
        info(instalador(), WBPROJECT, herramienta="Installer",
             tooltypes=["APPNAME=Tachyon", "MINUSER=AVERAGE", "DEFUSER=AVERAGE"]))


if __name__ == "__main__":
    main()
