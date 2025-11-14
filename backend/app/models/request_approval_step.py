from sqlalchemy import Column, Integer, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid

from app.db.base_class import Base
from app.db.types import GUID


class ApprovalAction(str, enum.Enum):
    """Действия в процессе согласования"""
    PENDING = "pending"  # Ожидает согласования
    APPROVED = "approved"  # Одобрено
    REJECTED = "rejected"  # Отклонено


class RequestApprovalStep(Base):
    """Шаги согласования заявки"""
    __tablename__ = "request_approval_steps"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    request_id = Column(Integer, ForeignKey("requests.id", ondelete="CASCADE"), nullable=False, index=True)
    step_order = Column(Integer, nullable=False)  # Порядок шага (1, 2, 3...)
    approver_user_id = Column(GUID(), ForeignKey("users.id"), nullable=True)  # Кто должен согласовать
    approver_role = Column(Text, nullable=True)  # Роль согласующего (куратор, деканат, руководитель и т.д.)
    action = Column(SQLEnum(ApprovalAction), nullable=False, default=ApprovalAction.PENDING)
    comment = Column(Text, nullable=True)  # Комментарий при согласовании/отклонении
    processed_at = Column(DateTime(timezone=True), nullable=True)  # Когда обработано
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    request = relationship("Request", back_populates="approval_steps")
    approver = relationship("User", foreign_keys=[approver_user_id])

