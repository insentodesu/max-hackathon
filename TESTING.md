# Тестирование backend и чат-бота (Docker)

> Mini app (frontend) сейчас не трогаем. Все проверки выполняем только в Docker.

## 1. Предпосылки

- Docker Engine 20.10+ и Docker Compose v2 (`docker compose`).
- Клонированный репозиторий `edumax`.
- Токен Max-бота (`BOT_TOKEN`), который будет обрабатывать сообщения в чате.

## 2. Переменные окружения (файл `.env` рядом с `docker-compose.yml`)

Docker Compose автоматически считывает `.env`, лежащий рядом с `docker-compose.yml`, и подставляет значения в секцию `environment`. Создайте в корне (`edumax/.env`) файл со всеми нужными переменными:

```env
# Backend
SECRET_KEY=supersecret
API_V1_PREFIX=/api/v1
DATABASE_URL=sqlite:////data/app.db
STATIC_ROOT=/data/static
STATIC_DIR=/data/static
STATIC_URL=/static
BOT_NOTIFY_BASE_URL=http://bot:8080
BOT_NOTIFY_TOKEN=my-bot-secret          # используется и backend-ом, и ботом
BOT_DEFAULT_SENDER_MAX_ID=1

# YooKassa (можно оставить пустыми, если не тестируем платежку)
YOOKASSA_SHOP_ID=
YOOKASSA_SECRET_KEY=
YOOKASSA_TEST_MODE=true

# Bot service
BOT_TOKEN=<токен из Max>
HTTP_BACKEND_TOKEN=my-bot-secret        # должен совпадать с BOT_NOTIFY_TOKEN
LOG_LEVEL=debug
BACKEND_API_BASE_URL=http://backend:8000/api/v1

# Фронт не используем, но переменная для build аргумента все равно может пригодиться
VITE_API_TOKEN=
```

> Теперь нет необходимости создавать отдельный `backend/.env`: все значения попадают в контейнер напрямую через `docker-compose.yml`.


## Тестовые данные для регистрации в боте

После запуска `./scripts/test-backend-bot.sh` база уже содержит тестовые данные из `backend/seed_*.py`. Ниже перечислены готовые профили — можно взять любого пользователя и пройти регистрацию полностью. Университет и подразделения у всех примеров одинаковые:  
**Московский государственный университет имени М.В. Ломоносова → факультет «Факультет информатики и вычислительной техники» → кафедра «Кафедра информатики» → группа «ИВТ-21-01» (или «ИВТ-21-02» для второго студента).**

### Студенты (роль `student`)
1. **Иванов Иван Иванович**  
   - Университет/факультет/кафедра/группа: см. описание выше.  
   - Город: Москва.  
   - Студенческий билет: `STU001`.
2. **Петров Пётр Петрович**  
   - Те же университет и факультет, группа `ИВТ-21-02`.  
   - Город: Москва.  
   - Студенческий билет: `STU002`.
3. **Сидоров Сидор Сидорович**  
   - Группа `ИВТ-21-01`.  
   - Город: Москва.  
   - Студенческий билет: `STU003`.

### Преподаватели (роль `staff`, ветка преподавателя)
1. **Профессоров Александр Иванович**  
   - Университет и факультет из описания выше, кафедра «Кафедра информатики».  
   - Город: Москва.  
   - Табельный номер: `TCH001`.
2. **Доцентов Сергей Петрович** — та же кафедра, табельный `TCH002`, город Москва.  
3. **Ассистентов Владимир Николаевич** — табельный `TCH003`, город Москва.

### Сотрудники деканата (роль `staff`, ветка административного персонала)
1. **Деканов Иван Петрович**  
   - Университет/факультет/кафедра: как в описании.  
   - Город: Москва.  
   - Табельный номер: `STF001`.
2. **Секретарев Мария Сергеевна** — табельный `STF002`, Москва.  
3. **Администраторов Андрей Николаевич** — табельный `STF003`, Москва.

