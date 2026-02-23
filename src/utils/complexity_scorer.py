"""
Complexity scorer for SDD auto-trigger.

Scores a task description text to determine whether it is complex enough
to warrant running the full SDD loop (sp.specify → sp.plan → sp.tasks).
A score of 3 or more triggers auto-generation.
"""
import re

_STEP_PATTERN = re.compile(
    r"\b(first|second|third|then|after that|next|step \d+|finally)\b",
    re.IGNORECASE,
)
_API_PATTERN = re.compile(
    r"\b(api|webhook|integration|endpoint|sdk|oauth|rest|graphql|mcp)\b",
    re.IGNORECASE,
)
_STAKEHOLDER_PATTERN = re.compile(
    r"\b(team|system|service|frontend|backend|database|stakeholder|coordinate)\b",
    re.IGNORECASE,
)


def complexity_score(text: str) -> int:
    """Score a task description for SDD loop auto-trigger. Returns 0–4."""
    if not text:
        return 0
    score = 0
    if len(text.split()) > 200:
        score += 1
    if _API_PATTERN.search(text):
        score += 1
    if len(_STEP_PATTERN.findall(text)) >= 2:
        score += 1
    if len(_STAKEHOLDER_PATTERN.findall(text)) >= 2:
        score += 1
    return score
