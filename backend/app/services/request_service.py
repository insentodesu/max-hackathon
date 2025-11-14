from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from sqlalchemy.sql import func
from typing import List, Optional
from datetime import datetime
import uuid
from pathlib import Path

"""
Модуль 4: Система заявок и документов

Примечание: Push-уведомления обрабатываются ботом мессенджера MAX, а не backend API.
Backend только меняет статусы заявок и предоставляет API для работы с заявками.
Бот отслеживает изменения статусов через API и отправляет push-уведомления пользователям.
"""
from app.models.request import Request, RequestType, RequestStatus
from app.models.request_document import RequestDocument
from app.models.request_approval_step import RequestApprovalStep, ApprovalAction
from app.models.user import User, UserRole
from app.models.student import Student
from app.models.student_group import StudentGroup
from app.models.teacher import Teacher
from app.models.staff import Staff
from app.models.faculty import Faculty
from app.models.kafedra import Kafedra
from app.schemas.request import RequestCreate, RequestApprove, RequestReject
from app.core.config import settings


def get_request_by_id(db: Session, request_id: int) -> Optional[Request]:
    """Получить заявку по ID"""
    return db.query(Request).filter(Request.id == request_id).first()


def get_user_requests(db: Session, user_id: uuid.UUID) -> List[Request]:
    """Получить все заявки пользователя (Мои заявки)"""
    return db.query(Request).filter(Request.author_user_id == user_id).order_by(Request.created_at.desc()).all()


def get_requests_for_approval(db: Session, approver_user_id: uuid.UUID) -> List[Request]:
    """Получить заявки на согласование для пользователя"""
    # Ищем заявки, где пользователь является текущим согласующим
    # ИЛИ где есть шаг согласования с PENDING для этого пользователя
    requests_by_current_approver = db.query(Request).filter(
        and_(
            Request.current_approver_id == approver_user_id,
            Request.status == RequestStatus.PENDING
        )
    ).all()
    
    # Также ищем через шаги согласования (на случай, если current_approver_id не установлен)
    pending_steps = db.query(RequestApprovalStep).filter(
        and_(
            RequestApprovalStep.approver_user_id == approver_user_id,
            RequestApprovalStep.action == ApprovalAction.PENDING
        )
    ).all()
    
    request_ids_from_steps = {step.request_id for step in pending_steps}
    requests_by_steps = db.query(Request).filter(
        and_(
            Request.id.in_(request_ids_from_steps),
            Request.status == RequestStatus.PENDING
        )
    ).all() if request_ids_from_steps else []
    
    # Объединяем результаты и убираем дубликаты
    all_requests = {req.id: req for req in requests_by_current_approver}
    for req in requests_by_steps:
        all_requests[req.id] = req
    
    # Сортируем по дате создания (новые сначала)
    return sorted(all_requests.values(), key=lambda r: r.created_at, reverse=True)


def _get_deanery_staff_for_faculty(db: Session, faculty_id: uuid.UUID) -> Optional[uuid.UUID]:
    """Найти сотрудника деканата для факультета"""
    # Находим факультет и его университет
    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not faculty:
        return None
    
    # Ищем первого сотрудника (Staff) из того же университета
    staff = db.query(Staff).filter(Staff.university_id == faculty.university_id).first()
    if staff:
        return staff.user_id
    
    # Если сотрудника нет, используем админа как fallback
    admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
    if admin:
        return admin.id
    
    return None


def _get_kafedra_head_for_teacher(db: Session, teacher_user_id: uuid.UUID) -> Optional[uuid.UUID]:
    """Найти руководителя кафедры для преподавателя"""
    teacher = db.query(Teacher).filter(Teacher.user_id == teacher_user_id).first()
    if not teacher:
        return None
    
    # Ищем первого преподавателя из той же кафедры (кроме самого автора)
    # В реальной системе здесь должна быть логика определения руководителя
    # Для MVP используем первого преподавателя из кафедры или админа
    kafedra_teacher = db.query(Teacher).filter(
        and_(
            Teacher.kafedra_id == teacher.kafedra_id,
            Teacher.user_id != teacher_user_id
        )
    ).first()
    
    if kafedra_teacher:
        return kafedra_teacher.user_id
    
    # Если преподавателя нет, используем админа как fallback
    admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
    if admin:
        return admin.id
    
    return None


def _get_hr_staff_for_university(db: Session, university_id: uuid.UUID) -> Optional[uuid.UUID]:
    """Найти сотрудника отдела кадров для университета"""
    # Ищем первого сотрудника (Staff) из университета
    staff = db.query(Staff).filter(Staff.university_id == university_id).first()
    if staff:
        return staff.user_id
    
    # Если сотрудника нет, используем админа как fallback
    admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
    if admin:
        return admin.id
    
    return None


