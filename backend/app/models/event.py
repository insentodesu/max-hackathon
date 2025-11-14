from sqlalchemy import Column, String, Text, DateTime, Integer, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid

from app.db.base_class import Base
from app.db.types import GUID


class EventType(str, enum.Enum):
    """Тип мероприятия (бесплатное/платное)"""
    FREE = "free"  # Бесплатное
    PAID = "paid"  # Платное


class EventFormat(str, enum.Enum):
    """Формат мероприятия"""
    ONLINE = "online"  # Онлайн
    OFFLINE = "offline"  # Оффлайн


class Event(Base):
    __tablename__ = "events"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    date = Column(DateTime(timezone=True), nullable=False)  # Дата и время начала
    end_time = Column(DateTime(timezone=True), nullable=True)  # Время окончания
    event_type = Column(SQLEnum(EventType), nullable=False, default=EventType.FREE)
    price = Column(Integer, nullable=True)  # Стоимость (если платное)
    format = Column(SQLEnum(EventFormat), nullable=False, default=EventFormat.OFFLINE)
    location = Column(Text, nullable=True)  # Место проведения (для оффлайн) или ссылка (для онлайн)
    max_participants = Column(Integer, nullable=False, default=100)
    current_participants = Column(Integer, nullable=False, default=0)
    image_url = Column(Text, nullable=True)  # URL фото мероприятия
    speaker_name = Column(Text, nullable=True)  # Имя спикера
    speaker_bio = Column(Text, nullable=True)  # Биография спикера
    topics = Column(Text, nullable=True)  # JSON массив тем
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    registrations = relationship("EventRegistration", back_populates="event", cascade="all, delete-orphan")


class EventRegistration(Base):
    __tablename__ = "event_registrations"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    event_id = Column(GUID(), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    registered_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    event = relationship("Event", back_populates="registrations")
    user = relationship("User", foreign_keys=[user_id])

