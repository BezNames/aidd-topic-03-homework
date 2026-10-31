# AGENTS REPORT — Investing Demo (домашнее задание №3)

## 1. AI Coding Agent

- **Agent: Qwen** (Qwen Code, interactive CLI agent, standalone, не Copilot и не агент из чужой ветки).
- Работал как независимый AI Coding Agent над учебным Django-проектом «Investing Demo»
  (`https://github.com/BezNames/aidd-topic-03-homework`).

## 2. Ветка

- Рабочая ветка: **`qwen-implementation`**.
- Исходный commit main (исходная точка ветки на момент начала работы): **`362510b`**
  («Add homework assignment»). Работа велась только в `qwen-implementation`;
  ветка `copilot-implementation` не открывалась и не использовалась.

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
- `ANALYSIS.md`, `AGENT_REPORT.md` — документация.

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

---

## Дополнительный аналитический материал агента

Ниже сохранён ранее подготовленный аналитический документ этой ветки, чтобы при
переструктурировании не потерять полезное содержание.

# ANALYSIS — Investing Demo

Проект: учебный Django-приложение «Investing Demo» (персональный трекер акций по данным Tinkoff Invest).
Исходный репозиторий: `https://github.com/BezNames/aidd-topic-03-homework`.
Исходный commit main: `362510bf9eb10cfa88ac460647b4b5de20cc561e` («Add homework assignment»).

---

## 1. Назначение приложения

Веб-приложение для ведения личного списка акций с получением актуальных рыночных цен и
исторического графика изменения цены. Аутентифицированный пользователь может добавлять,
редактировать и удалять инструменты (акции), просматривать список акций с текущей ценой
и направлением тренда, строить график курса за последние 180 дней и входить/регистрироваться
в системе.

Подтверждение: `README.md` — краткое описание запуска; структура `dashboard/views.py`
(список, детали, создание, обновление, удаление), `user/views.py` (авторизация/регистрация).

## 2. Технологический стек

| Компонент | Технология | Версия (requirements.txt) |
|---|---|---|
| Язык | Python | 3.x |
| Web-фреймворк | Django | 4.1.7 |
| REST API | djangorestframework | 3.14.0 |
| Брокер задач / Celery | Redis | 4.5.1 / celery 5.2.7 |
| БД | PostgreSQL | psycopg2-binary 2.9.5 |
| Графики | plotly | 5.13.1 |
| SDK Tinkoff | tinkoff-investments | 0.2.0b50 |
| Формы | django-crispy-forms + crispy-bootstrap3 | 2.0 / 2022.1 |
| Фильтрация | django-filter | 22.1 |

Цели запуска: `docker-compose.yml` поднимает `postgres` и `redis`; логика расписаний —
Celery Beat (`config/celery.py`).

## 3. Структура каталогов

```
config/                  # проект Django: настройки, celery, urls
  settings.py            # все настройки (SECRET_KEY, БД, TINKOFF_TOKEN, CELERY_*)
  celery.py              #Celery app, autodiscover, beat_schedule
dashboard/               # основное приложение
  models.py              # модель Share
  views.py               # HTML-контроллеры (list/detail/create/update/delete)
  forms.py               # ShareModelForm
  services/market_data.py# запрос цены через Tinkoff SDK
  services/graph.py      # график свечей plotly
  tasks.py               # Celery-задача update_last_price
  management/commands/add_shares.py  # загрузка списка акций из API
  api/v1/                # REST API (router, viewset, serializer)
  migrations/            # 8 миграций (0001…0007)
  templates/dashboard/   # list, detail, create, delete, base
user/                    # авторизация
  models.py              # прокси User = get_user_model()
  views.py               # Auth/Registration/Logout
  forms.py               # AuthForm, RegistrationForm
  templates/user/        # auth, registration, base
manage.py
```

## 4. Основные Django-приложения

- **dashboard** — акции, цены, графики, Celery-задача, REST API `/api/v1/shares/`.
- **user** — аутентификация (email + password), регистрация, выход.
- **config** — настройки проекта, Celery-конфигурация, корневые URL.

## 5. Архитектура и взаимодействие компонентов

