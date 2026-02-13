"""XML dokumentu metadatu parsēšana ar latviešu→angļu vērtību kartēšanu."""

import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

# --- Kartēšanas vārdnīcas: latviešu XML vērtības → kanoniskās DB vērtības ---

IMPORTANCE_MAP: dict[str, str] = {
    "zems": "low",
    "vidējs": "medium",
    "augsts": "high",
    "kritisks": "critical",
}

CATEGORY_MAP: dict[str, str] = {
    "publisks": "public",
    "iekšējs": "internal",
    "ierobežotas pieejamības": "restricted",
    "konfidenciāls": "confidential",
}

ACTIVE_MAP: dict[str, bool] = {
    "jā": True,
    "nē": False,
}

VALID_FILE_TYPES = {"pdf", "docx", "xlsx", "html"}


def _required_text(element: ET.Element, tag: str) -> str:
    """Nolasa obligāta elementa tekstu; ceļ kļūdu, ja trūkst."""
    child = element.find(tag)
    if child is None or not child.text:
        raise ValueError(f"Trūkst obligātā lauka: <{tag}>")
    return child.text.strip()


def _map_enum(value: str, mapping: dict, field_name: str):
    """Pārveido latviešu vērtību uz kanonisko; validē pret atļauto kopu."""
    if value not in mapping:
        allowed = ", ".join(mapping.keys())
        raise ValueError(
            f"Nederīga vērtība laukam '{field_name}': '{value}'. "
            f"Atļautās: {allowed}"
        )
    return mapping[value]


def parse_document(elem: ET.Element) -> dict:
    """Parsē vienu <document> elementu; atgriež vārdnīcu ar kanoniskām vērtībām."""
    file_type = _required_text(elem, "file_type")
    if file_type not in VALID_FILE_TYPES:
        raise ValueError(
            f"Nederīgs file_type: '{file_type}'. "
            f"Atļautie: {', '.join(VALID_FILE_TYPES)}"
        )

    reading_time = _required_text(elem, "reading_time_minutes")
    if not reading_time.isdigit():
        raise ValueError(f"reading_time_minutes nav vesels skaitlis: '{reading_time}'")

    return {
        "title": _required_text(elem, "title"),
        "description": _required_text(elem, "description"),
        "responsible_unit": _required_text(elem, "responsible_unit"),
        "created_at": date.fromisoformat(_required_text(elem, "created_at")),
        "url": _required_text(elem, "url"),
        "file_type": file_type,
        "reading_time_minutes": int(reading_time),
        "importance": _map_enum(
            _required_text(elem, "importance"), IMPORTANCE_MAP, "importance"
        ),
        "category": _map_enum(
            _required_text(elem, "category"), CATEGORY_MAP, "category"
        ),
        "active": _map_enum(
            _required_text(elem, "active"), ACTIVE_MAP, "active"
        ),
    }


def parse_xml(source: str | Path) -> list[dict]:
    """Parsē XML failu vai tekstu; atgriež dokumentu sarakstu."""
    if isinstance(source, Path):
        tree = ET.parse(source)
        root = tree.getroot()
    else:
        root = ET.fromstring(source)

    documents = []
    for i, elem in enumerate(root.findall("document"), start=1):
        try:
            documents.append(parse_document(elem))
        except ValueError as e:
            raise ValueError(f"Kļūda dokumentā #{i}: {e}") from e

    return documents
