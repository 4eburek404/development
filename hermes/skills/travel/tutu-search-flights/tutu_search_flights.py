"""Типизированный контракт Tutu и поиск через MCP SDK без проекции ответа."""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
from collections.abc import Callable
from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from mcp import types
from pydantic import (
    AliasChoices,
    AwareDatetime,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    ValidationError,
)

TUTU_MCP_URL = "https://mcp.tutu.ru/mcp"


def _source_number(value: object) -> Decimal:
    # Decimal допускает JSON-строки даже в strict mode; источник требует number.
    if type(value) not in (int, float, Decimal):
        raise ValueError("expected a JSON number")
    return Decimal(str(value))


def _source_date(value: object) -> date:
    if type(value) is date:
        return value
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        raise ValueError("expected a date string YYYY-MM-DD")
    return date.fromisoformat(value)


SourceNumber = Annotated[Decimal, BeforeValidator(_source_number)]
SourceDate = Annotated[date, BeforeValidator(_source_date)]


class SourceModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, strict=True)


class SearchArguments(SourceModel):
    origin: str = Field(validation_alias=AliasChoices("origin", "from_city"))
    destination: str = Field(validation_alias=AliasChoices("destination", "to_city"))
    departure_date: SourceDate
    return_date: SourceDate | None = None
    adults: int = Field(default=1, ge=1, le=9, strict=True)
    children: int = Field(default=0, ge=0, le=9, strict=True)
    infants: int = Field(default=0, ge=0, le=9, strict=True)
    service_class: Literal["Y", "S", "C", "F"] = "Y"
    page: int = Field(default=1, ge=1, le=10, strict=True)
    page_size: int = Field(default=10, ge=1, le=30, strict=True)
    sort: Literal["price_asc", "price_desc", "duration_asc", "departure_asc"] = "price_asc"
    price_max: float | None = Field(default=None, ge=0)
    direct_only: bool = Field(default=False, strict=True)
    carriers: list[str] | None = None
    flight_numbers: list[str] | None = None
    view: Literal["compact", "full"] = "compact"


class Price(SourceModel):
    amount: SourceNumber
    currency: str


class Baggage(SourceModel):
    kg: int | None = None
    pieces: int | None = None
    dimensions: str | None = None


class Exchange(SourceModel):
    available: bool
    deadline_hours: int | None = None


class Conditions(SourceModel):
    fare_family: str | None = None
    baggage: Baggage | None = None
    cabin_baggage: Baggage | None = None
    refundable: bool | None = None
    changeable: bool | None = None
    exchange: Exchange | None = None
    seat_selection: str | None = None
    boarding_privileges: str | None = None
    business_hall_allowed: bool | None = None


class ReviewSummary(SourceModel):
    rating: SourceNumber
    review_count: int
    label: str
    source: str
    scope: str
    subject: str
    scale: int
    feedback_key: str


class Variant(SourceModel):
    variant_id: str
    offer_hash: str
    price: Price
    conditions: Conditions
    service_class: str


class Segment(SourceModel):
    carrier: str
    voyage_no: str
    from_: str = Field(alias="from")
    to: str
    departure_at: AwareDatetime
    arrival_at: AwareDatetime
    duration_min: int
    from_geo_point_id: int
    to_geo_point_id: int
    review_summary: ReviewSummary | None = None


class Leg(SourceModel):
    label: str
    from_: str = Field(alias="from")
    to: str
    departure_at: AwareDatetime
    arrival_at: AwareDatetime
    duration_min: int
    segments: list[Segment]


class CheckoutPart(SourceModel):
    departure_geo_city_id: int
    arrival_geo_city_id: int
    departure_at: AwareDatetime
    from_: str = Field(alias="from")
    to: str
    flights: list[str]


class CheckoutRef(SourceModel):
    transport: str
    is_round_trip: bool
    search_results_url: str
    offer_hash: str
    departure_geo_city_id: int
    arrival_geo_city_id: int
    departure_at: AwareDatetime
    service_class: str
    departure_avia_id: str
    arrival_avia_id: str
    passengers_full: int
    passengers_child: int
    passengers_infant: int
    return_departure_at: AwareDatetime | None = None
    checkout_parts: list[CheckoutPart] | None = None


