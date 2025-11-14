from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import json
from pathlib import Path

from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.event import EventCreate, EventUpdate, EventRead, EventRegistrationRead
from app.services.event_service import (
    get_event_by_id,
    get_all_events,
    get_user_events,
    create_event,
    update_event,
    register_for_event,
    unregister_from_event,
    is_user_registered,
)
from app.api.deps import get_current_active_user, get_current_admin, get_optional_current_user
from app.core.config import settings

router = APIRouter()


@router.get("", response_model=List[EventRead], summary="Лента событий")
def get_events_feed(
    skip: int = 0,
    limit: int = 100,
    upcoming_only: bool = True,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
) -> List[EventRead]:
    """Получить ленту всех мероприятий"""
    events = get_all_events(db, skip=skip, limit=limit, upcoming_only=upcoming_only)
    
    result = []
    for event in events:
        # Парсим topics из JSON перед валидацией
        topics_list = []
        if event.topics:
            try:
                topics_list = json.loads(event.topics)
            except:
                topics_list = []
        
        # Создаем словарь для валидации, исключая topics из модели
        event_data = {
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "date": event.date,
            "end_time": event.end_time,
            "event_type": event.event_type,
            "price": event.price,
            "format": event.format,
            "location": event.location,
            "max_participants": event.max_participants,
            "current_participants": event.current_participants,
            "image_url": event.image_url,
            "speaker_name": event.speaker_name,
            "speaker_bio": event.speaker_bio,
            "topics": topics_list,  # Уже распарсенный список
            "created_at": event.created_at,
            "updated_at": event.updated_at,
            "is_registered": False,
        }
        
        # Проверяем, записан ли пользователь
        if current_user:
            event_data["is_registered"] = is_user_registered(
                db, event_id=event.id, user_id=current_user.id
            )
        
        result.append(EventRead(**event_data))
    
    return result


@router.get("/my", response_model=List[EventRead], summary="Мои события")
def get_my_events(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[EventRead]:
    """Получить мероприятия, на которые записан пользователь"""
    events = get_user_events(db, current_user.id)
    
    result = []
    for event in events:
        # Парсим topics из JSON перед валидацией
        topics_list = []
        if event.topics:
            try:
                topics_list = json.loads(event.topics)
            except:
                topics_list = []
        
        # Создаем словарь для валидации
        event_data = {
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "date": event.date,
            "end_time": event.end_time,
            "event_type": event.event_type,
            "price": event.price,
            "format": event.format,
            "location": event.location,
            "max_participants": event.max_participants,
            "current_participants": event.current_participants,
            "image_url": event.image_url,
            "speaker_name": event.speaker_name,
            "speaker_bio": event.speaker_bio,
            "topics": topics_list,  # Уже распарсенный список
            "created_at": event.created_at,
            "updated_at": event.updated_at,
            "is_registered": True,  # Всегда True для "Мои события"
        }
        
        result.append(EventRead(**event_data))
    
    return result


@router.get("/{event_id}", response_model=EventRead, summary="Детали мероприятия")
def get_event_details(
    event_id: uuid.UUID,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
) -> EventRead:
    """Получить детальную информацию о мероприятии"""
    event = get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Мероприятие не найдено")
    
    # Парсим topics из JSON перед валидацией
    topics_list = []
    if event.topics:
        try:
            topics_list = json.loads(event.topics)
        except:
            topics_list = []
    
    # Создаем словарь для валидации
    event_data = {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "date": event.date,
        "end_time": event.end_time,
        "event_type": event.event_type,
        "price": event.price,
        "format": event.format,
        "location": event.location,
        "max_participants": event.max_participants,
        "current_participants": event.current_participants,
        "image_url": event.image_url,
        "speaker_name": event.speaker_name,
        "speaker_bio": event.speaker_bio,
        "topics": topics_list,  # Уже распарсенный список
        "created_at": event.created_at,
        "updated_at": event.updated_at,
        "is_registered": False,
    }
    
    # Проверяем, записан ли пользователь
    if current_user:
        event_data["is_registered"] = is_user_registered(
            db, event_id=event.id, user_id=current_user.id
        )
    
    return EventRead(**event_data)


@router.post("", response_model=EventRead, status_code=status.HTTP_201_CREATED, summary="Создать мероприятие")
def create_event_endpoint(
    event_data: EventCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> EventRead:
    """Создать новое мероприятие (только для админов)"""
    event = create_event(db, event_data=event_data)
    
    event_dict = EventRead.model_validate(event).model_dump()
    event_dict["is_registered"] = False
    
    # Парсим topics из JSON
    if event.topics:
        try:
            event_dict["topics"] = json.loads(event.topics)
        except:
            event_dict["topics"] = []
    else:
        event_dict["topics"] = []
    
    return EventRead(**event_dict)


@router.put("/{event_id}", response_model=EventRead, summary="Обновить мероприятие")
def update_event_endpoint(
    event_id: uuid.UUID,
    event_data: EventUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> EventRead:
    """Обновить мероприятие (только для админов)"""
    event = update_event(db, event_id=event_id, event_data=event_data)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Мероприятие не найдено")
    
    event_dict = EventRead.model_validate(event).model_dump()
    event_dict["is_registered"] = is_user_registered(
        db, event_id=event.id, user_id=current_user.id
    )
    
    # Парсим topics из JSON
    if event.topics:
        try:
            event_dict["topics"] = json.loads(event.topics)
        except:
            event_dict["topics"] = []
    else:
        event_dict["topics"] = []
    
    return EventRead(**event_dict)


@router.post("/{event_id}/register", response_model=EventRegistrationRead, summary="Записаться на мероприятие")
def register_for_event_endpoint(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> EventRegistrationRead:
    """Записаться на мероприятие"""
    try:
        registration = register_for_event(db, event_id=event_id, user_id=current_user.id)
        return EventRegistrationRead.model_validate(registration)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{event_id}/register", status_code=status.HTTP_204_NO_CONTENT, summary="Отписаться от мероприятия")
def unregister_from_event_endpoint(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Отписаться от мероприятия"""
    try:
        unregister_from_event(db, event_id=event_id, user_id=current_user.id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{event_id}/upload-image", summary="Загрузить фото мероприятия")
async def upload_event_image(
    event_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Загрузить фото для мероприятия (только для админов)"""
    event = get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Мероприятие не найдено")
    
    # Проверяем тип файла
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл должен быть изображением"
        )
    
    # Создаем директорию для фото мероприятий
    # Определяем абсолютный путь к static директории (относительно корня проекта)
    base_dir = Path(__file__).parent.parent.parent.parent.parent
    static_dir = base_dir / settings.static_root
    events_dir = static_dir / "events"
    events_dir.mkdir(parents=True, exist_ok=True)
    
    # Генерируем уникальное имя файла
    file_extension = Path(file.filename).suffix if file.filename else ".jpg"
    unique_filename = f"{event_id}_{uuid.uuid4()}{file_extension}"
    file_path = events_dir / unique_filename
    
    # Сохраняем файл
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Обновляем URL в базе данных
    relative_path = f"events/{unique_filename}"
    event.image_url = relative_path
    db.commit()
    db.refresh(event)
    
    return {
        "image_url": f"{settings.static_url.rstrip('/')}/{relative_path}",
        "message": "Фото успешно загружено"
    }

