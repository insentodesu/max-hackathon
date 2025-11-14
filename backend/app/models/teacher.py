from sqlalchemy import Column, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.db.types import GUID


class Teacher(Base):
    __tablename__ = "teachers"

    user_id = Column(GUID(), ForeignKey("users.id"), primary_key=True, index=True)
    kafedra_id = Column(GUID(), ForeignKey("kafedras.id"), nullable=False)
    tab_number = Column(Text, nullable=False)

    # Relationships
    user = relationship("User", back_populates="teacher")
    kafedra = relationship("Kafedra", back_populates="teachers")
    # lessons доступны через user.lessons, так как Lesson ссылается на user_id

