"""Unit-Tests für die from_dict-Parser. Reine Fixtures, kein Netzwerk/Produktion.

Sichern die gotcha-lastigen Parsing-Regeln ab (BookView-Merge, Groß-/Kleinschreibung,
String-zu-Int, [{"grade": 5}]-Format, flache Arrays).

    python3 -m pytest tests/ -q
"""
from __future__ import annotations

from datetime import datetime

from ausleihe.models import Book, BorrowingRule, Series, Student


# ----------------------------------------------------------------------
# Book
# ----------------------------------------------------------------------

def test_book_basic_and_string_ints():
    b = Book.from_dict({
        "code": "00015193",
        "isbn": "9783062301261",
        "available": False,
        "distributed": True,
        "issuances": "5",          # API liefert String
        "long_issuances": "4",     # API liefert String
        "student": 2304,           # numerische ID
        "distributed_at": "2025-07-07T09:13:05.000Z",
    })
    assert b.code == "00015193"
    assert b.issuances == 5 and isinstance(b.issuances, int)
    assert b.long_issuances == 4
    assert b.student_id == 2304
    assert b.student is None  # kein "Student"-Objekt im Payload
    assert isinstance(b.distributed_at, datetime)


def test_book_bookview_merge_and_uppercase_student():
    # /students/:id/books verschachtelt die Buchdaten in "BookView"
    b = Book.from_dict({
        "BookView": {
            "code": "00099999",
            "isbn": "111",
            "available": True,
            "issuances": "0",
        },
        "series": {"isbn": "111", "title": "Mathe 5", "publisher": "Klett",
                   "price": "10", "fee": "3"},
        "Student": {"id": 1, "firstname": "Max", "lastname": "M", "iserv_act": "max.m"},
    })
    assert b.code == "00099999"      # aus BookView hochgezogen
    assert b.available is True
    assert b.series is not None and b.series.title == "Mathe 5"
    assert b.student is not None and b.student.firstname == "Max"


def test_book_missing_student_key():
    b = Book.from_dict({"code": "x", "issuances": None, "long_issuances": None})
    assert b.student_id is None
    assert b.issuances == 0  # None -> 0


# ----------------------------------------------------------------------
# Series
# ----------------------------------------------------------------------

def test_series_grade_subject_object_format():
    s = Series.from_dict({
        "isbn": "978",
        "title": "Bio 7",
        "publisher": "Cornelsen",
        "price": 33.99,
        "fee": 11.2,
        "grades": [{"grade": 5}, {"grade": 6}],
        "subjects": [{"subject": "Biologie"}],
        "total": 100,
        "available": 12,
    })
    assert s.grades == [5, 6]
    assert s.subjects == ["Biologie"]
    assert s.total == 100 and s.available == 12


def test_series_flat_and_meta_fields():
    s = Series.from_dict({
        "isbn": "978",
        "title": "Bio 7",
        "gradesFlat": [5, 6],
        "subjectsFlat": ["Biologie"],
        "isMultiYear": True,
        "abolished_at": "2024-01-01T00:00:00.000Z",
        "abolished_by": "admin",
    })
    assert s.grades_flat == [5, 6]
    assert s.subjects_flat == ["Biologie"]
    assert s.is_multi_year is True
    assert isinstance(s.abolished_at, datetime)
    assert s.abolished_by == "admin"


# ----------------------------------------------------------------------
# Student
# ----------------------------------------------------------------------

def test_student_dates_and_new_fields():
    s = Student.from_dict({
        "id": 2167,
        "firstname": "Erika",
        "lastname": "Muster",
        "iserv_act": "erika.muster",
        "date_of_birth": "2010-05-01T00:00:00.000Z",
        "left": None,
        "import_profile": 3,
        "created_by": "jens.puehn",
    })
    assert s.id == 2167
    assert isinstance(s.date_of_birth, datetime)
    assert s.left is None
    assert s.import_profile == 3
    assert s.created_by == "jens.puehn"


# ----------------------------------------------------------------------
# BorrowingRule
# ----------------------------------------------------------------------

def test_borrowing_rule():
    r = BorrowingRule.from_dict({
        "id": 1,
        "text": "<p>Regeltext</p>",
        "created_at": "2023-01-01T00:00:00.000Z",
    })
    assert r.id == 1
    assert r.text == "<p>Regeltext</p>"
    assert isinstance(r.created_at, datetime)
