import os
from pathlib import Path

import httpx
from mcp.server import MCPServer

from .narrator import data, economics, physics


API_URL = os.getenv(
    "DARK_FOREST_SIM_API",
    "http://127.0.0.1:8099",
).rstrip("/")

PROJECT_SPACE = Path(
    os.getenv(
        "DARK_FOREST_PROJECT_SPACE",
        "/home/owen/dark-forest-sim/project_space",
    )
).resolve()

MAX_DOCUMENT_TREE_ENTRIES = 500
MAX_DOCUMENT_TREE_DEPTH = 12


mcp = MCPServer(
    name="Dark Forest Civilization",
    instructions="""
1. INSPECTION
   Inspect your own civilization and information that has reached you.

2. CALCULATION
   Perform mathematical, physical, astronomical, relativistic,
   demographic, and economic calculations.
   Pay attention to units and the assumptions described by each tool.

3. DOCUMENTS
   Use to create and maintain you documents regarding any discoveries, plan, or anything else you want

4. ACTION PROPOSALS
   Use propose_action to state your actions.

5. TIME ADVANCEMENT
   Use time_lapse to wait for a positive integer number of years, use this when you decide that you have done everything you want and there is nothing else you want to do beside waiting for results.
""",
)


# ---------------------------------------------------------------------------
# Simulation API
# ---------------------------------------------------------------------------

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


async def get_civilization_id() -> str:
    context = await api_request(
        "GET",
        "/api/civilization/context",
    )

    civilization_id = context.get("civilization_id")

    if not isinstance(civilization_id, str) or not civilization_id:
        raise RuntimeError(
            "The simulation API returned an invalid civilization ID."
        )

    return civilization_id


# ---------------------------------------------------------------------------
# Civilization document workspace
# ---------------------------------------------------------------------------

async def get_civilization_workspace() -> Path:
    civilization_id = await get_civilization_id()

    if (
        civilization_id in {".", ".."}
        or "/" in civilization_id
        or "\\" in civilization_id
        or "\x00" in civilization_id
    ):
        raise RuntimeError(
            "The civilization ID cannot be used as a workspace name."
        )

    PROJECT_SPACE.mkdir(
        parents=True,
        exist_ok=True,
    )

    workspace = PROJECT_SPACE / f"civilization-{civilization_id}"

    workspace.mkdir(
        exist_ok=True,
    )

    resolved_workspace = workspace.resolve()

    if not resolved_workspace.is_relative_to(PROJECT_SPACE):
        raise RuntimeError(
            "Civilization workspace is outside the project space."
        )

    if resolved_workspace.is_symlink():
        raise RuntimeError(
            "Civilization workspace is not a valid document workspace."
        )

    return resolved_workspace


def resolve_document_path(
    workspace: Path,
    relative_path: str,
    *,
    allow_workspace_root: bool = False,
) -> Path:
    if not isinstance(relative_path, str):
        raise ValueError("Document path must be a string.")

    if "\x00" in relative_path:
        raise ValueError("Document path contains an invalid character.")

    if not relative_path.strip():
        raise ValueError("Document path cannot be empty.")

    path = Path(relative_path)

    if path.is_absolute():
        raise ValueError("Document path must be relative.")

    if ".." in path.parts:
        raise ValueError("Document path cannot contain parent-directory traversal.")

    if path == Path(".") and not allow_workspace_root:
        raise ValueError("Document path must identify a file or folder.")

    candidate = workspace / path

    current = workspace

    for component in path.parts:
        if component in {"", "."}:
            continue

        current = current / component

        if current.is_symlink():
            raise ValueError("Document path contains a symbolic link.")

    resolved = candidate.resolve()

    if not resolved.is_relative_to(workspace):
        raise ValueError("Document path is outside the workspace.")

    return resolved


# ---------------------------------------------------------------------------
# Document tree generation
# ---------------------------------------------------------------------------

def build_document_tree(
    root: Path,
    *,
    max_entries: int = MAX_DOCUMENT_TREE_ENTRIES,
    max_depth: int = MAX_DOCUMENT_TREE_DEPTH,
) -> str:
    lines = [root.name]
    entry_count = 0
    truncated = False

    def walk(directory: Path, prefix: str, depth: int):
        nonlocal entry_count, truncated

        if depth >= max_depth:
            try:
                has_entries = next(os.scandir(directory), None) is not None
            except OSError:
                has_entries = False

            if has_entries:
                lines.append(f"{prefix}└── ... (maximum depth reached)")

            return

        try:
            with os.scandir(directory) as iterator:
                entries = list(iterator)
        except OSError as exc:
            lines.append(
                f"{prefix}└── [unable to read directory: {exc}]"
            )
            return

        entries.sort(
            key=lambda entry: (
                not entry.is_dir(follow_symlinks=False),
                entry.name.casefold(),
            )
        )

        for index, entry in enumerate(entries):
            if entry_count >= max_entries:
                truncated = True
                return

            entry_count += 1

            is_last = index == len(entries) - 1
            branch = "└── " if is_last else "├── "
            child_prefix = prefix + ("    " if is_last else "│   ")

            if entry.is_symlink():
                lines.append(
                    f"{prefix}{branch}{entry.name} [symlink blocked]"
                )
                continue

            try:
                is_directory = entry.is_dir(follow_symlinks=False)
            except OSError:
                is_directory = False

            if is_directory:
                lines.append(
                    f"{prefix}{branch}{entry.name}/"
                )

                walk(
                    Path(entry.path),
                    child_prefix,
                    depth + 1,
                )
            else:
                lines.append(
                    f"{prefix}{branch}{entry.name}"
                )

            if truncated:
                return

    walk(root, "", 0)

    if truncated:
        lines.append(
            f"... (listing truncated after {max_entries} entries)"
        )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Inspection tools
