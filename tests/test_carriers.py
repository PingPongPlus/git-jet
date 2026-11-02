import importlib.util
import math
from collections import deque
from datetime import date, timedelta
from pathlib import Path

import pytest
from PIL import Image

from git_jet import art
from git_jet.calendar import make_calendar
from git_jet.cli import main
from git_jet.demo import demo_calendar
from git_jet.flight import sprite_heading
from git_jet.render import Renderer

ROOT = Path(__file__).resolve().parents[1]


def test_lincoln_is_the_default_and_matches_the_approved_drawing():
    spec = importlib.util.spec_from_file_location(
        "approved_lincoln", ROOT / "artwork/drafts/lincoln_redline.py"
    )
    approved = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(approved)
    assert Renderer(demo_calendar()).carrier == art.DEFAULT_CARRIER == "lincoln"
    with Image.open(
        ROOT / "artwork/drafts/output/lincoln-island-detail-transparent.png"
    ) as reference:
        assert art.carrier_sprite().tobytes() == reference.tobytes()
    for index in range(80):
        assert (
            art.carrier_sprite(index / 80).tobytes()
            == approved.carrier_sprite(index / 80).tobytes()
        )
    assert art.carrier_sprite().tobytes() != art.carrier_sprite(carrier="classic").tobytes()


@pytest.mark.parametrize(
    ("carrier", "deck", "bow"),
    (("classic", (224, 33, 28), (-8, 32, 28)), ("lincoln", (224, 28, 30), (-15, 21, 30))),
)
def test_each_carrier_aligns_launch_and_landing_with_its_deck(carrier, deck, bow):
    renderer = Renderer(demo_calendar(), jets=3, seed="carrier-deck", carrier=carrier)
    for flight in renderer.flights:
        sx, sy = art.project(*deck)
        bx, by = art.project(*bow)
        assert flight.deck == (65 + sx, 12 + sy)
        assert flight.bow == (65 + bx, 12 + by)
        assert (flight.pose(0).x, flight.pose(0).y) == flight.deck
        assert (flight.pose(flight.landed).x, flight.pose(flight.landed).y) == flight.deck
        assert flight.carrier == carrier


@pytest.mark.parametrize("carrier", ("lincoln", "classic"))
def test_carrier_radar_has_no_detached_pixels_during_the_entire_rotation(carrier):
    for index in range(80):
        image = art.carrier_sprite(index / 80, carrier=carrier)
        assert image.tobytes() == art.carrier_sprite(1 + index / 80, carrier=carrier).tobytes()
        assert set(image.getchannel("A").tobytes()) == {0, 255}
        left, top, right, bottom = image.getbbox()
        assert 0 < left < right < 350 and 0 < top < bottom < 190
        pixels = image.load()
        start = art.project(*art.carrier_radar_origin(carrier))
        queue, connected = deque([start]), {start}
        while queue:
            x, y = queue.popleft()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    q = (x + dx, y + dy)
                    if 170 <= q[0] < 260 and 0 <= q[1] < 70 and q not in connected and pixels[q][3]:
                        connected.add(q)
                        queue.append(q)
        assert all(
            (x, y) in connected for y in range(25) for x in range(170, 260) if pixels[x, y][3]
        )


@pytest.mark.parametrize("carrier", ("lincoln", "classic"))
@pytest.mark.parametrize("jets", (1, 3))
def test_both_carriers_keep_all_year_targets_and_smooth_flight(carrier, jets):
    end = date(2026, 11, 1)
    calendar = make_calendar(
        "octocat", end, 365, {end - timedelta(days=i): i + 1 for i in range(365)}
    )
    renderer = Renderer(calendar, carrier=carrier, jets=jets, seed="carrier-route")
    assert (
        len(renderer.flight.strikes)
        == len({s.cell.day.date for s in renderer.flight.strikes})
        == 365
    )
    assert sum(s.cell.day.commits for s in renderer.flight.strikes) == calendar.total
    for flight in renderer.flights:
        for frame in range(flight.launch_end + 1, flight.touchdown):
            previous, pose = flight.pose(frame - 1), flight.pose(frame)
            assert 95 < math.dist((previous.x, previous.y), (pose.x, pose.y)) * flight.fps < 102
            assert abs((pose.heading - previous.heading + 180) % 360 - 180) < 12
            sprite = renderer.jets[sprite_heading(pose.heading), 1, pose.bank]
            left, top, right, bottom = sprite.getbbox()
            assert 0 <= round(pose.x) - 18 + left < round(pose.x) - 18 + right <= 480
            assert 0 <= round(pose.y) - 18 + top < round(pose.y) - 18 + bottom <= 320


@pytest.mark.parametrize("carrier", ("unknown", "LINCOLN", None, [], 1))
def test_invalid_carriers_are_rejected(carrier):
    with pytest.raises(ValueError, match="carrier"):
        Renderer(demo_calendar(), carrier=carrier)


def test_cli_rejects_unknown_carrier_before_requesting_data(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("invalid carrier must not start collection")

    monkeypatch.setattr("git_jet.cli.GitHubClient.collect", forbidden)
    with pytest.raises(SystemExit) as error:
        main(["render", "--username", "octocat", "--carrier", "unknown"])
    assert error.value.code == 2
