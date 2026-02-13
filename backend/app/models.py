from sqlalchemy import Column, Integer, String, DateTime
from app.db import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    title = Column(String, nullable=True)
    author = Column(String, nullable=True)
    description = Column(String, nullable=True)
    imported_at = Column(DateTime, nullable=False)
