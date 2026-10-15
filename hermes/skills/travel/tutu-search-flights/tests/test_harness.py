"""Целостность исторических research-записей и manifest."""

from pathlib import Path

from recordings import FIXTURES, Manifest, ProtocolResult, Record


def manifest() -> Manifest:
    return Manifest.model_validate_json((FIXTURES / "manifest.json").read_text())


def test_манифест_читается_и_не_пуст():
    assert len(manifest().entries) >= 19


def test_каждая_запись_манифеста_указывает_на_существующий_файл():
    assert all((FIXTURES / entry.file).exists() for entry in manifest().entries)


def test_каждая_фикстура_на_диске_есть_в_манифесте():
    declared = {entry.file for entry in manifest().entries}
    actual = {
        str(p.relative_to(FIXTURES)) for p in FIXTURES.rglob("*.json") if p.name != "manifest.json"
    }
    assert actual <= declared


def test_у_каждого_конверта_есть_опорная_дата_и_обязательные_поля():
    for entry in manifest().entries:
        record = Record[ProtocolResult].model_validate_json((FIXTURES / entry.file).read_text())
        assert record.recorded_at.utcoffset() is not None
        assert record.recorded_at == entry.recorded_at
        assert record.arguments == entry.arguments
        assert record.note == entry.note
        assert record.source == "tutu"
        assert record.method == entry.method


def test_записаны_и_отказы_тоже():
    roles = {Path(entry.file).stem for entry in manifest().entries}
    assert {"empty-route", "past-date", "bad-input", "unknown-carrier"} <= roles
