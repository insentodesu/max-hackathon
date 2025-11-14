"""
РЈРїСЂР°РІР»РµРЅРёРµ СЂР°СЃРїРёСЃР°РЅРёРµРј
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.db.session import get_db
from app.schemas.schedule import LessonRead, SchedulePatch, ScheduleChangelogRead
from app.services.schedule_service import (
    get_schedule_for_group,
    get_schedule_for_teacher,
    patch_schedule,
    get_schedule_changelog,
)
from app.models.lesson_group import LessonGroup
from app.models.user import User, UserRole
from app.models.room import Room
from app.models.subject import Subject
from app.models.student_group import StudentGroup
from app.models.timeslot import Timeslot
import uuid

router = APIRouter()


@router.get(
    "",
    response_model=List[LessonRead],
    summary="РџРѕР»СѓС‡РµРЅРёРµ СЂР°СЃРїРёСЃР°РЅРёСЏ",
    description="РџРѕР»СѓС‡Р°РµС‚ СЂР°СЃРїРёСЃР°РЅРёРµ РґР»СЏ РіСЂСѓРїРїС‹ РёР»Рё РїСЂРµРїРѕРґР°РІР°С‚РµР»СЏ. РњРѕР¶РЅРѕ СѓРєР°Р·Р°С‚СЊ week_start РґР»СЏ С„РёР»СЊС‚СЂР°С†РёРё РїРѕ РЅРµРґРµР»Рµ.",
)
def get_schedule(
    group_id: uuid.UUID | None = None,
    teacher_user_id: uuid.UUID | None = None,
    max_id: int | None = None,
    week_start: Optional[date] = None,
    db: Session = Depends(get_db),
) -> List[LessonRead]:
    """
    Получить расписание

    Позволяет студенту или сотруднику получить неделю расписания. week_start — начало недели (YYYY-MM-DD).
    Если явно не переданы group_id/teacher_user_id, можно передать max_id и система определит нужные параметры автоматически.
    """
    if not group_id and not teacher_user_id:
        if max_id is not None:
            user = db.query(User).filter(User.max_id == max_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="Пользователь с указанным max_id не найден")
            if user.role == UserRole.STUDENT:
                if not user.student or not user.student.group_id:
                    raise HTTPException(status_code=400, detail="Для студента не найдена учебная группа")
                group_id = user.student.group_id
            else:
                teacher = getattr(user, "teacher", None)
                if not teacher:
                    raise HTTPException(status_code=400, detail="Для сотрудника не найдена связь с расписанием преподавателя")
                teacher_user_id = teacher.user_id
        else:
            raise HTTPException(status_code=400, detail="Необходимо указать group_id, teacher_user_id или max_id")

    if group_id:
        lessons = get_schedule_for_group(db=db, group_id=group_id, week_start=week_start)
    elif teacher_user_id:
        lessons = get_schedule_for_teacher(db=db, teacher_user_id=teacher_user_id, week_start=week_start)
    else:
        lessons = []

    result = []
    for lesson in lessons:
        teacher = db.get(User, lesson.teacher_user_id)
        teacher_name = teacher.full_name if teacher else "Неизвестно"

        room = db.get(Room, lesson.room_id)
        room_name = f"Ауд. {room.number}" if room else "Неизвестно"
        if room and room.building:
            room_name = f"{room_name} ({room.building})"

        subject = db.get(Subject, lesson.subject_id)
        subject_name = subject.title if subject else "Неизвестно"

        lesson_groups = db.query(LessonGroup).filter(LessonGroup.lesson_id == lesson.id).all()
        group_names = []
        for lg in lesson_groups:
            group = db.get(StudentGroup, lg.group_id)
            if group:
                group_names.append(group.name)

        timeslot = db.get(Timeslot, lesson.pair_no)
        time_str = None
        if timeslot:
            start_str = timeslot.start.strftime("%H:%M")
            end_str = timeslot.end.strftime("%H:%M")
            time_str = f"{start_str} - {end_str}"

        result.append(LessonRead(
            id=lesson.id,
            teacher=teacher_name,
            room=room_name,
            subject=subject_name,
            pair_no=lesson.pair_no,
            groups=group_names,
            time=time_str,
        ))

    return result

@router.patch(
    "/patch",
    summary="РџСЂРёРјРµРЅРµРЅРёРµ РїР°С‚С‡РµР№ Рє СЂР°СЃРїРёСЃР°РЅРёСЋ",
    description="РџСЂРёРјРµРЅСЏРµС‚ РёР·РјРµРЅРµРЅРёСЏ (РїР°С‚С‡Рё) Рє СЂР°СЃРїРёСЃР°РЅРёСЋ. "
                "Р—Р°РїРёСЃС‹РІР°РµС‚ РёР·РјРµРЅРµРЅРёСЏ РІ Р¶СѓСЂРЅР°Р» Рё РѕР±РЅРѕРІР»СЏРµС‚ РІРµСЂСЃРёСЋ СЂР°СЃРїРёСЃР°РЅРёСЏ.",
)
def patch_schedule_endpoint(
    patches: List[SchedulePatch],
    group_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
):
    """
    РџСЂРёРјРµРЅРµРЅРёРµ РїР°С‚С‡РµР№ Рє СЂР°СЃРїРёСЃР°РЅРёСЋ
    
    РџСЂРёРјРµРЅСЏРµС‚ РёР·РјРµРЅРµРЅРёСЏ Рє СЂР°СЃРїРёСЃР°РЅРёСЋ:
    - РЎРѕР·РґР°РµС‚ Р·Р°РїРёСЃРё РІ Schedule changelog
    - РћР±РЅРѕРІР»СЏРµС‚ РІРµСЂСЃРёСЋ СЂР°СЃРїРёСЃР°РЅРёСЏ
    - РћС‚РїСЂР°РІР»СЏРµС‚ СѓРІРµРґРѕРјР»РµРЅРёСЏ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏРј, СЃРІСЏР·Р°РЅРЅС‹Рј СЃ РёР·РјРµРЅРµРЅРёРµРј
    """
    try:
        results = patch_schedule(db=db, patches=patches, group_id=group_id)
        return {
            "success": True,
            "results": results,
            "message": "РџР°С‚С‡Рё РїСЂРёРјРµРЅРµРЅС‹ СѓСЃРїРµС€РЅРѕ"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"РћС€РёР±РєР° РїСЂРё РїСЂРёРјРµРЅРµРЅРёРё РїР°С‚С‡РµР№: {str(e)}")


@router.get(
    "/changelog",
    response_model=List[ScheduleChangelogRead],
    summary="Р–СѓСЂРЅР°Р» РёР·РјРµРЅРµРЅРёР№ СЂР°СЃРїРёСЃР°РЅРёСЏ",
    description="РџРѕР»СѓС‡Р°РµС‚ Р¶СѓСЂРЅР°Р» РёР·РјРµРЅРµРЅРёР№ СЂР°СЃРїРёСЃР°РЅРёСЏ РґР»СЏ РіСЂСѓРїРїС‹ РёР»Рё РїСЂРµРїРѕРґР°РІР°С‚РµР»СЏ.",
)
def get_schedule_changelog_endpoint(
    group_id: uuid.UUID | None = None,
    teacher_user_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
) -> List[ScheduleChangelogRead]:
    """РџРѕР»СѓС‡РёС‚СЊ Р¶СѓСЂРЅР°Р» РёР·РјРµРЅРµРЅРёР№ СЂР°СЃРїРёСЃР°РЅРёСЏ"""
    changelogs = get_schedule_changelog(db=db, group_id=group_id, teacher_user_id=teacher_user_id)
    return [ScheduleChangelogRead.model_validate(changelog) for changelog in changelogs]

