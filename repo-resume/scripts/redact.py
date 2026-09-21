"""Small, conservative secret detection helper for checkpoint validation."""
from __future__ import annotations

import re


_PATTERNS = (
    re.compile(r"-----BEGIN [^-]*PRIVATE KEY-----.*?-----END [^-]*PRIVATE KEY-----", re.DOTALL),
    re.compile(r"(?i)authorization\s*:\s*bearer\s+(?!\[REDACTED\])[^\s\"']+"),
    re.compile(r"(?i)\b(?:password|passwd|pwd|token|api[_-]?key|secret|private[_-]?key)\s*[:=]\s*(?!\[REDACTED\])[^\s,;]+"),
    re.compile(r"(?i)https?://[^\s/@:]+:[^\s/@]+@"),
    re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,})\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
)


def contains_secret(value: str) -> bool:
    return any(pattern.search(value) for pattern in _PATTERNS)