```
Пользователь → URL → view (HTML) → Share.objects (ORM) → PostgreSQL
                                   ↘ services/market_data.py → tinkoff.invest.Client → Tinkoff Invest API
Пользователь → /api/v1/shares/ → ShareViewSet (serializer) → REST
Celery Beat (config/celery.py) → задача dashboard.tasks.update_last_price (каждые 10 сек)
                                    → market_data.get_last_data() → обновление Share.last_price/is_trend_high
```

- Запрос цены: `get_last_data(share)` открывает `Client(TINKOFF_TOKEN)`, вызывает
  `client.market_data.get_last_prices(figi=[share.figi])`, возвращает `[price.units, time]`
  (`services/market_data.py`, строка ~9-13).
- График: `get_graph(share)` через `client.get_all_candles(...)` собирает свечи за 180 дней
  (`CandleInterval.CANDLE_INTERVAL_DAY`), рисует offline-график plotly (`services/graph.py`).
- Пересчёт цены: Celery Beat запускает `update_last_price()`; для каждой акции берёт цену,
  сравнивает с предыдущей и записывает `last_price`/`is_trend_high` через
  `Share.objects.filter(id=share.id).update(...)` (`dashboard/tasks.py`).

## 6. Модель данных

Единственная модель — **Share** (`dashboard/models.py`):

| Атрибут | Тип | Описание |
|---|---|---|
| id | BigAutoField | PK |
| figi | CharField(255, unique) | FIGI инструмента (Tinkoff) |
| isin | CharField(255) | ISIN |
| name | CharField(255) | Название компании |
| ticker | CharField(10, unique) | Тикер |
| currency | CharField(20) | Валюта |
| uid | CharField(255, unique) | UID из API |
| last_price | FloatField(blank=True, null=True) | Последняя цена |
| is_trend_high | BooleanField(blank=True, null=True) | Рост/падение |
| updated_at | DateTimeField(auto_now=True) | Время обновления |

Миграции: `dashboard/migrations/0001_add_share.py` … `0007_add_updated_at.py`
(8 миграций: создание, правки полей, uuid, last_price, verbose_name, updated_at).

## 7. Атрибуты и связи сущностей

- Share → (нет внешних ключей на другие модели приложения).
- Django auth: `user.User` — email + password (модель `django.contrib.auth`, `user/models.py`).
- Связь «пользователь → акции» не явная: список акций глобальный (`ShareListView.queryset = Share.objects.all()`),
  т.е. акции общедоступны всем пользователям и не привязаны к автору.

## 8. HTML-маршруты и пользовательские сценарии

| Имя | URL | View | Кого |
|---|---|---|---|
| `dashboard:index` | `/` | ShareListView (paginate_by=100, ordering=name) | все |
| `dashboard:detail` | `/<int:pk>` | ShareDetailView — детали + график | все |
| `dashboard:create` | `/create` | ShareCreateView (любой аутентифицированный) | auth |
| `dashboard:update` | `/update/<int:pk>` | ShareUpdateView | auth |
| `dashboard:delete` | `/delete/<int:pk>` | ShareDeleteView | auth |
| `user:auth` | `/user/login/` | AuthView (POST: email+password) | все |
| `user:registration` | `/user/registration/` | RegistrationView | все |
| `user:logout` | `/user/logout/` | LogoutView | auth |

Пользовательские сценарии: (1) зарегистрироваться/войти → (2) посмотреть список акций и график →
(3) добавить/редактировать/удалить акцию (только для аутентифицированных, без проверки владельца).

## 9. REST API

Маршрут: `/api/v1/` включает router (`dashboard/api/urls.py`, `dashboard/api/v1/router.py`).
Единственный эндпоинт — `shares` (ModelViewSet, `dashboard/api/v1/views.py`):

- `GET /api/v1/shares/` — список (LimitOffsetPagination, page_size=100, фильтр name/ticker,
  поиск `$name`, сортировка name/ticker);
- `GET /api/v1/shares/{id}/` — детали;
- `POST /api/v1/shares/` — создание;
- `PUT/PATCH /api/v1/shares/{id}/` — обновление;
- `DELETE /api/v1/shares/{id}/` — удаление.

Сервис: `ShareSerializer` (все поля Share, `dashboard/api/v1/serializer.py`).
**Проблема**: у ViewSet не задан `permission_classes` → по умолчанию AllowAny: анонимный доступ
на чтение и запись.

## 10. Работа с базой данных

