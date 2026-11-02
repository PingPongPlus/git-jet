"""Before/after review of the island wall details and radar-pixel cleanup."""

import importlib.util
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("carrier_detail", ROOT / "lincoln_redline.py")
draft = importlib.util.module_from_spec(spec)
spec.loader.exec_module(draft)


def main():
    output = ROOT / "output"
    output.mkdir(parents=True, exist_ok=True)
    before = Image.open(output / "lincoln-redline-before-detail.png").convert("RGBA")
    after = draft.carrier_sprite()
    font = ImageFont.load_default(size=22)
    region = (176, 0, 239, 77)
    sheet = Image.new("RGB", (820, 530), "#0d1117")
    for index, (label, image) in enumerate((("BEFORE", before), ("REVISED ISLAND", after))):
        detail = image.crop(region).resize((378, 462), Image.Resampling.NEAREST)
        left = 20 + index * 410
        sheet.paste(detail, (left, 50), detail)
        ImageDraw.Draw(sheet).text((left, 13), label, fill="#c9d1d9", font=font)
    sheet.save(output / "lincoln-island-detail-comparison.png")
    full = after.resize((1400, 760), Image.Resampling.NEAREST)
    image = Image.new("RGB", full.size, "#0d1117")
    image.paste(full, (0, 0), full)
    image.save(output / "lincoln-island-detail-revised.png")
    after.save(output / "lincoln-island-detail-transparent.png")
    frames = []
    for index in range(80):
        carrier = draft.carrier_sprite(index / 80).resize((1050, 570), Image.Resampling.NEAREST)
        frame = Image.new("RGB", (1080, 600), "#0d1117")
        frame.paste(carrier, (15, 30), carrier)
        ImageDraw.Draw(frame).text(
            (24, 8), "Revised island details and connected radar mast", fill="#c9d1d9", font=font
        )
        frames.append(frame)
    frames[0].save(
        output / "lincoln-island-detail-motion.gif",
        save_all=True,
        append_images=frames[1:],
        duration=50,
        loop=0,
        disposal=2,
    )


if __name__ == "__main__":
    main()
