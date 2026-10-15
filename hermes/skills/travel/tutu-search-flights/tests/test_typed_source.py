"""Контракт: неизвестные поля отклоняются, известный исходный JSON сохраняется."""

from pathlib import Path

import pytest
from pydantic import ValidationError
from tutu_search_flights import SearchResponse, _validate_source_text

# Извлечение SDK text-блока без использования вспомогательного response.payload.
from tests.mcp_recording_server import read_recording


def test_unknown_source_field_is_rejected():
    record = read_recording("avia/baseline.json")
    text = record.response.envelope.result.content[0].text
    changed = text.replace('"offers":', '"unknown_field":123,"offers":', 1)
    with pytest.raises(ValidationError, match="extra_forbidden"):
        _validate_source_text(changed)


def test_all_recorded_successes_validate_without_projection():
    root = Path(__file__).resolve().parents[1] / "fixtures/avia"
    for path in root.glob("*.json"):
        record = read_recording("avia/" + path.name)
        result = record.response.envelope.result
        if result.is_error:
            continue
        text = result.content[0].text
        assert _validate_source_text(text) == text
        model = SearchResponse.model_validate_json(text)
        assert "offers" in model.model_fields_set
