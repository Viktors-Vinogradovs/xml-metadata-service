import { useEffect, useState } from "react";
import { type Document, type DocumentParams, fetchDocuments, importDocuments } from "./api";
import "./App.css";

// Kategoriju opcijas atbilst DB kanoniskajām vērtībām
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

function App() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [category, setCategory] = useState("");
  const [sortOrder, setSortOrder] = useState<"desc" | "asc">("desc");
  const [importing, setImporting] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: DocumentParams = {
        sort: "created_at",
        order: sortOrder,
      };
      if (category) params.category = category;
      setDocuments(await fetchDocuments(params));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Nezināma kļūda");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [category, sortOrder]);

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

        <button onClick={() => setSortOrder((o) => (o === "desc" ? "asc" : "desc"))}>
          Datums: {sortOrder === "desc" ? "jaunākie" : "vecākie"} ↕
        </button>
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
              <th>Saite</th>
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
                <td>
                  <a href={doc.url} target="_blank" rel="noopener noreferrer">
                    {doc.file_type.toUpperCase()}
                  </a>
                </td>
              </tr>
            ))}
            {documents.length === 0 && (
              <tr>
                <td colSpan={7} className="empty">Nav dokumentu</td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default App;
