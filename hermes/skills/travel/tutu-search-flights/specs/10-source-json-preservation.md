# S9 — сохранение проверенного исходного JSON Tutu

Спецификация защищает передачу данных источника без собственной проекции,
с обязательной валидацией и различием отсутствующего поля и `null`.

## Дано

Записанный raw MCP response `fixtures/avia/baseline.json`. Контрольные случаи:
исходная запись, точное числовое значение цены, неизвестное поле в корне или
вложенном объекте, неверный исходный JSON-тип известного поля.
Изменения создаются только в памяти; fixture не редактируется.

Контрольные случаи неверного типа создаются независимо, заменой одного значения:
- `variants[].price.amount`: число `4446.87` заменено строкой `"4446.87"`;
- `variants[].conditions.refundable`: boolean `false` заменён строкой `"false"`;
- `variants[].conditions.baggage.kg`: целое `0` заменено строкой `"0"`.

Это примеры общего требования к исходным JSON-типам, а не закрытый перечень
полей. Значение, которое можно преобразовать в ожидаемый тип, ещё не является
значением этого типа в ответе источника.


## Когда

Production CLI вызывает `search_avia` через MCP SDK с записанным in-memory server.

## Тогда

- Успешный stdout содержит исходный JSON Tutu без переименования или потери полей.
- Все поля успешного ответа проходят проверку исходных JSON-типов структуры
  источника на каждом уровне вложенности. Число, строка и boolean различаются;
  возможность преобразования не делает исходный ответ корректным.
- Строка вместо числовой цены, строка вместо boolean или целого значения
  вызывает код 1, диагностику ошибочного поля в stderr и пустой stdout.
  Невалидный ответ не выдаётся как успешный JSON и не исправляется перед выводом.
- Отсутствующее поле не добавляется; явный `null` не удаляется. Отсутствие и
  `null` допустимы только там, где это разрешено контрактом конкретного поля;
  они не заменяют обязательную числовую цену.
- Числовая цена и временные строки не меняются из-за пересериализации.
- Неизвестное поле на любом уровне вызывает ошибку, ненулевой exit status,
  объяснение в stderr и отсутствие успешного JSON в stdout.
- Tool-level, transport и прочие ошибки остаются под контрактами S3/S8.

## Исполнение и граница проверки

`make spec` и `make check` работают без сети и LLM. Источник истины — text-блок
raw envelope, не дублирующий `response.payload`.

В `tests/test_source_json_preservation.py`:
- `test_successful_cli_preserves_tutu_json[recorded]`;
- `test_successful_cli_preserves_tutu_json[precise-number]`;
- `test_absent_and_null_remain_distinct`;
- `test_unknown_fields_fail_without_success_json[root]`, `[meta]`, `[offer]`,
  `[leg]`, `[segment]`, `[variant]`, `[price]`, `[conditions]`, `[pricing]`.

Все имена выше имеют префикс `tests/test_source_json_preservation.py::`.
`tests/test_typed_source.py::test_all_recorded_successes_validate_without_projection`
проверяет полный набор успешных исторических записей.
`tests/test_typed_source.py::test_unknown_source_field_is_rejected` отдельно
защищает отказ валидатора. Эти проверки не подтверждают неизменность живой схемы
Tutu или качество ответа агента; новое поле живого сервера требует обновления модели.

### Граница проверки исходных JSON-типов

Статус новых случаев: **GREEN — три неверных исходных типа отклоняются
с кодом 1, пустым stdout и диагностикой поля**. Существующий schema-invalid
тест S8 проверяет неполный объект, а неизвестные поля проверяют имена;
эти проверки не заменяют отказ при неверных исходных JSON-типах.

Исполняемые узлы:

- `tests/test_source_json_preservation.py::test_wrong_source_types_fail_without_success_json[price-string]`;
- `tests/test_source_json_preservation.py::test_wrong_source_types_fail_without_success_json[boolean-string]`;
- `tests/test_source_json_preservation.py::test_wrong_source_types_fail_without_success_json[weight-string]`.

Каждый независимо заменяет только одно поле первого тарифа в памяти и проходит
через production CLI, настоящий SDK и записанный MCP server. Проверяются код 1,
пустой stdout, имя ошибочного поля в stderr и исходный вызов `search_avia`.

Положительные контрпримеры — исходные JSON-типы тех же полей, в том числе boolean
`false` и число `0`, в `test_successful_cli_preserves_tutu_json[recorded]`, а также
высокоточная числовая цена в `[precise-number]` с тем же префиксом
`tests/test_source_json_preservation.py::`. Корректный ответ сохраняется текстом.
Все случаи входят в `make spec` и `make check`. RED на `7f9e172` и последующий
GREEN зафиксированы в [матрице](../docs/verification.md).
