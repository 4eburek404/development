"""S4: цена группы остаётся связана со своим тарифом."""

from tests.product_driver import run_recording


def test_party_total_price_is_not_multiplied_again():
    result, source = run_recording("party-2a-1c.json")
    assert result.meta.pricing.basis == "party_total"
    assert result.meta.pricing.passengers.full == 2
    assert result.meta.pricing.passengers.child == 1
    assert len(result.offers) == len(source.offers) == 2
    for offer, raw_offer in zip(result.offers, source.offers, strict=True):
        assert offer.offer_id == raw_offer.offer_id
        assert len(offer.variants) == len(raw_offer.variants)
        for variant, raw in zip(offer.variants, raw_offer.variants, strict=True):
            assert variant.conditions.fare_family == raw.conditions.fare_family
            assert variant.price.amount == raw.price.amount
            assert variant.price.amount != raw.price.amount * 3
            assert variant.price.currency == raw.price.currency
            assert variant.conditions == raw.conditions
