"""S9: исходный JSON сохраняется; неизвестные поля вызывают отказ."""

import pytest
import tutu_search_flights
from mcp import types
from tutu_search_flights import SearchResponse

from tests.mcp_recording_server import install_recorded_mcp, read_recording, request_from_record


@pytest.mark.parametrize("precise", [False, True], ids=["recorded", "precise-number"])
def test_successful_cli_preserves_tutu_json(monkeypatch, capsys, precise):
    fixture = read_recording("avia/baseline.json")
    request = request_from_record(fixture)
    result = fixture.response.envelope.result.model_copy(deep=True)
    text = result.content[0].text
    if precise:
        text = text.replace("4446.87", "4446.870000000000000000000000001")
        result.content[0].text = text
    recording = install_recorded_mcp(monkeypatch, result)
    assert tutu_search_flights.main([request.model_dump_json(exclude_unset=True)]) == 0
    output = capsys.readouterr()
    assert output.err == ""
    assert output.out == text + "\n"
    assert recording.calls == [("search_avia", request)]
    SearchResponse.model_validate_json(output.out)
    if precise:
        assert "4446.870000000000000000000000001" in output.out


@pytest.mark.parametrize(
    "marker",
    [
        '"offers":',
        '"pricing":',
        '"offer_id":',
        '"label":',
        '"voyage_no":',
        '"variant_id":',
        '"amount":',
        '"fare_family":',
        '"passengers":',
    ],
    ids=["root", "meta", "offer", "leg", "segment", "variant", "price", "conditions", "pricing"],
)
def test_unknown_fields_fail_without_success_json(monkeypatch, capsys, marker):
    fixture = read_recording("avia/baseline.json")
    result = fixture.response.envelope.result.model_copy(deep=True)
    text = result.content[0].text
    assert marker in text
    result.content[0].text = text.replace(marker, '"unknown_field":123,' + marker, 1)
    install_recorded_mcp(monkeypatch, result)
    assert (
        tutu_search_flights.main([request_from_record(fixture).model_dump_json(exclude_unset=True)])
        == 1
    )
    output = capsys.readouterr()
    assert output.out == ""
    assert "extra_forbidden" in output.err


def test_absent_and_null_remain_distinct(monkeypatch, capsys):
    fixture = read_recording("avia/baseline.json")
    text = fixture.response.envelope.result.content[0].text
    source = SearchResponse.model_validate_json(text)
    assert "has_self_transfer" not in source.offers[0].model_fields_set
    assert "upstream_note" in source.meta.model_fields_set
    assert source.meta.upstream_note is None
    result = types.CallToolResult(content=[types.TextContent(type="text", text=text)])
    install_recorded_mcp(monkeypatch, result)
    assert (
        tutu_search_flights.main([request_from_record(fixture).model_dump_json(exclude_unset=True)])
        == 0
    )
    assert capsys.readouterr().out == text + "\n"


@pytest.mark.parametrize(
    ("old", "new", "field"),
    [
        ('"amount":4446.87', '"amount":"4446.87"', "amount"),
        ('"refundable":false', '"refundable":"false"', "refundable"),
        ('"kg":0', '"kg":"0"', "kg"),
    ],
    ids=["price-string", "boolean-string", "weight-string"],
)
def test_wrong_source_types_fail_without_success_json(monkeypatch, capsys, old, new, field):
    fixture = read_recording("avia/baseline.json")
    result = fixture.response.envelope.result.model_copy(deep=True)
    text = result.content[0].text
    # Меняем только поле первого тарифа, не верхнеуровневую цену предложения.
    start = text.index('"variants":[')
    prefix, variants = text[:start], text[start:]
    assert old in variants
    result.content[0].text = prefix + variants.replace(old, new, 1)
    request = request_from_record(fixture)
    recording = install_recorded_mcp(monkeypatch, result)
    exit_code = tutu_search_flights.main([request.model_dump_json(exclude_unset=True)])
    output = capsys.readouterr()
    assert exit_code == 1
    assert output.out == ""
    assert field in output.err
    assert recording.calls == [("search_avia", request)]
