"""
Скрипт для заполнения базы данных моковым расписанием
Запуск: python seed_schedule.py
"""
import sys
from pathlib import Path
from datetime import time

# Добавляем путь к приложению
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session, configure_mappers
from app.db.session import SessionLocal
from app.db.base import Base
from app.models.timeslot import Timeslot
from app.models.subject import Subject
from app.models.room import Room
from app.models.lesson import Lesson
from app.models.lesson_group import LessonGroup
from app.models.student_group import StudentGroup
from app.models.teacher import Teacher
from app.models.user import User

# Настраиваем все relationships перед использованием
try:
    configure_mappers()
except Exception:
    pass

# Временные слоты (пары)
TIMESLOTS = [
    {"pair_no": 1, "start": time(9, 0), "end": time(10, 30)},
    {"pair_no": 2, "start": time(10, 40), "end": time(12, 10)},
    {"pair_no": 3, "start": time(12, 20), "end": time(13, 50)},
    {"pair_no": 4, "start": time(14, 0), "end": time(15, 30)},
    {"pair_no": 5, "start": time(15, 40), "end": time(17, 10)},
    {"pair_no": 6, "start": time(17, 20), "end": time(18, 50)},
    {"pair_no": 7, "start": time(19, 0), "end": time(20, 30)},
    {"pair_no": 8, "start": time(20, 40), "end": time(22, 10)},
]

# Предметы для разных типов факультетов
SUBJECTS = {
    "технический": [
        "Математический анализ",
        "Линейная алгебра",
        "Программирование",
        "Базы данных",
        "Архитектура компьютеров",
        "Операционные системы",
        "Алгоритмы и структуры данных",
        "Веб-разработка",
    ],
    "гуманитарный": [
        "История России",
        "Русский язык",
        "Литература",
        "Философия",
        "Культурология",
        "Психология",
        "Иностранный язык",
        "Социология",
    ],
    "экономический": [
        "Экономическая теория",
        "Микроэкономика",
        "Макроэкономика",
        "Бухгалтерский учет",
        "Финансы и кредит",
        "Маркетинг",
        "Менеджмент",
        "Статистика",
    ],
    "естественнонаучный": [
        "Общая физика",
        "Теоретическая физика",
        "Общая химия",
        "Органическая химия",
        "Биология",
        "Математика",
        "Информатика",
        "Экология",
    ],
}

# Аудитории
ROOMS = [
    {"number": "101", "building": "Главный корпус", "capacity": "30"},
    {"number": "102", "building": "Главный корпус", "capacity": "30"},
    {"number": "201", "building": "Главный корпус", "capacity": "50"},
    {"number": "202", "building": "Главный корпус", "capacity": "50"},
    {"number": "301", "building": "Главный корпус", "capacity": "100"},
    {"number": "302", "building": "Главный корпус", "capacity": "100"},
    {"number": "401", "building": "Корпус А", "capacity": "30"},
    {"number": "402", "building": "Корпус А", "capacity": "30"},
    {"number": "501", "building": "Корпус Б", "capacity": "50"},
    {"number": "502", "building": "Корпус Б", "capacity": "50"},
    {"number": "Лаб-1", "building": "Лабораторный корпус", "capacity": "20"},
    {"number": "Лаб-2", "building": "Лабораторный корпус", "capacity": "20"},
    {"number": "Лаб-3", "building": "Лабораторный корпус", "capacity": "20"},
]

# Расписание на неделю (дни недели: 1-5, пары: 1-6)
# Для каждой группы создаем по 3-4 пары в день
SCHEDULE_TEMPLATE = {
    1: [1, 2, 3],  # Понедельник: пары 1, 2, 3
    2: [2, 3, 4],  # Вторник: пары 2, 3, 4
    3: [1, 3, 5],  # Среда: пары 1, 3, 5
    4: [2, 4, 6],  # Четверг: пары 2, 4, 6
    5: [1, 4, 5],  # Пятница: пары 1, 4, 5
}


def seed_timeslots(db: Session):
    """Заполнение временных слотов (пар)"""
    print("Заполнение временных слотов...")
    
    created_count = 0
    for slot_data in TIMESLOTS:
        existing = db.query(Timeslot).filter(Timeslot.pair_no == slot_data["pair_no"]).first()
        if existing:
            continue
        
        timeslot = Timeslot(
            pair_no=slot_data["pair_no"],
            start=slot_data["start"],
            end=slot_data["end"],
        )
        db.add(timeslot)
        created_count += 1
        print(f"  + Добавлен временной слот: пара {slot_data['pair_no']} ({slot_data['start']} - {slot_data['end']})")
    
    db.commit()
    print(f"  ✅ Создано временных слотов: {created_count}\n")


def seed_subjects(db: Session):
    """Заполнение предметов"""
    print("Заполнение предметов...")
    
    subjects_dict = {}
    created_count = 0
    
    for faculty_type, subject_list in SUBJECTS.items():
        for subject_title in subject_list:
            existing = db.query(Subject).filter(Subject.title == subject_title).first()
            if existing:
                subjects_dict[subject_title] = existing
                continue
            
            subject = Subject(title=subject_title)
            db.add(subject)
            db.flush()
            subjects_dict[subject_title] = subject
            created_count += 1
            print(f"  + Добавлен предмет: {subject_title}")
    
    db.commit()
    print(f"  ✅ Создано предметов: {created_count}\n")
    return subjects_dict


