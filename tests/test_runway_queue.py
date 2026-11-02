import math

import pytest
from PIL import Image, ImageChops, ImageDraw

from git_jet.art import project
from git_jet.demo import demo_calendar
from git_jet.flight import HEIGHT, WIDTH
from git_jet.render import Renderer


@pytest.mark.parametrize("carrier", ("lincoln", "classic"))
@pytest.mark.parametrize("jets", (1, 2, 3))
@pytest.mark.parametrize("fps", (5, 10, 20, 25))
def test_jets_stay_visible_and_move_continuously_to_their_runway_slots(carrier, jets, fps):
    renderer = Renderer(demo_calendar(), jets=jets, fps=fps, carrier=carrier, seed="runway-queue")
    first = renderer.flight.visible_poses(0)
    assert len(first) == jets
    assert len({(p.x, p.y) for p in first}) == jets
    previous = first
    for frame in range(1, renderer.frame_count):
        poses = renderer.flight.visible_poses(frame)
        assert len(poses) == jets
        for before, pose, flight in zip(previous, poses, renderer.flights, strict=True):
            assert math.dist((before.x, before.y), (pose.x, pose.y)) * fps < 103
            if frame < flight.launch_start or frame >= flight.touchdown:
                assert pose.heading == pytest.approx(flight.takeoff_heading)
                assert pose.bank == 0 and pose.thrust == 0
        previous = poses
    assert previous == first


@pytest.mark.parametrize("carrier", ("lincoln", "classic"))
@pytest.mark.parametrize("jets", (2, 3))
def test_runway_is_clear_for_each_arrival_and_grounded_jets_do_not_overlap(carrier, jets):
    renderer = Renderer(demo_calendar(), jets=jets, carrier=carrier, seed="runway-reservations")
    for first, second in zip(renderer.flights, renderer.flights[1:], strict=False):
        assert first.landed < second.touchdown
        assert math.dist(first.deck, second.deck) >= 31
    for frame in range(renderer.frame_count):
        occupied = Image.new("1", (WIDTH, HEIGHT))
        for flight in renderer.flights:
            if flight.launch_end < frame < flight.touchdown:
                continue
            pose = flight.pose(frame)
            sprite = renderer.jet_image(pose, frame)
            mask = Image.new("1", (WIDTH, HEIGHT))
            half = sprite.width // 2
            mask.paste(
                sprite.getchannel("A").convert("1"),
                (round(pose.x) - half, round(pose.y) - half),
            )
            assert ImageChops.logical_and(occupied, mask).getbbox() is None, frame
            occupied = ImageChops.logical_or(occupied, mask)


@pytest.mark.parametrize("jets", (1, 2, 3))
def test_classic_touchdown_and_parking_keep_the_whole_jet_on_deck(jets):
    renderer = Renderer(demo_calendar(), jets=jets, carrier="classic", seed="classic-touchdown")
    deck = Image.new("L", (WIDTH, HEIGHT))
    ImageDraw.Draw(deck).polygon(
        [
            (65 + x, 12 + y)
            for x, y in (
                project(u, v, 25)
                for u, v in (
                    (-18, 20),
                    (0, 0),
                    (248, 0),
                    (256, 12),
                    (256, 52),
                    (8, 52),
                    (-18, 36),
                )
            )
        ],
        fill=255,
    )
    for flight in renderer.flights:
        for frame in [0, *range(flight.touchdown, flight.landed + 1)]:
            pose = flight.pose(frame)
            sprite = renderer.jet_image(pose, frame)
            mask = Image.new("L", (WIDTH, HEIGHT))
            half = sprite.width // 2
            mask.paste(sprite.getchannel("A"), (round(pose.x) - half, round(pose.y) - half))
            assert ImageChops.subtract(mask, deck).getbbox() is None
