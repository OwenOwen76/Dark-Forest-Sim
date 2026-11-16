from dataclasses import dataclass
from math import sqrt, isfinite


@dataclass(frozen=True, slots=True)
class Position:
    """A position in three-dimensional space, measured in light-years."""

    x: float
    y: float
    z: float

    def __post_init__(self):
        for name, value in (
            ("x", self.x),
            ("y", self.y),
            ("z", self.z),
        ):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"Coordinate {name} must be numeric.")

            if not isfinite(value):
                raise ValueError(f"Coordinate {name} must be finite.")

    def distance_to(self, other: "Position") -> float:
        """Calculate the Euclidean distance to another position."""
        return sqrt(
            (self.x - other.x) ** 2
            + (self.y - other.y) ** 2
            + (self.z - other.z) ** 2
        )
