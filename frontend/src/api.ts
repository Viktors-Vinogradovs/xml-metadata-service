export interface Document {
  id: number;
  title: string;
  description: string | null;
  responsible_unit: string;
  created_at: string;
  url: string;
  file_type: string;
  reading_time_minutes: number;
  importance: string;
  category: string;
  active: boolean;
}

export interface DocumentParams {
  category?: string;
  active?: string;
  sort?: string;
  order?: "asc" | "desc";
  created_from?: string;
  created_to?: string;
}

const BASE = "/api";

export async function fetchDocuments(
  params: DocumentParams = {}
): Promise<Document[]> {
  const query = new URLSearchParams();
  if (params.category) query.set("category", params.category);
  if (params.active) query.set("active", params.active);
  if (params.sort) query.set("sort", params.sort);
  if (params.order) query.set("order", params.order);
  if (params.created_from) query.set("created_from", params.created_from);
  if (params.created_to) query.set("created_to", params.created_to);

  const res = await fetch(`${BASE}/documents?${query}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function importDocuments(): Promise<{ imported: number }> {
  const res = await fetch(`${BASE}/import`, { method: "POST" });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
