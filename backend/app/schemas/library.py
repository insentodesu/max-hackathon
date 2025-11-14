from pydantic import BaseModel, ConfigDict
import uuid


class LibraryAccessRead(BaseModel):
    """Схема для чтения информации о доступе к библиотеке"""
    id: uuid.UUID
    university_id: uuid.UUID
    login: str
    password: str
    portal_url: str
    instructions: str | None = None
    model_config = ConfigDict(from_attributes=True)


class LibraryAccessCreate(BaseModel):
    """Схема для создания информации о доступе"""
    university_id: uuid.UUID
    login: str
    password: str
    portal_url: str
    instructions: str | None = None


class LibraryAccessUpdate(BaseModel):
    """Схема для обновления информации о доступе"""
    login: str | None = None
    password: str | None = None
    portal_url: str | None = None
    instructions: str | None = None

