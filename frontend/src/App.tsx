import { useEffect, useState } from "react";
import { type Document, type DocumentParams, fetchDocuments, importDocuments } from "./api";
import "./App.css";

const CATEGORIES = ["", "public", "internal", "restricted", "confidential"];
const CATEGORY_LABELS: Record<string, string> = {
  "": "Visas kategorijas",
  public: "Publisks",
  internal: "Iekšējs",
  restricted: "Ierobežotas pieejamības",
  confidential: "Konfidenciāls",
};

const IMPORTANCE_LABELS: Record<string, string> = {
  low: "Zems",
  medium: "Vidējs",
  high: "Augsts",
  critical: "Kritisks",
};

const SORT_OPTIONS = [
  { value: "created_at", label: "Datums" },
  { value: "title", label: "Nosaukums" },
  { value: "importance", label: "Svarīgums" },
];

function App() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [category, setCategory] = useState("");
  const [active, setActive] = useState("");
  const [sortField, setSortField] = useState("created_at");
  const [sortOrder, setSortOrder] = useState<"desc" | "asc">("desc");
  const [createdFrom, setCreatedFrom] = useState("");
  const [createdTo, setCreatedTo] = useState("");
  const [importing, setImporting] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: DocumentParams = {
        sort: sortField,
        order: sortOrder,
      };
      if (category) params.category = category;
      if (active) params.active = active;
      if (createdFrom) params.created_from = createdFrom;
      if (createdTo) params.created_to = createdTo;
      setDocuments(await fetchDocuments(params));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Nezināma kļūda");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [category, active, sortField, sortOrder, createdFrom, createdTo]);

  const handleImport = async () => {
    setImporting(true);
    setError(null);
    try {
      const result = await importDocuments();
      alert(`Importēti ${result.imported} dokumenti`);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Importa kļūda");
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="container">
      <h1>Dokumentu metadati</h1>

      <div className="controls">
        <button onClick={handleImport} disabled={importing}>
          {importing ? "Importē..." : "Importēt datus"}
        </button>

        <select value={category} onChange={(e) => setCategory(e.target.value)}>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {CATEGORY_LABELS[c]}
            </option>
          ))}
        </select>

        <select value={active} onChange={(e) => setActive(e.target.value)}>
          <option value="">Visi statusi</option>
          <option value="true">Aktīvie</option>
          <option value="false">Neaktīvie</option>
        </select>

        <select value={sortField} onChange={(e) => setSortField(e.target.value)}>
          {SORT_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>

        <button onClick={() => setSortOrder((o) => (o === "desc" ? "asc" : "desc"))}>
          {sortOrder === "desc" ? "▼ Dilstoši" : "▲ Augoši"}
        </button>
      </div>

      <div className="controls">
        <label className="date-label">
          No:
          <input
            type="date"
            value={createdFrom}
            onChange={(e) => setCreatedFrom(e.target.value)}
          />
        </label>
        <label className="date-label">
          Līdz:
          <input
            type="date"
            value={createdTo}
            onChange={(e) => setCreatedTo(e.target.value)}
          />
        </label>
        {(createdFrom || createdTo) && (
          <button onClick={() => { setCreatedFrom(""); setCreatedTo(""); }}>
            Notīrīt datumus
          </button>
        )}
      </div>

      {error && <div className="error">{error}</div>}

      {loading ? (
        <p className="loading">Ielādē...</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Nosaukums</th>
              <th>Atbildīgā vienība</th>
              <th>Izveidots</th>
              <th>Svarīgums</th>
              <th>Kategorija</th>
              <th>Aktīvs</th>
              <th>Tips</th>
              <th>Dokuments</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((doc) => (
              <tr key={doc.id} className={doc.active ? "" : "inactive"}>
                <td>{doc.title}</td>
                <td>{doc.responsible_unit}</td>
                <td>{doc.created_at}</td>
                <td>
                  <span className={`badge importance-${doc.importance}`}>
                    {IMPORTANCE_LABELS[doc.importance] ?? doc.importance}
                  </span>
                </td>
                <td>{CATEGORY_LABELS[doc.category] ?? doc.category}</td>
                <td>{doc.active ? "Jā" : "Nē"}</td>
                <td><span className="badge file-type">{doc.file_type.toUpperCase()}</span></td>
                <td>
                  <a href={doc.url} target="_blank" rel="noopener noreferrer">
                    Atvērt ↗
                  </a>
                </td>
              </tr>
            ))}
            {documents.length === 0 && (
              <tr>
                <td colSpan={8} className="empty">Nav dokumentu</td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default App;
