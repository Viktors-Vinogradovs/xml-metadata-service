"""Dokumentu importa serviss: XML ielāde no attālā avota un saglabāšana DB."""

import httpx
from sqlalchemy.orm import Session

from app.models import Document
from app.parser import parse_documents_xml


def load_remote_xml(remote_url: str, timeout: float = 10.0) -> str:
    """Ielādē XML saturu no attālā URL."""
    response = httpx.get(remote_url, timeout=timeout)
    response.raise_for_status()
    return response.text


def import_documents(xml_text: str, db: Session) -> int:
    """Parsē XML un veic upsert pēc URL; atgriež importēto dokumentu skaitu."""
    parsed = parse_documents_xml(xml_text)
    count = 0

    for doc_data in parsed:
        data = doc_data.model_dump()
        existing = db.query(Document).filter(Document.url == data["url"]).first()

        if existing:
            for key, value in data.items():
                setattr(existing, key, value)
        else:
            db.add(Document(**data))

        count += 1

    db.commit()
    return count
