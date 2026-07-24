from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class SourceAttribution:
    source_name: str
    license_name: str
    attribution_text: str
    source_url: str
    data_date: date

    def __post_init__(self) -> None:
        if not all(
            (
                self.source_name.strip(),
                self.license_name.strip(),
                self.attribution_text.strip(),
                self.source_url.strip(),
            )
        ):
            raise ValueError("Attribution text required")
        if (
            self.source_name.lower() == "openstreetmap"
            and "OpenStreetMap" not in self.attribution_text
        ):
            raise ValueError("OSM attribution required")
