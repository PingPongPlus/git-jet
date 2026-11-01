import importlib.util
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_publisher_changes_only_assets_and_skips_unchanged(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "publish_assets", ROOT / "scripts/publish_assets.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    remote, work, assets = (tmp_path / name for name in ("remote.git", "work", "assets"))
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    work.mkdir()

    def git(*args):
        return subprocess.run(
            ["git", *args], cwd=work, check=True, capture_output=True, text=True
        ).stdout.strip()

    git("init", "-b", "main")
    git("config", "user.name", "Test")
    git("config", "user.email", "test@example.invalid")
    (work / "README.md").write_text("default branch must stay untouched")
    git("add", "README.md")
    git("commit", "-m", "Initial")
    git("remote", "add", "origin", str(remote))
    git("push", "origin", "main")
    before = git("rev-parse", "HEAD")
    assets.mkdir()
    for name in module.ASSETS:
        (assets / name).write_bytes(b"fixture")
    (assets / "unrelated.txt").write_text("never publish this")
    assert module.publish(assets, str(remote), "main") is True
    assert module.publish(assets, str(remote), "main") is False
    git("fetch", "origin", "output")
    assert set(git("ls-tree", "--name-only", "origin/output").splitlines()) == set(module.ASSETS)
    assert git("rev-parse", "main") == before
    # An existing unrelated output-branch file survives the next refresh.
    git("checkout", "-b", "output", "origin/output")
    (work / "keep.txt").write_text("keep")
    git("add", "keep.txt")
    git("commit", "-m", "Unrelated output file")
    git("push", "origin", "output")
    (assets / "git-jet.gif").write_bytes(b"changed fixture")
    assert module.publish(assets, str(remote), "main") is True
    git("fetch", "origin", "output")
    assert git("show", "origin/output:keep.txt") == "keep"
    assert git("rev-parse", "main") == before
    with pytest.raises(ValueError, match="default branch"):
        module.publish(assets, str(remote), "output")
