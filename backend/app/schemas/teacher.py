from pydantic import BaseModel, ConfigDict
import uuid


class TeacherBase(BaseModel):
    tab_number: str
    kafedra_id: uuid.UUID


class TeacherCreate(BaseModel):
    tab_number: str
    kafedra_id: uuid.UUID
    full_name: str
    city: str
    university_id: uuid.UUID | None = None


class TeacherRead(TeacherBase):
    user_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

