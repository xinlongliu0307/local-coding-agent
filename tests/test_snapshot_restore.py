"""Tests for snapshot restoration, capture integrity, and failure surfacing."""

from __future__ import annotations

import json
import os
import shutil

import pytest

import agent.snapshot as snapshot_module
from agent.snapshot import (
    MANIFEST_NAME,
    restore_snapshot,
    snapshot_failures,
    take_snapshot,
)


def test_snapshot_round_trip_restores_original_content(tmp_path):
    target = tmp_path / "code.py"
    target.write_text("original\n")
    snapshot_dir = take_snapshot(
        [str(target)], snapshot_root=str(tmp_path / "snaps")
    )
    assert snapshot_dir is not None

    target.write_text("modified\n")
    restored = restore_snapshot(snapshot_dir)

    assert os.path.abspath(str(target)) in restored
    assert target.read_text() == "original\n"


def test_snapshot_preserves_files_with_same_basename(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    file_a = tmp_path / "a" / "config.py"
    file_b = tmp_path / "b" / "config.py"
    file_a.write_text("A original\n")
    file_b.write_text("B original\n")

    snapshot_dir = take_snapshot(
        [str(file_a), str(file_b)], snapshot_root=str(tmp_path / "snaps")
    )
    file_a.write_text("A changed\n")
    file_b.write_text("B changed\n")
    restore_snapshot(snapshot_dir)

    assert file_a.read_text() == "A original\n"
    assert file_b.read_text() == "B original\n"


def test_restore_recreates_missing_parent_directory(tmp_path):
    sub = tmp_path / "nested" / "deep"
    sub.mkdir(parents=True)
    target = sub / "file.txt"
    target.write_text("keep\n")
    snapshot_dir = take_snapshot(
        [str(target)], snapshot_root=str(tmp_path / "snaps")
    )

    shutil.rmtree(tmp_path / "nested")
    assert not target.exists()

    restore_snapshot(snapshot_dir)
    assert target.read_text() == "keep\n"


def test_restore_raises_when_manifest_missing(tmp_path):
    empty_dir = tmp_path / "not_a_snapshot"
    empty_dir.mkdir()
    with pytest.raises(FileNotFoundError):
        restore_snapshot(str(empty_dir))


def test_manifest_records_captured_files(tmp_path):
    target = tmp_path / "x.py"
    target.write_text("data\n")
    snapshot_dir = take_snapshot(
        [str(target)], snapshot_root=str(tmp_path / "snaps")
    )
    with open(
        os.path.join(snapshot_dir, MANIFEST_NAME), encoding="utf-8"
    ) as handle:
        manifest = json.load(handle)
    assert os.path.abspath(str(target)) in manifest["captured"].values()
    assert manifest["failed"] == []


def test_snapshot_surfaces_copy_failure(tmp_path, monkeypatch):
    good = tmp_path / "good.py"
    bad = tmp_path / "bad.py"
    good.write_text("good\n")
    bad.write_text("bad\n")

    real_copy = snapshot_module.shutil.copy2

    def failing_copy(src, dst, *args, **kwargs):
        if os.path.basename(str(src)) == "bad.py":
            raise OSError("simulated copy failure")
        return real_copy(src, dst, *args, **kwargs)

    monkeypatch.setattr(snapshot_module.shutil, "copy2", failing_copy)

    snapshot_dir = take_snapshot(
        [str(good), str(bad)], snapshot_root=str(tmp_path / "snaps")
    )
    failures = snapshot_failures(snapshot_dir)

    assert os.path.abspath(str(bad)) in failures
    with open(
        os.path.join(snapshot_dir, MANIFEST_NAME), encoding="utf-8"
    ) as handle:
        manifest = json.load(handle)
    assert os.path.abspath(str(good)) in manifest["captured"].values()
