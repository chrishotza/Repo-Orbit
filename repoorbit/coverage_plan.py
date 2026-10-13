"""Deterministic, resumable *calendar-slot* coverage planning.

The earlier scheduled jobs reread the first N pending references forever.
This planner selects a different bounded page on each UTC date without
stateful tokens, write permission, or modifying the approved corpus.

A stable queue with K pages gets a complete scheduled sweep in K successful
daily executions. Changes to the queue, missed runs or unresolved sources can
invalidate that guarantee. Never equate "attempted" with "verified".
"""
from __future__ import annotations

from datetime import date
from math import ceil
from typing import Any

BASE_DATE = date(2026, 10, 13)


def plan(items: list[str], limit: int, cycle_date: str | None = None) -> dict[str, Any]:
    if type(limit) is not int or not 1 <= limit <= 25:
        raise ValueError("page limit must be 1..25")
    if not isinstance(items, list) or any(
        not isinstance(x, str) or not x for x in items
    ):
        raise ValueError("queue must be a list of nonempty slugs")
    # Queue building/validation occurs elsewhere; avoid sorting/copying at every
    # page. Checking order costs O(N), but each request is only one bounded page.
    if any(left >= right for left, right in zip(items, items[1:])):
        raise ValueError("queue must be strictly sorted and unique")
    count = len(items)
    pages = ceil(count / limit) if count else 0
    if cycle_date is None:
        day = 0
        scheduled = False
    else:
        if type(cycle_date) is not str:
            raise ValueError("cycle date must be YYYY-MM-DD")
        try:
            observed = date.fromisoformat(cycle_date)
        except ValueError as exc:
            raise ValueError("cycle date must be YYYY-MM-DD") from exc
        if observed.isoformat() != cycle_date or observed < BASE_DATE:
            raise ValueError("invalid or pre-baseline cycle date")
        day = (observed - BASE_DATE).days
        scheduled = True
    index = day % pages if pages else 0
    start = index * limit
    return {
        "items": items[start:start + limit],
        "queue_total": count,
        "page_size": limit,
        "pages": pages,
        "page_index": index,
        "page_start": start,
        "scheduled": scheduled,
        "cycle_date": cycle_date,
        "next_page_index": (index + 1) % pages if pages else None,
        "scope": "attempted_daily_rotation_not_cumulative_verification",
    }
