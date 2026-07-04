import { useState } from "react";
import { Loader2 } from "lucide-react";
import { api } from "../services/api.js";

const TOOLS = [
  { key: "summary", label: "Summary", fn: (id) => api.summarize(id).then((r) => r.summary) },
  { key: "keywords", label: "Keywords", fn: (id) => api.keywords(id).then((r) => r.keywords.join(", ")) },
  { key: "contributions", label: "Contributions", fn: (id) => api.contributions(id).then((r) => r.contributions) },
  { key: "limitations", label: "Limitations", fn: (id) => api.limitations(id).then((r) => r.limitations) },
  { key: "future_work", label: "Future Work", fn: (id) => api.futureWork(id).then((r) => r.future_work) },
  { key: "notes", label: "Reading Notes", fn: (id) => api.readingNotes(id).then((r) => r.notes) },
  { key: "quiz", label: "Quiz", fn: (id) => api.quiz(id).then((r) => r.quiz) },
  {
    key: "related",
    label: "Related Papers",
    fn: (id) =>
      api.related(id).then((r) =>
        r.related.length
          ? r.related.map((p) => `${p.title} (similarity ${p.similarity_score})`).join("\n")
          : "No other ready papers to compare against yet."
      ),
  },
];

export default function AnalysisPanel({ paper }) {
  const [active, setActive] = useState(null);
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(false);

  const run = async (tool) => {
    if (!paper) return;
    setActive(tool.key);
    setLoading(true);
    setResult("");
    try {
      const text = await tool.fn(paper.id);
      setResult(text);
    } catch (err) {
      setResult(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col">
      <div className="flex flex-wrap gap-2 mb-4">
        {TOOLS.map((tool) => (
          <button
            key={tool.key}
            onClick={() => run(tool)}
            disabled={!paper}
            className={`text-xs font-mono px-3 py-1.5 rounded-full border transition-colors
              ${active === tool.key ? "bg-indigo text-paper border-indigo" : "border-rule text-ink-soft hover:border-indigo/50"}
              disabled:opacity-40 disabled:cursor-not-allowed`}
          >
            {tool.label}
          </button>
        ))}
      </div>
      <div className="flex-1 overflow-y-auto bg-white/50 border border-rule rounded-card p-4">
        {!paper && <p className="text-ink-soft text-sm italic">Select a paper to run analysis tools.</p>}
        {paper && !active && <p className="text-ink-soft text-sm italic">Choose a tool above.</p>}
        {loading && (
          <div className="flex items-center gap-2 text-ink-soft text-sm font-mono">
            <Loader2 size={14} className="animate-spin" /> generating…
          </div>
        )}
        {!loading && result && (
          <p className="font-display text-sm text-ink whitespace-pre-wrap leading-relaxed">{result}</p>
        )}
      </div>
    </div>
  );
}
