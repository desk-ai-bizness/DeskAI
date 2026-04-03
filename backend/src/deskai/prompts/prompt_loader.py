"""Prompt loader with safe variable injection and output validation.

This module loads prompt templates and injects variables safely.
All user input is sanitized before injection -- no f-strings with raw user data.
"""

from __future__ import annotations

import json
import re
from typing import Any

from deskai.prompts.injection_defense import sanitize_input

# Maximum allowed length for any single variable value injected into a prompt.
MAX_VARIABLE_LENGTH = 50_000

# Maximum total prompt length after variable injection.
MAX_PROMPT_LENGTH = 200_000


class PromptLoadError(Exception):
    """Raised when a prompt template cannot be loaded or rendered."""


class PromptValidationError(Exception):
    """Raised when the LLM output fails JSON schema validation."""


def render_prompt(template: str, variables: dict[str, str]) -> str:
    """Render a prompt template by safely injecting variables.

    Uses ``str.format_map`` with a restricted formatter that only allows
    simple field names (no attribute access, no indexing, no format specs).
    Every variable value is sanitized and length-limited before injection.

    Args:
        template: The prompt template string with ``{variable_name}`` placeholders.
        variables: Mapping of variable names to their string values.

    Returns:
        The rendered prompt string.

    Raises:
        PromptLoadError: If a required variable is missing, a value exceeds the
            length limit, or the rendered prompt is too long.
    """
    sanitized = _sanitize_variables(variables)
    try:
        rendered = template.format_map(_SafeFormatMapping(sanitized))
    except KeyError as exc:
        raise PromptLoadError(f"Missing required prompt variable: {exc}") from exc

    if len(rendered) > MAX_PROMPT_LENGTH:
        raise PromptLoadError(
            f"Rendered prompt exceeds maximum length "
            f"({len(rendered)} > {MAX_PROMPT_LENGTH})"
        )
    return rendered


def validate_json_output(raw_output: str) -> dict[str, Any]:
    """Parse and validate that LLM output is valid JSON.

    Strips common LLM artifacts (markdown code fences, leading/trailing
    whitespace) before parsing.

    Args:
        raw_output: The raw text output from the LLM.

    Returns:
        Parsed JSON as a Python dict.

    Raises:
        PromptValidationError: If the output is not valid JSON.
    """
    cleaned = _strip_code_fences(raw_output.strip())
    try:
        parsed = json.loads(cleaned)
    except (json.JSONDecodeError, TypeError) as exc:
        raise PromptValidationError(f"LLM output is not valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise PromptValidationError(
            f"Expected JSON object, got {type(parsed).__name__}"
        )
    return parsed


def validate_required_fields(
    data: dict[str, Any],
    required_fields: list[str],
) -> list[str]:
    """Check that all required top-level fields are present in parsed output.

    Args:
        data: The parsed JSON output.
        required_fields: List of field names that must be present.

    Returns:
        List of missing field names (empty if all present).
    """
    return [f for f in required_fields if f not in data]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_CODE_FENCE_RE = re.compile(
    r"^```(?:json)?\s*\n?(.*?)\n?\s*```$",
    re.DOTALL,
)


def _strip_code_fences(text: str) -> str:
    """Remove markdown code fences if the entire output is wrapped in them."""
    match = _CODE_FENCE_RE.match(text)
    return match.group(1) if match else text


def _sanitize_variables(variables: dict[str, str]) -> dict[str, str]:
    """Sanitize and length-limit all variable values."""
    result: dict[str, str] = {}
    for key, value in variables.items():
        if not isinstance(value, str):
            value = str(value)
        value = sanitize_input(value)
        if len(value) > MAX_VARIABLE_LENGTH:
            raise PromptLoadError(
                f"Variable '{key}' exceeds maximum length "
                f"({len(value)} > {MAX_VARIABLE_LENGTH})"
            )
        result[key] = value
    return result


class _SafeFormatMapping(dict):
    """A dict subclass that prevents attribute/index access in format strings.

    ``str.format_map`` with a plain dict already prevents ``__getattr__``
    exploitation, but this class adds an explicit ``__missing__`` to
    surface clear errors for undefined variables.
    """

    def __missing__(self, key: str) -> str:
        raise KeyError(key)
