"""Tests for prompt loading, variable injection, and output validation."""

import json

import pytest

from deskai.prompts.prompt_loader import (
    MAX_PROMPT_LENGTH,
    MAX_VARIABLE_LENGTH,
    PromptLoadError,
    PromptValidationError,
    render_prompt,
    validate_json_output,
    validate_required_fields,
)


# -------------------------------------------------------------------------
# render_prompt — safe variable injection
# -------------------------------------------------------------------------


class TestRenderPrompt:
    """Tests for the render_prompt function."""

    def test_renders_simple_template(self) -> None:
        template = "Hello, {name}! Your appointment is on {date}."
        result = render_prompt(template, {"name": "Dr. Silva", "date": "2026-04-01"})
        assert result == "Hello, Dr. Silva! Your appointment is on 2026-04-01."

    def test_renders_template_with_no_variables(self) -> None:
        template = "This prompt has no variables."
        result = render_prompt(template, {})
        assert result == "This prompt has no variables."

    def test_raises_on_missing_variable(self) -> None:
        template = "Patient: {patient_name}, DOB: {patient_dob}"
        with pytest.raises(PromptLoadError, match="Missing required prompt variable"):
            render_prompt(template, {"patient_name": "Joao"})

    def test_raises_on_variable_exceeding_max_length(self) -> None:
        template = "Transcript: {transcript}"
        long_value = "x" * (MAX_VARIABLE_LENGTH + 1)
        with pytest.raises(PromptLoadError, match="exceeds maximum length"):
            render_prompt(template, {"transcript": long_value})

    def test_raises_on_rendered_prompt_exceeding_max_length(self) -> None:
        template = "Data: {data}"
        big_value = "x" * (MAX_PROMPT_LENGTH - 5)
        with pytest.raises(PromptLoadError, match="exceeds maximum length"):
            render_prompt(template, {"data": big_value})

    def test_sanitizes_control_characters_in_variables(self) -> None:
        template = "Input: {text}"
        result = render_prompt(template, {"text": "hello\x00world\x07end"})
        assert result == "Input: helloworldend"

    def test_converts_non_string_variables_to_string(self) -> None:
        template = "Count: {count}"
        result = render_prompt(template, {"count": "42"})
        assert result == "Count: 42"

    def test_handles_curly_braces_in_variable_values(self) -> None:
        template = "Data: {data}"
        result = render_prompt(template, {"data": "json: {key: value}"})
        assert "json: {key: value}" in result

    def test_prevents_attribute_access_via_format(self) -> None:
        template = "Safe: {name}"
        result = render_prompt(template, {"name": "test"})
        assert result == "Safe: test"

    def test_multiple_occurrences_of_same_variable(self) -> None:
        template = "{name} said hello. Again, {name} said hello."
        result = render_prompt(template, {"name": "Ana"})
        assert result == "Ana said hello. Again, Ana said hello."

    def test_preserves_newlines_in_variables(self) -> None:
        template = "Transcript:\n{transcript}"
        result = render_prompt(
            template, {"transcript": "Line 1\nLine 2\nLine 3"}
        )
        assert "Line 1\nLine 2\nLine 3" in result


# -------------------------------------------------------------------------
# validate_json_output
# -------------------------------------------------------------------------


class TestValidateJsonOutput:
    """Tests for JSON output validation."""

    def test_parses_valid_json(self) -> None:
        raw = json.dumps({"queixa_principal": "dor de cabeca"})
        result = validate_json_output(raw)
        assert result == {"queixa_principal": "dor de cabeca"}

    def test_strips_markdown_code_fences(self) -> None:
        raw = '```json\n{"key": "value"}\n```'
        result = validate_json_output(raw)
        assert result == {"key": "value"}

    def test_strips_code_fences_without_language_tag(self) -> None:
        raw = '```\n{"key": "value"}\n```'
        result = validate_json_output(raw)
        assert result == {"key": "value"}

    def test_handles_leading_trailing_whitespace(self) -> None:
        raw = '   \n{"field": 42}\n   '
        result = validate_json_output(raw)
        assert result == {"field": 42}

    def test_raises_on_invalid_json(self) -> None:
        with pytest.raises(PromptValidationError, match="not valid JSON"):
            validate_json_output("this is not json at all")

    def test_raises_on_json_array(self) -> None:
        with pytest.raises(PromptValidationError, match="Expected JSON object"):
            validate_json_output("[1, 2, 3]")

    def test_raises_on_empty_string(self) -> None:
        with pytest.raises(PromptValidationError, match="not valid JSON"):
            validate_json_output("")

    def test_raises_on_json_string(self) -> None:
        with pytest.raises(PromptValidationError, match="Expected JSON object"):
            validate_json_output('"just a string"')

    def test_parses_nested_json(self) -> None:
        raw = json.dumps({
            "subjetivo": {"queixa_principal": "dor"},
            "objetivo": {"exame_fisico": "nao_informado"},
        })
        result = validate_json_output(raw)
        assert result["subjetivo"]["queixa_principal"] == "dor"


# -------------------------------------------------------------------------
# validate_required_fields
# -------------------------------------------------------------------------


class TestValidateRequiredFields:
    """Tests for required field validation."""

    def test_returns_empty_when_all_present(self) -> None:
        data = {"a": 1, "b": 2, "c": 3}
        result = validate_required_fields(data, ["a", "b", "c"])
        assert result == []

    def test_returns_missing_fields(self) -> None:
        data = {"a": 1}
        result = validate_required_fields(data, ["a", "b", "c"])
        assert result == ["b", "c"]

    def test_returns_all_when_none_present(self) -> None:
        data = {}
        result = validate_required_fields(data, ["x", "y"])
        assert result == ["x", "y"]

    def test_handles_empty_required_list(self) -> None:
        data = {"a": 1}
        result = validate_required_fields(data, [])
        assert result == []

    def test_handles_none_values_as_present(self) -> None:
        data = {"field": None}
        result = validate_required_fields(data, ["field"])
        assert result == []
