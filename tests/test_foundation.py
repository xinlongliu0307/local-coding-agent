"""Tests for the Phase One foundation: the model wrapper and the first tool."""

from __future__ import annotations

import os

from agent.model import ModelClient, DEFAULT_MODEL
from agent.tools.list_files import list_files


def test_model_client_instantiates_with_default_model():
    client = ModelClient()
    assert client.model == DEFAULT_MODEL


def test_model_client_accepts_custom_model():
    client = ModelClient(model="custom-model")
    assert client.model == "custom-model"


def test_list_files_returns_known_entry(tmp_path):
    (tmp_path / "example.txt").write_text("content")
    result = list_files(str(tmp_path))
    assert "example.txt" in result


def test_list_files_handles_missing_directory():
    result = list_files("/path/that/does/not/exist")
    assert "Error" in result
