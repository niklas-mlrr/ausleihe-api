from __future__ import annotations

import time
from typing import TYPE_CHECKING

from .models import Book

if TYPE_CHECKING:
    from .client import AusleiheClient

_CACHE_TTL = 300  # seconds


class BookAPI:
    def __init__(self, client: AusleiheClient) -> None:
        self._client = client

    def get_all(self, include_deleted: bool = False) -> list[Book]:
        cache = self._client._books_cache
        if cache and not include_deleted and time.time() - cache[1] < _CACHE_TTL:
            return cache[0]

        params = {"deleted": "true"} if include_deleted else {}
        raw = self._client.get("/books", params=params)
        books = [Book.from_dict(d) for d in raw]

        if not include_deleted:
            self._client._books_cache = (books, time.time())

        return books

    def get_by_code(self, code: str) -> Book:
        raw = self._client.get(f"/books/{code}")
        return Book.from_dict(raw)

    def filter_by_isbn(self, isbn: str, include_deleted: bool = False) -> list[Book]:
        return [b for b in self.get_all(include_deleted) if b.isbn == isbn]

    def filter_by_student(self, student_id: int, include_deleted: bool = False) -> list[Book]:
        return [b for b in self.get_all(include_deleted) if b.student_id == student_id]

    def filter_available(self) -> list[Book]:
        return [b for b in self.get_all() if b.available and not b.deleted]

    def filter_distributed(self) -> list[Book]:
        return [b for b in self.get_all() if b.distributed and not b.deleted]

    def invalidate_cache(self) -> None:
        self._client._books_cache = None
