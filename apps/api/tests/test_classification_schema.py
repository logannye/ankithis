from ankithis_api.llm.schemas import ClassificationOutput, schema_for

def test_classification_output_validates():
    data = {
        "content_type": "research_paper",
        "domain": "oncology",
        "difficulty": "advanced",
        "information_density": "dense",
        "structure_quality": "well_structured",
        "primary_knowledge_type": "conceptual",
        "recommended_cloze_ratio": 0.4,
        "recommended_qa_ratio": 0.6,
        "special_considerations": ["heavy_notation"],
    }
    output = ClassificationOutput.model_validate(data)
    assert output.content_type == "research_paper"
    assert output.difficulty == "advanced"
    assert output.recommended_cloze_ratio == 0.4

def test_classification_schema_has_required_fields():
    schema = schema_for(ClassificationOutput)
    props = schema["properties"]
    assert "content_type" in props
    assert "domain" in props
    assert "difficulty" in props
    assert "special_considerations" in props
