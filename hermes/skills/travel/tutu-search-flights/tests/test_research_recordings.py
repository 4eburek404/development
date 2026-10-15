"""Research хранит исходный envelope и типизированный manifest без payload-копии."""

from pathlib import Path

import probe
from recordings import Entry, Manifest, ProtocolResult, Record, RecordedArguments


def test_research_recording_preserves_raw_envelope_and_other_manifest_group(tmp_path, monkeypatch):
    monkeypatch.setattr(probe, "ФИКСТУРЫ", tmp_path)
    args = RecordedArguments(origin="Москва", destination="Сочи", departure_date="вчера")
    raw = (
        '{"jsonrpc":"2.0","id":1,"result":{"content":'
        '[{"type":"text","text":"ошибка даты"}],"isError":true}}'
    )
    entry = probe.записать(
        "bad-input", "avia", "tools/call", "search_avia", args, raw, "ошибка даты"
    )
    record_text = (tmp_path / entry.file).read_text()
    assert raw in record_text
    record = Record[ProtocolResult].model_validate_json(record_text)
    assert record.arguments.departure_date == "вчера"
    assert record.response.envelope.result.is_error is True
    assert '"payload"' not in record_text
    foreign = Entry(
        file="meta/old.json",
        recorded_at=entry.recorded_at,
        method="tools/list",
        tool="tools/list",
        arguments=RecordedArguments(),
        note="history",
        volatile=[],
    )
    manifest = Manifest(
        recorded_at=entry.recorded_at, source="tutu", url=probe.URL, entries=[foreign]
    )
    (tmp_path / "manifest.json").write_text(manifest.model_dump_json())
    path = probe.обновить_манифест("avia", [entry])
    actual = Manifest.model_validate_json(Path(path).read_text())
    assert actual.entries == [entry, foreign]


def test_research_preserves_json_rpc_error(tmp_path, monkeypatch):
    monkeypatch.setattr(probe, "ФИКСТУРЫ", tmp_path)
    raw = '{"jsonrpc":"2.0","id":1,"error":{"code":-32602,"message":"Invalid params"}}'
    entry = probe.записать(
        "rpc-error",
        "meta",
        "tools/list",
        "tools/list",
        RecordedArguments(),
        raw,
        "protocol failure",
    )
    saved = (tmp_path / entry.file).read_text()
    assert raw in saved
    record = Record[ProtocolResult].model_validate_json(saved)
    assert record.response.envelope.error.code == -32602
    assert record.response.envelope.error.message == "Invalid params"
