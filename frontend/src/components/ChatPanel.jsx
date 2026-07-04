import { useState, useRef, useEffect } from "react";
import { Send } from "lucide-react";
import ChatMessage from "./ChatMessage.jsx";
import { api } from "../services/api.js";

export default function ChatPanel({ paper, scope }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const send = async () => {
    const query = input.trim();
    if (!query || loading) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: query }]);
    setLoading(true);
    try {
      const paperId = scope === "this" ? paper?.id : null;
      const res = await api.chat(query, paperId);
      setMessages((m) => [...m, { role: "assistant", content: res.answer, citations: res.citations }]);
    } catch (err) {
      setMessages((m) => [...m, { role: "assistant", content: `Something went wrong: ${err.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto py-4">
        {messages.length === 0 && (
          <p className="text-ink-soft text-sm font-body italic">
            Ask a question about {scope === "this" && paper ? `"${paper.title}"` : "your uploaded papers"}.
          </p>
        )}
        {messages.map((m, i) => (
          <ChatMessage key={i} {...m} />
        ))}
        {loading && <p className="text-ink-soft text-xs font-mono animate-pulse">retrieving & reasoning…</p>}
        <div ref={bottomRef} />
      </div>
      <div className="flex items-center gap-2 rule-hairline pt-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="Ask about the methodology, results, related work…"
          className="flex-1 bg-white/70 border border-rule rounded-card px-3 py-2 text-sm
                     focus:outline-none focus:ring-2 focus:ring-indigo/40"
        />
        <button
          onClick={send}
          disabled={loading}
          className="bg-indigo text-paper rounded-card p-2.5 hover:bg-indigo-light transition-colors disabled:opacity-50"
          aria-label="Send"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  );
}
