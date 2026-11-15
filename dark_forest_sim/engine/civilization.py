from dataclasses import dataclass
from enum import Enum

from .space import Position


class CivilizationStatus(str, Enum):
    ACTIVE = "active"
    SLEEPING = "sleeping"
    DESTROYED = "destroyed"


@dataclass(slots=True)
class Civilization:
    """Represents a civilization and its capital planet."""

    id: str
    name: str
    position: Position
    year: int
    status: CivilizationStatus = CivilizationStatus.ACTIVE

    def __post_init__(self):
        if not self.id.strip():
            raise ValueError("Civilization ID cannot be empty.")

        if not self.name.strip():
            raise ValueError("Civilization name cannot be empty.")

        if isinstance(self.year, bool) or not isinstance(self.year, int):
            raise TypeError("Civilization year must be an integer.")
