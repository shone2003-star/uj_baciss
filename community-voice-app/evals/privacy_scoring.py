"""Scores for the privacy filter. Plain functions: no AI, no network.

Each report lists the personal details planted in it and the area that must stay.
"""

import re
from collections import defaultdict

# Score name -> the kinds of planted details it covers.
GROUPS = {
    "names_removed": ["names"],
    "addresses_removed": ["addresses"],
    "numbers_removed": ["phones", "ids", "emails"],
}


def _gone(item: str, text: str, kind: str) -> bool:
    """A name counts as removed only if every part of it is gone."""
    text = text.lower()
    if kind == "names":
        return not any(word.lower() in text for word in re.findall(r"\w{3,}", item))
    return item.lower() not in text


def score_report(redacted: str, pii: dict, area: str) -> dict[str, list[float]]:
    """One 0/1 score per planted item, and one for keeping the area."""
    scores: dict[str, list[float]] = defaultdict(list)
    for name, kinds in GROUPS.items():
        for kind in kinds:
            for item in pii[kind]:
                scores[name].append(float(_gone(item, redacted, kind)))
    scores["area_kept"].append(float(area.lower() in redacted.lower()))
    return scores


def summarize(per_report: list[dict[str, list[float]]]) -> dict[str, float]:
    """Mean per score over all items, plus 'pii_removed' over every planted item."""
    merged: dict[str, list[float]] = defaultdict(list)
    for scores in per_report:
        for key, values in scores.items():
            merged[key].extend(values)
    merged["pii_removed"] = [v for key in GROUPS for v in merged[key]]
    return {key: round(sum(v) / len(v), 3) for key, v in merged.items() if v}
