import asyncio
import importlib

import httpx
import pytest

from dark_forest_sim.narrator import runtime as runtime_module


@pytest.fixture(scope="module")
def inspector_proxy(tmp_path_factory):
    save_path = tmp_path_factory.mktemp("inspector") / "simulation.json"

    original_runtime = runtime_module.NarratorRuntime

    runtime_module.NarratorRuntime = lambda: original_runtime(
        save_path=save_path
    )

    try:
        module = importlib.import_module(
            "dark_forest_sim.inspector.proxy"
        )
        yield module
    finally:
        runtime_module.NarratorRuntime = original_runtime


@pytest.mark.asyncio
async def test_broadcast_queue_remains_bounded(inspector_proxy, monkeypatch):
    proxy = inspector_proxy
    queue = asyncio.Queue(maxsize=2)
    monkeypatch.setattr(proxy, "subscribers", {queue})

    for index in range(10):
        await proxy.broadcast({
            "type": "token",
            "text": str(index),
        })

    assert queue.qsize() <= 2

    messages = [
        queue.get_nowait(),
        queue.get_nowait(),
    ]

    assert any('"type":"overflow"' in message for message in messages)
    assert any('"text": "9"' in message for message in messages)


@pytest.mark.asyncio
async def test_upstream_connection_failure_returns_502(inspector_proxy, monkeypatch):
    proxy = inspector_proxy
    async with proxy.app.router.lifespan_context(proxy.app):
        client = proxy.app.state.client

        async def fail_send(request, **kwargs):
            raise httpx.ConnectError(
                "Inference server unavailable",
                request=request,
            )

        monkeypatch.setattr(client, "send", fail_send)

        transport = httpx.ASGITransport(app=proxy.app)

        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as test_client:
            response = await test_client.post(
                "/v1/chat/completions",
                json={
                    "model": "test-model",
                    "messages": [{"role": "user", "content": "Hello"}],
                },
            )

    assert response.status_code == 502
    assert response.json()["error"] == "upstream_unavailable"
