from sqlalchemy import Column, Text
from sqlalchemy.orm import relationship
import uuid

from app.db.base_class import Base
from app.db.types import GUID


class ApprovalRoad(Base):
    __tablename__ = "approval_roads"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(Text, nullable=True)  # Название пути согласования
    description = Column(Text, nullable=True)  # Описание

    # Relationships
    # Убрали back_populates, так как в Request используется viewonly=True
    requests = relationship("Request", lazy="select", viewonly=True)

