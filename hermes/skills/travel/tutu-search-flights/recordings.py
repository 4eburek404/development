"""Типизированное чтение исторических записей; JSON-схемы принадлежат MCP SDK."""

from __future__ import annotations

from pathlib import Path
from typing import Generic, TypeVar

from mcp import types
from pydantic import AwareDatetime, BaseModel, ConfigDict
from tutu_search_flights import SearchArguments, SourceModel


class RecordedArguments(SearchArguments):
    # Research намеренно содержит невалидные даты для исследования отказов.
    origin: str | None = None
    destination: str | None = None
    departure_date: str | None = None
    return_date: str | None = None
    uri: str | None = None


Result = TypeVar("Result", bound=BaseModel)


class Envelope(SourceModel, Generic[Result]):
    jsonrpc: str
    id: int | str
    result: Result


class Response(BaseModel, Generic[Result]):
    # payload в старых fixtures — дублирующее представление, не источник истины.
    # Не читаем его и не передаём в код поиска.
    model_config = ConfigDict(extra="ignore")
    envelope: Envelope[Result] | types.JSONRPCError


class Entry(SourceModel):
    file: str
    recorded_at: AwareDatetime
    method: str
    tool: str
    arguments: RecordedArguments
    note: str
    volatile: list[str]


class Manifest(SourceModel):
    recorded_at: AwareDatetime
    source: str
    url: str
    entries: list[Entry]


class Record(SourceModel, Generic[Result]):
    recorded_at: AwareDatetime
    source: str
    method: str
    tool: str
    arguments: RecordedArguments
    note: str
    volatile: list[str]
    response: Response[Result]


FIXTURES = Path(__file__).resolve().parent / "fixtures"
ProtocolResult = types.CallToolResult | types.ListToolsResult | types.InitializeResult


def read_recording(path: str) -> Record[types.CallToolResult]:
    return Record[types.CallToolResult].model_validate_json((FIXTURES / path).read_text())


def request_from_record(record: Record) -> SearchArguments:
    return SearchArguments.model_validate_json(record.arguments.model_dump_json(exclude_unset=True))
