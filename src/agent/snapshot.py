"""Automatic file-content snapshotting of files modified during a task.

A snapshot captures the content of files at a point in time so that changes
can be undone. Each snapshot records, in a manifest, the original absolute
path of every file it stores, so the snapshot can be restored to the exact
locations it was taken from. Files are stored under collision-proof names so
that two files sharing a basename in different directories are both preserved.
The manifest also lists any existing file that could not be copied, so a
partial capture is surfaced rather than hidden.
"""

from __future__ import annotations

import json
import os
import shutil
import time
from datetime import datetime, timedelta


DEFAULT_SNAPSHOT_ROOT = os.path.expanduser("~/.local-coding-agent/snapshots")
RETENTION_DAYS = 30
MANIFEST_NAME = "manifest.json"


def take_snapshot(
    paths: list[str],
    snapshot_root: str = DEFAULT_SNAPSHOT_ROOT,
) -> str | None:
    """Copy the current content of the given files into a timestamped snapshot.

    Each call creates a subdirectory named for the current time and copies
    each existing path into it under a collision-proof name. A manifest
    records the original absolute path of every captured file and lists any
    existing file that could not be copied. Files that no longer exist are
    skipped. Returns the snapshot directory path, or None if there were no
    files to capture.
    """
    existing = [path for path in paths if os.path.isfile(path)]
    if not existing:
        return None

    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
    snapshot_dir = os.path.join(snapshot_root, stamp)
    os.makedirs(snapshot_dir, exist_ok=True)

    captured: dict[str, str] = {}
    failed: list[str] = []
    for index, path in enumerate(existing):
        original = os.path.abspath(path)
        stored_name = f"{index:04d}_{os.path.basename(original)}"
        destination = os.path.join(snapshot_dir, stored_name)
        try:
            shutil.copy2(path, destination)
        except OSError:
            failed.append(original)
            continue
        captured[stored_name] = original

    manifest = {"captured": captured, "failed": failed}
    with open(
        os.path.join(snapshot_dir, MANIFEST_NAME), "w", encoding="utf-8"
    ) as handle:
        json.dump(manifest, handle, indent=2)

    return snapshot_dir


def restore_snapshot(snapshot_dir: str) -> list[str]:
    """Restore files from a snapshot to their original locations.

    Reads the snapshot's manifest and copies each captured file back to the
    absolute path it was taken from, recreating parent directories as needed.
    Returns the list of original paths restored. Raises FileNotFoundError if
    the snapshot directory has no manifest.

    This is an administrative recovery function for the operator. It is not a
    model-callable tool and is deliberately not registered in the tool
    registry, since it writes to arbitrary absolute paths.
    """
    manifest_path = os.path.join(snapshot_dir, MANIFEST_NAME)
    if not os.path.isfile(manifest_path):
        raise FileNotFoundError(
            f"no manifest found in snapshot '{snapshot_dir}'; cannot restore"
        )
    with open(manifest_path, "r", encoding="utf-8") as handle:
        manifest = json.load(handle)

    captured = manifest.get("captured", {})
    restored: list[str] = []
    for stored_name, original in captured.items():
        source = os.path.join(snapshot_dir, stored_name)
        if not os.path.isfile(source):
            continue
        parent = os.path.dirname(original)
        if parent:
            os.makedirs(parent, exist_ok=True)
        shutil.copy2(source, original)
        restored.append(original)
    return restored


def snapshot_failures(snapshot_dir: str) -> list[str]:
    """Return the files a snapshot could not capture, from its manifest.

    Returns an empty list if the snapshot has no manifest or recorded no
    failures.
    """
    manifest_path = os.path.join(snapshot_dir, MANIFEST_NAME)
    if not os.path.isfile(manifest_path):
        return []
    with open(manifest_path, "r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    return manifest.get("failed", [])


def prune_old_snapshots(
    snapshot_root: str = DEFAULT_SNAPSHOT_ROOT,
    retention_days: int = RETENTION_DAYS,
) -> int:
    """Remove snapshot subdirectories older than the retention period.

    Returns the number of snapshot directories removed. A directory is judged
    old by its modification time. If the snapshot root does not exist, nothing
    is removed and zero is returned.
    """
    if not os.path.isdir(snapshot_root):
        return 0

    cutoff = time.time() - timedelta(days=retention_days).total_seconds()
    removed = 0
    for entry in os.listdir(snapshot_root):
        candidate = os.path.join(snapshot_root, entry)
        if not os.path.isdir(candidate):
            continue
        if os.path.getmtime(candidate) < cutoff:
            try:
                shutil.rmtree(candidate)
                removed += 1
            except OSError:
                continue
    return removed
