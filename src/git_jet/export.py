"""Stream a shared-palette GIF; audit decoded frames before replacing good assets."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from array import array
from dataclasses import dataclass
from pathlib import Path

from PIL import GifImagePlugin, Image, ImageChops

from . import art
from .flight import HEIGHT, WIDTH
from .render import Renderer

ASSETS = ("git-jet.gif", "git-jet.png", "report.json", "calendar.json")
MAX_BYTES = 25_000_000


@dataclass(frozen=True)
class Options:
    scale: int = 2
    fps: int = 20

    def __post_init__(self):
        if type(self.scale) is not int or not 1 <= self.scale <= 4:
            raise ValueError("scale must be an integer in 1..4")
        if type(self.fps) is not int or self.fps not in (5, 10, 20, 25):
            raise ValueError("fps must be 5, 10, 20 or 25")


def palette():
    samples = [
        art.carrier_sprite(),
        *(art.commit_tile(i) for i in range(5)),
        *(art.explosion_sprite(i / 10) for i in range(10)),
        *(art.jet_sprite(0, thrust, bank) for thrust in range(3) for bank in (-1, 0, 1)),
    ]
    colors = sorted({color for sample in samples for _, color in sample.getcolors(256) if color[3]})
    if len(colors) > 255 or any(color[3] != 255 for color in colors):
        raise ValueError("artwork must fit 255 opaque colors plus transparency")
    entries = [(0, 0, 0, 0), *colors]
    mapping = {
        int.from_bytes(bytes(color), sys.byteorder): index for index, color in enumerate(entries)
    }
    rgb = [v for color in entries for v in color[:3]]
    return mapping, rgb + [0] * (768 - len(rgb))


def indexed(frame, mapping, rgb, scale):
    pixels = array("I", frame.tobytes())
    image = Image.frombytes("P", frame.size, bytes(mapping[p] for p in pixels))
    image.putpalette(rgb)
    image.info["transparency"] = 0
    if scale != 1:
        image = image.resize((WIDTH * scale, HEIGHT * scale), Image.Resampling.NEAREST)
    return image


def verify(path: Path, renderer: Renderer, options: Options):
    with Image.open(path) as gif:
        if gif.n_frames != renderer.frame_count or gif.info.get("loop") != 0:
            raise ValueError("GIF frame count or looping metadata changed")
        for index in range(gif.n_frames):
            gif.seek(index)
            expected = renderer.frame(index).resize(gif.size, Image.Resampling.NEAREST)
            actual = gif.convert("RGBA")
            alpha = expected.getchannel("A")
            if ImageChops.difference(alpha, actual.getchannel("A")).getbbox():
                raise ValueError(f"GIF transparency changed at frame {index}")
            difference = ImageChops.difference(expected.convert("RGB"), actual.convert("RGB"))
            if ImageChops.multiply(difference, alpha.convert("RGB")).getbbox():
                raise ValueError(f"GIF colors changed at frame {index}")
            if gif.info["duration"] != 1000 // options.fps or gif.disposal_method != 2:
                raise ValueError("GIF timing or transparent cleanup changed")


def export(renderer: Renderer, output: Path, options: Options, *, source="live"):
    if renderer.flight.fps != options.fps:
        raise ValueError("renderer FPS differs from export FPS; rebuild the renderer")
    if renderer.frame_count * WIDTH * HEIGHT > 460_800_000:
        raise ValueError("animation exceeds the render budget; select fewer days")
    output.mkdir(parents=True, exist_ok=True)
    mapping, rgb = palette()
    with tempfile.TemporaryDirectory(prefix=".git-jet-", dir=output) as scratch:
        root = Path(scratch)
        gif = root / "git-jet.gif"
        with gif.open("wb") as stream:
            for index in range(renderer.frame_count):
                frame = indexed(renderer.frame(index), mapping, rgb, options.scale)
                if index == 0:
                    header, _ = GifImagePlugin.getheader(frame, info={"loop": 0, "transparency": 0})
                    for block in header:
                        stream.write(block)
                for block in GifImagePlugin.getdata(
                    frame, duration=1000 // options.fps, disposal=2, transparency=0
                ):
                    stream.write(block)
                if stream.tell() > MAX_BYTES:
                    raise ValueError("GIF exceeds 25 MB; reduce scale or the selected days")
            stream.write(b";")
        first = renderer.frame(0).resize(
            (WIDTH * options.scale, HEIGHT * options.scale), Image.Resampling.NEAREST
        )
        first.save(root / "git-jet.png")
        verify(gif, renderer, options)
        renderer.calendar.write(root / "calendar.json")
        report = {
            "username": renderer.calendar.username,
            "source": source,
            "scope": renderer.calendar.to_dict()["scope"],
            "start_date": renderer.calendar.days[0].date.isoformat(),
            "end_date": renderer.calendar.days[-1].date.isoformat(),
            "days": len(renderer.calendar.days),
            "total_commits": renderer.calendar.total,
            "active_days": len(renderer.flight.strikes),
            "attacks": len(renderer.flight.strikes),
            "attack_mode": "day-cell",
            "jets": renderer.jet_count,
            "seed": renderer.flight.seed,
            "flights": [
                {
                    "jet": flight.jet_id + 1,
                    "seed": flight.seed,
                    "attacks": len(flight.strikes),
                    "launch_frame": flight.launch_start,
                    "landed_frame": flight.landed,
                }
                for flight in renderer.flights
            ],
            "maneuvers": renderer.flight.maneuvers,
            "width": WIDTH * options.scale,
            "height": HEIGHT * options.scale,
            "frames": renderer.frame_count,
            "fps": options.fps,
            "duration_seconds": renderer.frame_count / options.fps,
            "transparent": True,
            "decoded_frames_match": True,
            "gif_bytes": gif.stat().st_size,
            "targets": [
                {
                    "date": s.cell.day.date.isoformat(),
                    "jet": s.jet_id + 1,
                    "commits": s.cell.day.commits,
                    "column": s.cell.column,
                    "row": s.cell.row,
                    "fire_frame": s.fire,
                    "hit_frame": s.hit,
                }
                for s in renderer.flight.strikes
            ],
        }
        (root / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        for name in ASSETS:
            os.replace(root / name, output / name)
    return report
