from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.db.types import GUID


class Student(Base):
    __tablename__ = "students"

    user_id = Column(GUID(), ForeignKey("users.id"), primary_key=True, index=True)
    faculty_id = Column(GUID(), ForeignKey("faculties.id"), nullable=False)
    group_id = Column(GUID(), ForeignKey("student_groups.id"), nullable=False)
    student_card = Column(String, nullable=False, unique=True)

    # Relationships
    user = relationship("User", back_populates="student")
    faculty = relationship("Faculty", back_populates="students")
    group = relationship("StudentGroup", back_populates="students")

