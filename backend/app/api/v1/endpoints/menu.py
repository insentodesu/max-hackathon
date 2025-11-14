"""
Модуль 7: Главное меню и навигация
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.menu import MenuResponse
from app.services.menu_service import get_menu_for_role
from app.api.deps import get_current_active_user

router = APIRouter()


@router.get(
    "",
    response_model=MenuResponse,
    summary="Главное меню",
    description="Получить динамическое главное меню в зависимости от роли пользователя",
)
def get_main_menu(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> MenuResponse:
    """
    Модуль 7: Получить главное меню
    
    Возвращает динамическое меню в зависимости от роли:
    - Студент: Лента мероприятий, Элективы, ЛК (Библиотека, Помощь)
    - Преподаватель/Сотрудник: Лента мероприятий, Документооборот, ЛК (Помощь)
    - Админ: Все пункты + Админ-панель
    """
    menu = get_menu_for_role(current_user.role)
    return menu

