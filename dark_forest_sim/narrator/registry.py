from dataclasses import dataclass
from typing import Any, Callable

from ..engine.scheduler import CivilizationScheduler
from ..engine.universe import Universe
from . import data, physics, world


@dataclass(slots=True)
class Tool:
    name: str
    description: str
    category: str
    parameters: dict
    handler: Callable


class NarratorToolbox:
    """Provides the narrator with controlled access to simulation tools."""

    def __init__(
        self,
        universe: Universe,
        scheduler: CivilizationScheduler,
        on_change: Callable[[], None] | None = None,
    ):
        self._universe = universe
        self._scheduler = scheduler
        self._tools: dict[str, Tool] = {}
        self._on_change = on_change

        self._register_tools()

    def _register(
        self,
        name: str,
        description: str,
        category: str,
        properties: dict,
        handler: Callable,
        required: list[str] | None = None,
    ):
        self._tools[name] = Tool(
            name=name,
            description=description,
            category=category,
            parameters={
                "type": "object",
                "properties": properties,
                "required": required or [],
                "additionalProperties": False,
            },
            handler=handler,
        )

    def _register_tools(self):
        u = self._universe
        s = self._scheduler

        # World Modification Toolbox

        self._register(
            "create_civilization",
            "Create a civilization at a capital planet.",
            "world",
            {
                "civilization_id": {"type": "string"},
                "name": {"type": "string"},
                "x": {"type": "number"},
                "y": {"type": "number"},
                "z": {"type": "number"},
                "year": {"type": "integer"},
            },
            lambda **kw: world.create_civilization(u, **kw),
            ["civilization_id", "name", "x", "y", "z", "year"],
        )

        self._register(
            "modify_civilization",
            "Modify a civilization's name or capital position.",
            "world",
            {
                "civilization_id": {"type": "string"},
                "name": {"type": "string"},
                "x": {"type": "number"},
                "y": {"type": "number"},
                "z": {"type": "number"},
            },
            lambda **kw: world.modify_civilization(u, **kw),
            ["civilization_id"],
        )

        self._register(
            "destroy_civilization",
            "Destroy a civilization.",
            "world",
            {"civilization_id": {"type": "string"}},
            lambda **kw: world.destroy_civilization(u, s, **kw),
            ["civilization_id"],
        )

        self._register(
            "create_event",
            "Create an event. This does not automatically propagate it.",
            "world",
            {
                "event_id": {"type": "string"},
                "event_type": {"type": "string"},
                "created_at": {"type": "number"},
                "description": {"type": "string"},
                "x": {"type": "number"},
                "y": {"type": "number"},
                "z": {"type": "number"},
                "propagation_speed": {"type": "number"},
                "target_civilization_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            lambda **kw: world.create_event(u, **kw),
            [
                "event_id",
                "event_type",
                "created_at",
                "description",
                "x",
                "y",
                "z",
                "propagation_speed",
            ],
        )

        self._register(
            "propagate_event",
            "Propagate an event to its designated recipients.",
            "world",
            {"event_id": {"type": "string"}},
            lambda **kw: world.propagate_event(u, **kw),
            ["event_id"],
        )

        self._register(
            "advance_time",
            "Advance the internal universe timeline to an absolute time.",
            "world",
            {"to_time": {"type": "number"}},
            lambda **kw: world.advance_time(u, **kw),
            ["to_time"],
        )

        self._register(
            "sleep_civilization",
            "Put a civilization to sleep for a positive integer number of years.",
            "world",
            {
                "civilization_id": {"type": "string"},
                "years": {"type": "integer"},
            },
            lambda **kw: world.sleep_civilization(u, s, **kw),
            ["civilization_id", "years"],
        )

        self._register(
            "wake_civilization",
            "Wake a sleeping civilization. Interrupt allows an early wake.",
            "world",
            {
                "civilization_id": {"type": "string"},
                "interrupt": {"type": "boolean"},
            },
            lambda **kw: world.wake_civilization(u, s, **kw),
            ["civilization_id"],
        )

        self._register(
            "advance_when_idle",
            "Advance to the next scheduled wake or pending event arrival.",
            "world",
            {},
            lambda **kw: world.advance_when_idle(u, s),
        )

        # Mathematics & Data Toolbox

        self._register(
            "get_universe_status",
            "Read a summary of the universe's current state.",
            "data",
            {},
            lambda **kw: data.get_universe_status(u),
        )

        self._register(
            "list_civilizations",
            "List all civilizations and their public simulation state.",
            "data",
            {},
            lambda **kw: data.list_civilizations(u),
        )

        self._register(
            "inspect_civilization",
            "Inspect a civilization's current state.",
            "data",
            {"civilization_id": {"type": "string"}},
            lambda **kw: data.inspect_civilization(u, **kw),
            ["civilization_id"],
        )

        self._register(
            "list_events",
            "List all recorded events.",
            "data",
            {},
            lambda **kw: data.list_events(u),
        )

        self._register(
            "inspect_event",
            "Inspect an event and its deliveries.",
            "data",
            {"event_id": {"type": "string"}},
            lambda **kw: data.inspect_event(u, **kw),
            ["event_id"],
        )

        self._register(
            "list_deliveries",
            "List all event deliveries and their statuses.",
            "data",
            {},
            lambda **kw: data.list_deliveries(u),
        )

        self._register(
            "calculate_distance",
            "Calculate the distance between two 3D positions in light-years.",
            "data",
            {
                "x1": {"type": "number"},
                "y1": {"type": "number"},
                "z1": {"type": "number"},
                "x2": {"type": "number"},
                "y2": {"type": "number"},
                "z2": {"type": "number"},
            },
            data.calculate_distance,
            ["x1", "y1", "z1", "x2", "y2", "z2"],
        )

        self._register(
            "calculate_travel_time",
            "Calculate travel time in years from distance and speed.",
            "data",
            {
                "distance": {"type": "number"},
                "speed": {"type": "number"},
            },
            data.calculate_travel_time,
            ["distance", "speed"],
        )

        self._register(
            "calculate_signal_detection_range",
            "Calculate how far a signal can be detected against background noise, in light-years.",
            "data",
            {
                "signal_power_at_1_ly": {"type": "number"},
                "background_noise": {"type": "number"},
                "detection_threshold": {"type": "number"},
            },
            physics.calculate_detection_range,
            [
                "signal_power_at_1_ly",
                "background_noise",
                "detection_threshold",
            ],
        )

        self._register(
            "calculate_waste_heat_power",
            "Calculate average waste heat output in watts.",
            "data",
            {
                "energy_joules": {"type": "number"},
                "waste_heat_fraction": {"type": "number"},
                "duration_seconds": {"type": "number"},
            },
            physics.calculate_waste_heat_power,
            [
                "energy_joules",
                "waste_heat_fraction",
                "duration_seconds",
            ],
        )

        self._register(
            "calculate_infrared_detection_range",
            "Calculate how far waste heat can be detected in light-years.",
            "data",
            {
                "heat_power_watts": {"type": "number"},
                "detection_threshold_watts_per_square_meter": {
                    "type": "number"
                },
            },
            physics.calculate_infrared_detection_range,
            [
                "heat_power_watts",
                "detection_threshold_watts_per_square_meter",
            ],
        )

        self._register(
            "calculate_cooling_duration",
            "Calculate how long a civilization needs to cool its waste heat, in seconds.",
            "data",
            {
                "energy_joules": {"type": "number"},
                "waste_heat_fraction": {"type": "number"},
                "cooling_power_watts": {"type": "number"},
            },
            physics.calculate_cooling_duration,
            [
                "energy_joules",
                "waste_heat_fraction",
                "cooling_power_watts",
            ],
        )

        self._register(
            "calculate_signal_travel_time",
            "Calculate signal travel time in years, given distance in light-years and speed as a fraction of c.",
            "data",
            {
                "distance_light_years": {"type": "number"},
                "speed_fraction_of_c": {"type": "number"},
            },
            physics.calculate_signal_travel_time,
            ["distance_light_years", "speed_fraction_of_c"],
        )

        self._register(
            "calculate_signal_arrival_time",
            "Calculate the arrival time of a signal using its departure time, distance in light-years, and speed as a fraction of c.",
            "data",
            {
                "departure_time": {"type": "number"},
                "distance_light_years": {"type": "number"},
                "speed_fraction_of_c": {"type": "number"},
            },
            physics.calculate_signal_arrival_time,
            ["departure_time", "distance_light_years", "speed_fraction_of_c"],
        )

    def list_tools(self) -> list[dict]:
        """Return tool information grouped by category."""

        return [
            {
                "name": tool.name,
                "description": tool.description,
                "category": tool.category,
                "parameters": tool.parameters,
            }
            for tool in self._tools.values()
        ]

    def get_definitions(self) -> list[dict]:
        """Return OpenAI-compatible function definitions."""

        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for tool in self._tools.values()
        ]

    def call(self, name: str, arguments: dict[str, Any]) -> dict:
        """Execute a registered tool by name."""

        tool = self._tools.get(name)

        if tool is None:
            return {
                "ok": False,
                "error": f"Unknown tool: {name}",
            }

        if not isinstance(arguments, dict):
            return {
                "ok": False,
                "error": "Tool arguments must be an object.",
            }

        properties = tool.parameters["properties"]
        required = tool.parameters["required"]

        missing = [
            key for key in required
            if key not in arguments
        ]

        unexpected = [
            key for key in arguments
            if key not in properties
        ]

        if missing:
            return {
                "ok": False,
                "error": f"Missing required arguments: {missing}",
            }

        if unexpected:
            return {
                "ok": False,
                "error": f"Unexpected arguments: {unexpected}",
            }

        try:
            result = tool.handler(**arguments)

            if tool.category == "world" and self._on_change is not None:
                self._on_change()

            return {
                "ok": True,
                "tool": name,
                "result": result,
            }

        except (ValueError, TypeError, KeyError) as exc:
            return {
                "ok": False,
                "tool": name,
                "error": str(exc),
            }
