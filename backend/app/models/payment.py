from sqlalchemy import Column, String, Text, DateTime, Integer, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid

from app.db.base_class import Base
from app.db.types import GUID


class PaymentType(str, enum.Enum):
    """Тип платежа"""
    TUITION = "tuition"  # Оплата обучения
    DORMITORY = "dormitory"  # Оплата общежития
    EVENT = "event"  # Оплата мероприятия


class PaymentStatus(str, enum.Enum):
    """Статус платежа"""
    PENDING = "pending"  # Ожидает оплаты
    PROCESSING = "processing"  # В обработке
    SUCCESS = "success"  # Успешно оплачен
    FAILED = "failed"  # Ошибка оплаты
    CANCELLED = "cancelled"  # Отменен
    REFUNDED = "refunded"  # Возвращен


class Payment(Base):
    __tablename__ = "payments"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    payment_type = Column(SQLEnum(PaymentType), nullable=False)
    amount = Column(Integer, nullable=False)  # Сумма в копейках
    status = Column(SQLEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    
    # Связь с мероприятием (обязательно только для payment_type == EVENT)
    event_id = Column(GUID(), ForeignKey("events.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Данные для оплаты обучения/общежития (обязательно для payment_type == TUITION/DORMITORY)
    period = Column(Text, nullable=True)  # Период оплаты (например, "2024-2025 учебный год, 1 семестр")
    description = Column(Text, nullable=True)  # Описание платежа
    
    # ЮКасса данные
    yookassa_payment_id = Column(Text, nullable=True, unique=True, index=True)  # ID платежа в ЮКасса
    yookassa_confirmation_url = Column(Text, nullable=True)  # URL для подтверждения оплаты
    yookassa_payment_method_id = Column(Text, nullable=True)  # ID метода оплаты
    
    # Метаданные
    extra_data = Column(Text, nullable=True)  # JSON с дополнительными данными (переименовано из metadata, т.к. metadata зарезервировано в SQLAlchemy)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)  # Дата успешной оплаты

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    event = relationship("Event", foreign_keys=[event_id])


class PaymentHistory(Base):
    """История изменений статуса платежа"""
    __tablename__ = "payment_history"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    payment_id = Column(GUID(), ForeignKey("payments.id", ondelete="CASCADE"), nullable=False, index=True)
    old_status = Column(SQLEnum(PaymentStatus), nullable=True)
    new_status = Column(SQLEnum(PaymentStatus), nullable=False)
    comment = Column(Text, nullable=True)  # Комментарий к изменению
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    payment = relationship("Payment", foreign_keys=[payment_id])

