from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
import uuid


class ElectiveBase(BaseModel):
    title: str
    description: Optional[str] = None
    teacher_user_id: uuid.UUID
    max_students: int = 30
    schedule_info: Optional[str] = None
    credits: Optional[int] = None


class ElectiveCreate(ElectiveBase):
    """Схема для создания электива"""
    pass


class ElectiveUpdate(BaseModel):
    """Схема для обновления электива"""
    title: Optional[str] = None
    description: Optional[str] = None
    max_students: Optional[int] = None
    schedule_info: Optional[str] = None
    credits: Optional[int] = None
    is_active: Optional[int] = None


class ElectiveRead(ElectiveBase):
    """Схема для чтения электива"""
    id: uuid.UUID
    current_students: int
    is_active: int
    created_at: datetime
    updated_at: datetime
    teacher_full_name: Optional[str] = None
    is_registered: bool = False  # Записан ли текущий пользователь
    model_config = ConfigDict(from_attributes=True)


class ElectiveRegistrationRead(BaseModel):
    """Схема для чтения записи на электив"""
    id: uuid.UUID
    elective_id: uuid.UUID
    user_id: uuid.UUID
    registered_at: datetime
    model_config = ConfigDict(from_attributes=True)

