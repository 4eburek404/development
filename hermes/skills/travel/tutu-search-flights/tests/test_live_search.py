"""Opt-in smoke живого Tutu MCP; не входит в локальный gate."""

import asyncio
import os
from datetime import UTC, datetime, timedelta

import pytest
from tutu_search_flights import SearchArguments, SearchResponse, search_live

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(os.environ.get("TUTU_LIVE") != "1", reason="set TUTU_LIVE=1"),
]


def test_live_search_returns_current_tutu_offer():
    request = SearchArguments(
        origin="Москва",
        destination="Сочи",
        departure_date=(datetime.now(UTC).date() + timedelta(days=21)),
        page_size=1,
    )
    result = SearchResponse.model_validate_json(asyncio.run(search_live(request)))
    assert result.meta.pricing.basis == "party_total"
    assert result.meta.pricing.passengers.full == 1
    assert result.offers
    assert result.offers[0].variants
