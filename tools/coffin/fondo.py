"""Fondo de Dash: noche azul del Workbench, barras copper en el horizonte, rejilla y la D de cuadros con el cursor."""
import sys, math, random
from PIL import Image, ImageDraw, ImageFilter, ImageFont
W, H = int(sys.argv[2]), int(sys.argv[3])
img = Image.new("RGB", (W, H))
px = img.load()
top, mid = (6, 12, 34), (0, 52, 112)
hz = int(H * 0.62)
for y in range(H):
    if y < hz:
        t = (y / hz) ** 1.6
        c = tuple(int(top[i] + (mid[i] - top[i]) * t) for i in range(3))
    else:
        t = (y - hz) / (H - hz)
        c = tuple(int(mid[i] * (1 - t) * 0.35 + 4) for i in range(3))
    for x in range(W):
        px[x, y] = c
d = ImageDraw.Draw(img, "RGBA")
random.seed(7)
for _ in range(int(W * H / 9000)):          # estrellas
    x, y = random.randrange(W), random.randrange(int(hz * 0.9))
    a = random.randint(60, 200)
    d.point((x, y), fill=(255, 255, 255, a))
# barras copper en el horizonte
bars = [(255, 136, 0), (255, 200, 60), (255, 255, 255), (90, 170, 255), (0, 85, 170)]
bh = max(2, H // 180)
for i, col in enumerate(bars):
    y0 = hz - (len(bars) - i) * bh * 2
    for k in range(bh * 2):
        f = 1 - abs(k - bh) / bh
        d.line([(0, y0 + k), (W, y0 + k)], fill=col + (int(170 * f),))
# suelo con rejilla en perspectiva
vx = W * 0.5
for i in range(-14, 15):
    d.line([(vx + i * W / 60, hz + bh), (vx + i * W / 5, H)], fill=(255, 136, 0, 90), width=max(1, H // 700))
y, step = hz + bh * 2, 4.0
while y < H:
    d.line([(0, y), (W, y)], fill=(255, 136, 0, 80), width=max(1, H // 700))
    step *= 1.3; y += step
# la D del logo (rejilla de 16) con brillo
cell = H // 56
lx, ly = int(W * 0.5 - 8 * cell), int(hz - 16 * cell - len(bars) * bh * 2 - H * 0.06)
logo = Image.new("RGBA", (16 * cell, 16 * cell), (0, 0, 0, 0))
ld = ImageDraw.Draw(logo)
ld.rounded_rectangle([0, 0, 16 * cell - 1, 16 * cell - 1], radius=int(2.5 * cell), fill=(0, 85, 170, 255))
for (x, y, w, h) in [(3, 4, 5, 1), (3, 5, 2, 6), (7, 5, 2, 6), (3, 11, 5, 1)]:
    ld.rectangle([x * cell, y * cell, (x + w) * cell - 1, (y + h) * cell - 1], fill=(255, 136, 0, 255))
ld.rectangle([10 * cell, 11 * cell, 13 * cell - 1, 12 * cell - 1], fill=(255, 255, 255, 255))
glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
glow.paste((255, 136, 0, 140), (lx - cell, ly - cell, lx + 17 * cell, ly + 17 * cell))
glow = glow.filter(ImageFilter.GaussianBlur(cell * 2))
img.paste(glow, (0, 0), glow)
img.paste(logo, (lx, ly), logo)
# reflejo
refl = logo.transpose(Image.FLIP_TOP_BOTTOM).resize((16 * cell, 6 * cell))
a = refl.split()[3].point(lambda v: v * 0.22)
refl.putalpha(a)
img.paste(refl, (lx, hz + bh * 3), refl)
try:
    font = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSansMono-Bold.ttf", cell * 2)
    small = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSansMono.ttf", int(cell * 0.75))
except OSError:
    font = small = ImageFont.load_default()
t = "D.A.S.H."
tw = d.textlength(t, font=font)
d.text((lx + 8 * cell - tw / 2, ly - cell * 3.2), t, font=font, fill=(255, 255, 255, 230))
s = "Development Amiga Synthesis Hub"
sw = d.textlength(s, font=small)
d.text((lx + 8 * cell - sw / 2, ly - cell * 1.1), s, font=small, fill=(150, 200, 255, 210))
img.save(sys.argv[1])
