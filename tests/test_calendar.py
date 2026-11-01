import json
from datetime import date, timedelta

import pytest

from git_jet.calendar import Calendar, Day, make_calendar


@pytest.mark.parametrize("end", (date(2026, 11, 1), date(2024, 3, 1), date(2026, 1, 1)))
@pytest.mark.parametrize("span", (1, 7, 30, 365))
def test_complete_utc_days_map_once_to_a_sunday_first_grid(end, span):
    calendar = make_calendar("octocat", end, span, {end: 7})
    cells = calendar.cells()
    assert len(cells) == 53 * 7
    actual = [cell for cell in cells if cell.day is not None]
    assert len(actual) == span
    assert calendar.days[0].date == end - timedelta(days=span - 1)
    assert calendar.days[-1].date == end
    assert calendar.total == 7
    assert sum(cell.day.commits for cell in actual) == 7
    assert all(cell.row == (cell.day.date.weekday() + 1) % 7 for cell in actual)
    assert len({cell.day.date for cell in actual}) == span
    assert all(0 <= cell.column < 53 and 0 <= cell.row < 7 for cell in cells)


@pytest.mark.parametrize("commits", (-1, True, 1.5, "2"))
def test_day_counts_are_real_nonnegative_integers(commits):
    with pytest.raises(ValueError):
        Day(date(2026, 1, 1), commits)


def test_calendar_round_trip_and_tampered_total(tmp_path):
    calendar = make_calendar("octocat", date(2026, 11, 1), 30, {date(2026, 10, 31): 11})
    path = tmp_path / "calendar.json"
    calendar.write(path)
    assert Calendar.read(path) == calendar
    data = json.loads(path.read_text())
    data["total_commits"] = 12
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="total"):
        Calendar.read(path)


@pytest.mark.parametrize("days", (0, 366, True, "30"))
def test_invalid_spans_fail(days):
    with pytest.raises(ValueError, match="days"):
        make_calendar("octocat", date(2026, 11, 1), days, {})


def test_duplicate_and_missing_dates_are_rejected():
    first = Day(date(2026, 1, 1), 1)
    for days in ((first, first), (first, Day(date(2026, 1, 3), 2))):
        with pytest.raises(ValueError, match="consecutive"):
            Calendar("octocat", days)
