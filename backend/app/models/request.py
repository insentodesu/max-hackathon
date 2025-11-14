from sqlalchemy import Column, Integer, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid

from app.db.base_class import Base
from app.db.types import GUID


class RequestType(str, enum.Enum):
    """Типы заявок"""
    STUDENT_CERTIFICATE = "student_certificate"  # Справка об обучении
    ACADEMIC_LEAVE = "academic_leave"  # Академический отпуск
    TRANSFER = "transfer"  # Заявка на перевод
    VACATION = "vacation"  # Отпуск (для преподавателей)
    DOCUMENT_APPROVAL = "document_approval"  # Документ на согласование


class RequestStatus(str, enum.Enum):
    """Статусы заявок"""
    PENDING = "pending"  # Ожидает решения
    APPROVED = "approved"  # Одобрено
    REJECTED = "rejected"  # Отклонено


class Request(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    request_type = Column(SQLEnum(RequestType), nullable=False)  # Тип заявки
    author_user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    status = Column(SQLEnum(RequestStatus), nullable=False, default=RequestStatus.PENDING)
    content = Column(Text, nullable=True)  # Содержание заявки
    rejection_reason = Column(Text, nullable=True)  # Причина отклонения
    current_approver_id = Column(GUID(), ForeignKey("users.id"), nullable=True)  # Текущий согласующий
    approval_road_id = Column(GUID(), ForeignKey("approval_roads.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    author = relationship("User", back_populates="created_requests", foreign_keys=[author_user_id])
    current_approver = relationship("User", foreign_keys=[current_approver_id])
    # ApprovalRoad relationship убран из-за проблем с инициализацией
    # Если нужен доступ к approval_road, можно получить через approval_road_id напрямую
    documents = relationship("RequestDocument", back_populates="request", cascade="all, delete-orphan")
    approval_steps = relationship("RequestApprovalStep", back_populates="request", cascade="all, delete-orphan")

