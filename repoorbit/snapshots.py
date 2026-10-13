"""Authoritative active-source snapshot manifest.

Historical JSONL snapshots remain in Git, but do not inflate current search or
coverage. Only a rights-reviewed, pinned feed baseline is indexed.
"""
from __future__ import annotations

import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SAFE_PATH = re.compile(r"data/discoveries/[a-z0-9][a-z0-9-]*\.jsonl\Z")


def approved_discoveries() -> list[Path]:
    registry = json.loads((ROOT / "data" / "feeds.json").read_text(encoding="utf-8"))
    if registry.get("schema_version") != "0.1.0":
        raise ValueError("unsupported approved-feed registry")
    result = []
    identities = set()
    baselines = set()
    for feed in registry.get("sources", []):
        source = feed.get("repository")
        if not isinstance(source, str) or feed.get("id") != "github:" + source.casefold():
            raise ValueError("invalid approved-feed source identity")
        if feed["id"] in identities:
            raise ValueError("duplicate approved source")
        identities.add(feed["id"])
        relative = feed.get("baseline")
        if not isinstance(relative, str) or SAFE_PATH.fullmatch(relative) is None:
            raise ValueError("invalid approved snapshot path")
        if relative in baselines:
            raise ValueError("duplicate approved snapshot path")
        baselines.add(relative)
        path = ROOT / relative
        if not path.is_file():
            raise ValueError("approved snapshot does not exist: " + relative)
        result.append(path)
    if not result:
        raise ValueError("no approved discovery feeds")
    return result
