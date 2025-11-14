from datetime import datetime
from pydantic import BaseModel, ConfigDict
import uuid
from app.models.user import UserRole


class UserBase(BaseModel):
    full_name: str
    city: str
    role: UserRole


class UserCreate(UserBase):
    max_id: int | None = None
    university_id: uuid.UUID | None = None


class UserRead(UserBase):
    id: uuid.UUID
    max_id: int | None = None
    university_id: uuid.UUID | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UserRegistrationRequest(BaseModel):
    """Схема для самостоятельной регистрации пользователя (4.1.1)
    
    Регистрация происходит через бота в мессенджере MAX.
    Бот передает max_id пользователя из мессенджера.
    """
    max_id: int  # ID пользователя из мессенджера MAX (обязательное поле от бота)
    role: UserRole  # "Студент" или "Преподаватель/Сотрудник"
    full_name: str  # ФИО
    city: str  # Город
    university_id: uuid.UUID  # ВУЗ
    
    # Для студентов
    faculty_id: uuid.UUID | None = None  # Факультет
    group_id: uuid.UUID | None = None  # Направление/группа
    student_card: str | None = None  # Номер студенческого билета
    
    # Для преподавателей/сотрудников
    kafedra_id: uuid.UUID | None = None  # Кафедра/отдел
    tab_number: str | None = None  # Табельный номер


class UserVerificationRequest(BaseModel):
    """Схема для Модуля 1: верификация пользователя (проверка существования в БД деканата)"""
    max_id: int | None = None  # ID пользователя из мессенджера MAX (для привязки)
    role: UserRole
    full_name: str
    student_card: str | None = None  # Для студентов
    tab_number: str | None = None  # Для преподавателей/сотрудников
    city: str
    university_name: str | None = None


class UserRegistrationResponse(BaseModel):
    """Ответ на регистрацию пользователя"""
    success: bool
    message: str
    user_id: uuid.UUID
    access_token: str
    token_type: str = "bearer"


class UserVerificationResponse(BaseModel):
    """Ответ на верификацию пользователя"""
    success: bool
    message: str
    user_id: uuid.UUID | None = None
    max_id: int | None = None


class ProfileRead(BaseModel):
    """Схема для личного кабинета"""
    full_name: str  # ФИО
    role: str  # Роль (студент/преподаватель/сотрудник)
    
    # Для студентов
    course_faculty_group: str | None = None  # "2 курса, Экономический факультет, 204 группа"
    place_of_study: str | None = None  # "ФГБОУ ВО «КубГУ», Краснодар"
    student_card: str | None = None  # Номер студенческого билета
    
    # Для преподавателей/сотрудников
    place_of_work: str | None = None  # "ФГБОУ ВО «КубГУ», Краснодар"
    kafedra: str | None = None  # Кафедра/отдел (для преподавателей)
    tab_number: str | None = None  # Табельный номер
    
    model_config = ConfigDict(from_attributes=True)
