#!/usr/bin/env bash
set -euo pipefail

echo "🔄 Создаем таблицы в базе данных..."
python -c "from app.db.base import Base; from app.db.session import engine; Base.metadata.create_all(bind=engine)"

echo "📦 Загружаем справочники (университеты, факультеты, группы)..."
python seed_data.py

echo "👥 Добавляем тестовых студентов и преподавателей..."
python seed_students.py

echo "🗓️ Импортируем расписание..."
python seed_schedule.py

echo "🎉 Загружаем события..."
python seed_events.py

echo "🎓 Импортируем элективы..."
python seed_electives.py

echo "📚 Настраиваем доступ к библиотеке..."
python seed_library.py

echo "📋 Создаем тестовые регистрации и заявки..."
python seed_registrations.py

echo "✅ Инициализация базы данных завершена!"
