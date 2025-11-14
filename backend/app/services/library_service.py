from sqlalchemy.orm import Session
from typing import Optional
import uuid

from app.models.library import LibraryAccess
from app.models.user import User, UserRole
from app.schemas.library import LibraryAccessCreate, LibraryAccessUpdate


def get_library_access_for_user(db: Session, user_id: uuid.UUID) -> Optional[LibraryAccess]:
    """Получить информацию о доступе к библиотеке для пользователя"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    
    # Проверяем, что пользователь - студент
    if user.role != UserRole.STUDENT:
        return None
    
    # Получаем информацию о доступе для университета пользователя
    if not user.university_id:
        return None
    
    library_access = db.query(LibraryAccess).filter(
        LibraryAccess.university_id == user.university_id
    ).first()
    
    return library_access


def get_library_access_by_university(db: Session, university_id: uuid.UUID) -> Optional[LibraryAccess]:
    """Получить информацию о доступе к библиотеке по университету"""
    return db.query(LibraryAccess).filter(
        LibraryAccess.university_id == university_id
    ).first()


def create_library_access(db: Session, *, access_data: LibraryAccessCreate) -> LibraryAccess:
    """Создать информацию о доступе к библиотеке (для админов)"""
    library_access = LibraryAccess(
        university_id=access_data.university_id,
        login=access_data.login,
        password=access_data.password,
        portal_url=access_data.portal_url,
        instructions=access_data.instructions,
    )
    db.add(library_access)
    db.commit()
    db.refresh(library_access)
    return library_access


def update_library_access(
    db: Session,
    *,
    access_id: uuid.UUID,
    access_data: LibraryAccessUpdate
) -> Optional[LibraryAccess]:
    """Обновить информацию о доступе к библиотеке (для админов)"""
    library_access = db.query(LibraryAccess).filter(LibraryAccess.id == access_id).first()
    if not library_access:
        return None
    
    update_data = access_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(library_access, field):
            setattr(library_access, field, value)
    
    db.commit()
    db.refresh(library_access)
    return library_access

