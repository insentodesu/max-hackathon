from sqlalchemy import Column, Date, Integer, ForeignKey
from sqlalchemy.orm import relationship
import uuid

from app.db.base_class import Base
from app.db.types import GUID


class ScheduleMeta(Base):
    __tablename__ = "schedule_metas"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    group_id = Column(GUID(), ForeignKey("student_groups.id"), nullable=False)
    teacher_user_id = Column(GUID(), ForeignKey("users.id"), nullable=True)
    week_start = Column(Date, nullable=False)
    version = Column(Integer, nullable=False, default=1)

    # Relationships
    group = relationship("StudentGroup", back_populates="schedule_metas")
    teacher = relationship("User", back_populates="schedule_metas", foreign_keys=[teacher_user_id])

