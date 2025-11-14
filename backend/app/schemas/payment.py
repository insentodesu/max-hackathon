from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import List, Literal, Optional
import uuid

from app.models.payment import PaymentType, PaymentStatus


class PaymentBase(BaseModel):
    payment_type: PaymentType
    amount: int  # Сумма в копейках
    period: Optional[str] = None  # Период оплаты (обязательно для обучения/общежития)
    description: Optional[str] = None  # Описание платежа (обязательно для обучения/общежития)


class PaymentCreate(PaymentBase):
    """Схема для создания платежа
    
    Правила валидации:
    - Для EVENT: event_id обязателен, period и description не нужны
    - Для TUITION/DORMITORY: event_id должен быть None, period и description обязательны
    """
    event_id: Optional[uuid.UUID] = None  # Обязателен только для оплаты мероприятия (EVENT)


class PaymentRead(PaymentBase):
    """Схема для чтения платежа"""
    id: uuid.UUID
    user_id: uuid.UUID
    status: PaymentStatus
    event_id: Optional[uuid.UUID] = None
    yookassa_payment_id: Optional[str] = None
    yookassa_confirmation_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    paid_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class PaymentHistoryRead(BaseModel):
    """Схема для чтения истории платежа"""
    id: uuid.UUID
    payment_id: uuid.UUID
    old_status: Optional[PaymentStatus] = None
    new_status: PaymentStatus
    comment: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PaymentDetailRead(PaymentRead):
    """Детальная информация о платеже с историей"""
    history: List[PaymentHistoryRead] = []


class PaymentInitiate(BaseModel):
    """Схема для инициации платежа через ЮКассу
    
    Правила валидации:
    - Для EVENT: event_id обязателен, period и description не нужны
    - Для TUITION/DORMITORY: event_id должен быть None, period и description обязательны
    """
    payment_type: PaymentType
    amount: int
    period: Optional[str] = None  # Обязательно для TUITION/DORMITORY
    description: Optional[str] = None  # Обязательно для TUITION/DORMITORY
    event_id: Optional[uuid.UUID] = None  # Обязателен только для EVENT


class PaymentWebhook(BaseModel):
    """Схема для webhook от ЮКассы"""
    type: Optional[str] = None
    event: str
    object: dict  # Данные платежа от ЮКассы


class PaymentLinkRequest(BaseModel):
    """????? ??? ??????? ?????? ?? ?????? ??? MAX-ID"""
    user_id: int  # MAX ID ????????????
    kind: Literal["dorm", "tuition"]


class PaymentLinkResponse(BaseModel):
    """????? ??? ?????? ?? ??????"""
    url: str
    payment_id: uuid.UUID
