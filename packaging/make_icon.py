"""生成 namecraft 应用图标（多尺寸 ICO + 256px PNG 预览）。

图标与界面左上角一致：蓝紫渐变圆角方块 + 白色 nc 字标；16/20/24px 改用大写 N 保证小尺寸可读。

用法（仓库根目录）：
    .venv/Scripts/python.exe packaging/make_icon.py [--preview 预览输出.png]
"""

from __future__ import annotations

import argparse
import io
import struct
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
FONT_BOLD = Path("C:/Windows/Fonts/segoeuib.ttf")
SIZES = (16, 20, 24, 32, 40, 48, 64, 128, 256)
MASTER = 1024

C1 = (63, 110, 247)  # 左上蓝
C2 = (139, 85, 247)  # 右下紫


def _gradient(size: int) -> Image.Image:
    img = Image.new("RGB", (size, size))
    px = img.load()
    span = 2 * (size - 1)
    for y in range(size):
        for x in range(size):
            t = (x + y) / span
            px[x, y] = (
                round(C1[0] + (C2[0] - C1[0]) * t),
                round(C1[1] + (C2[1] - C1[1]) * t),
                round(C1[2] + (C2[2] - C1[2]) * t),
            )
    return img


GRADIENT = _gradient(MASTER)


def _tile(size: int) -> Image.Image:
    img = GRADIENT.resize((size, size), Image.Resampling.LANCZOS).convert("RGBA")

    # 左上柔光与底部压暗，避免纯平渐变
    light = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(light)
    d.ellipse(
        (-0.35 * size, -0.45 * size, 1.05 * size, 0.68 * size),
        fill=(255, 255, 255, 30),
    )
    light = light.filter(ImageFilter.GaussianBlur(size * 0.07))
    img = Image.alpha_composite(img, light)

    shade = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(shade)
    d.ellipse(
        (-0.2 * size, 0.62 * size, 1.2 * size, 1.35 * size),
        fill=(17, 20, 60, 46),
    )
    shade = shade.filter(ImageFilter.GaussianBlur(size * 0.08))
    img = Image.alpha_composite(img, shade)

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, size - 1, size - 1), radius=round(size * 0.225), fill=255
    )
    img.putalpha(mask)

    # 内侧高光边
    edge = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(edge).rounded_rectangle(
        (size * 0.008, size * 0.008, size - size * 0.008, size - size * 0.008),
        radius=round(size * 0.215),
        outline=(255, 255, 255, 46),
        width=max(1, round(size * 0.007)),
    )
    img = Image.alpha_composite(img, edge)
    img.putalpha(mask)
    return img


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_BOLD), size)


def render(size: int, scale: int = 4) -> Image.Image:
    """按目标尺寸渲染；小尺寸先放大画再缩回，保证笔画抗锯齿。"""
    n = size * scale
    img = _tile(n)
    draw = ImageDraw.Draw(img)

    if size <= 24:
        text, ratio = "N", 0.62
    elif size <= 32:
        text, ratio = "nc", 0.50
    else:
        text, ratio = "nc", 0.52

    font = _font(round(n * ratio))
    box = draw.textbbox((0, 0), text, font=font)
    x = (n - (box[2] - box[0])) / 2 - box[0]
    y = (n - (box[3] - box[1])) / 2 - box[1]
    if text == "nc":
        y -= n * 0.012
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))

    if scale > 1:
        img = img.resize((size, size), Image.Resampling.LANCZOS)
    return img


def write_ico(path: Path, images: list[tuple[int, Image.Image]]) -> None:
    """写 PNG 帧 ICO（Vista+ 支持各尺寸 PNG 条目）。"""
    blobs = []
    for _, im in images:
        buf = io.BytesIO()
        im.save(buf, format="PNG", optimize=True)
        blobs.append(buf.getvalue())

    header = struct.pack("<HHH", 0, 1, len(images))
    offset = 6 + 16 * len(images)
    entries = b""
    for (size, _), blob in zip(images, blobs):
        w = 0 if size >= 256 else size
        entries += struct.pack("<BBBBHHII", w, w, 0, 0, 1, 32, len(blob), offset)
        offset += len(blob)
    path.write_bytes(header + entries + b"".join(blobs))


def contact_sheet(images: list[tuple[int, Image.Image]]) -> Image.Image:
    pad, gap = 18, 16
    cell = 256
    width = pad * 2 + cell * 4 + gap * 3
    height = pad * 2 + cell * 2 + gap + 30
    sheet = Image.new("RGB", (width, height), (15, 17, 21))
    d = ImageDraw.Draw(sheet)
    label = _font(15)

    for row, bg in enumerate(((15, 17, 21), (242, 243, 246))):
        if row:
            d.rectangle((0, pad + cell + gap // 2, width, height), fill=bg)
        top = pad if row == 0 else pad + cell + gap + 30
        for i, (size, im) in enumerate(images):
            if i >= 8:
                break
            x = pad + i * (cell + gap)
            shown = im.resize((cell, cell), Image.Resampling.NEAREST)
            if row == 0:
                sheet.paste(shown, (x, top), shown)
                d.text((x, top + cell + 8), f"{size}px", font=label, fill=(200, 205, 215))
            else:
                sheet.paste(shown, (x, top), shown)
    return sheet


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", type=Path, help="输出对比预览 PNG")
    args = parser.parse_args()

    images = [(s, render(s)) for s in SIZES]
    write_ico(HERE / "namecraft.ico", images)
    images[-1][1].save(HERE / "namecraft-256.png", optimize=True)
    if args.preview:
        contact_sheet(images).save(args.preview, optimize=True)
    print("wrote", HERE / "namecraft.ico", "and", HERE / "namecraft-256.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
