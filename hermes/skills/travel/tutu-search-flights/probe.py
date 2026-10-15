#!/usr/bin/env python3
"""Research-only JSON-RPC через curl; исходные ответы сохраняются текстом.

Production transport находится в tutu_search_flights.py. Команды meta/avia
обновляют research fixtures и не входят в детерминированные проверки.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from mcp import types
from pydantic import TypeAdapter
from recordings import Entry, Envelope, Manifest, ProtocolResult, RecordedArguments

URL = "https://mcp.tutu.ru/mcp"
КОРЕНЬ = Path(__file__).resolve().parent
ФИКСТУРЫ = КОРЕНЬ / "fixtures"


def вызвать(метод: str, параметры_json: str, таймаут: int = 90) -> str:
    # JSON уже сформирован моделями или константой протокола; dict не требуется.
    тело = (
        '{"jsonrpc":"2.0","id":1,"method":'
        + json.dumps(метод)
        + ',"params":'
        + параметры_json
        + "}"
    )
    готово = subprocess.run(
        [
            "curl",
            "-sS",
            "-X",
            "POST",
            URL,
            "-H",
            "Content-Type: application/json",
            "-H",
            "Accept: application/json, text/event-stream",
            "-d",
            тело,
            "--max-time",
            str(таймаут),
        ],
        capture_output=True,
        text=True,
        timeout=таймаут + 15,
    )
    if готово.returncode:
        raise RuntimeError(готово.stderr.strip() or "curl failed")
    сырое = готово.stdout.strip()
    if not сырое:
        raise RuntimeError("Tutu MCP returned an empty response")
    строки = [s[6:] for s in сырое.splitlines() if s.startswith("data: ")]
    return строки[-1] if строки else сырое


def записать(
    роль: str,
    группа: str,
    метод: str,
    инструмент: str,
    аргументы: RecordedArguments,
    ответ_json: str,
    заметка: str,
    протухает: list[str] | None = None,
) -> Entry:
    # Protocol DTOs SDK проверяют envelope. JSON-схемы инструментов остаются
    # внутри SDK; исходный текст не пересобирается и не становится нашим dict.
    TypeAdapter(Envelope[ProtocolResult] | types.JSONRPCError).validate_json(ответ_json)
    запись = Entry(
        file=f"{группа}/{роль}.json",
        recorded_at=datetime.now(UTC),
        method=метод,
        tool=инструмент,
        arguments=аргументы,
        note=заметка,
        volatile=протухает or [],
    )
    заголовок = запись.model_dump_json(exclude={"file"}, exclude_unset=True)
    содержимое = заголовок[:-1] + ',"source":"tutu","response":{"envelope":' + ответ_json + "}}"
    путь = ФИКСТУРЫ / запись.file
    путь.parent.mkdir(parents=True, exist_ok=True)
    путь.write_text(содержимое + "\n", encoding="utf-8")
    return запись


def тул(
    роль: str,
    группа: str,
    имя: str,
    аргументы: RecordedArguments,
    заметка: str,
    протухает: list[str] | None = None,
) -> Entry:
    параметры = (
        '{"name":'
        + json.dumps(имя)
        + ',"arguments":'
        + аргументы.model_dump_json(exclude_unset=True)
        + "}"
    )
    ответ = вызвать("tools/call", параметры)
    запись = записать(роль, группа, "tools/call", имя, аргументы, ответ, заметка, протухает)
    print(f"  {роль:34} {len(ответ.encode('utf-8')):>8} байт")
    return запись


def разведать_мета() -> list[Entry]:
    записи: list[Entry] = []
    for роль, метод, параметры, заметка in (
        (
            "initialize",
            "initialize",
            '{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"tutu-flight-recon","version":"0.1.0"}}',
            "самоописание сервера",
        ),
        ("tools-list", "tools/list", "{}", "схемы инструментов"),
    ):
        записи.append(
            записать(
                роль, "meta", метод, метод, RecordedArguments(), вызвать(метод, параметры), заметка
            )
        )
    записи.append(
        тул(
            "avia-instructions",
            "meta",
            "get_avia_instructions",
            RecordedArguments(),
            "авиа-плейбук",
        )
    )
    for uri, роль, заметка in (
        ("tutu://help/overview", "resource-help", "общая справка"),
        ("tutu://status", "resource-status", "состояние сервера"),
        ("tutu://geo", "resource-geo", "справочник мест"),
    ):
        записи.append(тул(роль, "meta", "fetch_resource", RecordedArguments(uri=uri), заметка))
    return записи


def разведать_авиа() -> list[Entry]:
    def запрос(
        *,
        origin: str = "Москва",
        destination: str = "Сочи",
        departure_date: str = "2026-10-15",
        page_size: int = 3,
        page: int = 1,
        view: str = "compact",
        sort: str = "price_asc",
        direct_only: bool = False,
        return_date: str | None = None,
        adults: int = 1,
        children: int = 0,
        carriers: list[str] | None = None,
    ) -> RecordedArguments:
        return RecordedArguments(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            page_size=page_size,
            page=page,
            view=view,
            sort=sort,
            direct_only=direct_only,
            return_date=return_date,
            adults=adults,
            children=children,
            carriers=carriers,
        )

    пробы = [
        ("baseline", запрос(), "базовый ответ"),
        ("view-full", запрос(page_size=2, view="full"), "full против compact"),
        ("direct-only", запрос(direct_only=True), "фильтр прямых рейсов"),
        ("round-trip", запрос(page_size=2, return_date="2026-10-22"), "оба направления"),
        ("party-2a-1c", запрос(page_size=2, adults=2, children=1), "цена всей группы"),
        (
            "connections",
            запрос(origin="Калининград", destination="Владивосток", page_size=2),
            "пересадки",
        ),
        ("overnight", запрос(page_size=5, sort="duration_asc"), "смена суток"),
        ("page-2", запрос(page_size=2, page=2), "пагинация"),
        (
            "iata-airport",
            запрос(origin="SVO", destination="AER", page_size=2),
            "разрешение аэропортов",
        ),
        ("empty-route", запрос(origin="Урюпинск", destination="Певек"), "отказ маршрута"),
        ("past-date", запрос(departure_date="2020-01-01", page_size=2), "прошлая дата"),
        ("bad-input", запрос(departure_date="вчера"), "невалидный ввод"),
        ("unknown-carrier", запрос(carriers=["aeroflot"]), "пустой результат фильтра"),
    ]
    return [
        тул(
            роль,
            "avia",
            "search_avia",
            аргументы,
            заметка,
            ["offers[].price", "offers[].checkout_ref", "meta.search_id"],
        )
        for роль, аргументы, заметка in пробы
    ]


def обновить_манифест(группа: str, записи: list[Entry]) -> Path:
    путь = ФИКСТУРЫ / "manifest.json"
    прежние = Manifest.model_validate_json(путь.read_text()).entries if путь.exists() else []
    чужие = [entry for entry in прежние if entry.file.split("/", 1)[0] != группа]
    все = sorted(чужие + записи, key=lambda entry: entry.file)
    манифест = Manifest(
        recorded_at=max(entry.recorded_at for entry in все), source="tutu", url=URL, entries=все
    )
    путь.write_text(манифест.model_dump_json(exclude_unset=True, indent=2) + "\n", encoding="utf-8")
    return путь


if __name__ == "__main__":
    что = sys.argv[1] if len(sys.argv) > 1 else "meta"
    if что not in ("meta", "avia"):
        raise SystemExit("usage: probe.py [meta|avia]")
    записи = разведать_мета() if что == "meta" else разведать_авиа()
    путь = обновить_манифест(что, записи)
    print(f"записей: {len(записи)} → {путь}")
