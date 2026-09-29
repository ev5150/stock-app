"""アプリアイコンを作るスクリプト。

使い方:  python tools/setup_assets.py   （Pillow が必要: pip install pillow）
icons/ に PNG アイコンを書き出す。
"""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent


def draw_icon(size: int, maskable: bool) -> Image.Image:
    bg = (47, 107, 79)       # 深い緑
    paper = (243, 245, 241)
    warn = (240, 183, 90)
    img = Image.new("RGB", (size, size), bg)
    d = ImageDraw.Draw(img)
    s = size / 512
    pad = 0.18 if maskable else 0.12
    # 棚に並んだ3つの瓶。右端だけ残りわずか。
    x0, x1 = size * pad, size * (1 - pad)
    shelf_y = size * 0.72
    w = (x1 - x0) / 3
    for i, level in enumerate([0.95, 0.95, 0.25]):
        left = x0 + i * w + 10 * s
        right = x0 + (i + 1) * w - 10 * s
        top = size * 0.30
        d.rounded_rectangle([left, top, right, shelf_y], radius=18 * s, outline=paper, width=int(10 * s))
        fill_top = shelf_y - (shelf_y - top - 14 * s) * level
        color = warn if level < 0.5 else paper
        d.rounded_rectangle([left + 14 * s, fill_top, right - 14 * s, shelf_y - 14 * s], radius=8 * s, fill=color)
        d.rectangle([left + 16 * s, top - 26 * s, right - 16 * s, top - 4 * s], fill=paper)
    d.rounded_rectangle([x0 - 6 * s, shelf_y + 8 * s, x1 + 6 * s, shelf_y + 26 * s], radius=6 * s, fill=paper)
    return img


if __name__ == "__main__":
    icons = ROOT / "icons"
    icons.mkdir(exist_ok=True)
    draw_icon(192, False).save(icons / "icon-192.png")
    draw_icon(512, False).save(icons / "icon-512.png")
    draw_icon(512, True).save(icons / "icon-maskable-512.png")
    draw_icon(180, False).save(icons / "apple-touch-icon.png")
    print("icons/ にアイコンを書き出しました")
