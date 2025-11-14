from sqlalchemy import Column, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.base_class import Base
from app.db.types import GUID


class Broadcast(Base):
    """Рассылка от преподавателя группе/потоку студентов"""
    __tablename__ = "broadcasts"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    author_user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)  # Преподаватель
    group_id = Column(GUID(), ForeignKey("student_groups.id", ondelete="CASCADE"), nullable=True, index=True)  # Группа (если null - для всех групп потока)
    faculty_id = Column(GUID(), ForeignKey("faculties.id", ondelete="CASCADE"), nullable=True, index=True)  # Факультет/поток (если указан, рассылка для всех групп факультета)
    title = Column(Text, nullable=False)  # Заголовок рассылки
    message = Column(Text, nullable=False)  # Текст рассылки
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    author = relationship("User", foreign_keys=[author_user_id])
    group = relationship("StudentGroup", foreign_keys=[group_id])
    faculty = relationship("Faculty", foreign_keys=[faculty_id])

