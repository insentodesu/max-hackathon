"""
Модуль 4: Система заявок и документов
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.db.session import get_db
from app.models.user import User
from app.models.request import Request, RequestType, RequestStatus
from app.schemas.request import (
    RequestCreate, RequestRead, RequestDetailRead,
    RequestApprove, RequestReject, RequestListRead,
    RequestDocumentRead, RequestApprovalStepRead
)
from app.models.request_approval_step import RequestApprovalStep
from app.services.request_service import (
    create_request,
    get_request_by_id,
    get_user_requests,
    get_requests_for_approval,
    approve_request,
    reject_request,
    add_request_document,
    get_request_documents,
    get_request_detail,
)
from app.services import bot_notify_service
from app.api.deps import get_current_active_user
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

READY_DOCUMENT_REQUEST_TYPES = {
    RequestType.STUDENT_CERTIFICATE,
    RequestType.DOCUMENT_APPROVAL,
}


@router.get(
    "/my",
    response_model=List[RequestListRead],
    summary="Мои заявки",
    description="Получить все заявки текущего пользователя",
)
def get_my_requests(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[RequestListRead]:
    """Получить все заявки пользователя (раздел 'Мои заявки')"""
    requests = get_user_requests(db, user_id=current_user.id)
    return [RequestListRead.model_validate(req) for req in requests]


@router.get(
    "/approval",
    response_model=List[RequestListRead],
    summary="Согласование заявок",
    description="Получить заявки, требующие согласования текущего пользователя",
)
def get_approval_requests(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[RequestListRead]:
    """Получить заявки на согласование (раздел 'Согласование заявок')"""
    requests = get_requests_for_approval(db, approver_user_id=current_user.id)
    return [RequestListRead.model_validate(req) for req in requests]


@router.get(
    "/{request_id}",
    response_model=RequestDetailRead,
    summary="Детали заявки",
    description="Получить детальную информацию о заявке",
)
def get_request_details(
    request_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> RequestDetailRead:
    """Получить детальную информацию о заявке"""
    request = get_request_detail(db, request_id, current_user.id)
    if not request:
        raise HTTPException(status_code=404, detail="Заявка не найдена или нет доступа")
    
    # Получаем документы и шаги согласования
    documents = get_request_documents(db, request_id)
    approval_steps = db.query(RequestApprovalStep).filter(
        RequestApprovalStep.request_id == request_id
    ).order_by(RequestApprovalStep.step_order).all()
    
    # Формируем ответ
    detail = RequestDetailRead.model_validate(request)
    # Добавляем URL для документов
    detail.documents = [
        RequestDocumentRead(
            **doc.__dict__,
            file_url=f"{settings.static_url.rstrip('/')}/{doc.file_path}"
        ) for doc in documents
    ]
    detail.approval_steps = [RequestApprovalStepRead.model_validate(step) for step in approval_steps]
    
    # Добавляем имена автора и согласующего
    if request.author:
        detail.author_full_name = request.author.full_name
    if request.current_approver:
        detail.current_approver_full_name = request.current_approver.full_name
    
    return detail


@router.post(
    "",
    response_model=RequestRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать заявку",
    description="Создать новую заявку",
)
def create_new_request(
    request_data: RequestCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> RequestRead:
    """Создать новую заявку"""
    try:
        request = create_request(
            db=db,
            request_data=request_data,
            author_user_id=current_user.id
        )
        _notify_document_ready_if_needed(request, current_user.max_id)
        return RequestRead.model_validate(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при создании заявки: {str(e)}")


@router.post(
    "/{request_id}/approve",
    response_model=RequestRead,
    summary="Одобрить заявку",
    description="Одобрить заявку (только для текущего согласующего)",
)
def approve_request_endpoint(
    request_id: int,
    approve_data: RequestApprove,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> RequestRead:
    """Одобрить заявку"""
    try:
        request = approve_request(
            db=db,
            request_id=request_id,
            approver_user_id=current_user.id,
            approve_data=approve_data
        )
        author_max_id = _get_user_max_id(db, request.author_user_id)
        _notify_document_ready_if_needed(request, author_max_id)
        return RequestRead.model_validate(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при одобрении заявки: {str(e)}")


@router.post(
    "/{request_id}/reject",
    response_model=RequestRead,
    summary="Отклонить заявку",
    description="Отклонить заявку с указанием причины (только для текущего согласующего)",
)
def reject_request_endpoint(
    request_id: int,
    reject_data: RequestReject,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> RequestRead:
    """Отклонить заявку"""
    try:
        request = reject_request(
            db=db,
            request_id=request_id,
            approver_user_id=current_user.id,
            reject_data=reject_data
        )
        return RequestRead.model_validate(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при отклонении заявки: {str(e)}")


@router.post(
    "/{request_id}/documents",
    response_model=RequestDocumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Загрузить документ",
    description="Загрузить документ к заявке",
)
async def upload_request_document(
    request_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> RequestDocumentRead:
    """Загрузить документ к заявке"""
    request = get_request_by_id(db, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    
    if request.author_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Вы можете загружать документы только к своим заявкам")
    
    try:
        file_content = await file.read()
        document = add_request_document(
            db=db,
            request_id=request_id,
            filename=file.filename or "document",
            file_content=file_content,
            mime_type=file.content_type
        )
        return RequestDocumentRead(
            **document.__dict__,
            file_url=f"{settings.static_url.rstrip('/')}/{document.file_path}"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при загрузке документа: {str(e)}")


@router.get(
    "/{request_id}/documents",
    response_model=List[RequestDocumentRead],
    summary="Получить документы заявки",
    description="Получить список всех документов заявки",
)
def get_request_documents_endpoint(
    request_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[RequestDocumentRead]:
    """Получить все документы заявки"""
    request = get_request_by_id(db, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    
    # Проверяем права доступа
    if request.author_user_id != current_user.id and request.current_approver_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этой заявке")
    
    documents = get_request_documents(db, request_id)
    return [
        RequestDocumentRead(
            **doc.__dict__,
            file_url=f"{settings.static_url.rstrip('/')}/{doc.file_path}"
        ) for doc in documents
    ]


def _notify_document_ready_if_needed(request: Request, user_max_id: Optional[int]) -> None:
    if request.request_type not in READY_DOCUMENT_REQUEST_TYPES:
        return
    if request.status != RequestStatus.APPROVED:
        return
    if not user_max_id or int(user_max_id) <= 0:
        return
    try:
        bot_notify_service.notify_document_ready(int(user_max_id))
    except bot_notify_service.BotNotifyError as exc:
        logger.warning(
            "failed to notify bot about ready document %s: %s",
            request.id,
            exc,
        )


def _get_user_max_id(db: Session, user_id: uuid.UUID) -> Optional[int]:
    if not user_id:
        return None
    user = db.get(User, user_id)
    if user and user.max_id:
        return user.max_id
    return None

