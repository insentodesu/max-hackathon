from pydantic import BaseModel, ConfigDict
import uuid


class StudentBase(BaseModel):
    student_card: str
    faculty_id: uuid.UUID
    group_id: uuid.UUID


class StudentCreate(BaseModel):
    student_card: str
    faculty_id: uuid.UUID
    group_id: uuid.UUID
    full_name: str
    city: str
    university_id: uuid.UUID | None = None


class StudentRead(StudentBase):
    user_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

