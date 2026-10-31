# AGENTS REPORT — Investing Demo (домашнее задание №3)

## 1. AI Coding Agent

- **Agent: Qwen** (Qwen Code, interactive CLI agent, standalone, не Copilot и не агент из чужой ветки).
- Работал как независимый AI Coding Agent над учебным Django-проектом «Investing Demo»
  (`https://github.com/BezNames/aidd-topic-03-homework`).

## 2. Ветка

- Рабочая ветка: **`qwen-implementation`**.
- Исходный commit main (исходная точка ветки на момент начала работы): **`362510b`**
  («Add homework assignment»). Работа велась только в `qwen-implementation`;
  ветка `beznames-copilot-implementation` не открывалась и не использовалась.

## 3. Использованные промпты

1. Исходное задание (PROMT.md / HOMEWORK.md): инструкция выполнить Задания 1–4
   (анализ исходного кода; восстановление функциональных требований; технический аудит
   и исправления; новая функциональность «персональный мониторинг акций»), обязательные
   проверки, формат отчёта и финального коммита.
2. Промпт-уточнение по стартовому состоянию (в ходе работы): выбор варианта
   «Не сбрасывать, работать с текущим состоянием» — сохранить до начавшие
   незакоммиченные изменения рабочего дерева вместо `git reset --hard` от чистого main.

## 4. Этапы работы (порядок выполнения)

1. Изучение проекта: README, структура каталогов, models, views, urls, REST API,
   Celery, PostgreSQL/Redis, интеграция Tinkoff, существующие тесты, requirements.
2. **Задание 1** — подготовка ANALYSIS.md (15 разделов: назначение, стек, структура,
   приложения, архитектура, модель данных, связи, HTML-маршруты, REST API, БД,
   Celery/Redis, Tinkoff API, зависимости, существующие тесты, ограничения).
3. **Задание 2** — раздел 16 ANALYSIS.md: восстановленные требования
   (T-HTML-01..07, T-API-01..06, T-CEL-01..02, T-LOAD-01, T-TEST-01), отдельно
   неоднозначности (N-01..05) и дефекты (D-01..D-07).
4. **Задание 3** — технический аудит и исправления (см. п.16 ниже).
5. **Задание 4** — персональный мониторинг акций (см. п.17 ниже).
6. Повторные проверки (п.10–11) после каждого исправления и в конце.
7. Финальный коммит и пуш в `qwen-implementation`.

## 5. Изменённые файлы

### Новые файлы (созданы мной)

- `dashboard/services/tinkoff_client.py` — внутренний REST-клиент Tinkoff Invest
  (вместо несуществующего SDK): `market_data.get_last_prices`, `instruments.shares`,
  `get_all_candles`, Decimal-цены, исключения вместо `.pop()` на пустых ответах.
- `dashboard/services/watching.py` — логика Задания 4: `check_watches_for_share`,
  условия `gte`/`lte`, дедупликация через `last_triggered`, сброс условия.
- `dashboard/api/permissions.py` — `IsStaffOrReadOnly` (чтение для всех, запись только для персонала).
- `dashboard/migrations/0008_watch_watchnotification_and_more.py` — миграция моделей мониторинга.
- `user/migrations/0001_initial.py` — миграция кастомной модели User.
- `dashboard/templates/dashboard/watch_list.html`, `watch_create.html`,
  `watch_delete.html`, `watch_notifications.html` — HTML-интерфейс мониторинга.
- `ANALYSIS.md`, `AGENTS_REPORT.md` — документация.

### Изменённые файлы

- `requirements.txt` — убраны `tinkoff-investments`, `tinkoff`, `grpcio`, `protobuf`
  (несовместимы с Python 3.12 / отсутствуют на PyPI), добавлен `requests>=2.28.0`.
- `config/settings.py` — `SECRET_KEY` из env (fallback на `.secret_key`), `ALLOWED_HOSTS` из env,
  SQLite по умолчанию + PostgreSQL через `DJANGO_DATABASE_URL`, `LOGGING`, `TINKOFF_TOKEN`,
  `CELERY_BROKER_URL`, `CELERY_TASK_ALWAYS_EAGER`, `AUTH_USER_MODEL`.
- `config/celery.py` — beat-расписание переименовано и исправлено: `update-prices-every-5-min`,
  `schedule: 300.0` (было 10 сек с именем «5 минут»).
- `dashboard/models.py` — модели `Watch` и `WatchNotification` (+ `WATCH_DIRECTIONS`,
  `Meta.constraints` UniqueConstraint `(user, share)`, `Share.__str__`).
