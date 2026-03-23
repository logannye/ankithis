from ankithis_api.services.section_annotator import annotate_section


def test_definitions_section():
    result = annotate_section("Key Definitions", "A receptor is defined as a protein...")
    assert result == "definitions"


def test_methodology_section():
    assert annotate_section("Methods", "The protocol involves three steps...") == "methodology"


def test_theory_section():
    assert annotate_section("Theoretical Framework", "The mechanism by which...") == "theory"


def test_examples_section():
    result = annotate_section("Case Study: Patient X", "Consider the following example...")
    assert result == "examples"


def test_data_results_section():
    assert annotate_section("Results", "Figure 3 shows that p < 0.01...") == "data_results"


def test_summary_section():
    assert annotate_section("Summary", "In summary, the key takeaways are...") == "summary"


def test_code_section():
    assert annotate_section("Implementation", "```python\ndef calculate():...") == "code"


def test_enumeration_section():
    body = "- High specificity\n- Catalytic efficiency\n- Regulated activity"
    assert annotate_section("Properties of Enzymes", body) == "enumeration"


def test_unknown_fallback():
    result = annotate_section("Chapter 4", "The quick brown fox jumps over the lazy dog.")
    assert result == "unknown"


def test_none_title():
    assert annotate_section(None, "This is defined as something important.") == "definitions"
