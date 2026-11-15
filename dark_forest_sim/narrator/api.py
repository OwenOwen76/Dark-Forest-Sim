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

civilization_router = APIRouter(
    prefix="/api/civilization",
    tags=["civilization"],
)


class ActivateRequest(BaseModel):
    civilization_id: str


class ActionRequest(BaseModel):
    description: str


class ActionRulingRequest(BaseModel):
    proposal_id: str
    approved: bool
    explanation: str = ""


class TimeLapseRequest(BaseModel):
    years: int


@router.post("/activate")
async def activate_civilization(
    body: ActivateRequest,
    request: Request,
):
    runtime = get_runtime(request)

    try:
        return await runtime.activate_civilization(body.civilization_id)
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/pending-action")
async def get_pending_action(request: Request):
    runtime = get_runtime(request)
    return {"pending_action": runtime.pending_action}


@router.post("/resolve-action")
async def resolve_action(
    body: ActionRulingRequest,
    request: Request,
):
    runtime = get_runtime(request)

    try:
        return await runtime.resolve_action(
            body.proposal_id,
            body.approved,
            body.explanation,
        )
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@civilization_router.get("/context")
async def get_civilization_context(request: Request):
    runtime = get_runtime(request)

    try:
        return runtime.civilization_context()
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@civilization_router.post("/action")
async def civilization_action(
    body: ActionRequest,
    request: Request,
):
    runtime = get_runtime(request)

    try:
        return await runtime.submit_action(body.description)
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@civilization_router.post("/time-lapse")
async def civilization_time_lapse(
    body: TimeLapseRequest,
    request: Request,
):
    runtime = get_runtime(request)

    try:
        return await runtime.end_turn(body.years)
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=409, detail=str(exc))
