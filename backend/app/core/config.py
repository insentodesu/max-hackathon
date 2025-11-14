from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_v1_prefix: str = Field(default="/api/v1")
    project_name: str = Field(default="Система управления образовательным процессом")
    secret_key: str = Field(default="supersecret")
    access_token_expire_minutes: int = Field(default=60)
    algorithm: str = Field(default="HS256")
    database_url: str = Field(default="sqlite:///./app.db")
    static_root: str = Field(default="static")
    static_dir: str = Field(default="static")  # Абсолютный путь к директории со статикой
    static_url: str = Field(default="/static")
    request_documents_prefix: str = Field(default="requests")
    # ЮКасса настройки (для реальной интеграции)
    yookassa_shop_id: str = Field(default="")
    yookassa_secret_key: str = Field(default="")
    yookassa_test_mode: bool = Field(default=True)
    bot_notify_base_url: str = Field(default="http://bot:8080")
    bot_notify_token: str = Field(default="")
    bot_default_sender_max_id: int = Field(default=1)

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,  # Позволяет читать DATABASE_URL из env
    }


settings = Settings()
