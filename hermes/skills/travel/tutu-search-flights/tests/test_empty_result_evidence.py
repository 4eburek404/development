"""S7: объяснение пустой выдачи и счётчики остаются в meta."""

from tests.product_driver import run_recording


def test_upstream_note_survives_empty_result():
    result, source = run_recording("past-date.json")
    assert result.offers == []
    assert result.meta.total_matched_exact is True
    assert result.meta.upstream_note == source.meta.upstream_note
    assert result.meta.upstream_note
    assert result.meta == source.meta
    assert result.meta.post_filter_dropped_wrong_carrier == 0
    assert result.meta.post_filter_dropped_not_direct == 0
    assert result.meta.post_filter_dropped_over_cap == 0
    assert result.meta.post_filter_dropped_wrong_airport == 0
    assert result.meta.post_filter_dropped_wrong_flight_number == 0


def test_filter_drops_survive_empty_result():
    result, source = run_recording("unknown-carrier.json")
    assert result.offers == []
    assert result.meta.total_matched_exact is True
    assert result.meta.upstream_note is None
    assert result.meta == source.meta
    assert result.meta.post_filter_dropped_wrong_carrier > 0
    assert result.meta.post_filter_dropped_not_direct == 0
    assert result.meta.post_filter_dropped_over_cap == 0
    assert result.meta.post_filter_dropped_wrong_airport == 0
    assert result.meta.post_filter_dropped_wrong_flight_number == 0
