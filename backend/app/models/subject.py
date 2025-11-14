from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
import uuid

from app.db.base_class import Base
from app.db.types import GUID


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String, nullable=False)

    # Relationships
    lessons = relationship("Lesson", back_populates="subject")

