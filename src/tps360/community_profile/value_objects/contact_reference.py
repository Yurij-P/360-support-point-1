import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ContactReference:
    reference_id: str
    label: str
    access_level: str

    def __post_init__(self) -> None:
        if not all(
            (self.reference_id.strip(), self.label.strip(), self.access_level.strip())
        ) or re.search(r"@|\+?\d[\d -]{6,}", self.reference_id + self.label):
            raise ValueError("contact")
