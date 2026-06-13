"""Tests for workspace path confinement."""

from __future__ import annotations

import os

import pytest

from agent.workspace import (
    PathOutsideWorkspace,
    resolve_within_workspace,
    set_workspace_root,
    get_workspace_root,
)
from agent.tools.read_file import read_file
from agent.tools.write_file import write_file
from agent.tools.edit_file import edit_file


def test_path_inside_root_is_allowed(tmp_path):
    target = tmp_path / "file.txt"
    target.write_text("x")
    resolved = resolve_within_workspace(str(target), root=str(tmp_path))
    assert resolved == os.path.realpath(str(target))


def test_relative_path_resolves_within_root(tmp_path):
    (tmp_path / "sub").mkdir()
    resolved = resolve_within_workspace("sub/file.txt", root=str(tmp_path))
    assert resolved.startswith(os.path.realpath(str(tmp_path)) + os.sep)


def test_parent_traversal_is_refused(tmp_path):
    with pytest.raises(PathOutsideWorkspace):
        resolve_within_workspace("../escape.txt", root=str(tmp_path))


def test_absolute_path_outside_root_is_refused(tmp_path):
    with pytest.raises(PathOutsideWorkspace):
        resolve_within_workspace("/etc/passwd", root=str(tmp_path))


def test_sibling_with_shared_prefix_is_refused(tmp_path):
    root = tmp_path / "work"
    root.mkdir()
    sibling = tmp_path / "work-evil"
    sibling.mkdir()
    (sibling / "f.txt").write_text("x")
    with pytest.raises(PathOutsideWorkspace):
        resolve_within_workspace(str(sibling / "f.txt"), root=str(root))


def test_symlink_escaping_root_is_refused(tmp_path):
    root = tmp_path / "work"
    root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("secret")
    link = root / "link.txt"
    os.symlink(str(outside), str(link))
    with pytest.raises(PathOutsideWorkspace):
        resolve_within_workspace(str(link), root=str(root))


def test_root_itself_is_allowed(tmp_path):
    resolved = resolve_within_workspace(str(tmp_path), root=str(tmp_path))
    assert resolved == os.path.realpath(str(tmp_path))


def test_read_file_refuses_path_outside_root(tmp_path):
    root = tmp_path / "work"
    root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("secret")
    set_workspace_root(str(root))
    try:
        result = read_file(str(outside))
        assert "PATH_REFUSED" in result
    finally:
        set_workspace_root(None)


def test_write_file_refuses_path_outside_root(tmp_path):
    root = tmp_path / "work"
    root.mkdir()
    outside = tmp_path / "should_not_appear.txt"
    set_workspace_root(str(root))
    try:
        result = write_file(str(outside), "data")
        assert "PATH_REFUSED" in result
        assert not outside.exists()
    finally:
        set_workspace_root(None)


def test_write_file_allows_path_inside_root(tmp_path):
    root = tmp_path / "work"
    root.mkdir()
    inside = root / "created.txt"
    set_workspace_root(str(root))
    try:
        result = write_file(str(inside), "data")
        assert "PATH_REFUSED" not in result
        assert inside.read_text() == "data"
    finally:
        set_workspace_root(None)


def test_edit_file_refuses_path_outside_root(tmp_path):
    root = tmp_path / "work"
    root.mkdir()
    outside = tmp_path / "outside.py"
    outside.write_text("greeting = 'hello'\n")
    set_workspace_root(str(root))
    try:
        result = edit_file(str(outside), "hello", "goodbye")
        assert "PATH_REFUSED" in result
        assert outside.read_text() == "greeting = 'hello'\n"
    finally:
        set_workspace_root(None)
