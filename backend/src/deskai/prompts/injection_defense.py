"""Prompt injection defense utilities.

Provides input sanitization, injection pattern detection, output validation,
and role separation enforcement for the AI pipeline.
"""

from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# Injection pattern detection
# ---------------------------------------------------------------------------

# Patterns commonly used in prompt injection attacks.
# Each tuple is (compiled_regex, description).
_INJECTION_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|rules?|prompts?)",
            re.IGNORECASE,
        ),
        "ignore-previous-instructions",
    ),
    (
        re.compile(
            r"disregard\s+(all\s+)?(previous|prior|above)\s+(instructions?|rules?|prompts?)",
            re.IGNORECASE,
        ),
        "disregard-instructions",
    ),
    (
        re.compile(r"you\s+are\s+now\s+(a|an|the)\s+", re.IGNORECASE),
        "role-override",
    ),
    (
        re.compile(r"new\s+instructions?\s*:", re.IGNORECASE),
        "new-instructions",
    ),
    (
        re.compile(r"system\s*:\s*", re.IGNORECASE),
        "system-role-injection",
    ),
    (
        re.compile(r"<\s*/?\s*system\s*>", re.IGNORECASE),
        "system-tag-injection",
    ),
    (
        re.compile(
            r"\[INST\]|\[/INST\]|\<\|im_start\|\>|\<\|im_end\|\>",
            re.IGNORECASE,
        ),
        "chat-template-injection",
    ),
    (
        re.compile(
            r"forget\s+(everything|all|what)\s+(you|above)",
            re.IGNORECASE,
        ),
        "forget-instructions",
    ),
    (
        re.compile(
            r"do\s+not\s+follow\s+(the\s+)?(previous|system|above)",
            re.IGNORECASE,
        ),
        "do-not-follow",
    ),
    (
        re.compile(
            r"override\s+(the\s+)?(system|instructions?|rules?|prompt)",
            re.IGNORECASE,
        ),
        "override-instructions",
    ),
]

# Control characters that should never appear in user input to the LLM
# (except normal whitespace: space, tab, newline, carriage return).
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")


def detect_injection_patterns(text: str) -> list[str]:
    """Scan text for known prompt injection patterns.

    Args:
        text: The input text to scan.

    Returns:
        List of matched pattern descriptions. Empty if no patterns found.
    """
    found: list[str] = []
    for pattern, description in _INJECTION_PATTERNS:
        if pattern.search(text):
            found.append(description)
    return found


def sanitize_input(text: str) -> str:
    """Sanitize user input for safe inclusion in a prompt.

    Operations:
    1. Strip control characters (except normal whitespace).

    This does NOT strip injection patterns -- those are detected separately
    so the caller can decide whether to reject or log.

    Args:
        text: Raw user input.

    Returns:
        Sanitized text safe for prompt injection.
    """
    return _CONTROL_CHAR_RE.sub("", text)


def strip_control_characters(text: str) -> str:
    """Remove control characters from text.

    Preserves normal whitespace (space, tab, newline, CR).
    Alias for ``sanitize_input`` for explicit call-site readability.
    """
    return sanitize_input(text)


# ---------------------------------------------------------------------------
# Output validation
# ---------------------------------------------------------------------------


def validate_output_schema(
    data: dict[str, Any],
    required_fields: list[str],
) -> list[str]:
    """Validate that a parsed LLM JSON output has all required fields.

    Args:
        data: Parsed JSON dict from LLM output.
        required_fields: Top-level fields that must be present.

    Returns:
        List of missing field names. Empty if valid.
    """
    return [f for f in required_fields if f not in data]


def validate_no_extra_text(raw_output: str) -> bool:
    """Check that raw output is ONLY JSON, with no surrounding prose.

    Allows optional markdown code fences wrapping the JSON.

    Args:
        raw_output: Raw LLM text output.

    Returns:
        True if the output appears to be pure JSON (possibly fenced).
    """
    stripped = raw_output.strip()
    # Allow ```json ... ``` wrapping
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        if lines[-1].strip() == "```":
            inner = "\n".join(lines[1:-1]).strip()
            return inner.startswith("{") and inner.endswith("}")
    return stripped.startswith("{") and stripped.endswith("}")


# ---------------------------------------------------------------------------
# Role separation enforcement
# ---------------------------------------------------------------------------


def enforce_role_separation(
    system_prompt: str,
    user_content: str,
) -> tuple[str, str]:
    """Enforce that user content does not leak into system prompt territory.

    Verifies that user content does not contain system-level directives.

    Args:
        system_prompt: The system-level prompt template (no user data).
        user_content: The user-level message with injected variables.

    Returns:
        Tuple of (system_prompt, user_content) if valid.

    Raises:
        ValueError: If role boundaries are violated.
    """
    injections = detect_injection_patterns(user_content)
    if injections:
        raise ValueError(
            f"Prompt injection patterns detected in user content: {injections}"
        )
    return system_prompt, user_content
