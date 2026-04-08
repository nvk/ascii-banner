# SPDX-License-Identifier: MIT AND Commons-Clause-1.0
# Copyright (c) 2026 nvk
"""Fuzzy font name matching."""

from __future__ import annotations


def fuzzy_match(query: str, candidates: list[str], max_results: int = 5) -> list[str]:
    """Find best matching font names for a query. Returns sorted by score."""
    query_lower = query.lower()

    # Exact match (case-insensitive)
    for c in candidates:
        if c.lower() == query_lower:
            return [c]

    scored: list[tuple[float, str]] = []
    for c in candidates:
        score = _score(query_lower, c.lower(), c)
        if score > 0:
            scored.append((score, c))

    scored.sort(key=lambda x: (-x[0], x[1].lower()))
    return [name for _, name in scored[:max_results]]


def _score(query: str, candidate_lower: str, candidate: str) -> float:
    """Score a candidate against a query. Higher = better match."""
    score = 0.0

    # Exact substring match (strongest signal)
    if query in candidate_lower:
        score += 100.0
        # Bonus for matching at word boundary
        idx = candidate_lower.index(query)
        if idx == 0:
            score += 50.0  # Starts with query
        elif candidate[idx - 1] in " -_":
            score += 30.0  # Word boundary

        # Bonus for length ratio (prefer shorter matches)
        score += 20.0 * len(query) / len(candidate_lower)
        return score

    # Character sequence match (all query chars appear in order)
    qi = 0
    for ci, ch in enumerate(candidate_lower):
        if qi < len(query) and ch == query[qi]:
            qi += 1
    if qi == len(query):
        score += 30.0
        score += 10.0 * len(query) / len(candidate_lower)
        return score

    # Edit distance for short queries (catch typos)
    if len(query) <= 12:
        dist = _edit_distance(query, candidate_lower)
        max_dist = max(1, len(query) // 3)  # Allow ~1 error per 3 chars
        if dist <= max_dist:
            score += 20.0 * (1.0 - dist / (max_dist + 1))
            return score

    return score


def _edit_distance(a: str, b: str) -> int:
    """Levenshtein edit distance."""
    if len(a) > len(b):
        a, b = b, a
    prev = list(range(len(a) + 1))
    for j in range(1, len(b) + 1):
        curr = [j] + [0] * len(a)
        for i in range(1, len(a) + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            curr[i] = min(curr[i - 1] + 1, prev[i] + 1, prev[i - 1] + cost)
        prev = curr
    return prev[len(a)]
