from preprocessing.text_cleaner import TextCleaner


def test_dehyphenation_across_line_breaks():
    cleaner = TextCleaner()
    raw = "This is a trans-\nformer model."
    assert "transformer" in cleaner.clean(raw)
    assert "trans-\nformer" not in cleaner.clean(raw)


def test_collapses_single_newlines_but_keeps_paragraph_breaks():
    cleaner = TextCleaner()
    raw = "First line\nsecond line\n\nNew paragraph."
    cleaned = cleaner.clean(raw)
    assert "First line second line" in cleaned
    assert "\n\n" in cleaned


def test_strips_stray_page_number_lines():
    cleaner = TextCleaner()
    raw = "Some content.\n12\nMore content."
    cleaned = cleaner.clean(raw)
    assert "\n12\n" not in cleaned


def test_detect_section_recognizes_common_headings():
    cleaner = TextCleaner()
    assert cleaner.detect_section("Introduction") == "Introduction"
    assert cleaner.detect_section("2. Methodology") == "Methodology"
    assert cleaner.detect_section("ABSTRACT") == "Abstract"


def test_detect_section_returns_none_for_body_text():
    cleaner = TextCleaner()
    assert cleaner.detect_section("This is a regular sentence about attention.") is None


def test_tag_sections_splits_on_headings():
    cleaner = TextCleaner()
    raw = "Title line\n\nIntroduction\nSome intro text.\n\nMethodology\nSome method text."
    segments = cleaner.tag_sections(raw)
    section_names = [s for s, _ in segments]
    assert "Introduction" in section_names
    assert "Methodology" in section_names
