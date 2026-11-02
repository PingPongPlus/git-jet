import importlib.util
from pathlib import Path

import pytest
from PIL import Image

from git_jet import art
from git_jet.cli import main
from git_jet.demo import demo_calendar
from git_jet.export import indexed, palette
from git_jet.flight import HEIGHT, WIDTH
from git_jet.render import Renderer
from git_jet.water import POSITION, water_sprite


def test_water_moves_loops_and_keeps_clear_space_around_the_surface():
    first = water_sprite(0)
    assert first.tobytes() == water_sprite(1).tobytes() == water_sprite(-1).tobytes()
    assert len({water_sprite(i / 20).tobytes() for i in range(20)}) == 20
    for index in range(100):
        surface = water_sprite(index / 100)
        assert set(surface.getchannel("A").tobytes()) == {0, 255}
        left, top, right, bottom = surface.getbbox()
        assert 0 < left < right < surface.width
        assert 0 < top < bottom < surface.height
        assert bottom + POSITION[1] < 230  # the calendar begins at y=237
        assert surface.getchannel("A").histogram()[0] > surface.width * surface.height / 2


def test_every_water_frame_survives_the_shared_gif_palette_exactly():
    mapping, rgb = palette()
    for index in range(100):
        frame = Image.new("RGBA", (WIDTH, HEIGHT))
        frame.alpha_composite(water_sprite(index / 100), POSITION)
        assert indexed(frame, mapping, rgb, 1).convert("RGBA").tobytes() == frame.tobytes()


@pytest.mark.parametrize(
    "carrier,study",
    (
        ("classic", "sprites.py"),
        ("lincoln", "lincoln_redline.py"),
    ),
)
def test_original_water_recreates_the_approved_carrier_frames(carrier, study):
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("original_study", root / "artwork/drafts" / study)
    original = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(original)
    for phase in (0, 0.13, 0.25, 0.5, 0.91):
        current = water_sprite(phase, water="original", carrier=carrier).crop((40, 0, 390, 190))
        current.alpha_composite(art.carrier_sprite(phase, carrier=carrier))
        reference = original.carrier_sprite(phase)
        if carrier == "classic":
            x, y = art.project(*art.carrier_radar_origin(carrier))
            radar = (x - 7, y - 27, x + 9, y - 12)
            reference.paste(current.crop(radar), radar[:2])
        assert current.tobytes() == reference.tobytes()


@pytest.mark.parametrize("water", ("unknown", None, [], 1))
def test_invalid_water_is_rejected(water):
    with pytest.raises(ValueError, match="water"):
        Renderer(demo_calendar(), water=water)


def test_cli_rejects_unknown_water_before_collecting(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("invalid water must not start collection")

    monkeypatch.setattr("git_jet.cli.GitHubClient.collect", forbidden)
    with pytest.raises(SystemExit) as error:
        main(["render", "--username", "octocat", "--water", "unknown"])
    assert error.value.code == 2
