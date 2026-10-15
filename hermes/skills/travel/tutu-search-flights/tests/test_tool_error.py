"""S3: recorded Tutu tool errors remain errors through the real MCP SDK."""

import asyncio

import pytest
import tutu_search_flights
from recordings import request_from_record

from tests.mcp_recording_server import install_recorded_mcp, read_recording


def test_tool_error_is_reported_as_error_not_empty_search(monkeypatch):
    fixture = read_recording("avia/empty-route.json")
    result_record = fixture.response.envelope.result
    reason = result_record.content[0].text
    recording = install_recorded_mcp(monkeypatch, result_record)

    with pytest.raises(RuntimeError) as error:
        asyncio.run(tutu_search_flights.search_live(request_from_record(fixture)))

    assert str(error.value) == reason
    assert recording.client_urls == ["https://mcp.tutu.ru/mcp"]
    assert recording.calls == [("search_avia", request_from_record(fixture))]
