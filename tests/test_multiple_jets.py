import math
from datetime import date, timedelta

import pytest

from git_jet import art
from git_jet.calendar import make_calendar
from git_jet.cli import main
from git_jet.demo import demo_calendar
from git_jet.flight import GRID_STEP, GRID_X, GRID_Y, sprite_heading
from git_jet.render import Renderer


def busy_calendar():
    end = date(2026, 11, 1)
    return make_calendar("octocat", end, 365, {end - timedelta(days=i): i + 1 for i in range(365)})


@pytest.mark.parametrize("jets", (2, 3))
@pytest.mark.parametrize("seed", ("0", "1", "2", "3", "git-jet-loop"))
def test_more_jets_shorten_busy_calendars_without_losing_or_repeating_targets(jets, seed):
    calendar = busy_calendar()
    single = Renderer(calendar, seed=seed)
    renderer = Renderer(calendar, jets=jets, seed=seed)
    strikes = renderer.flight.strikes
    assert renderer.frame_count < single.frame_count
    assert len(strikes) == len({s.cell.day.date for s in strikes}) == 365
    assert sum(s.cell.day.commits for s in strikes) == calendar.total
    assert {s.jet_id for s in strikes} == set(range(jets))
    assert (
        max(len(f.strikes) for f in renderer.flights)
        - min(len(f.strikes) for f in renderer.flights)
        <= 1
    )
    for a, b in zip(renderer.flights, renderer.flights[1:], strict=False):
        assert a.launch_end < b.launch_start
    all_airborne = max(f.cruise_start for f in renderer.flights)
    assert len(renderer.flight.visible_poses(all_airborne)) == jets
    for strike in strikes:
        flight = renderer.flights[strike.jet_id]
        pose = flight.pose(strike.fire)
        angle = math.radians(sprite_heading(pose.heading))
        assert strike.origin == pytest.approx(
            (pose.x + math.sin(angle) * 15, pose.y - math.cos(angle) * 15)
        )
        assert flight.cruise_start <= strike.fire < flight.cruise_end
        assert strike.hit < flight.landed <= renderer.flight.landed < renderer.flight.reset_start


def test_three_jets_reproduce_the_entire_squadron_from_a_long_seed():
    first = Renderer(busy_calendar(), jets=3, seed="x" * 128)
    second = Renderer(busy_calendar(), jets=3, seed="x" * 128)
    assert first.flight.seed == second.flight.seed == "x" * 128
    assert first.flight.strikes == second.flight.strikes
    assert first.flight.maneuvers == second.flight.maneuvers
    assert [f.seed for f in first.flights] == [f.seed for f in second.flights]
    assert len({f.seed for f in first.flights}) == 3
    for frame in range(first.frame_count):
        assert first.flight.visible_poses(frame) == second.flight.visible_poses(frame)


def test_multi_jet_routes_keep_smooth_motion_and_remain_inside_the_canvas():
    renderer = Renderer(busy_calendar(), jets=3, seed="smooth-squadron")
    for flight in renderer.flights:
        for frame in range(flight.launch_end + 1, flight.touchdown):
            before, pose = flight.pose(frame - 1), flight.pose(frame)
            assert 95 < math.dist((before.x, before.y), (pose.x, pose.y)) * flight.fps < 102
            assert abs((pose.heading - before.heading + 180) % 360 - 180) < 12
            sprite = art.jet_sprite(sprite_heading(pose.heading), pose.thrust, pose.bank)
            left, top, right, bottom = sprite.getbbox()
            assert 0 <= round(pose.x) - 18 + left < round(pose.x) - 18 + right <= 480
            assert 0 <= round(pose.y) - 18 + top < round(pose.y) - 18 + bottom <= 320


def test_shared_calendar_waits_for_every_jet_before_restoring_hit_cells():
    renderer = Renderer(busy_calendar(), jets=3, seed="shared-reset")
    frame = max(f.landed for f in renderer.flights) - 1
    grid = renderer.grid_frame(frame)
    for strike in renderer.flight.strikes:
        cell = strike.cell
        assert (
            grid.getpixel(
                (GRID_X + cell.column * GRID_STEP + 3, GRID_Y + cell.row * GRID_STEP + 3)
            )[3]
            == 0
        )
    assert (
        renderer.grid_frame(renderer.frame_count - 1).tobytes() == renderer.grid_frame(0).tobytes()
    )
    assert renderer.flight.visible_poses(0) == renderer.flight.visible_poses(
        renderer.frame_count - 1
    )


@pytest.mark.parametrize("fps", (5, 10, 20, 25))
@pytest.mark.parametrize("jets", (2, 3))
def test_multi_jet_full_year_preserves_targets_at_every_supported_frame_rate(fps, jets):
    renderer = Renderer(busy_calendar(), jets=jets, fps=fps, seed="frame-rate")
    assert len(renderer.flight.strikes) == 365
    assert renderer.frame_count <= 3000 and renderer.frame_count % (fps * 4) == 0
    for flight in renderer.flights:
        assert 98 < flight.step * fps <= 100


@pytest.mark.parametrize("jets", (2, 3))
@pytest.mark.parametrize("commits", (0, 10))
def test_sparse_calendars_have_no_fabricated_or_duplicate_attacks(jets, commits):
    calendar = make_calendar("octocat", date(2026, 11, 1), 1, {date(2026, 11, 1): commits})
    renderer = Renderer(calendar, jets=jets, seed="sparse")
    assert len(renderer.flight.strikes) == int(commits > 0)
    assert sum(s.cell.day.commits for s in renderer.flight.strikes) == commits
    assert len(renderer.flights) == jets


def test_omitting_jets_keeps_the_existing_single_jet_frames():
    default = Renderer(demo_calendar(), seed="existing-route")
    explicit = Renderer(demo_calendar(), seed="existing-route", jets=1)
    assert default.jet_count == explicit.jet_count == 1
    assert default.frame_count == explicit.frame_count
    for frame in range(default.frame_count):
        assert default.frame(frame).tobytes() == explicit.frame(frame).tobytes()


@pytest.mark.parametrize("jets", (0, 4, -1, True, "3", 2.5, None))
def test_unsupported_jet_counts_are_rejected(jets):
    with pytest.raises(ValueError, match="jets"):
        Renderer(demo_calendar(), jets=jets)


@pytest.mark.parametrize("jets", ("0", "4", "many"))
def test_cli_rejects_invalid_jet_count_before_network_access(jets, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("invalid options must be rejected before collection")

    monkeypatch.setattr("git_jet.cli.GitHubClient.collect", forbidden)
    with pytest.raises(SystemExit) as error:
        main(["render", "--username", "octocat", "--jets", jets])
    assert error.value.code == 2
