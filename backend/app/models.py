from sqlalchemy import Boolean, Column, Date, Index, Integer, String

from app.db import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    responsible_unit = Column(String, nullable=False)
    created_at = Column(Date, nullable=False)
    url = Column(String, nullable=False, unique=True)
    file_type = Column(String, nullable=False)
    reading_time_minutes = Column(Integer, nullable=False)
    importance = Column(String, nullable=False)
    category = Column(String, nullable=False)
    active = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        Index("ix_documents_importance", "importance"),
        Index("ix_documents_category", "category"),
        Index("ix_documents_active", "active"),
        Index("ix_documents_created_at", "created_at"),
    )
