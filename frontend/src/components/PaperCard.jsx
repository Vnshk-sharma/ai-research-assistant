import { FileText, Trash2 } from "lucide-react";

const STATUS_STYLES = {
  ready: "text-indigo",
  processing: "text-sienna animate-pulse",
  failed: "text-red-600",
};

export default function PaperCard({ paper, active, onSelect, onDelete }) {
  return (
    <div
      onClick={() => onSelect(paper)}
      className={`group relative border-l-4 pl-3 py-2.5 pr-2 cursor-pointer rounded-r-card transition-colors
        ${active ? "border-sienna bg-sienna/5" : "border-rule hover:border-indigo/50 hover:bg-black/[0.02]"}`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="font-display text-sm text-ink truncate">{paper.title || paper.filename}</p>
          <p className="text-xs text-ink-soft font-mono truncate mt-0.5">
            {paper.authors || "Unknown authors"} {paper.year && `· ${paper.year}`}
          </p>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete(paper.id);
          }}
          className="opacity-0 group-hover:opacity-100 transition-opacity text-ink-soft hover:text-sienna"
          aria-label={`Delete ${paper.title}`}
        >
          <Trash2 size={14} />
        </button>
      </div>
      <div className="flex items-center gap-2 mt-1.5 text-[11px] font-mono">
        <FileText size={11} className="text-ink-soft" />
        <span className={STATUS_STYLES[paper.status] || "text-ink-soft"}>{paper.status}</span>
        {paper.reading_progress > 0 && (
          <span className="text-ink-soft">· {paper.reading_progress}% read</span>
        )}
      </div>
    </div>
  );
}
