import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db import get_db
from app.import_service import import_documents, load_remote_xml

router = APIRouter(prefix="/api", tags=["documents"])

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
REMOTE_URL = os.getenv(
    "REMOTE_URL", "http://localhost:8000/api/remote/documents.xml"
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
