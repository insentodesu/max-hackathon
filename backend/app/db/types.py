import json
import uuid
from typing import Any

from sqlalchemy.types import TypeDecorator, Text, String


class JSONEncodedList(TypeDecorator):
    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Any, dialect) -> str | None:  
        if value is None:
            return None
        if not isinstance(value, list):
            raise TypeError("JSONEncodedList only accepts Python list values")
        return json.dumps(value, ensure_ascii=False)

    def process_result_value(self, value: Any, dialect) -> list[str]:
        if value is None:
            return []
        try:
            decoded = json.loads(value)
        except (TypeError, json.JSONDecodeError):
            return []
        if isinstance(decoded, list):
            return decoded
        return []


class GUID(TypeDecorator):
    """UUID type для SQLite совместимости"""
    impl = String
    cache_ok = True

    def process_bind_param(self, value: Any, dialect) -> str | None:
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return str(value)
        if isinstance(value, str):
            return value
        raise TypeError(f"GUID only accepts UUID or string values, got {type(value)}")

    def process_result_value(self, value: Any, dialect) -> uuid.UUID | None:
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        if isinstance(value, str):
            return uuid.UUID(value)
        raise TypeError(f"GUID process_result_value got unexpected type: {type(value)}")