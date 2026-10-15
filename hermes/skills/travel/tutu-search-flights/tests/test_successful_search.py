"""S1: предложения, тарифы, времена и исходные неизвестные значения."""

from decimal import Decimal

from tests.product_driver import run_recording


def test_successful_search_preserves_source_results_prices_and_conditions():
    result, source = run_recording("baseline.json")
    assert result.meta.pricing.basis == "party_total"
    assert result.meta.pricing.passengers.full == 1
    assert result.meta.has_more is True
    assert len(result.offers) == len(source.offers) == 3
    assert {offer.offer_id for offer in result.offers} == {
        offer.offer_id for offer in source.offers
    }
    control = next(o for o in result.offers if o.offer_id == "a409680c1e4217c387b49c1763e75d16")
    segment = control.legs[0].segments[0]
    assert segment.voyage_no == "DP-6949"
    assert segment.carrier == "Победа"
    assert segment.from_ == "Москва — Шереметьево (SVO), терм. D"
    assert segment.to == "Сочи, AER"
    assert segment.departure_at.isoformat() == "2026-10-15T19:25:00+03:00"
    assert segment.arrival_at.isoformat() == "2026-10-15T23:05:00+03:00"
    assert control.duration_min == 220
    assert control.segments_count == 1
    assert control.price.amount == Decimal("4446.87")
    assert control.price.currency == "RUB"
    for offer, raw in zip(result.offers, source.offers, strict=True):
        assert offer.offer_id == raw.offer_id
        assert offer.price == raw.price
        assert offer.departure_at == raw.departure_at
        assert offer.arrival_at == raw.arrival_at
        assert offer.departure_at.utcoffset() is not None
        assert offer.arrival_at.utcoffset() is not None
        assert offer.duration_min == raw.duration_min
        assert offer.segments_count == raw.segments_count
        assert offer.legs == raw.legs
        assert offer.variants == raw.variants
        assert offer.checkout_ref == raw.checkout_ref
        assert offer.review_summary == raw.review_summary
    base = next(v for v in control.variants if v.conditions.fare_family == "Базовый")
    assert base.conditions.cabin_baggage.kg is None
    assert base.conditions.cabin_baggage.pieces == 1
    assert base.conditions.cabin_baggage.dimensions == "36 × 30 × 27"
    changeable = next(v for v in control.variants if v.conditions.fare_family == "Выгодный")
    assert changeable.conditions.exchange.available is True
    assert changeable.conditions.exchange.deadline_hours == 48
