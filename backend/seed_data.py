"""
Скрипт для заполнения базы данных начальными данными
Запуск: python seed_data.py
"""
import sys
from pathlib import Path

# Добавляем путь к приложению
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session, configure_mappers
from app.db.session import SessionLocal
# Импортируем все модели через base, чтобы relationships были правильно настроены
from app.db.base import Base
# Импортируем все модели, чтобы relationships были правильно настроены
from app.models.university import University
from app.models.faculty import Faculty
from app.models.kafedra import Kafedra
from app.models.student_group import StudentGroup

# Настраиваем все relationships перед использованием
try:
    configure_mappers()
except Exception:
    # Игнорируем ошибки relationships - они не критичны для seed скрипта
    pass


# Данные для заполнения
UNIVERSITIES_DATA = [
    # Москва
    {"name": "Московский государственный университет имени М.В. Ломоносова", "city": "Москва"},
    {"name": "Московский государственный технический университет им. Н.Э. Баумана", "city": "Москва"},
    {"name": "Национальный исследовательский ядерный университет «МИФИ»", "city": "Москва"},
    {"name": "Московский физико-технический институт", "city": "Москва"},
    {"name": "Национальный исследовательский университет «Высшая школа экономики»", "city": "Москва"},
    {"name": "Московский государственный институт международных отношений", "city": "Москва"},
    {"name": "Российский университет дружбы народов", "city": "Москва"},
    {"name": "Московский авиационный институт", "city": "Москва"},
    {"name": "Национальный исследовательский технологический университет «МИСиС»", "city": "Москва"},
    
    # Санкт-Петербург
    {"name": "Санкт-Петербургский государственный университет", "city": "Санкт-Петербург"},
    {"name": "Санкт-Петербургский политехнический университет Петра Великого", "city": "Санкт-Петербург"},
    
    # Другие города
    {"name": "Новосибирский государственный университет", "city": "Новосибирск"},
    {"name": "Казанский (Приволжский) федеральный университет", "city": "Казань"},
    {"name": "Уральский федеральный университет имени первого Президента России Б.Н. Ельцина", "city": "Екатеринбург"},
    {"name": "Томский государственный университет", "city": "Томск"},
]

FACULTIES_DATA = {
    "технический": [
        "Факультет информатики и вычислительной техники",
        "Факультет автоматики и вычислительной техники",
        "Факультет машиностроения",
    ],
    "гуманитарный": [
        "Факультет гуманитарных наук",
        "Факультет филологии",
        "Факультет истории",
    ],
    "экономический": [
        "Экономический факультет",
        "Факультет менеджмента",
        "Факультет финансов",
    ],
    "естественнонаучный": [
        "Факультет математики и механики",
        "Факультет физики",
        "Факультет химии",
    ],
}

KAFEDRAS_DATA = {
    "технический": [
        "Кафедра информатики",
        "Кафедра программной инженерии",
        "Кафедра систем управления",
    ],
    "гуманитарный": [
        "Кафедра русского языка",
        "Кафедра литературы",
        "Кафедра истории России",
    ],
    "экономический": [
        "Кафедра экономической теории",
        "Кафедра менеджмента",
        "Кафедра финансов и кредита",
    ],
    "естественнонаучный": [
        "Кафедра математического анализа",
        "Кафедра теоретической физики",
        "Кафедра органической химии",
    ],
}

GROUPS_DATA = {
    "технический": [
        {"name": "ИВТ-21-01", "code": "IVT-21-01"},
        {"name": "ИВТ-21-02", "code": "IVT-21-02"},
        {"name": "ПИ-21-01", "code": "PI-21-01"},
    ],
    "гуманитарный": [
        {"name": "ФИЛ-21-01", "code": "FIL-21-01"},
        {"name": "ИСТ-21-01", "code": "IST-21-01"},
        {"name": "ЛИТ-21-01", "code": "LIT-21-01"},
    ],
    "экономический": [
        {"name": "ЭКО-21-01", "code": "EKO-21-01"},
        {"name": "МЕН-21-01", "code": "MEN-21-01"},
        {"name": "ФИН-21-01", "code": "FIN-21-01"},
    ],
    "естественнонаучный": [
        {"name": "МАТ-21-01", "code": "MAT-21-01"},
        {"name": "ФИЗ-21-01", "code": "FIZ-21-01"},
        {"name": "ХИМ-21-01", "code": "HIM-21-01"},
    ],
}


