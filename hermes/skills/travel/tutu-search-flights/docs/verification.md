# Матрица требований и доказательств

Текущий контракт: проверка исходных типов моделей Tutu и передача исходного JSON.
Сценарии S8/S9 для числовых дат и неверных типов ответа прошли цикл RED → GREEN
13.10.2026. Подтверждённый охват и ограничения приведены ниже.
Неизвестные поля вызывают явную ошибку; словари данных исключены из кода skill,
кроме документированных границ MCP SDK. Исторические результаты приведены отдельно.
Таблица связывает текущее наблюдаемое поведение с test node IDs и ограничивает
выводы фактическим охватом. Исторические fixtures не редактировались.

| Спецификация | Наблюдаемое требование | Test node IDs | Фактический охват |
|---|---|---|---|
| S1 | Сохранить предложения, цены, валюты, условия тарифов, сегменты, timezone-aware времена и пагинацию из ответа источника. | `tests/test_successful_search.py::test_successful_search_preserves_source_results_prices_and_conditions` | Baseline fixture: все 3 предложения; цена и валюта оффера; все варианты, цены и условия; маршрут, время, длительность и `meta.has_more`. Контрольные значения относятся только к этой записи. |
| S2 | Production CLI использует MCP SDK, вызывает `search_avia` с исходными аргументами и возвращает успешный JSON в stdout. | `tests/test_production_sdk_search.py::test_production_cli_uses_sdk_search_avia_and_returns_product_result` | Настоящий SDK 2.2.0 и локальный in-memory MCP Server; проверяются URL, единственный вызов и аргументы, цена и поля ответа Tutu. |
| S3 | Tool-level error остаётся ошибкой, а не пустой выдачей. | `tests/test_tool_error.py::test_tool_error_is_reported_as_error_not_empty_search` | SDK client/session получает сохранённый ответ ошибки; исключение содержит исходную причину. |
| S4 | `party_total` — цена всей группы; сумма, валюта и условия остаются связаны со своим вариантом тарифа. | `tests/test_party_pricing.py::test_party_total_price_is_not_multiplied_again` | Запрос двух взрослых и ребёнка; цены каждого тарифа сверяются с источником и проверяются против повторного умножения на 3. |
| S5 | Пересадки сохраняют плечи, сегменты и self-transfer evidence. | `tests/test_connections.py::test_connection_offer_preserves_segments_and_transfer_evidence` | Оба предложения, каждый сегмент, перевозчик, номер, аэропорты, времена, длительности и исходное пояснение. Неизвестные поля отклоняет S9. |
| S6 | Round-trip сохраняет outbound и return как отдельные legs и сегменты. | `tests/test_round_trip.py::test_round_trip_preserves_both_legs_and_outbound_route` | Проверены оба направления, время обратного плеча, маршрут outbound, длительности и значения сегментов. |
| S7 | Пустой список не теряет пояснение источника, точность счётчика и свидетельства фильтра. | `tests/test_empty_result_evidence.py::test_upstream_note_survives_empty_result`; `tests/test_empty_result_evidence.py::test_filter_drops_survive_empty_result` | Два записанных случая: `meta.upstream_note` при пустом ответе и ненулевой `meta.post_filter_dropped_wrong_carrier`; в обоих проверяется полное множество и значения `meta.post_filter_dropped_*` относительно текстового JSON Tutu. |
| S8 | Ошибки ввода, tool, transport, timeout и ответа имеют заданный exit status/stderr; stdout не выдаёт успешный JSON. | Десять базовых node IDs перечислены ниже; типизированный вход и положительные случаи — в S8. | Проверяются коды 2/1, сообщения причин, пустой stdout, пустой content и content без текстового блока, malformed JSON и schema-invalid ответ. **GREEN:** четыре числовые даты отклоняются до SDK; три положительных варианта проходят. |
| S9 | Проверенный исходный JSON сохраняется; неизвестные поля — ошибка. | Полные варианты перечислены в [S9](../specs/10-source-json-preservation.md). | Исходный и высокоточный числовой ответ, отсутствие/null, отказ на девяти уровнях, все успешные fixtures. Нет собственной выходной модели или проекции. **GREEN:** строки вместо цены/boolean/веса отклоняются; исходный корректный JSON сохраняется. |

## Узлы S8