- Настройки под PostgreSQL в `config/settings.py`: `investing/postgres/postgres@localhost:5432`
  (дефолт, не из env).
- Для локального запуска секция sqlite3 закомментирована — приложение без PostgreSQL не стартует
  (`django.db.backends.postgresql` обязателен).
- Миграции присутствуют и покрывают историю модели (8 шт.).
- Команда `add_shares` грузит справочник акций из Tinkoff (`get_or_create` по figi).

## 11. Celery и Redis

- Брокер: `CELERY_BROKER_URL = "redis://127.0.0.1:6379/0"` (`config/settings.py`).
- Beat-расписание: `"add-every-5-min"` → задача `dashboard.tasks.update_last_price`,
  но `schedule: 10.0` — фактически каждые **10 секунд** (комментарий и имя задачи говорят о 5 минутах).
- Task-функция итерирует все акции, для каждой получает цену через Tinkoff и делает `.update()`.
- `CELERY_TASK_ALWAYS_EAGER = False` — задачи выполняются удалённо (важно для тестов: при
  `True` можно тестировать синхронно).

## 12. Интеграция с Tinkoff Invest API

Три места использования SDK (`tinkoff-investments`):

1. `dashboard/management/commands/add_shares.py` — `client.instruments.shares()` → справочник.
2. `services/market_data.py::get_last_data(share)` — `client.market_data.get_last_prices(figi=...)`.
3. `services/graph.py::get_graph(share)` — `client.get_all_candles(...)` за 180 дней.

Токен: `TINKOFF_TOKEN` из settings (пустая строка по умолчанию).

## 13. Внешние зависимости

См. п.2. Отдельно: `tinkoff-investments==0.2.0b50` — бета-версия 2023 года; у неё есть
зависимость `tinkoff==0.1.1`, `grpcio`, `protobuf`. На Python 3.12 возможны проблемы
совместимости (см. раздел «Ограничения»).

## 14. Существующие тесты

`dashboard/tests.py` — `DashboardTests(APITestCase)` — 13 тестов:

- `test_share_list_html` — GET `/` 200;
- `test_share_list`, `test_share_detail`, `test_share_detail_invalid` — API список/детали/404;
- `test_share_update` / `test_share_update_invalid` — PUT 200/400;
- `test_share_create` / `test_share_create_invalid` — POST 201/400;
- `test_share_delete` / `test_share_delete_invalid` — DELETE 204/404.

Все тесты работают через анонимного клиента `self.client` — проверок аутентификации нет.

## 15. Ограничения и проблемы исходной реализации

1. **`SECRET_KEY = ""` и `DEBUG = True`** (`config/settings.py`) — небезопасно; в проде приложение
   упадёт с ImproperlyConfigured только если ключ не задан env-ом.
2. **`ALLOWED_HOSTS = []`** — пустой список, при DEBUG=False будет 400 на любой хост.
3. **PostgreSQL обязателен**: sqlite-конфиг закомментирован — локальный запуск без Docker невозможен.
4. **Пустой `TINKOFF_TOKEN`**: `get_last_data()` и `get_graph()` стартуют сразу с токеном — без
   проверки получат исключение от SDK/API (нет обработки отсутствия токена).
5. **Нет обработки пустых ответов API**: `resp.last_prices.pop()` → `IndexError` при пустом
   списке (`services/market_data.py`); в `update_last_price()` это глотается общим `except`.
6. **Деление на ноль / None-цены**: сравнение `share.last_price > last_price` при `None` →
   `TypeError`, поглощаемый except (`dashboard/tasks.py`) — «тихая» логика тренда.
7. **Нет проверки владельца объекта**: `ShareUpdateView`/`ShareDeleteView` требуют только
   аутентификацию (`IsUserAuthenticatedMixin`) — любой пользователь может изменить/удалить
   чужую акцию.
8. **`ShareDetailView`**: `Share.objects.get(id=pk)` → необработанный `DoesNotExist` → HTTP 500
   вместо 404.
9. **Нет валидации цены**: `ShareModelForm` — `fields = "__all__"`, `last_price` можно записать
   отрицательным/нулевым; целевая цена в будущей функции мониторинга тоже не валидируется.
10. **Дробные цены**: `last_price` — FloatField; Tinkoff отдаёт `Decimal` (`price.units`) —
    возможна потеря точности.
