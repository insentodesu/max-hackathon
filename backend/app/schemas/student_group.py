from pydantic import BaseModel, ConfigDict
import uuid


class StudentGroupBase(BaseModel):
    name: str
    code: str
    faculty_id: uuid.UUID
    curator_user_id: uuid.UUID | None = None


class StudentGroupCreate(StudentGroupBase):
    pass


class StudentGroupRead(StudentGroupBase):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)



