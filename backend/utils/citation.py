"""
Citation engine.

Turns a RetrievedChunk into a structured citation the frontend can render,
guaranteeing every generated answer is traceable back to paper, section,
page, and similarity score.
"""

from models.schemas import CitationOut
from retrieval.retriever import RetrievedChunk

SNIPPET_LEN = 220


def build_citation(chunk: RetrievedChunk) -> CitationOut:
    snippet = chunk.text[:SNIPPET_LEN]
    if len(chunk.text) > SNIPPET_LEN:
        snippet = snippet.rsplit(" ", 1)[0] + "…"

    return CitationOut(
        paper_id=chunk.paper_id,
        paper_title=chunk.paper_title,
        section=chunk.section,
        page_number=chunk.page_number,
        similarity_score=round(chunk.similarity_score, 4),
        snippet=snippet,
    )


def build_citations(chunks: list[RetrievedChunk]) -> list[CitationOut]:
    return [build_citation(c) for c in chunks]
