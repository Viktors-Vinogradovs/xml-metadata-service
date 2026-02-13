from datetime import datetime
from pydantic import BaseModel


class DocumentBase(BaseModel):
    filename: str
    title: str | None = None
    author: str | None = None
    description: str | None = None


class DocumentCreate(DocumentBase):
    pass


class DocumentRead(DocumentBase):
    id: int
    imported_at: datetime

    model_config = {"from_attributes": True}