def _get_first_approver_for_request(
    db: Session,
    request_type: RequestType,
    author_user_id: uuid.UUID
) -> Optional[uuid.UUID]:
    """Определить первого согласующего для заявки"""
    if request_type == RequestType.STUDENT_CERTIFICATE:
        # Справка об обучении - автоматически готово, согласующих нет
        return None
    elif request_type == RequestType.ACADEMIC_LEAVE:
        # Академический отпуск: Куратор → Деканат
        student = db.query(Student).filter(Student.user_id == author_user_id).first()
        if student and student.group and student.group.curator_user_id:
            return student.group.curator_user_id
    elif request_type == RequestType.TRANSFER:
        # Заявка на перевод: Деканат
        student = db.query(Student).filter(Student.user_id == author_user_id).first()
        if student and student.faculty_id:
            return _get_deanery_staff_for_faculty(db, student.faculty_id)
    elif request_type == RequestType.VACATION:
        # Отпуск: Руководитель → Отдел кадров
        # Для преподавателя находим руководителя кафедры
        return _get_kafedra_head_for_teacher(db, author_user_id)
    elif request_type == RequestType.DOCUMENT_APPROVAL:
        # Документ на согласование: Руководитель
        # Для преподавателя находим руководителя кафедры
        return _get_kafedra_head_for_teacher(db, author_user_id)
    
    return None


def create_request(db: Session, *, request_data: RequestCreate, author_user_id: uuid.UUID) -> Request:
    """Создать новую заявку"""
    # Определяем маршрут согласования в зависимости от типа заявки
    approval_road_id = None
    current_approver_id = None
    initial_status = RequestStatus.PENDING
    
    # Для справки об обучении - автоматически одобрено
    if request_data.request_type == RequestType.STUDENT_CERTIFICATE:
        initial_status = RequestStatus.APPROVED
    else:
        # Определяем первого согласующего
        current_approver_id = _get_first_approver_for_request(
            db=db,
            request_type=request_data.request_type,
            author_user_id=author_user_id
        )
        if not current_approver_id:
            # Если не нашли согласующего, оставляем в ожидании
            initial_status = RequestStatus.PENDING
    
    request = Request(
        request_type=request_data.request_type,
        author_user_id=author_user_id,
        content=request_data.content,
        status=initial_status,
        approval_road_id=approval_road_id,
        current_approver_id=current_approver_id,
    )
    db.add(request)
    db.flush()
    
    # Создаем шаги согласования (если нужно)
    if initial_status == RequestStatus.PENDING and current_approver_id:
        # Определяем роль согласующего
        approver_role = "Куратор"
        if request_data.request_type == RequestType.TRANSFER:
            approver_role = "Деканат"
        elif request_data.request_type in [RequestType.VACATION, RequestType.DOCUMENT_APPROVAL]:
            approver_role = "Руководитель"
        
        step = RequestApprovalStep(
            request_id=request.id,
            step_order=1,
            approver_user_id=current_approver_id,
            approver_role=approver_role,
            action=ApprovalAction.PENDING,
        )
        db.add(step)
    
    db.commit()
    db.refresh(request)
    return request