Чтобы выйти на конкретного пользователя, в боте выбери указанные университет, факультет, кафедру/группу и введи его ФИО вместе с соответствующим номером (студенческий или табельный). Это гарантированно найдёт запись в базе и позволит протестировать весь сценарий регистрации.

## 3. Запуск контейнеров

### Вариант со скриптом

```bash
chmod +x scripts/test-backend-bot.sh
./scripts/test-backend-bot.sh
```

Скрипт делает следующее:
- запускает `backend` и `bot` (``docker compose up -d backend bot``);
- ждёт, пока `/health` и `/healthz` начнут отвечать;
- внутри `backend` выполняет `./init_db.sh`, чтобы накатывать схему и сиды (можно пропустить: `SKIP_SEED=1 ./scripts/test-backend-bot.sh`);
- выводит ответы health-check и текущее состояние контейнеров.

Параметры можно переопределять переменными окружения:
- `COMPOSE_CMD="docker compose -p edumax-dev" ./scripts/test-backend-bot.sh`;
- `BACKEND_HEALTH_URL="http://localhost:18000/health" ...`.

### Ручной запуск

```bash
docker compose up --build backend bot

# После старта контейнеров
docker compose exec backend bash -lc "bash ./init_db.sh"
```

`init_db.sh` создаёт схему и заполняет тестовыми данными (университеты, студенты, расписание, события, заявки, платежи и т. д.).

## 4. Базовые проверки backend

Все запросы идут на `http://localhost:8000/api/v1/...`. Авторизация — Bearer-токен.

1. Health:
   ```bash
   curl -s http://localhost:8000/health
   ```
2. Swagger UI:
   открыть `http://localhost:8000/docs` и убедиться, что endpoints прогружаются.
3. Получить токен (пример с `max_id=1001`, возьмите любой из сидов):
   ```bash
   TOKEN=$(curl -s "http://localhost:8000/api/v1/auth/login-by-max-id?max_id=1001" | jq -r .access_token)
   ```
4. Расписание:
   ```bash
   curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/schedule/today
   ```
5. Заявки:
   ```bash
   curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/requests/my
   ```
6. Платежи:
   ```bash
   curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/payments/balance
   curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/payments
   ```
7. Рассылки (роль STAFF/ADMIN):
   ```bash
   curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/broadcasts/my
   ```

Убеждаемся, что ответы корректны и в `docker compose logs backend` нет ошибок 5xx.

## 5. Базовые проверки чат-бота

1. HTTP API:
   ```bash
   curl -s http://localhost:8080/healthz
   ```
2. Max Messenger:
   - написать боту `/start`;
   - проверить, что появляется главное меню и работают ветки расписания, заявок и платежей.
3. В логах `bot` (``docker compose logs -f bot``) видно входящие сообщения и ответы.

## 6. Интеграция backend → bot

1. `BOT_NOTIFY_TOKEN` (backend) == `HTTP_BACKEND_TOKEN` (bot).
2. Войти в backend как админ/сотрудник (через авторизацию и получение Bearer-токена).
3. Создать рассылку:
   ```bash
   curl -s -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"title":"Тест","message":"Hello","group_id":null,"faculty_id":null}' \
        http://localhost:8000/api/v1/broadcasts
   ```
   В логах `bot` появится POST `/notify/bulk`, а студенты с заполненным `max_id` получат сообщение.
4. Отправить напоминание об оплате:
   ```bash
   curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
        -X POST http://localhost:8000/api/v1/payments/tuition/remind/1001
   ```
   Бот вызовет `/notify/payment/tuition/1001` и отправит уведомление пользователю.

Если backend вернул 502 — бот не принял запрос (обычно из-за неверного токена).

## 7. Полезные команды

```bash
# Логи
docker compose logs -f backend
docker compose logs -f bot

# Состояние контейнеров
docker compose ps backend bot

# Повторная инициализация БД
docker compose exec backend bash -lc "./init_db.sh"

# Остановка
docker compose down
```

