# Запуск приложения

- Требования: установлен Docker и Docker Compose (плагин `docker compose`).
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
docker compose up -d backend bot frontend
docker compose exec backend bash -lc "bash ./init_db.sh"
```

## Доступы

- Backend API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Frontend: `http://localhost:4173`
- Bot (health): `http://localhost:8080/healthz`

## Полезные команды

```bash
docker compose logs -f backend
docker compose logs -f bot
docker compose logs -f frontend

docker compose ps
docker compose down
```

## Подробнее

Подробные инструкции по тестированию, сценарии и примеры переменных смотрите в файле `TESTING.md`.

