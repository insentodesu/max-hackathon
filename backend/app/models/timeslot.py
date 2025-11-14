from sqlalchemy import Column, Integer, Time
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Timeslot(Base):
    __tablename__ = "timeslots"

    pair_no = Column(Integer, primary_key=True, index=True)
    start = Column(Time, nullable=False)
    end = Column(Time, nullable=False)

    # Relationships
    lessons = relationship("Lesson", back_populates="timeslot")



