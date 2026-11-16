import json

import httpx
import pytest

from dark_forest_sim.narrator.llm import OpenAICompatibleClient


@pytest.mark.asyncio
async def test_client_sends_chat_completion_request():
    requests = []

    def handler(request):
        requests.append(request)

        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "We should investigate the nearby star system.",
                        }
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(transport=transport) as http:
        client = OpenAICompatibleClient(
            base_url="http://localhost:8080/v1",
            model="test-model",
            api_key="test-key",
            http_client=http,
        )

        messages = [
            {"role": "system", "content": "You are a civilization."},
            {"role": "user", "content": "What should we do?"},
        ]

        result = await client.complete(messages)

    assert len(requests) == 1
    assert requests[0].url.path == "/v1/chat/completions"
    assert requests[0].headers["authorization"] == "Bearer test-key"

    payload = json.loads(requests[0].content)

    assert payload["model"] == "test-model"
    assert payload["messages"] == messages
    assert result == {
        "role": "assistant",
        "content": "We should investigate the nearby star system.",
    }


@pytest.mark.asyncio
async def test_client_raises_on_api_error():
    def handler(request):
        return httpx.Response(
            500,
            json={"error": {"message": "Internal server error"}},
        )

    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(transport=transport) as http:
        client = OpenAICompatibleClient(
            base_url="http://localhost:8080/v1",
            model="test-model",
            http_client=http,
        )

        with pytest.raises(httpx.HTTPStatusError):
            await client.complete(
                [{"role": "user", "content": "Hello"}]
            )
