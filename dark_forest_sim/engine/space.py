from dataclasses import dataclass
from math import sqrt, isfinite


@dataclass(frozen=True, slots=True)
class Position:
    """A position in three-dimensional space, measured in light-years."""

    x: float
    y: float
    z: float

    def __post_init__(self):
        if not all(isfinite(v) for v in (self.x, self.y, self.z)):
            raise ValueError("Coordinates must be finite numbers.")

    def distance_to(self, other: "Position") -> float:
        """Calculate the Euclidean distance to another position."""
        return sqrt(
            (self.x - other.x) ** 2
            + (self.y - other.y) ** 2
            + (self.z - other.z) ** 2
        )
