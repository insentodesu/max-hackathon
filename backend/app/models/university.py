from sqlalchemy import Column, Text
from sqlalchemy.orm import relationship
import uuid

from app.db.base_class import Base
from app.db.types import GUID


class University(Base):
    __tablename__ = "universities"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(Text, nullable=False)
    city = Column(Text, nullable=False)

    # Relationships
    users = relationship("User", back_populates="university")
    staff = relationship("Staff", back_populates="university")
    faculties = relationship("Faculty", back_populates="university")
    library_access = relationship("LibraryAccess", back_populates="university", uselist=False)

