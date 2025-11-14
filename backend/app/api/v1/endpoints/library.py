"""
Модуль 6: Электронная библиотека
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.library import LibraryAccessRead, LibraryAccessCreate, LibraryAccessUpdate
from app.services.library_service import (
    get_library_access_for_user,
    get_library_access_by_university,
    create_library_access,
    update_library_access,
)
from app.api.deps import get_current_active_user, get_current_admin

router = APIRouter()


@router.get(
    "/access",
    response_model=LibraryAccessRead,
    summary="Гид по доступу к библиотеке",
    description="Получить информацию о доступе к электронной библиотеке (логин, пароль, ссылка на портал, инструкция)",
)
def get_library_access(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> LibraryAccessRead:
    """
    Модуль 6: Получить гайд по доступу к электронной библиотеке
    
    Доступно только для студентов.
    Возвращает логин, пароль, ссылку на портал и пошаговую инструкцию.
    """
    # Проверяем, что пользователь - студент
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ к библиотеке доступен только для студентов"
        )
    
    library_access = get_library_access_for_user(db, current_user.id)
    
    if not library_access:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Информация о доступе к библиотеке не найдена. Обратитесь в администрацию вашего вуза."
        )
    
    return LibraryAccessRead.model_validate(library_access)


@router.post(
    "/access",
    response_model=LibraryAccessRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать информацию о доступе к библиотеке",
    description="Создать информацию о доступе к библиотеке для университета (только для админов)",
)
def create_library_access_endpoint(
    access_data: LibraryAccessCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> LibraryAccessRead:
    """Создать информацию о доступе к библиотеке (только для админов)"""
    # Проверяем, не существует ли уже информация для этого университета
    existing = get_library_access_by_university(db, access_data.university_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Информация о доступе для этого университета уже существует. Используйте PUT для обновления."
        )
    
    library_access = create_library_access(db, access_data=access_data)
    return LibraryAccessRead.model_validate(library_access)


@router.put(
    "/access/{access_id}",
    response_model=LibraryAccessRead,
    summary="Обновить информацию о доступе к библиотеке",
    description="Обновить информацию о доступе к библиотеке (только для админов)",
)
def update_library_access_endpoint(
    access_id: uuid.UUID,
    access_data: LibraryAccessUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> LibraryAccessRead:
    """Обновить информацию о доступе к библиотеке (только для админов)"""
    library_access = update_library_access(db, access_id=access_id, access_data=access_data)
    if not library_access:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Информация о доступе не найдена"
        )
    
    return LibraryAccessRead.model_validate(library_access)

