"""Tests for LLM pipeline stages A-D with mocked structured_call."""

from unittest.mock import patch

from ankithis_api.models.enums import CardStyle, DeckSize


# --- Stage A: Concept Extraction ---

@patch("ankithis_api.services.stages.concept_extraction.structured_call")
def test_stage_a_extracts_concepts(mock_call):
    mock_call.return_value = {
        "concepts": [
            {
                "name": "Mitochondria function",
                "description": "Mitochondria are the powerhouse of the cell",
                "importance": 9,
                "source_quote": "mitochondria generate most of the cell's ATP",
            },
            {
                "name": "ATP synthesis",
                "description": "ATP is synthesized via oxidative phosphorylation",
                "importance": 8,
                "source_quote": "oxidative phosphorylation produces ATP",
            },
        ]
    }

    from ankithis_api.services.stages.concept_extraction import extract_concepts

    concepts = extract_concepts("The mitochondria generate most of the cell's ATP.")
    assert len(concepts) == 2
    assert concepts[0]["name"] == "Mitochondria function"
    assert concepts[0]["importance"] == 9
    mock_call.assert_called_once()


@patch("ankithis_api.services.stages.concept_extraction.structured_call")
def test_stage_a_with_study_goal(mock_call):
    mock_call.return_value = {"concepts": []}

    from ankithis_api.services.stages.concept_extraction import extract_concepts

    extract_concepts("Some text", study_goal="Focus on cell biology")
    call_args = mock_call.call_args
    assert "Focus on cell biology" in call_args.kwargs["user"]


# --- Stage B: Concept Merge ---

@patch("ankithis_api.services.stages.concept_merge.structured_call")
def test_stage_b_merges_concepts(mock_call):
    mock_call.return_value = {
        "concepts": [
            {
                "name": "Cell energy production",
                "description": "Mitochondria produce ATP via oxidative phosphorylation",
                "importance": 9,
                "merged_from": ["Mitochondria function", "ATP synthesis"],
            }
        ]
    }

    from ankithis_api.services.stages.concept_merge import merge_concepts

    input_concepts = [
        {"name": "Mitochondria function", "description": "...", "importance": 9},
        {"name": "ATP synthesis", "description": "...", "importance": 8},
    ]
    merged = merge_concepts(input_concepts, section_title="Cell Biology")
    assert len(merged) == 1
    assert "Mitochondria function" in merged[0]["merged_from"]


@patch("ankithis_api.services.stages.concept_merge.structured_call")
def test_stage_b_empty_input(mock_call):
    from ankithis_api.services.stages.concept_merge import merge_concepts

    result = merge_concepts([])
    assert result == []
    mock_call.assert_not_called()


# --- Stage C: Card Planning ---

@patch("ankithis_api.services.stages.card_planning.structured_call")
def test_stage_c_plans_cards(mock_call):
    mock_call.return_value = {
        "cards": [
            {
                "concept_name": "Cell energy production",
                "card_type": "cloze",
                "direction": "What organelle produces ATP",
                "priority": 9,
            },
            {
                "concept_name": "Cell energy production",
                "card_type": "basic",
                "direction": "Explain oxidative phosphorylation",
                "priority": 7,
            },
        ]
    }

    from ankithis_api.services.stages.card_planning import plan_cards

    concepts = [{"name": "Cell energy production", "description": "...", "importance": 9}]
    plans = plan_cards(concepts, DeckSize.MEDIUM, CardStyle.CLOZE_HEAVY)
    assert len(plans) == 2
    assert plans[0]["card_type"] == "cloze"
    assert plans[1]["card_type"] == "basic"


@patch("ankithis_api.services.stages.card_planning.structured_call")
def test_stage_c_empty_input(mock_call):
    from ankithis_api.services.stages.card_planning import plan_cards

    result = plan_cards([])
    assert result == []
    mock_call.assert_not_called()


# --- Stage D: Card Generation ---

@patch("ankithis_api.services.stages.card_generation.structured_call")
def test_stage_d_generates_cloze(mock_call):
    mock_call.return_value = {
        "cards": [
            {
                "front": "{{c1::Mitochondria}} are the powerhouse of the cell.",
                "back": "",
                "card_type": "cloze",
                "tags": "biology,cell",
            }
        ]
    }

    from ankithis_api.services.stages.card_generation import generate_cards

    plans = [{"concept_name": "Mitochondria", "card_type": "cloze", "direction": "...", "priority": 9}]
    cards = generate_cards(plans, source_text="The mitochondria...")
    assert len(cards) == 1
    assert "{{c1::" in cards[0]["front"]
    assert cards[0]["card_type"] == "cloze"


@patch("ankithis_api.services.stages.card_generation.structured_call")
def test_stage_d_generates_basic(mock_call):
    mock_call.return_value = {
        "cards": [
            {
                "front": "What is the function of mitochondria?",
                "back": "Mitochondria produce ATP through oxidative phosphorylation.",
                "card_type": "basic",
                "tags": "biology,cell",
            }
        ]
    }

    from ankithis_api.services.stages.card_generation import generate_cards

    plans = [{"concept_name": "Mitochondria", "card_type": "basic", "direction": "...", "priority": 9}]
    cards = generate_cards(plans, source_text="The mitochondria...")
    assert len(cards) == 1
    assert cards[0]["front"].endswith("?")
    assert len(cards[0]["back"]) > 0


@patch("ankithis_api.services.stages.card_generation.structured_call")
def test_stage_d_empty_input(mock_call):
    from ankithis_api.services.stages.card_generation import generate_cards

    result = generate_cards([], source_text="")
    assert result == []
    mock_call.assert_not_called()


@patch("ankithis_api.services.stages.card_generation.structured_call")
def test_stage_d_batches_large_input(mock_call):
    """More than BATCH_SIZE plans should result in multiple LLM calls."""
    mock_call.return_value = {"cards": [
        {"front": "Q?", "back": "A", "card_type": "basic", "tags": "t"}
    ]}

    from ankithis_api.services.stages.card_generation import generate_cards, BATCH_SIZE

    plans = [{"concept_name": f"C{i}", "card_type": "basic", "direction": "...", "priority": 5}
             for i in range(BATCH_SIZE + 5)]
    cards = generate_cards(plans, source_text="text")
    assert mock_call.call_count == 2  # ceil((BATCH_SIZE+5)/BATCH_SIZE)