- `tests/test_cli_errors.py::test_invalid_json_uses_argparse_error_contract`
- `tests/test_cli_errors.py::test_non_object_json_uses_argparse_error_contract`
- `tests/test_cli_errors.py::test_tool_error_emits_full_reason_on_stderr`
- `tests/test_cli_errors.py::test_transport_error_emits_reason_on_stderr`
- `tests/test_cli_errors.py::test_timeout_emits_reason_on_stderr[with-message]`
- `tests/test_cli_errors.py::test_timeout_emits_reason_on_stderr[empty-message]`
- `tests/test_cli_errors.py::test_missing_text_fails_without_success_json[empty-content]`
- `tests/test_cli_errors.py::test_missing_text_fails_without_success_json[non-text-content]`
- `tests/test_cli_errors.py::test_malformed_result_text_fails_without_success_json`
- `tests/test_cli_errors.py::test_invalid_search_result_fails_without_success_json`

## Историческая проверка прежнего S9 (до запрета неизвестных полей)

Зависимости установлены в отдельный Python 3.11 environment по lock-файлу
`requirements-dev.txt` (`mcp==2.2.0`, `mcp-types==2.2.0`). Команды запускались из
директории этого skill с `PYTHON=$HOME/.venvs/hermes-backup/bin/python`.

- Baseline `f1574f162150cc999b473f86b18107c156207b96`, `make spec`: **17 passed,
  2 failed**, оба отказа — ожидаемое сравнение S9 против прежней проекции.
- Baseline `make check`: **22 passed, 2 failed, 1 deselected**; оба отказа — S9.
- После актуализации успешного-output ожиданий целевой RED против прежней
  реализации: **9 failed** на устаревшей проекции/отсутствующих исходных полях.
- После реализации `make spec`: **20 passed**.
- После реализации `make check`: **25 passed, 1 deselected**; Ruff lint прошёл,
  все 17 Python-файлов отформатированы, команды документации проверены для 17 файлов.
- Отдельный запуск S9 и связанных ошибок (`test_source_json_preservation.py`,
  S3 `test_tool_error.py`, S8 empty/non-text/malformed/schema-invalid result): **7 passed**.
- `make PYTHON=$HOME/.venvs/hermes-backup/bin/python live`: **1 passed in 2.58s** на живом Tutu MCP. Это отдельный
  smoke; детерминированные проверки используют сохранённые записи и локальный MCP Server.

Содержательные проверки S1–S8 сохранены; изменены только успешные-output ожидания,
закреплявшие устаревшие переименования, проекцию `fares`/`pricing_basis` и
производные поля. Ошибочные сценарии S3/S8 остаются отдельными проверками и не
выдаются за успешный пустой результат.

## Историческое внешнее свидетельство

GitHub Actions run `36174651955` был GREEN для commit `8f6dce235d69f5ef1dc14debb58a8ba01ac5a145`
на `new-tutu` 2026-09-25, то есть до контракта S9; он не подтверждает текущий код.
Статус Actions для итогового опубликованного commit проверяется отдельно.

Branch protection не подтверждён. Agent evaluation не запускался и не является
заменой product specs, локальным gates или live smoke.

## Проверка типизированного контракта — 12.10.2026

Основание изменений: `a3be881`, до фиксации текущего коммита.
Все команды используют `/Users/home/.venvs/hermes-backup/bin/python`.

- RED: `test_unknown_source_field_is_rejected` — DID NOT RAISE на прежнем коде.
- RED research: `test_research_preserves_json_rpc_error` — прежний recorder
  требовал `result` и отвергал JSON-RPC `error`.
- `make spec` — 38 passed.
- `make check` — 45 passed, 1 live deselected; Ruff lint/format и команды docs прошли.
- `tests/test_request_validation.py` — 5 отказов до SDK и сохранение legacy aliases
  без добавления незапрошенных defaults (входят в make check).
- `tests/test_research_recordings.py` — исходный envelope, сохранение другой группы
  manifest и JSON-RPC error; historical raw fixtures не менялись.
- Внешние contract checks `evals/tutu-search-flights/tests/test_tutu_search_flights_eval_contract.py`
  — 16 passed. Harness привязывает исторические версии отдельно; его код не менялся.
- `make live` — 1 passed in 2.30s. Это один запрос Москва → Сочи, не все маршруты.
- AST-проверка собственного Python-кода skill: нет словарных литералов,
  comprehensions и типов `dict`/`Any`/`Mapping`/`TypedDict`. Единственный
  `model_dump` — непосредственно аргумент SDK `Client.call_tool`.
