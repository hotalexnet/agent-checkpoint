"""Small, conservative secret redaction helpers for checkpoint text."""
from __future__ import annotations

import re


_REDACTED = "[REDACTED]"
_PATTERNS = (
    (re.compile(r"-----BEGIN [^-]*PRIVATE KEY-----.*?-----END [^-]*PRIVATE KEY-----", re.DOTALL), _REDACTED),
    (re.compile(r"(?i)(authorization\s*:\s*bearer\s+)(?!\[REDACTED\])[^\s\"']+"), r"\1" + _REDACTED),
    (re.compile(r"(?i)(\b(?:password|passwd|pwd|token|api[_-]?key|secret|private[_-]?key)\s*[:=]\s*)(?!\[REDACTED\])[^\s,;]+"), r"\1" + _REDACTED),
    (re.compile(r"(?i)(https?://)[^\s/@:]+:[^\s/@]+@"), r"\1" + _REDACTED + "@"),
    (re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,})\b"), _REDACTED),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), _REDACTED),
)


def redact_text(value: str) -> str:
    """Redact common credentials while leaving normal technical text intact."""
    redacted = value
    for pattern, replacement in _PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def contains_secret(value: str) -> bool:
    """Return whether text still matches a credential pattern."""
    return redact_text(value) != value
