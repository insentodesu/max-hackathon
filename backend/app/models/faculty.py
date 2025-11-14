from sqlalchemy import Column, Text, ForeignKey
from sqlalchemy.orm import relationship
import uuid

from app.db.base_class import Base
from app.db.types import GUID


class Faculty(Base):
    __tablename__ = "faculties"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    university_id = Column(GUID(), ForeignKey("universities.id"), nullable=False)
    title = Column(Text, nullable=False)

    # Relationships
    university = relationship("University", back_populates="faculties")
    student_groups = relationship("StudentGroup", back_populates="faculty")
    kafedras = relationship("Kafedra", back_populates="faculty")
    students = relationship("Student", back_populates="faculty")
    broadcasts = relationship("Broadcast", back_populates="faculty", foreign_keys="Broadcast.faculty_id")

