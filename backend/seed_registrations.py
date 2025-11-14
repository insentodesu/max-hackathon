"""
Скрипт для заполнения базы данных регистрациями на события, элективы и заявками
Запуск: python seed_registrations.py
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
import random

# Добавляем путь к приложению
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session, configure_mappers
from app.db.session import SessionLocal
from app.db.base import Base

# Импортируем все модели для правильной инициализации relationships
from app.models.user import User, UserRole
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.staff import Staff
from app.models.event import Event, EventRegistration, EventType
from app.models.elective import Elective, ElectiveRegistration
from app.models.request import Request, RequestType, RequestStatus
from app.models.request_approval_step import RequestApprovalStep, ApprovalAction
from app.models.student_group import StudentGroup
from app.models.faculty import Faculty
from app.models.kafedra import Kafedra
from app.models.payment import Payment, PaymentType, PaymentStatus
from app.models.broadcast import Broadcast

# Настраиваем все relationships перед использованием
try:
    configure_mappers()
except Exception:
    pass


def seed_event_registrations(db: Session):
    """Создать регистрации на события"""
    print("\n📅 Создаем регистрации на события...")
    
    # Получаем всех студентов
    students = db.query(User).join(Student).filter(User.role == UserRole.STUDENT).all()
    if not students:
        print("  ⚠️  Не найдено студентов в базе данных")
        return 0
    
    # Получаем все предстоящие события
    events = db.query(Event).filter(Event.date >= datetime.now(timezone.utc)).all()
    if not events:
        print("  ⚠️  Не найдено предстоящих событий в базе данных")
        return 0
    
    created_count = 0
    
    # Для каждого студента регистрируем на случайные события (1-5 событий)
    for student in students:
        # Выбираем случайные события (от 1 до 5)
        num_registrations = random.randint(1, min(5, len(events)))
        selected_events = random.sample(events, num_registrations)
        
        for event in selected_events:
            # Проверяем, не записан ли уже
            existing = db.query(EventRegistration).filter(
                EventRegistration.event_id == event.id,
                EventRegistration.user_id == student.id
            ).first()
            
            if existing:
                continue
            
            # Проверяем наличие свободных мест
            if event.current_participants >= event.max_participants:
                continue
            
            # Создаем регистрацию
            registration = EventRegistration(
                event_id=event.id,
                user_id=student.id,
            )
            db.add(registration)
            
            # Увеличиваем счетчик участников
            event.current_participants += 1
            created_count += 1
    
    db.commit()
    print(f"  ✅ Создано регистраций на события: {created_count}")
    return created_count


def seed_elective_registrations(db: Session):
    """Создать регистрации на элективы"""
    print("\n🎓 Создаем регистрации на элективы...")
    
    # Получаем всех студентов
    students = db.query(User).join(Student).filter(User.role == UserRole.STUDENT).all()
    if not students:
        print("  ⚠️  Не найдено студентов в базе данных")
        return 0
    
    # Получаем все активные элективы
    electives = db.query(Elective).filter(Elective.is_active == 1).all()
    if not electives:
        print("  ⚠️  Не найдено активных элективов в базе данных")
        return 0
    
    created_count = 0
    
    # Для каждого студента регистрируем на случайные элективы (1-3 электива)
    for student in students:
        # Выбираем случайные элективы (от 1 до 3)
        num_registrations = random.randint(1, min(3, len(electives)))
        selected_electives = random.sample(electives, num_registrations)
        
        for elective in selected_electives:
            # Проверяем, не записан ли уже
            existing = db.query(ElectiveRegistration).filter(
                ElectiveRegistration.elective_id == elective.id,
                ElectiveRegistration.user_id == student.id
            ).first()
            
            if existing:
                continue
            
            # Проверяем наличие свободных мест
            if elective.current_students >= elective.max_students:
                continue
            
            # Создаем регистрацию
            registration = ElectiveRegistration(
                elective_id=elective.id,
                user_id=student.id,
            )
            db.add(registration)
            
            # Увеличиваем счетчик участников
            elective.current_students += 1
            created_count += 1
    
    db.commit()
    print(f"  ✅ Создано регистраций на элективы: {created_count}")
    return created_count


def _get_deanery_staff_for_faculty(db: Session, faculty_id):
    """Найти сотрудника деканата для факультета"""
    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not faculty:
        return None
    
    staff = db.query(Staff).filter(Staff.university_id == faculty.university_id).first()
    if staff:
        return staff.user_id
    
    admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
    if admin:
        return admin.id
    
    return None


def _get_kafedra_head_for_teacher(db: Session, teacher_user_id):
    """Найти руководителя кафедры для преподавателя"""
    teacher = db.query(Teacher).filter(Teacher.user_id == teacher_user_id).first()
    if not teacher:
        return None
    
    kafedra_teacher = db.query(Teacher).filter(
        Teacher.kafedra_id == teacher.kafedra_id,
        Teacher.user_id != teacher_user_id
    ).first()
    
    if kafedra_teacher:
        return kafedra_teacher.user_id
    
    admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
    if admin:
        return admin.id
    
    return None


def seed_requests(db: Session):
    """Создать заявки для согласования"""
    print("\n📝 Создаем заявки...")
    
    created_count = 0
    
    # 1. Заявки от студентов на академический отпуск
    students = db.query(User).join(Student).filter(User.role == UserRole.STUDENT).all()
    for student_user in students[:3]:  # Берем первых 3 студентов
        student = db.query(Student).filter(Student.user_id == student_user.id).first()
        if not student or not student.group:
            continue
        
        # Находим куратора группы
        curator_id = student.group.curator_user_id if student.group.curator_user_id else None
        if not curator_id:
            # Если нет куратора, используем админа
            admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
            if admin:
                curator_id = admin.id
            else:
                continue
        
        request = Request(
            request_type=RequestType.ACADEMIC_LEAVE,
            author_user_id=student_user.id,
            content="Прошу предоставить академический отпуск по семейным обстоятельствам",
            status=RequestStatus.PENDING,
            current_approver_id=curator_id,
        )
        db.add(request)
        db.flush()
        
        # Создаем шаг согласования
        step = RequestApprovalStep(
            request_id=request.id,
            step_order=1,
            approver_user_id=curator_id,
            approver_role="Куратор",
            action=ApprovalAction.PENDING,
        )
        db.add(step)
        created_count += 1
    
    # 2. Заявки от студентов на перевод
    for student_user in students[3:6] if len(students) > 3 else []:  # Следующие 3 студента
        student = db.query(Student).filter(Student.user_id == student_user.id).first()
        if not student or not student.faculty_id:
            continue
        
        deanery_id = _get_deanery_staff_for_faculty(db, student.faculty_id)
        if not deanery_id:
            continue
        
        request = Request(
            request_type=RequestType.TRANSFER,
            author_user_id=student_user.id,
            content="Прошу перевести меня на другой факультет",
            status=RequestStatus.PENDING,
            current_approver_id=deanery_id,
        )
        db.add(request)
        db.flush()
        
        # Создаем шаг согласования
        step = RequestApprovalStep(
            request_id=request.id,
            step_order=1,
            approver_user_id=deanery_id,
            approver_role="Деканат",
            action=ApprovalAction.PENDING,
        )
        db.add(step)
        created_count += 1
    
    # 3. Заявки от преподавателей на отпуск
    teachers = db.query(User).join(Teacher).filter(User.role == UserRole.STAFF).all()
    for teacher_user in teachers[:3]:  # Берем первых 3 преподавателей
        kafedra_head_id = _get_kafedra_head_for_teacher(db, teacher_user.id)
        if not kafedra_head_id:
            continue
        
        request = Request(
            request_type=RequestType.VACATION,
            author_user_id=teacher_user.id,
            content="Прошу предоставить ежегодный оплачиваемый отпуск",
            status=RequestStatus.PENDING,
            current_approver_id=kafedra_head_id,
        )
        db.add(request)
        db.flush()
        
        # Создаем шаг согласования
        step = RequestApprovalStep(
            request_id=request.id,
            step_order=1,
            approver_user_id=kafedra_head_id,
            approver_role="Руководитель",
            action=ApprovalAction.PENDING,
        )
        db.add(step)
        created_count += 1
    
    # 4. Заявки от преподавателей на согласование документа
    for teacher_user in teachers[3:6] if len(teachers) > 3 else []:  # Следующие 3 преподавателя
        kafedra_head_id = _get_kafedra_head_for_teacher(db, teacher_user.id)
        if not kafedra_head_id:
            continue
        
        request = Request(
            request_type=RequestType.DOCUMENT_APPROVAL,
            author_user_id=teacher_user.id,
            content="Прошу согласовать документ",
            status=RequestStatus.PENDING,
            current_approver_id=kafedra_head_id,
        )
        db.add(request)
        db.flush()
        
        # Создаем шаг согласования
        step = RequestApprovalStep(
            request_id=request.id,
            step_order=1,
            approver_user_id=kafedra_head_id,
            approver_role="Руководитель",
            action=ApprovalAction.PENDING,
        )
        db.add(step)
        created_count += 1
    
    db.commit()
    print(f"  ✅ Создано заявок: {created_count}")
    return created_count


def seed_payments(db: Session):
    """Создать тестовые платежи"""
    print("\n💳 Создаем тестовые платежи...")
    
    # Получаем всех студентов
    students = db.query(User).join(Student).filter(User.role == UserRole.STUDENT).all()
    if not students:
        print("  ⚠️  Не найдено студентов в базе данных")
        return 0
    
    created_count = 0
    
    # Создаем платежи для обучения и общежития для нескольких студентов
    for student in students[:5]:  # Берем первых 5 студентов
        # Платеж за обучение
        payment_tuition = Payment(
            user_id=student.id,
            payment_type=PaymentType.TUITION,
            amount=15000000,  # 150000 руб
            status=random.choice([PaymentStatus.SUCCESS, PaymentStatus.PENDING, PaymentStatus.PROCESSING]),
            period="2024-2025 учебный год, 1 семестр",
            description="Оплата обучения за первый семестр",
        )
        db.add(payment_tuition)
        created_count += 1
        
        # Платеж за общежитие
        payment_dormitory = Payment(
            user_id=student.id,
            payment_type=PaymentType.DORMITORY,
            amount=5000000,  # 50000 руб
            status=random.choice([PaymentStatus.SUCCESS, PaymentStatus.PENDING]),
            period="2024-2025 учебный год, 1 семестр",
            description="Оплата проживания в общежитии",
        )
        db.add(payment_dormitory)
        created_count += 1
    
    # Создаем платежи за платные мероприятия
    paid_events = db.query(Event).filter(Event.event_type == EventType.PAID).all()
    for event in paid_events[:3]:  # Берем первые 3 платных мероприятия
        # Находим студентов, записанных на это мероприятие
        registrations = db.query(EventRegistration).filter(EventRegistration.event_id == event.id).limit(2).all()
        for reg in registrations:
            payment_event = Payment(
                user_id=reg.user_id,
                payment_type=PaymentType.EVENT,
                amount=event.price,
                status=random.choice([PaymentStatus.SUCCESS, PaymentStatus.PENDING]),
                event_id=event.id,
            )
            db.add(payment_event)
            created_count += 1
    
    db.commit()
    print(f"  ✅ Создано платежей: {created_count}")
    return created_count


def seed_broadcasts(db: Session):
    """Создать тестовые рассылки"""
    print("\n📢 Создаем тестовые рассылки...")
    
    # Получаем всех преподавателей
    teachers = db.query(User).join(Teacher).filter(User.role == UserRole.STAFF).all()
    if not teachers:
        print("  ⚠️  Не найдено преподавателей в базе данных")
        return 0
    
    # Получаем группы
    groups = db.query(StudentGroup).all()
    if not groups:
        print("  ⚠️  Не найдено групп в базе данных")
        return 0
    
    # Получаем факультеты
    faculties = db.query(Faculty).all()
    if not faculties:
        print("  ⚠️  Не найдено факультетов в базе данных")
        return 0
    
    created_count = 0
    
    # Создаем рассылки для групп
    for teacher in teachers[:3]:  # Берем первых 3 преподавателей
        for group in groups[:2]:  # Берем первые 2 группы
            broadcast = Broadcast(
                author_user_id=teacher.id,
                group_id=group.id,
                title=f"Важное объявление для группы {group.name}",
                message=f"Уважаемые студенты группы {group.name}! Напоминаю о важном событии. Пожалуйста, ознакомьтесь с информацией.",
            )
            db.add(broadcast)
            created_count += 1
    
    # Создаем рассылки для факультетов
    for teacher in teachers[3:5] if len(teachers) > 3 else []:  # Следующие 2 преподавателя
        for faculty in faculties[:2]:  # Берем первые 2 факультета
            broadcast = Broadcast(
                author_user_id=teacher.id,
                faculty_id=faculty.id,
                title=f"Объявление для факультета {faculty.title}",
                message=f"Уважаемые студенты факультета {faculty.title}! Информация для всех групп факультета.",
            )
            db.add(broadcast)
            created_count += 1
    
    db.commit()
    print(f"  ✅ Создано рассылок: {created_count}")
    return created_count


def main():
    """Основная функция для заполнения базы данных"""
    print("=" * 60)
    print("Заполнение базы данных регистрациями и заявками")
    print("=" * 60)
    
    db: Session = SessionLocal()
    
    try:
        # Заполняем данные
        seed_event_registrations(db)
        seed_elective_registrations(db)
        seed_requests(db)
        seed_payments(db)
        seed_broadcasts(db)
        
        print("\n" + "=" * 60)
        print("✅ Заполнение базы данных завершено успешно!")
        print("=" * 60)
        
        # Выводим статистику
        event_reg_count = db.query(EventRegistration).count()
        elective_reg_count = db.query(ElectiveRegistration).count()
        requests_count = db.query(Request).count()
        pending_requests = db.query(Request).filter(Request.status == RequestStatus.PENDING).count()
        payments_count = db.query(Payment).count()
        broadcasts_count = db.query(Broadcast).count()
        
        print(f"\nСтатистика:")
        print(f"  Регистраций на события: {event_reg_count}")
        print(f"  Регистраций на элективы: {elective_reg_count}")
        print(f"  Всего заявок: {requests_count}")
        print(f"  Заявок на согласование: {pending_requests}")
        print(f"  Платежей: {payments_count}")
        print(f"  Рассылок: {broadcasts_count}")
        
    except Exception as e:
        print(f"\n❌ Ошибка при заполнении базы данных: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()

