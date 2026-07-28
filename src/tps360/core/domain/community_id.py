"""Canonical community identifier type (ADR-0016, stage 1 — type foundation).

The platform is migrating community identity from opaque UUIDs to the official
KATOTTG code (ADR-0014). `CommunityId` is the canonical alias; helpers validate
and normalize KATOTTG codes. No behaviour change yet — later stages adopt this
type across the domain, ORM and API.

A KATOTTG code is "UA" + 17 digits, e.g. "UA48060030000037887".
"""
from __future__ import annotations

import re

CommunityId = str

_KATOTTG_RE = re.compile(r"^ua\d{17}$")


def normalize_community_id(value: str) -> str:
    """Canonical form of a community id (trimmed, lower-case)."""
    return value.strip().lower()


def is_katottg_code(value: str) -> bool:
    """Whether the value is a well-formed KATOTTG code (UA + 17 digits)."""
    return bool(_KATOTTG_RE.match(normalize_community_id(value)))
