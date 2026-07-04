import { useEffect, useState, useCallback } from "react";
import { BookOpen, MessageSquare, Sparkles } from "lucide-react";
import UploadZone from "./components/UploadZone.jsx";
import PaperCard from "./components/PaperCard.jsx";
import ChatPanel from "./components/ChatPanel.jsx";
import AnalysisPanel from "./components/AnalysisPanel.jsx";
import { api } from "./services/api.js";

const TABS = [
  { key: "chat", label: "Chat", icon: MessageSquare },
  { key: "analysis", label: "Tools", icon: Sparkles },
];

export default function App() {
  const [papers, setPapers] = useState([]);
  const [selected, setSelected] = useState(null);
  const [tab, setTab] = useState("chat");
  const [chatScope, setChatScope] = useState("this"); // "this" | "all"
  const [uploading, setUploading] = useState(false);

  const refreshPapers = useCallback(async () => {
    const list = await api.listPapers();
    setPapers(list);
    return list;
  }, []);

  useEffect(() => {
    refreshPapers();
  }, [refreshPapers]);

  // Poll while any paper is still processing, so the UI reflects
  // ingestion completing without a manual refresh.
  useEffect(() => {
    if (!papers.some((p) => p.status === "processing")) return;
    const id = setInterval(refreshPapers, 2500);
    return () => clearInterval(id);
  }, [papers, refreshPapers]);

  const handleUpload = async (file) => {
    setUploading(true);
    try {
      const paper = await api.uploadPaper(file);
      const list = await refreshPapers();
      setSelected(list.find((p) => p.id === paper.id) || paper);
    } catch (err) {
      alert(`Upload failed: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id) => {
    await api.deletePaper(id);
    if (selected?.id === id) setSelected(null);
    refreshPapers();
  };

  return (
    <div className="h-screen flex flex-col">
      <header className="border-b border-rule px-6 py-4 flex items-baseline gap-3">
        <BookOpen size={20} className="text-sienna" />
        <h1 className="font-display text-xl text-ink">Marginal</h1>
        <p className="text-ink-soft text-xs font-mono">an AI research assistant for reading papers closely</p>
      </header>

      <div className="flex flex-1 min-h-0">
        {/* Library sidebar */}
        <aside className="w-80 border-r border-rule flex flex-col p-4 min-h-0">
          <UploadZone onUpload={handleUpload} uploading={uploading} />
          <div className="flex-1 overflow-y-auto mt-4 space-y-1">
            {papers.map((p) => (
              <PaperCard
                key={p.id}
                paper={p}
                active={selected?.id === p.id}
                onSelect={setSelected}
                onDelete={handleDelete}
              />
            ))}
            {papers.length === 0 && (
              <p className="text-ink-soft text-xs italic mt-4">No papers uploaded yet.</p>
            )}
          </div>
        </aside>

        {/* Workspace */}
        <main className="flex-1 flex flex-col p-6 min-h-0">
          <div className="flex items-center justify-between mb-4">
            <div className="flex gap-1 bg-white/50 border border-rule rounded-full p-1">
              {TABS.map(({ key, label, icon: Icon }) => (
                <button
                  key={key}
                  onClick={() => setTab(key)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-mono transition-colors
                    ${tab === key ? "bg-indigo text-paper" : "text-ink-soft hover:text-ink"}`}
                >
                  <Icon size={13} /> {label}
                </button>
              ))}
            </div>

            {tab === "chat" && (
              <div className="flex gap-1 text-xs font-mono">
                <button
                  onClick={() => setChatScope("this")}
                  className={`px-2.5 py-1 rounded-full border ${
                    chatScope === "this" ? "border-sienna text-sienna" : "border-rule text-ink-soft"
                  }`}
                >
                  This paper
                </button>
                <button
                  onClick={() => setChatScope("all")}
                  className={`px-2.5 py-1 rounded-full border ${
                    chatScope === "all" ? "border-sienna text-sienna" : "border-rule text-ink-soft"
                  }`}
                >
                  All papers
                </button>
              </div>
            )}
          </div>

          <div className="flex-1 min-h-0">
            {tab === "chat" && <ChatPanel paper={selected} scope={chatScope} />}
            {tab === "analysis" && <AnalysisPanel paper={selected} />}
          </div>
        </main>
      </div>
    </div>
  );
}
