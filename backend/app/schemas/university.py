from pydantic import BaseModel, ConfigDict
import uuid


class UniversityBase(BaseModel):
    name: str
    city: str


class UniversityCreate(UniversityBase):
    pass


class UniversityRead(UniversityBase):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)



