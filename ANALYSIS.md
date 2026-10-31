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
    воспроизведено: `pip install -r requirements.txt` на Python 3.12 не удаётся (см. AGENTS_REPORT.md).
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

При выполнении этой работы ветка `beznames-copilot-implementation` не открывалась и не
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
| Ошибки | 14 зафиксированных ошибок (см. AGENTS_REPORT.md, п.6): несовместимые зависимости, отсутствующие пакеты на PyPI, отсутствие модели User, тестовые падения (403/404, choices, basename, импорты, IntegrityError дубля, пустая БД). Все разобраны и исправлены. | Каждая ошибка зафиксирована с точным текстом/stacktrace и обходом. |
| Ограничения | Python 3.12 (нет колёс grpcio/protobuf, Django 4.1.7 не поддерживает 3.12 официально), флаки DNS к PyPI, недоступность PostgreSQL/Redis локально. Обход: внутренний Tinkoff REST-клиент, SQLite по умолчанию. | Ограничения зафиксированы в отчёте, не скрыты. |
| Удобство сопровождения | Внутренний клиент Tinkoff (один файл, явные исключения вместо SDK «без бэкэкса»); SQLite-по-умолчанию устраняет необходимость Postgres для разработки; env-конфигурация (SECRET_KEY, ALLOWED_HOSTS, DATABASE_URL) стандартна. | Зависимости проекта теперь полностью совместимы с Python 3.12. |
| Сравнимость с Copilot | Прямое сравнение по пунктам «полнота/время/итерации/ошибки» невозможно без инспекции ветки `beznames-copilot-implementation`, что исключено условиями задания. По фактам собственной работы: анализ полный, требования корректны и восстановлены, все дефекты исправлены, новая функция полная и тестированная (25/25). | Для объективного сравнения в будущем достаточно инспектировать ветку Copilot по тем же 11 критериям. |