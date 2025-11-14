from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
import uuid
import json

from app.models.event import EventType, EventFormat


class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    date: datetime
    end_time: Optional[datetime] = None
    event_type: EventType
    price: Optional[int] = None
    format: EventFormat
    location: Optional[str] = None
    max_participants: int = 100
    speaker_name: Optional[str] = None
    speaker_bio: Optional[str] = None
    topics: Optional[List[str]] = None  # Список тем


class EventCreate(EventBase):
    """Схема для создания мероприятия"""
    image_url: Optional[str] = None


class EventUpdate(BaseModel):
    """Схема для обновления мероприятия"""
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[datetime] = None
    end_time: Optional[datetime] = None
    event_type: Optional[EventType] = None
    price: Optional[int] = None
    format: Optional[EventFormat] = None
    location: Optional[str] = None
    max_participants: Optional[int] = None
    image_url: Optional[str] = None
    speaker_name: Optional[str] = None
    speaker_bio: Optional[str] = None
    topics: Optional[List[str]] = None


class EventRead(EventBase):
    """Схема для чтения мероприятия"""
    id: uuid.UUID
    current_participants: int
    image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_registered: bool = False  # Зарегистрирован ли текущий пользователь
    model_config = ConfigDict(from_attributes=True)


class EventRegistrationRead(BaseModel):
    """Схема для чтения записи на мероприятие"""
    id: uuid.UUID
    event_id: uuid.UUID
    user_id: uuid.UUID
    registered_at: datetime
    model_config = ConfigDict(from_attributes=True)

