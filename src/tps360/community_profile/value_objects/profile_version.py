from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProfileVersion:
    major: int = 0
    minor: int = 0
    patch: int = 0

    def __post_init__(self) -> None:
        if min(self.major, self.minor, self.patch) < 0:
            raise ValueError("version")

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def next_minor(self) -> ProfileVersion:
        return ProfileVersion(self.major, self.minor + 1, 0)

    def next_patch(self) -> ProfileVersion:
        return ProfileVersion(self.major, self.minor, self.patch + 1)
