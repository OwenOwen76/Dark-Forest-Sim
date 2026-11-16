import httpx
import pytest

from dark_forest_sim.narrator.llm import OpenAICompatibleClient


async def complete_response(payload):
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=payload)
    )

    async with httpx.AsyncClient(transport=transport) as http_client:
        client = OpenAICompatibleClient(
            base_url="http://localhost:9931/v1",
            model="test-model",
            http_client=http_client,
        )
        return await client.complete([])


@pytest.mark.asyncio
async def test_valid_text_response():
    message = await complete_response({
        "choices": [{
            "message": {
                "role": "assistant",
                "content": "Hello, universe!",
            }
        }]
    })

    assert message["content"] == "Hello, universe!"


@pytest.mark.asyncio
async def test_valid_tool_call_response():
    message = await complete_response({
        "choices": [{
            "message": {
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": "call-1",
                    "type": "function",
                    "function": {
                        "name": "time_lapse",
                        "arguments": '{"years": 10}',
                    },
                }],
            }
        }]
    })

    assert message["tool_calls"][0]["function"]["name"] == "time_lapse"


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [
    {},
    {"choices": []},
    {"choices": "invalid"},
    {"choices": [{"message": None}]},
    {"choices": [{"message": {"role": "user", "content": "Hello"}}]},
])
async def test_malformed_response_is_rejected(payload):
    with pytest.raises(ValueError):
        await complete_response(payload)


@pytest.mark.asyncio
async def test_invalid_tool_call_arguments_are_rejected():
    with pytest.raises(ValueError, match="invalid JSON"):
        await complete_response({
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call-1",
                        "function": {
                            "name": "time_lapse",
                            "arguments": "{invalid json}",
                        },
                    }],
                }
            }]
        })


@pytest.mark.asyncio
async def test_tool_call_arguments_must_be_json_object():
    with pytest.raises(ValueError, match="decode to an object"):
        await complete_response({
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call-1",
                        "function": {
                            "name": "time_lapse",
                            "arguments": "[1, 2, 3]",
                        },
                    }],
                }
            }]
        })


@pytest.mark.asyncio
async def test_empty_assistant_response_is_rejected():
    with pytest.raises(ValueError, match="empty message"):
        await complete_response({
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "",
                }
            }]
        })
