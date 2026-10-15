"""S2: production CLI uses the real MCP SDK against a recorded in-memory server."""

from decimal import Decimal

import tutu_search_flights
from recordings import request_from_record
from tutu_search_flights import SearchArguments, SearchResponse

from tests.mcp_recording_server import install_recorded_mcp, read_recording

REQUEST = SearchArguments(
    origin="Москва", destination="Сочи", departure_date="2026-10-15", page_size=3
)


def test_production_cli_uses_sdk_search_avia_and_returns_product_result(monkeypatch, capsys):
    fixture = read_recording("avia/baseline.json")
    assert request_from_record(fixture) == REQUEST
    result_record = fixture.response.envelope.result
    source_text = result_record.content[0].text
    recording = install_recorded_mcp(monkeypatch, result_record)

    exit_code = tutu_search_flights.main([REQUEST.model_dump_json(exclude_unset=True)])
    captured = capsys.readouterr()
    actual = SearchResponse.model_validate_json(captured.out)

    assert exit_code == 0
    assert captured.err == ""
    assert recording.client_urls == ["https://mcp.tutu.ru/mcp"]
    assert recording.calls == [("search_avia", REQUEST)]

    # Independent source anchors guard the SDK-backed CLI output.
    source_payload = SearchResponse.model_validate_json(source_text)
    assert captured.out.rstrip("\n") == source_text
    assert actual.meta.pricing.basis == "party_total"
    assert actual.meta.pricing.passengers.full == 1
    assert len(actual.offers) == len(source_payload.offers) == 3
    assert actual.offers[0].offer_id == source_payload.offers[0].offer_id
    assert actual.offers[0].legs[0].segments[0].voyage_no == "DP-6949"
    assert actual.offers[0].price.amount == Decimal("4446.87")
    assert actual.offers[0].price.currency == "RUB"
    assert actual.offers[0].variants[0].price.amount == Decimal("4446.87")
