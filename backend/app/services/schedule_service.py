"""
Модуль 2: Управление расписанием

Примечание: Push-уведомления об изменениях расписания обрабатываются ботом мессенджера MAX.
Backend хранит расписание в БД и записывает изменения в changelog.
Бот отслеживает изменения через API (changelog) и отправляет push-уведомления пользователям.

Примечание по ТЗ: ТЗ указывает хранение расписания в JSON-файлах, но для MVP используется БД
для гибкости и масштабируемости. JSON можно добавить для экспорта/импорта.
"""
from sqlalchemy.orm import Session
from datetime import date
import uuid

from app.models.lesson import Lesson
from app.models.lesson_group import LessonGroup
from app.models.schedule_meta import ScheduleMeta
from app.models.schedule_changelog import ScheduleChangelog
from app.models.student_group import StudentGroup
from app.schemas.schedule import LessonCreate, SchedulePatch, ScheduleMetaCreate
from sqlalchemy import and_


def get_schedule_for_group(db: Session, group_id: uuid.UUID, week_start: date | None = None):
    """Получить расписание для группы"""
    query = db.query(Lesson).join(LessonGroup).filter(LessonGroup.group_id == group_id)
    
    if week_start:
        # Фильтрация по неделе через ScheduleMeta
        # Находим метаданные расписания для этой группы и недели
        schedule_meta = db.query(ScheduleMeta).filter(
            and_(
                ScheduleMeta.group_id == group_id,
                ScheduleMeta.week_start == week_start
            )
        ).first()
        
        if schedule_meta:
            # Можно добавить дополнительную фильтрацию по версии расписания
            pass
    
    return query.all()


def get_schedule_for_teacher(db: Session, teacher_user_id: uuid.UUID, week_start: date | None = None):
    """Получить расписание для преподавателя"""
    query = db.query(Lesson).filter(Lesson.teacher_user_id == teacher_user_id)
    
    if week_start:
        # Фильтрация по неделе через ScheduleMeta
        schedule_meta = db.query(ScheduleMeta).filter(
            and_(
                ScheduleMeta.teacher_user_id == teacher_user_id,
                ScheduleMeta.week_start == week_start
            )
        ).first()
    
    return query.all()


def create_lesson(db: Session, *, lesson_data: LessonCreate) -> Lesson:
    """Создать занятие"""
    lesson = Lesson(
        teacher_user_id=lesson_data.teacher_user_id,
        room_id=lesson_data.room_id,
        subject_id=lesson_data.subject_id,
        pair_no=lesson_data.pair_no,
    )
    db.add(lesson)
    db.flush()
    
    # Добавляем связи с группами
    for group_id in lesson_data.group_ids:
        lesson_group = LessonGroup(
            lesson_id=lesson.id,
            group_id=group_id,
        )
        db.add(lesson_group)
    
    db.commit()
    db.refresh(lesson)
    return lesson


def patch_schedule(db: Session, *, patches: list[SchedulePatch], group_id: uuid.UUID | None = None):
    """
    Модуль 2: Применение патчей к расписанию
    Создает записи в changelog и обновляет версию расписания
    """
    results = []
    
    for patch in patches:
        if patch.action == "create":
            if not patch.data:
                continue
            
            # Создаем занятие из данных патча
            lesson_data = LessonCreate(**patch.data)
            lesson = create_lesson(db, lesson_data=lesson_data)
            
            # Записываем в changelog
            changelog = ScheduleChangelog(
                group_id=group_id or (lesson_data.group_ids[0] if lesson_data.group_ids else None),
                teacher_user_id=lesson_data.teacher_user_id,
                change_type="create",
                change_data={"lesson_id": str(lesson.id)},
            )
            db.add(changelog)
            
            results.append({"action": "create", "lesson_id": lesson.id, "success": True})
        
        elif patch.action == "update":
            if not patch.lesson_id or not patch.data:
                continue
            
            lesson = db.query(Lesson).filter(Lesson.id == patch.lesson_id).first()
            if not lesson:
                results.append({"action": "update", "lesson_id": patch.lesson_id, "success": False, "error": "Lesson not found"})
                continue
            
            # Обновляем занятие
            for key, value in patch.data.items():
                if hasattr(lesson, key):
                    setattr(lesson, key, value)
            
            # Обновляем связи с группами если нужно
            if "group_ids" in patch.data:
                # Удаляем старые связи
                db.query(LessonGroup).filter(LessonGroup.lesson_id == lesson.id).delete()
                # Добавляем новые
                for group_id in patch.data["group_ids"]:
                    lesson_group = LessonGroup(lesson_id=lesson.id, group_id=group_id)
                    db.add(lesson_group)
            
            # Записываем в changelog
            changelog = ScheduleChangelog(
                group_id=group_id or (patch.data.get("group_ids", [None])[0] if patch.data.get("group_ids") else None),
                teacher_user_id=lesson.teacher_user_id,
                change_type="update",
                change_data={"lesson_id": str(lesson.id), "changes": patch.data},
            )
            db.add(changelog)
            
            results.append({"action": "update", "lesson_id": patch.lesson_id, "success": True})
        
        elif patch.action == "delete":
            if not patch.lesson_id:
                continue
            
            lesson = db.query(Lesson).filter(Lesson.id == patch.lesson_id).first()
            if not lesson:
                results.append({"action": "delete", "lesson_id": patch.lesson_id, "success": False, "error": "Lesson not found"})
                continue
            
            # Записываем в changelog перед удалением
            changelog = ScheduleChangelog(
                group_id=group_id,
                teacher_user_id=lesson.teacher_user_id,
                change_type="delete",
                change_data={"lesson_id": str(lesson.id)},
            )
            db.add(changelog)
            
            # Удаляем занятие
            db.delete(lesson)
            
            results.append({"action": "delete", "lesson_id": patch.lesson_id, "success": True})
    
    # Обновляем версию расписания для всех затронутых групп
    if group_id:
        schedule_meta = db.query(ScheduleMeta).filter(
            ScheduleMeta.group_id == group_id
        ).order_by(ScheduleMeta.version.desc()).first()
        
        if schedule_meta:
            new_meta = ScheduleMeta(
                group_id=group_id,
                teacher_user_id=schedule_meta.teacher_user_id,
                week_start=schedule_meta.week_start,
                version=schedule_meta.version + 1,
            )
            db.add(new_meta)
    
    db.commit()
    return results


def get_schedule_changelog(db: Session, group_id: uuid.UUID | None = None, teacher_user_id: uuid.UUID | None = None):
    """Получить журнал изменений расписания"""
    query = db.query(ScheduleChangelog)
    
    if group_id:
        query = query.filter(ScheduleChangelog.group_id == group_id)
    if teacher_user_id:
        query = query.filter(ScheduleChangelog.teacher_user_id == teacher_user_id)
    
    return query.order_by(ScheduleChangelog.created_at.desc()).all()



