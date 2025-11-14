from sqlalchemy.orm import Session
import uuid

from app.models.user import User, UserRole
from app.models.student import Student
from app.schemas.student import StudentCreate


def create_student(db: Session, *, student_data: StudentCreate) -> Student:
    """
    Модуль 2: Добавление нового студента
    Создает пользователя и студента
    """
    # Создаем пользователя
    user = User(
        role=UserRole.STUDENT,
        full_name=student_data.full_name,
        city=student_data.city,
        university_id=student_data.university_id,
    )
    db.add(user)
    db.flush()  # Получаем ID пользователя
    
    # Создаем студента
    student = Student(
        user_id=user.id,
        student_card=student_data.student_card,
        faculty_id=student_data.faculty_id,
        group_id=student_data.group_id,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    db.refresh(user)
    return student


def get_student_by_id(db: Session, user_id: uuid.UUID) -> Student | None:
    return db.query(Student).filter(Student.user_id == user_id).first()


def get_students_by_group(db: Session, group_id: uuid.UUID):
    return db.query(Student).filter(Student.group_id == group_id).all()



