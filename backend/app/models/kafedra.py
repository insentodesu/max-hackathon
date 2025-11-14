from sqlalchemy import Column, Text, ForeignKey
from sqlalchemy.orm import relationship
import uuid

from app.db.base_class import Base
from app.db.types import GUID


class Kafedra(Base):
    __tablename__ = "kafedras"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    faculty_id = Column(GUID(), ForeignKey("faculties.id"), nullable=False)
    title = Column(Text, nullable=True)  # Добавил title, так как обычно у кафедры есть название

    # Relationships
    faculty = relationship("Faculty", back_populates="kafedras")
    teachers = relationship("Teacher", back_populates="kafedra")

