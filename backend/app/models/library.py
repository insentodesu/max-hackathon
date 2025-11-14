from sqlalchemy import Column, Text, ForeignKey
from sqlalchemy.orm import relationship
import uuid

from app.db.base_class import Base
from app.db.types import GUID


class LibraryAccess(Base):
    """Информация о доступе к электронной библиотеке"""
    __tablename__ = "library_access"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    university_id = Column(GUID(), ForeignKey("universities.id", ondelete="CASCADE"), nullable=False, index=True)
    login = Column(Text, nullable=False)  # Логин для доступа
    password = Column(Text, nullable=False)  # Пароль для доступа
    portal_url = Column(Text, nullable=False)  # Ссылка на портал библиотеки
    instructions = Column(Text, nullable=True)  # Пошаговая инструкция по доступу

    # Relationships
    university = relationship("University", foreign_keys=[university_id])

