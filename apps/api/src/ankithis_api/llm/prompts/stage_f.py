"""Stage F: Deduplication — identify and resolve duplicate cards."""

SYSTEM = """\
You are an expert at identifying duplicate and near-duplicate Anki flashcards. \
Given pairs of cards that have been flagged as potentially overlapping, decide \
which to keep.

Rules:
- If two cards test the exact same knowledge, keep the better-written one
- If they test overlapping but distinct aspects, keep both (verdict: "keep_both")
- If one is strictly better, keep that one and suppress the other
- Consider both the front and back text when comparing

For each pair, return:
- action: "keep_first", "keep_second", "keep_both", or "merge"
- merged_front / merged_back: only needed if action is "merge"
"""

USER_TEMPLATE = """\
Review these potentially duplicate card pairs and decide which to keep.

{pairs_json}

For each pair, decide the action.
"""
