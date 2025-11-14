from sqlalchemy.orm import Session
from sqlalchemy import and_
import uuid

from app.models.user import User, UserRole
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.staff import Staff
from app.models.student_group import StudentGroup
from app.models.faculty import Faculty
from app.models.kafedra import Kafedra
from app.models.university import University
from app.schemas.user import UserRegistrationRequest, UserVerificationRequest, UserVerificationResponse
from app.core.security import create_access_token
from app.schemas.auth import Token


def register_user(db: Session, *, registration_data: UserRegistrationRequest) -> tuple[User, Token]:
    """
    Самостоятельная регистрация пользователя (4.1.1)
    
    Регистрация происходит через бота в мессенджере MAX.
    Бот передает max_id пользователя из мессенджера.
    
    Логика:
    1. Проверяем данные через верификацию с БД деканата
    2. Если пользователь найден в БД деканата - обновляем его max_id
    3. Если не найден - создаем нового пользователя с max_id
    """
    # Проверяем существование университета
    university = db.query(University).filter(University.id == registration_data.university_id).first()
    if not university:
        raise ValueError("Университет не найден")
    
    # Проверяем, что город совпадает с городом университета
    if university.city != registration_data.city:
        raise ValueError(f"Город не совпадает с городом университета. Ожидается: {university.city}")
    
    # Проверяем, не существует ли уже пользователь с таким max_id
    existing_user_by_max_id = db.query(User).filter(User.max_id == registration_data.max_id).first()
    if existing_user_by_max_id:
        raise ValueError(f"Пользователь с max_id={registration_data.max_id} уже зарегистрирован")
    
    if registration_data.role == UserRole.STUDENT:
        # Проверяем обязательные поля для студента
        if not registration_data.faculty_id or not registration_data.group_id or not registration_data.student_card:
            raise ValueError("Для студента необходимо указать факультет, группу и номер студенческого билета")
        
        # Проверяем существование факультета
        faculty = db.query(Faculty).filter(
            and_(
                Faculty.id == registration_data.faculty_id,
                Faculty.university_id == registration_data.university_id
            )
        ).first()
        if not faculty:
            raise ValueError("Факультет не найден")
        
        # Проверяем существование группы
        group = db.query(StudentGroup).filter(
            and_(
                StudentGroup.id == registration_data.group_id,
                StudentGroup.faculty_id == registration_data.faculty_id
            )
        ).first()
        if not group:
            raise ValueError("Группа не найдена")
        
        # Сначала проверяем верификацию - существует ли студент в БД деканата
        verification_request = UserVerificationRequest(
            max_id=registration_data.max_id,
            role=UserRole.STUDENT,
            full_name=registration_data.full_name,
            student_card=registration_data.student_card,
            city=registration_data.city,
        )
        verification_result = verify_user_after_registration(db, verification_request, registration_data.max_id)
        
        if not verification_result.success:
            raise ValueError(verification_result.message)
        
        # Если пользователь найден в БД деканата - обновляем его max_id
        if verification_result.user_id:
            user = db.query(User).filter(User.id == verification_result.user_id).first()
            if user:
                # Обновляем max_id у существующего пользователя
                user.max_id = registration_data.max_id
                db.commit()
                db.refresh(user)
                
                # Создаем токен
                access_token = create_access_token(subject=str(user.id))
                token = Token(access_token=access_token, token_type="bearer")
                return user, token
        
        # Если пользователь не найден в БД деканата, но верификация прошла - создаем нового
        # (это не должно происходить, но на всякий случай)
        
        # Проверяем, не существует ли уже студент с таким номером билета
        existing_student = db.query(Student).filter(
            Student.student_card == registration_data.student_card
        ).first()
        if existing_student:
            raise ValueError("Студент с таким номером студенческого билета уже зарегистрирован")
        
        # Создаем нового пользователя с max_id
        user = User(
            max_id=registration_data.max_id,
            role=UserRole.STUDENT,
            full_name=registration_data.full_name,
            city=registration_data.city,
            university_id=registration_data.university_id,
        )
        db.add(user)
        db.flush()
        
        # Создаем студента
        student = Student(
            user_id=user.id,
            student_card=registration_data.student_card,
            faculty_id=registration_data.faculty_id,
            group_id=registration_data.group_id,
        )
        db.add(student)
        db.commit()
        db.refresh(user)
        
        # Создаем токен
        access_token = create_access_token(subject=str(user.id))
        token = Token(access_token=access_token, token_type="bearer")
        
        return user, token
    
    elif registration_data.role == UserRole.STAFF:
        # Проверяем обязательные поля для преподавателя/сотрудника
        if not registration_data.kafedra_id or not registration_data.tab_number:
            raise ValueError("Для преподавателя/сотрудника необходимо указать кафедру/отдел и табельный номер")
        
        # Проверяем существование кафедры
        kafedra = db.query(Kafedra).filter(
            and_(
                Kafedra.id == registration_data.kafedra_id,
                Kafedra.faculty_id.in_(
                    db.query(Faculty.id).filter(Faculty.university_id == registration_data.university_id)
                )
            )
        ).first()
        if not kafedra:
            raise ValueError("Кафедра/отдел не найдена")
        
        # Сначала проверяем верификацию - существует ли преподаватель/сотрудник в БД деканата
        verification_request = UserVerificationRequest(
            max_id=registration_data.max_id,
            role=UserRole.STAFF,
            full_name=registration_data.full_name,
            tab_number=registration_data.tab_number,
            city=registration_data.city,
        )
        verification_result = verify_user_after_registration(db, verification_request, registration_data.max_id)
        
        if not verification_result.success:
            raise ValueError(verification_result.message)
        
        # Если пользователь найден в БД деканата - обновляем его max_id
        if verification_result.user_id:
            user = db.query(User).filter(User.id == verification_result.user_id).first()
            if user:
                # Обновляем max_id у существующего пользователя
                user.max_id = registration_data.max_id
                db.commit()
                db.refresh(user)
                
                # Создаем токен
                access_token = create_access_token(subject=str(user.id))
                token = Token(access_token=access_token, token_type="bearer")
                return user, token
        
        # Если пользователь не найден в БД деканата, но верификация прошла - создаем нового
        # (это не должно происходить, но на всякий случай)
        
        # Проверяем, не существует ли уже преподаватель/сотрудник с таким табельным номером
        existing_teacher = db.query(Teacher).filter(
            Teacher.tab_number == registration_data.tab_number
        ).first()
        existing_staff = db.query(Staff).filter(
            Staff.tab_number == registration_data.tab_number
        ).first()
        if existing_teacher or existing_staff:
            raise ValueError("Пользователь с таким табельным номером уже зарегистрирован")
        
        # Создаем нового пользователя с max_id
        user = User(
            max_id=registration_data.max_id,
            role=UserRole.STAFF,
            full_name=registration_data.full_name,
            city=registration_data.city,
            university_id=registration_data.university_id,
        )
        db.add(user)
        db.flush()
        
        # Создаем преподавателя (или сотрудника - можно определить по kafedra)
        teacher = Teacher(
            user_id=user.id,
            tab_number=registration_data.tab_number,
            kafedra_id=registration_data.kafedra_id,
        )
        db.add(teacher)
        db.commit()
        db.refresh(user)
        
        # Создаем токен
        access_token = create_access_token(subject=str(user.id))
        token = Token(access_token=access_token, token_type="bearer")
        
        return user, token
    
    else:
        raise ValueError(f"Регистрация для роли {registration_data.role} не поддерживается")


