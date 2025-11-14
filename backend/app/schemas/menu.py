from pydantic import BaseModel
from typing import List, Optional


class MenuItem(BaseModel):
    """Элемент меню"""
    id: str  # Уникальный идентификатор пункта меню
    title: str  # Название пункта меню
    icon: Optional[str] = None  # Иконка (опционально)
    route: Optional[str] = None  # Маршрут/ссылка (опционально)
    children: Optional[List["MenuItem"]] = None  # Подменю (опционально)


class MenuResponse(BaseModel):
    """Ответ с главным меню"""
    items: List[MenuItem]  # Список пунктов меню


# Для рекурсивных моделей
MenuItem.model_rebuild()

