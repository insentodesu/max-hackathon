from pydantic import BaseModel, ConfigDict
import uuid


class FacultyBase(BaseModel):
    title: str
    university_id: uuid.UUID


class FacultyCreate(FacultyBase):
    pass


class FacultyRead(FacultyBase):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)



