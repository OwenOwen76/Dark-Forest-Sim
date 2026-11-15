import asyncio
import json
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

from ..narrator.api import router as narrator_router
from ..narrator.runtime import NarratorRuntime


LLAMA_SERVER_URL = "http://127.0.0.1:9931"

INFERENCE_ENDPOINTS = {
    "v1/completions",
    "v1/chat/completions",
}

subscribers: set[asyncio.Queue] = set()


async def broadcast(event: dict) -> None:
    """Send an inspector event to every connected viewer."""
    message = f"data: {json.dumps(event)}\n\n"

    for queue in list(subscribers):
        await queue.put(message)


async def parse_inference_chunk(data: str, request_id: str) -> None:
    """Extract useful information from an OpenAI-compatible SSE chunk."""
    try:
        chunk = json.loads(data)
    except json.JSONDecodeError:
        return

    choices = chunk.get("choices") or [{}]
    choice = choices[0]
    delta = choice.get("delta") or {}

    text = choice.get("text") or delta.get("content") or ""
    reasoning = delta.get("reasoning_content") or ""

    if text:
        await broadcast({
            "type": "token",
            "id": request_id,
            "text": text,
        })

    if reasoning:
        await broadcast({
            "type": "reasoning",
            "id": request_id,
            "text": reasoning,
        })

    for tool_call in delta.get("tool_calls") or []:
        function = tool_call.get("function") or {}

        await broadcast({
            "type": "tool_call",
            "id": request_id,
            "index": tool_call.get("index"),
            "tool_id": tool_call.get("id"),
            "name": function.get("name"),
            "arguments": function.get("arguments"),
        })

    if choice.get("finish_reason"):
        await broadcast({
            "type": "finish",
            "id": request_id,
            "reason": choice["finish_reason"],
        })


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.client = httpx.AsyncClient(timeout=None)
    yield
    await app.state.client.aclose()


app = FastAPI(lifespan=lifespan)


app.state.narrator_runtime = NarratorRuntime()
app.include_router(narrator_router)

STATIC_DIR = Path(__file__).parent / "static"

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static",
)


@app.get("/")
async def inspector():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/events")
async def sse_events():
    queue = asyncio.Queue()
    subscribers.add(queue)

    async def event_stream():
        try:
            while True:
                try:
                    yield await asyncio.wait_for(queue.get(), timeout=15)
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            subscribers.discard(queue)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )


async def proxy_to_llama(path: str, request: Request):
    request_id = str(uuid.uuid4())
    body = await request.body()

    url = f"{LLAMA_SERVER_URL}/{path}"
    if request.url.query:
        url += f"?{request.url.query}"

    request_headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in {
            "host",
            "content-length",
            "transfer-encoding",
            "connection",
        }
    }

    upstream_request = request.app.state.client.build_request(
        method=request.method,
        url=url,
        content=body,
        headers=request_headers,
    )

    is_inference = path in INFERENCE_ENDPOINTS

    if is_inference:
        await broadcast({
            "type": "start",
            "id": request_id,
            "path": f"/{path}",
        })

    upstream = await request.app.state.client.send(
        upstream_request,
        stream=True,
    )

    response_headers = {
        key: value
        for key, value in upstream.headers.items()
        if key.lower() not in {
            "connection",
            "keep-alive",
            "transfer-encoding",
            "content-encoding",
            "content-length",
        }
    }

    is_sse = (
        "text/event-stream"
        in upstream.headers.get("content-type", "").lower()
    )

    if is_sse:

        async def stream_response():
            try:
                async for line in upstream.aiter_lines():
                    if is_inference and line.startswith("data:"):
                        data = line[5:].strip()

                        if data:
                            if data == "[DONE]":
                                await broadcast({
                                    "type": "done",
                                    "id": request_id,
                                })
                            else:
                                await parse_inference_chunk(
                                    data,
                                    request_id,
                                )

                    yield (line + "\n").encode("utf-8")

            finally:
                await upstream.aclose()

        return StreamingResponse(
            stream_response(),
            status_code=upstream.status_code,
            headers=response_headers,
        )

    try:
        content = await upstream.aread()
    finally:
        await upstream.aclose()

    return Response(
        content=content,
        status_code=upstream.status_code,
        headers=response_headers,
    )


@app.post("/v1/chat/completions")
async def proxy_chat_completions(request: Request):
    return await proxy_to_llama("v1/chat/completions", request)


@app.post("/v1/completions")
async def proxy_completions(request: Request):
    return await proxy_to_llama("v1/completions", request)


@app.get("/v1/models")
async def proxy_models(request: Request):
    return await proxy_to_llama("v1/models", request)
