"""Bounded public REST collection; distinct authored SHAs, never contribution totals."""

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import UTC, date, datetime, time, timedelta

from .calendar import make_calendar, validate_username


class GitHubError(RuntimeError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise GitHubError("unexpected API redirect; retry using the account's current login")


class GitHubClient:
    def __init__(self, token: str = ""):
        self.token = token
        self.requests = 0

    def request(self, path: str, *, anonymous: bool = False):
        if not path.startswith("/") or path.startswith("//"):
            raise GitHubError("invalid GitHub API path")
        self.requests += 1
        if self.requests > 1000:
            raise GitHubError("request budget exceeded; select fewer days")
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "git-jet/0.1.0",
            "X-GitHub-Api-Version": "2026-03-10",
        }
        if self.token and not anonymous:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            opener = urllib.request.build_opener(NoRedirect())
            with opener.open(
                urllib.request.Request("https://api.github.com" + path, headers=headers), timeout=20
            ) as response:
                payload = response.read(10_000_001)
            if len(payload) > 10_000_000:
                raise GitHubError("GitHub response exceeds the size limit")
            return json.loads(payload)
        except urllib.error.HTTPError as error:
            if (
                error.code == 403
                and self.token
                and not anonymous
                and error.headers.get("X-RateLimit-Remaining") != "0"
            ):
                try:
                    message = json.loads(error.read(4096)).get("message", "")
                except (json.JSONDecodeError, UnicodeDecodeError):
                    message = ""
                if message in {
                    "Resource not accessible by integration",
                    "Resource not accessible by personal access token",
                }:
                    print(
                        "git-jet: token scope rejected a public GET; retrying anonymously",
                        file=sys.stderr,
                    )
                    return self.request(path, anonymous=True)
            if error.code == 409 and "/commits?" in path:
                return []  # Empty repository.
            if error.code in (403, 429):
                raise GitHubError(
                    "GitHub denied the request or the rate limit was reached"
                ) from None
            raise GitHubError(f"GitHub API returned HTTP {error.code}") from None
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            raise GitHubError(
                "unable to read GitHub API data; no partial calendar was saved"
            ) from None

    def pages(self, path: str):
        separator = "&" if "?" in path else "?"
        for page in range(1, 21):
            items = self.request(f"{path}{separator}per_page=100&page={page}")
            if not isinstance(items, list):
                raise GitHubError("unexpected GitHub list response")
            yield from items
            if len(items) < 100:
                return
        raise GitHubError("pagination limit reached; choose a shorter data period")

    def collect(self, username: str, *, days: int = 365, end: date | None = None):
        validate_username(username)
        end = end or datetime.now(UTC).date()
        # Validate the selected span before making any network requests.
        make_calendar(username, end, days, {})
        start = end - timedelta(days=days - 1)
        since = datetime.combine(start, time.min, UTC)
        until = datetime.combine(end, time.max, UTC)
        identity = self.request(f"/users/{username}")
        if not isinstance(identity, dict) or identity.get("type") != "User":
            raise GitHubError("username must identify a GitHub user account")
        canonical = identity.get("login", username)
        validate_username(canonical)
        counts = Counter()
        seen = set()
        for repo in self.pages(f"/users/{canonical}/repos?type=owner&sort=full_name"):
            if (
                repo.get("private", True)
                or repo.get("fork", True)
                or repo.get("owner", {}).get("login", "").casefold() != canonical.casefold()
            ):
                continue
            name = repo.get("name", "")
            if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
                raise GitHubError("invalid repository name in API response")
            query = urllib.parse.urlencode({"since": since.isoformat(), "until": until.isoformat()})
            for commit in self.pages(f"/repos/{canonical}/{name}/commits?{query}"):
                author = commit.get("author") or {}
                if author.get("login", "").casefold() != canonical.casefold():
                    continue
                sha = commit.get("sha", "")
                if not isinstance(sha, str) or not re.fullmatch(r"[a-fA-F0-9]{40}", sha):
                    raise GitHubError("invalid commit SHA in API response")
                try:
                    instant = datetime.fromisoformat(
                        commit["commit"]["committer"]["date"].replace("Z", "+00:00")
                    )
                    if instant.tzinfo is None:
                        raise ValueError("timezone required")
                except (KeyError, ValueError, TypeError):
                    raise GitHubError("invalid commit date in API response") from None
                day = instant.astimezone(UTC).date()
                sha = sha.lower()
                if start <= day <= end and sha not in seen:
                    counts[day] += 1
                    seen.add(sha)
        return make_calendar(canonical, end, days, counts)
