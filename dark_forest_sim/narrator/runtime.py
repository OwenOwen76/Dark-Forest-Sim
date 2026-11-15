from dataclasses import dataclass, field

from ..engine.scheduler import CivilizationScheduler
from ..engine.universe import Universe
from .registry import NarratorToolbox


@dataclass(slots=True)
class NarratorRuntime:
    universe: Universe = field(default_factory=Universe)
    scheduler: CivilizationScheduler = field(
        default_factory=CivilizationScheduler
    )
    toolbox: NarratorToolbox = field(init=False)

    def __post_init__(self):
        self.toolbox = NarratorToolbox(
            self.universe,
            self.scheduler,
        )
