"""アプリアイコンを作るスクリプト（ぬいぐるみをもとにしたマスコットの顔）。

使い方:  python tools/setup_assets.py   （Pillow が必要: pip install pillow）
icons/ に PNG アイコンを書き出す。
"""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent

BLUE = (62, 104, 176)
STRIPE = (111, 147, 207)
WHITE = (251, 250, 246)
FUR = (207, 201, 190)
FUR_EDGE = (189, 182, 170)
KNIT = (173, 166, 151)
KNIT_DARK = (148, 141, 126)
NOSE = (110, 65, 40)
INK = (43, 39, 36)
CHEEK = (236, 186, 180)
LEAF = (156, 196, 138)
STITCH = (95, 135, 201)


def draw_icon(size: int, maskable: bool) -> Image.Image:
    ss = 4                                   # 4倍で描いて縮小（なめらかにする）
    S = size * ss
    img = Image.new("RGB", (S, S), BLUE)
    d = ImageDraw.Draw(img)
    k = S / 512
    scale = 0.78 if maskable else 1.0        # maskable は周りが切られるので小さめに
    cx, cy = S / 2, S / 2 + 20 * k

    def P(x, y):
        return (cx + (x - 256) * k * scale, cy + (y - 256) * k * scale)

    def box(x0, y0, x1, y1):
        return [*P(x0, y0), *P(x1, y1)]

    # シャツ（ボーダー）
    shirt = box(96, 380, 416, 640)
    layer = Image.new("RGB", (S, S), WHITE)
    ld = ImageDraw.Draw(layer)
    for y in range(392, 640, 36):
        ld.rectangle(box(0, y, 512, y + 16), fill=STRIPE)
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle(shirt, radius=110 * k * scale, fill=255)
    img.paste(layer, (0, 0), mask)

    # 顔
    d.ellipse(box(106, 96, 406, 396), fill=FUR, outline=FUR_EDGE, width=int(6 * k * scale))
    # ニット帽
    d.chord(box(100, 60, 412, 330), start=180, end=360, fill=KNIT)
    d.rectangle(box(100, 190, 412, 196), fill=KNIT)
    d.arc(box(100, 150, 412, 250), start=190, end=350, fill=KNIT_DARK, width=int(22 * k * scale))
    d.ellipse(box(330, 96, 366, 132), fill=LEAF)
    # 帽子の刺しゅう「う〜」
    w = int(12 * k * scale)
    d.line([P(196, 104), P(226, 104)], fill=STITCH, width=w)
    d.line([P(180, 134), P(204, 124), P(226, 124), P(240, 136), P(238, 154), P(222, 170), P(202, 178)], fill=STITCH, width=w, joint="curve")
    import math
    wave = [P(254 + t, 142 - 7 * math.sin(t / 80 * 2 * math.pi * 1.5)) for t in range(0, 81, 2)]
    d.line(wave, fill=STITCH, width=w, joint="curve")
    # 目
    for x in (190, 322):
        d.ellipse(box(x - 13, 232, x + 13, 258), fill=INK)
    # ほっぺ
    for x in (160, 352):
        d.ellipse(box(x - 30, 286, x + 30, 310), fill=CHEEK)
    # 鼻
    d.ellipse(box(212, 262, 300, 338), fill=NOSE)
    d.ellipse(box(226, 274, 252, 290), fill=(160, 120, 100))

    return img.resize((size, size), Image.LANCZOS)


if __name__ == "__main__":
    icons = ROOT / "icons"
    icons.mkdir(exist_ok=True)
    draw_icon(192, False).save(icons / "icon-192.png")
    draw_icon(512, False).save(icons / "icon-512.png")
    draw_icon(512, True).save(icons / "icon-maskable-512.png")
    draw_icon(180, False).save(icons / "apple-touch-icon.png")
    print("icons/ にアイコンを書き出しました")
