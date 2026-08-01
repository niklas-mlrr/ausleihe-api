from __future__ import annotations

from ausleihe._util import encode_path_segment
from ausleihe.admin import AdminAPI
from ausleihe.books import BookAPI
from ausleihe.schoolyears import SchoolyearsAPI
from ausleihe.series import SeriesAPI


class Client:
    def __init__(self):
        self.paths = []

    def get(self, path, **kwargs):
        self.paths.append(path)
        if path.startswith("/books/"):
            return {"code": "x"}
        if path.startswith("/series/"):
            return {"isbn": "x", "title": "x"}
        return {}

    def put(self, path, **kwargs):
        self.paths.append(path)
        return {}

    def _get_binary(self, path, **kwargs):
        self.paths.append(path)
        return b""


def test_path_segment_encodes_slashes_and_query_characters():
    assert encode_path_segment("a/b ?") == "a%2Fb%20%3F"


def test_dynamic_codes_are_encoded_once():
    client = Client()
    BookAPI(client).get_by_code("a/b")
    SeriesAPI(client).get_by_isbn("978/abc")
    AdminAPI(client).get_student_id("x?y")
    SchoolyearsAPI(client).get_by_id("2025/2026")
    SchoolyearsAPI(client).get_booklist("2025/2026", "x/y")
    AdminAPI(client).get_booklist_pdf("2025/2026", "x/y")
    assert client.paths == [
        "/books/a%2Fb",
        "/series/978%2Fabc",
        "/studentids/x%3Fy",
        "/schoolyears/2025%2F2026",
        "/schoolyears/2025%2F2026/booklists/x%2Fy",
        "schoolyears/2025%2F2026/booklists/x%2Fy/pdf",
    ]