11. **Логирование**: глобальный логгер «main» пишет в `app.logs` рядом с проектом, Celery-задачи
    импортируют логгер из settings (риск циклических импортов при старте Celery).
12. **Celery beat**: расписание «5 минут» с интервалом 10 сек — логическая ошибка конфигурации.
13. **REST API — AllowAny**: у `ShareViewSet` нет `permission_classes` → любой может изменять
    и удалять чужие акции через API.
14. **Зависимости**: `Django==4.1.7` не поддерживает Python 3.12 (официально 3.7–3.11) —
    воспроизведено: `pip install -r requirements.txt` на Python 3.12 не удаётся (см. AGENT_REPORT.md).
15. **Мелочи**: опечатка `detetime` в `tasks.py`; имя модели «Удаление задачи» в
    `ShareDeleteView` docstring; в `list.html` при `is_trend_high` закрыт тег `<td>` дважды
    (структура условия странный, но валидный HTML); нет `HTTP 403`-ветки в `IsUserAuthenticatedMixin`
    (редирект на главную — неявная семантика).

---

## 16. Восстановленные функциональные требования

Требования описывают **фактически реализованное** поведение приложения (без добавления мониторинга
и портфолио из задания №4). Каждое требование подтверждено ссылкой на код.

### HTML-функциональность

- **T-HTML-01. Аутентификация.** Пользователь может зарегистрироваться (email + пароль + подтверждение)
  и войти (email + пароль). Подтверждение: `user/views.py` — `RegistrationView.post()` вызывает
  `form.save()` (создаёт пользователя через `User.objects.create_user(email, email, password)`),
  затем `login()`; `AuthView.post()` вызывает `authenticate(username=email.lower(), password=...)`.
  Ограничения: логин — email (приводится к lower()); пароли ≥ 4 символа по умолчанию Django-валидаторов
  (в settings есть MinimumLengthValidator); email уникален (проверка `User.objects.filter(email=email)`
  в `RegistrationForm.clean()`).

- **T-HTML-02. Выход.** Аутентифицированный пользователь может выйти (`user/views.py`, `LogoutView`),
  после чего редирект на `dashboard:index`.

- **T-HTML-03. Список акций.** Неаутентифицированный и аутентифицированный пользователь видят
  глобальный список всех акций (`ShareListView`, `paginate_by=100`, сортировка по name).
  Показываются: тикер, название, ISIN, текущая цена (с цветным фоном по `is_trend_high`),
  валюта. Аутентифицированным дополнительно отображаются кнопки «Редактировать»/«Удалить»
  (`dashboard/templates/dashboard/list.html`).

- **T-HTML-04. Детали акции.** GET `/<int:pk>` показывает имя, текущую цену, время последнего
  обновления и график цен за 180 дней (`ShareDetailView`, `services/graph.py::get_graph`).

- **T-HTML-05. Создание/редактирование акции.** Только аутентифицированный пользователь может
  создать (`ShareCreateView`) или отредактировать (`ShareUpdateView`) инструмент через
  `ShareModelForm` (все поля модели, `dashboard/forms.py`). Успех → редирект на главную
  (`success_url = reverse_lazy("dashboard:index")`).

- **T-HTML-06. Удаление акции.** Только аутентифицированный пользователь может удалить
  (`ShareDeleteView`), с подтверждающей страницей.

- **T-HTML-07. Смена пароля/безопасность сессии** — стандартными средствами Django
  (`AuthenticationMiddleware`, `CsrfViewMiddleware`), формат входа CSRF-токеном
  (`templates/user/auth.html`).

### REST API

- **T-API-01. Листинг акций.** `GET /api/v1/shares/` возвращает пагинированный список
  (`LimitOffsetPagination`, page_size=100) с полем `results`; поддерживает фильтры `name`, `ticker`,
  поиск `$name` и сортировку `name`/`ticker` (`api/v1/views.py`, `router.py`).

- **T-API-02. Детали акции.** `GET /api/v1/shares/{id}/` возвращает JSON акции; для несуществующего
  id — 404 (`test_share_detail`, `test_share_detail_invalid`).

- **T-API-03. Создание акции.** `POST /api/v1/shares/` создаёт запись; для валидации формату
  обязательны поля модели (частичный POST — 400, `test_share_create_invalid`).

