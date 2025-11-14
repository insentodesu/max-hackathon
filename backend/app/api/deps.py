from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
import uuid

# Используем HTTPBearer для авторизации через токен в заголовке Authorization
security = HTTPBearer(auto_error=False)


def get_db_session() -> Generator[Session, None, None]:
    yield from get_db()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db_session),
) -> User:
    """Получить текущего пользователя из JWT токена. Выбрасывает 401, если токен невалиден."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось подтвердить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials:
        raise credentials_exception
    
    token = credentials.credentials

    # Декодируем JWT токен
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError as exc:
        # Более детальная ошибка для отладки
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Невалидный токен: {str(exc)}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    # Преобразуем user_id в UUID
    try:
        user_uuid = uuid.UUID(user_id)
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Некорректный формат user_id в токене: {user_id}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    
    # Получаем пользователя из БД
    user = db.get(User, user_uuid)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Пользователь с ID {user_uuid} не найден",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db_session),
) -> User | None:
    """Получить текущего пользователя, если токен передан. Возвращает None, если токен не передан или невалиден."""
    if not credentials:
        return None
    
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None
    
    try:
        user_uuid = uuid.UUID(user_id)
        user = db.get(User, user_uuid)
        return user
    except (ValueError, TypeError):
        return None

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    # В новой модели нет поля is_active, всегда возвращаем пользователя
    return current_user


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    from app.models.user import UserRole
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
    return current_user
