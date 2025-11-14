from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.payment import PaymentType
from app.schemas.payment import (
    PaymentCreate, PaymentRead, PaymentDetailRead,
    PaymentInitiate, PaymentWebhook, PaymentHistoryRead,
    PaymentLinkRequest, PaymentLinkResponse,
)
from app.services.payment_service import (
    get_payment_by_id,
    get_user_payments,
    create_payment,
    initiate_yookassa_payment,
    process_yookassa_webhook,
    cancel_payment,
    get_payment_history,
    get_user_balance_info,
)
from app.api.deps import get_current_active_user, get_current_admin
from app.core.config import settings
from app.services import bot_notify_service

router = APIRouter()


@router.get("/balance", summary="Просмотр баланса")
def get_balance(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> dict:
    """Получить информацию о балансе (суммы к оплате за обучение и общежитие)"""
    balance_info = get_user_balance_info(db, current_user.id)
    return {
        "tuition_amount": balance_info["tuition_amount"],
        "dormitory_amount": balance_info["dormitory_amount"],
        "total_amount": balance_info["total_amount"],
        "tuition_amount_rub": balance_info["tuition_amount"] / 100,
        "dormitory_amount_rub": balance_info["dormitory_amount"] / 100,
        "total_amount_rub": balance_info["total_amount"] / 100,
    }




@router.get("/status", summary="Статус задолженностей по оплате")
def get_payment_status(
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
) -> dict:
    """Вернуть необходимость оплат по MAX-ID"""
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id is required",
        )

    user = db.query(User).filter(User.max_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    balance_info = get_user_balance_info(db, user.id)
    return {
        "need_dorm": balance_info.get("dormitory_amount", 0) > 0,
        "need_tuition": balance_info.get("tuition_amount", 0) > 0,
    }

@router.get("", response_model=List[PaymentRead], summary="История платежей")
def get_my_payments(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[PaymentRead]:
    """Получить историю всех платежей пользователя"""
    payments = get_user_payments(db, current_user.id)
    return [PaymentRead.model_validate(payment) for payment in payments]


@router.get("/{payment_id}", response_model=PaymentDetailRead, summary="Детали платежа")
def get_payment_details(
    payment_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> PaymentDetailRead:
    """Получить детальную информацию о платеже"""
    payment = get_payment_by_id(db, payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Платеж не найден")
    
    # Проверяем, что платеж принадлежит пользователю
    if payment.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этому платежу")
    
    history = get_payment_history(db, payment_id)
    
    payment_dict = PaymentRead.model_validate(payment).model_dump()
    return PaymentDetailRead(
        **payment_dict,
        history=[PaymentHistoryRead.model_validate(h) for h in history]
    )


@router.post("", response_model=PaymentRead, status_code=status.HTTP_201_CREATED, summary="Создать платеж")
def create_payment_endpoint(
    payment_data: PaymentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> PaymentRead:
    """Создать новый платеж"""
    try:
        payment = create_payment(db, payment_data=payment_data, user_id=current_user.id)
        return PaymentRead.model_validate(payment)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))




@router.post(
    "/link",
    response_model=PaymentLinkResponse,
    summary="Создать ссылку на оплату для MAX-ID",
)
def generate_payment_link(
    payload: PaymentLinkRequest,
    db: Session = Depends(get_db),
) -> PaymentLinkResponse:
    """Генерирует ссылку на оплату для пользователя по MAX-ID (используется ботом)."""
    user = db.query(User).filter(User.max_id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь с таким MAX-ID не найден")

    kind_map = {
        "dorm": (
            PaymentType.DORMITORY,
            "Оплата проживания в общежитии",
            "Период проживания",
        ),
        "tuition": (
            PaymentType.TUITION,
            "Оплата обучения",
            "Период обучения",
        ),
    }
    kind_meta = kind_map.get(payload.kind)
    if not kind_meta:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Некорректный тип платежа")

    payment_type, description, period_title = kind_meta
    balance_info = get_user_balance_info(db, user.id)
    amount_lookup = {
        "dorm": balance_info.get("dormitory_amount", 0),
        "tuition": balance_info.get("tuition_amount", 0),
    }
    amount = amount_lookup.get(payload.kind, 0)
    if amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Нет начислений по этому платежу")

    payment_create = PaymentCreate(
        payment_type=payment_type,
        amount=amount,
        period=period_title,
        description=description,
    )

    try:
        payment = create_payment(db, payment_data=payment_create, user_id=user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return_url = f"{settings.api_v1_prefix}/payments/{payment.id}/success"
    try:
        payment = initiate_yookassa_payment(db, payment_id=payment.id, return_url=return_url)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    if not payment.yookassa_confirmation_url:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Не удалось получить ссылку на оплату")

    return PaymentLinkResponse(
        url=payment.yookassa_confirmation_url,
        payment_id=payment.id,
    )

@router.post("/initiate", response_model=PaymentRead, summary="Инициировать платеж через ЮКассу")
def initiate_payment(
    payment_data: PaymentInitiate,
    return_url: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> PaymentRead:
    """Инициировать платеж через ЮКассу (создает платеж и возвращает ссылку для оплаты)"""
    # Создаем платеж
    payment_create = PaymentCreate(
        payment_type=payment_data.payment_type,
        amount=payment_data.amount,
        period=payment_data.period,
        description=payment_data.description,
        event_id=payment_data.event_id,
    )
    
    try:
        payment = create_payment(db, payment_data=payment_create, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    # Инициируем платеж в ЮКассе
    default_return_url = f"{settings.api_v1_prefix}/payments/{payment.id}/success"
    return_url = return_url or default_return_url
    
    try:
        payment = initiate_yookassa_payment(db, payment_id=payment.id, return_url=return_url)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    return PaymentRead.model_validate(payment)


@router.post("/webhook", status_code=status.HTTP_200_OK, summary="Webhook от ЮКассы")
def yookassa_webhook(
    webhook_data: PaymentWebhook,
    db: Session = Depends(get_db)
):
    """Обработка webhook от ЮКассы (для обновления статусов платежей)"""
    try:
        payment = process_yookassa_webhook(db, webhook_data=webhook_data.model_dump())
        if payment:
            return {"status": "ok", "payment_id": str(payment.id)}
        return {"status": "ok", "message": "Payment not found"}
    except Exception as e:
        # Логируем ошибку, но возвращаем 200, чтобы ЮКасса не повторяла запрос
        return {"status": "error", "message": str(e)}


@router.post("/{payment_id}/cancel", response_model=PaymentRead, summary="Отменить платеж")
def cancel_payment_endpoint(
    payment_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> PaymentRead:
    """Отменить платеж"""
    payment = get_payment_by_id(db, payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Платеж не найден")
    
    # Проверяем, что платеж принадлежит пользователю
    if payment.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этому платежу")
    
    try:
        payment = cancel_payment(db, payment_id=payment_id)
        return PaymentRead.model_validate(payment)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{payment_id}/success", summary="Страница успешной оплаты")
def payment_success(
    payment_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Страница успешной оплаты (редирект от ЮКассы)"""
    payment = get_payment_by_id(db, payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Платеж не найден")
    
    return {
        "status": "success",
        "message": "Платеж успешно обработан",
        "payment_id": str(payment.id),
        "payment_status": payment.status.value,
    }


@router.post("/tuition/remind/{max_id}", summary="Отправить напоминание об оплате", status_code=status.HTTP_200_OK)
def remind_tuition_payment(
    max_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Администратор вручную напоминает студенту об оплате и инициирует пуш в чат‑боте"""
    user = db.query(User).filter(User.max_id == max_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Пользователь с max_id={max_id} не найден")

    try:
        bot_notify_service.notify_tuition_reminder(max_id)
    except bot_notify_service.BotNotifyError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    return {"status": "sent", "user_id": str(user.id), "max_id": max_id}
