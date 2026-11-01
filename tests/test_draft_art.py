import importlib.util
from pathlib import Path

from PIL import ImageChops

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("draft_sprites", ROOT / "artwork/drafts/sprites.py")
art = importlib.util.module_from_spec(spec)
spec.loader.exec_module(art)


def test_carrier_waves_loop_and_background_is_binary_transparent():
    first = art.carrier_sprite(0)
    assert first.tobytes() == art.carrier_sprite(1).tobytes()
    assert first.tobytes() != art.carrier_sprite(0.25).tobytes()
    assert first.getchannel("A").histogram()[0] > first.width * first.height / 2
    assert set(first.getchannel("A").tobytes()) == {0, 255}
    bounds = first.getbbox()
    assert bounds[0] > 0 and bounds[1] > 0 and bounds[2] < first.width and bounds[3] < first.height


def test_directional_sprites_and_banking_have_no_soft_edges():
    frames = [art.jet_sprite(index * 22.5, 2) for index in range(16)]
    assert len({frame.tobytes() for frame in frames}) == 16
    assert all(set(frame.getchannel("A").tobytes()) == {0, 255} for frame in frames)
    assert ImageChops.difference(art.jet_sprite(90, 1, -1), art.jet_sprite(90, 1, 1)).getbbox(
        alpha_only=False
    )


def test_empty_day_and_cleared_cell_are_transparent_inside_and_blast_clears():
    assert art.commit_tile(0).getpixel((3, 3))[3] == 0
    assert art.commit_tile(4, destroyed=True).tobytes() == art.commit_tile(0).tobytes()
    assert art.commit_tile(4).getpixel((3, 3))[3] == 255
    assert art.explosion_sprite(1).getbbox() is None
