from __future__ import annotations

import json

import httpx


class OpenAICompatibleClient:
    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str = "none",
        http_client: httpx.AsyncClient | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self._http_client = http_client
        self._owns_client = http_client is None

    async def complete(self, messages: list[dict]) -> dict:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=120.0)

        response = await self._http_client.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": messages,
            },
        )

        response.raise_for_status()

        try:
            data = response.json()
        except ValueError as exc:
            raise ValueError("LLM returned invalid JSON.") from exc

        if not isinstance(data, dict):
            raise ValueError("Invalid chat completion response.")

        choices = data.get("choices")

        if (
            not isinstance(choices, list)
            or not choices
            or not isinstance(choices[0], dict)
        ):
            raise ValueError("Invalid chat completion choices.")

        message = choices[0].get("message")

        if not isinstance(message, dict) or message.get("role") != "assistant":
            raise ValueError("Invalid assistant message.")

        content = message.get("content")
        reasoning = message.get("reasoning_content")
        tool_calls = message.get("tool_calls", [])

        if content is not None and not isinstance(content, str):
            raise ValueError("Assistant content must be a string or None.")

        if reasoning is not None and not isinstance(reasoning, str):
            raise ValueError("Assistant reasoning must be a string or None.")

        if not isinstance(tool_calls, list):
            raise ValueError("Assistant tool_calls must be a list.")

        for tool_call in tool_calls:
            if not isinstance(tool_call, dict):
                raise ValueError("Invalid assistant tool call.")

            if not isinstance(tool_call.get("id"), str) or not tool_call["id"]:
                raise ValueError("Tool call ID must be a non-empty string.")

            function = tool_call.get("function")

            if not isinstance(function, dict):
                raise ValueError("Tool call function must be an object.")

            if (
                not isinstance(function.get("name"), str)
                or not function["name"]
            ):
                raise ValueError("Tool call name must be a non-empty string.")

            arguments = function.get("arguments")

            if not isinstance(arguments, str):
                raise ValueError("Tool call arguments must be a JSON string.")

            try:
                parsed_arguments = json.loads(arguments)
            except json.JSONDecodeError as exc:
                raise ValueError("Tool call arguments contain invalid JSON.") from exc

            if not isinstance(parsed_arguments, dict):
                raise ValueError("Tool call arguments must decode to an object.")

        if not content and not reasoning and not tool_calls:
            raise ValueError("Assistant returned an empty message.")

        return message

    async def close(self) -> None:
        if self._owns_client and self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()
