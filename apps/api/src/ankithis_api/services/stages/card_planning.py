"""Stage C: Plan cards — decide count, type, and direction for each concept."""

from __future__ import annotations

import json
import logging

from ankithis_api.config import settings
from ankithis_api.llm.client import structured_call
from ankithis_api.llm.prompts.stage_c import DENSITY_MODIFIERS, SYSTEM, USER_TEMPLATE
from ankithis_api.llm.schemas import CardPlanOutput, schema_for
from ankithis_api.models.enums import CardStyle, DeckSize

logger = logging.getLogger(__name__)

# Cards per 1,000 words — scales with document length
CARDS_PER_1K_WORDS = {
    DeckSize.SMALL: 5,  # key concepts only
    DeckSize.MEDIUM: 12,  # solid coverage
    DeckSize.LARGE: 22,  # deep, thorough coverage
}

MIN_CARDS = 5
MAX_CARDS = 300

CARD_STYLE_DESC = {
    CardStyle.CLOZE_HEAVY: "Strongly prefer cloze cards (70-80% cloze, rest basic)",
    CardStyle.QA_HEAVY: "Strongly prefer basic Q&A cards (70-80% basic, rest cloze)",
    CardStyle.BALANCED: "Balance evenly between cloze and basic cards (50/50)",
}


def plan_cards(
    concepts: list[dict],
    deck_size: DeckSize = DeckSize.MEDIUM,
    card_style: CardStyle = CardStyle.CLOZE_HEAVY,
    study_goal: str = "Master the key concepts in this material",
    total_words: int = 0,
    content_profile: dict | None = None,
) -> list[dict]:
    """Plan cards for a set of merged concepts. Returns card plan dicts."""
    if not concepts:
        return []

    density = CARDS_PER_1K_WORDS[deck_size]
    base_target = max(MIN_CARDS, min(MAX_CARDS, round(total_words / 1000 * density)))

    # Apply density modifier from content profile
    density_modifier = 1.0
    if content_profile:
        info_density = content_profile.get("information_density")
        if info_density and info_density in DENSITY_MODIFIERS:
            density_modifier = DENSITY_MODIFIERS[info_density]

    target = max(MIN_CARDS, round(base_target * density_modifier))
    style_desc = CARD_STYLE_DESC[card_style]

    # Blend user card style preference with content-recommended ratios
    ratio_note = ""
    if content_profile:
        cloze_ratio = content_profile.get("recommended_cloze_ratio")
        qa_ratio = content_profile.get("recommended_qa_ratio")
        if cloze_ratio is not None and qa_ratio is not None:
            ratio_note = (
                f"\nContent analysis suggests approximately {cloze_ratio * 100:.0f}% cloze "
                f"and {qa_ratio * 100:.0f}% Q&A cards for this material. "
                f"Blend this recommendation with the user's card style preference above."
            )

    system = SYSTEM.format(card_style=style_desc, target_cards=target)
    user = USER_TEMPLATE.format(
        target_cards=target,
        card_style=style_desc,
        study_goal=study_goal,
        concepts_json=json.dumps(concepts, indent=2),
    )
    if ratio_note:
        user += ratio_note
    result = structured_call(
        system=system,
        user=user,
        tool_name="plan_cards",
        tool_schema=schema_for(CardPlanOutput),
        model=settings.model_stage_c,
        max_tokens=2048,
    )
    output = CardPlanOutput.model_validate(result)
    plans = [c.model_dump() for c in output.cards]

    # Phase 2.4c: Ensure prerequisite concepts have at least one card plan
    plans = _ensure_prerequisite_cards(plans, concepts)

    # Phase 2.5: Add reverse cards for definitions in factual/foreign-language content
    plans = _add_reverse_definition_cards(plans, content_profile)

    return plans


def _ensure_prerequisite_cards(plans: list[dict], concepts: list[dict]) -> list[dict]:
    """Ensure every concept listed as a prerequisite has at least one card plan.

    If a prerequisite concept was extracted but has no card plan (e.g. because
    it was low importance), add a basic card plan for it.
    """
    # Collect all prerequisite concept names
    all_prereqs: set[str] = set()
    concept_map: dict[str, dict] = {}
    for c in concepts:
        concept_map[c["name"]] = c
        for prereq in c.get("prerequisites", []):
            all_prereqs.add(prereq)

    # Find concepts that already have card plans
    planned_concepts = {p["concept_name"] for p in plans}

    # Add basic card plans for unplanned prerequisites that were extracted
    for prereq_name in all_prereqs:
        if prereq_name not in planned_concepts and prereq_name in concept_map:
            prereq = concept_map[prereq_name]
            plans.append(
                {
                    "concept_name": prereq_name,
                    "card_type": "basic",
                    "direction": f"Define {prereq_name} (prerequisite)",
                    "priority": min(prereq.get("importance", 5), 6),
                }
            )
            logger.info("Added prerequisite card plan for: %s", prereq_name)

    return plans


def _add_reverse_definition_cards(plans: list[dict], content_profile: dict | None) -> list[dict]:
    """Add reverse (definition-to-term) cards for definition-type card plans.

    Activated when the content profile indicates factual knowledge or includes
    foreign_language_terms in special_considerations.
    """
    if not content_profile:
        return plans

    knowledge_type = content_profile.get("primary_knowledge_type")
    special = content_profile.get("special_considerations", [])
    if knowledge_type != "factual" and "foreign_language_terms" not in special:
        return plans

    reverse_plans = []
    for plan in plans:
        if plan.get("direction") == "term_to_definition":
            reverse_plans.append(
                {
                    **plan,
                    "direction": "definition_to_term",
                    "priority": max(1, plan.get("priority", 5) - 1),
                }
            )

    plans.extend(reverse_plans)
    return plans
