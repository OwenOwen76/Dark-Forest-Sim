import os

import httpx
from mcp.server import MCPServer

from .narrator import data, economics, physics


API_URL = os.getenv(
    "DARK_FOREST_SIM_API",
    "http://127.0.0.1:8099",
).rstrip("/")


mcp = MCPServer(
    name="Dark Forest Civilization",
    instructions=(
        "You are a civilization in the Dark Forest simulation. "
        "You may inspect your own identity, resources, and delivered "
        "knowledge. You have mathematical tools for analyzing the "
        "universe and your civilization. You may propose actions to "
        "the narrator, but cannot directly modify the universe. "
        "Use time_lapse to end your turn and sleep."
    ),
)


async def api_request(
    method: str,
    path: str,
    payload: dict | None = None,
):
    async with httpx.AsyncClient(timeout=None) as client:
        response = await client.request(
            method,
            f"{API_URL}{path}",
            json=payload,
        )

    if response.is_error:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text

        raise RuntimeError(f"Simulation API error: {detail}")

    return response.json()


@mcp.tool(
    description=(
        "Inspect your own civilization's identity, local year, "
        "status, position, and resources."
    )
)
async def inspect_self() -> dict:
    return await api_request(
        "GET",
        "/api/civilization/context",
    )


@mcp.tool(
    description=(
        "Inspect events whose information has physically arrived "
        "at your civilization. Events still travelling are excluded."
    )
)
async def inspect_knowledge() -> dict:
    return await api_request(
        "GET",
        "/api/civilization/knowledge",
    )


@mcp.tool(
    description="Calculate the distance between two 3D positions in light-years."
)
async def calculate_distance(
    x1: float,
    y1: float,
    z1: float,
    x2: float,
    y2: float,
    z2: float,
) -> dict:
    distance = data.calculate_distance(
        x1, y1, z1,
        x2, y2, z2,
    )

    return {"distance_light_years": distance}


@mcp.tool(
    description=(
        "Calculate travel time in years given a distance in light-years "
        "and a travel speed in light-years per year."
    )
)
async def calculate_travel_time(
    distance_light_years: float,
    speed_light_years_per_year: float,
) -> dict:
    years = data.calculate_travel_time(
        distance_light_years,
        speed_light_years_per_year,
    )

    return {"travel_time_years": years}


@mcp.tool(
    description=(
        "Calculate the maximum distance at which a signal can be "
        "detected against background noise."
    )
)
async def calculate_detection_range(
    signal_power_at_1_ly: float,
    background_noise: float,
    detection_threshold: float,
) -> dict:
    distance = physics.calculate_detection_range(
        signal_power_at_1_ly,
        background_noise,
        detection_threshold,
    )

    return {"detection_range_light_years": distance}


@mcp.tool(
    description=(
        "Calculate a civilization's thermal signature, infrared "
        "detection range, and cooling duration."
    )
)
async def calculate_thermal_signature(
    energy_joules: float,
    waste_heat_fraction: float,
    duration_seconds: float,
    cooling_power_watts: float,
    detection_threshold_watts_per_square_meter: float,
) -> dict:
    heat_power = physics.calculate_waste_heat_power(
        energy_joules,
        waste_heat_fraction,
        duration_seconds,
    )

    detection_range = physics.calculate_infrared_detection_range(
        heat_power,
        detection_threshold_watts_per_square_meter,
    )

    cooling_duration = physics.calculate_cooling_duration(
        energy_joules,
        waste_heat_fraction,
        cooling_power_watts,
    )

    return {
        "waste_heat_power_watts": heat_power,
        "infrared_detection_range_light_years": detection_range,
        "cooling_duration_seconds": cooling_duration,
    }


@mcp.tool(
    description=(
        "Calculate when a signal will arrive at its destination, "
        "using simulation time in years and distance in light-years."
    )
)
async def calculate_signal_arrival(
    departure_time: float,
    distance_light_years: float,
    speed_fraction_of_c: float,
) -> dict:
    travel_time = physics.calculate_signal_travel_time(
        distance_light_years,
        speed_fraction_of_c,
    )

    arrival_time = physics.calculate_signal_arrival_time(
        departure_time,
        distance_light_years,
        speed_fraction_of_c,
    )

    return {
        "travel_time_years": travel_time,
        "arrival_time": arrival_time,
    }


@mcp.tool(
    description=(
        "Calculate relativistic travel time, proper time experienced "
        "aboard the ship, and the Lorentz factor."
    )
)
async def calculate_relativistic_travel(
    distance_light_years: float,
    speed_fraction_of_c: float,
) -> dict:
    lorentz_factor = physics.calculate_lorentz_factor(
        speed_fraction_of_c,
    )

    external_time = physics.calculate_relativistic_travel_time(
        distance_light_years,
        speed_fraction_of_c,
    )

    proper_time = physics.calculate_proper_travel_time(
        distance_light_years,
        speed_fraction_of_c,
    )

    return {
        "lorentz_factor": lorentz_factor,
        "external_travel_time_years": external_time,
        "proper_travel_time_years": proper_time,
    }


@mcp.tool(
    description=(
        "Calculate energy demand, surplus, and deficit "
        "for a civilization."
    )
)
async def calculate_energy_budget(
    population: int,
    energy_production_watts: float,
    energy_consumption_watts_per_person: float,
) -> dict:
    return economics.calculate_energy_budget(
        population,
        energy_production_watts,
        energy_consumption_watts_per_person,
    )


@mcp.tool(
    description=(
        "Calculate future population using compound annual growth."
    )
)
async def calculate_population_growth(
    population: int,
    annual_growth_rate: float,
    years: int,
) -> dict:
    result = economics.calculate_population_after_growth(
        population,
        annual_growth_rate,
        years,
    )

    return {
        "initial_population": population,
        "annual_growth_rate": annual_growth_rate,
        "years": years,
        "projected_population": result,
    }


@mcp.tool(
    description=(
        "Propose an action to the narrator. The narrator must approve "
        "or reject the proposal before the call completes."
    )
)
async def propose_action(description: str) -> dict:
    return await api_request(
        "POST",
        "/api/civilization/action",
        {"description": description},
    )


@mcp.tool(
    description=(
        "End your current turn and sleep for the specified positive "
        "integer number of local years."
    )
)
async def time_lapse(years: int) -> dict:
    return await api_request(
        "POST",
        "/api/civilization/time-lapse",
        {"years": years},
    )


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