# ---------------------------------------------------------------------------

@mcp.tool(
    description=(
        "Inspect your civilization's current identity, local year, "
        "status, position, and resources."
    )
)
async def inspect_civilization() -> dict:
    return await api_request(
        "GET",
        "/api/civilization/context",
    )


@mcp.tool(
    description=(
        "Review information that has reached your civilization, "
        "including received events and discoveries."
    )
)
async def inspect_knowledge() -> dict:
    return await api_request(
        "GET",
        "/api/civilization/knowledge",
    )


# ---------------------------------------------------------------------------
# Document tools
# ---------------------------------------------------------------------------

@mcp.tool(
    description=(
        "List the documents and folders in your civilization's workspace "
        "as a tree. Provide a folder path to inspect a specific part "
        "of the workspace."
    )
)
async def list_doc(path: str = ".") -> dict:
    workspace = await get_civilization_workspace()

    directory = resolve_document_path(
        workspace,
        path,
        allow_workspace_root=True,
    )

    if not directory.exists():
        raise FileNotFoundError(
            f"Document folder does not exist: {path}"
        )

    if not directory.is_dir():
        raise ValueError(
            f"Document path is not a folder: {path}"
        )

    return {
        "path": path,
        "tree": build_document_tree(directory),
    }


@mcp.tool(
    description=(
        "Read a document from your civilization's workspace "
        "using its relative path."
    )
)
async def read_doc(path: str) -> dict:
    workspace = await get_civilization_workspace()

    document = resolve_document_path(
        workspace,
        path,
    )

    if not document.exists():
        raise FileNotFoundError(
            f"Document does not exist: {path}"
        )

    if not document.is_file():
        raise ValueError(
            f"Document path is not a file: {path}"
        )

    return {
        "path": path,
        "content": document.read_text(encoding="utf-8"),
    }


@mcp.tool(
    description=(
        "Replace the contents of a document in your civilization's "
        "workspace."
    )
)
async def write_doc(
    path: str,
    content: str,
) -> dict:
    workspace = await get_civilization_workspace()

    document = resolve_document_path(
        workspace,
        path,
    )

    if not document.exists():
        raise FileNotFoundError(
            f"Document does not exist: {path}"
        )

    if not document.is_file():
        raise ValueError(
            f"Document path is not a file: {path}"
        )

    document.write_text(
        content,
        encoding="utf-8",
    )

    return {
        "success": True,
        "path": path,
        "characters_written": len(content),
    }


@mcp.tool(
    description=(
        "Create a new document in your civilization's workspace "
        "with the supplied contents."
    )
)
async def create_doc(
    path: str,
    content: str,
) -> dict:
    workspace = await get_civilization_workspace()

    document = resolve_document_path(
        workspace,
        path,
    )

    if document.exists():
        raise FileExistsError(
            f"Document already exists: {path}"
        )

    if not document.parent.is_dir():
        raise FileNotFoundError(
            f"Parent folder does not exist: {document.parent}"
        )

    with document.open(
        "x",
        encoding="utf-8",
    ) as file:
        file.write(content)

    return {
        "success": True,
        "path": path,
        "characters_written": len(content),
    }


@mcp.tool(
    description=(
        "Create a new folder in your civilization's document workspace."
    )
)
async def create_doc_folder(path: str) -> dict:
    workspace = await get_civilization_workspace()

    directory = resolve_document_path(
        workspace,
        path,
    )

    directory.mkdir(
        parents=True,
        exist_ok=False,
    )

    return {
        "success": True,
        "path": path,
    }


# ---------------------------------------------------------------------------
# Spatial calculations
# ---------------------------------------------------------------------------

