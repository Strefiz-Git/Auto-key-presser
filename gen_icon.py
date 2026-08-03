import math
import os

from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
SIZE = 256
TOP = (59, 130, 246)
BOT = (30, 58, 138)
GOLD = (251, 191, 36)


def font(paths, px):
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, px)
    return ImageFont.load_default()


def arrowhead(d, center, angle, r, color, tip, half, w=4):
    cx, cy = center
    p = (cx + r * math.cos(angle), cy + r * math.sin(angle))
    dirc = (-math.sin(angle), -math.cos(angle))
    perp = (math.cos(angle), -math.sin(angle))
    pts = [
        (p[0] + dirc[0] * tip, p[1] + dirc[1] * tip),
        (p[0] - dirc[0] * half + perp[0] * w, p[1] - dirc[1] * half + perp[1] * w),
        (p[0] - dirc[0] * half - perp[0] * w, p[1] - dirc[1] * half - perp[1] * w),
    ]
    d.polygon(pts, fill=color)


img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

for y in range(SIZE):
    t = y / SIZE
    c = tuple(int(TOP[i] + (BOT[i] - TOP[i]) * t) for i in range(3))
    d.line([(0, y), (SIZE, y)], fill=c + (255,))

mask = Image.new("L", (SIZE, SIZE), 0)
dm = ImageDraw.Draw(mask)
dm.rounded_rectangle([16, 16, SIZE - 16, SIZE - 16], radius=48, fill=255)
img = Image.composite(img, Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0)), mask)
d = ImageDraw.Draw(img)

d.rounded_rectangle([16, 16, SIZE - 16, SIZE - 16], radius=48,
                    outline=(147, 197, 253, 255), width=6)

cx, cy = SIZE / 2, SIZE / 2
r = 92
d.arc([cx - r, cy - r, cx + r, cy + r], start=210, end=330, fill=GOLD + (255,), width=12)
d.arc([cx - r, cy - r, cx + r, cy + r], start=30, end=150, fill=GOLD + (255,), width=12)

arrowhead(d, (cx, cy), math.radians(150), r, GOLD + (255,), 18, 10)
arrowhead(d, (cx, cy), math.radians(330), r, GOLD + (255,), 18, 10)
arrowhead(d, (cx, cy), math.radians(30), r, GOLD + (255,), 18, 10)
arrowhead(d, (cx, cy), math.radians(210), r, GOLD + (255,), 18, 10)

key = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
kd = ImageDraw.Draw(key)
kd.rounded_rectangle([90, 96, 166, 172], radius=16, fill=(255, 255, 255, 255),
                     outline=(226, 232, 240, 255), width=4)
ft = font([r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\arialbd.ttf"], 66)
bbox = kd.textbbox((0, 0), "F", font=ft)
tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
tx = 128 - tw / 2 - bbox[0]
ty = 134 - th / 2 - bbox[1]
kd.text((tx, ty), "F", font=ft, fill=(30, 58, 138, 255))
img = Image.alpha_composite(img, key)

img.save(os.path.join(BASE, "icon.png"))
img.save(os.path.join(BASE, "icon.ico"), sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
print("icon.png / icon.ico gerados")
