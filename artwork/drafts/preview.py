"""Generate first-review art sheets and an offline motion study."""

import argparse
import math
from pathlib import Path

from PIL import GifImagePlugin, Image, ImageDraw, ImageFont
from sprites import (
    CREAM,
    GOLD,
    INK,
    LIGHT,
    WAVE,
    carrier_sprite,
    commit_tile,
    explosion_sprite,
    jet_sprite,
    project,
)

WIDTH, HEIGHT = 480, 320
SCALE = 2
HERE = Path(__file__).resolve().parent


def on_background(image, color):
    background = Image.new("RGBA", image.size, color)
    background.alpha_composite(image)
    return background.convert("RGB")


def carrier_sheet(output):
    sheet = Image.new("RGB", (1400, 440), "#0d1117")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=20)
    sprite = carrier_sprite().resize((700, 380), Image.Resampling.NEAREST)
    for x, color, label in ((0, "#0d1117", "DARK README"), (700, "#f4f6f8", "LIGHT README")):
        draw.rectangle((x, 0, x + 699, 439), fill=color)
        draw.text(
            (x + 24, 18),
            f"GIT JET / CARRIER STUDY / {label}",
            fill=LIGHT if x == 0 else INK,
            font=font,
        )
        sheet.paste(on_background(sprite, color), (x, 50))
    sheet.save(output / "carrier-approval.png")
    carrier_sprite().save(output / "carrier-transparent.png")


def jet_sheet(output):
    sheet = Image.new("RGB", (960, 480), "#0d1117")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=16)
    draw.text((18, 12), "JET STUDY / 16 HEADINGS + BANKING + EXHAUST", fill=CREAM, font=font)
    for index in range(16):
        x, y = (index % 8) * 120, 40 + (index // 8) * 150
        sprite = jet_sprite(index * 22.5, 1).resize((111, 111), Image.Resampling.NEAREST)
        sheet.paste(on_background(sprite, "#0d1117"), (x + 4, y))
        draw.text((x + 10, y + 114), f"{index * 22.5:g} deg", fill=LIGHT, font=font)
    for index, (heading, thrust, bank, label) in enumerate(
        (
            (90, 0, 0, "Parked / glide"),
            (90, 1, -1, "Bank left"),
            (90, 2, 1, "Bank right"),
            (90, 2, 0, "Afterburner"),
        )
    ):
        x = 20 + index * 235
        sprite = jet_sprite(heading, thrust, bank).resize((111, 111), Image.Resampling.NEAREST)
        sheet.paste(on_background(sprite, "#0d1117"), (x, 345))
        draw.text((x + 98, 399), label, fill=LIGHT, font=font)
    sheet.save(output / "jet-approval.png")


def effects_sheet(output):
    sheet = Image.new("RGB", (960, 320), "#0d1117")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=18)
    draw.text((20, 15), "COMMIT GRID / ONE ATTACK CLEARS ONE DAY CELL", fill=CREAM, font=font)
    for index, level in enumerate(range(5)):
        tile = commit_tile(level).resize((56, 56), Image.Resampling.NEAREST)
        sheet.paste(on_background(tile, "#0d1117"), (24 + index * 85, 54))
    draw.text((470, 70), "Transparent gaps / 4 activity levels", fill=LIGHT, font=font)
    draw.text(
        (20, 144), "IMPACT / CORE FLASH - PIXEL SHARDS - SMOKE - CLEAR", fill=CREAM, font=font
    )
    for index, age in enumerate((0, 0.12, 0.25, 0.4, 0.55, 0.7, 0.85, 1)):
        tile = explosion_sprite(age).resize((90, 90), Image.Resampling.NEAREST)
        sheet.paste(on_background(tile, "#0d1117"), (15 + index * 118, 180))
    draw.line((25, 298, 104, 298), fill=WAVE, width=2)
    draw.line((85, 298, 107, 298), fill=GOLD, width=2)
    draw.point((108, 298), fill=CREAM)
    draw.text(
        (130, 285), "Projectile: pale core + gold streak + short blue trail", fill=LIGHT, font=font
    )
    sheet.save(output / "effects-approval.png")


