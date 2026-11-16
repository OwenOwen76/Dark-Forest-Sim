from __future__ import annotations

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

        data = response.json()

        try:
            message = data["choices"][0]["message"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError(
                "Invalid chat completion response."
            ) from exc

        if not isinstance(message, dict):
            raise ValueError("Invalid assistant message.")

        return message

    async def close(self) -> None:
        if self._owns_client and self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()
