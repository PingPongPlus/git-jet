import importlib.util
import math
from datetime import date, timedelta
from pathlib import Path

import pytest
from PIL import Image

from git_jet import art
from git_jet.calendar import make_calendar
from git_jet.demo import demo_calendar
from git_jet.flight import GRID_STEP, GRID_X, GRID_Y, Flight, sprite_heading
from git_jet.render import Renderer

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("span", (1, 7, 30, 365))
def test_every_active_day_gets_exactly_one_on_screen_attack(span):
    end = date(2026, 11, 1)
    counts = {end - timedelta(days=i): i + 1 for i in range(span)}
    calendar = make_calendar("octocat", end, span, counts)
    flight = Flight(calendar)
    assert len(flight.strikes) == span
    assert {strike.cell.day.date for strike in flight.strikes} == set(counts)
    assert sum(strike.cell.day.commits for strike in flight.strikes) == calendar.total
    assert flight.frame_count < 3000
    assert flight.strikes[-1].hit < flight.landed < flight.reset_start
    assert all(a.hit <= b.hit for a, b in zip(flight.strikes, flight.strikes[1:], strict=False))
    for strike in flight.strikes:
        pose = flight.pose(strike.fire)
        direction = math.radians(sprite_heading(pose.heading))
        assert strike.origin == pytest.approx(
            (pose.x + math.sin(direction) * 15, pose.y - math.cos(direction) * 15)
        )
        assert 0 < strike.target[0] < 480 and 0 < strike.target[1] < 320


def test_grid_clears_only_hit_cells_then_rebuilds_and_static_frame_stays_full():
    renderer = Renderer(demo_calendar())
    original = renderer.grid_frame(0)
    for strike in renderer.flight.strikes:
        for other in renderer.flight.strikes:
            cell = other.cell
            x, y = GRID_X + cell.column * GRID_STEP + 3, GRID_Y + cell.row * GRID_STEP + 3
            before = renderer.grid_frame(strike.hit - 1).getpixel((x, y))[3]
            after = renderer.grid_frame(strike.hit).getpixel((x, y))[3]
            assert after == (0 if other.hit <= strike.hit else 255)
            if other == strike:
                assert before == 255 and after == 0
    assert renderer.grid_frame(renderer.frame_count - 1).tobytes() == original.tobytes()
    assert renderer.frame(0).tobytes() == renderer.frame(renderer.frame_count).tobytes()
    assert renderer.frame(-1).tobytes() == renderer.frame(renderer.frame_count - 1).tobytes()


def test_zero_commits_patrol_has_no_targets_or_fabricated_hits():
    renderer = Renderer(make_calendar("octocat", date(2026, 11, 1), 365, {}))
    assert not renderer.flight.strikes
    assert renderer.calendar.total == 0
    for frame in (0, 31, 60, renderer.frame_count - 1):
        assert renderer.grid_frame(frame).tobytes() == renderer.grid_frame(0).tobytes()
        assert set(renderer.frame(frame).getchannel("A").tobytes()) == {0, 255}


def test_production_art_preserves_approved_body_and_effects(assert_carrier_body_preserved):
    spec = importlib.util.spec_from_file_location(
        "approved_art", ROOT / "artwork/drafts/sprites.py"
    )
    approved = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(approved)
    with Image.open(ROOT / "artwork/drafts/output/carrier-transparent.png") as reference:
        reference = reference.copy()
        x, y = art.project(185, 10, 60)
        # The owner requested removal of this detached five-pixel aerial.
        reference.paste((0, 0, 0, 0), (x - 3, y - 26, x - 2, y - 21))
        assert_carrier_body_preserved(art.carrier_sprite(carrier="classic"), reference)
    for phase in (0, 0.12, 0.5, 0.95):
        current, original = (
            art.carrier_sprite(phase, carrier="classic"),
            approved.carrier_sprite(phase),
        )
        x, y = art.project(185, 10, 60)
        radar = (x - 7, y - 27, x + 9, y - 12)
        original.paste(current.crop(radar), radar[:2])
        assert_carrier_body_preserved(current, original)
    for heading in (i * 22.5 for i in range(16)):
        for bank in (-1, 0, 1):
            for thrust in (0, 1, 2):
                assert (
                    art.jet_sprite(heading, thrust, bank).tobytes()
                    == approved.jet_sprite(heading, thrust, bank).tobytes()
                )
    for level in range(5):
        assert art.commit_tile(level).tobytes() == approved.commit_tile(level).tobytes()
    for age in (0, 0.12, 0.4, 0.7, 0.95, 1):
        assert art.explosion_sprite(age).tobytes() == approved.explosion_sprite(age).tobytes()


def test_jet_stays_inside_the_canvas_for_the_entire_demo_flight():
    renderer = Renderer(demo_calendar())
    for frame in range(renderer.frame_count):
        pose = renderer.flight.pose(frame)
        sprite = art.jet_sprite(sprite_heading(pose.heading), pose.thrust, pose.bank)
        left, top, right, bottom = sprite.getbbox()
        assert 0 <= round(pose.x) - 18 + left < round(pose.x) - 18 + right <= 480
        assert 0 <= round(pose.y) - 18 + top < round(pose.y) - 18 + bottom <= 320


def test_airborne_speed_and_heading_are_continuous_through_shots_and_path_joins():
    flight = Flight(demo_calendar())
    for frame in range(flight.launch_end + 1, flight.touchdown):
        previous, current = flight.pose(frame - 1), flight.pose(frame)
        speed = math.dist((previous.x, previous.y), (current.x, current.y)) * flight.fps
        turn = abs((current.heading - previous.heading + 180) % 360 - 180)
        assert 95 < speed < 102, (frame, speed)
        assert turn < 12, (frame, turn)
    for strike in flight.strikes:
        a, b = flight.pose(strike.fire), flight.pose(strike.fire + 1)
        assert math.dist((a.x, a.y), (b.x, b.y)) * flight.fps > 95


def test_frame_rate_changes_sampling_not_cruise_speed():
    for fps in (5, 10, 20, 25):
        flight = Flight(demo_calendar(), fps=fps, seed="frame-rate-sampling")
        assert flight.frame_count % (fps * 4) == 0
        assert 98 < flight.step * fps <= 100
        a, b = flight.pose(flight.cruise_start + 1), flight.pose(flight.cruise_start + 2)
        assert 98 < math.dist((a.x, a.y), (b.x, b.y)) * fps <= 100


def test_projectiles_leave_the_nose_then_curve_to_the_exact_day_cell():
    flight = Flight(demo_calendar())
    for strike in flight.strikes:
        assert strike.projectile(0) == pytest.approx(strike.origin)
        assert strike.projectile(1) == pytest.approx(strike.target)
        near = strike.projectile(0.0001)
        direction = ((near[0] - strike.origin[0]), (near[1] - strike.origin[1]))
        magnitude = math.hypot(*direction)
        assert tuple(value / magnitude for value in direction) == pytest.approx(
            strike.direction, abs=0.001
        )