def seed_rooms(db: Session):
    """Заполнение аудиторий"""
    print("Заполнение аудиторий...")
    
    rooms_dict = {}
    created_count = 0
    
    for room_data in ROOMS:
        existing = db.query(Room).filter(
            Room.number == room_data["number"],
            Room.building == room_data["building"]
        ).first()
        if existing:
            rooms_dict[f"{room_data['building']}-{room_data['number']}"] = existing
            continue
        
        room = Room(
            number=room_data["number"],
            building=room_data["building"],
            capacity=room_data["capacity"],
        )
        db.add(room)
        db.flush()
        rooms_dict[f"{room_data['building']}-{room_data['number']}"] = room
        created_count += 1
        print(f"  + Добавлена аудитория: {room_data['building']}, {room_data['number']}")
    
    db.commit()
    print(f"  ✅ Создано аудиторий: {created_count}\n")
    return rooms_dict


def get_faculty_type(faculty_title: str) -> str:
    """Определяет тип факультета по названию"""
    if any(word in faculty_title.lower() for word in ["информатик", "вычислительн", "автоматик", "машиностроен"]):
        return "технический"
    elif any(word in faculty_title.lower() for word in ["гуманитарн", "филолог", "истори", "литератур"]):
        return "гуманитарный"
    elif any(word in faculty_title.lower() for word in ["экономическ", "менеджмент", "финанс"]):
        return "экономический"
    else:
        return "естественнонаучный"


def seed_schedule_for_groups(db: Session, subjects_dict: dict, rooms_dict: dict):
    """Заполнение расписания для всех групп"""
    print("Заполнение расписания для групп...")
    
    # Получаем все группы
    groups = db.query(StudentGroup).all()
    if not groups:
        print("  ⚠️  Нет групп в базе. Сначала запустите seed_data.py")
        return
    
    # Получаем всех преподавателей
    teachers = db.query(Teacher).all()
    if not teachers:
        print("  ⚠️  Нет преподавателей в базе. Сначала запустите seed_students.py")
        return
    
    # Получаем все факультеты для определения типа
    from app.models.faculty import Faculty
    faculties = {f.id: f for f in db.query(Faculty).all()}
    
    created_lessons = 0
    
    for group in groups:
        # Определяем тип факультета
        faculty = faculties.get(group.faculty_id)
        if not faculty:
            continue
        
        faculty_type = get_faculty_type(faculty.title)
        
        # Получаем предметы для этого типа факультета
        available_subjects = [s for s in subjects_dict.values() if s.title in SUBJECTS.get(faculty_type, [])]
        if not available_subjects:
            continue
        
        # Получаем преподавателей для этой группы (можно использовать любых)
        available_teachers = teachers[:len(available_subjects)] if len(teachers) >= len(available_subjects) else teachers
        
        # Получаем аудитории
        available_rooms = list(rooms_dict.values())
        
        # Создаем расписание на неделю
        subject_index = 0
        teacher_index = 0
        room_index = 0
        
        for day, pairs in SCHEDULE_TEMPLATE.items():
            for pair_no in pairs:
                # Выбираем предмет, преподавателя и аудиторию
                subject = available_subjects[subject_index % len(available_subjects)]
                teacher = available_teachers[teacher_index % len(available_teachers)]
                room = available_rooms[room_index % len(available_rooms)]
                
                # Проверяем, не существует ли уже такой урок для этой группы
                existing_lesson = db.query(Lesson).join(LessonGroup).filter(
                    LessonGroup.group_id == group.id,
                    Lesson.pair_no == pair_no,
                    Lesson.teacher_user_id == teacher.user_id
                ).first()
                
                if existing_lesson:
                    subject_index += 1
                    teacher_index += 1
                    room_index += 1
                    continue
                
                # Создаем урок
                lesson = Lesson(
                    teacher_user_id=teacher.user_id,
                    room_id=room.id,
                    subject_id=subject.id,
                    pair_no=pair_no,
                )
                db.add(lesson)
                db.flush()
                
                # Связываем урок с группой
                lesson_group = LessonGroup(
                    lesson_id=lesson.id,
                    group_id=group.id,
                )
                db.add(lesson_group)
                
                created_lessons += 1
                
                subject_index += 1
                teacher_index += 1
                room_index += 1
        
        print(f"  + Создано расписание для группы: {group.name}")
    
    db.commit()
    print(f"\n  ✅ Создано уроков: {created_lessons}\n")


def main():
    """Основная функция для заполнения расписания"""
    print("=" * 60)
    print("Заполнение базы данных моковым расписанием")
    print("=" * 60)
    
    db: Session = SessionLocal()
    
    try:
        # Заполняем данные
        seed_timeslots(db)
        subjects_dict = seed_subjects(db)
        rooms_dict = seed_rooms(db)
        seed_schedule_for_groups(db, subjects_dict, rooms_dict)
        
        print("=" * 60)
        print("✅ Заполнение расписания завершено успешно!")
        print("=" * 60)
        
        # Выводим статистику
        timeslot_count = db.query(Timeslot).count()
        subject_count = db.query(Subject).count()
        room_count = db.query(Room).count()
        lesson_count = db.query(Lesson).count()
        lesson_group_count = db.query(LessonGroup).count()
        
        print(f"\nСтатистика:")
        print(f"  Временных слотов (пар): {timeslot_count}")
        print(f"  Предметов: {subject_count}")
        print(f"  Аудиторий: {room_count}")
        print(f"  Уроков: {lesson_count}")
        print(f"  Связей урок-группа: {lesson_group_count}")
        
    except Exception as e:
        print(f"\n❌ Ошибка при заполнении расписания: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

