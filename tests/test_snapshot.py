"""Tests for automatic file-content snapshotting and pruning."""

from __future__ import annotations

import os
import time

from agent.snapshot import prune_old_snapshots, take_snapshot


def test_snapshot_captures_file_content(tmp_path):
    source = tmp_path / "file.txt"
    source.write_text("captured content")
    root = tmp_path / "snapshots"

    snapshot_dir = take_snapshot([str(source)], snapshot_root=str(root))

    assert snapshot_dir is not None
    captured = os.path.join(snapshot_dir, "file.txt")
    assert os.path.isfile(captured)
    with open(captured, "r", encoding="utf-8") as handle:
        assert handle.read() == "captured content"


def test_snapshot_skips_nonexistent_files(tmp_path):
    source = tmp_path / "real.txt"
    source.write_text("present")
    missing = tmp_path / "absent.txt"
    root = tmp_path / "snapshots"

    snapshot_dir = take_snapshot(
        [str(source), str(missing)], snapshot_root=str(root)
    )

    assert snapshot_dir is not None
    assert os.path.isfile(os.path.join(snapshot_dir, "real.txt"))
    assert not os.path.exists(os.path.join(snapshot_dir, "absent.txt"))


def test_snapshot_returns_none_for_empty_input(tmp_path):
    root = tmp_path / "snapshots"
    result = take_snapshot([], snapshot_root=str(root))
    assert result is None


def test_prune_removes_only_old_snapshots(tmp_path):
    root = tmp_path / "snapshots"
    root.mkdir()
    old = root / "old_snapshot"
    old.mkdir()
    recent = root / "recent_snapshot"
    recent.mkdir()

    # Backdate the old directory beyond the retention window.
    old_time = time.time() - (40 * 24 * 60 * 60)
    os.utime(old, (old_time, old_time))

    removed = prune_old_snapshots(snapshot_root=str(root), retention_days=30)

    assert removed == 1
    assert not old.exists()
    assert recent.exists()


def test_prune_handles_missing_root(tmp_path):
    root = tmp_path / "does_not_exist"
    removed = prune_old_snapshots(snapshot_root=str(root))
    assert removed == 0
