"""S5: все плечи, сегменты и свидетельства самостоятельной пересадки."""

from tests.product_driver import run_recording


def test_connection_offer_preserves_segments_and_transfer_evidence():
    result, source = run_recording("connections.json")
    assert len(result.offers) == len(source.offers) == 2
    for offer, raw in zip(result.offers, source.offers, strict=True):
        assert offer.offer_id == raw.offer_id
        assert offer.has_self_transfer is raw.has_self_transfer is True
        assert offer.is_multi_pnr is raw.is_multi_pnr is True
        assert offer.multi_pnr_note == raw.multi_pnr_note
        assert offer.segments_count == raw.segments_count == 2
        assert offer.legs == raw.legs
        assert len(offer.legs[0].segments) == 2
        for leg, raw_leg in zip(offer.legs, raw.legs, strict=True):
            assert leg.duration_min == raw_leg.duration_min
            for segment, raw_segment in zip(leg.segments, raw_leg.segments, strict=True):
                assert segment.voyage_no == raw_segment.voyage_no
                assert segment.carrier == raw_segment.carrier
                assert segment.from_ == raw_segment.from_
                assert segment.to == raw_segment.to
                assert segment.departure_at == raw_segment.departure_at
                assert segment.arrival_at == raw_segment.arrival_at
                assert segment.duration_min == raw_segment.duration_min
