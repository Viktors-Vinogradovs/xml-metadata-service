"""Testi XML parsēšanas modulim."""

from datetime import date

import pytest

from app.parser import parse_documents_xml
from app.schemas import DocumentCreate

# --- Palīgdati ---

VALID_DOC_XML = """\
<documents>
  <document>
    <title>Testa dokuments</title>
    <description>Apraksts</description>
    <responsible_unit>IT nodaļa</responsible_unit>
    <created_at>2024-03-15</created_at>
    <url>https://example.com/docs/0001.pdf</url>
    <file_type>pdf</file_type>
    <reading_time_minutes>10</reading_time_minutes>
    <importance>augsts</importance>
    <category>iekšējs</category>
    <active>jā</active>
  </document>
  <document>
    <title>Otrs dokuments</title>
    <description>Otrs apraksts</description>
    <responsible_unit>Juridiskā nodaļa</responsible_unit>
    <created_at>2023-01-01</created_at>
    <url>https://example.com/docs/0002.docx</url>
    <file_type>docx</file_type>
    <reading_time_minutes>45</reading_time_minutes>
    <importance>zems</importance>
    <category>publisks</category>
    <active>nē</active>
  </document>
</documents>
"""


class TestParseDocumentsXml:
    def test_valid_xml_returns_correct_count(self):
        result = parse_documents_xml(VALID_DOC_XML)
        assert len(result) == 2

    def test_returns_document_create_instances(self):
        result = parse_documents_xml(VALID_DOC_XML)
        assert all(isinstance(doc, DocumentCreate) for doc in result)

    def test_latvian_importance_mapped_to_english(self):
        result = parse_documents_xml(VALID_DOC_XML)
        assert result[0].importance == "high"
        assert result[1].importance == "low"

    def test_latvian_category_mapped_to_english(self):
        result = parse_documents_xml(VALID_DOC_XML)
        assert result[0].category == "internal"
        assert result[1].category == "public"

    def test_latvian_active_mapped_to_bool(self):
        result = parse_documents_xml(VALID_DOC_XML)
        assert result[0].active is True
        assert result[1].active is False

    def test_created_at_parsed_as_date(self):
        result = parse_documents_xml(VALID_DOC_XML)
        assert result[0].created_at == date(2024, 3, 15)

    def test_reading_time_parsed_as_int(self):
        result = parse_documents_xml(VALID_DOC_XML)
        assert result[0].reading_time_minutes == 10

    def test_scalar_fields_preserved(self):
        result = parse_documents_xml(VALID_DOC_XML)
        doc = result[0]
        assert doc.title == "Testa dokuments"
        assert doc.description == "Apraksts"
        assert doc.responsible_unit == "IT nodaļa"
        assert doc.url == "https://example.com/docs/0001.pdf"
        assert doc.file_type == "pdf"

    def test_missing_required_field_raises_error(self):
        xml = """<documents><document>
            <title>Test</title>
        </document></documents>"""
        with pytest.raises(ValueError, match="Trūkst obligātā lauka"):
            parse_documents_xml(xml)

    def test_invalid_importance_raises_error(self):
        xml = VALID_DOC_XML.replace("augsts", "high")
        with pytest.raises(ValueError, match="Nederīga vērtība laukam 'importance'"):
            parse_documents_xml(xml)

    def test_invalid_category_raises_error(self):
        xml = VALID_DOC_XML.replace("iekšējs", "internal")
        with pytest.raises(ValueError, match="Nederīga vērtība laukam 'category'"):
            parse_documents_xml(xml)

    def test_invalid_active_raises_error(self):
        xml = VALID_DOC_XML.replace("jā", "true")
        with pytest.raises(ValueError, match="Nederīga vērtība laukam 'active'"):
            parse_documents_xml(xml)

    def test_invalid_file_type_raises_error(self):
        xml = VALID_DOC_XML.replace(">pdf<", ">exe<")
        with pytest.raises(ValueError, match="Nederīgs file_type"):
            parse_documents_xml(xml)

    def test_empty_documents_returns_empty_list(self):
        result = parse_documents_xml("<documents></documents>")
        assert result == []

    def test_invalid_xml_raises_error(self):
        with pytest.raises(Exception):
            parse_documents_xml("<not-valid-xml")
