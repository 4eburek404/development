# S8 — ошибки production CLI

Эта исполняемая спецификация задаёт наблюдаемый контракт CLI для некорректного
ввода и ошибок поиска.

## Дано

Production CLI получает один позиционный аргумент с JSON. Ошибки поиска
воспроизводятся детерминированно: tool-level error, отсутствие текста и
некорректный текст результата приходят от локального in-memory MCP `Server`
через настоящий MCP SDK 2.2.0; транспортная ошибка и таймаут внедряются на
границе создания MCP client. Для вложенной `ExceptionGroup` причина берётся
из leaf exception и должна сохраниться в stderr.

Контрольные случаи типа даты: в остальном корректный запрос содержит число
`0` или `1792022400` вместо строки в `departure_date` либо `return_date`.
Число не является датой запроса и не трактуется как Unix timestamp, число дней
или другая форма даты. Допустимые даты передаются строками `YYYY-MM-DD`.
Для `return_date` отсутствие и явный `null` по-прежнему означают отсутствие
обратной даты; это не ошибки числового типа.

## Когда

CLI разбирает аргумент или выполняет живой поиск.

## Тогда

- невалидный JSON и JSON-значение не-объект завершают argparse с кодом 2;
  stdout пуст, stderr содержит usage и причину;
- неверный JSON-тип `departure_date` или `return_date`, в частности число,
  завершается кодом 2 до создания MCP client и до вызова `search_avia`;
  stdout пуст, stderr содержит usage, имя ошибочного поля и причину;
- неверный тип даты не преобразуется в календарную дату и не отправляется
  серверу как исправленный запрос;
- tool-level error выводит полный текст причины в stderr и завершается с кодом 1;
- транспортная ошибка и таймаут завершаются с кодом 1, сохраняя причину в stderr; если у исключения нет сообщения, stderr содержит имя его типа;
- отсутствующий текст, синтаксически некорректный текст и JSON результата,
  не соответствующий модели поиска, завершаются с кодом 1 и сообщением в stderr;
- при любой ошибке поиска stdout пуст: успешный JSON и `offers: []` не выдаются.

## Исполняемые проверки и граница

[test_cli_errors.py](../tests/test_cli_errors.py) закрепляет каждый исход:

- `test_invalid_json_uses_argparse_error_contract`
- `test_non_object_json_uses_argparse_error_contract`
- `test_tool_error_emits_full_reason_on_stderr`
- `test_transport_error_emits_reason_on_stderr`
- `test_timeout_emits_reason_on_stderr[with-message]`
- `test_timeout_emits_reason_on_stderr[empty-message]`
- `test_missing_text_fails_without_success_json[empty-content]`
- `test_missing_text_fails_without_success_json[non-text-content]`
- `test_malformed_result_text_fails_without_success_json`
- `test_invalid_search_result_fails_without_success_json`

Проверки с MCP проходят через настоящий SDK client/session/call на in-memory
server; два сетевых сбоя внедряются на границе создания client. HTTP и живой
Tutu не используются. Спецификация закрепляет коды выхода и потоки CLI, без
повторов, политики таймаутов или поведения при живой сети.

Дополнение типизированного входа: `tests/test_request_validation.py` проверяет
отказы до SDK при отсутствующих полях, неверной дате, составе пассажиров,
размере страницы и неизвестном аргументе. Все завершаются кодом 2 без stdout.
Полные узлы: `tests/test_request_validation.py::test_invalid_arguments_fail_before_sdk[missing]`,
`[date]`, `[party]`, `[page-size]`, `[unknown]` с тем же префиксом.

### Граница проверки типов даты

Статус новых случаев: **GREEN — четыре числовые даты отклоняются до SDK
с кодом 2; положительные строковые/null/отсутствующие варианты проходят**.
Существующий вариант `[date]` проверяет строку `"вчера"` и не заменяет новые случаи.

Исполняемые узлы в `tests/test_request_validation.py`:

- `tests/test_request_validation.py::test_numeric_dates_fail_before_sdk[zero-departure_date]`;
- `tests/test_request_validation.py::test_numeric_dates_fail_before_sdk[zero-return_date]`;
- `tests/test_request_validation.py::test_numeric_dates_fail_before_sdk[timestamp-departure_date]`;
- `tests/test_request_validation.py::test_numeric_dates_fail_before_sdk[timestamp-return_date]`.

Для каждого проверяются код 2, пустой stdout, usage и имя поля в stderr,
отсутствие создания MCP client. Сеть не используется: попытка создания SDK client
перехватывается и регистрируется на внешней границе.

Положительные узлы (GREEN):

- `tests/test_request_validation.py::test_string_dates_and_optional_return_reach_sdk[absent]`;
- `tests/test_request_validation.py::test_string_dates_and_optional_return_reach_sdk[null]`;
- `tests/test_request_validation.py::test_string_dates_and_optional_return_reach_sdk[date-string]`.

Они выполняют production CLI с настоящим SDK и записанным in-memory server,
проверяют исходные аргументы и успешный JSON. Все случаи входят в `make spec`
и `make check`. RED на коде `7f9e172` и последующий GREEN зафиксированы
в [матрице](../docs/verification.md).
