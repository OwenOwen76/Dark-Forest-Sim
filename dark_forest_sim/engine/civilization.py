from dataclasses import dataclass
from enum import Enum
from dataclasses import dataclass, field
from math import isfinite


from .space import Position


class CivilizationStatus(str, Enum):
    ACTIVE = "active"
    SLEEPING = "sleeping"
    DESTROYED = "destroyed"


@dataclass(slots=True)
class CivilizationResources:
    """Persistent economic and demographic state."""

    population: int = 0
    annual_population_growth_rate: float = 0.0
    energy_production_watts: float = 0.0
    energy_reserve_joules: float = 0.0
    energy_consumption_watts_per_person: float = 0.0


    def __post_init__(self):
        if (
            isinstance(self.population, bool)
            or not isinstance(self.population, int)
            or self.population < 0
        ):
            raise ValueError("Population must be a non-negative integer.")

        values = {
            "Population growth rate": self.annual_population_growth_rate,
            "Energy production": self.energy_production_watts,
            "Energy reserves": self.energy_reserve_joules,
            "Energy consumption per person":
                self.energy_consumption_watts_per_person,
        }

        for name, value in values.items():
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ValueError(f"{name} must be numeric.")
            if not isfinite(value):
                raise ValueError(f"{name} must be finite.")

        if self.annual_population_growth_rate <= -1:
            raise ValueError("Population growth rate must be greater than -1.")

        if self.energy_production_watts < 0:
            raise ValueError("Energy production must be non-negative.")

        if self.energy_reserve_joules < 0:
            raise ValueError("Energy reserves must be non-negative.")

        if self.energy_consumption_watts_per_person < 0:
            raise ValueError("Energy consumption must be non-negative.")

@dataclass(slots=True)
class Civilization:
    """Represents a civilization and its capital planet."""

    id: str
    name: str
    position: Position
    year: int
    status: CivilizationStatus = CivilizationStatus.ACTIVE
    resources: CivilizationResources = field(
        default_factory=CivilizationResources
    )

    def __post_init__(self):
        if not self.id.strip():
            raise ValueError("Civilization ID cannot be empty.")

        if not self.name.strip():
            raise ValueError("Civilization name cannot be empty.")

        if isinstance(self.year, bool) or not isinstance(self.year, int):
            raise TypeError("Civilization year must be an integer.")
