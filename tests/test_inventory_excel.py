from __future__ import annotations

from ausleihe.inventory_excel import match_book

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
