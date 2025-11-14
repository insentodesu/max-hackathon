from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, schedule, requests, events, payments, library, menu, electives, broadcasts, universities

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Авторизация и верификация"])
api_router.include_router(universities.router, prefix="/universities", tags=["Университеты"])
api_router.include_router(users.router, prefix="/users", tags=["Управление пользователями"])
api_router.include_router(schedule.router, prefix="/schedule", tags=["Управление расписанием"])
api_router.include_router(requests.router, prefix="/requests", tags=["Система заявок и документов"])
api_router.include_router(events.router, prefix="/events", tags=["Лента событий и мероприятия"])
api_router.include_router(payments.router, prefix="/payments", tags=["Оплата услуг"])
api_router.include_router(library.router, prefix="/library", tags=["Электронная библиотека"])
api_router.include_router(menu.router, prefix="/menu", tags=["Главное меню"])
api_router.include_router(electives.router, prefix="/electives", tags=["Элективы"])
api_router.include_router(broadcasts.router, prefix="/broadcasts", tags=["Рассылки"])