def seed_universities(db: Session):
    """Заполнение таблицы университетов"""
    print("Заполнение университетов...")
    universities = {}
    
    for uni_data in UNIVERSITIES_DATA:
        # Проверяем, существует ли уже такой университет
        existing = db.query(University).filter(
            University.name == uni_data["name"]
        ).first()
        
        if existing:
            print(f"  ✓ Университет '{uni_data['name']}' уже существует")
            universities[uni_data["name"]] = existing
        else:
            university = University(
                name=uni_data["name"],
                city=uni_data["city"]
            )
            db.add(university)
            db.flush()
            universities[uni_data["name"]] = university
            print(f"  + Добавлен университет: {uni_data['name']}")
    
    db.commit()
    return universities


def seed_faculties(db: Session, universities: dict):
    """Заполнение таблицы факультетов"""
    print("\nЗаполнение факультетов...")
    faculties_dict = {}
    
    for uni_name, university in universities.items():
        # Для каждого университета добавляем по 2-3 факультета разных типов
        faculty_types = ["технический", "гуманитарный", "экономический"]
        
        for faculty_type in faculty_types:
            for faculty_title in FACULTIES_DATA[faculty_type][:1]:  # Берем по одному факультету каждого типа
                # Проверяем, существует ли уже такой факультет
                existing = db.query(Faculty).filter(
                    Faculty.university_id == university.id,
                    Faculty.title == faculty_title
                ).first()
                
                if existing:
                    key = f"{uni_name}_{faculty_title}"
                    faculties_dict[key] = existing
                else:
                    faculty = Faculty(
                        university_id=university.id,
                        title=faculty_title
                    )
                    db.add(faculty)
                    db.flush()
                    key = f"{uni_name}_{faculty_title}"
                    faculties_dict[key] = faculty
                    print(f"  + Добавлен факультет: {faculty_title} ({uni_name})")
    
    db.commit()
    return faculties_dict


def seed_kafedras(db: Session, faculties_dict: dict):
    """Заполнение таблицы кафедр"""
    print("\nЗаполнение кафедр...")
    
    for key, faculty in faculties_dict.items():
        # Определяем тип факультета по названию
        faculty_type = None
        for f_type, titles in FACULTIES_DATA.items():
            if any(title in faculty.title for title in titles):
                faculty_type = f_type
                break
        
        if not faculty_type:
            faculty_type = "технический"  # По умолчанию
        
        # Добавляем кафедры для этого факультета
        for kafedra_title in KAFEDRAS_DATA[faculty_type][:2]:  # По 2 кафедры на факультет
            existing = db.query(Kafedra).filter(
                Kafedra.faculty_id == faculty.id,
                Kafedra.title == kafedra_title
            ).first()
            
            if not existing:
                kafedra = Kafedra(
                    faculty_id=faculty.id,
                    title=kafedra_title
                )
                db.add(kafedra)
                print(f"  + Добавлена кафедра: {kafedra_title} ({faculty.title})")
    
    db.commit()


def seed_student_groups(db: Session, faculties_dict: dict):
    """Заполнение таблицы студенческих групп"""
    print("\nЗаполнение студенческих групп...")
    
    for key, faculty in faculties_dict.items():
        # Определяем тип факультета
        faculty_type = None
        for f_type, titles in FACULTIES_DATA.items():
            if any(title in faculty.title for title in titles):
                faculty_type = f_type
                break
        
        if not faculty_type:
            faculty_type = "технический"
        
        # Добавляем группы для этого факультета
        for group_data in GROUPS_DATA[faculty_type][:2]:  # По 2 группы на факультет
            existing = db.query(StudentGroup).filter(
                StudentGroup.faculty_id == faculty.id,
                StudentGroup.code == group_data["code"]
            ).first()
            
            if not existing:
                group = StudentGroup(
                    name=group_data["name"],
                    faculty_id=faculty.id,
                    code=group_data["code"]
                )
                db.add(group)
                print(f"  + Добавлена группа: {group_data['name']} ({faculty.title})")
    
    db.commit()


def main():
    """Основная функция для заполнения базы данных"""
    print("=" * 60)
    print("Заполнение базы данных начальными данными")
    print("=" * 60)
    
    db: Session = SessionLocal()
    
    try:
        # Заполняем данные
        universities = seed_universities(db)
        faculties = seed_faculties(db, universities)
        seed_kafedras(db, faculties)
        seed_student_groups(db, faculties)
        
        print("\n" + "=" * 60)
        print("✅ Заполнение базы данных завершено успешно!")
        print("=" * 60)
        
        # Выводим статистику
        uni_count = db.query(University).count()
        faculty_count = db.query(Faculty).count()
        kafedra_count = db.query(Kafedra).count()
        group_count = db.query(StudentGroup).count()
        
        print(f"\nСтатистика:")
        print(f"  Университетов: {uni_count}")
        print(f"  Факультетов: {faculty_count}")
        print(f"  Кафедр: {kafedra_count}")
        print(f"  Студенческих групп: {group_count}")
        
    except Exception as e:
        print(f"\n❌ Ошибка при заполнении базы данных: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

