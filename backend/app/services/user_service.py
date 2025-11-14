from sqlalchemy.orm import Session
from sqlalchemy import and_
import uuid
import re

from app.models.user import User, UserRole
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.staff import Staff
from app.schemas.user import UserCreate, UserVerificationRequest, UserVerificationResponse


def get_user_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_max_id(db: Session, max_id: int) -> User | None:
    """Получить пользователя по max_id (ID из внешней системы деканата)"""
    return db.query(User).filter(User.max_id == max_id).first()


def get_student_by_card(db: Session, student_card: str) -> Student | None:
    """Получить студента по номеру студенческого билета"""
    return db.query(Student).filter(Student.student_card == student_card).first()


def get_teacher_by_tab_number(db: Session, tab_number: str) -> Teacher | None:
    """Получить преподавателя по табельному номеру"""
    return db.query(Teacher).filter(Teacher.tab_number == tab_number).first()


def get_staff_by_tab_number(db: Session, tab_number: str) -> Staff | None:
    """Получить сотрудника по табельному номеру"""
    return db.query(Staff).filter(Staff.tab_number == tab_number).first()


def create_user(db: Session, *, user_data: UserCreate) -> User:
    """Создать нового пользователя"""
    user = User(
        max_id=user_data.max_id,
        role=user_data.role,
        full_name=user_data.full_name,
        city=user_data.city,
        university_id=user_data.university_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def verify_user(db: Session, *, request: UserVerificationRequest) -> UserVerificationResponse:
    """
    Модуль 1: Верификация пользователя
    Проверяет существование пользователя в базе деканата и привязывает max_id к существующему пользователю
    
    Если max_id передан в запросе, обновляет его у найденного пользователя.
    """
    if request.role == UserRole.STUDENT:
        if not request.student_card:
            return UserVerificationResponse(
                success=False,
                message="Для студента необходимо указать номер студенческого билета",
                user_id=None,
                max_id=None
            )
        
        # Ищем студента по номеру студенческого билета
        student = get_student_by_card(db, request.student_card)
        if not student:
            return UserVerificationResponse(
                success=False,
                message="Данные не найдены. Обратитесь в администрацию вашего вуза",
                user_id=None,
                max_id=None
            )
        
        # Студент найден - привязываем max_id к существующему пользователю
        user = student.user
        
        # Если max_id передан в запросе, обновляем его у найденного пользователя
        if request.max_id is not None:
            user.max_id = request.max_id
            db.commit()
            db.refresh(user)
        
        return UserVerificationResponse(
            success=True,
            message="Успешная верификация. Привязываем max_id к уже созданному (деканатом) пользователю",
            user_id=user.id,
            max_id=user.max_id
        )
    
    elif request.role == UserRole.STAFF:
        if not request.tab_number:
            return UserVerificationResponse(
                success=False,
                message="Для сотрудника необходимо указать табельный номер",
                user_id=None,
                max_id=None
            )
        
        # Ищем сотрудника по табельному номеру
        staff = get_staff_by_tab_number(db, request.tab_number)
        if not staff:
            return UserVerificationResponse(
                success=False,
                message="Данные не найдены. Обратитесь в администрацию вашего вуза",
                user_id=None,
                max_id=None
            )
        
        user = staff.user
        
        # Если max_id передан в запросе, обновляем его у найденного пользователя
        if request.max_id is not None:
            user.max_id = request.max_id
            db.commit()
            db.refresh(user)
        
        return UserVerificationResponse(
            success=True,
            message="Успешная верификация. Привязываем max_id к уже созданному (деканатом) пользователю",
            user_id=user.id,
            max_id=user.max_id
        )
    
    else:
        # Для других ролей (например, admin) можно добавить свою логику
        return UserVerificationResponse(
            success=False,
            message=f"Верификация для роли {request.role} пока не поддерживается",
            user_id=None,
            max_id=None
        )


def get_user_profile(db: Session, user_id: uuid.UUID) -> dict:
    """Получить данные личного кабинета пользователя"""
    user = db.get(User, user_id)
    if not user:
        raise ValueError("Пользователь не найден")
    
    profile = {
        "full_name": user.full_name,
        "role": user.role.value,
    }
    
    # Формируем место учёбы/работы
    if user.university:
        place = f"{user.university.name}, {user.university.city}"
    else:
        place = f"{user.city}"
    
    if user.role == UserRole.STUDENT:
        if user.student:
            student = user.student
            # Получаем факультет и группу
            faculty_name = student.faculty.title if student.faculty else "Неизвестно"
            group_name = student.group.name if student.group else "Неизвестно"
            
            # Пытаемся извлечь курс из названия группы (например, "204" -> "2 курс")
            # Или можно просто использовать номер группы
            course = "Не указан"
            if student.group and student.group.name:
                # Пытаемся найти цифру в начале названия группы
                match = re.match(r'(\d+)', student.group.name)
                if match:
                    group_num = int(match.group(1))
                    # Предполагаем, что номер группы содержит курс (например, 204 = 2 курс)
                    course = f"{group_num // 100} курса" if group_num >= 100 else f"{group_num} курса"
            
            profile["course_faculty_group"] = f"{course}, {faculty_name}, {group_name} группа"
            profile["place_of_study"] = place
            profile["student_card"] = student.student_card
    
    elif user.role == UserRole.STAFF:
        profile["place_of_work"] = place
        
        # Проверяем, преподаватель или сотрудник
        if user.teacher:
            profile["kafedra"] = user.teacher.kafedra.title if user.teacher.kafedra else None
            profile["tab_number"] = user.teacher.tab_number
        elif user.staff:
            profile["tab_number"] = user.staff.tab_number
    
    return profile
