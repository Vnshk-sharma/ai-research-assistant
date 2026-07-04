import CitationMarker from "./CitationMarker.jsx";

export default function ChatMessage({ role, content, citations = [] }) {
  const isUser = role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={`max-w-[80%] px-4 py-3 rounded-card ${
          isUser
            ? "bg-indigo text-paper font-body"
            : "bg-white/60 border border-rule font-display text-ink"
        }`}
      >
        <p className="leading-relaxed whitespace-pre-wrap">
          {content}
          {!isUser &&
            citations.map((c, i) => (
              <CitationMarker key={i} index={i + 1} citation={c} />
            ))}
        </p>
      </div>
    </div>
  );
}
