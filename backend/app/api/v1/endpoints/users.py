"""
Управление пользователями
Добавление студентов и преподавателей
Личный кабинет
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.api.deps import get_current_active_user
from app.schemas.student import StudentCreate, StudentRead
from app.schemas.teacher import TeacherCreate, TeacherRead
from app.schemas.user import ProfileRead
from app.services.student_service import create_student
from app.services.teacher_service import create_teacher
from app.services.user_service import get_user_profile

router = APIRouter()


@router.post(
    "/students/add",
    response_model=StudentRead,
    summary="Добавление нового студента",
    description="Добавляет нового студента в систему. Создает пользователя и запись студента.",
)
def add_student(
    student_data: StudentCreate,
    db: Session = Depends(get_db),
) -> StudentRead:
    """
    Добавление нового студента
    
    Используется сотрудником ВУЗа для добавления студентов в систему.
    """
    try:
        student = create_student(db=db, student_data=student_data)
        return StudentRead.model_validate(student)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при создании студента: {str(e)}")


@router.post(
    "/teachers/add",
    response_model=TeacherRead,
    summary="Добавление нового преподавателя",
    description="Добавляет нового преподавателя в систему. Создает пользователя и запись преподавателя.",
)
def add_teacher(
    teacher_data: TeacherCreate,
    db: Session = Depends(get_db),
) -> TeacherRead:
    """
    Добавление нового преподавателя
    
    Используется сотрудником ВУЗа для добавления преподавателей в систему.
    """
    try:
        teacher = create_teacher(db=db, teacher_data=teacher_data)
        return TeacherRead.model_validate(teacher)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при создании преподавателя: {str(e)}")


@router.get(
    "/profile",
    response_model=ProfileRead,
    summary="Личный кабинет",
    description="Получить данные личного кабинета текущего пользователя",
)
def get_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ProfileRead:
    """Получить данные личного кабинета текущего пользователя"""
    try:
        profile_data = get_user_profile(db, current_user.id)
        return ProfileRead(**profile_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении профиля: {str(e)}")

