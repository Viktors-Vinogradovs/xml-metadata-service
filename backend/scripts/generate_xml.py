"""XML dokumentu metadatu ģenerators."""

import argparse
import random
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from pathlib import Path

TITLES = [
    "Gada pārskats",
    "Projekta plāns",
    "Budžeta tāme",
    "Drošības politika",
    "Personāla rokasgrāmata",
    "IT infrastruktūras audits",
    "Klientu aptaujas rezultāti",
    "Datu aizsardzības noteikumi",
    "Iepirkumu procedūra",
    "Apmācību programma",
    "Kvalitātes vadības sistēma",
    "Risku novērtējums",
    "Stratēģiskais plāns",
    "Iekšējā audita ziņojums",
    "Komunikācijas stratēģija",
]

UNITS = [
    "Finanšu departaments",
    "IT nodaļa",
    "Personāla nodaļa",
    "Juridiskā nodaļa",
    "Mārketinga nodaļa",
    "Drošības nodaļa",
    "Kvalitātes nodaļa",
    "Projektu vadība",
]

FILE_TYPES = ["pdf", "docx", "xlsx", "html"]
IMPORTANCE_LEVELS = ["zems", "vidējs", "augsts", "kritisks"]
CATEGORIES = ["publisks", "iekšējs", "ierobežotas pieejamības", "konfidenciāls"]


def generate_document(doc_id: int, rng: random.Random) -> ET.Element:
    doc = ET.Element("document")

    title_base = rng.choice(TITLES)
    # Pievieno gadu virsrakstam, lai katrs dokuments būtu unikālāks
    year = rng.randint(2019, 2026)
    ET.SubElement(doc, "title").text = f"{title_base} {year}"

    ET.SubElement(doc, "description").text = (
        f"Dokuments nr. {doc_id}: {title_base.lower()} — "
        f"sagatavots {year}. gadā."
    )

    ET.SubElement(doc, "responsible_unit").text = rng.choice(UNITS)

    start = date(2019, 1, 1)
    offset = rng.randint(0, (date(2026, 1, 1) - start).days)
    created = start + timedelta(days=offset)
    ET.SubElement(doc, "created_at").text = created.isoformat()

    file_type = rng.choice(FILE_TYPES)
    ET.SubElement(doc, "url").text = (
        f"https://example.com/docs/{doc_id:04d}.{file_type}"
    )
    ET.SubElement(doc, "file_type").text = file_type

    ET.SubElement(doc, "reading_time_minutes").text = str(rng.randint(1, 120))
    ET.SubElement(doc, "importance").text = rng.choice(IMPORTANCE_LEVELS)
    ET.SubElement(doc, "category").text = rng.choice(CATEGORIES)
    ET.SubElement(doc, "active").text = rng.choice(["jā", "nē"])

    return doc


def generate_xml(n: int, seed: int | None = None) -> str:
    rng = random.Random(seed)
    root = ET.Element("documents")

    for i in range(1, n + 1):
        root.append(generate_document(i, rng))

    raw = ET.tostring(root, encoding="unicode", xml_declaration=False)
    # minidom formatē XML ar atkāpēm lasāmībai
    pretty = minidom.parseString(raw).toprettyxml(indent="  ", encoding=None)
    # Noņem minidom pievienoto XML deklarāciju — pievienosim savu
    lines = pretty.splitlines()
    body = "\n".join(lines[1:])
    return f'<?xml version="1.0" encoding="UTF-8"?>\n{body}\n'


def main():
    parser = argparse.ArgumentParser(description="Ģenerē XML testa datus")
    parser.add_argument("-n", type=int, default=50, help="Dokumentu skaits")
    parser.add_argument("--seed", type=int, default=None, help="Nejaušības sēkla")
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Izvades faila ceļš (noklusējums: backend/data/documents.xml)",
    )
    args = parser.parse_args()

    xml_content = generate_xml(args.n, args.seed)

    if args.output:
        out_path = Path(args.output)
    else:
        out_path = Path(__file__).resolve().parent.parent / "data" / "documents.xml"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(xml_content, encoding="utf-8")
    print(f"Generated {args.n} documents -> {out_path}")


if __name__ == "__main__":
    main()