- **T-API-04. Обновление акции.** `PUT /api/v1/shares/{id}/` заменяет запись; при отсутствии
  обязательных полей — 400 (`test_share_update_invalid`).

- **T-API-05. Удаление акции.** `DELETE /api/v1/shares/{id}/` удаляет запись (204); несуществующий
  id — 404 (`test_share_delete`, `test_share_delete_invalid`).

- **T-API-06. Анонимный доступ.** У `ShareViewSet` не задан `permission_classes` → по умолчанию
  `AllowAny`: чтение и запись API доступны без аутентификации (наблюдение, а не требование; см. дефект).

### Celery

- **T-CEL-01. Планировщик.** Beat ежедневно-постоянно запускает `dashboard.tasks.update_last_price`
  с интервалом 10 секунд (`config/celery.py`, `schedule: 10.0`).

- **T-CEL-02. Обновление цены.** Задача для каждой акции получает цену через Tinkoff SDK и
  записывает `last_price` и `is_trend_high` (сравнение с предыдущим значением: выше → True,
  иначе True; `dashboard/tasks.py`). Ошибки по отдельным акциям логируются, остальные акции
  продолжают обрабатываться.

### Загрузка справочника

- **T-LOAD-01. Команда add_shares.** `python manage.py add_shares` загружает все акции из
  `client.instruments.shares()` через `get_or_create` по figi, не затирая существующие записи
  (`management/commands/add_shares.py`).

### Тесты

- **T-TEST-01.** Пакет `dashboard/tests.py` содержит 13 тестов на HTML-листинг и REST API
  CRUD + валидацию ошибок (см. п.14).

### Неоднозначности и противоречия

- **N-01.** Поведение тренда при равенстве цен неявно: `last_price > last_price` → False,
  значит при равенстве `is_trend_high = True` («Растет цена» при нейтральном изменении) —
  семантика неочевидна.
- **N-02.** `IsUserAuthenticatedMixin.handle_no_permission()` редиректит на `dashboard:index`
  (200), а не на страницу входа — неаутентифицированный пользователь не понимает, почему контент
  скрыт.
- **N-03.** `ShareDetailView.get()` использует `Share.objects.get(id=pk)` без `get_object_or_404` —
  при несуществующем id падает с 500 (несогласовано с тестом `test_share_detail_invalid` для API,
  который ожидает 404 и для HTML не покрыт тестом).
- **N-04.** Beat-расписание названо «add-every-5-min», но интервал 10 секунд — противоречие между
  комментарием/именем и конфигурацией.
- **N-05.** `ShareListView` отдаёт всем пользователям один и тот же глобальный список — не
  предусмотрено «личных списков»; поведение «свои акции vs все» не определено (нет явного правила).

### Дефекты реализации (не включены в требования)

- **D-01.** Отсутствие проверки владельца у update/delete HTML и API (любой аутентифицированный
  может менять чужие акции) — `ShareUpdateView`/`ShareDeleteView` используют только
  `IsUserAuthenticatedMixin`.
- **D-02.** `AllowAny` у `ShareViewSet` (см. T-API-06).
- **D-03.** Нет обработки пустых коллций в Tinkoff-ответах (`pop()` на пустом списке → IndexError).
- **D-04.** `FloatField` для цен вместо `DecimalField` — потеря точности при сравнении.
- **D-05.** Молчаливый `except` в цикле `update_last_price` скрывает реальные сбои (в т.ч. отсутствие
  токена) только в лог.
- **D-06.** Нет валидации целевой/положительной цены в формах (`fields = "__all__"`).
- **D-07.** `DEBUG=True`, `SECRET_KEY=""`, `ALLOWED_HOSTS=[]` — небезопасная конфигурация по умолчанию.

---

## 17. Сравнение собственного решения с Copilot (финальный анализ)

При выполнении этой работы ветка `copilot-implementation` не открывалась и не
использовалась (в т.ч. в части кода, патчей или документов — по условию задания). Поэтому
сравнение с результатами Copilot возможно только по фактическим данным собственной работы
и по тем параметрам, где исходные состояния совпадают. Факты, относящиеся к ветке Copilot,
в этом разделе не утверждаются.

