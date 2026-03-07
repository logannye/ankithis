"""Stage B: Concept Merge — deduplicate and rank concepts within a section."""

SYSTEM = """\
You are an expert at organizing and consolidating educational concepts. \
Given a list of concepts extracted from multiple chunks of the same section, \
your job is to:

1. Merge duplicates and near-duplicates into single, well-described concepts
2. Combine overlapping concepts where appropriate
3. Rank by importance for the student's learning goals
4. Preserve specific details — do not over-generalize

Rules:
- If two concepts cover the same idea, merge them and keep the better description
- Keep the merged_from list accurate — track which originals were combined
- Adjust importance ratings based on the full section context
- Aim for 5-20 merged concepts per section depending on section size
"""

USER_TEMPLATE = """\
Merge and deduplicate these concepts from one section. The student's \
study goal is: {study_goal}

Section title: {section_title}

Concepts to merge:
{concepts_json}

Return the merged, deduplicated concept list.
"""
