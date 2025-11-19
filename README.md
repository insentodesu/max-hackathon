# Запуск приложения
# ДАННЫЕ ДЛЯ РЕГИСТРАЦИИ В БОТЕ СМОТРЕТЬ в TESTING.MD !!!

- Требования: установлен Docker и docker-compose (плагин `docker-compose`).
- Переменные окружения: проверьте и при необходимости отредактируйте файл `.env` в корне.
  Минимум укажите `BOT_TOKEN`, а также согласуйте токены `HTTP_BACKEND_TOKEN` и `BOT_NOTIFY_TOKEN`.


## Быстрый старт (с Bash/WSL/Git Bash)

```bash
chmod +x scripts/test-backend-bot.sh
./scripts/test-backend-bot.sh
```

Скрипт поднимет `backend`, `bot`, `frontend`, дождётся health-check и выполнит начальное наполнение БД (`init_db.sh`).
Для пересборки образов используйте: `./scripts/test-backend-bot-rebuild.sh`.

## Ручной запуск (PowerShell/без Bash)

```powershell
docker-compose up -d backend bot frontend
docker-compose exec backend bash -lc "bash ./init_db.sh"
```

## Доступы

- Backend API: `http://localhost:8160`
- Swagger: `http://localhost:8160/docs`
- Frontend: `http://localhost:8170`
- Bot (health): `http://localhost:8180/healthz`

## Полезные команды

```bash
docker-compose logs -f backend
docker-compose logs -f bot
docker-compose logs -f frontend

docker-compose ps
docker-compose down
```

## Работа с ботом

1. Создайте бота в MAX, активируйте токен и пропишите его в `.env` (`BOT_TOKEN`). Там же укажите `BACKEND_API_BASE_URL` (обычно `http://backend:8000/api/v1`) и сервисный `HTTP_BACKEND_TOKEN`, чтобы Go‑бот мог ходить в backend, а backend — отправлять нотификации через `BOT_NOTIFY_BASE_URL/BOT_NOTIFY_TOKEN`.
2. После запуска стека откройте MAX (веб/мобильный клиент), найдите своего бота и отправьте `/start`. Сервис проверит, зарегистрирован ли MAX ID в базе.
   - Если пользователя нет, бот запустит мастера регистрации (`/register` можно вызвать вручную): выберите роль (студент / сотрудник), заполните ФИО, затем последовательно выберите вуз → факультет → группу (для студентов) или кафедру/табельный номер (для сотрудников). Данные берутся из backend (`identity`), поэтому используйте сиды из `TESTING.md`.
   - После успешного ввода бот сохранит MAX ID в backend и покажет главное меню.
3. Основные сценарии из `max_bot/internal/app`:
   - `Платежи` — бот запрашивает `payments.Status` и, если есть задолженности, выдаёт отдельные кнопки: *Оплатить общежитие* (`action:payment:pay_dorm`) или *Оплатить обучение* (`action:payment:pay_tuition`). По нажатию приходит персональная ссылка из backend.
   - `Расписание` — кнопки *Сегодня* и *Неделя* вызывают `schedule.Today/Week`, выводя текстовую сводку занятий.
   - `Заявки` — ветки для студентов и сотрудников. После выбора типа (справка с места учёбы, академический отпуск, перевод, справка с места работы) бот строит форму из `applicationCoordinator`: задаёт последовательные вопросы, может просить вложить файл и отправляет готовую заявку в backend. Процесс можно отменить кнопкой «Отменить заполнение».
   - Уведомления о готовых документах приходят через `sendReadyNotification`: пользователь выбирает *Заберу в офисе* или *Отправить на почту*. Во втором случае бот просит e-mail и пересылает его в backend.
4. В любое время `/help` выводит список зарегистрированных команд, а `/start` перезапускает меню. Если бот отвечает «нужна регистрация», проверьте MAX ID и сиды (см. `TESTING.md`).

## Подробнее

Подробные инструкции по тестированию, сценарии и примеры переменных смотрите в файле `TESTING.md`.
