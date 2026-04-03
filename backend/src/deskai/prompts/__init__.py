"""DeskAI prompt templates and loading utilities."""

from deskai.prompts.anamnesis_prompt import (
    ANAMNESIS_SYSTEM_PROMPT,
    ANAMNESIS_USER_TEMPLATE,
)
from deskai.prompts.insights_prompt import (
    INSIGHTS_SYSTEM_PROMPT,
    INSIGHTS_USER_TEMPLATE,
)
from deskai.prompts.prescription_prompt import (
    PRESCRIPTION_SYSTEM_PROMPT,
    PRESCRIPTION_USER_TEMPLATE,
)
from deskai.prompts.summary_prompt import (
    SUMMARY_SYSTEM_PROMPT,
    SUMMARY_USER_TEMPLATE,
)
from deskai.prompts.transcript_prompt import (
    TRANSCRIPT_SYSTEM_PROMPT,
    TRANSCRIPT_USER_TEMPLATE,
)

__all__ = [
    "ANAMNESIS_SYSTEM_PROMPT",
    "ANAMNESIS_USER_TEMPLATE",
    "INSIGHTS_SYSTEM_PROMPT",
    "INSIGHTS_USER_TEMPLATE",
    "PRESCRIPTION_SYSTEM_PROMPT",
    "PRESCRIPTION_USER_TEMPLATE",
    "SUMMARY_SYSTEM_PROMPT",
    "SUMMARY_USER_TEMPLATE",
    "TRANSCRIPT_SYSTEM_PROMPT",
    "TRANSCRIPT_USER_TEMPLATE",
]
