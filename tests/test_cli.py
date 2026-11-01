from datetime import date

from git_jet.calendar import Calendar, make_calendar
from git_jet.cli import main
from git_jet.github import GitHubError


def test_collect_saves_only_successful_complete_data(monkeypatch, tmp_path):
    calendar = make_calendar("octocat", date(2026, 11, 1), 7, {date(2026, 11, 1): 3})
    monkeypatch.setattr("git_jet.cli.GitHubClient.collect", lambda *args, **kwargs: calendar)
    path = tmp_path / "calendar.json"
    assert main(["collect", "--username", "octocat", "--output", str(path)]) == 0
    assert Calendar.read(path) == calendar
    original = path.read_bytes()

    def denied(*args, **kwargs):
        raise GitHubError("rate limit")

    monkeypatch.setattr("git_jet.cli.GitHubClient.collect", denied)
    assert main(["collect", "--username", "octocat", "--output", str(path)]) == 1
    assert path.read_bytes() == original
