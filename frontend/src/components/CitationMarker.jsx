import { useState } from "react";

/**
 * Renders a superscript footnote marker (e.g. "1") that, on hover or
 * keyboard focus, reveals a small card with the source paper, section,
 * page number, and similarity score — mirroring how a printed paper's
 * footnotes work, but interactive.
 */
export default function CitationMarker({ index, citation }) {
  const [open, setOpen] = useState(false);

  return (
    <span className="relative inline-block">
      <button
        type="button"
        className="footnote-marker"
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        aria-label={`Citation ${index}: ${citation.paper_title}`}
      >
        {index}
      </button>
      {open && (
        <div className="footnote-card bottom-6 left-0" role="tooltip">
          <div className="font-display text-ink text-sm mb-1">{citation.paper_title}</div>
          <div className="flex gap-2 font-mono text-[11px] text-ink-soft mb-2">
            {citation.section && <span>{citation.section}</span>}
            {citation.page_number != null && <span>· p.{citation.page_number}</span>}
            <span>· sim {citation.similarity_score}</span>
          </div>
          <p className="italic text-ink-soft">"{citation.snippet}"</p>
        </div>
      )}
    </span>
  );
}
