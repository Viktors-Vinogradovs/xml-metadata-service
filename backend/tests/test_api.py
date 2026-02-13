"""API galapunktu integrācijas testi."""

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.import_service import import_documents

# --- Testa DB atmiņā; StaticPool nodrošina vienu koplietotu savienojumu ---

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

SAMPLE_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<documents>
  <document>
    <title>Alfa dokuments</title>
    <description>Apraksts A</description>
    <responsible_unit>IT nodaļa</responsible_unit>
    <created_at>2024-06-01</created_at>
    <url>https://example.com/docs/a.pdf</url>
    <file_type>pdf</file_type>
    <reading_time_minutes>10</reading_time_minutes>
    <importance>augsts</importance>
    <category>iekšējs</category>
    <active>jā</active>
  </document>
  <document>
    <title>Beta dokuments</title>
    <description>Apraksts B</description>
    <responsible_unit>Juridiskā nodaļa</responsible_unit>
    <created_at>2023-01-15</created_at>
    <url>https://example.com/docs/b.docx</url>
    <file_type>docx</file_type>
    <reading_time_minutes>30</reading_time_minutes>
    <importance>zems</importance>
    <category>publisks</category>
    <active>nē</active>
  </document>
  <document>
    <title>Gamma dokuments</title>
    <description>Apraksts G</description>
    <responsible_unit>Finanšu departaments</responsible_unit>
    <created_at>2025-02-20</created_at>
    <url>https://example.com/docs/g.xlsx</url>
    <file_type>xlsx</file_type>
    <reading_time_minutes>5</reading_time_minutes>
    <importance>augsts</importance>
    <category>iekšējs</category>
    <active>jā</active>
  </document>
</documents>
"""


@pytest.fixture(autouse=True)
def setup_db():
    """Izveido tabulas pirms katra testa un notīra pēc."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


def _seed_db():
    """Importē testa datus tieši caur servisu."""
    db = TestSession()
    try:
        import_documents(SAMPLE_XML, db)
    finally:
        db.close()


class TestGetDocuments:
    def test_returns_imported_documents(self):
        _seed_db()
        resp = client.get("/api/documents")
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    def test_empty_db_returns_empty_list(self):
        resp = client.get("/api/documents")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_filter_by_active_true(self):
        _seed_db()
        resp = client.get("/api/documents", params={"active": "true"})
        data = resp.json()
        assert len(data) == 2
        assert all(d["active"] is True for d in data)

    def test_filter_by_active_false(self):
        _seed_db()
        resp = client.get("/api/documents", params={"active": "false"})
        data = resp.json()
        assert len(data) == 1
        assert data[0]["active"] is False

    def test_filter_by_importance(self):
        _seed_db()
        resp = client.get("/api/documents", params={"importance": "high"})
        data = resp.json()
        assert len(data) == 2
        assert all(d["importance"] == "high" for d in data)

    def test_filter_by_category(self):
        _seed_db()
        resp = client.get("/api/documents", params={"category": "public"})
        data = resp.json()
        assert len(data) == 1
        assert data[0]["category"] == "public"

    def test_combined_filters(self):
        _seed_db()
        resp = client.get(
            "/api/documents",
            params={"importance": "high", "active": "true"},
        )
        assert len(resp.json()) == 2

    def test_sort_created_at_desc_default(self):
        _seed_db()
        data = client.get("/api/documents").json()
        dates = [d["created_at"] for d in data]
        assert dates == sorted(dates, reverse=True)

    def test_sort_created_at_asc(self):
        _seed_db()
        data = client.get(
            "/api/documents", params={"sort": "created_at", "order": "asc"}
        ).json()
        dates = [d["created_at"] for d in data]
        assert dates == sorted(dates)

    def test_sort_title_asc(self):
        _seed_db()
        data = client.get(
            "/api/documents", params={"sort": "title", "order": "asc"}
        ).json()
        titles = [d["title"] for d in data]
        assert titles == sorted(titles)

    def test_limit(self):
        _seed_db()
        resp = client.get("/api/documents", params={"limit": 1})
        assert len(resp.json()) == 1

    def test_offset(self):
        _seed_db()
        all_docs = client.get("/api/documents").json()
        offset_docs = client.get("/api/documents", params={"offset": 1}).json()
        assert len(offset_docs) == 2
        assert offset_docs[0]["id"] == all_docs[1]["id"]

    def test_documents_have_id(self):
        _seed_db()
        data = client.get("/api/documents").json()
        assert all("id" in d for d in data)

    def test_filter_no_match_returns_empty(self):
        _seed_db()
        resp = client.get("/api/documents", params={"importance": "critical"})
        assert resp.json() == []


class TestImportEndpoint:
    def test_import_via_local_xml(self):
        """Simulē attālo XML ielādi, aizstājot HTTP izsaukumu ar lokālo failu."""
        xml_path = Path(__file__).resolve().parent.parent / "data" / "documents.xml"
        xml_content = xml_path.read_text(encoding="utf-8")

        with patch("app.routes.load_remote_xml", return_value=xml_content):
            resp = client.post("/api/import")

        assert resp.status_code == 200
        assert resp.json()["imported"] > 0