def approve_request(
    db: Session,
    *,
    request_id: int,
    approver_user_id: uuid.UUID,
    approve_data: RequestApprove
) -> Request:
    """Одобрить заявку"""
    request = get_request_by_id(db, request_id)
    if not request:
        raise ValueError("Заявка не найдена")
    
    if request.current_approver_id != approver_user_id:
        raise ValueError("Вы не являетесь текущим согласующим")
    
    if request.status != RequestStatus.PENDING:
        raise ValueError("Заявка уже обработана")
    
    # Обновляем текущий шаг согласования
    current_step = db.query(RequestApprovalStep).filter(
        and_(
            RequestApprovalStep.request_id == request_id,
            RequestApprovalStep.action == ApprovalAction.PENDING
        )
    ).order_by(RequestApprovalStep.step_order.desc()).first()
    
    if current_step:
        current_step.action = ApprovalAction.APPROVED
        current_step.comment = approve_data.comment
        current_step.processed_at = datetime.utcnow()
    
    # Определяем следующий шаг согласования
    next_approver_id = None
    next_approver_role = None
    
    if request.request_type == RequestType.ACADEMIC_LEAVE:
        # После куратора идет деканат
        if current_step and current_step.step_order == 1:
            # Находим студента и его факультет
            student = db.query(Student).filter(Student.user_id == request.author_user_id).first()
            if student and student.faculty_id:
                next_approver_id = _get_deanery_staff_for_faculty(db, student.faculty_id)
                next_approver_role = "Деканат"
    elif request.request_type == RequestType.VACATION:
        # После руководителя идет отдел кадров
        if current_step and current_step.step_order == 1:
            # Находим преподавателя и его университет
            teacher = db.query(Teacher).filter(Teacher.user_id == request.author_user_id).first()
            if teacher:
                # Находим кафедру и факультет, чтобы получить university_id
                kafedra = db.query(Kafedra).filter(Kafedra.id == teacher.kafedra_id).first()
                if kafedra:
                    faculty = db.query(Faculty).filter(Faculty.id == kafedra.faculty_id).first()
                    if faculty:
                        next_approver_id = _get_hr_staff_for_university(db, faculty.university_id)
                        next_approver_role = "Отдел кадров"
    elif request.request_type == RequestType.TRANSFER:
        # Заявка на перевод идет только в деканат, после одобрения - одобрено
        # После одобрения деканатом статус меняется на APPROVED
        if current_step and current_step.step_order == 1:
            # Это был последний шаг - заявка одобрена
            pass
    elif request.request_type == RequestType.DOCUMENT_APPROVAL:
        # Документ на согласование: только руководитель, после одобрения - одобрено
        # После одобрения руководителем статус меняется на APPROVED
        if current_step and current_step.step_order == 1:
            # Это был последний шаг - заявка одобрена
            pass
    
    if next_approver_id:
        # Есть следующий шаг
        next_step = RequestApprovalStep(
            request_id=request_id,
            step_order=current_step.step_order + 1 if current_step else 1,
            approver_user_id=next_approver_id,
            approver_role=next_approver_role or "Деканат",
            action=ApprovalAction.PENDING,
        )
        db.add(next_step)
        request.current_approver_id = next_approver_id
        request.status = RequestStatus.PENDING
    else:
        # Все шаги пройдены - заявка одобрена
        request.status = RequestStatus.APPROVED
        request.current_approver_id = None
    
    db.commit()
    db.refresh(request)
    return request


def reject_request(
    db: Session,
    *,
    request_id: int,
    approver_user_id: uuid.UUID,
    reject_data: RequestReject
) -> Request:
    """Отклонить заявку"""
    request = get_request_by_id(db, request_id)
    if not request:
        raise ValueError("Заявка не найдена")
    
    if request.current_approver_id != approver_user_id:
        raise ValueError("Вы не являетесь текущим согласующим")
    
    if request.status != RequestStatus.PENDING:
        raise ValueError("Заявка уже обработана")
    
    # Обновляем текущий шаг согласования
    current_step = db.query(RequestApprovalStep).filter(
        and_(
            RequestApprovalStep.request_id == request_id,
            RequestApprovalStep.action == ApprovalAction.PENDING
        )
    ).order_by(RequestApprovalStep.step_order.desc()).first()
    
    if current_step:
        current_step.action = ApprovalAction.REJECTED
        current_step.comment = reject_data.reason
        current_step.processed_at = datetime.utcnow()
    
    request.status = RequestStatus.REJECTED
    request.rejection_reason = reject_data.reason
    request.current_approver_id = None
    
    db.commit()
    db.refresh(request)
    return request


def add_request_document(
    db: Session,
    *,
    request_id: int,
    filename: str,
    file_content: bytes,
    mime_type: Optional[str] = None
) -> RequestDocument:
    """Добавить документ к заявке"""
    request = get_request_by_id(db, request_id)
    if not request:
        raise ValueError("Заявка не найдена")
    
    # Сохраняем файл
    static_dir = Path(settings.static_root)
    requests_dir = static_dir / settings.request_documents_prefix / str(request_id)
    requests_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = requests_dir / filename
    file_path.write_bytes(file_content)
    
    relative_path = f"{settings.request_documents_prefix}/{request_id}/{filename}"
    
    document = RequestDocument(
        request_id=request_id,
        filename=filename,
        file_path=relative_path,
        file_size=len(file_content),
        mime_type=mime_type,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def get_request_documents(db: Session, request_id: int) -> List[RequestDocument]:
    """Получить все документы заявки"""
    return db.query(RequestDocument).filter(RequestDocument.request_id == request_id).all()


def get_request_detail(db: Session, request_id: int, user_id: uuid.UUID) -> Optional[Request]:
    """Получить детальную информацию о заявке с проверкой прав доступа"""
    request = get_request_by_id(db, request_id)
    if not request:
        return None
    
    # Проверяем права доступа
    if request.author_user_id != user_id and request.current_approver_id != user_id:
        return None
    
    return request