def scene(t):
    """Draft flight only: eight example cells, not fabricated live statistics."""
    t %= 1
    image = Image.new("RGBA", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)
    image.alpha_composite(carrier_sprite(t), (65, 12))
    # Full custom 53-week grid sits below the carrier, with no backing panel.
    targets = ((9, 1), (14, 5), (20, 2), (27, 4), (32, 0), (37, 5), (44, 3), (49, 1))
    attack_start, attack_end = 0.28, 0.75
    for col in range(53):
        for row in range(7):
            level = 0
            destroyed = False
            if (col, row) in targets:
                index = targets.index((col, row))
                level = index % 4 + 1
                destroyed = t > attack_start + (index + 0.7) / len(targets) * (
                    attack_end - attack_start
                )
            image.alpha_composite(commit_tile(level, destroyed), (28 + col * 8, 237 + row * 8))
    # Catapult launch follows the runway towards the left-hand bow.
    sx, sy = project(224, 33, 28)
    launch_start = (65 + sx, 12 + sy)
    bx, by = project(-8, 32, 28)
    launch_end = (65 + bx, 12 + by)
    if t < 0.08:
        jet_x, jet_y = launch_start
        heading, bank, thrust = 252, 0, 0
    elif t < 0.20:
        p = ((t - 0.08) / 0.12) ** 1.6
        jet_x = launch_start[0] + (launch_end[0] - launch_start[0]) * p
        jet_y = launch_start[1] + (launch_end[1] - launch_start[1]) * p
        heading, bank, thrust = 252, 0, 2
    elif t < attack_start:
        p = (t - 0.20) / (attack_start - 0.20)
        jet_x = launch_end[0] - 26 * math.sin(math.pi * p)
        jet_y = launch_end[1] + p * (210 - launch_end[1])
        heading, bank, thrust = 180 - 90 * p, -1, 1
    elif t < attack_end:
        p = (t - attack_start) / (attack_end - attack_start)
        jet_x = 55 + p * 380
        jet_y = 211 + 9 * math.sin(p * math.tau)
        heading, bank, thrust = 90, 0, 1
    else:
        p = (t - attack_end) / (1 - attack_end)
        jet_x = 435 + (launch_start[0] - 435) * p + 25 * math.sin(math.pi * p)
        jet_y = 211 + (launch_start[1] - 211) * p
        heading, bank, thrust = 330 - p * 78, -1, 0
    # The production planner will aim each attack at the selected real day cell.
    for index, (col, row) in enumerate(targets):
        hit = attack_start + (index + 0.7) / len(targets) * (attack_end - attack_start)
        tx, ty = 31 + col * 8, 240 + row * 8
        if hit - 0.035 <= t < hit:
            p = (t - (hit - 0.035)) / 0.035
            origin_x = 55 + (hit - attack_start) / (attack_end - attack_start) * 380
            px, py = origin_x + (tx - origin_x) * p, 211 + (ty - 211) * p
            dx, dy = tx - origin_x, ty - 211
            length = max(1, math.hypot(dx, dy))
            draw.line(
                (round(px - dx / length * 6), round(py - dy / length * 6), round(px), round(py)),
                fill=GOLD,
            )
            draw.point((round(px), round(py)), fill=CREAM)
        age = (t - hit) / 0.045
        if 0 <= age < 1:
            image.alpha_composite(explosion_sprite(age), (tx - 12, ty - 12))
    heading = round(heading / 22.5) * 22.5
    image.alpha_composite(jet_sprite(heading, thrust, bank), (round(jet_x) - 18, round(jet_y) - 18))
    return image.resize((WIDTH * SCALE, HEIGHT * SCALE), Image.Resampling.NEAREST)


def write_gif(output):
    frames = [scene(index / 160) for index in range(160)]
    assert scene(0).tobytes() == scene(1).tobytes()
    colors = sorted({color for frame in frames for _, color in frame.getcolors(256) if color[3]})
    assert len(colors) < 256 and all(color[3] == 255 for color in colors)
    mapping = {color: i + 1 for i, color in enumerate(colors)}
    palette = [0, 0, 0] + [v for color in colors for v in color[:3]]
    palette += [0] * (768 - len(palette))
    path = output / "motion-study.gif"
    with path.open("wb") as stream:
        for index, frame in enumerate(frames):
            indexed = Image.new("P", frame.size)
            indexed.putpalette(palette)
            indexed.putdata(
                [mapping[color] if color[3] else 0 for color in frame.get_flattened_data()]
            )
            if index == 0:
                header, _ = GifImagePlugin.getheader(indexed, info={"loop": 0, "transparency": 0})
                for block in header:
                    stream.write(block)
            for block in GifImagePlugin.getdata(indexed, duration=100, disposal=2, transparency=0):
                stream.write(block)
        stream.write(b";")
    with Image.open(path) as gif:
        assert gif.n_frames == 160
        for index, frame in enumerate(frames):
            gif.seek(index)
            actual = gif.convert("RGBA")
            assert actual.getchannel("A").tobytes() == frame.getchannel("A").tobytes()
    frames[0].save(output / "scene-transparent.png")
    on_background(frames[50], "#0d1117").save(output / "scene-preview.png")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=HERE / "output")
    parser.add_argument("--still-only", action="store_true")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    carrier_sheet(args.output_dir)
    jet_sheet(args.output_dir)
    effects_sheet(args.output_dir)
    if not args.still_only:
        write_gif(args.output_dir)
    print(args.output_dir)


if __name__ == "__main__":
    main()
