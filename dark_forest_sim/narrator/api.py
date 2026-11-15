from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from .runtime import NarratorRuntime

from . import data

router = APIRouter(prefix="/api/narrator", tags=["narrator"])


class ToolCallRequest(BaseModel):
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)


def get_runtime(request: Request) -> NarratorRuntime:
    runtime = getattr(request.app.state, "narrator_runtime", None)

    if runtime is None:
        raise HTTPException(
            status_code=503,
            detail="Narrator runtime is not initialized.",
        )

    return runtime


@router.get("/tools")
async def get_tools(request: Request):
    runtime = get_runtime(request)

    return {
        "tools": runtime.toolbox.list_tools(),
    }


@router.post("/call")
async def call_tool(
    body: ToolCallRequest,
    request: Request,
):
    runtime = get_runtime(request)

    return runtime.toolbox.call(
        body.tool,
        body.arguments,
    )


@router.get("/state")
async def get_state(request: Request):
    runtime = get_runtime(request)

    return data.get_universe_status(runtime.universe)
