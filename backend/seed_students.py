"""
Скрипт для заполнения базы данных тестовыми студентами и преподавателями
(моковая база деканата для верификации)
Запуск: python seed_students.py
"""
import sys
from pathlib import Path

# Добавляем путь к приложению
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session, configure_mappers
from app.db.session import SessionLocal
from app.db.base import Base
from app.models.university import University
from app.models.faculty import Faculty
from app.models.kafedra import Kafedra
from app.models.student_group import StudentGroup
from app.models.user import User, UserRole
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.staff import Staff

# Настраиваем все relationships перед использованием
try:
    configure_mappers()
except Exception:
    pass

# Тестовые данные для студентов
STUDENTS_DATA = [
    {"full_name": "Иванов Иван Иванович", "student_card": "STU001", "city": "Москва"},
    {"full_name": "Петров Петр Петрович", "student_card": "STU002", "city": "Москва"},
    {"full_name": "Сидоров Сидор Сидорович", "student_card": "STU003", "city": "Москва"},
    {"full_name": "Смирнова Анна Сергеевна", "student_card": "STU004", "city": "Москва"},
    {"full_name": "Козлова Мария Дмитриевна", "student_card": "STU005", "city": "Москва"},
    {"full_name": "Новиков Алексей Владимирович", "student_card": "STU006", "city": "Москва"},
    {"full_name": "Морозова Елена Александровна", "student_card": "STU007", "city": "Москва"},
    {"full_name": "Волков Дмитрий Игоревич", "student_card": "STU008", "city": "Москва"},
    {"full_name": "Лебедева Ольга Николаевна", "student_card": "STU009", "city": "Москва"},
    {"full_name": "Соколов Артем Павлович", "student_card": "STU010", "city": "Москва"},
    {"full_name": "Попов Игорь Сергеевич", "student_card": "STU011", "city": "Санкт-Петербург"},
    {"full_name": "Васильева Татьяна Андреевна", "student_card": "STU012", "city": "Санкт-Петербург"},
    {"full_name": "Семенов Роман Викторович", "student_card": "STU013", "city": "Новосибирск"},
    {"full_name": "Голубева Наталья Игоревна", "student_card": "STU014", "city": "Казань"},
    {"full_name": "Федоров Максим Олегович", "student_card": "STU015", "city": "Екатеринбург"},
]

# Тестовые данные для преподавателей
TEACHERS_DATA = [
    {"full_name": "Профессоров Александр Иванович", "tab_number": "TCH001", "city": "Москва"},
    {"full_name": "Доцентов Сергей Петрович", "tab_number": "TCH002", "city": "Москва"},
    {"full_name": "Ассистентов Владимир Николаевич", "tab_number": "TCH003", "city": "Москва"},
    {"full_name": "Лекторов Ольга Сергеевна", "tab_number": "TCH004", "city": "Москва"},
    {"full_name": "Преподавателев Дмитрий Александрович", "tab_number": "TCH005", "city": "Москва"},
    {"full_name": "Учителев Игорь Викторович", "tab_number": "TCH006", "city": "Санкт-Петербург"},
    {"full_name": "Наставников Анна Дмитриевна", "tab_number": "TCH007", "city": "Санкт-Петербург"},
    {"full_name": "Менторов Павел Игоревич", "tab_number": "TCH008", "city": "Новосибирск"},
]

# Тестовые данные для сотрудников деканата
STAFF_DATA = [
    {"full_name": "Деканов Иван Петрович", "tab_number": "STF001", "city": "Москва"},
    {"full_name": "Секретарев Мария Сергеевна", "tab_number": "STF002", "city": "Москва"},
    {"full_name": "Администраторов Андрей Николаевич", "tab_number": "STF003", "city": "Москва"},
    {"full_name": "Координаторов Елена Владимировна", "tab_number": "STF004", "city": "Санкт-Петербург"},
]


def seed_students(db: Session):
    """Заполнение базы данных тестовыми студентами"""
    print("Заполнение базы данных студентами...")
    
    # Получаем все университеты
    universities = db.query(University).all()
    if not universities:
        print("  ⚠️  Нет университетов в базе. Сначала запустите seed_data.py")
        return
    
    # Получаем все факультеты и группы
    faculties = db.query(Faculty).all()
    groups = db.query(StudentGroup).all()
    
    if not faculties or not groups:
        print("  ⚠️  Нет факультетов или групп в базе. Сначала запустите seed_data.py")
        return
    
    created_count = 0
    skipped_count = 0
    
    for i, student_data in enumerate(STUDENTS_DATA):
        # Выбираем университет по городу
        university = next((u for u in universities if u.city == student_data["city"]), universities[0])
        
        # Выбираем факультет и группу (распределяем равномерно)
        faculty = faculties[i % len(faculties)]
        group = next((g for g in groups if g.faculty_id == faculty.id), groups[i % len(groups)])
        
        # Проверяем, существует ли уже студент с таким номером билета
        existing_student = db.query(Student).filter(
            Student.student_card == student_data["student_card"]
        ).first()
        
        if existing_student:
            print(f"  ✓ Студент с номером билета '{student_data['student_card']}' уже существует")
            skipped_count += 1
            continue
        
        # Создаем пользователя
        user = User(
            role=UserRole.STUDENT,
            full_name=student_data["full_name"],
            city=student_data["city"],
            university_id=university.id,
        )
        db.add(user)
        db.flush()
        
        # Создаем студента
        student = Student(
            user_id=user.id,
            student_card=student_data["student_card"],
            faculty_id=faculty.id,
            group_id=group.id,
        )
        db.add(student)
        created_count += 1
        print(f"  + Добавлен студент: {student_data['full_name']} (билет: {student_data['student_card']})")
    
    db.commit()
    print(f"\n  ✅ Создано студентов: {created_count}, пропущено: {skipped_count}")


