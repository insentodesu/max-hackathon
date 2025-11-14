from sqlalchemy import Column, Text, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.base_class import Base
from app.db.types import GUID


class Elective(Base):
    """Факультативный курс"""
    __tablename__ = "electives"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(Text, nullable=False)  # Название курса
    description = Column(Text, nullable=True)  # Описание курса
    teacher_user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)  # Преподаватель
    max_students = Column(Integer, nullable=False, default=30)  # Максимальное количество студентов
    current_students = Column(Integer, nullable=False, default=0)  # Текущее количество записанных
    schedule_info = Column(Text, nullable=True)  # Информация о расписании (например, "Понедельник, 18:00")
    credits = Column(Integer, nullable=True)  # Количество кредитов
    is_active = Column(Integer, nullable=False, default=1)  # Активен ли курс (1 - да, 0 - нет)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    teacher = relationship("User", foreign_keys=[teacher_user_id])
    registrations = relationship("ElectiveRegistration", back_populates="elective", cascade="all, delete-orphan")


class ElectiveRegistration(Base):
    """Запись студента на электив"""
    __tablename__ = "elective_registrations"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    elective_id = Column(GUID(), ForeignKey("electives.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    registered_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    elective = relationship("Elective", back_populates="registrations")
    user = relationship("User", foreign_keys=[user_id])

