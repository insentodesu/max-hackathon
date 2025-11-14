from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from datetime import datetime
import uuid

from app.models.elective import Elective, ElectiveRegistration
from app.schemas.elective import ElectiveCreate, ElectiveUpdate


def get_elective_by_id(db: Session, elective_id: uuid.UUID) -> Optional[Elective]:
    """Получить электив по ID"""
    return db.query(Elective).filter(Elective.id == elective_id).first()


def get_all_electives(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True
) -> List[Elective]:
    """Получить все элективы"""
    query = db.query(Elective)
    
    if active_only:
        query = query.filter(Elective.is_active == 1)
    
    return query.order_by(Elective.created_at.desc()).offset(skip).limit(limit).all()


def get_user_electives(db: Session, user_id: uuid.UUID) -> List[Elective]:
    """Получить элективы, на которые записан пользователь (Мои элективы)"""
    return db.query(Elective).join(ElectiveRegistration).filter(
        and_(
            ElectiveRegistration.user_id == user_id,
            Elective.is_active == 1
        )
    ).order_by(Elective.created_at.desc()).all()


def create_elective(db: Session, *, elective_data: ElectiveCreate) -> Elective:
    """Создать новый электив"""
    elective = Elective(
        title=elective_data.title,
        description=elective_data.description,
        teacher_user_id=elective_data.teacher_user_id,
        max_students=elective_data.max_students,
        schedule_info=elective_data.schedule_info,
        credits=elective_data.credits,
    )
    db.add(elective)
    db.commit()
    db.refresh(elective)
    return elective


def update_elective(db: Session, *, elective_id: uuid.UUID, elective_data: ElectiveUpdate) -> Optional[Elective]:
    """Обновить электив"""
    elective = get_elective_by_id(db, elective_id)
    if not elective:
        return None
    
    update_data = elective_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(elective, field):
            setattr(elective, field, value)
    
    db.commit()
    db.refresh(elective)
    return elective


def register_for_elective(db: Session, *, elective_id: uuid.UUID, user_id: uuid.UUID) -> ElectiveRegistration:
    """Записаться на электив"""
    elective = get_elective_by_id(db, elective_id)
    if not elective:
        raise ValueError("Электив не найден")
    
    if elective.is_active == 0:
        raise ValueError("Электив неактивен")
    
    # Проверяем, не записан ли уже
    existing = db.query(ElectiveRegistration).filter(
        and_(
            ElectiveRegistration.elective_id == elective_id,
            ElectiveRegistration.user_id == user_id
        )
    ).first()
    
    if existing:
        raise ValueError("Вы уже записаны на этот электив")
    
    # Проверяем наличие свободных мест
    if elective.current_students >= elective.max_students:
        raise ValueError("Нет свободных мест")
    
    registration = ElectiveRegistration(
        elective_id=elective_id,
        user_id=user_id,
    )
    db.add(registration)
    
    # Увеличиваем счетчик участников
    elective.current_students += 1
    
    db.commit()
    db.refresh(registration)
    return registration


def unregister_from_elective(db: Session, *, elective_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    """Отписаться от электива"""
    registration = db.query(ElectiveRegistration).filter(
        and_(
            ElectiveRegistration.elective_id == elective_id,
            ElectiveRegistration.user_id == user_id
        )
    ).first()
    
    if not registration:
        raise ValueError("Вы не записаны на этот электив")
    
    elective = get_elective_by_id(db, elective_id)
    if elective:
        # Уменьшаем счетчик участников
        elective.current_students = max(0, elective.current_students - 1)
    
    db.delete(registration)
    db.commit()
    return True


def is_user_registered(db: Session, *, elective_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    """Проверить, записан ли пользователь на электив"""
    registration = db.query(ElectiveRegistration).filter(
        and_(
            ElectiveRegistration.elective_id == elective_id,
            ElectiveRegistration.user_id == user_id
        )
    ).first()
    return registration is not None

