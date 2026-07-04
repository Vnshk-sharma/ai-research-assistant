import fitz
import pytest

from preprocessing.pdf_extractor import PDFExtractor


@pytest.fixture
def sample_pdf(tmp_path):
    doc = fitz.open()
    page = doc.new_page()
    text = (
        "Attention Is All You Need\n"
        "Ashwin V, Noam S, and others\n\n"
        "Abstract\n"
        "We propose a new simple network architecture, the Transformer.\n\n"
        "Introduction\n"
        "Recurrent neural networks have long been the dominant approach.\n"
    )
    page.insert_text((50, 50), text, fontsize=11)
    path = tmp_path / "sample.pdf"
    doc.save(str(path))
    doc.close()
    return str(path)


def test_extract_returns_correct_page_count(sample_pdf):
    extractor = PDFExtractor()
    result = extractor.extract(sample_pdf)
    assert result.num_pages == 1
    assert len(result.pages) == 1


def test_extract_finds_title_heuristically(sample_pdf):
    extractor = PDFExtractor()
    result = extractor.extract(sample_pdf)
    assert "Attention" in result.title


def test_extract_finds_year_when_present(tmp_path):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "A Paper Title\nAuthors, 2023\n\nAbstract\nSome text here.")
    path = tmp_path / "with_year.pdf"
    doc.save(str(path))
    doc.close()

    extractor = PDFExtractor()
    result = extractor.extract(str(path))
    assert result.year == "2023"


def test_extract_handles_missing_metadata_gracefully(tmp_path):
    doc = fitz.open()
    doc.new_page()  # blank page, no text at all
    path = tmp_path / "blank.pdf"
    doc.save(str(path))
    doc.close()

    extractor = PDFExtractor()
    result = extractor.extract(str(path))
    assert result.title  # falls back to "Untitled Paper"
    assert result.authors  # falls back to "Unknown Authors"
