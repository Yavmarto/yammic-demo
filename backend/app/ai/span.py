"""Evidence-span helpers.

Every span the service sends back to the API is a half-open ``[start, end)``
interval into the original document text. The API checks the span again, so a
span that does not match exactly is rejected with 422. Providers must therefore
re-locate model output instead of trusting the model's offsets.
"""
from __future__ import annotations

import re

from .types import Evidence


def make_evidence(text: str, start: int, end: int) -> Evidence:
    if not (0 <= start < end <= len(text)):
        raise ValueError(f"span {start}-{end} outside document of length {len(text)}")
    return Evidence(start=start, end=end, text=text[start:end])


def span_matches(text: str, ev: Evidence) -> bool:
    return 0 <= ev.start < ev.end <= len(text) and text[ev.start:ev.end] == ev.text


def _trim_candidates(quote: str) -> list[str]:
    """Quotes often come back with stray quotes, ellipses or a trailing period."""
    out = [quote, quote.strip()]
    for q in list(out):
        q2 = q.strip().strip('"').strip("'").strip()
        q2 = re.sub(r"^(?:\.\.\.|…)\s*", "", q2)
        q2 = re.sub(r"\s*(?:\.\.\.|…)$", "", q2)
        out.append(q2)
    # longest first so the highlight is useful
    return sorted({q for q in out if q}, key=len, reverse=True)


def locate_quote(text: str, quote: str | None) -> tuple[int, int, str] | None:
    """Find ``quote`` verbatim in ``text`` and return ``(start, end, matched_text)``.

    Order: exact, case-insensitive, then whitespace-insensitive. The
    whitespace-insensitive fallback keeps the original offsets by matching the
    same number of characters between words, so the API span check passes.
    """
    if not quote or not quote.strip():
        return None
    for candidate in _trim_candidates(quote):
        idx = text.find(candidate)
        if idx >= 0:
            return idx, idx + len(candidate), candidate
    for candidate in _trim_candidates(quote):
        idx = text.casefold().find(candidate.casefold())
        if idx >= 0:
            # casefold can change length in rare cases; only trust it for our ASCII corpus
            if len(candidate) == len(candidate.casefold()):
                return idx, idx + len(candidate), text[idx:idx + len(candidate)]
    for candidate in _trim_candidates(quote):
        parts = [re.escape(p) for p in candidate.split()]
        if not parts:
            continue
        pattern = re.compile(r"\s+".join(parts), re.IGNORECASE)
        m = pattern.search(text)
        if m:
            return m.start(), m.end(), m.group(0)
    return None


def find_pattern(text: str, pattern: str, flags: int = 0) -> re.Match[str] | None:
    return re.search(pattern, text, flags)


def expand_to_line(text: str, start: int, end: int, *, left: int = 40, right: int = 40) -> tuple[int, int]:
    """Grow a match to nearby word boundaries without crossing a line break."""
    a = max(text.rfind("\n", 0, start) + 1, start - left)
    b = min(text.find("\n", end) if text.find("\n", end) != -1 else len(text), end + right)
    # do not start or end inside a word
    while a > 0 and text[a - 1].isalnum():
        a -= 1
    while b < len(text) and text[b].isalnum():
        b += 1
    return a, b


def quote_in(text: str, quote: str) -> bool:
    if not quote:
        return False
    return quote.casefold() in text.casefold()