- `dashboard/services/market_data.py` — переписан на внутренний клиент; Decimal-цена,
  исключение при пустом ответе API.
- `dashboard/services/graph.py` — переписан на внутренний клиент; try/except вокруг Tinkoff.
- `dashboard/tasks.py` — переписан: per-share try/except с логированием, `save(update_fields=...)`,
  вызов `check_watches_for_share(share)` после обновления цены.
- `dashboard/api/v1/views.py` — `ShareViewSet` с `IsStaffOrReadOnly`; новые `WatchViewSet`
  (только свои наблюдения, `IsAuthenticated`) и `WatchNotificationViewSet` (read-only, свои).
- `dashboard/api/v1/router.py` — регистрация `watches` и `watch-notifications`.
- `dashboard/api/v1/serializer.py` — `WatchSerializer`/`WatchNotificationSerializer`, валидация
  целевой цены (положительная), дедупликация `(user, share)` в `validate()`.
- `dashboard/views.py` — `IsUserAuthenticatedMixin`, `IsStaffRequiredMixin` (CRUD акций — персонал),
  `WatchListView`/`WatchCreateView`/`WatchDeleteView`/`WatchNotificationListView` (только свои),
  `ShareDetailView` через `get_object_or_404`.
- `dashboard/urls.py`, `dashboard/forms.py` — маршруты и форма мониторинга
  (`WatchModelForm`, валидация целевой цены).
- `dashboard/tests.py` — переписан: 25 тестов (см. п.12–13).
- `dashboard/templates/dashboard/base.html`, `list.html`, `detail.html`, `create.html`,
  `delete.html` — правки в соответствии с новой функциональностью и исправлениями.
- `user/models.py` — кастомная `User(AbstractUser)`: `username=None`, `email=EmailField(unique)`,
  `USERNAME_FIELD="email"`, `REQUIRED_FIELDS=[]`, менеджер с `create_user/create_superuser`.
- `user/forms.py` — `RegistrationForm.save()` через `User.objects.create_user(email, password)`.
- `user/templates/user/auth.html`, `registration.html`, `base.html`, `user/urls.py`, `user/apps.py`,
  `user/static/user/css/signin.css`, `user/static/user/css/bootstrap.min.css`,
  `user/static/user/bootstrap.min.css`-пути — интеграция кастомного User.
- `manage.py`, `config/__init__.py`, `config/asgi.py`, `config/wsgi.py`, `config/urls.py`,
  `dashboard/apps.py`, `dashboard/admin.py`, `dashboard/api/urls.py`,
  `dashboard/urls.py`, `dashboard/management/commands/add_shares.py`,
  `dashboard/static/dashboard/css/*` — синхронизация/мелкие правки, сохранение существующей функциональности.

> Примечание: рабочее дерево на момент начала работы уже содержало незакоммиченные
> изменения файлов, не связанных с моей сессией (`.gitignore`, `docker-compose.yml`,
> `manage.py`, `HOMEWORK.md`, `README.md`, статические CSS и др.). По решению пользователя
> они сохранены и включаются в финальный коммит вместе с моими изменениями.

## 6. Ошибки и проблемы

1. **`git reset --hard` («начать от чистого main»)** — команда отклонена как разрушительная;
   вместо неё пользователь выбрал «работать с текущим состоянием».
2. **pip: нестабильная сеть** — установка пакетов висела (флаки DNS к `files.pythonhosted.org`);
   обход — установка по одному без `--quiet`.
3. **`protobuf==3.20.3` / `grpcio==1.51.3`** — нет колёс под Python 3.12, сборка из исходников
   падала (`ModuleNotFoundError: No module named 'pkg_resources'`). Убраны из requirements,
   Tinkoff SDK заменён внутренним REST-клиентом.
4. **`tinkoff-investments==0.2.0b50` и `tinkoff==0.1.1`** — не существуют на PyPI
   («No matching distribution found»). Полностью заменены внутренним клиентом `tinkoff_client.py`
   с совпадающей поверхностью вызовов (`get_last_prices`, `get_all_candles`, `instruments.shares`).
5. **`get_random_secret_key`** — не существует в Django 4.1.7 → использован `get_random_string(length=64)`.
6. **`NameError: No module named 'tinkoff'`** в `graph.py` после отказа от SDK — закрыт
   внутренним клиентом, совместимым с вызовами.
