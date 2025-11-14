from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.db.types import GUID


class LessonGroup(Base):
    __tablename__ = "lesson_groups"

    lesson_id = Column(GUID(), ForeignKey("lessons.id"), primary_key=True)
    group_id = Column(GUID(), ForeignKey("student_groups.id"), primary_key=True)

    # Relationships
    lesson = relationship("Lesson", back_populates="groups")
    group = relationship("StudentGroup", back_populates="lesson_groups")

