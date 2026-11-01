import math
from datetime import date, timedelta

import pytest

from git_jet import art
from git_jet.calendar import make_calendar
from git_jet.demo import demo_calendar
from git_jet.flight import Flight, sprite_heading


def trace(flight):
    return tuple(flight.pose(frame) for frame in range(flight.frame_count))


def test_fixed_seed_repeats_route_and_attack_schedule():
    first = Flight(demo_calendar(), seed="repeat-this-route")
    second = Flight(demo_calendar(), seed="repeat-this-route")
    assert trace(first) == trace(second)
    assert first.strikes == second.strikes and first.maneuvers == second.maneuvers


def test_unset_seed_is_fresh_per_generation_and_never_changes_during_a_flight(monkeypatch):
    values = iter(("first-route", "second-route"))
    monkeypatch.setattr("git_jet.flight.secrets.token_hex", lambda size: next(values))
    first = Flight(demo_calendar())
    before = trace(first)
    second = Flight(demo_calendar())
    assert first.seed == "first-route" and second.seed == "second-route"
    assert trace(first) == before
    assert first.course.point(150) != second.course.point(150)


def test_route_pool_contains_loops_and_sweeps_without_loops():
    flights = [
        Flight(demo_calendar(), seed=seed) for seed in ("demo", "alpha", "beta", "git-jet-loop")
    ]
    assert any(f.maneuvers for f in flights) and any(not f.maneuvers for f in flights)
    assert len({f.course.point(150) for f in flights}) == len(flights)
    for flight in flights:
        if flight.maneuvers:
            assert any(
                m["start_frame"] <= s.fire <= m["end_frame"]
                for m in flight.maneuvers
                for s in flight.strikes
            )


@pytest.mark.parametrize("seed", [str(i) for i in range(12)])
def test_randomized_routes_stay_smooth_and_inside_the_canvas(seed):
    flight = Flight(demo_calendar(), seed=seed)
    for frame in range(flight.launch_end + 1, flight.touchdown):
        before, current = flight.pose(frame - 1), flight.pose(frame)
        speed = math.dist((before.x, before.y), (current.x, current.y)) * flight.fps
        turn = abs((current.heading - before.heading + 180) % 360 - 180)
        assert 95 < speed < 102, (seed, frame, speed)
        assert turn < 12, (seed, frame, turn)
        sprite = art.jet_sprite(sprite_heading(current.heading), 2, current.bank)
        left, top, right, bottom = sprite.getbbox()
        assert 0 <= round(current.x) - 18 + left < round(current.x) - 18 + right <= 480
        assert 0 <= round(current.y) - 18 + top < round(current.y) - 18 + bottom <= 320


@pytest.mark.parametrize("seed", ("0", "1", "2", "3", "git-jet-loop"))
def test_random_maneuvers_preserve_all_365_day_targets(seed):
    end = date(2026, 11, 1)
    counts = {end - timedelta(days=i): i + 1 for i in range(365)}
    calendar = make_calendar("octocat", end, 365, counts)
    flight = Flight(calendar, seed=seed)
    assert len(flight.strikes) == 365
    assert {s.cell.day.date for s in flight.strikes} == set(counts)
    assert flight.frame_count <= 3000
    assert sum(s.cell.day.commits for s in flight.strikes) == calendar.total


@pytest.mark.parametrize("seed", ("", 1, True, "x" * 129))
def test_invalid_route_seeds_are_rejected(seed):
    with pytest.raises(ValueError, match="seed"):
        Flight(demo_calendar(), seed=seed)
