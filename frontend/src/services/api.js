const BASE = "/api";

async function handle(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  // Papers
  listPapers: () => fetch(`${BASE}/papers`).then(handle),
  getPaper: (id) => fetch(`${BASE}/papers/${id}`).then(handle),
  deletePaper: (id) => fetch(`${BASE}/papers/${id}`, { method: "DELETE" }).then(handle),
  uploadPaper: (file) => {
    const form = new FormData();
    form.append("file", file);
    return fetch(`${BASE}/papers/upload`, { method: "POST", body: form }).then(handle);
  },
  updateProgress: (id, progress) =>
    fetch(`${BASE}/papers/${id}/progress?progress=${progress}`, { method: "PATCH" }).then(handle),

  // Notes
  listNotes: (paperId) => fetch(`${BASE}/papers/${paperId}/notes`).then(handle),
  createNote: (paperId, title, content) =>
    fetch(`${BASE}/papers/notes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ paper_id: paperId, title, content }),
    }).then(handle),

  // Chat + search
  chat: (query, paperId, topK = 5) =>
    fetch(`${BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, paper_id: paperId, top_k: topK }),
    }).then(handle),
  search: (q, paperId) =>
    fetch(`${BASE}/search?q=${encodeURIComponent(q)}${paperId ? `&paper_id=${paperId}` : ""}`).then(handle),

  // Analysis
  summarize: (paperId, length = "medium") =>
    fetch(`${BASE}/analysis/summarize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ paper_id: paperId, length }),
    }).then(handle),
  compare: (paperIdA, paperIdB) =>
    fetch(`${BASE}/analysis/compare`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ paper_id_a: paperIdA, paper_id_b: paperIdB }),
    }).then(handle),
  explain: (paperId, paragraph) =>
    fetch(`${BASE}/analysis/explain`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ paper_id: paperId, paragraph }),
    }).then(handle),
  keywords: (paperId) => fetch(`${BASE}/analysis/${paperId}/keywords`).then(handle),
  contributions: (paperId) => fetch(`${BASE}/analysis/${paperId}/contributions`).then(handle),
  limitations: (paperId) => fetch(`${BASE}/analysis/${paperId}/limitations`).then(handle),
  futureWork: (paperId) => fetch(`${BASE}/analysis/${paperId}/future-work`).then(handle),
  readingNotes: (paperId) => fetch(`${BASE}/analysis/${paperId}/notes-auto`).then(handle),
  quiz: (paperId, numQuestions = 5) =>
    fetch(`${BASE}/analysis/${paperId}/quiz?num_questions=${numQuestions}`).then(handle),
  related: (paperId) => fetch(`${BASE}/analysis/${paperId}/related`).then(handle),
};
