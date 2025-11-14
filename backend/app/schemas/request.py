from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
import uuid

from app.models.request import RequestType, RequestStatus
from app.models.request_approval_step import ApprovalAction


class RequestBase(BaseModel):
    request_type: RequestType
    content: Optional[str] = None


class RequestCreate(RequestBase):
    """Схема для создания заявки"""
    pass


class RequestDocumentRead(BaseModel):
    """Схема для чтения документа заявки"""
    id: uuid.UUID
    filename: str
    file_path: str
    file_url: Optional[str] = None  # URL для доступа к файлу
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    uploaded_at: datetime
    model_config = ConfigDict(from_attributes=True)


class RequestApprovalStepRead(BaseModel):
    """Схема для чтения шага согласования"""
    id: uuid.UUID
    step_order: int
    approver_user_id: Optional[uuid.UUID] = None
    approver_role: Optional[str] = None
    action: ApprovalAction
    comment: Optional[str] = None
    processed_at: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class RequestRead(BaseModel):
    """Схема для чтения заявки"""
    id: int
    request_type: RequestType
    author_user_id: uuid.UUID
    status: RequestStatus
    content: Optional[str] = None
    rejection_reason: Optional[str] = None
    current_approver_id: Optional[uuid.UUID] = None
    approval_road_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class RequestDetailRead(RequestRead):
    """Детальная схема заявки с дополнительной информацией"""
    documents: List[RequestDocumentRead] = []
    approval_steps: List[RequestApprovalStepRead] = []
    author_full_name: Optional[str] = None
    current_approver_full_name: Optional[str] = None


class RequestApprove(BaseModel):
    """Схема для одобрения заявки"""
    comment: Optional[str] = None


class RequestReject(BaseModel):
    """Схема для отклонения заявки"""
    reason: str  # Обязательная причина отклонения


class RequestListRead(BaseModel):
    """Схема для списка заявок (краткая информация)"""
    id: int
    request_type: RequestType
    status: RequestStatus
    created_at: datetime
    content: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

