import hashlib
import json
from collections.abc import Mapping
from datetime import datetime
from uuid import UUID


def generate_context_checksum(context_data: Mapping[str, object]) -> str:
    """Generate a deterministic SHA-256 checksum from non-secret context data."""
    normalized_data = _normalize(context_data)
    serialized_data = json.dumps(
        normalized_data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(serialized_data.encode("utf-8")).hexdigest()


def _normalize(value: object) -> object:
    if isinstance(value, UUID | datetime):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _normalize(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_normalize(item) for item in value]
    return value