def verify_user_after_registration(db: Session, request: UserVerificationRequest, max_id: int | None = None) -> UserVerificationResponse:
    """
    Верификация после регистрации - проверяет, что данные совпадают с БД деканата
    
    Если пользователь найден в БД деканата, обновляет его max_id.
    """
    from app.services.user_service import (
        get_student_by_card,
        get_staff_by_tab_number,
        get_teacher_by_tab_number
    )
    
    if request.role == UserRole.STUDENT:
        if not request.student_card:
            return UserVerificationResponse(
                success=False,
                message="Для студента необходимо указать номер студенческого билета",
                user_id=None,
                max_id=None
            )
        
        student = get_student_by_card(db, request.student_card)
        if not student:
            return UserVerificationResponse(
                success=False,
                message="Данные не найдены. Обратитесь в администрацию вашего вуза",
                user_id=None,
                max_id=None
            )
        
        # Проверяем совпадение данных
        user = student.user
        if user.full_name != request.full_name or user.city != request.city:
            return UserVerificationResponse(
                success=False,
                message="Данные не совпадают с данными в базе деканата. Обратитесь в администрацию вашего вуза",
                user_id=None,
                max_id=None
            )
        
        # Обновляем max_id у найденного пользователя, если он передан
        if max_id is not None:
            user.max_id = max_id
            db.commit()
            db.refresh(user)
        
        return UserVerificationResponse(
            success=True,
            message="Успешная верификация",
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
        
        staff = get_staff_by_tab_number(db, request.tab_number)
        teacher = get_teacher_by_tab_number(db, request.tab_number) if not staff else None
        
        person = staff or teacher
        if not person:
            return UserVerificationResponse(
                success=False,
                message="Данные не найдены. Обратитесь в администрацию вашего вуза",
                user_id=None,
                max_id=None
            )
        
        user = person.user
        if user.full_name != request.full_name or user.city != request.city:
            return UserVerificationResponse(
                success=False,
                message="Данные не совпадают с данными в базе деканата. Обратитесь в администрацию вашего вуза",
                user_id=None,
                max_id=None
            )
        
        # Обновляем max_id у найденного пользователя, если он передан
        if max_id is not None:
            user.max_id = max_id
            db.commit()
            db.refresh(user)
        
        return UserVerificationResponse(
            success=True,
            message="Успешная верификация",
            user_id=user.id,
            max_id=user.max_id
        )
    
    return UserVerificationResponse(
        success=False,
        message=f"Верификация для роли {request.role} не поддерживается",
        user_id=None,
        max_id=None
    )