- Belief map обновлена; `boundaries tutu_search_flights` — OK.

Модели покрывают поля успешных записанных avia responses. Не наблюдавшиеся формы
живого источника могут потребовать обновления модели; они не принимаются молча.
Отдельный agent evaluation для нового контракта не выполнялся.

## История дефектов на 7f9e172 — 13.10.2026

Проверен commit `7f9e172`. Первоначальные точечные воспроизведения ниже затем
закреплены исполняемыми спецификациями; результаты RED приведены отдельным разделом.

| Требование | Прямое наблюдение | Охват и статус |
|---|---|---|
| S8: даты — строки `YYYY-MM-DD`; число отклоняется до SDK | Валидация запроса с `departure_date=0` принимает его и превращает в `1970-01-01`. | **PARTIAL / RED:** четыре отрицательных сценария для обеих дат, `0` и ненулевого числа; реальные node IDs перечислены в S8. |
| S9: типы проверяются в исходном JSON, без признания преобразуемого значения корректным | Валидатор принимает строки вместо `amount`, `refundable` и `kg`. Через CLI случай `refundable="false"` даёт exit 0, пустой stderr и исходную строку в stdout. | **PARTIAL / RED:** три независимых отрицательных сценария через CLI/SDK; реальные node IDs перечислены в S9. |

Повторно выполненные `make check` (45 passed, 1 deselected) и `make spec`
(38 passed) не покрывают эти случаи. Ruff и проверка команд документации прошли;
pytest сообщил только о невозможности записать cache из-за прав sandbox.
Live-поиск при этом повторном review не запускался.

## Исполняемые спецификации новых случаев — RED, 13.10.2026

На неизменённом production-коде `7f9e172` добавлены тесты:

- S8: `tests/test_request_validation.py::test_numeric_dates_fail_before_sdk`
  — **4 failed**. Вместо ошибки ввода с кодом 2 даты проходят к границе SDK.
- S9: `tests/test_source_json_preservation.py::test_wrong_source_types_fail_without_success_json`
  — **3 failed**. CLI возвращает код 0 вместо 1 на строках вместо цены/boolean/веса.
- Положительные случаи
  `tests/test_request_validation.py::test_string_dates_and_optional_return_reach_sdk`
  — **3 passed** для отсутствующей, null и строковой обратной даты.

Все варианты node IDs перечислены в S8/S9. Сеть не используется. Raw fixtures
не меняются. Эти файлы уже включены в `make spec` и `make check`.
На этапе этого RED production-код не исправлялся; отказы не маскировались xfail.

Полный `make spec` с `PYTEST_ADDOPTS='-p no:cacheprovider --tb=short'`:
**7 failed, 41 passed**. Все семь отказов — новые сценарии выше; прежние
спецификации и положительные контрпримеры проходят. Ruff check/format двух
изменённых тестовых файлов, команды документации и `git diff --check` прошли.

## Исправление типов — GREEN, 13.10.2026

Путь eval-теста ниже обновлён после переноса; результат запуска остаётся историческим.

На том же наборе тестов после исправления production-валидации:

- `PYTEST_ADDOPTS='-p no:cacheprovider --tb=short' make PYTHON=/Users/home/.venvs/hermes-backup/bin/python spec`
  — **48 passed**, включая все семь прежних RED-сценариев.
- Та же настройка, `make check` — **55 passed, 1 live deselected**; Ruff lint,
  форматирование и проверка команд документации прошли.
- `evals/tutu-search-flights/tests/test_tutu_search_flights_eval_contract.py` — **16 passed**.
- `make live` — **1 passed in 7.33s**; один актуальный запрос Москва → Сочи.
- Независимое review: новых блокирующих дефектов не найдено; совместимость
  historical fixtures, research-записей и SDK callback подтверждена тестами.

Нативные JSON-типы проверяются строго; числовые даты и строки вместо чисел
не преобразуются в допустимые значения. Допустимые даты разбираются только
из `YYYY-MM-DD` (либо принимаются как готовый `date` во внутреннем Python-вызове).
`Decimal` дополнительно требует исходное числовое значение, поскольку его
стандартная strict-валидация JSON допускает строки. Выход CLI по-прежнему берётся
из исходного текста: не меняются точные числовые токены, времена, отсутствие/null.
Raw fixtures не менялись. Remote CI и отдельный agent evaluation не запускались.