@mcp.tool(
    description=(
        "Calculate the distance between two positions in three-dimensional "
        "space, in light-years."
    )
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

    return {
        "distance_light_years": distance,
    }


@mcp.tool(
    description=(
        "Calculate travel time from a distance and travel speed, "
        "in years."
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

    return {
        "travel_time_years": years,
    }


# ---------------------------------------------------------------------------
# Signal and waste heat calculations
# ---------------------------------------------------------------------------

@mcp.tool(
    description=(
        "Estimate the maximum distance at which a signal can be "
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

    return {
        "detection_range_light_years": distance,
    }


@mcp.tool(
    description=(
        "Calculate the average waste heat produced by energy use, "
        "in watts."
    )
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

    return {
        "waste_heat_power_watts": result,
    }


@mcp.tool(
    description=(
        "Estimate the infrared detection range of a heat source, "
        "in light-years."
    )
)
async def calculate_infrared_detection_range(
    heat_power_watts: float,
    detection_threshold_watts_per_square_meter: float,
) -> dict:
    result = physics.calculate_infrared_detection_range(
        heat_power_watts,
        detection_threshold_watts_per_square_meter,
    )

    return {
        "detection_range_light_years": result,
    }


@mcp.tool(
    description=(
        "Calculate the time required to cool a given amount of thermal "
        "energy at a specified cooling power, in seconds."
    )
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

    return {
        "cooling_duration_seconds": result,
    }


@mcp.tool(
    description=(
        "Calculate the travel time of a signal over a given distance, "
        "in years."
    )
)
async def calculate_signal_travel_time(
    distance_light_years: float,
    speed_fraction_of_c: float,
) -> dict:
    result = physics.calculate_signal_travel_time(
        distance_light_years,
        speed_fraction_of_c,
    )

    return {
        "travel_time_years": result,
    }


@mcp.tool(
    description=(
        "Calculate when a signal will arrive from its departure time, "
        "distance, and propagation speed."
    )
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

    return {
        "arrival_time": result,
    }


# ---------------------------------------------------------------------------
# Relativistic calculations
# ---------------------------------------------------------------------------

@mcp.tool(
    description=(
        "Calculate the Lorentz factor for a given fraction "
        "of light speed."
    )
)
async def calculate_lorentz_factor(
    speed_fraction_of_c: float,
) -> dict:
    result = physics.calculate_lorentz_factor(
        speed_fraction_of_c,
    )

    return {
        "lorentz_factor": result,
    }


@mcp.tool(
    description=(
        "Calculate travel time in the universe reference frame "
        "for relativistic travel, in years."
    )
)
async def calculate_relativistic_travel_time(
    distance_light_years: float,
    speed_fraction_of_c: float,
) -> dict:
    result = physics.calculate_relativistic_travel_time(
        distance_light_years,
        speed_fraction_of_c,
    )

    return {
        "travel_time_years": result,
    }


@mcp.tool(
    description=(
        "Calculate the time experienced aboard a relativistic "
        "spacecraft during a journey, in years."
    )
)
async def calculate_proper_travel_time(
    distance_light_years: float,
    speed_fraction_of_c: float,
) -> dict:
    result = physics.calculate_proper_travel_time(
        distance_light_years,
        speed_fraction_of_c,
    )

    return {
        "proper_travel_time_years": result,
    }


@mcp.tool(
    description=(
        "Calculate relativistic kinetic energy from rest mass "
        "and speed, in joules."
    )
)
async def calculate_relativistic_kinetic_energy(
    mass_kg: float,
    speed_fraction_of_c: float,
) -> dict:
    result = physics.calculate_relativistic_kinetic_energy(
        mass_kg,
        speed_fraction_of_c,
    )

    return {
        "kinetic_energy_joules": result,
    }


@mcp.tool(
    description=(
        "Calculate relativistic momentum from rest mass and speed, "
        "in kg·m/s."
    )
)
async def calculate_relativistic_momentum(
    mass_kg: float,
    speed_fraction_of_c: float,
) -> dict:
    result = physics.calculate_relativistic_momentum(
        mass_kg,
        speed_fraction_of_c,
    )

    return {
        "momentum_kg_m_per_s": result,
    }


# ---------------------------------------------------------------------------
# Economic and demographic calculations
# ---------------------------------------------------------------------------

@mcp.tool(
    description=(
        "Calculate your civilization's energy demand, surplus, "
        "and deficit from population and energy consumption."
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
        "Project your civilization's future population using "
        "an annual compound growth rate."
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
        "Calculate the energy production associated with "
        "a given Kardashev scale."
    )
)
async def calculate_kardashev_energy_output(
    kardashev_scale: float,
) -> dict:
    result = economics.calculate_kardashev_energy_output(
        kardashev_scale,
    )

    return {
        "kardashev_scale": kardashev_scale,
        "energy_output_watts": result,
    }


# ---------------------------------------------------------------------------
# Action proposals
# ---------------------------------------------------------------------------

@mcp.tool(
    description=(
        "Propose an action for your civilization to undertake. "
        "The proposal is sent to the simulation for resolution."
    )
)
async def propose_action(description: str) -> dict:
    return await api_request(
        "POST",
        "/api/civilization/action",
        {
            "description": description,
        },
    )


# ---------------------------------------------------------------------------
# Time advancement
# ---------------------------------------------------------------------------

@mcp.tool(
    description=(
        "End your current turn and wait for the specified number "
        "of local years."
    )
)
async def time_lapse(years: int) -> dict:
    return await api_request(
        "POST",
        "/api/civilization/time-lapse",
        {
            "years": years,
        },
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
