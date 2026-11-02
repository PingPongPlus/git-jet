"""Render complete three-jet launch/landing loops and a scene contact sheet."""

from pathlib import Path

from PIL import Image, ImageDraw

from git_jet.calendar import Calendar
from git_jet.export import Options, render_assets
from git_jet.render import Renderer


def main():
    root = Path(__file__).resolve().parents[1]
    calendar = Calendar.read(root / "examples/demo/calendar.json")
    for carrier in ("lincoln", "classic"):
        output = root / "out/runway-preview" / carrier
        report = render_assets(
            calendar,
            output,
            Options(),
            jets=3,
            carrier=carrier,
            seed="git-jet-loop",
            source="demo",
        )
        renderer = Renderer(
            calendar, fps=report["fps"], jets=3, carrier=carrier, seed=report["seed"]
        )
        first, last = renderer.flights[0], renderer.flights[-1]
        scenes = (
            ("Queued", 0),
            ("First takeoff", first.launch_end),
            ("All launched", last.launch_end),
            ("First touchdown", first.touchdown),
            ("First parked", first.landed),
            ("All parked", renderer.flight.landed),
        )
        sheet = Image.new("RGB", (1440, 640), "#0d1117")
        for index, (label, frame) in enumerate(scenes):
            panel = Image.new("RGBA", (480, 320), "#0d1117")
            panel.alpha_composite(renderer.frame(frame))
            ImageDraw.Draw(panel).text(
                (8, 8), f"{label} — {frame / report['fps']:.1f}s", fill="white"
            )
            sheet.paste(panel.convert("RGB"), ((index % 3) * 480, (index // 3) * 320))
        sheet.save(output / "runway-contact-sheet.png")
        print(f"{carrier}: {report['duration_seconds']}s, {report['gif_bytes']} bytes, {output}")


if __name__ == "__main__":
    main()