class Offer(SourceModel):
    offer_id: str
    transport: str
    price: Price
    carriers: list[str]
    search_results_url: str
    duration_min: int
    segments_count: int
    departure_at: AwareDatetime
    arrival_at: AwareDatetime
    legs: list[Leg]
    variants: list[Variant]
    checkout_ref: CheckoutRef
    review_summary: ReviewSummary | None = None
    is_round_trip: bool | None = None
    return_departure_at: AwareDatetime | None = None
    return_arrival_at: AwareDatetime | None = None
    has_self_transfer: bool | None = None
    is_multi_pnr: bool | None = None
    multi_pnr_note: str | None = None


class Passengers(SourceModel):
    full: int
    child: int | None = None
    infant: int | None = None


class Pricing(SourceModel):
    basis: str
    passengers: Passengers
    note: str


class Place(SourceModel):
    name: str
    geo_id: str
    region: str
    iata: str
    match: str | None = None
    query: str | None = None
    kind: str | None = None


class CarrierAvailable(SourceModel):
    name: str
    offers_count: int
    price_from: SourceNumber


class Meta(SourceModel):
    transport: str
    checkout_hint: str
    pricing: Pricing
    from_: Place = Field(alias="from")
    to: Place
    round_trip: bool
    return_date: SourceDate | None
    sort: str
    page: int
    page_size: int
    total_returned: int
    total_matched: int
    has_more: bool
    total_matched_exact: bool
    carriers_available: list[CarrierAvailable]
    upstream_note: str | None = None
    post_filter_dropped_over_cap: int = 0
    post_filter_dropped_not_direct: int = 0
    post_filter_dropped_wrong_carrier: int = 0
    post_filter_dropped_wrong_flight_number: int = 0
    post_filter_dropped_wrong_airport: int = 0


class SearchResponse(SourceModel):
    offers: list[Offer]
    meta: Meta


def _validate_source_text(text: str) -> str:
    """Проверить все поля; исходный текст сохраняет числа и отсутствие/null."""
    SearchResponse.model_validate_json(text)
    return text


def result_text(result: types.CallToolResult) -> str:
    text = next(
        (block.text for block in result.content if isinstance(block, types.TextContent)), None
    )
    if result.is_error:
        raise RuntimeError(text or "Tutu MCP search_avia failed")
    if text is None:
        raise ValueError("Tutu MCP search_avia returned no text result")
    return _validate_source_text(text)


def search(
    arguments: SearchArguments,
    *,
    call_tool: Callable[[str, SearchArguments], types.CallToolResult],
) -> SearchResponse:
    return SearchResponse.model_validate_json(result_text(call_tool("search_avia", arguments)))


async def search_live(arguments: SearchArguments, *, url: str = TUTU_MCP_URL) -> str:
    from mcp import Client

    async with Client(url) as client:
        # SDK 2.2.0 требует dict: временное представление только на этой границе.
        result = await client.call_tool(
            "search_avia",
            arguments.model_dump(mode="json", by_alias=True, exclude_unset=True),
        )
    return result_text(result)


def _exception_message(error: Exception) -> str:
    if isinstance(error, ExceptionGroup):
        message = "; ".join(_exception_message(child) for child in error.exceptions)
        return message or str(error) or type(error).__name__
    return str(error) or type(error).__name__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Живой поиск авиабилетов через Tutu MCP")
    parser.add_argument("arguments", help="JSON-объект аргументов search_avia")
    parsed = parser.parse_args(argv)
    try:
        arguments = SearchArguments.model_validate_json(parsed.arguments)
    except ValidationError as exc:
        if '"type":"json_invalid"' in exc.json():
            parser.error("arguments must be valid JSON")
        if not parsed.arguments.lstrip().startswith("{"):
            parser.error("arguments must be a JSON object")
        parser.error(f"invalid search_avia arguments: {exc}")
    try:
        result = asyncio.run(search_live(arguments))
    except Exception as exc:
        print(_exception_message(exc), file=sys.stderr)
        return 1
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
