"""Review sheets for the fresh draft based on the annotated carrier reference."""

import importlib.util
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from git_jet.art import project
from git_jet.demo import demo_calendar
from git_jet.render import Renderer

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("redline_draft", ROOT / "lincoln_redline.py")
draft = importlib.util.module_from_spec(spec)
spec.loader.exec_module(draft)


def main():
    output = ROOT / "output"
    output.mkdir(parents=True, exist_ok=True)
    font = ImageFont.load_default(size=20)
    original = draft.carrier_sprite()
    original.save(output / "lincoln-redline-transparent.png")
    guides = original.copy()
    draw = ImageDraw.Draw(guides)
    outline = [project(*draft.reference_point(*p, 30)) for p in draft.REFERENCE_OUTLINE]
    lane = [project(*draft.reference_point(*p, 31)) for p in draft.REFERENCE_RUNWAY]
    draw.line([*outline, outline[0]], fill="#f94743", width=1)
    draw.line(lane[:2], fill="#36b649", width=1)
    draw.line(lane[2:], fill="#36b649", width=1)
    sheet = Image.new("RGB", (1440, 430), "#0d1117")
    for index, (label, image) in enumerate(
        (("NEW DRAWING", original), ("RED: SILHOUETTE   GREEN: RUNWAY", guides))
    ):
        scaled = image.resize((700, 380), Image.Resampling.NEAREST)
        sheet.paste(scaled, (index * 720 + 10, 45), scaled)
        ImageDraw.Draw(sheet).text((index * 720 + 24, 12), label, fill="#c9d1d9", font=font)
    sheet.save(output / "lincoln-redline-approval.png")
    renderer = Renderer(demo_calendar(), seed="git-jet-loop")
    scene = renderer.frame(0)
    scene.resize((1440, 960), Image.Resampling.NEAREST).save(output / "lincoln-redline-scene.png")
    frames = []
    for index in range(80):
        carrier = draft.carrier_sprite(index / 80).resize((1050, 570), Image.Resampling.NEAREST)
        frame = Image.new("RGB", (1080, 600), "#0d1117")
        frame.paste(carrier, (15, 30), carrier)
        ImageDraw.Draw(frame).text(
            (24, 8), "REDRAW - annotated silhouette and angled runway", fill="#c9d1d9", font=font
        )
        frames.append(frame)
    frames[0].save(
        output / "lincoln-redline-motion.gif",
        save_all=True,
        append_images=frames[1:],
        duration=50,
        loop=0,
        disposal=2,
    )


if __name__ == "__main__":
    main()
