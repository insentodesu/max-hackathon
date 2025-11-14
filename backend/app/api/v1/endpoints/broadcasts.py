"""
Работа с рассылками для пользователей.
"""
import logging
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.config import settings
from app.db.session import get_db
from app.models.student import Student
from app.models.user import User, UserRole
from app.schemas.broadcast import BroadcastCreate, BroadcastRead
from app.services import bot_notify_service
from app.services.broadcast_service import (
    create_broadcast,
    get_broadcast_by_id,
    get_broadcasts_for_group,
    get_broadcasts_for_user,
    get_teacher_broadcasts,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", response_model=List[BroadcastRead], summary="Получить рассылки")
def get_broadcasts(
    group_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[BroadcastRead]:
    """
    Возвращает рассылки, доступные пользователю.

    - Для студента без параметров выводим его персональные сообщения.
    - Если указан `group_id`, берём рассылки только этой группы.
    - Для сотрудников/админов без фильтра возвращаем пустой список (для них есть отдельный `/my`).
    """
    if group_id:
        broadcasts = get_broadcasts_for_group(db, group_id)
    elif current_user.role == UserRole.STUDENT:
        broadcasts = get_broadcasts_for_user(db, current_user.id)
    else:
        broadcasts = []

    result = []
    for broadcast in broadcasts:
        payload = BroadcastRead.model_validate(broadcast).model_dump()
        if broadcast.author:
            payload["author_full_name"] = broadcast.author.full_name
        if broadcast.group:
            payload["group_name"] = broadcast.group.name
        if broadcast.faculty:
            payload["faculty_name"] = broadcast.faculty.name
        result.append(BroadcastRead(**payload))
    return result


@router.get("/my", response_model=List[BroadcastRead], summary="Мои рассылки (для преподавателей)")
def get_my_broadcasts(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[BroadcastRead]:
    """Возвращает рассылки, созданные текущим преподавателем/администратором."""
    if current_user.role not in [UserRole.STAFF, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для просмотра списка рассылок",
        )

    broadcasts = get_teacher_broadcasts(db, current_user.id)
    result = []
    for broadcast in broadcasts:
        payload = BroadcastRead.model_validate(broadcast).model_dump()
        if broadcast.author:
            payload["author_full_name"] = broadcast.author.full_name
        if broadcast.group:
            payload["group_name"] = broadcast.group.name
        if broadcast.faculty:
            payload["faculty_name"] = broadcast.faculty.name
        result.append(BroadcastRead(**payload))
    return result


@router.get("/{broadcast_id}", response_model=BroadcastRead, summary="Получить рассылку по ID")
def get_broadcast_details(
    broadcast_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> BroadcastRead:
    """Возвращает полное описание выбранной рассылки."""
    broadcast = get_broadcast_by_id(db, broadcast_id)
    if not broadcast:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Рассылка не найдена")

    payload = BroadcastRead.model_validate(broadcast).model_dump()
    if broadcast.author:
        payload["author_full_name"] = broadcast.author.full_name
    if broadcast.group:
        payload["group_name"] = broadcast.group.name
    if broadcast.faculty:
        payload["faculty_name"] = broadcast.faculty.name
    return BroadcastRead(**payload)


@router.post("", response_model=BroadcastRead, status_code=status.HTTP_201_CREATED, summary="Создать рассылку")
def create_broadcast_endpoint(
    broadcast_data: BroadcastCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> BroadcastRead:
    """
    Создаёт новую рассылку (доступно сотрудникам/админам) и сразу отправляет её через чат-бота.
    """
    try:
        broadcast = create_broadcast(db, broadcast_data=broadcast_data, author_user_id=current_user.id)
        _push_broadcast_to_bot(db, broadcast, current_user)

        payload = BroadcastRead.model_validate(broadcast).model_dump()
        if broadcast.author:
            payload["author_full_name"] = broadcast.author.full_name
        if broadcast.group:
            payload["group_name"] = broadcast.group.name
        if broadcast.faculty:
            payload["faculty_name"] = broadcast.faculty.name
        return BroadcastRead(**payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


def _push_broadcast_to_bot(db: Session, broadcast, author: User) -> None:
    try:
        recipients = _collect_recipient_max_ids(db, broadcast.group_id, broadcast.faculty_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning("failed to collect broadcast recipients: %s", exc)
        return

    if not recipients:
        logger.info("broadcast %s has no recipients with max_id", broadcast.id)
        return

    sender_id = author.max_id or settings.bot_default_sender_max_id
    if sender_id <= 0:
        sender_id = settings.bot_default_sender_max_id

    text = _format_broadcast_text(broadcast)
    try:
        delivered = bot_notify_service.notify_bulk(sender_id, recipients, text)
        logger.info("broadcast %s delivered to %d users via bot", broadcast.id, delivered)
    except bot_notify_service.BotNotifyError as exc:
        logger.warning("failed to push broadcast %s to bot: %s", broadcast.id, exc)


def _collect_recipient_max_ids(
    db: Session,
    group_id: uuid.UUID | None,
    faculty_id: uuid.UUID | None,
) -> list[int]:
    stmt = select(User.max_id).join(Student, Student.user_id == User.id)
    if group_id:
        stmt = stmt.filter(Student.group_id == group_id)
    elif faculty_id:
        stmt = stmt.filter(Student.faculty_id == faculty_id)
    stmt = stmt.filter(User.max_id.is_not(None))

    rows = db.execute(stmt).all()
    ids = [row[0] for row in rows if row[0]]
    seen: set[int] = set()
    unique: list[int] = []
    for value in ids:
        if value in seen:
            continue
        seen.add(value)
        unique.append(value)
    return unique


def _format_broadcast_text(broadcast) -> str:
    author = getattr(broadcast, "author", None)
    author_name = author.full_name if author else "Администрация"
    title = (broadcast.title or "").strip()
    body = (broadcast.message or "").strip()

    parts = [f"📢 Сообщение от {author_name}"]
    if title:
        parts.append(f"Тема: {title}")
    if body:
        parts.append("")
        parts.append(body)
    return "\n".join(parts).strip()
