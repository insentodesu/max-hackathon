from sqlalchemy import Column, DateTime, Text, ForeignKey
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.base_class import Base
from app.db.types import GUID


class ScheduleChangelog(Base):
    __tablename__ = "schedule_changelogs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    group_id = Column(GUID(), ForeignKey("student_groups.id"), nullable=True)
    teacher_user_id = Column(GUID(), ForeignKey("users.id"), nullable=True)
    change_type = Column(Text, nullable=False)  # 'create', 'update', 'delete'
    change_data = Column(JSON, nullable=True)  # Данные об изменении
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    group = relationship("StudentGroup")
    teacher = relationship("User", foreign_keys=[teacher_user_id])

