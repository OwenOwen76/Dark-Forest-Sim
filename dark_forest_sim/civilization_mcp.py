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
        "detected against background noise, in light-years."
    )
)
async def calculate_signal_detection_range(
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
    description="Calculate average waste heat output in watts."
)
async def calculate_waste_heat_power(
    energy_joules: float,
    waste_heat_fraction: float,
    duration_seconds: float,
) -> dict:
    result = physics.calculate_waste_heat_power(
        energy_joules,
        waste_heat_fraction,
        duration_seconds,
    )
    return {"waste_heat_power_watts": result}


@mcp.tool(
    description="Calculate infrared detection range in light-years."
)
async def calculate_infrared_detection_range(
    heat_power_watts: float,
    detection_threshold_watts_per_square_meter: float,
) -> dict:
    result = physics.calculate_infrared_detection_range(
        heat_power_watts,
        detection_threshold_watts_per_square_meter,
    )
    return {"detection_range_light_years": result}


@mcp.tool(
    description="Calculate how long it takes to cool a given energy reserve, in seconds."
)
async def calculate_cooling_duration(
    energy_joules: float,
    waste_heat_fraction: float,
    cooling_power_watts: float,
) -> dict:
    result = physics.calculate_cooling_duration(
        energy_joules,
        waste_heat_fraction,
        cooling_power_watts,
    )
    return {"cooling_duration_seconds": result}

@mcp.tool(
    description="Calculate signal travel time in years."
)
async def calculate_signal_travel_time(
    distance_light_years: float,
    speed_fraction_of_c: float,
) -> dict:
    result = physics.calculate_signal_travel_time(
        distance_light_years,
        speed_fraction_of_c,
    )
    return {"travel_time_years": result}


@mcp.tool(
    description="Calculate the absolute arrival time of a signal in simulation years."
)
async def calculate_signal_arrival_time(
    departure_time: float,
    distance_light_years: float,
    speed_fraction_of_c: float,
) -> dict:
    result = physics.calculate_signal_arrival_time(
        departure_time,
        distance_light_years,
        speed_fraction_of_c,
    )
    return {"arrival_time": result}


@mcp.tool(
    description="Calculate the Lorentz factor for a given fraction of light speed."
)
async def calculate_lorentz_factor(
    speed_fraction_of_c: float,
) -> dict:
    result = physics.calculate_lorentz_factor(speed_fraction_of_c)
    return {"lorentz_factor": result}


@mcp.tool(
    description="Calculate relativistic travel time in the universe reference frame, in years."
)
async def calculate_relativistic_travel_time(
    distance_light_years: float,
    speed_fraction_of_c: float,
) -> dict:
    result = physics.calculate_relativistic_travel_time(
        distance_light_years,
        speed_fraction_of_c,
    )
    return {"travel_time_years": result}


@mcp.tool(
    description="Calculate time experienced aboard a relativistic ship, in years."
)
async def calculate_proper_travel_time(
    distance_light_years: float,
    speed_fraction_of_c: float,
) -> dict:
    result = physics.calculate_proper_travel_time(
        distance_light_years,
        speed_fraction_of_c,
    )
    return {"proper_travel_time_years": result}

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
