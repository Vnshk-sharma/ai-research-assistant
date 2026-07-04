from preprocessing.chunker import SemanticChunker
from preprocessing.text_cleaner import TextCleaner


def test_chunk_text_respects_chunk_size_roughly():
    chunker = SemanticChunker(chunk_size=50, overlap=10)
    text = (
        "The Transformer is a model architecture. "
        "It relies entirely on attention mechanisms. "
        "It dispenses with recurrence and convolutions."
    )
    chunks = chunker.chunk_text(text, section="Body", page_number=1)
    assert len(chunks) >= 2
    for c in chunks:
        assert c.section == "Body"
        assert c.page_number == 1


def test_chunk_text_produces_overlap_between_consecutive_chunks():
    chunker = SemanticChunker(chunk_size=60, overlap=30)
    text = (
        "Sentence one is here. Sentence two follows. "
        "Sentence three continues. Sentence four wraps up. "
        "Sentence five ends it."
    )
    chunks = chunker.chunk_text(text, section="Body", page_number=None)
    assert len(chunks) >= 2
    # Some words from the end of chunk[i] should reappear at the start of chunk[i+1]
    first_words = set(chunks[0].text.split())
    second_words = set(chunks[1].text.split())
    assert first_words & second_words


def test_chunk_text_empty_input_returns_no_chunks():
    chunker = SemanticChunker()
    assert chunker.chunk_text("", section="Body", page_number=1) == []


def test_chunk_text_single_short_sentence_returns_one_chunk():
    chunker = SemanticChunker(chunk_size=800, overlap=150)
    chunks = chunker.chunk_text("A short sentence.", section="Abstract", page_number=1)
    assert len(chunks) == 1
    assert chunks[0].text == "A short sentence."


class _FakePage:
    def __init__(self, page_number, text):
        self.page_number = page_number
        self.text = text


def test_chunk_document_tags_sections_from_pages():
    chunker = SemanticChunker(chunk_size=200, overlap=40)
    cleaner = TextCleaner()
    pages = [
        _FakePage(
            1,
            "Abstract\nWe propose a new method for research paper analysis.\n\n"
            "Introduction\nPrior work has explored various NLP techniques.",
        )
    ]
    chunks = chunker.chunk_document(pages, cleaner)
    sections = {c.section for c in chunks}
    assert "Abstract" in sections
    assert "Introduction" in sections