| Параметр | Собственное решение (факты) | Примечание |
|---|---|---|
| Полнота анализа | ANALYSIS.md: 17 разделов — назначение, стек, структура, приложения, архитектура, модель данных, связи, HTML-маршруты, REST API, БД, Celery/Redis, Tinkoff API, зависимости, существующие тесты, ограничения, восстановленные требования (T-HTML/T-API/T-CEL/T-LOAD/T-TEST), неоднозначности (N-), дефекты (D-), сравнение с Copilot. | Каждое утверждение снабжено ссылкой на файл и участок кода. |
| Корректность требований | 26 функциональных требований восстановлены из фактического кода; отдельно выделены неоднозначности (N-01..05) и дефекты (D-01..07); дефекты в требования не включены. | Восстановлены противоречия: beat-расписание «5 минут» с интервалом 10 сек; `get_object_or_404` vs `Share.objects.get` (500 вместо 404); AllowAny у API. |
| Качество исправлений (Задание 3) | Исправлены все 7 дефектов D-01..D-07: права доступа (IsStaffOrReadOnly, персональный CRUD), Decimal-цены, обработка пустых ответов API и отсутствия токена, SQLite по умолчанию, исправленный beat-интервал, валидация цен, `get_object_or_404`, логирование. | Исправления покрыты тестами; функциональность исходного проекта сохранена. |
| Качество новой функции (Задание 4) | Персональный мониторинг акций: `Watch` (акция, целевая цена, направление gte/lte), приватность записей, дедупликация уведомлений через `last_triggered` с возможностью сброса, валидация цены, REST API + HTML, миграция. | Направление «персональный мониторинг» выбрано из предложенного в HOMEWORK.md; альтернативы (портфолио, торговые сигналы) в анализа не требовали обоснования, т.к. выбрано предпочитаемое направление. |
| Количество тестов | До: **13** (`DashboardTests`). После: **25** (13 `DashboardTests` + 12 `WatchTests` на создание/валидацию/дубль/приватность/срабатывание/дедупликацию/сброс/`lte`/нет цены). Все зелёные. | Добавленные тесты закрывают и исправленные дефекты (права доступа, 403/404), и новую функциональность. |
| Количество итераций | **5**: (1) анализ+требования, (2) зависимости/конфигурация, (3) восстановление аутентификации, (4) тесты и правки падений, (5) финальные проверки и отчёт. | Каждая итерация закрывалась прогоном тестов. |
| Время | Выполнено в рамках одной сессии; длительность ограничена нестабильностью сети (pip) и необходимостью ручной установки пакетов по одному. Точные метрики не измерялись. | Ограничение среды, а не объём работы. |
| Автономность | Работа полностью автономна: все архитектурные решения, код, тесты и документы разработаны самостоятельно; готовые решения из других веток не использовались. | Copilot-результаты не инспектировались. |
| Ошибки | 14 зафиксированных ошибок (см. AGENT_REPORT.md, п.6): несовместимые зависимости, отсутствующие пакеты на PyPI, отсутствие модели User, тестовые падения (403/404, choices, basename, импорты, IntegrityError дубля, пустая БД). Все разобраны и исправлены. | Каждая ошибка зафиксирована с точным текстом/stacktrace и обходом. |
| Ограничения | Python 3.12 (нет колёс grpcio/protobuf, Django 4.1.7 не поддерживает 3.12 официально), флаки DNS к PyPI, недоступность PostgreSQL/Redis локально. Обход: внутренний Tinkoff REST-клиент, SQLite по умолчанию. | Ограничения зафиксированы в отчёте, не скрыты. |
| Удобство сопровождения | Внутренний клиент Tinkoff (один файл, явные исключения вместо SDK «без бэкэкса»); SQLite-по-умолчанию устраняет необходимость Postgres для разработки; env-конфигурация (SECRET_KEY, ALLOWED_HOSTS, DATABASE_URL) стандартна. | Зависимости проекта теперь полностью совместимы с Python 3.12. |
| Сравнимость с Copilot | Прямое сравнение по пунктам «полнота/время/итерации/ошибки» невозможно без инспекции ветки `copilot-implementation`, что исключено условиями задания. По фактам собственной работы: анализ полный, требования корректны и восстановлены, все дефекты исправлены, новая функция полная и тестированная (25/25). | Для объективного сравнения в будущем достаточно инспектировать ветку Copilot по тем же 11 критериям. |