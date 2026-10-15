"""S6: оба направления и все исходные сегменты."""

from tests.product_driver import run_recording


def test_round_trip_preserves_both_legs_and_outbound_route():
    result, source = run_recording("round-trip.json")
    assert result.meta.total_matched_exact is source.meta.total_matched_exact is False
    assert len(result.offers) == len(source.offers) == 2
    for offer, raw in zip(result.offers, source.offers, strict=True):
        assert offer.offer_id == raw.offer_id
        assert offer.is_round_trip is raw.is_round_trip is True
        assert offer.return_departure_at == raw.return_departure_at
        assert offer.return_arrival_at == raw.return_arrival_at
        assert [leg.label for leg in offer.legs] == ["outbound", "return"]
        assert offer.legs == raw.legs
        for leg, raw_leg in zip(offer.legs, raw.legs, strict=True):
            assert leg.from_ == raw_leg.from_
            assert leg.to == raw_leg.to
            assert leg.duration_min == raw_leg.duration_min
            for segment, raw_segment in zip(leg.segments, raw_leg.segments, strict=True):
                assert segment.voyage_no == raw_segment.voyage_no
                assert segment.carrier == raw_segment.carrier
                assert segment.departure_at == raw_segment.departure_at
                assert segment.arrival_at == raw_segment.arrival_at
