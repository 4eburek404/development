# Проверки evaluate

Тесты оценщиков находятся рядом с владельцем:

- `harness/tests/` — общий harness и источники версий skills;
- `development-workflow/tests/` — оценщик разработки и извлечение свидетельств;
- `github-code-review/tests/` — consumer проверки кода;
- `tutu-search-flights/tests/` — оценщик поиска Tutu.

Из корня репозитория, в окружении с pytest и зависимостями оценщиков:

```sh
python3 -m pytest -q evals
```

Для одного компонента замените `evals` на `evals/<компонент>/tests`.
Все эти проверки детерминированные: они не запускают настоящую модель.
Development-workflow также использует `ptyprocess` и настоящий `hermes_state.SessionDB`
с временной базой данных. Дочерние команды `python3` должны использовать то же
окружение с pytest.

На локальном Mac с каноническим окружением и Hermes в `~/.hermes/hermes-agent`
полный запуск выполняется так (исходники Hermes доступны также дочерним процессам;
локальный `evals` импортируется до одноимённого пакета Hermes):

```sh
PATH=/Users/home/.venvs/hermes-backup/bin:$PATH \
PYTHONPATH=/Users/home/.hermes/hermes-agent \
/Users/home/.venvs/hermes-backup/bin/python - <<'PY'
import sys
sys.path.remove('/Users/home/.hermes/hermes-agent')
import pytest
import evals.harness.core
sys.path.append('/Users/home/.hermes/hermes-agent')
raise SystemExit(pytest.main(['-q', 'evals']))
PY
```

Сохранённые трассы и JSON-свидетельства содержат исторические пути и при переносе
тестов не переписываются. В исторических отчётах с обновлёнными командами числа
прошлых запусков не являются результатом новой проверки.
