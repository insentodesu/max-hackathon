"""
Элективы (факультативные курсы)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.elective import (
    ElectiveCreate, ElectiveUpdate, ElectiveRead, ElectiveRegistrationRead
)
from app.services.elective_service import (
    get_elective_by_id,
    get_all_electives,
    get_user_electives,
    create_elective,
    update_elective,
    register_for_elective,
    unregister_from_elective,
    is_user_registered,
)
from app.api.deps import get_current_active_user, get_current_admin, get_optional_current_user

router = APIRouter()


@router.get("", response_model=List[ElectiveRead], summary="Список элективов")
def get_electives_list(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
) -> List[ElectiveRead]:
    """Получить список всех доступных элективов"""
    electives = get_all_electives(db, skip=skip, limit=limit, active_only=active_only)
    
    result = []
    for elective in electives:
        elective_dict = ElectiveRead.model_validate(elective).model_dump()
        
        # Добавляем имя преподавателя
        if elective.teacher:
            elective_dict["teacher_full_name"] = elective.teacher.full_name
        
        # Проверяем, записан ли пользователь (если авторизован)
        if current_user:
            elective_dict["is_registered"] = is_user_registered(
                db, elective_id=elective.id, user_id=current_user.id
            )
        else:
            elective_dict["is_registered"] = False
        
        result.append(ElectiveRead(**elective_dict))
    
    return result


@router.get("/my", response_model=List[ElectiveRead], summary="Мои элективы")
def get_my_electives(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[ElectiveRead]:
    """Получить элективы, на которые записан пользователь"""
    electives = get_user_electives(db, current_user.id)
    
    result = []
    for elective in electives:
        elective_dict = ElectiveRead.model_validate(elective).model_dump()
        elective_dict["is_registered"] = True  # Всегда True для "Мои элективы"
        
        # Добавляем имя преподавателя
        if elective.teacher:
            elective_dict["teacher_full_name"] = elective.teacher.full_name
        
        result.append(ElectiveRead(**elective_dict))
    
    return result


@router.get("/{elective_id}", response_model=ElectiveRead, summary="Детали электива")
def get_elective_details(
    elective_id: uuid.UUID,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
) -> ElectiveRead:
    """Получить детальную информацию об элективе"""
    elective = get_elective_by_id(db, elective_id)
    if not elective:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Электив не найден")
    
    elective_dict = ElectiveRead.model_validate(elective).model_dump()
    
    # Добавляем имя преподавателя
    if elective.teacher:
        elective_dict["teacher_full_name"] = elective.teacher.full_name
    
    # Проверяем, записан ли пользователь
    if current_user:
        elective_dict["is_registered"] = is_user_registered(
            db, elective_id=elective.id, user_id=current_user.id
        )
    else:
        elective_dict["is_registered"] = False
    
    return ElectiveRead(**elective_dict)


@router.post("", response_model=ElectiveRead, status_code=status.HTTP_201_CREATED, summary="Создать электив")
def create_elective_endpoint(
    elective_data: ElectiveCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> ElectiveRead:
    """Создать новый электив (только для админов)"""
    elective = create_elective(db, elective_data=elective_data)
    
    elective_dict = ElectiveRead.model_validate(elective).model_dump()
    elective_dict["is_registered"] = False
    
    # Добавляем имя преподавателя
    if elective.teacher:
        elective_dict["teacher_full_name"] = elective.teacher.full_name
    
    return ElectiveRead(**elective_dict)


@router.put("/{elective_id}", response_model=ElectiveRead, summary="Обновить электив")
def update_elective_endpoint(
    elective_id: uuid.UUID,
    elective_data: ElectiveUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> ElectiveRead:
    """Обновить электив (только для админов)"""
    elective = update_elective(db, elective_id=elective_id, elective_data=elective_data)
    if not elective:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Электив не найден")
    
    elective_dict = ElectiveRead.model_validate(elective).model_dump()
    elective_dict["is_registered"] = is_user_registered(
        db, elective_id=elective.id, user_id=current_user.id
    )
    
    # Добавляем имя преподавателя
    if elective.teacher:
        elective_dict["teacher_full_name"] = elective.teacher.full_name
    
    return ElectiveRead(**elective_dict)


@router.post("/{elective_id}/register", response_model=ElectiveRegistrationRead, summary="Записаться на электив")
def register_for_elective_endpoint(
    elective_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ElectiveRegistrationRead:
    """Записаться на электив (только для студентов)"""
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Запись на элективы доступна только для студентов"
        )
    
    try:
        registration = register_for_elective(db, elective_id=elective_id, user_id=current_user.id)
        return ElectiveRegistrationRead.model_validate(registration)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{elective_id}/register", status_code=status.HTTP_204_NO_CONTENT, summary="Отписаться от электива")
def unregister_from_elective_endpoint(
    elective_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Отписаться от электива"""
    try:
        unregister_from_elective(db, elective_id=elective_id, user_id=current_user.id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

