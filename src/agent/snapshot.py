"""Automatic file-content snapshotting of files modified during a task."""

from __future__ import annotations

import os
import shutil
import time
from datetime import datetime, timedelta


DEFAULT_SNAPSHOT_ROOT = os.path.expanduser("~/.local-coding-agent/snapshots")
RETENTION_DAYS = 30


def take_snapshot(
    paths: list[str],
    snapshot_root: str = DEFAULT_SNAPSHOT_ROOT,
) -> str | None:
    """Copy the current content of the given files into a timestamped snapshot.

    Each call creates a subdirectory named for the current time and copies
    each existing path into it, preserving the file's basename. Files that no
    longer exist are skipped. Returns the path of the snapshot directory
    created, or None if there were no files to capture.
    """
    existing = [path for path in paths if os.path.isfile(path)]
    if not existing:
        return None

    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
    snapshot_dir = os.path.join(snapshot_root, stamp)
    os.makedirs(snapshot_dir, exist_ok=True)

    for path in existing:
        basename = os.path.basename(path)
        destination = os.path.join(snapshot_dir, basename)
        try:
            shutil.copy2(path, destination)
        except OSError:
            # A file that cannot be copied is skipped rather than aborting
            # the whole snapshot.
            continue

    return snapshot_dir


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
