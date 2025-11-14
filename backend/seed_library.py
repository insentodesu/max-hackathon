"""
Скрипт для заполнения базы данных данными о доступе к электронной библиотеке Юрайт
Запуск: python seed_library.py
"""
import sys
from pathlib import Path

# Добавляем путь к приложению
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session, configure_mappers
from app.db.session import SessionLocal
from app.db.base import Base
from app.models.library import LibraryAccess
from app.models.university import University

# Настраиваем все relationships перед использованием
try:
    configure_mappers()
except Exception:
    pass  # Игнорируем ошибки relationships - они не критичны для seed скрипта


# Инструкция по доступу к библиотеке Юрайт
URAIT_INSTRUCTIONS = """Пошаговая инструкция по доступу к образовательной платформе Юрайт:

1. Перейдите на портал библиотеки по ссылке выше
2. Нажмите кнопку "Вход" в правом верхнем углу
3. Введите логин и пароль, предоставленные вашим университетом
4. После входа вы получите доступ к:
   - Более 10 000 учебников
   - Более 5 000 курсов
   - Тестам и заданиям платформы
   - Медиаматериалам (видео и аудио)
   - Мобильному приложению для чтения без интернета

5. Для поиска нужной литературы используйте каталог или поиск по дисциплинам
6. Книги можно читать онлайн или скачать в мобильное приложение

При возникновении проблем обращайтесь в библиотеку вашего университета."""


def create_library_access_for_all_universities(db: Session):
    """Создать доступ к библиотеке Юрайт для всех университетов"""
    created_count = 0
    skipped_count = 0
    
    universities = db.query(University).all()
    
    if not universities:
        print("⚠️  Не найдено университетов в базе данных. Сначала запустите seed_data.py")
        return 0, 0
    
    for university in universities:
        # Проверяем, существует ли уже доступ для этого университета
        existing = db.query(LibraryAccess).filter(
            LibraryAccess.university_id == university.id
        ).first()
        
        if existing:
            skipped_count += 1
            continue
        
        # Создаем логин и пароль на основе названия университета
        # Используем первые буквы названия и ID для уникальности
        university_name_short = "".join([word[0].upper() for word in university.name.split()[:3]])
        login = f"{university_name_short.lower()}_student"
        password = f"urait_{university.id.hex[:8]}"  # Используем часть UUID для пароля
        
        library_access = LibraryAccess(
            university_id=university.id,
            login=login,
            password=password,
            portal_url="https://urait.ru/",
            instructions=URAIT_INSTRUCTIONS,
        )
        
        db.add(library_access)
        created_count += 1
        print(f"✅ Добавлен доступ к библиотеке Юрайт для: {university.name}")
    
    db.commit()
    return created_count, skipped_count


if __name__ == "__main__":
    print("📚 Начинаем заполнение базы данных данными о доступе к библиотеке Юрайт...")
    
    db: Session = SessionLocal()
    try:
        created, skipped = create_library_access_for_all_universities(db)
        print(f"\n✅ Создано записей о доступе: {created}")
        if skipped > 0:
            print(f"⏭️  Пропущено (уже существуют): {skipped}")
        print("🎊 Заполнение завершено!")
    except Exception as e:
        print(f"❌ Ошибка при заполнении: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()

