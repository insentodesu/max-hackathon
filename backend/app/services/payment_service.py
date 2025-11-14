"""
Модуль 5: Оплата услуг

Примечание: Push-уведомления о статусе платежей обрабатываются ботом мессенджера MAX.
Backend обрабатывает платежи через ЮКассу (webhook) и меняет статусы.
Бот отслеживает изменения статусов через API и отправляет push-уведомления пользователям.
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime
import uuid
import json
from datetime import timezone
# import requests  # Раскомментировать для реальной интеграции с ЮКассой

from app.models.payment import Payment, PaymentHistory, PaymentType, PaymentStatus
from app.models.event import Event
from app.schemas.payment import PaymentCreate, PaymentInitiate
from app.core.config import settings


def get_payment_by_id(db: Session, payment_id: uuid.UUID) -> Optional[Payment]:
    """Получить платеж по ID"""
    return db.query(Payment).filter(Payment.id == payment_id).first()


def get_user_payments(db: Session, user_id: uuid.UUID) -> List[Payment]:
    """Получить все платежи пользователя"""
    return db.query(Payment).filter(Payment.user_id == user_id).order_by(Payment.created_at.desc()).all()


def get_payment_by_yookassa_id(db: Session, yookassa_payment_id: str) -> Optional[Payment]:
    """Получить платеж по ID из ЮКассы"""
    return db.query(Payment).filter(Payment.yookassa_payment_id == yookassa_payment_id).first()


def create_payment(db: Session, *, payment_data: PaymentCreate, user_id: uuid.UUID) -> Payment:
    """Создать новый платеж"""
    # Валидация в зависимости от типа платежа
    if payment_data.payment_type == PaymentType.EVENT:
        # Для оплаты мероприятия event_id обязателен
        if not payment_data.event_id:
            raise ValueError("Для оплаты мероприятия необходимо указать event_id")
        
        event = db.query(Event).filter(Event.id == payment_data.event_id).first()
        if not event:
            raise ValueError("Мероприятие не найдено")
        if event.event_type.value != "paid":
            raise ValueError("Мероприятие не является платным")
        if event.price and payment_data.amount != event.price:
            raise ValueError(f"Сумма должна быть {event.price} копеек")
    else:
        # Для оплаты обучения или общежития event_id должен быть None
        if payment_data.event_id:
            raise ValueError(f"Для типа платежа {payment_data.payment_type.value} поле event_id не должно быть указано")
        
        # Для обучения и общежития желательно указать период и описание
        if not payment_data.period:
            raise ValueError(f"Для типа платежа {payment_data.payment_type.value} необходимо указать период оплаты")
        if not payment_data.description:
            raise ValueError(f"Для типа платежа {payment_data.payment_type.value} необходимо указать описание")
    
    payment = Payment(
        user_id=user_id,
        payment_type=payment_data.payment_type,
        amount=payment_data.amount,
        period=payment_data.period,
        description=payment_data.description,
        event_id=payment_data.event_id if payment_data.payment_type == PaymentType.EVENT else None,
        status=PaymentStatus.PENDING,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    
    # Создаем запись в истории
    _add_payment_history(db, payment.id, None, PaymentStatus.PENDING, "Платеж создан")
    
    return payment


def initiate_yookassa_payment(
    db: Session,
    *,
    payment_id: uuid.UUID,
    return_url: str
) -> Payment:
    """Инициировать платеж через ЮКассу"""
    payment = get_payment_by_id(db, payment_id)
    if not payment:
        raise ValueError("Платеж не найден")
    
    if payment.status != PaymentStatus.PENDING:
        raise ValueError("Платеж уже обработан")
    
    # Здесь должна быть реальная интеграция с ЮКассой
    # Для MVP используем заглушку
    
    # В реальной интеграции:
    # 1. Получаем shop_id и secret_key из настроек
    # 2. Формируем запрос к API ЮКассы
    # 3. Получаем confirmation_url и payment_id
    
    # Заглушка для MVP:
    yookassa_payment_id = f"yookassa_{uuid.uuid4()}"
    confirmation_url = f"https://yookassa.ru/checkout/payments/{yookassa_payment_id}"
    
    # В реальной интеграции:
    # import base64
    # auth = base64.b64encode(f"{settings.yookassa_shop_id}:{settings.yookassa_secret_key}".encode()).decode()
    # headers = {
    #     "Authorization": f"Basic {auth}",
    #     "Content-Type": "application/json"
    # }
    # data = {
    #     "amount": {
    #         "value": f"{payment.amount / 100:.2f}",
    #         "currency": "RUB"
    #     },
    #     "confirmation": {
    #         "type": "redirect",
    #         "return_url": return_url
    #     },
    #     "description": payment.description or f"Оплата {payment.payment_type.value}",
    #     "metadata": {
    #         "payment_id": str(payment.id),
    #         "user_id": str(payment.user_id)
    #     }
    # }
    # response = requests.post("https://api.yookassa.ru/v3/payments", headers=headers, json=data)
    # result = response.json()
    # yookassa_payment_id = result["id"]
    # confirmation_url = result["confirmation"]["confirmation_url"]
    
    payment.yookassa_payment_id = yookassa_payment_id
    payment.yookassa_confirmation_url = confirmation_url
    payment.status = PaymentStatus.PROCESSING
    db.commit()
    db.refresh(payment)
    
    _add_payment_history(db, payment.id, PaymentStatus.PENDING, PaymentStatus.PROCESSING, "Платеж инициирован в ЮКассе")
    
    return payment


def process_yookassa_webhook(db: Session, *, webhook_data: dict) -> Optional[Payment]:
    """Обработать webhook от ЮКассы"""
    event_type = webhook_data.get("event")
    payment_data = webhook_data.get("object", {})
    
    yookassa_payment_id = payment_data.get("id")
    if not yookassa_payment_id:
        return None
    
    payment = get_payment_by_yookassa_id(db, yookassa_payment_id)
    if not payment:
        return None
    
    old_status = payment.status
    
    # Обрабатываем статусы от ЮКассы
    if event_type == "payment.succeeded":
        payment.status = PaymentStatus.SUCCESS
        payment.paid_at = datetime.now(timezone.utc)
        _add_payment_history(db, payment.id, old_status, PaymentStatus.SUCCESS, "Платеж успешно завершен")
        
        # Если это оплата мероприятия, автоматически регистрируем пользователя
        if payment.event_id and payment.payment_type == PaymentType.EVENT:
            from app.services.event_service import register_for_event
            try:
                register_for_event(db, event_id=payment.event_id, user_id=payment.user_id)
            except Exception as e:
                # Логируем ошибку, но не прерываем процесс
                pass
        
    elif event_type == "payment.canceled":
        payment.status = PaymentStatus.CANCELLED
        _add_payment_history(db, payment.id, old_status, PaymentStatus.CANCELLED, "Платеж отменен")
    elif event_type == "payment.waiting_for_capture":
        # Платеж ожидает подтверждения
        payment.status = PaymentStatus.PROCESSING
        _add_payment_history(db, payment.id, old_status, PaymentStatus.PROCESSING, "Платеж ожидает подтверждения")
    else:
        # Другие статусы
        return payment
    
    db.commit()
    db.refresh(payment)
    return payment


def cancel_payment(db: Session, *, payment_id: uuid.UUID) -> Payment:
    """Отменить платеж"""
    payment = get_payment_by_id(db, payment_id)
    if not payment:
        raise ValueError("Платеж не найден")
    
    if payment.status in [PaymentStatus.SUCCESS, PaymentStatus.CANCELLED, PaymentStatus.REFUNDED]:
        raise ValueError("Невозможно отменить платеж в текущем статусе")
    
    old_status = payment.status
    payment.status = PaymentStatus.CANCELLED
    db.commit()
    db.refresh(payment)
    
    _add_payment_history(db, payment.id, old_status, PaymentStatus.CANCELLED, "Платеж отменен пользователем")
    
    return payment


def get_payment_history(db: Session, payment_id: uuid.UUID) -> List[PaymentHistory]:
    """Получить историю платежа"""
    return db.query(PaymentHistory).filter(
        PaymentHistory.payment_id == payment_id
    ).order_by(PaymentHistory.created_at.asc()).all()


def _add_payment_history(
    db: Session,
    payment_id: uuid.UUID,
    old_status: Optional[PaymentStatus],
    new_status: PaymentStatus,
    comment: Optional[str] = None
):
    """Добавить запись в историю платежа"""
    history = PaymentHistory(
        payment_id=payment_id,
        old_status=old_status,
        new_status=new_status,
        comment=comment,
    )
    db.add(history)
    db.commit()


def get_user_balance_info(db: Session, user_id: uuid.UUID) -> dict:
    """Получить информацию о балансе пользователя (суммы к оплате)"""
    # Получаем все неоплаченные платежи
    pending_payments = db.query(Payment).filter(
        and_(
            Payment.user_id == user_id,
            Payment.status.in_([PaymentStatus.PENDING, PaymentStatus.PROCESSING])
        )
    ).all()
    
    tuition_amount = 0
    dormitory_amount = 0
    
    for payment in pending_payments:
        if payment.payment_type == PaymentType.TUITION:
            tuition_amount += payment.amount
        elif payment.payment_type == PaymentType.DORMITORY:
            dormitory_amount += payment.amount
    
    return {
        "tuition_amount": tuition_amount,  # В копейках
        "dormitory_amount": dormitory_amount,  # В копейках
        "total_amount": tuition_amount + dormitory_amount,
    }

