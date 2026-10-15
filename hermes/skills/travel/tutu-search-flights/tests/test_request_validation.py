"""Типизированный ввод проверяется до обращения к SDK."""

import mcp
import pytest
from tutu_search_flights import SearchArguments, main


@pytest.mark.parametrize(
    "arguments",
    [
        "{}",
        '{"origin":"Москва","destination":"Сочи","departure_date":"вчера"}',
        '{"origin":"Москва","destination":"Сочи","departure_date":"2026-11-15","adults":0}',
        '{"origin":"Москва","destination":"Сочи","departure_date":"2026-11-15","page_size":31}',
        '{"origin":"Москва","destination":"Сочи","departure_date":"2026-11-15","unknown":true}',
    ],
    ids=["missing", "date", "party", "page-size", "unknown"],
)
def test_invalid_arguments_fail_before_sdk(monkeypatch, capsys, arguments):
    def forbidden_client(url):
        pytest.fail("invalid arguments reached SDK")

    monkeypatch.setattr(mcp, "Client", forbidden_client)
    with pytest.raises(SystemExit) as error:
        main([arguments])
    assert error.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "invalid search_avia arguments" in captured.err


def test_legacy_aliases_resolve_to_source_request_fields():
    request = SearchArguments.model_validate_json(
        '{"from_city":"Москва","to_city":"Сочи","departure_date":"2026-11-15"}'
    )
    assert request.origin == "Москва"
    assert request.destination == "Сочи"
    assert request.model_fields_set == {"origin", "destination", "departure_date"}
    assert '"adults"' not in request.model_dump_json(exclude_unset=True)


@pytest.mark.parametrize("field", ["departure_date", "return_date"])
@pytest.mark.parametrize("value", [0, 1792022400], ids=["zero", "timestamp"])
def test_numeric_dates_fail_before_sdk(monkeypatch, capsys, field, value):
    client_urls = []

    def forbidden_client(url):
        client_urls.append(url)
        raise RuntimeError("numeric date reached SDK")

    monkeypatch.setattr(mcp, "Client", forbidden_client)
    dates = (
        f'"departure_date":{value}'
        if field == "departure_date"
        else f'"departure_date":"2026-11-15","return_date":{value}'
    )
    arguments = '{"origin":"Москва","destination":"Сочи",' + dates + "}"
    with pytest.raises(SystemExit) as error:
        main([arguments])
    captured = capsys.readouterr()
    assert error.value.code == 2
    assert captured.out == ""
    assert "usage:" in captured.err
    assert field in captured.err
    assert client_urls == []


@pytest.mark.parametrize(
    "return_field",
    ["", ',"return_date":null', ',"return_date":"2026-10-22"'],
    ids=["absent", "null", "date-string"],
)
def test_string_dates_and_optional_return_reach_sdk(monkeypatch, capsys, return_field):
    from tests.mcp_recording_server import install_recorded_mcp, read_recording

    fixture_name = "avia/round-trip.json" if return_field.endswith('"') else "avia/baseline.json"
    fixture = read_recording(fixture_name)
    recording = install_recorded_mcp(monkeypatch, fixture.response.envelope.result)
    arguments = (
        '{"origin":"Москва","destination":"Сочи","departure_date":"2026-10-15"' + return_field + "}"
    )
    assert main([arguments]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == fixture.response.envelope.result.content[0].text + "\n"
    assert recording.calls == [("search_avia", SearchArguments.model_validate_json(arguments))]
