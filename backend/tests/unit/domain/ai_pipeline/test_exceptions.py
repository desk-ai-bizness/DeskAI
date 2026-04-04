"""Unit tests for AI pipeline domain exceptions."""

import unittest

from deskai.domain.ai_pipeline.exceptions import (
    ArtifactPersistenceError,
    GenerationError,
    IncompleteOutputError,
    PipelineError,
    PipelineStepError,
    SchemaValidationError,
)
from deskai.shared.errors import DeskAIError


class PipelineErrorTest(unittest.TestCase):
    def test_instantiation_with_message(self) -> None:
        err = PipelineError("pipeline failed")
        self.assertEqual(str(err), "pipeline failed")

    def test_is_deskai_error(self) -> None:
        err = PipelineError("base")
        self.assertIsInstance(err, DeskAIError)


class SchemaValidationErrorTest(unittest.TestCase):
    def test_instantiation_with_message(self) -> None:
        err = SchemaValidationError("schema invalid")
        self.assertEqual(str(err), "schema invalid")

    def test_is_pipeline_error(self) -> None:
        err = SchemaValidationError("bad schema")
        self.assertIsInstance(err, PipelineError)

    def test_is_deskai_error(self) -> None:
        err = SchemaValidationError("bad schema")
        self.assertIsInstance(err, DeskAIError)


class GenerationErrorTest(unittest.TestCase):
    def test_instantiation_with_message(self) -> None:
        err = GenerationError("LLM call timed out")
        self.assertEqual(str(err), "LLM call timed out")

    def test_is_pipeline_error(self) -> None:
        err = GenerationError("fail")
        self.assertIsInstance(err, PipelineError)


class ArtifactPersistenceErrorTest(unittest.TestCase):
    def test_instantiation_with_message(self) -> None:
        err = ArtifactPersistenceError("S3 write failed")
        self.assertEqual(str(err), "S3 write failed")

    def test_is_pipeline_error(self) -> None:
        err = ArtifactPersistenceError("fail")
        self.assertIsInstance(err, PipelineError)


class PipelineStepErrorTest(unittest.TestCase):
    def test_instantiation_with_attributes(self) -> None:
        err = PipelineStepError(
            message="step blew up",
            step_name="anamnesis_generation",
            cause="timeout",
        )
        self.assertEqual(str(err), "step blew up")
        self.assertEqual(err.step_name, "anamnesis_generation")
        self.assertEqual(err.cause, "timeout")

    def test_is_pipeline_error(self) -> None:
        err = PipelineStepError(message="fail", step_name="summary", cause="bad input")
        self.assertIsInstance(err, PipelineError)

    def test_is_deskai_error(self) -> None:
        err = PipelineStepError(message="fail", step_name="summary", cause="bad input")
        self.assertIsInstance(err, DeskAIError)

    def test_attributes_accessible(self) -> None:
        err = PipelineStepError(message="oops", step_name="insights", cause="parse error")
        self.assertTrue(hasattr(err, "step_name"))
        self.assertTrue(hasattr(err, "cause"))


class IncompleteOutputErrorTest(unittest.TestCase):
    def test_instantiation_with_message(self) -> None:
        err = IncompleteOutputError("missing queixa_principal")
        self.assertEqual(str(err), "missing queixa_principal")

    def test_is_pipeline_error(self) -> None:
        err = IncompleteOutputError("incomplete")
        self.assertIsInstance(err, PipelineError)


if __name__ == "__main__":
    unittest.main()
