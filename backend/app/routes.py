import os
from enum import Enum
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db import get_db
from app.import_service import import_documents, load_remote_xml
from app.models import Document
from app.schemas import DocumentOut

router = APIRouter(prefix="/api", tags=["documents"])

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
REMOTE_URL = os.getenv(
    "REMOTE_URL", "http://localhost:8000/api/remote/documents.xml"
)


class SortField(str, Enum):
    created_at = "created_at"
    title = "title"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


@router.get("/remote/documents.xml")
def serve_xml():
    """Simulē attālo XML avotu — atgriež lokālo failu."""
    xml_path = DATA_DIR / "documents.xml"
    if not xml_path.exists():
        raise HTTPException(status_code=404, detail="XML fails nav atrasts")
    return Response(
        content=xml_path.read_text(encoding="utf-8"),
        media_type="application/xml",
    )


@router.post("/import")
def trigger_import(db: Session = Depends(get_db)):
    """Ielādē XML no attālā URL un importē dokumentus DB."""
    try:
        xml_text = load_remote_xml(REMOTE_URL)
    except Exception as e:
        raise HTTPException(
            status_code=502, detail=f"Neizdevās ielādēt XML: {e}"
        ) from e

    try:
        count = import_documents(xml_text, db)
    except ValueError as e:
        raise HTTPException(
            status_code=422, detail=f"XML parsēšanas kļūda: {e}"
        ) from e

    return {"imported": count}


@router.get("/documents", response_model=list[DocumentOut])
def list_documents(
    importance: str | None = None,
    category: str | None = None,
    active: bool | None = None,
    sort: SortField = SortField.created_at,
    order: SortOrder = SortOrder.desc,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Document)

    if importance is not None:
        query = query.filter(Document.importance == importance)
    if category is not None:
        query = query.filter(Document.category == category)
    if active is not None:
        query = query.filter(Document.active == active)

    sort_column = getattr(Document, sort.value)
    query = query.order_by(
        sort_column.asc() if order == SortOrder.asc else sort_column.desc()
    )

    return query.offset(offset).limit(limit).all()
