from datetime import date
from email.message import Message
from io import BytesIO
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlparse

import pytest

from git_jet.github import GitHubClient, GitHubError


def repository(name, **overrides):
    return {
        "name": name,
        "owner": {"login": "Octocat"},
        "fork": False,
        "private": False,
        **overrides,
    }


def commit(number, when="2026-10-31T12:00:00Z", author="octocat"):
    return {
        "sha": f"{number:040x}",
        "author": {"login": author},
        "commit": {"committer": {"date": when}},
    }


def test_collection_deduplicates_shas_filters_scope_and_uses_utc_days(monkeypatch):
    client = GitHubClient()
    calls = []

    def request(path):
        calls.append(path)
        parsed = urlparse(path)
        if path == "/users/octocat":
            return {"login": "Octocat", "type": "User"}
        if parsed.path == "/users/Octocat/repos":
            return [
                repository("code"),
                repository("copy"),
                repository("fork", fork=True),
                repository("secret", private=True),
                repository("foreign", owner={"login": "other"}),
            ]
        query = parse_qs(parsed.query)
        assert "author" not in query
        assert query["since"] == ["2026-10-26T00:00:00+00:00"]
        assert query["until"] == ["2026-11-01T23:59:59.999999+00:00"]
        if parsed.path == "/repos/Octocat/code/commits":
            return [
                commit(1),
                commit(2, "2026-11-01T00:30:00+02:00"),
                commit(3, author="another"),
                commit(4, "2026-10-25T23:59:59Z"),
                commit(5, "2026-11-02T00:00:00Z"),
                {**commit(6), "author": None},
            ]
        if parsed.path == "/repos/Octocat/copy/commits":
            return [commit(1), commit(7, "2026-11-01T23:59:59Z")]
        raise AssertionError(path)

    monkeypatch.setattr(client, "request", request)
    calendar = client.collect("octocat", days=7, end=date(2026, 11, 1))
    assert calendar.total == 3
    assert {day.date.isoformat(): day.commits for day in calendar.days if day.commits} == {
        "2026-10-31": 2,
        "2026-11-01": 1,
    }
    assert len(calls) == 4


def test_pagination_is_complete_and_rejects_truncation(monkeypatch):
    client = GitHubClient()
    calls = []

    def request(path):
        calls.append(path)
        return list(range(100)) if parse_qs(urlparse(path).query)["page"] == ["1"] else [100]

    monkeypatch.setattr(client, "request", request)
    assert len(list(client.pages("/list"))) == 101
    assert len(calls) == 2
    monkeypatch.setattr(client, "request", lambda path: [None] * 100)
    with pytest.raises(GitHubError, match="pagination"):
        list(client.pages("/list"))


def test_invalid_selection_fails_without_network(monkeypatch):
    client = GitHubClient()

    def unexpected(path):
        raise AssertionError("must validate before network access")

    monkeypatch.setattr(client, "request", unexpected)
    with pytest.raises(ValueError):
        client.collect("../bad")
    with pytest.raises(ValueError):
        client.collect("octocat", days=366)


def test_request_budget_is_enforced_before_network():
    client = GitHubClient("not-a-real-token")
    client.requests = 1000
    with pytest.raises(GitHubError, match="budget"):
        client.request("/users/octocat")
    with pytest.raises(GitHubError, match="path"):
        client.request("https://example.com")


def test_installation_scope_fallback_drops_auth_only_for_the_same_public_api(monkeypatch):
    calls = []
    headers = Message()
    headers["X-RateLimit-Remaining"] = "100"

    class Response(BytesIO):
        pass

    class Opener:
        def open(self, request, timeout):
            calls.append((request.full_url, request.get_header("Authorization")))
            if len(calls) == 1:
                raise HTTPError(
                    request.full_url,
                    403,
                    "scope",
                    headers,
                    BytesIO(b'{"message":"Resource not accessible by integration"}'),
                )
            return Response(b'{"login":"octocat","type":"User"}')

    monkeypatch.setattr("git_jet.github.urllib.request.build_opener", lambda *args: Opener())
    client = GitHubClient("fake-test-token")
    assert client.request("/users/octocat")["login"] == "octocat"
    assert calls == [
        ("https://api.github.com/users/octocat", "Bearer fake-test-token"),
        ("https://api.github.com/users/octocat", None),
    ]


def test_rate_limit_errors_are_not_silently_retried_anonymously(monkeypatch):
    headers = Message()
    headers["X-RateLimit-Remaining"] = "0"

    class Opener:
        def open(self, request, timeout):
            raise HTTPError(
                request.full_url,
                403,
                "rate limit",
                headers,
                BytesIO(b'{"message":"Resource not accessible by integration"}'),
            )

    monkeypatch.setattr("git_jet.github.urllib.request.build_opener", lambda *args: Opener())
    client = GitHubClient("fake-test-token")
    with pytest.raises(GitHubError, match="rate limit"):
        client.request("/users/octocat")
    assert client.requests == 1
