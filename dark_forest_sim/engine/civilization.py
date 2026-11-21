from dataclasses import dataclass, field
from enum import Enum
from math import isfinite

from .space import Position


class CivilizationStatus(str, Enum):
    ACTIVE = "active"
    SLEEPING = "sleeping"
    DESTROYED = "destroyed"


def _validate_numeric(value: object, name: str) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
    ):
        raise TypeError(f"{name} must be numeric.")

    if not isfinite(value):
        raise ValueError(f"{name} must be finite.")


@dataclass(slots=True)
class DemographicsState:
    """Authoritative demographic state."""

    population: int = 0
    annual_population_growth_rate: float = 0.0

    def __post_init__(self):
        if isinstance(self.population, bool) or not isinstance(
            self.population, int
        ):
            raise TypeError("Population must be an integer.")

        _validate_numeric(
            self.annual_population_growth_rate,
            "Population growth rate",
        )


@dataclass(slots=True)
class EnergyState:
    """Authoritative energy state."""

    energy_production_watts: float = 0.0
    energy_reserve_joules: float = 0.0
    energy_consumption_watts_per_person: float = 0.0

    def __post_init__(self):
        _validate_numeric(
            self.energy_production_watts,
            "Energy production",
        )
        _validate_numeric(
            self.energy_reserve_joules,
            "Energy reserves",
        )
        _validate_numeric(
            self.energy_consumption_watts_per_person,
            "Energy consumption per person",
        )


@dataclass(slots=True)
class CivilizationState:
    """The authoritative internal state of a civilization."""

    demographics: DemographicsState = field(
        default_factory=DemographicsState
    )
    energy: EnergyState = field(
        default_factory=EnergyState
    )

    def __post_init__(self):
        if not isinstance(self.demographics, DemographicsState):
            raise TypeError(
                "demographics must be a DemographicsState."
            )

        if not isinstance(self.energy, EnergyState):
            raise TypeError("energy must be an EnergyState.")


@dataclass(slots=True)
class Civilization:
    """Represents a civilization and its reference position."""

    id: str
    name: str
    position: Position
    year: int
    status: CivilizationStatus = CivilizationStatus.ACTIVE
    state: CivilizationState = field(
        default_factory=CivilizationState
    )

    def __post_init__(self):
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("Civilization ID cannot be empty.")

        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Civilization name cannot be empty.")

        if isinstance(self.year, bool) or not isinstance(self.year, int):
            raise TypeError("Civilization year must be an integer.")

        if not isinstance(self.position, Position):
            raise TypeError("position must be a Position.")

        if not isinstance(self.state, CivilizationState):
            raise TypeError("state must be a CivilizationState.")

        self.status = CivilizationStatus(self.status)
