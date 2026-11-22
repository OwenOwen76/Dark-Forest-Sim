from __future__ import annotations

import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parents[2]
    / "mcp-servers.json"
)


class CivilizationMCPClient:
    def __init__(
        self,
        config_path: Path = DEFAULT_CONFIG_PATH,
        server_name: str = "dark-forest",
    ):
        self.config_path = Path(config_path)
        self.server_name = server_name

    def _server_parameters(self) -> StdioServerParameters:
        try:
            config = json.loads(
                self.config_path.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(
                f"Unable to load MCP configuration: {exc}"
            ) from exc

        servers = config.get("mcpServers")

        if not isinstance(servers, dict):
            raise ValueError(
                "MCP configuration must contain mcpServers."
            )

        server = servers.get(self.server_name)

        if not isinstance(server, dict):
            raise ValueError(
                f"Unknown MCP server: {self.server_name}"
            )

        command = server.get("command")
        args = server.get("args", [])
        environment = server.get("env", {})
        cwd = server.get("cwd")

        if not isinstance(command, str) or not command:
            raise ValueError("MCP command must be a non-empty string.")

        if not isinstance(args, list) or not all(
            isinstance(arg, str) for arg in args
        ):
            raise ValueError("MCP args must be a list of strings.")

        if not isinstance(environment, dict) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in environment.items()
        ):
            raise ValueError("MCP env must contain string values.")

        if cwd is not None and not isinstance(cwd, str):
            raise ValueError("MCP cwd must be a string.")

        env = os.environ.copy()
        env.update(environment)

        return StdioServerParameters(
            command=command,
            args=args,
            env=env,
            cwd=cwd,
        )

    @asynccontextmanager
    async def connect(self):
        parameters = self._server_parameters()

        async with stdio_client(parameters) as streams:
            read_stream, write_stream = streams

            async with ClientSession(
                read_stream,
                write_stream,
            ) as session:
                await session.initialize()
                yield session

    @staticmethod
    async def get_openai_tools(
        session: ClientSession,
    ) -> list[dict[str, Any]]:
        response = await session.list_tools()

        tools = []

        for tool in response.tools:
            tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema,
                },
            })

        return tools

    @staticmethod
    async def call_tool(
        session: ClientSession,
        name: str,
        arguments: dict[str, Any],
    ) -> Any:
        result = await session.call_tool(
            name,
            arguments=arguments,
        )

        if result.isError:
            messages = [
                item.text
                for item in result.content
                if hasattr(item, "text")
            ]

            raise RuntimeError(
                "\n".join(messages) or f"MCP tool failed: {name}"
            )

        structured = getattr(
            result,
            "structuredContent",
            None,
        )

        if structured is not None:
            return structured

        text_content = [
            item.text
            for item in result.content
            if hasattr(item, "text")
        ]

        if len(text_content) == 1:
            try:
                return json.loads(text_content[0])
            except json.JSONDecodeError:
                return text_content[0]

        return text_content