7. **Отсутствовала модель User вовсе** — регистрация была неработоспособна с момента создания
   проекта; `UserManager.create_user()` требовал `username`. Переписан `user/models.py`
   (кастомный User с email USERNAME_FIELD), добавлен migration и фикс `user/forms.py`.
8. **`test_share_delete_invalid` возвращал 403** (проверка прав выполняется раньше 404)
   после добавления `IsStaffOrReadOnly` → тест обновлён (аутентификация персоналом).
9. **`ValueError: too many values to unpack (expected 2)`** в `CharField.formfield()` при
   `choices=TextChoices_class` ( ChoicesMeta итерируется как список членов, а не пар) →
   заменено на плоский кортеж `WATCH_DIRECTIONS`, шаблон и `watching.py` переведены на строковые ключи `"gte"/"lte"`.
10. **`AssertionError: basename argument not specified`** у DRF-роутера для `WatchViewSet`
    (нет `.queryset` атрибута) → регистрация с `basename="watch"`.
11. **`NameError: name 'WatchNotification' is not defined` / 'Watch'** в `views.py` в `get_queryset` →
    добавлены в импорт из `dashboard.models`.
12. **`IntegrityError: UNIQUE constraint failed: dashboard_watch.user_id, dashboard_share_id`**
    при тесте дубля — сериализатор не проверял UniqueConstraint на уровне валидации
    (DRF ModelSerializer не добавляет UniqueValidator для UniqueConstraint автоматически) →
    добавлен `validate()` в `WatchSerializer`, возвращающий 400.
13. **`GET /` возвращал 500 / `OperationalError`** — `db.sqlite3` был нулевого размера
    (миграции не применялись) → выполнен `manage.py migrate`, база создана.
14. **Порядок ответа 403 vs 404** (см. п.8) и молчаливые `except` — см. дефекты D-01…D-07.

## 7. Дополнительные итерации

- Итерация 1: анализ + Задания 1–2 (документация). Проверка показала, что исходник
  неработоспособен на Python 3.12 (зависимости) и не стартует без PostgreSQL.
- Итерация 2: исправление зависимостей и конфигурации (Задание 3), замена Tinkoff SDK.
- Итерация 3: восстановление аутентификации (кастомный User) — обнаружено при прогоне тестов.
- Итерация 4: тесты (13 → 25), правки по падениям (403/404, choices-кортеж, basename, импорты).
- Итерация 5: финальные проверки (makemigrations --check --dry-run, compileall, runserver GET /),
  AGENTS_REPORT, финальный анализ, коммит.

## 8. Исправления после проверок

- После первого прогона тестов (5 ошибок NameError в `views.py`) — добавлены недостающие
  импорты `Watch`, `WatchNotification`, `Share` в `dashboard/api/v1/views.py`.
- После прогона с дублем (`IntegrityError`) — добавлена валидация дублей в `WatchSerializer.validate()`.
- После `makemigrations --check --dry-run` (без изменений) и `compileall` (без ошибок) —
  дополнительные правки не потребовались; финальный прогон `manage.py test` — 25/25 OK.

## 9. Команды проверки

Выполнены в конце работы (рабочая директория проекта, `python` из `.venv`):

1. `.venv/bin/python manage.py check` → «System check identified no issues (0 silenced)».
2. `.venv/bin/python manage.py makemigrations --check --dry-run` → «No changes detected».
3. `.venv/bin/python manage.py migrate --noinput` → все миграции применены OK.
4. `.venv/bin/python manage.py test` → «Ran 25 tests … OK».
5. `python -m compileall -q config dashboard user manage.py` → без ошибок (exit 0).
6. `.venv/bin/python manage.py runserver 127.0.0.1:8001 --noreload` (фоновый процесс) →
   `curl http://127.0.0.1:8001/` → **200 OK**; сервер остановлен.

## 10. Результаты всех проверок

| Проверка | Результат |
|---|---|
| `python manage.py check` | 0 issues |
| `makemigrations --check --dry-run` | No changes detected |
| `migrate --noinput` | OK (миграции 0001…0008, user 0001) |
| `python manage.py test` | **25/25 OK** |
| `compileall -q config dashboard user manage.py` | OK (exit 0) |
| runserver + `GET /` | 200 OK |

## 11. Количество тестов

- **До изменений (исходный код): 13 тестов** (`dashboard/tests.py`, только CRUD акций и API).
- **После изменений: 25 тестов** (`DashboardTests`: HTML/REST API 13; `WatchTests`: мониторинг 12 —
  создание, валидация цены, дубль, приватность списка/доступа/удаления, срабатывание условия,
  дедупликация, сброс условия и повторное срабатывание, направление `lte`, отсутствие цены).

