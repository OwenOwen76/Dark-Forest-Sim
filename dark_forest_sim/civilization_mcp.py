import os

import httpx
from mcp.server import MCPServer


API_URL = os.getenv(
    "DARK_FOREST_SIM_API",
    "http://127.0.0.1:8099",
).rstrip("/")

mcp = MCPServer(
    name="Dark Forest Civilization",
    instructions=(
        "You are a civilization in the Dark Forest simulation. "
        "You can inspect only your own civilization context. "
        "Use action to propose actions to the narrator. "
        "Use time_lapse to end your turn and sleep."
    ),
)


async def api_request(method: str, path: str, payload: dict | None = None):
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


@mcp.tool(description="Get your civilization's current local year.")
async def get_time() -> dict:
    context = await api_request("GET", "/api/civilization/context")
    return {"year": context["year"]}


@mcp.tool(description="Inspect your own civilization's identity and status.")
async def get_status() -> dict:
    return await api_request("GET", "/api/civilization/context")


@mcp.tool(
    description=(
        "Propose an action to the narrator. "
        "This call waits until the narrator approves or rejects it."
    )
)
async def action(description: str) -> dict:
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
