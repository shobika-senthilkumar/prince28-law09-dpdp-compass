import json
from pathlib import Path
from typing import Any


class RecordStore:
    """Load and access compliance records from a JSON file."""

    def __init__(self, data_file: Path) -> None:
        self.data_file = data_file
        self._records: list[dict[str, Any]] = []

    def load(self) -> None:
        """Load records from the configured JSON file."""
        with self.data_file.open("r", encoding="utf-8") as file:
            self._records = json.load(file)

    def all(self) -> list[dict[str, Any]]:
        """Return all loaded records."""
        return self._records

    def get(self, record_id: str) -> dict[str, Any] | None:
        """Return a record by ID."""
        return next(
            (record for record in self._records if record.get("id") == record_id),
            None,
        )

    @property
    def count(self) -> int:
        """Return the number of loaded records."""
        return len(self._records)
