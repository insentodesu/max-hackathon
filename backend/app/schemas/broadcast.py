from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
import uuid


class BroadcastBase(BaseModel):
    title: str
    message: str
    group_id: Optional[uuid.UUID] = None  # Если указан - для конкретной группы
    faculty_id: Optional[uuid.UUID] = None  # Если указан - для всех групп факультета/потока


class BroadcastCreate(BroadcastBase):
    """Схема для создания рассылки"""
    pass


class BroadcastRead(BroadcastBase):
    """Схема для чтения рассылки"""
    id: uuid.UUID
    author_user_id: uuid.UUID
    created_at: datetime
    author_full_name: Optional[str] = None
    group_name: Optional[str] = None
    faculty_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

