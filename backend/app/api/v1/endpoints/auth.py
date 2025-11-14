"""
Авторизация и верификация пользователя
Проверка существования студента в базе деканата и привязка max_id к существующему пользователю
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.api.deps import get_current_active_user
from app.schemas.user import (
    UserVerificationRequest, UserVerificationResponse,
    UserRegistrationRequest, UserRegistrationResponse
)
from app.schemas.auth import Token
from app.services.user_service import verify_user, get_user_by_id
from app.services.registration_service import register_user
from app.core.security import create_access_token
import uuid

router = APIRouter()


@router.post(
    "/register",
    response_model=UserRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Самостоятельная регистрация",
    description="Самостоятельная регистрация пользователя. После регистрации автоматически выполняется верификация.",
)
def register_user_endpoint(
    registration_data: UserRegistrationRequest,
    db: Session = Depends(get_db),
) -> UserRegistrationResponse:
    """
    Самостоятельная регистрация (4.1.1)
    
    Пользователь выбирает роль и вводит данные:
    - Общие поля: ФИО, город, вуз
    - Для студента: факультет, группа, номер студенческого билета
    - Для преподавателя/сотрудника: кафедра/отдел, табельный номер
    
    После регистрации автоматически выполняется верификация данных с БД деканата.
    Если данные не совпадают, регистрация отменяется.
    """
    try:
        user, token = register_user(db, registration_data=registration_data)
        return UserRegistrationResponse(
            success=True,
            message="Регистрация успешна. Данные проверены и подтверждены.",
            user_id=user.id,
            access_token=token.access_token,
            token_type=token.token_type
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при регистрации: {str(e)}"
        )


@router.post(
    "/verify",
    response_model=UserVerificationResponse,
    summary="Верификация пользователя",
    description="Проверяет существование пользователя в базе деканата. "
                "Если пользователь найден, привязывает max_id к существующему пользователю.",
)
def verify_user_endpoint(
    request: UserVerificationRequest,
    db: Session = Depends(get_db),
) -> UserVerificationResponse:
    """
    Верификация пользователя
    
    Пользователь выбирает роль и вводит данные.
    Система проверяет, существует ли такой студент/преподаватель/сотрудник в базе деканата.
    
    - Если найден: успех, привязываем max_id к уже созданному пользователю
    - Если не найден: ошибка, пользователь должен обратиться в деканат
    """
    result = verify_user(db=db, request=request)
    
    if not result.success:
        raise HTTPException(
            status_code=404,
            detail=result.message
        )
    
    return result


@router.post(
    "/login",
    response_model=Token,
    summary="Получение токена доступа",
    description="Получает JWT токен для доступа к API. Можно передать user_id напрямую или использовать OAuth2 форму.",
)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    """
    Получение токена доступа
    
    Используйте OAuth2 форму:
    - username: user_id (UUID пользователя)
    - password: можно оставить пустым или передать любой строкой (для совместимости с OAuth2)
    
    Или после успешной верификации через /verify, используйте user_id из ответа.
    """
    try:
        user_uuid = uuid.UUID(form_data.username)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Некорректный формат user_id. Используйте UUID в поле 'username'"
        )
    
    user = get_user_by_id(db, user_uuid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    access_token = create_access_token(subject=str(user.id))
    return Token(access_token=access_token, token_type="bearer")


@router.get(
    "/login-by-max-id",
    response_model=Token,
    summary="Получение токена доступа по max_id",
    description="Получает JWT токен для доступа к API по max_id пользователя из мессенджера MAX.",
)
def login_by_max_id(
    max_id: int,
    db: Session = Depends(get_db),
) -> Token:
    """
    Получение токена доступа по max_id
    
    Используется ботом для получения токена по max_id пользователя из мессенджера MAX.
    
    Параметры:
    - max_id: ID пользователя из мессенджера MAX
    """
    from app.services.user_service import get_user_by_max_id
    
    user = get_user_by_max_id(db, max_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь с max_id={max_id} не найден. Сначала зарегистрируйтесь через /register"
        )
    
    access_token = create_access_token(subject=str(user.id))
    return Token(access_token=access_token, token_type="bearer")

