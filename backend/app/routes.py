import os
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import case
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

VALID_SORT_FIELDS = {"created_at", "title", "importance", "active"}

# Svarīguma loģiskā secība SQL CASE izteiksmei
IMPORTANCE_ORDER = case(
    {"low": 0, "medium": 1, "high": 2, "critical": 3},
    value=Document.importance,
    else_=4,
)


def _parse_date(value: str, field_name: str) -> date:
    """Parsē datumu no teksta; atgriež 400, ja formāts nederīgs."""
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Nederīgs datuma formāts laukam '{field_name}': '{value}'. Gaidīts: YYYY-MM-DD",
        )


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
    created_from: str | None = None,
    created_to: str | None = None,
    sort: str = "created_at",
    order: str = "desc",
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    if sort not in VALID_SORT_FIELDS:
        raise HTTPException(
            status_code=400,
            detail=f"Nederīgs kārtošanas lauks: '{sort}'. Atļautie: {', '.join(sorted(VALID_SORT_FIELDS))}",
        )
    if order not in ("asc", "desc"):
        raise HTTPException(
            status_code=400,
            detail=f"Nederīga kārtošanas secība: '{order}'. Atļautās: asc, desc",
        )

    query = db.query(Document)

    if importance is not None:
        query = query.filter(Document.importance == importance)
    if category is not None:
        query = query.filter(Document.category == category)
    if active is not None:
        query = query.filter(Document.active == active)
    if created_from is not None:
        query = query.filter(Document.created_at >= _parse_date(created_from, "created_from"))
    if created_to is not None:
        query = query.filter(Document.created_at <= _parse_date(created_to, "created_to"))

    # Svarīgumam izmanto loģisko secību, nevis alfabētisko
    sort_expr = IMPORTANCE_ORDER if sort == "importance" else getattr(Document, sort)
    query = query.order_by(sort_expr.asc() if order == "asc" else sort_expr.desc())

    return query.offset(offset).limit(limit).all()
