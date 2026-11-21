from dataclasses import dataclass
from typing import Any, Callable

from ..engine.scheduler import CivilizationScheduler
from ..engine.universe import Universe
from . import data, economics, physics, technology, world


@dataclass(slots=True)
class Operation:
    description: str
    properties: dict
    required: tuple[str, ...]
    handler: Callable


@dataclass(slots=True)
class Tool:
    name: str
    description: str
    category: str
    operations: dict[str, Operation]
    parameters: dict


class NarratorToolbox:
    """Provides the narrator with a compact, operation-based toolbox."""

    def __init__(
        self,
        universe: Universe,
        scheduler: CivilizationScheduler,
        on_change: Callable[[], None] | None = None,
    ):
        self._universe = universe
        self._scheduler = scheduler
        self._on_change = on_change
        self._tools: dict[str, Tool] = {}
        self._register_tools()

    @staticmethod
    def _operation(
        description: str,
        properties: dict,
        handler: Callable,
        required: tuple[str, ...] = (),
    ) -> Operation:
        return Operation(
            description=description,
            properties=properties,
            required=required,
            handler=handler,
        )

    def _register_group(
        self,
        name: str,
        description: str,
        category: str,
        operations: dict[str, Operation],
    ) -> None:
        """Register a tool containing multiple selectable operations."""

        properties = {
            "operation": {
                "type": "string",
                "enum": list(operations),
                "description": "Operation to execute.",
            }
        }

        for operation in operations.values():
            for field_name, schema in operation.properties.items():
                existing = properties.get(field_name)

                if existing is not None and existing != schema:
                    raise ValueError(
                        f"Conflicting schemas for field {field_name!r} "
                        f"in tool {name!r}."
                    )

                properties[field_name] = schema

        self._tools[name] = Tool(
            name=name,
            description=description,
            category=category,
            operations=operations,
            parameters={
                "type": "object",
                "properties": properties,
                "required": ["operation"],
                "additionalProperties": False,
            },
        )

    def _register_tools(self) -> None:
        u = self._universe
        s = self._scheduler

        string = {"type": "string"}
        number = {"type": "number"}
        integer = {"type": "integer"}
        boolean = {"type": "boolean"}

        position_fields = {
            "x": number,
            "y": number,
            "z": number,
        }

        demographics_fields = {
            "type": "object",
            "properties": {
                "population": integer,
                "annual_population_growth_rate": number,
            },
            "additionalProperties": False,
        }

        energy_fields = {
            "type": "object",
            "properties": {
                "energy_production_watts": number,
                "energy_reserve_joules": number,
                "energy_consumption_watts_per_person": number,
            },
            "additionalProperties": False,
        }

        # ------------------------------------------------------------
        # Civilization management
        # ------------------------------------------------------------

        self._register_group(
            "manage_civilization",
            "Create, modify, update the authoritative state of, or destroy a civilization.",
            "world",
            {
                "create": self._operation(
                    "Create a civilization at a specified position and local year.",
                    {
                        "civilization_id": string,
                        "name": string,
                        **position_fields,
                        "year": integer,
                    },
                    lambda **kw: world.create_civilization(u, **kw),
                    (
                        "civilization_id",
                        "name",
                        "x",
                        "y",
                        "z",
                        "year",
                    ),
                ),
                "modify": self._operation(
                    "Modify a civilization's name or position. "
                    "All three coordinates must be supplied together.",
                    {
                        "civilization_id": string,
                        "name": string,
                        **position_fields,
                    },
                    lambda **kw: world.modify_civilization(u, **kw),
                    ("civilization_id",),
                ),
                "update_state": self._operation(
                    "Update one or more civilization state domains.",
                    {
                        "civilization_id": string,
                        "demographics": demographics_fields,
                        "energy": energy_fields,
                    },
                    lambda civilization_id, **changes: (
                        world.update_civilization_state(
                            u,
                            civilization_id,
                            **changes,
                        )
                    ),
                    ("civilization_id",),
                ),
                "destroy": self._operation(
                    "Mark a civilization as destroyed.",
                    {"civilization_id": string},
                    lambda **kw: world.destroy_civilization(u, s, **kw),
                    ("civilization_id",),
                ),
            },
        )

        # ------------------------------------------------------------
        # Event management
        # ------------------------------------------------------------

        self._register_group(
            "manage_event",
            "Create and propagate simulation events.",
            "world",
            {
                "create": self._operation(
                    "Create an event without automatically propagating it.",
                    {
                        "event_id": string,
                        "event_type": string,
                        "created_at": number,
                        "description": string,
                        **position_fields,
                        "propagation_speed": number,
                        "target_civilization_ids": {
                            "type": "array",
                            "items": string,
                        },
                    },
                    lambda **kw: world.create_event(u, **kw),
                    (
                        "event_id",
                        "event_type",
                        "created_at",
                        "description",
                        "x",
                        "y",
                        "z",
                        "propagation_speed",
                    ),
                ),
                "propagate": self._operation(
                    "Propagate an event to its designated recipients.",
                    {"event_id": string},
                    lambda **kw: world.propagate_event(u, **kw),
                    ("event_id",),
                ),
            },
        )

        # ------------------------------------------------------------
        # Simulation management
        # ------------------------------------------------------------

        self._register_group(
            "manage_simulation",
            "Control the universe timeline and civilization sleep states.",
            "world",
            {
                "advance_time": self._operation(
                    "Advance the universe timeline to an absolute time.",
                    {"to_time": number},
                    lambda **kw: world.advance_time(u, **kw),
                    ("to_time",),
                ),
                "advance_when_idle": self._operation(
                    "Advance to the next scheduled wake or pending event arrival.",
                    {},
                    lambda **kw: world.advance_when_idle(u, s),
                ),
                "sleep": self._operation(
                    "Put a civilization to sleep for a positive number of years.",
                    {
                        "civilization_id": string,
                        "years": integer,
                    },
                    lambda **kw: world.sleep_civilization(u, s, **kw),
                    ("civilization_id", "years"),
                ),
                "wake": self._operation(
                    "Wake a sleeping civilization. "
                    "Interrupt can be used to wake it early.",
                    {
                        "civilization_id": string,
                        "interrupt": boolean,
                    },
                    lambda **kw: world.wake_civilization(u, s, **kw),
                    ("civilization_id",),
                ),
            },
        )

        # ------------------------------------------------------------
        # Universe queries
        # ------------------------------------------------------------

        self._register_group(
            "query_universe",
            "Read universe, civilization, event, delivery, and knowledge state.",
            "data",
            {
                "universe_status": self._operation(
                    "Get a summary of the universe's current state.",
                    {},
                    lambda **kw: data.get_universe_status(u),
                ),
                "list_civilizations": self._operation(
                    "List all civilizations and their public state.",
                    {},
                    lambda **kw: data.list_civilizations(u),
                ),
                "inspect_civilization": self._operation(
                    "Inspect one civilization, including its authoritative state.",
                    {"civilization_id": string},
                    lambda **kw: data.inspect_civilization(u, **kw),
                    ("civilization_id",),
                ),
                "list_events": self._operation(
                    "List all recorded events.",
                    {},
                    lambda **kw: data.list_events(u),
                ),
                "inspect_event": self._operation(
                    "Inspect an event and its deliveries.",
                    {"event_id": string},
                    lambda **kw: data.inspect_event(u, **kw),
                    ("event_id",),
                ),
                "list_deliveries": self._operation(
                    "List all event deliveries and their statuses.",
                    {},
                    lambda **kw: data.list_deliveries(u),
                ),
                "event_knowledge": self._operation(
                    "Check whether an event's information has reached a civilization.",
                    {
                        "event_id": string,
                        "civilization_id": string,
                    },
                    lambda **kw: data.can_civilization_know_event(u, **kw),
                    ("event_id", "civilization_id"),
                ),
            },
        )

        # ------------------------------------------------------------
        # Mathematics and calculations
        # ------------------------------------------------------------

        self._register_group(
            "calculate",
            "Perform physics, astronomy, relativistic, technology, and economic calculations.",
            "data",
            {
                "distance": self._operation(
                    "Calculate distance between two 3D positions in light-years.",
                    {
                        "x1": number,
                        "y1": number,
                        "z1": number,
                        "x2": number,
                        "y2": number,
                        "z2": number,
                    },
                    data.calculate_distance,
                    ("x1", "y1", "z1", "x2", "y2", "z2"),
                ),
                "travel_time": self._operation(
                    "Calculate travel time in years from distance and speed.",
                    {
                        "distance": number,
                        "speed": number,
                    },
                    data.calculate_travel_time,
                    ("distance", "speed"),
                ),
                "signal_detection_range": self._operation(
                    "Calculate signal detection range in light-years.",
                    {
                        "signal_power_at_1_ly": number,
                        "background_noise": number,
                        "detection_threshold": number,
                    },
                    physics.calculate_detection_range,
                    (
                        "signal_power_at_1_ly",
                        "background_noise",
                        "detection_threshold",
                    ),
                ),
                "waste_heat_power": self._operation(
                    "Calculate average waste heat output in watts.",
                    {
                        "energy_joules": number,
                        "waste_heat_fraction": number,
                        "duration_seconds": number,
                    },
                    physics.calculate_waste_heat_power,
                    (
                        "energy_joules",
                        "waste_heat_fraction",
                        "duration_seconds",
                    ),
                ),
                "infrared_detection_range": self._operation(
                    "Calculate infrared detection range in light-years.",
                    {
                        "heat_power_watts": number,
                        "detection_threshold_watts_per_square_meter": number,
                    },
                    physics.calculate_infrared_detection_range,
                    (
                        "heat_power_watts",
                        "detection_threshold_watts_per_square_meter",
                    ),
                ),
                "cooling_duration": self._operation(
                    "Calculate cooling duration in seconds.",
                    {
                        "energy_joules": number,
                        "waste_heat_fraction": number,
                        "cooling_power_watts": number,
                    },
                    physics.calculate_cooling_duration,
                    (
                        "energy_joules",
                        "waste_heat_fraction",
                        "cooling_power_watts",
                    ),
                ),
                "signal_travel_time": self._operation(
                    "Calculate signal travel time in years.",
                    {
                        "distance_light_years": number,
                        "speed_fraction_of_c": number,
                    },
                    physics.calculate_signal_travel_time,
                    ("distance_light_years", "speed_fraction_of_c"),
                ),
                "signal_arrival_time": self._operation(
                    "Calculate the absolute arrival time of a signal.",
                    {
                        "departure_time": number,
                        "distance_light_years": number,
                        "speed_fraction_of_c": number,
                    },
                    physics.calculate_signal_arrival_time,
                    (
                        "departure_time",
                        "distance_light_years",
                        "speed_fraction_of_c",
                    ),
                ),
                "lorentz_factor": self._operation(
                    "Calculate the Lorentz factor.",
                    {"speed_fraction_of_c": number},
                    physics.calculate_lorentz_factor,
                    ("speed_fraction_of_c",),
                ),
                "relativistic_travel_time": self._operation(
                    "Calculate travel time in the universe reference frame.",
                    {
                        "distance_light_years": number,
                        "speed_fraction_of_c": number,
                    },
                    physics.calculate_relativistic_travel_time,
                    ("distance_light_years", "speed_fraction_of_c"),
                ),
                "proper_travel_time": self._operation(
                    "Calculate time experienced aboard a relativistic ship.",
                    {
                        "distance_light_years": number,
                        "speed_fraction_of_c": number,
                    },
                    physics.calculate_proper_travel_time,
                    ("distance_light_years", "speed_fraction_of_c"),
                ),
                "relativistic_kinetic_energy": self._operation(
                    "Calculate relativistic kinetic energy in joules.",
                    {
                        "mass_kg": number,
                        "speed_fraction_of_c": number,
                    },
                    physics.calculate_relativistic_kinetic_energy,
                    ("mass_kg", "speed_fraction_of_c"),
                ),
                "relativistic_momentum": self._operation(
                    "Calculate relativistic momentum in kg m/s.",
                    {
                        "mass_kg": number,
                        "speed_fraction_of_c": number,
                    },
                    physics.calculate_relativistic_momentum,
                    ("mass_kg", "speed_fraction_of_c"),
                ),
                "kardashev_energy_output": self._operation(
                    "Calculate energy production in watts for a Kardashev scale.",
                    {"kardashev_scale": number},
                    economics.calculate_kardashev_energy_output,
                    ("kardashev_scale",),
                ),
                "population_after_growth": self._operation(
                    "Calculate population after compound annual growth.",
                    {
                        "population": integer,
                        "annual_growth_rate": number,
                        "years": integer,
                    },
                    economics.calculate_population_after_growth,
                    ("population", "annual_growth_rate", "years"),
                ),
                "energy_budget": self._operation(
                    "Calculate energy demand, surplus, and deficit.",
                    {
                        "population": integer,
                        "energy_production_watts": number,
                        "energy_consumption_watts_per_person": number,
                    },
                    economics.calculate_energy_budget,
                    (
                        "population",
                        "energy_production_watts",
                        "energy_consumption_watts_per_person",
                    ),
                ),
                "technology_breakthrough": self._operation(
                    "Roll for a technology breakthrough.",
                    {
                        "minor_probability": number,
                        "major_probability": number,
                        "revolutionary_probability": number,
                        "seed": integer,
                    },
                    technology.roll_technology_breakthrough,
                    (
                        "minor_probability",
                        "major_probability",
                        "revolutionary_probability",
                    ),
                ),
            },
        )

    def list_tools(self) -> list[dict]:
        """Return tool definitions, including operation-specific schemas."""

        result = []

        for tool in self._tools.values():
            result.append(
                {
                    "name": tool.name,
                    "description": tool.description,
                    "category": tool.category,
                    "parameters": tool.parameters,
                    "operations": [
                        {
                            "name": name,
                            "description": operation.description,
                            "parameters": {
                                "type": "object",
                                "properties": operation.properties,
                                "required": list(operation.required),
                                "additionalProperties": False,
                            },
                        }
                        for name, operation in tool.operations.items()
                    ],
                }
            )

        return result

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
        """Validate and execute a selected operation."""

        tool = self._tools.get(name)

        if tool is None:
            return {
                "ok": False,
                "error": f"Unknown tool: {name}",
            }

        if not isinstance(arguments, dict):
            return {
                "ok": False,
                "tool": name,
                "error": "Tool arguments must be an object.",
            }

        operation_name = arguments.get("operation")

        if not isinstance(operation_name, str):
            return {
                "ok": False,
                "tool": name,
                "error": "A valid operation must be selected.",
            }

        operation = tool.operations.get(operation_name)

        if operation is None:
            return {
                "ok": False,
                "tool": name,
                "error": f"Unknown operation: {operation_name}",
            }

        allowed = set(operation.properties) | {"operation"}
        supplied = set(arguments)

        missing = [
            field
            for field in operation.required
            if field not in supplied
        ]

        unexpected = sorted(supplied - allowed)

        if missing:
            return {
                "ok": False,
                "tool": name,
                "operation": operation_name,
                "error": f"Missing required arguments: {missing}",
            }

        if unexpected:
            return {
                "ok": False,
                "tool": name,
                "operation": operation_name,
                "error": f"Unexpected arguments for this operation: {unexpected}",
            }

        call_arguments = {
            key: value
            for key, value in arguments.items()
            if key != "operation"
        }

        try:
            result = operation.handler(**call_arguments)

            if tool.category == "world" and self._on_change is not None:
                self._on_change()

            return {
                "ok": True,
                "tool": name,
                "operation": operation_name,
                "result": result,
            }

        except (ValueError, TypeError, KeyError, OverflowError) as exc:
            return {
                "ok": False,
                "tool": name,
                "operation": operation_name,
                "error": str(exc),
            }
