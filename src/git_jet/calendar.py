"""A credential-free, commit-only UTC calendar and Sunday-first grid layout."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

USERNAME = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?\Z")
SCOPE = "public-owned-default-branches"


def validate_username(username: str) -> None:
    if not isinstance(username, str) or not USERNAME.fullmatch(username):
        raise ValueError("username must be a GitHub login")


@dataclass(frozen=True)
class Day:
    date: date
    commits: int

    def __post_init__(self):
        if type(self.date) is not date or type(self.commits) is not int or self.commits < 0:
            raise ValueError("calendar days require a date and a nonnegative integer commit count")


@dataclass(frozen=True)
class Cell:
    column: int
    row: int
    day: Day | None


@dataclass(frozen=True)
class Calendar:
    username: str
    days: tuple[Day, ...]

    def __post_init__(self):
        validate_username(self.username)
        if not 1 <= len(self.days) <= 365 or any(not isinstance(d, Day) for d in self.days):
            raise ValueError("calendar must contain 1..365 complete UTC days")
        if any(
            b.date - a.date != timedelta(days=1)
            for a, b in zip(self.days, self.days[1:], strict=False)
        ):
            raise ValueError("calendar dates must be unique, consecutive and ascending")

    @property
    def total(self):
        return sum(day.commits for day in self.days)

    def cells(self) -> tuple[Cell, ...]:
        offset = (self.days[0].date.weekday() + 1) % 7
        columns = (offset + len(self.days) + 6) // 7
        left = 53 - columns
        by_position = {
            (left + (offset + index) // 7, (offset + index) % 7): day
            for index, day in enumerate(self.days)
        }
        return tuple(
            Cell(col, row, by_position.get((col, row))) for col in range(53) for row in range(7)
        )

    def to_dict(self):
        return {
            "schema_version": 1,
            "username": self.username,
            "scope": SCOPE,
            "total_commits": self.total,
            "days": [{"date": day.date.isoformat(), "commits": day.commits} for day in self.days],
        }

    def write(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")

    @classmethod
    def read(cls, path: Path):
        if path.stat().st_size > 2_000_000:
            raise ValueError("cached calendar exceeds the size limit")
        data = json.loads(path.read_text(encoding="utf-8"))
        if (
            not isinstance(data, dict)
            or type(data.get("schema_version")) is not int
            or data.get("schema_version") != 1
            or data.get("scope") != SCOPE
        ):
            raise ValueError("unsupported calendar schema or scope")
        result = cls(
            data["username"],
            tuple(Day(date.fromisoformat(d["date"]), d["commits"]) for d in data["days"]),
        )
        if type(data.get("total_commits")) is not int or data["total_commits"] != result.total:
            raise ValueError("cached calendar total does not match its day counts")
        return result


def make_calendar(username: str, end: date, days: int, counts: dict[date, int]) -> Calendar:
    if type(days) is not int or not 1 <= days <= 365:
        raise ValueError("days must be an integer in 1..365")
    start = end - timedelta(days=days - 1)
    return Calendar(
        username,
        tuple(
            Day(start + timedelta(days=i), counts.get(start + timedelta(days=i), 0))
            for i in range(days)
        ),
    )
