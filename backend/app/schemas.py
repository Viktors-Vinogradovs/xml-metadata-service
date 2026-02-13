from datetime import date

from pydantic import BaseModel


class DocumentBase(BaseModel):
    title: str
    description: str | None = None
    responsible_unit: str
    created_at: date
    url: str
    file_type: str
    reading_time_minutes: int
    importance: str
    category: str
    active: bool


class DocumentCreate(DocumentBase):
    pass


class DocumentRead(DocumentBase):
    id: int

    model_config = {"from_attributes": True}