## 12. Время или порядок выполнения этапов

Порядок: Задание 1 (анализ) → Задание 2 (требования) → Задание 3 (аудит/исправления:
зависимости, конфигурация, Tinkoff-клиент, аутентификация, права, Celery, тесты) →
Задание 4 (мониторинг акций: модели, миграция, сервис, API/HTML, тесты) → повторные
проверки → отчёт/финальный анализ → коммит/пуш. Каждый этап закрывался прогоном
тестов; итоговые проверки выполнены один раз после всех правок (п.9).

## 13. Ограничения среды

- **Python 3.12.16** — официально Django 4.1.7 не поддерживает 3.12; пакеты `grpcio`/`protobuf`
  не имеют колёс, а `tinkoff-investments`/`tinkoff` отсутствуют на PyPI — потребовалась
  замена Tinkoff SDK на внутренний REST-клиент.
- **Нестабильная сеть к `files.pythonhosted.org`** — установка зависимостей шла с перебоями.
- **PostgreSQL/Redis не были доступны локально** — сделано SQLite по умолчанию (PostgreSQL
  по-прежнему поддерживается через `DJANGO_DATABASE_URL`); Redis остаётся брокером Celery.
- Зависимости не устанавливаются «в лоб» на Python 3.12 — зафиксировано и обходной путь
  описан (см. п.6, п.2).

## 14. Изменения, относящиеся к Заданию 3 (технический аудит и исправления)

- `requirements.txt` (уязвимые/несуществующие зависимости),
- `config/settings.py`, `config/celery.py` (SECRET_KEY, ALLOWED_HOSTS, SQLite по умолчанию,
  исправленное beat-расписание, логирование),
- `dashboard/services/tinkoff_client.py` (новый внутренний клиент: отсутствие токена, пустые
  ответы, ошибки API — пп. D-03, D-05),
- `dashboard/services/market_data.py`, `dashboard/services/graph.py` (Decimal-цены, обработка
  ошибок — D-04, D-05),
- `dashboard/tasks.py` (логирование, per-share обработка ошибок),
- `dashboard/api/permissions.py`, `dashboard/api/v1/views.py`, `dashboard/views.py`,
  `dashboard/forms.py` (права доступа, валидации — D-01, D-02, D-06),
- `dashboard/models.py` (Decimal для цен — D-04),
- `user/models.py`, `user/forms.py`, `user/migrations/0001_initial.py` (восстановление
  неработоспособной аутентификации),
- `dashboard/tests.py` (новые тесты на исправленные проблемы),
- мелкие исправления шаблонов, `get_object_or_404`, опечатки.

## 15. Изменения, относящиеся к Заданию 4 (новая функциональность — персональный мониторинг акций)

- `dashboard/models.py` — модели `Watch` (user, share, target_price, direction `gte`/`lte`,
  `created_at`, `last_triggered`, UniqueConstraint `(user, share)`) и `WatchNotification`
  (watch, message, `triggered_at`); `WATCH_DIRECTIONS`; `Share.__str__`;
- `dashboard/migrations/0008_watch_watchnotification_and_more.py`;
- `dashboard/services/watching.py` — проверка условий при обновлении цены, дедупликация,
  сброс условия (см. решение о направлении и дедупликации в ANALYSIS.md, п.17);
- `dashboard/tasks.py` — вызов `check_watches_for_share(share)` после обновления цены;
- `dashboard/api/v1/views.py`, `router.py`, `serializer.py` — REST API `watches` и
  `watch-notifications` (IsAuthenticated, только свои записи);
- `dashboard/views.py`, `urls.py`, `forms.py`, `templates/dashboard/watch_*.html` (4 шт.) —
  HTML-интерфейс: список своих наблюдений, создание, удаление, список уведомлений;
- `dashboard/tests.py` — блок `WatchTests` (12 тестов).

Порядок «направление выше/равна / ниже/равна» реализован через строковые ключи
`"gte"`/`"lte"` (plain tuple choices вместо TextChoices — из-за pitfalls Django 4.1.7
в `CharField.formfield()`); API-интерфейс использован как основной (HTML поверх — для
полноты пользовательского сценария).

## 16. Итог проверок после финальных правок

Все обязательные проверки (п.9) пройдены, дерево готово к коммиту.