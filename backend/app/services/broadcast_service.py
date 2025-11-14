from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
import uuid

from app.models.broadcast import Broadcast
from app.models.user import User, UserRole
from app.models.student import Student
from app.models.student_group import StudentGroup
from app.schemas.broadcast import BroadcastCreate


def get_broadcast_by_id(db: Session, broadcast_id: uuid.UUID) -> Optional[Broadcast]:
    """Получить рассылку по ID"""
    return db.query(Broadcast).filter(Broadcast.id == broadcast_id).first()


def get_broadcasts_for_user(db: Session, user_id: uuid.UUID) -> List[Broadcast]:
    """
    Получить рассылки для пользователя (студента)
    Рассылки для его группы или факультета
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.role != UserRole.STUDENT:
        return []
    
    student = db.query(Student).filter(Student.user_id == user_id).first()
    if not student or not student.group_id:
        return []
    
    group = db.query(StudentGroup).filter(StudentGroup.id == student.group_id).first()
    if not group:
        return []
    
    # Получаем рассылки для группы или для факультета группы
    query = db.query(Broadcast).filter(
        or_(
            Broadcast.group_id == group.id,
            Broadcast.faculty_id == group.faculty_id
        )
    )
    
    return query.order_by(Broadcast.created_at.desc()).all()


def get_broadcasts_for_group(db: Session, group_id: uuid.UUID) -> List[Broadcast]:
    """Получить рассылки для конкретной группы"""
    return db.query(Broadcast).filter(
        or_(
            Broadcast.group_id == group_id,
            Broadcast.faculty_id.in_(
                db.query(StudentGroup.faculty_id).filter(StudentGroup.id == group_id)
            )
        )
    ).order_by(Broadcast.created_at.desc()).all()


def get_teacher_broadcasts(db: Session, teacher_user_id: uuid.UUID) -> List[Broadcast]:
    """Получить все рассылки преподавателя"""
    return db.query(Broadcast).filter(
        Broadcast.author_user_id == teacher_user_id
    ).order_by(Broadcast.created_at.desc()).all()


def create_broadcast(db: Session, *, broadcast_data: BroadcastCreate, author_user_id: uuid.UUID) -> Broadcast:
    """Создать новую рассылку"""
    # Проверяем, что автор - преподаватель или админ
    user = db.query(User).filter(User.id == author_user_id).first()
    if not user or user.role not in [UserRole.STAFF, UserRole.ADMIN]:
        raise ValueError("Только преподаватели и администраторы могут создавать рассылки")
    
    # Проверяем, что указана либо группа, либо факультет
    if not broadcast_data.group_id and not broadcast_data.faculty_id:
        raise ValueError("Необходимо указать group_id или faculty_id")
    
    broadcast = Broadcast(
        author_user_id=author_user_id,
        title=broadcast_data.title,
        message=broadcast_data.message,
        group_id=broadcast_data.group_id,
        faculty_id=broadcast_data.faculty_id,
    )
    db.add(broadcast)
    db.commit()
    db.refresh(broadcast)
    return broadcast

