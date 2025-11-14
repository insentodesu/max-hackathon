from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship
import uuid

from app.db.base_class import Base
from app.db.types import GUID


class Room(Base):
    __tablename__ = "rooms"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    number = Column(String, nullable=False)
    building = Column(Text, nullable=True)
    capacity = Column(String, nullable=True)

    # Relationships
    lessons = relationship("Lesson", back_populates="room")

