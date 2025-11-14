from datetime import date, time, datetime
from pydantic import BaseModel, ConfigDict
import uuid


class TimeslotBase(BaseModel):
    pair_no: int
    start: time
    end: time


class TimeslotRead(TimeslotBase):
    model_config = ConfigDict(from_attributes=True)


class LessonBase(BaseModel):
    teacher_user_id: uuid.UUID
    room_id: uuid.UUID
    subject_id: uuid.UUID
    pair_no: int
    group_ids: list[uuid.UUID] = []


class LessonCreate(LessonBase):
    pass


class LessonRead(BaseModel):
    id: uuid.UUID
    teacher: str  # Полное имя преподавателя
    room: str  # Название аудитории (например, "ауд 54")
    subject: str  # Название предмета
    pair_no: int
    groups: list[str] = []  # Список названий групп (например, ["ПИ 38/2"])
    time: str | None = None  # Время в формате "12:40 - 14:00"
    model_config = ConfigDict(from_attributes=True)


class ScheduleMetaBase(BaseModel):
    group_id: uuid.UUID
    teacher_user_id: uuid.UUID | None = None
    week_start: date
    version: int = 1


class ScheduleMetaCreate(ScheduleMetaBase):
    pass


class ScheduleMetaRead(ScheduleMetaBase):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)


class SchedulePatch(BaseModel):
    """Схема для патча расписания"""
    lesson_id: uuid.UUID | None = None
    action: str  # 'create', 'update', 'delete'
    data: dict | None = None  # Данные для создания/обновления


class ScheduleChangelogRead(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID | None = None
    teacher_user_id: uuid.UUID | None = None
    change_type: str
    change_data: dict | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

