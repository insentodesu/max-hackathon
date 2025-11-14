"""
Управление университетами
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.schemas.university import UniversityRead
from app.models.university import University

router = APIRouter()


@router.get(
    "",
    response_model=List[UniversityRead],
    summary="Получить список всех университетов",
    description="Возвращает список всех университетов в системе. Используется для выбора вуза при регистрации.",
)
def get_universities(
    db: Session = Depends(get_db),
) -> List[UniversityRead]:
    """
    Получить список всех университетов
    
    Возвращает список всех университетов, отсортированных по названию.
    Используется для выбора вуза при регистрации пользователя.
    """
    universities = db.query(University).order_by(University.name).all()
    return [UniversityRead.model_validate(uni) for uni in universities]


@router.get(
    "/{university_id}/faculties",
    response_model=List[dict],
    summary="Получить список факультетов университета",
    description="Возвращает список всех факультетов указанного университета.",
)
def get_university_faculties(
    university_id: str,
    db: Session = Depends(get_db),
) -> List[dict]:
    """
    Получить список факультетов университета
    
    Возвращает список всех факультетов указанного университета.
    Используется для выбора факультета при регистрации студента.
    """
    from app.models.faculty import Faculty
    import uuid
    
    try:
        uni_uuid = uuid.UUID(university_id)
    except ValueError:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Некорректный формат ID университета"
        )
    
    faculties = db.query(Faculty).filter(
        Faculty.university_id == uni_uuid
    ).order_by(Faculty.title).all()
    
    return [
        {
            "id": str(fac.id),
            "title": fac.title,
        }
        for fac in faculties
    ]


@router.get(
    "/{university_id}/faculties/{faculty_id}/groups",
    response_model=List[dict],
    summary="Получить список групп факультета",
    description="Возвращает список всех студенческих групп указанного факультета.",
)
def get_faculty_groups(
    university_id: str,
    faculty_id: str,
    db: Session = Depends(get_db),
) -> List[dict]:
    """
    Получить список групп факультета
    
    Возвращает список всех студенческих групп указанного факультета.
    Используется для выбора группы при регистрации студента.
    """
    from app.models.faculty import Faculty
    from app.models.student_group import StudentGroup
    import uuid
    
    try:
        uni_uuid = uuid.UUID(university_id)
        fac_uuid = uuid.UUID(faculty_id)
    except ValueError:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Некорректный формат ID"
        )
    
    # Проверяем, что факультет принадлежит указанному университету
    faculty = db.query(Faculty).filter(
        Faculty.id == fac_uuid,
        Faculty.university_id == uni_uuid
    ).first()
    
    if not faculty:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Факультет не найден"
        )
    
    groups = db.query(StudentGroup).filter(
        StudentGroup.faculty_id == fac_uuid
    ).order_by(StudentGroup.name).all()
    
    return [
        {
            "id": str(group.id),
            "name": group.name,
            "code": group.code,
        }
        for group in groups
    ]


@router.get(
    "/{university_id}/faculties/{faculty_id}/kafedras",
    response_model=List[dict],
    summary="Получить список кафедр факультета",
    description="Возвращает список всех кафедр указанного факультета.",
)
def get_faculty_kafedras(
    university_id: str,
    faculty_id: str,
    db: Session = Depends(get_db),
) -> List[dict]:
    """
    Получить список кафедр факультета
    
    Возвращает список всех кафедр указанного факультета.
    Используется для выбора кафедры при регистрации преподавателя/сотрудника.
    """
    from app.models.faculty import Faculty
    from app.models.kafedra import Kafedra
    import uuid
    
    try:
        uni_uuid = uuid.UUID(university_id)
        fac_uuid = uuid.UUID(faculty_id)
    except ValueError:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Некорректный формат ID"
        )
    
    # Проверяем, что факультет принадлежит указанному университету
    faculty = db.query(Faculty).filter(
        Faculty.id == fac_uuid,
        Faculty.university_id == uni_uuid
    ).first()
    
    if not faculty:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Факультет не найден"
        )
    
    kafedras = db.query(Kafedra).filter(
        Kafedra.faculty_id == fac_uuid
    ).order_by(Kafedra.title).all()
    
    return [
        {
            "id": str(kaf.id),
            "title": kaf.title or "Без названия",
        }
        for kaf in kafedras
    ]

