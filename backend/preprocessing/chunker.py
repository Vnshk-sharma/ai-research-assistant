"""
Semantic chunking module.

Splits cleaned, section-tagged text into overlapping chunks that respect
sentence boundaries where possible, so embeddings capture coherent units
of meaning rather than arbitrary character windows.
"""

import re
from dataclasses import dataclass

from utils.config import settings

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z(\"'])")


@dataclass
class Chunk:
    text: str
    section: str
    page_number: int | None


class SemanticChunker:
    def __init__(self, chunk_size: int = None, overlap: int = None):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.overlap = overlap or settings.CHUNK_OVERLAP

    def _split_sentences(self, text: str) -> list[str]:
        sentences = _SENTENCE_SPLIT_RE.split(text)
        return [s.strip() for s in sentences if s.strip()]

    def chunk_text(self, text: str, section: str, page_number: int | None) -> list[Chunk]:
        """Greedily pack sentences into ~chunk_size windows with overlap."""
        sentences = self._split_sentences(text)
        if not sentences:
            return []

        chunks: list[Chunk] = []
        current: list[str] = []
        current_len = 0

        for sentence in sentences:
            if current_len + len(sentence) > self.chunk_size and current:
                chunk_text = " ".join(current)
                chunks.append(Chunk(text=chunk_text, section=section, page_number=page_number))

                # Build overlap: keep trailing sentences that fit within
                # `self.overlap` characters, to preserve context continuity.
                overlap_sentences = []
                overlap_len = 0
                for s in reversed(current):
                    if overlap_len + len(s) > self.overlap:
                        break
                    overlap_sentences.insert(0, s)
                    overlap_len += len(s)

                current = overlap_sentences
                current_len = overlap_len

            current.append(sentence)
            current_len += len(sentence)

        if current:
            chunks.append(Chunk(text=" ".join(current), section=section, page_number=page_number))

        return chunks

    def chunk_document(self, pages: list, cleaner) -> list[Chunk]:
        """
        Chunk an entire document. `pages` is a list of PageContent objects
        (page_number, text). Cleans + section-tags each page, then chunks.
        """
        all_chunks: list[Chunk] = []
        for page in pages:
            segments = cleaner.tag_sections(page.text)
            for section, raw_segment in segments:
                cleaned = cleaner.clean(raw_segment)
                if not cleaned:
                    continue
                all_chunks.extend(
                    self.chunk_text(cleaned, section=section, page_number=page.page_number)
                )
        return all_chunks
