from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


def _parse_dt(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    # API returns ISO 8601 with trailing Z
    s = s.replace("Z", "+00:00")
    return datetime.fromisoformat(s)


@dataclass
class Student:
    id: int
    firstname: str
    lastname: str
    iserv_act: str
    date_of_birth: Optional[datetime]
    left: Optional[datetime]
    anonymized_at: Optional[datetime]
    import_id: Optional[str]
    created_at: Optional[datetime]
    import_profile: Optional[int] = None
    created_by: Optional[str] = None

    @classmethod
    def from_dict(cls, d: dict) -> Student:
        return cls(
            id=d["id"],
            firstname=d["firstname"],
            lastname=d["lastname"],
            iserv_act=d.get("iserv_act", ""),
            date_of_birth=_parse_dt(d.get("date_of_birth")),
            left=_parse_dt(d.get("left")),
            anonymized_at=_parse_dt(d.get("anonymized_at")),
            import_id=d.get("import_id"),
            created_at=_parse_dt(d.get("created_at")),
            import_profile=d.get("import_profile"),
            created_by=d.get("created_by"),
        )

    def __str__(self) -> str:
        return f"{self.firstname} {self.lastname} ({self.iserv_act})"


@dataclass
class Series:
    isbn: str
    title: str
    publisher: str
    price: float
    fee: float
    abolished: bool
    grades: list[int]
    subjects: list[str]
    total: Optional[int] = None
    available: Optional[int] = None
    # API liefert zusätzlich flache Arrays und Meta-Felder
    grades_flat: list[int] = field(default_factory=list)
    subjects_flat: list[str] = field(default_factory=list)
    is_multi_year: bool = False
    last_change: Optional[datetime] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    abolished_at: Optional[datetime] = None  # nur in der /series-Liste
    abolished_by: Optional[str] = None       # nur in der /series-Liste

    @classmethod
    def from_dict(cls, d: dict) -> Series:
        raw_grades = d.get("grades") or []
        raw_subjects = d.get("subjects") or []
        # API returns [{"grade": 5}, ...] and [{"subject": "Biologie"}, ...]
        grades = [g["grade"] for g in raw_grades if "grade" in g]
        subjects = [s["subject"] for s in raw_subjects if "subject" in s]
        return cls(
            isbn=d["isbn"],
            title=d["title"],
            publisher=d.get("publisher", ""),
            price=float(d.get("price", 0)),
            fee=float(d.get("fee", 0)),
            abolished=bool(d.get("abolished", False)),
            grades=grades,
            subjects=subjects,
            total=d.get("total"),
            available=d.get("available"),
            grades_flat=list(d.get("gradesFlat") or []),
            subjects_flat=list(d.get("subjectsFlat") or []),
            is_multi_year=bool(d.get("isMultiYear", False)),
            last_change=_parse_dt(d.get("last_change")),
            created_by=d.get("created_by"),
            created_at=_parse_dt(d.get("created_at")),
            abolished_at=_parse_dt(d.get("abolished_at")),
            abolished_by=d.get("abolished_by"),
        )

    def __str__(self) -> str:
        return f"{self.title} ({self.isbn})"


@dataclass
class Book:
    code: str
    isbn: str
    available: bool
    distributed: bool
    deleted: bool
    inventory: bool
    imported: bool
    issuances: int
    long_issuances: int
    distributed_id: Optional[int]
    distributed_by: Optional[str]
    distributed_at: Optional[datetime]
    student_id: Optional[int]
    text: Optional[str]
    created_by: Optional[str]
    created_at: Optional[datetime]
    series: Optional[Series] = None
    student: Optional[Student] = None

    @classmethod
    def from_dict(cls, d: dict) -> Book:
        # /students/:id/books wraps the full book data in a "BookView" key;
        # merge it so all fields are accessible at the top level.
        if "BookView" in d:
            d = {**d, **d["BookView"]}

        series = Series.from_dict(d["series"]) if d.get("series") else None
        # JSON key is "Student" (uppercase) when nested in book response
        raw_student = d.get("Student") or d.get("student_obj")
        student = Student.from_dict(raw_student) if isinstance(raw_student, dict) else None
        return cls(
            code=d["code"],
            isbn=d.get("isbn", ""),
            available=bool(d.get("available", False)),
            distributed=bool(d.get("distributed", False)),
            deleted=bool(d.get("deleted", False)),
            inventory=bool(d.get("inventory", False)),
            imported=bool(d.get("imported", False)),
            # API returns these as strings
            issuances=int(d.get("issuances") or 0),
            long_issuances=int(d.get("long_issuances") or 0),
            distributed_id=d.get("distributed_id"),
            distributed_by=d.get("distributed_by"),
            distributed_at=_parse_dt(d.get("distributed_at")),
            # "student" field in JSON is the numeric ID
            student_id=d["student"] if isinstance(d.get("student"), int) else None,
            text=d.get("text"),
            created_by=d.get("created_by"),
            created_at=_parse_dt(d.get("created_at")),
            series=series,
            student=student,
        )

    def __str__(self) -> str:
        title = self.series.title if self.series else self.isbn
        return f"[{self.code}] {title}"


@dataclass
class BorrowingRule:
    id: int
    text: str
    created_at: Optional[datetime]

    @classmethod
    def from_dict(cls, d: dict) -> BorrowingRule:
        return cls(
            id=d["id"],
            text=d.get("text", ""),
            created_at=_parse_dt(d.get("created_at")),
        )
