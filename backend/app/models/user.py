from sqlalchemy import Column, String, Text, DateTime, Integer, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.db.base_class import Base
from app.db.types import GUID


class UserRole(str, enum.Enum):
    STUDENT = "student"
    STAFF = "staff"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    max_id = Column(Integer, nullable=True)  # ID из внешней системы
    role = Column(SQLEnum(UserRole), nullable=False)
    full_name = Column(Text, nullable=False)
    city = Column(Text, nullable=False)
    university_id = Column(GUID(), ForeignKey("universities.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    university = relationship("University", back_populates="users", foreign_keys=[university_id])
    student = relationship("Student", back_populates="user", uselist=False)
    teacher = relationship("Teacher", back_populates="user", uselist=False)
    staff = relationship("Staff", back_populates="user", uselist=False)
    curated_groups = relationship("StudentGroup", back_populates="curator", foreign_keys="StudentGroup.curator_user_id")
    created_requests = relationship("Request", back_populates="author", foreign_keys="Request.author_user_id")
    lessons = relationship("Lesson", back_populates="teacher", foreign_keys="Lesson.teacher_user_id")
    schedule_metas = relationship("ScheduleMeta", back_populates="teacher", foreign_keys="ScheduleMeta.teacher_user_id")
    event_registrations = relationship("EventRegistration", back_populates="user", foreign_keys="EventRegistration.user_id")
    payments = relationship("Payment", back_populates="user", foreign_keys="Payment.user_id")
    elective_registrations = relationship("ElectiveRegistration", back_populates="user", foreign_keys="ElectiveRegistration.user_id")
    taught_electives = relationship("Elective", back_populates="teacher", foreign_keys="Elective.teacher_user_id")
    broadcasts = relationship("Broadcast", back_populates="author", foreign_keys="Broadcast.author_user_id")
