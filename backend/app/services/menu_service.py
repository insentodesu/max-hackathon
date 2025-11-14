from app.models.user import UserRole
from app.schemas.menu import MenuItem, MenuResponse


def get_menu_for_role(role: UserRole) -> MenuResponse:
    """
    Генерирует динамическое меню в зависимости от роли пользователя
    
    Меню студента:
    - Лента мероприятий
    - Элективы
    - ЛК (Библиотека, Помощь)
    
    Меню преподавателя:
    - Лента мероприятий
    - Документооборот (Мои заявки, Согласование заявок, Отпуск)
    - ЛК (Помощь)
    
    Меню админа:
    - Все пункты + админ-панель
    """
    
    if role == UserRole.STUDENT:
        return MenuResponse(
            items=[
                MenuItem(
                    id="events",
                    title="Лента мероприятий",
                    icon="calendar",
                    route="/events"
                ),
                MenuItem(
                    id="electives",
                    title="Элективы",
                    icon="book",
                    route="/electives"
                ),
                MenuItem(
                    id="profile",
                    title="Личный кабинет",
                    icon="user",
                    children=[
                        MenuItem(
                            id="library",
                            title="Библиотека",
                            icon="library",
                            route="/library/access"
                        ),
                        MenuItem(
                            id="help",
                            title="Помощь",
                            icon="help",
                            route="/help"
                        )
                    ]
                )
            ]
        )
    
    elif role == UserRole.STAFF:
        return MenuResponse(
            items=[
                MenuItem(
                    id="events",
                    title="Лента мероприятий",
                    icon="calendar",
                    route="/events"
                ),
                MenuItem(
                    id="documents",
                    title="Документооборот",
                    icon="file-text",
                    children=[
                        MenuItem(
                            id="my-requests",
                            title="Мои заявки",
                            icon="inbox",
                            route="/requests/my"
                        ),
                        MenuItem(
                            id="approval",
                            title="Согласование заявок",
                            icon="check-circle",
                            route="/requests/approval"
                        ),
                        MenuItem(
                            id="vacation",
                            title="Отпуск",
                            icon="briefcase",
                            route="/requests?type=vacation"
                        )
                    ]
                ),
                MenuItem(
                    id="profile",
                    title="Личный кабинет",
                    icon="user",
                    children=[
                        MenuItem(
                            id="help",
                            title="Помощь",
                            icon="help",
                            route="/help"
                        )
                    ]
                )
            ]
        )
    
    elif role == UserRole.ADMIN:
        return MenuResponse(
            items=[
                MenuItem(
                    id="events",
                    title="Лента мероприятий",
                    icon="calendar",
                    route="/events"
                ),
                MenuItem(
                    id="documents",
                    title="Документооборот",
                    icon="file-text",
                    children=[
                        MenuItem(
                            id="my-requests",
                            title="Мои заявки",
                            icon="inbox",
                            route="/requests/my"
                        ),
                        MenuItem(
                            id="approval",
                            title="Согласование заявок",
                            icon="check-circle",
                            route="/requests/approval"
                        ),
                        MenuItem(
                            id="vacation",
                            title="Отпуск",
                            icon="briefcase",
                            route="/requests?type=vacation"
                        )
                    ]
                ),
                MenuItem(
                    id="admin",
                    title="Админ-панель",
                    icon="settings",
                    children=[
                        MenuItem(
                            id="users",
                            title="Пользователи",
                            icon="users",
                            route="/admin/users"
                        ),
                        MenuItem(
                            id="events-management",
                            title="Управление мероприятиями",
                            icon="calendar",
                            route="/admin/events"
                        ),
                        MenuItem(
                            id="library-management",
                            title="Управление библиотекой",
                            icon="library",
                            route="/admin/library"
                        )
                    ]
                ),
                MenuItem(
                    id="profile",
                    title="Личный кабинет",
                    icon="user",
                    children=[
                        MenuItem(
                            id="help",
                            title="Помощь",
                            icon="help",
                            route="/help"
                        )
                    ]
                )
            ]
        )
    
    # По умолчанию возвращаем пустое меню
    return MenuResponse(items=[])

