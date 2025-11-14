"""
Модуль 3: Лента событий и запись на мероприятия

Примечание: Push-уведомления об анонсах новых мероприятий обрабатываются ботом мессенджера MAX.
Backend только предоставляет API для работы с мероприятиями и регистрациями.
Бот отслеживает создание новых мероприятий через API и отправляет push-уведомления пользователям.
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from datetime import datetime
import uuid
from datetime import timezone

from app.models.event import Event, EventRegistration
from app.schemas.event import EventCreate, EventUpdate


def get_event_by_id(db: Session, event_id: uuid.UUID) -> Optional[Event]:
    """Получить мероприятие по ID"""
    return db.query(Event).filter(Event.id == event_id).first()


def get_all_events(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 100,
    upcoming_only: bool = True
) -> List[Event]:
    """Получить все мероприятия"""
    query = db.query(Event)
    
    if upcoming_only:
        query = query.filter(Event.date >= func.now())
    
    return query.order_by(Event.date.asc()).offset(skip).limit(limit).all()


def get_user_events(db: Session, user_id: uuid.UUID) -> List[Event]:
    """Получить мероприятия, на которые записан пользователь (Мои события)"""
    return db.query(Event).join(EventRegistration).filter(
        and_(
            EventRegistration.user_id == user_id,
            Event.date >= func.now()  # Только предстоящие
        )
    ).order_by(Event.date.asc()).all()


def create_event(db: Session, *, event_data: EventCreate) -> Event:
    """Создать новое мероприятие"""
    # Преобразуем topics в JSON строку
    topics_json = None
    if event_data.topics:
        import json
        topics_json = json.dumps(event_data.topics, ensure_ascii=False)
    
    event = Event(
        title=event_data.title,
        description=event_data.description,
        date=event_data.date,
        end_time=event_data.end_time,
        event_type=event_data.event_type,
        price=event_data.price,
        format=event_data.format,
        location=event_data.location,
        max_participants=event_data.max_participants,
        image_url=event_data.image_url,
        speaker_name=event_data.speaker_name,
        speaker_bio=event_data.speaker_bio,
        topics=topics_json,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def update_event(db: Session, *, event_id: uuid.UUID, event_data: EventUpdate) -> Optional[Event]:
    """Обновить мероприятие"""
    event = get_event_by_id(db, event_id)
    if not event:
        return None
    
    update_data = event_data.model_dump(exclude_unset=True)
    
    # Обрабатываем topics
    if "topics" in update_data and update_data["topics"] is not None:
        import json
        update_data["topics"] = json.dumps(update_data["topics"], ensure_ascii=False)
    
    for field, value in update_data.items():
        if hasattr(event, field):
            setattr(event, field, value)
    
    db.commit()
    db.refresh(event)
    return event


def register_for_event(db: Session, *, event_id: uuid.UUID, user_id: uuid.UUID) -> EventRegistration:
    """Записаться на мероприятие"""
    event = get_event_by_id(db, event_id)
    if not event:
        raise ValueError("Мероприятие не найдено")
    
    # Проверяем, не записан ли уже
    existing = db.query(EventRegistration).filter(
        and_(
            EventRegistration.event_id == event_id,
            EventRegistration.user_id == user_id
        )
    ).first()
    
    if existing:
        raise ValueError("Вы уже записаны на это мероприятие")
    
    # Проверяем наличие свободных мест
    if event.current_participants >= event.max_participants:
        raise ValueError("Нет свободных мест")
    
    # Проверяем, не прошло ли мероприятие
    now = datetime.now(timezone.utc)
    # Если event.date не имеет timezone, считаем его UTC
    event_date = event.date
    if event_date.tzinfo is None:
        event_date = event_date.replace(tzinfo=timezone.utc)
    if event_date < now:
        raise ValueError("Мероприятие уже прошло")
    
    registration = EventRegistration(
        event_id=event_id,
        user_id=user_id,
    )
    db.add(registration)
    
    # Увеличиваем счетчик участников
    event.current_participants += 1
    
    db.commit()
    db.refresh(registration)
    return registration


def unregister_from_event(db: Session, *, event_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    """Отписаться от мероприятия"""
    registration = db.query(EventRegistration).filter(
        and_(
            EventRegistration.event_id == event_id,
            EventRegistration.user_id == user_id
        )
    ).first()
    
    if not registration:
        raise ValueError("Вы не записаны на это мероприятие")
    
    event = get_event_by_id(db, event_id)
    if event:
        # Уменьшаем счетчик участников
        event.current_participants = max(0, event.current_participants - 1)
    
    db.delete(registration)
    db.commit()
    return True


def is_user_registered(db: Session, *, event_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    """Проверить, записан ли пользователь на мероприятие"""
    registration = db.query(EventRegistration).filter(
        and_(
            EventRegistration.event_id == event_id,
            EventRegistration.user_id == user_id
        )
    ).first()
    return registration is not None


def get_event_participants_count(db: Session, event_id: uuid.UUID) -> int:
    """Получить количество зарегистрированных участников"""
    return db.query(EventRegistration).filter(EventRegistration.event_id == event_id).count()

