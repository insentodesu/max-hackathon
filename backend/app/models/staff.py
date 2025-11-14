from sqlalchemy import Column, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.db.types import GUID


class Staff(Base):
    __tablename__ = "staff"

    user_id = Column(GUID(), ForeignKey("users.id"), primary_key=True, index=True)
    university_id = Column(GUID(), ForeignKey("universities.id"), nullable=False)
    tab_number = Column(Text, nullable=False)

    # Relationships
    user = relationship("User", back_populates="staff")
    university = relationship("University", back_populates="staff")

