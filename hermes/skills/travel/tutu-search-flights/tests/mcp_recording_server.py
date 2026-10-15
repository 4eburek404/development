"""Настоящий MCP SDK с записанными типизированными ответами."""

from dataclasses import dataclass, field

import mcp
from mcp import Client as real_Client
from mcp import types
from mcp.server import Server
from recordings import FIXTURES, Record, read_recording, request_from_record
from tutu_search_flights import SearchArguments

__all__ = ["install_recorded_mcp", "read_recording", "request_from_record"]


@dataclass
class Recording:
    client_urls: list[str] = field(default_factory=list)
    calls: list[tuple[str, SearchArguments]] = field(default_factory=list)


def install_recorded_mcp(monkeypatch, call_result: types.CallToolResult) -> Recording:
    tools = (
        Record[types.ListToolsResult]
        .model_validate_json((FIXTURES / "meta/tools-list.json").read_text())
        .response.envelope.result
    )
    recording = Recording()

    async def call_handler(ctx, params):
        # SDK передаёт dict; немедленно валидируем, не сохраняем сырой контейнер.
        recording.calls.append((params.name, SearchArguments.model_validate(params.arguments)))
        return call_result.model_copy(deep=True)

    async def list_handler(ctx, params):
        return tools.model_copy(deep=True)

    server = Server("recorded", on_call_tool=call_handler, on_list_tools=list_handler)

    def client_factory(url: str):
        recording.client_urls.append(url)
        return real_Client(server)

    monkeypatch.setattr(mcp, "Client", client_factory)
    return recording
