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
    <importance>kritisks</importance>
    <category>iekšējs</category>
    <active>jā</active>
  </document>
  <document>
    <title>Delta dokuments</title>
    <description>Apraksts D</description>
    <responsible_unit>Drošības nodaļa</responsible_unit>
    <created_at>2024-03-10</created_at>
    <url>https://example.com/docs/d.html</url>
    <file_type>html</file_type>
    <reading_time_minutes>15</reading_time_minutes>
    <importance>vidējs</importance>
    <category>konfidenciāls</category>
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
        assert len(resp.json()) == 4

    def test_empty_db_returns_empty_list(self):
        resp = client.get("/api/documents")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_filter_by_active_true(self):
        _seed_db()
        resp = client.get("/api/documents", params={"active": "true"})
        data = resp.json()
        assert len(data) == 3
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
        assert len(data) == 1
        assert data[0]["importance"] == "high"

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
            params={"category": "internal", "active": "true"},
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
        assert len(offset_docs) == 3
        assert offset_docs[0]["id"] == all_docs[1]["id"]

    def test_documents_have_id(self):
        _seed_db()
        data = client.get("/api/documents").json()
        assert all("id" in d for d in data)

    def test_filter_no_match_returns_empty(self):
        _seed_db()
        resp = client.get("/api/documents", params={"importance": "nonexistent"})
        assert resp.json() == []


class TestImportanceSorting:
    """Svarīguma kārtošana pēc loģiskās prioritātes: low < medium < high < critical."""

    def test_importance_sort_asc(self):
        _seed_db()
        data = client.get(
            "/api/documents", params={"sort": "importance", "order": "asc"}
        ).json()
        levels = [d["importance"] for d in data]
        assert levels == ["low", "medium", "high", "critical"]

    def test_importance_sort_desc(self):
        _seed_db()
        data = client.get(
            "/api/documents", params={"sort": "importance", "order": "desc"}
        ).json()
        levels = [d["importance"] for d in data]
        assert levels == ["critical", "high", "medium", "low"]


class TestDateRangeFiltering:
    def test_created_from(self):
        _seed_db()
        data = client.get(
            "/api/documents", params={"created_from": "2024-01-01"}
        ).json()
        assert all(d["created_at"] >= "2024-01-01" for d in data)
        assert len(data) == 3

    def test_created_to(self):
        _seed_db()
        data = client.get(
            "/api/documents", params={"created_to": "2024-01-01"}
        ).json()
        assert all(d["created_at"] <= "2024-01-01" for d in data)
        assert len(data) == 1

    def test_date_range_both(self):
        _seed_db()
        data = client.get(
            "/api/documents",
            params={"created_from": "2024-01-01", "created_to": "2024-12-31"},
        ).json()
        assert len(data) == 2
        assert all("2024-01-01" <= d["created_at"] <= "2024-12-31" for d in data)

    def test_date_range_no_match(self):
        _seed_db()
        data = client.get(
            "/api/documents",
            params={"created_from": "2026-01-01", "created_to": "2026-12-31"},
        ).json()
        assert data == []

    def test_invalid_date_format_returns_400(self):
        _seed_db()
        resp = client.get("/api/documents", params={"created_from": "01-2024-15"})
        assert resp.status_code == 400
        assert "created_from" in resp.json()["detail"]

    def test_invalid_date_to_returns_400(self):
        _seed_db()
        resp = client.get("/api/documents", params={"created_to": "not-a-date"})
        assert resp.status_code == 400
        assert "created_to" in resp.json()["detail"]


class TestValidation:
    def test_invalid_sort_field_returns_400(self):
        _seed_db()
        resp = client.get("/api/documents", params={"sort": "nonexistent"})
        assert resp.status_code == 400
        assert "nonexistent" in resp.json()["detail"]

    def test_invalid_order_returns_400(self):
        _seed_db()
        resp = client.get("/api/documents", params={"order": "random"})
        assert resp.status_code == 400

    def test_sort_by_active_works(self):
        _seed_db()
        data = client.get(
            "/api/documents", params={"sort": "active", "order": "asc"}
        ).json()
        assert data[0]["active"] is False


class TestImportEndpoint:
    def test_import_via_local_xml(self):
        """Simulē attālo XML ielādi, aizstājot HTTP izsaukumu ar lokālo failu."""
        xml_path = Path(__file__).resolve().parent.parent / "data" / "documents.xml"
        xml_content = xml_path.read_text(encoding="utf-8")

        with patch("app.routes.load_remote_xml", return_value=xml_content):
            resp = client.post("/api/import")

        assert resp.status_code == 200
        assert resp.json()["imported"] > 0
