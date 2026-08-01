from __future__ import annotations

from pathlib import Path

import pytest

from ausleihe.inventory_excel import atomic_save_workbook, match_book

BOOKS = [
    {"isbn": "one", "title": "Mathe Grundlagen", "subjects": ["Mathe"]},
    {"isbn": "two", "title": "Mathe Erweiterung", "subjects": ["Mathe"]},
]


def test_ambiguous_subject_needs_override():
    result = match_book(BOOKS, "Mathe", None)
    assert result.book is None
    assert "Mehrdeutiger" in result.error
    assert match_book(BOOKS, "Mathe", None, override_isbn="two").book["isbn"] == "two"


def test_hint_can_select_one_book():
    result = match_book(BOOKS, "Mathe", "Erweiterung")
    assert result.book and result.book["isbn"] == "two"


class Workbook:
    def __init__(self, content: bytes = b"new"):
        self.content = content

    def save(self, path):
        Path(path).write_bytes(self.content)


def test_atomic_save_replaces_only_after_success_and_creates_backup(tmp_path):
    target = tmp_path / "bestand.xlsx"
    target.write_bytes(b"old")
    backup = atomic_save_workbook(Workbook(), target, backup_dir=tmp_path / "backups")
    assert target.read_bytes() == b"new"
    assert backup and backup.read_bytes() == b"old"


def test_atomic_save_failure_keeps_original(tmp_path):
    target = tmp_path / "bestand.xlsx"
    target.write_bytes(b"old")

    class FailingWorkbook:
        def save(self, _):
            raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        atomic_save_workbook(FailingWorkbook(), target)
    assert target.read_bytes() == b"old"
