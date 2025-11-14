from sqlalchemy.orm import Session
import uuid

from app.models.user import User, UserRole
from app.models.teacher import Teacher
from app.schemas.teacher import TeacherCreate


def create_teacher(db: Session, *, teacher_data: TeacherCreate) -> Teacher:
    """
    Модуль 2: Добавление нового преподавателя
    Создает пользователя и преподавателя
    """
    # Создаем пользователя
    user = User(
        role=UserRole.STAFF,  # Преподаватели обычно имеют роль staff
        full_name=teacher_data.full_name,
        city=teacher_data.city,
        university_id=teacher_data.university_id,
    )
    db.add(user)
    db.flush()  # Получаем ID пользователя
    
    # Создаем преподавателя
    teacher = Teacher(
        user_id=user.id,
        tab_number=teacher_data.tab_number,
        kafedra_id=teacher_data.kafedra_id,
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    db.refresh(user)
    return teacher


def get_teacher_by_id(db: Session, user_id: uuid.UUID) -> Teacher | None:
    return db.query(Teacher).filter(Teacher.user_id == user_id).first()



