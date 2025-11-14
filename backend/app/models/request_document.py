from sqlalchemy import Column, Text, String, ForeignKey, DateTime, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.base_class import Base
from app.db.types import GUID


class RequestDocument(Base):
    __tablename__ = "request_documents"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    request_id = Column(Integer, ForeignKey("requests.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(Text, nullable=False)  # Путь к файлу на сервере
    file_size = Column(Integer, nullable=True)  # Размер файла в байтах
    mime_type = Column(String, nullable=True)  # MIME тип файла
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    request = relationship("Request", back_populates="documents")

