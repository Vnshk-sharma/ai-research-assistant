"""
PDF extraction module.

Responsible for pulling raw text (per page), document metadata, and a
best-effort title/author guess out of a PDF using PyMuPDF (fitz).
"""

import re
from dataclasses import dataclass, field

import fitz  # PyMuPDF


@dataclass
class PageContent:
    page_number: int
    text: str


@dataclass
class ExtractedDocument:
    title: str
    authors: str
    year: str
    num_pages: int
    pages: list[PageContent] = field(default_factory=list)


class PDFExtractor:
    """Extracts text + metadata from a research paper PDF."""

    YEAR_PATTERN = re.compile(r"\b(19|20)\d{2}\b")

    # Boilerplate that commonly shows up as small print (copyright notices,
    # attribution/license footers, conference disclaimers, etc.) near the
    # top of page 1. These lines should never be mistaken for the title,
    # even if they happen to be extracted before the real title line.
    BOILERPLATE_PATTERNS = re.compile(
        r"("
        r"hereby grants permission|"
        r"all rights reserved|"
        r"copyright \xa9|copyright \(c\)|copyright \d|"
        r"proper attribution|"
        r"permission to (make|reproduce|copy)|"
        r"licensed under|"
        r"this paper is (a )?preprint|"
        r"arxiv:|"
        r"doi:|"
        r"proceedings of|"
        r"published as a conference paper|"
        r"under review|"
        r"^work in progress$"
        r")",
        re.IGNORECASE,
    )

    def extract(self, file_path: str) -> ExtractedDocument:
        doc = fitz.open(file_path)
        try:
            pages = [
                PageContent(page_number=i + 1, text=page.get_text("text"))
                for i, page in enumerate(doc)
            ]
            title, authors, year = self._extract_metadata(doc, pages)
            return ExtractedDocument(
                title=title,
                authors=authors,
                year=year,
                num_pages=len(pages),
                pages=pages,
            )
        finally:
            doc.close()

    def _is_boilerplate(self, line: str) -> bool:
        return bool(self.BOILERPLATE_PATTERNS.search(line))

    def _title_from_font_size(self, doc: "fitz.Document") -> str:
        """Pick the line with the largest font size in the upper portion of
        page 1 as the title. This is far more reliable than "first line of
        text", since raw text order can place small-print footers (license
        notices, copyright lines, etc.) before the actual title.
        """
        if len(doc) == 0:
            return ""

        page = doc[0]
        page_height = page.rect.height
        raw = page.get_text("dict")

        candidates = []  # (font_size, y_position, text)
        for block in raw.get("blocks", []):
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                if not spans:
                    continue
                text = "".join(s.get("text", "") for s in spans).strip()
                if not text or len(text) < 4:
                    continue
                if self._is_boilerplate(text):
                    continue
                # Only consider lines in the top half of the page, since
                # titles are almost always near the top.
                y = spans[0].get("bbox", [0, 0, 0, 0])[1]
                if y > page_height * 0.5:
                    continue
                # Ignore obvious running headers / page numbers.
                if len(text) < 8 and text.isdigit():
                    continue
                max_font = max(s.get("size", 0) for s in spans)
                candidates.append((max_font, -y, text))

        if not candidates:
            return ""

        # Prefer the largest font size; break ties by earliest (highest) on
        # the page.
        candidates.sort(key=lambda c: (c[0], c[1]), reverse=True)
        best_font = candidates[0][0]

        # A title sometimes wraps across two lines rendered at the same
        # font size and consecutively near the top - merge lines that share
        # (approximately) the top font size, in their original top-to-bottom
        # order, up to a reasonable length.
        top_lines = [c for c in candidates if abs(c[0] - best_font) < 0.5]
        top_lines.sort(key=lambda c: -c[1])  # restore top-to-bottom order
        merged = " ".join(c[2] for c in top_lines[:3])
        return merged[:200].strip()

    def _extract_metadata(self, doc: "fitz.Document", pages: list[PageContent]):
        meta = doc.metadata or {}
        title = (meta.get("title") or "").strip()
        authors = (meta.get("author") or "").strip()

        # PDF metadata title is sometimes present but garbage (e.g. the
        # source filename, "Microsoft Word - ...", or boilerplate) - treat
        # those the same as missing.
        if title and (self._is_boilerplate(title) or title.lower().endswith(".doc") or title.lower().endswith(".docx")):
            title = ""

        first_page_text = pages[0].text if pages else ""
        lines = [ln.strip() for ln in first_page_text.split("\n") if ln.strip()]

        if not title:
            # Primary heuristic: largest-font line(s) near the top of page 1.
            title = self._title_from_font_size(doc)

        if not title and lines:
            # Fallback: first non-boilerplate line, in case the font-size
            # heuristic found nothing usable (e.g. scanned/odd PDFs).
            for ln in lines:
                if not self._is_boilerplate(ln):
                    title = ln[:200]
                    break

        if not authors and len(lines) > 1:
            # Heuristic: an author line often follows the title and contains
            # commas or "and", and is shorter than a typical abstract line.
            for ln in lines[1:4]:
                if self._is_boilerplate(ln):
                    continue
                if ("," in ln or " and " in ln.lower()) and len(ln) < 200:
                    authors = ln
                    break

        year_match = self.YEAR_PATTERN.search(first_page_text)
        year = year_match.group(0) if year_match else ""

        return title or "Untitled Paper", authors or "Unknown Authors", year
