"""Render a four-second water study and matching light/dark review images."""

import argparse
from pathlib import Path

from PIL import Image

from git_jet.art import CARRIERS, DEFAULT_CARRIER, carrier_sprite
from git_jet.export import indexed, palette
from git_jet.water import DEFAULT_WATER, POSITION, WATER_STYLES, water_sprite


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--carrier", choices=CARRIERS, default=DEFAULT_CARRIER)
    parser.add_argument("--water", choices=WATER_STYLES, default=DEFAULT_WATER)
    args = parser.parse_args()
    output = Path(__file__).resolve().parents[1] / "out/water-preview"
    output.mkdir(parents=True, exist_ok=True)
    mapping, rgb = palette()
    frames = []
    bow_frames = []
    for index in range(80):
        phase = index / 80
        scene = Image.new("RGBA", (480, 320))
        scene.alpha_composite(water_sprite(phase, water=args.water, carrier=args.carrier), POSITION)
        scene.alpha_composite(carrier_sprite(phase, carrier=args.carrier), (65, 12))
        frame = indexed(scene, mapping, rgb, 2).crop((0, 0, 960, 440))
        frames.append(frame)
        bow = frame.crop((45, 220, 425, 415)).resize((760, 390), Image.Resampling.NEAREST)
        bow.putpalette(rgb)
        bow_frames.append(bow)
    frames[0].save(
        output / f"{args.water}-{args.carrier}-motion-v4.gif",
        save_all=True,
        append_images=frames[1:],
        duration=50,
        loop=0,
        transparency=0,
        disposal=2,
        optimize=False,
    )
    review = Image.new("RGB", (960, 880))
    for row, color in enumerate(("#0d1117", "#ffffff")):
        background = Image.new("RGBA", (960, 440), color)
        background.alpha_composite(frames[0].convert("RGBA"))
        review.paste(background.convert("RGB"), (0, row * 440))
    review.save(output / f"{args.water}-{args.carrier}-backgrounds-v4.png")
    bow_frames[0].save(
        output / f"{args.water}-{args.carrier}-bow-v4.gif",
        save_all=True,
        append_images=bow_frames[1:],
        duration=50,
        loop=0,
        transparency=0,
        disposal=2,
        optimize=False,
    )
    print(output)


if __name__ == "__main__":
    main()
