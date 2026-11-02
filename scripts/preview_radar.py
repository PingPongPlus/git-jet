"""Render the carrier-radar review GIF and an eight-angle detail sheet."""

from pathlib import Path

from PIL import Image, ImageDraw

from git_jet.art import CREAM, carrier_sprite, project


def main():
    output = Path(__file__).resolve().parents[1] / "artwork/drafts/output"
    output.mkdir(parents=True, exist_ok=True)
    x, y = project(185, 10, 60)
    region = (x - 12, y - 31, x + 12, y + 1)
    frames = []
    for frame in range(80):
        carrier = carrier_sprite(frame / 80, carrier="classic")
        image = Image.new("RGB", (960, 400), "#0d1117")
        full = carrier.resize((700, 380), Image.Resampling.NEAREST)
        image.paste(full, (0, 10), full)
        detail = carrier.crop(region).resize((192, 256), Image.Resampling.NEAREST)
        image.paste(detail, (736, 84), detail)
        draw = ImageDraw.Draw(image)
        draw.text((720, 35), "RADAR SPINNER", fill=CREAM)
        draw.text((720, 55), "Full turn every 4 seconds", fill=CREAM)
        draw.text((720, 360), "Mast detail - 8x pixel scale", fill=CREAM)
        frames.append(image)
    frames[0].save(
        output / "radar-spinner.gif",
        save_all=True,
        append_images=frames[1:],
        duration=50,
        loop=0,
        disposal=2,
    )
    sheet = Image.new("RGB", (640, 380), "#0d1117")
    for index in range(8):
        detail = (
            carrier_sprite(index / 8, carrier="classic")
            .crop(region)
            .resize((120, 160), Image.Resampling.NEAREST)
        )
        left, top = (index % 4) * 160 + 20, (index // 4) * 190 + 20
        sheet.paste(detail, (left, top), detail)
        ImageDraw.Draw(sheet).text((left, top - 16), f"{index * 45} degrees", fill=CREAM)
    sheet.save(output / "radar-spinner-sheet.png")


if __name__ == "__main__":
    main()
