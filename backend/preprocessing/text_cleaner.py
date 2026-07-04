"""
Text cleaning + lightweight section detection.

Research PDFs extract with a lot of noise: hyphenation across line breaks,
repeated headers/footers, stray page numbers, ligature artifacts. This
module normalizes that text and tags likely section headings so downstream
chunking can attach a `section` label to each chunk.
"""

import re

COMMON_SECTIONS = [
    "abstract", "introduction", "related work", "background",
    "methodology", "methods", "approach", "experiments", "results",
    "discussion", "conclusion", "conclusions", "future work",
    "limitations", "references", "acknowledgements", "acknowledgments",
]

_SECTION_HEADER_RE = re.compile(
    r"^(?:\d+\.?\s*)?(" + "|".join(re.escape(s) for s in COMMON_SECTIONS) + r")\s*$",
    re.IGNORECASE,
)


class TextCleaner:
    def clean(self, text: str) -> str:
        # Re-join words split by a hyphen at a line break: "trans-\nformer" -> "transformer"
        text = re.sub(r"-\n(?=[a-z])", "", text)
        # Collapse remaining single newlines (mid-paragraph) into spaces,
        # but keep paragraph breaks (double newlines).
        text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
        # Strip stray page-number-only lines, e.g. "12" on its own line.
        text = re.sub(r"\n\s*\d{1,4}\s*\n", "\n", text)
        # Normalize whitespace.
        text = re.sub(r"[ \t]{2,}", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def detect_section(self, line: str) -> str | None:
        """Return a canonical section name if `line` looks like a heading."""
        match = _SECTION_HEADER_RE.match(line.strip())
        if match:
            return match.group(1).title()
        return None

    def tag_sections(self, raw_text: str) -> list[tuple[str, str]]:
        """
        Split raw (uncleaned) page text into (section, text) segments by
        scanning for heading-like lines.
        """
        segments: list[tuple[str, str]] = []
        current_section = "Body"
        buffer: list[str] = []

        for line in raw_text.split("\n"):
            section = self.detect_section(line)
            if section:
                if buffer:
                    segments.append((current_section, "\n".join(buffer)))
                    buffer = []
                current_section = section
            else:
                buffer.append(line)

        if buffer:
            segments.append((current_section, "\n".join(buffer)))

        return segments
