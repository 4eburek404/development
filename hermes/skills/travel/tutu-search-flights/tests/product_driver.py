"""Тестовый адаптер использует типизированный production-интерфейс."""

from mcp import types
from recordings import read_recording, request_from_record
from tutu_search_flights import SearchArguments, SearchResponse, search


def run_recording(name: str) -> tuple[SearchResponse, SearchResponse]:
    record = read_recording("avia/" + name)
    request = request_from_record(record)
    raw = record.response.envelope.result
    calls: list[tuple[str, SearchArguments]] = []

    def recorded_tool(tool: str, arguments: SearchArguments) -> types.CallToolResult:
        calls.append((tool, arguments))
        return raw.model_copy(deep=True)

    result = search(request, call_tool=recorded_tool)
    assert calls == [("search_avia", request)]
    source = SearchResponse.model_validate_json(raw.content[0].text)
    return result, source