def seed_teachers(db: Session):
    """Заполнение базы данных тестовыми преподавателями"""
    print("\nЗаполнение базы данных преподавателями...")
    
    # Получаем все университеты
    universities = db.query(University).all()
    if not universities:
        print("  ⚠️  Нет университетов в базе. Сначала запустите seed_data.py")
        return
    
    # Получаем все кафедры
    kafedras = db.query(Kafedra).all()
    
    if not kafedras:
        print("  ⚠️  Нет кафедр в базе. Сначала запустите seed_data.py")
        return
    
    created_count = 0
    skipped_count = 0
    
    for i, teacher_data in enumerate(TEACHERS_DATA):
        # Выбираем университет по городу
        university = next((u for u in universities if u.city == teacher_data["city"]), universities[0])
        
        # Выбираем кафедру (распределяем равномерно)
        kafedra = kafedras[i % len(kafedras)]
        
        # Проверяем, существует ли уже преподаватель с таким табельным номером
        existing_teacher = db.query(Teacher).filter(
            Teacher.tab_number == teacher_data["tab_number"]
        ).first()
        
        if existing_teacher:
            print(f"  ✓ Преподаватель с табельным номером '{teacher_data['tab_number']}' уже существует")
            skipped_count += 1
            continue
        
        # Создаем пользователя
        user = User(
            role=UserRole.STAFF,
            full_name=teacher_data["full_name"],
            city=teacher_data["city"],
            university_id=university.id,
        )
        db.add(user)
        db.flush()
        
        # Создаем преподавателя
        teacher = Teacher(
            user_id=user.id,
            tab_number=teacher_data["tab_number"],
            kafedra_id=kafedra.id,
        )
        db.add(teacher)
        created_count += 1
        print(f"  + Добавлен преподаватель: {teacher_data['full_name']} (табельный: {teacher_data['tab_number']})")
    
    db.commit()
    print(f"\n  ✅ Создано преподавателей: {created_count}, пропущено: {skipped_count}")


def seed_staff(db: Session):
    """Заполнение базы данных тестовыми сотрудниками деканата"""
    print("\nЗаполнение базы данных сотрудниками деканата...")
    
    # Получаем все университеты
    universities = db.query(University).all()
    if not universities:
        print("  ⚠️  Нет университетов в базе. Сначала запустите seed_data.py")
        return
    
    created_count = 0
    skipped_count = 0
    
    for i, staff_data in enumerate(STAFF_DATA):
        # Выбираем университет по городу
        university = next((u for u in universities if u.city == staff_data["city"]), universities[0])
        
        # Проверяем, существует ли уже сотрудник с таким табельным номером
        existing_staff = db.query(Staff).filter(
            Staff.tab_number == staff_data["tab_number"]
        ).first()
        
        if existing_staff:
            print(f"  ✓ Сотрудник с табельным номером '{staff_data['tab_number']}' уже существует")
            skipped_count += 1
            continue
        
        # Создаем пользователя
        user = User(
            role=UserRole.STAFF,
            full_name=staff_data["full_name"],
            city=staff_data["city"],
            university_id=university.id,
        )
        db.add(user)
        db.flush()
        
        # Создаем сотрудника
        staff = Staff(
            user_id=user.id,
            tab_number=staff_data["tab_number"],
            university_id=university.id,
        )
        db.add(staff)
        created_count += 1
        print(f"  + Добавлен сотрудник: {staff_data['full_name']} (табельный: {staff_data['tab_number']})")
    
    db.commit()
    print(f"\n  ✅ Создано сотрудников: {created_count}, пропущено: {skipped_count}")


def main():
    """Основная функция для заполнения базы данных"""
    print("=" * 60)
    print("Заполнение базы данных тестовыми студентами и преподавателями")
    print("(моковая база деканата для верификации)")
    print("=" * 60)
    
    db: Session = SessionLocal()
    
    try:
        # Заполняем данные
        seed_students(db)
        seed_teachers(db)
        seed_staff(db)
        
        print("\n" + "=" * 60)
        print("✅ Заполнение базы данных завершено успешно!")
        print("=" * 60)
        
        # Выводим статистику
        student_count = db.query(Student).count()
        teacher_count = db.query(Teacher).count()
        staff_count = db.query(Staff).count()
        
        print(f"\nСтатистика:")
        print(f"  Студентов: {student_count}")
        print(f"  Преподавателей: {teacher_count}")
        print(f"  Сотрудников деканата: {staff_count}")
        
        print("\n" + "=" * 60)
        print("Тестовые данные для регистрации:")
        print("=" * 60)
        print("\nСтуденты (для регистрации):")
        print("  - Иванов Иван Иванович, билет: STU001, город: Москва")
        print("  - Петров Петр Петрович, билет: STU002, город: Москва")
        print("  - Сидоров Сидор Сидорович, билет: STU003, город: Москва")
        print("\nПреподаватели (для регистрации):")
        print("  - Профессоров Александр Иванович, табельный: TCH001, город: Москва")
        print("  - Доцентов Сергей Петрович, табельный: TCH002, город: Москва")
        print("\nСотрудники (для регистрации):")
        print("  - Деканов Иван Петрович, табельный: STF001, город: Москва")
        print("  - Секретарев Мария Сергеевна, табельный: STF002, город: Москва")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Ошибка при заполнении базы данных: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

