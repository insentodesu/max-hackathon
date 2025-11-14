from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.orm import relationship
import uuid

from app.db.base_class import Base
from app.db.types import GUID


class StudentGroup(Base):
    __tablename__ = "student_groups"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)
    faculty_id = Column(GUID(), ForeignKey("faculties.id"), nullable=False)
    code = Column(Text, nullable=False)
    curator_user_id = Column(GUID(), ForeignKey("users.id"), nullable=True)

    # Relationships
    faculty = relationship("Faculty", back_populates="student_groups")
    curator = relationship("User", back_populates="curated_groups", foreign_keys=[curator_user_id])
    students = relationship("Student", back_populates="group")
    lesson_groups = relationship("LessonGroup", back_populates="group")
    schedule_metas = relationship("ScheduleMeta", back_populates="group")

