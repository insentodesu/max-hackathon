from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
import uuid

from app.db.base_class import Base
from app.db.types import GUID


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    teacher_user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    room_id = Column(GUID(), ForeignKey("rooms.id"), nullable=False)
    subject_id = Column(GUID(), ForeignKey("subjects.id"), nullable=False)
    pair_no = Column(Integer, ForeignKey("timeslots.pair_no"), nullable=False)

    # Relationships
    teacher = relationship("User", back_populates="lessons", foreign_keys=[teacher_user_id])
    room = relationship("Room", back_populates="lessons")
    subject = relationship("Subject", back_populates="lessons")
    timeslot = relationship("Timeslot", back_populates="lessons")
    groups = relationship("LessonGroup", back_populates="lesson", cascade="all, delete-orphan")

