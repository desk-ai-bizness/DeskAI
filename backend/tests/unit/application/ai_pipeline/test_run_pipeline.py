"""Unit tests for RunPipelineUseCase."""

import unittest
from unittest.mock import MagicMock, patch

from deskai.domain.ai_pipeline.entities import PipelineResult, PipelineStatus
from deskai.domain.ai_pipeline.exceptions import (
    GenerationError,
    PipelineStepError,
)
from deskai.domain.ai_pipeline.value_objects import (
    StructuredOutput,
)
from deskai.domain.audit.entities import AuditAction
from deskai.domain.consultation.entities import ConsultationStatus
from deskai.domain.consultation.value_objects import ArtifactType
from tests.conftest import (
    make_sample_anamnesis_output,
    make_sample_consultation,
    make_sample_insights_output,
    make_sample_patient,
    make_sample_summary_output,
)

_FIXED_TIME = "2026-04-03T10:00:00+00:00"
_FIXED_UUID = "evt-test-001"

_MODULE = "deskai.application.ai_pipeline.run_pipeline"


def _patch_time_and_id(fn):
    """Decorator to patch utc_now_iso and new_uuid in the use case module."""
    fn = patch(f"{_MODULE}.new_uuid", return_value=_FIXED_UUID)(fn)
    fn = patch(f"{_MODULE}.utc_now_iso", return_value=_FIXED_TIME)(fn)
    return fn


def _build_use_case(
    *,
    llm_provider=None,
    artifact_repo=None,
    consultation_repo=None,
    transcript_repo=None,
    patient_repo=None,
    audit_repo=None,
    transcript_lookup_attempts=20,
    transcript_lookup_interval_seconds=3.0,
):
    """Build a RunPipelineUseCase with optional mock overrides."""
    from deskai.application.ai_pipeline.run_pipeline import RunPipelineUseCase

    return RunPipelineUseCase(
        llm_provider=llm_provider or MagicMock(),
        artifact_repo=artifact_repo or MagicMock(),
        consultation_repo=consultation_repo or MagicMock(),
        transcript_repo=transcript_repo or MagicMock(),
        patient_repo=patient_repo or MagicMock(),
        audit_repo=audit_repo or MagicMock(),
        transcript_lookup_attempts=transcript_lookup_attempts,
        transcript_lookup_interval_seconds=transcript_lookup_interval_seconds,
    )


def _make_llm_provider_mock(
    anamnesis_output=None,
    summary_output=None,
    insights_output=None,
):
    """Build an LLM provider mock returning structured outputs."""
    provider = MagicMock()
    responses = []
    if anamnesis_output is not None:
        responses.append(StructuredOutput(task="anamnesis", payload=anamnesis_output))
    if summary_output is not None:
        responses.append(StructuredOutput(task="summary", payload=summary_output))
    if insights_output is not None:
        responses.append(StructuredOutput(task="insights", payload=insights_output))
    provider.generate_structured_output.side_effect = responses
    return provider


class TestRunPipelineFullSuccess(unittest.TestCase):
    """Tests for the happy path where all 3 artifacts succeed."""

    @_patch_time_and_id
    def test_full_pipeline_returns_completed_status(self, mock_time, mock_uuid) -> None:
        consultation = make_sample_consultation(
            status=ConsultationStatus.IN_PROCESSING,
        )
        patient = make_sample_patient()
        consultation_repo = MagicMock()
        consultation_repo.find_by_id.return_value = consultation
        transcript_repo = MagicMock()
        transcript_repo.get_normalized_transcript.return_value = MagicMock(
            transcript_text="Doutor: oi. Paciente: Estou com dor de cabeca ha dois dias."
        )
        patient_repo = MagicMock()
        patient_repo.find_by_id.return_value = patient
        artifact_repo = MagicMock()
        audit_repo = MagicMock()
        llm = _make_llm_provider_mock(
            anamnesis_output=make_sample_anamnesis_output(),
            summary_output=make_sample_summary_output(),
            insights_output=make_sample_insights_output(),
        )

        uc = _build_use_case(
            llm_provider=llm,
            artifact_repo=artifact_repo,
            consultation_repo=consultation_repo,
            transcript_repo=transcript_repo,
            patient_repo=patient_repo,
            audit_repo=audit_repo,
        )

        result = uc.execute(consultation_id="cons-001", clinic_id="clinic-001")

        self.assertEqual(result.status, PipelineStatus.COMPLETED)
        self.assertIsInstance(result, PipelineResult)
        self.assertEqual(result.consultation_id, "cons-001")
        self.assertEqual(result.clinic_id, "clinic-001")

    @_patch_time_and_id
    def test_full_pipeline_saves_all_three_artifacts(self, mock_time, mock_uuid) -> None:
        consultation = make_sample_consultation(
            status=ConsultationStatus.IN_PROCESSING,
        )
        consultation_repo = MagicMock()
        consultation_repo.find_by_id.return_value = consultation
        transcript_repo = MagicMock()
        transcript_repo.get_normalized_transcript.return_value = MagicMock(
            transcript_text="Doutor: oi. Paciente: Estou com dor de cabeca ha dois dias."
        )
        patient_repo = MagicMock()
        patient_repo.find_by_id.return_value = make_sample_patient()
        artifact_repo = MagicMock()
        audit_repo = MagicMock()
        llm = _make_llm_provider_mock(
            anamnesis_output=make_sample_anamnesis_output(),
            summary_output=make_sample_summary_output(),
            insights_output=make_sample_insights_output(),
        )

        uc = _build_use_case(
            llm_provider=llm,
            artifact_repo=artifact_repo,
            consultation_repo=consultation_repo,
            transcript_repo=transcript_repo,
            patient_repo=patient_repo,
            audit_repo=audit_repo,
        )
        uc.execute(consultation_id="cons-001", clinic_id="clinic-001")

        self.assertEqual(artifact_repo.save_artifact.call_count, 3)
        save_calls = artifact_repo.save_artifact.call_args_list
        saved_types = [c[0][2] for c in save_calls]
        self.assertIn(ArtifactType.MEDICAL_HISTORY, saved_types)
        self.assertIn(ArtifactType.SUMMARY, saved_types)
        self.assertIn(ArtifactType.INSIGHTS, saved_types)

    @_patch_time_and_id
    def test_full_pipeline_updates_status_to_draft_generated(self, mock_time, mock_uuid) -> None:
        consultation = make_sample_consultation(
            status=ConsultationStatus.IN_PROCESSING,
        )
        consultation_repo = MagicMock()
        consultation_repo.find_by_id.return_value = consultation
        transcript_repo = MagicMock()
        transcript_repo.get_normalized_transcript.return_value = MagicMock(
            transcript_text="Doutor: oi. Paciente: Estou com dor de cabeca ha dois dias."
        )
        patient_repo = MagicMock()
        patient_repo.find_by_id.return_value = make_sample_patient()
        llm = _make_llm_provider_mock(
            anamnesis_output=make_sample_anamnesis_output(),
            summary_output=make_sample_summary_output(),
            insights_output=make_sample_insights_output(),
        )

        uc = _build_use_case(
            llm_provider=llm,
            consultation_repo=consultation_repo,
            transcript_repo=transcript_repo,
            patient_repo=patient_repo,
        )
        uc.execute(consultation_id="cons-001", clinic_id="clinic-001")

        saved_consultation = consultation_repo.save.call_args[0][0]
        self.assertEqual(
            saved_consultation.status,
            ConsultationStatus.DRAFT_GENERATED,
        )

    @_patch_time_and_id
    def test_full_pipeline_returns_three_completed_artifacts(self, mock_time, mock_uuid) -> None:
        consultation = make_sample_consultation(
            status=ConsultationStatus.IN_PROCESSING,
        )
        consultation_repo = MagicMock()
        consultation_repo.find_by_id.return_value = consultation
        transcript_repo = MagicMock()
        transcript_repo.get_normalized_transcript.return_value = MagicMock(
            transcript_text="Doutor: oi. Paciente: Estou com dor de cabeca ha dois dias."
        )
        patient_repo = MagicMock()
        patient_repo.find_by_id.return_value = make_sample_patient()
        llm = _make_llm_provider_mock(
            anamnesis_output=make_sample_anamnesis_output(),
            summary_output=make_sample_summary_output(),
            insights_output=make_sample_insights_output(),
        )

        uc = _build_use_case(
            llm_provider=llm,
            consultation_repo=consultation_repo,
            transcript_repo=transcript_repo,
            patient_repo=patient_repo,
        )
        result = uc.execute(consultation_id="cons-001", clinic_id="clinic-001")

        self.assertEqual(len(result.completed_artifacts()), 3)
        self.assertIsNotNone(result.medical_history)
        self.assertIsNotNone(result.summary)
        self.assertIsNotNone(result.insights)

    @_patch_time_and_id
    def test_full_pipeline_emits_started_and_completed_audit_events(
        self, mock_time, mock_uuid
    ) -> None:
        consultation = make_sample_consultation(
            status=ConsultationStatus.IN_PROCESSING,
        )
        consultation_repo = MagicMock()
        consultation_repo.find_by_id.return_value = consultation
        transcript_repo = MagicMock()
        transcript_repo.get_normalized_transcript.return_value = MagicMock(
            transcript_text="Doutor: oi. Paciente: Estou com dor de cabeca ha dois dias."
        )
        patient_repo = MagicMock()
        patient_repo.find_by_id.return_value = make_sample_patient()
        audit_repo = MagicMock()
        llm = _make_llm_provider_mock(
            anamnesis_output=make_sample_anamnesis_output(),
            summary_output=make_sample_summary_output(),
            insights_output=make_sample_insights_output(),
        )

        uc = _build_use_case(
            llm_provider=llm,
            consultation_repo=consultation_repo,
            transcript_repo=transcript_repo,
            patient_repo=patient_repo,
            audit_repo=audit_repo,
        )
        uc.execute(consultation_id="cons-001", clinic_id="clinic-001")

        audit_calls = audit_repo.append.call_args_list
        event_types = [c[0][0].event_type for c in audit_calls]
        self.assertIn(AuditAction.PROCESSING_STARTED, event_types)
        self.assertIn(AuditAction.PROCESSING_COMPLETED, event_types)


class TestRunPipelinePrerequisiteFailures(unittest.TestCase):
    """Tests for prerequisite check failures."""

    @_patch_time_and_id
    def test_consultation_not_found_raises_pipeline_step_error(self, mock_time, mock_uuid) -> None:
        consultation_repo = MagicMock()
        consultation_repo.find_by_id.return_value = None

        uc = _build_use_case(consultation_repo=consultation_repo)

        with self.assertRaises(PipelineStepError) as ctx:
            uc.execute(consultation_id="cons-999", clinic_id="clinic-001")
        self.assertEqual(ctx.exception.step_name, "prerequisites")

    @_patch_time_and_id
    def test_consultation_wrong_status_raises_pipeline_step_error(
        self, mock_time, mock_uuid
    ) -> None:
        consultation = make_sample_consultation(
            status=ConsultationStatus.STARTED,
        )
        consultation_repo = MagicMock()
        consultation_repo.find_by_id.return_value = consultation

        uc = _build_use_case(consultation_repo=consultation_repo)

        with self.assertRaises(PipelineStepError) as ctx:
            uc.execute(consultation_id="cons-001", clinic_id="clinic-001")
        self.assertIn("IN_PROCESSING", str(ctx.exception))

    @_patch_time_and_id
    def test_transcript_not_found_marks_failed_and_raises(self, mock_time, mock_uuid) -> None:
        consultation = make_sample_consultation(
            status=ConsultationStatus.IN_PROCESSING,
        )
        consultation_repo = MagicMock()
        consultation_repo.find_by_id.return_value = consultation
        transcript_repo = MagicMock()
        transcript_repo.get_normalized_transcript.return_value = None

        uc = _build_use_case(
            consultation_repo=consultation_repo,
            transcript_repo=transcript_repo,
            transcript_lookup_attempts=1,
            transcript_lookup_interval_seconds=0.0,
        )

        with self.assertRaises(PipelineStepError):
            uc.execute(consultation_id="cons-001", clinic_id="clinic-001")

        saved = consultation_repo.save.call_args[0][0]
        self.assertEqual(saved.status, ConsultationStatus.PROCESSING_FAILED)

    @_patch_time_and_id
    def test_transcript_retry_succeeds_when_artifact_arrives_late(
        self, mock_time, mock_uuid
    ) -> None:
        consultation = make_sample_consultation(
            status=ConsultationStatus.IN_PROCESSING,
        )
        consultation_repo = MagicMock()
        consultation_repo.find_by_id.return_value = consultation
        transcript_repo = MagicMock()
        transcript_repo.get_normalized_transcript.side_effect = [
            None,
            None,
            MagicMock(transcript_text="Doutor: oi. Paciente: dor de garganta."),
        ]
        patient_repo = MagicMock()
        patient_repo.find_by_id.return_value = make_sample_patient()
        llm = _make_llm_provider_mock(
            anamnesis_output=make_sample_anamnesis_output(),
            summary_output=make_sample_summary_output(),
            insights_output=make_sample_insights_output(),
        )

        uc = _build_use_case(
            llm_provider=llm,
            consultation_repo=consultation_repo,
            transcript_repo=transcript_repo,
            patient_repo=patient_repo,
            transcript_lookup_attempts=3,
            transcript_lookup_interval_seconds=0.01,
        )

        with patch(f"{_MODULE}.time.sleep", return_value=None) as sleep_mock:
            result = uc.execute(consultation_id="cons-001", clinic_id="clinic-001")

        self.assertEqual(result.status, PipelineStatus.COMPLETED)
        self.assertEqual(transcript_repo.get_normalized_transcript.call_count, 3)
        self.assertEqual(sleep_mock.call_count, 2)


class TestRunPipelineAnamnesisFailure(unittest.TestCase):
    """Tests when anamnesis step fails."""

    @_patch_time_and_id
    def test_anamnesis_generation_error_returns_failed_result(self, mock_time, mock_uuid) -> None:
        consultation = make_sample_consultation(
            status=ConsultationStatus.IN_PROCESSING,
        )
        consultation_repo = MagicMock()
        consultation_repo.find_by_id.return_value = consultation
        transcript_repo = MagicMock()
        transcript_repo.get_normalized_transcript.return_value = MagicMock(
            transcript_text="Doutor: oi."
        )
        patient_repo = MagicMock()
        patient_repo.find_by_id.return_value = make_sample_patient()
        llm = MagicMock()
        llm.generate_structured_output.side_effect = GenerationError("LLM timeout")

        uc = _build_use_case(
            llm_provider=llm,
            consultation_repo=consultation_repo,
            transcript_repo=transcript_repo,
            patient_repo=patient_repo,
        )
        result = uc.execute(consultation_id="cons-001", clinic_id="clinic-001")

        self.assertEqual(result.status, PipelineStatus.FAILED)
        self.assertIn("Anamnesis failed", result.error_message)

    @_patch_time_and_id
    def test_anamnesis_generation_error_marks_consultation_failed(
        self, mock_time, mock_uuid
    ) -> None:
        consultation = make_sample_consultation(
            status=ConsultationStatus.IN_PROCESSING,
        )
        consultation_repo = MagicMock()
        consultation_repo.find_by_id.return_value = consultation
        transcript_repo = MagicMock()
        transcript_repo.get_normalized_transcript.return_value = MagicMock(
            transcript_text="Doutor: oi."
        )
        patient_repo = MagicMock()
        patient_repo.find_by_id.return_value = make_sample_patient()
        llm = MagicMock()
        llm.generate_structured_output.side_effect = GenerationError("LLM timeout")

        uc = _build_use_case(
            llm_provider=llm,
            consultation_repo=consultation_repo,
            transcript_repo=transcript_repo,
            patient_repo=patient_repo,
        )
        uc.execute(consultation_id="cons-001", clinic_id="clinic-001")

        saved = consultation_repo.save.call_args[0][0]
        self.assertEqual(saved.status, ConsultationStatus.PROCESSING_FAILED)

    @_patch_time_and_id
    def test_anamnesis_schema_validation_error_returns_failed(self, mock_time, mock_uuid) -> None:
        consultation = make_sample_consultation(
            status=ConsultationStatus.IN_PROCESSING,
        )
        consultation_repo = MagicMock()
        consultation_repo.find_by_id.return_value = consultation
        transcript_repo = MagicMock()
        transcript_repo.get_normalized_transcript.return_value = MagicMock(
            transcript_text="Doutor: oi."
        )
        patient_repo = MagicMock()
        patient_repo.find_by_id.return_value = make_sample_patient()
        # Return an incomplete anamnesis (missing required fields)
        llm = MagicMock()
        llm.generate_structured_output.return_value = StructuredOutput(
            task="anamnesis", payload={"queixa_principal": "dor"}
        )

        uc = _build_use_case(
            llm_provider=llm,
            consultation_repo=consultation_repo,
            transcript_repo=transcript_repo,
            patient_repo=patient_repo,
        )
        result = uc.execute(consultation_id="cons-001", clinic_id="clinic-001")

        self.assertEqual(result.status, PipelineStatus.FAILED)
        self.assertIn("Anamnesis", result.error_message)


class TestRunPipelineSummaryFailure(unittest.TestCase):
    """Tests when summary step fails after anamnesis succeeds."""

    @_patch_time_and_id
    def test_summary_failure_returns_partially_completed(self, mock_time, mock_uuid) -> None:
        consultation = make_sample_consultation(
            status=ConsultationStatus.IN_PROCESSING,
        )
        consultation_repo = MagicMock()
        consultation_repo.find_by_id.return_value = consultation
        transcript_repo = MagicMock()
        transcript_repo.get_normalized_transcript.return_value = MagicMock(
            transcript_text="Doutor: oi. Paciente: Estou com dor de cabeca ha dois dias."
        )
        patient_repo = MagicMock()
        patient_repo.find_by_id.return_value = make_sample_patient()
        artifact_repo = MagicMock()
        llm = MagicMock()
        llm.generate_structured_output.side_effect = [
            StructuredOutput(
                task="anamnesis",
                payload=make_sample_anamnesis_output(),
            ),
            GenerationError("Summary LLM timeout"),
        ]

        uc = _build_use_case(
            llm_provider=llm,
            artifact_repo=artifact_repo,
            consultation_repo=consultation_repo,
            transcript_repo=transcript_repo,
            patient_repo=patient_repo,
        )
        result = uc.execute(consultation_id="cons-001", clinic_id="clinic-001")

        self.assertEqual(result.status, PipelineStatus.PARTIALLY_COMPLETED)
        self.assertIsNotNone(result.medical_history)
        self.assertIsNone(result.summary)
        self.assertIn("Summary failed", result.error_message)

    @_patch_time_and_id
    def test_summary_failure_still_saves_anamnesis_artifact(self, mock_time, mock_uuid) -> None:
        consultation = make_sample_consultation(
            status=ConsultationStatus.IN_PROCESSING,
        )
        consultation_repo = MagicMock()
        consultation_repo.find_by_id.return_value = consultation
        transcript_repo = MagicMock()
        transcript_repo.get_normalized_transcript.return_value = MagicMock(
            transcript_text="Doutor: oi. Paciente: Estou com dor de cabeca ha dois dias."
        )
        patient_repo = MagicMock()
        patient_repo.find_by_id.return_value = make_sample_patient()
        artifact_repo = MagicMock()
        llm = MagicMock()
        llm.generate_structured_output.side_effect = [
            StructuredOutput(
                task="anamnesis",
                payload=make_sample_anamnesis_output(),
            ),
            GenerationError("Summary LLM timeout"),
        ]

        uc = _build_use_case(
            llm_provider=llm,
            artifact_repo=artifact_repo,
            consultation_repo=consultation_repo,
            transcript_repo=transcript_repo,
            patient_repo=patient_repo,
        )
        uc.execute(consultation_id="cons-001", clinic_id="clinic-001")

        self.assertEqual(artifact_repo.save_artifact.call_count, 1)
        saved_type = artifact_repo.save_artifact.call_args[0][2]
        self.assertEqual(saved_type, ArtifactType.MEDICAL_HISTORY)


class TestRunPipelineInsightsFailure(unittest.TestCase):
    """Tests when insights step fails after anamnesis+summary succeed."""

    @_patch_time_and_id
    def test_insights_failure_returns_partially_completed(self, mock_time, mock_uuid) -> None:
        consultation = make_sample_consultation(
            status=ConsultationStatus.IN_PROCESSING,
        )
        consultation_repo = MagicMock()
        consultation_repo.find_by_id.return_value = consultation
        transcript_repo = MagicMock()
        transcript_repo.get_normalized_transcript.return_value = MagicMock(
            transcript_text="Doutor: oi. Paciente: Estou com dor de cabeca ha dois dias."
        )
        patient_repo = MagicMock()
        patient_repo.find_by_id.return_value = make_sample_patient()
        artifact_repo = MagicMock()
        llm = MagicMock()
        llm.generate_structured_output.side_effect = [
            StructuredOutput(
                task="anamnesis",
                payload=make_sample_anamnesis_output(),
            ),
            StructuredOutput(
                task="summary",
                payload=make_sample_summary_output(),
            ),
            GenerationError("Insights LLM timeout"),
        ]

        uc = _build_use_case(
            llm_provider=llm,
            artifact_repo=artifact_repo,
            consultation_repo=consultation_repo,
            transcript_repo=transcript_repo,
            patient_repo=patient_repo,
        )
        result = uc.execute(consultation_id="cons-001", clinic_id="clinic-001")

        self.assertEqual(result.status, PipelineStatus.PARTIALLY_COMPLETED)
        self.assertIsNotNone(result.medical_history)
        self.assertIsNotNone(result.summary)
        self.assertIsNone(result.insights)

    @_patch_time_and_id
    def test_insights_failure_saves_anamnesis_and_summary(self, mock_time, mock_uuid) -> None:
        consultation = make_sample_consultation(
            status=ConsultationStatus.IN_PROCESSING,
        )
        consultation_repo = MagicMock()
        consultation_repo.find_by_id.return_value = consultation
        transcript_repo = MagicMock()
        transcript_repo.get_normalized_transcript.return_value = MagicMock(
            transcript_text="Doutor: oi. Paciente: Estou com dor de cabeca ha dois dias."
        )
        patient_repo = MagicMock()
        patient_repo.find_by_id.return_value = make_sample_patient()
        artifact_repo = MagicMock()
        llm = MagicMock()
        llm.generate_structured_output.side_effect = [
            StructuredOutput(
                task="anamnesis",
                payload=make_sample_anamnesis_output(),
            ),
            StructuredOutput(
                task="summary",
                payload=make_sample_summary_output(),
            ),
            GenerationError("Insights LLM timeout"),
        ]

        uc = _build_use_case(
            llm_provider=llm,
            artifact_repo=artifact_repo,
            consultation_repo=consultation_repo,
            transcript_repo=transcript_repo,
            patient_repo=patient_repo,
        )
        uc.execute(consultation_id="cons-001", clinic_id="clinic-001")

        self.assertEqual(artifact_repo.save_artifact.call_count, 2)

    @_patch_time_and_id
    def test_insights_failure_still_updates_status_to_draft_generated(
        self, mock_time, mock_uuid
    ) -> None:
        consultation = make_sample_consultation(
            status=ConsultationStatus.IN_PROCESSING,
        )
        consultation_repo = MagicMock()
        consultation_repo.find_by_id.return_value = consultation
        transcript_repo = MagicMock()
        transcript_repo.get_normalized_transcript.return_value = MagicMock(
            transcript_text="Doutor: oi. Paciente: Estou com dor de cabeca ha dois dias."
        )
        patient_repo = MagicMock()
        patient_repo.find_by_id.return_value = make_sample_patient()
        llm = MagicMock()
        llm.generate_structured_output.side_effect = [
            StructuredOutput(
                task="anamnesis",
                payload=make_sample_anamnesis_output(),
            ),
            StructuredOutput(
                task="summary",
                payload=make_sample_summary_output(),
            ),
            GenerationError("Insights LLM timeout"),
        ]

        uc = _build_use_case(
            llm_provider=llm,
            consultation_repo=consultation_repo,
            transcript_repo=transcript_repo,
            patient_repo=patient_repo,
        )
        uc.execute(consultation_id="cons-001", clinic_id="clinic-001")

        saved = consultation_repo.save.call_args[0][0]
        self.assertEqual(saved.status, ConsultationStatus.DRAFT_GENERATED)


class TestRunPipelinePromptVariables(unittest.TestCase):
    """Tests that correct prompt variables are passed to the LLM."""

    @_patch_time_and_id
    def test_anamnesis_prompt_receives_transcript_and_patient(self, mock_time, mock_uuid) -> None:
        consultation = make_sample_consultation(
            status=ConsultationStatus.IN_PROCESSING,
        )
        consultation_repo = MagicMock()
        consultation_repo.find_by_id.return_value = consultation
        transcript_repo = MagicMock()
        transcript_repo.get_normalized_transcript.return_value = MagicMock(
            transcript_text="transcript text here"
        )
        patient_repo = MagicMock()
        patient_repo.find_by_id.return_value = make_sample_patient(
            name="Maria", date_of_birth="1985-03-10"
        )
        llm = _make_llm_provider_mock(
            anamnesis_output=make_sample_anamnesis_output(),
            summary_output=make_sample_summary_output(),
            insights_output=make_sample_insights_output(),
        )

        uc = _build_use_case(
            llm_provider=llm,
            consultation_repo=consultation_repo,
            transcript_repo=transcript_repo,
            patient_repo=patient_repo,
        )
        uc.execute(consultation_id="cons-001", clinic_id="clinic-001")

        first_call = llm.generate_structured_output.call_args_list[0]
        self.assertEqual(first_call[0][0], "anamnesis")
        payload = first_call[0][1]
        self.assertIn("system_prompt", payload)
        self.assertIn("user_message", payload)

    @_patch_time_and_id
    def test_llm_called_three_times_for_full_pipeline(self, mock_time, mock_uuid) -> None:
        consultation = make_sample_consultation(
            status=ConsultationStatus.IN_PROCESSING,
        )
        consultation_repo = MagicMock()
        consultation_repo.find_by_id.return_value = consultation
        transcript_repo = MagicMock()
        transcript_repo.get_normalized_transcript.return_value = MagicMock(
            transcript_text="Doutor: oi. Paciente: Estou com dor de cabeca ha dois dias."
        )
        patient_repo = MagicMock()
        patient_repo.find_by_id.return_value = make_sample_patient()
        llm = _make_llm_provider_mock(
            anamnesis_output=make_sample_anamnesis_output(),
            summary_output=make_sample_summary_output(),
            insights_output=make_sample_insights_output(),
        )

        uc = _build_use_case(
            llm_provider=llm,
            consultation_repo=consultation_repo,
            transcript_repo=transcript_repo,
            patient_repo=patient_repo,
        )
        uc.execute(consultation_id="cons-001", clinic_id="clinic-001")

        self.assertEqual(llm.generate_structured_output.call_count, 3)
        tasks = [c[0][0] for c in llm.generate_structured_output.call_args_list]
        self.assertEqual(tasks, ["anamnesis", "summary", "insights"])


class TestRunPipelinePatientNotFound(unittest.TestCase):
    """Tests when patient cannot be found."""

    @_patch_time_and_id
    def test_patient_not_found_uses_nao_informado_defaults(self, mock_time, mock_uuid) -> None:
        consultation = make_sample_consultation(
            status=ConsultationStatus.IN_PROCESSING,
        )
        consultation_repo = MagicMock()
        consultation_repo.find_by_id.return_value = consultation
        transcript_repo = MagicMock()
        transcript_repo.get_normalized_transcript.return_value = MagicMock(
            transcript_text="Doutor: oi. Paciente: Estou com dor de cabeca ha dois dias."
        )
        patient_repo = MagicMock()
        patient_repo.find_by_id.return_value = None
        llm = _make_llm_provider_mock(
            anamnesis_output=make_sample_anamnesis_output(),
            summary_output=make_sample_summary_output(),
            insights_output=make_sample_insights_output(),
        )

        uc = _build_use_case(
            llm_provider=llm,
            consultation_repo=consultation_repo,
            transcript_repo=transcript_repo,
            patient_repo=patient_repo,
        )
        result = uc.execute(consultation_id="cons-001", clinic_id="clinic-001")

        # Should still succeed even without patient info
        self.assertEqual(result.status, PipelineStatus.COMPLETED)


class TestRunPipelineAuditEvents(unittest.TestCase):
    """Tests for audit event creation patterns."""

    @_patch_time_and_id
    def test_failed_pipeline_emits_started_and_failed_audit(self, mock_time, mock_uuid) -> None:
        consultation = make_sample_consultation(
            status=ConsultationStatus.IN_PROCESSING,
        )
        consultation_repo = MagicMock()
        consultation_repo.find_by_id.return_value = consultation
        transcript_repo = MagicMock()
        transcript_repo.get_normalized_transcript.return_value = MagicMock(
            transcript_text="Doutor: oi."
        )
        patient_repo = MagicMock()
        patient_repo.find_by_id.return_value = make_sample_patient()
        audit_repo = MagicMock()
        llm = MagicMock()
        llm.generate_structured_output.side_effect = GenerationError("LLM timeout")

        uc = _build_use_case(
            llm_provider=llm,
            consultation_repo=consultation_repo,
            transcript_repo=transcript_repo,
            patient_repo=patient_repo,
            audit_repo=audit_repo,
        )
        uc.execute(consultation_id="cons-001", clinic_id="clinic-001")

        audit_calls = audit_repo.append.call_args_list
        event_types = [c[0][0].event_type for c in audit_calls]
        self.assertIn(AuditAction.PROCESSING_STARTED, event_types)
        self.assertIn(AuditAction.PROCESSING_FAILED, event_types)

    @_patch_time_and_id
    def test_completed_audit_event_has_partial_false(self, mock_time, mock_uuid) -> None:
        consultation = make_sample_consultation(
            status=ConsultationStatus.IN_PROCESSING,
        )
        consultation_repo = MagicMock()
        consultation_repo.find_by_id.return_value = consultation
        transcript_repo = MagicMock()
        transcript_repo.get_normalized_transcript.return_value = MagicMock(
            transcript_text="Doutor: oi. Paciente: Estou com dor de cabeca ha dois dias."
        )
        patient_repo = MagicMock()
        patient_repo.find_by_id.return_value = make_sample_patient()
        audit_repo = MagicMock()
        llm = _make_llm_provider_mock(
            anamnesis_output=make_sample_anamnesis_output(),
            summary_output=make_sample_summary_output(),
            insights_output=make_sample_insights_output(),
        )

        uc = _build_use_case(
            llm_provider=llm,
            consultation_repo=consultation_repo,
            transcript_repo=transcript_repo,
            patient_repo=patient_repo,
            audit_repo=audit_repo,
        )
        uc.execute(consultation_id="cons-001", clinic_id="clinic-001")

        completed_events = [
            c[0][0]
            for c in audit_repo.append.call_args_list
            if c[0][0].event_type == AuditAction.PROCESSING_COMPLETED
        ]
        self.assertEqual(len(completed_events), 1)
        self.assertFalse(completed_events[0].payload["partial"])


class TestRunPipelineResultFields(unittest.TestCase):
    """Tests for PipelineResult fields in various scenarios."""

    @_patch_time_and_id
    def test_completed_result_has_timestamps(self, mock_time, mock_uuid) -> None:
        consultation = make_sample_consultation(
            status=ConsultationStatus.IN_PROCESSING,
        )
        consultation_repo = MagicMock()
        consultation_repo.find_by_id.return_value = consultation
        transcript_repo = MagicMock()
        transcript_repo.get_normalized_transcript.return_value = MagicMock(
            transcript_text="Doutor: oi. Paciente: Estou com dor de cabeca ha dois dias."
        )
        patient_repo = MagicMock()
        patient_repo.find_by_id.return_value = make_sample_patient()
        llm = _make_llm_provider_mock(
            anamnesis_output=make_sample_anamnesis_output(),
            summary_output=make_sample_summary_output(),
            insights_output=make_sample_insights_output(),
        )

        uc = _build_use_case(
            llm_provider=llm,
            consultation_repo=consultation_repo,
            transcript_repo=transcript_repo,
            patient_repo=patient_repo,
        )
        result = uc.execute(consultation_id="cons-001", clinic_id="clinic-001")

        self.assertEqual(result.started_at, _FIXED_TIME)
        self.assertEqual(result.completed_at, _FIXED_TIME)
        self.assertEqual(result.error_message, "")

    @_patch_time_and_id
    def test_failed_result_has_error_message(self, mock_time, mock_uuid) -> None:
        consultation = make_sample_consultation(
            status=ConsultationStatus.IN_PROCESSING,
        )
        consultation_repo = MagicMock()
        consultation_repo.find_by_id.return_value = consultation
        transcript_repo = MagicMock()
        transcript_repo.get_normalized_transcript.return_value = MagicMock(
            transcript_text="Doutor: oi."
        )
        patient_repo = MagicMock()
        patient_repo.find_by_id.return_value = make_sample_patient()
        llm = MagicMock()
        llm.generate_structured_output.side_effect = GenerationError("LLM broke")

        uc = _build_use_case(
            llm_provider=llm,
            consultation_repo=consultation_repo,
            transcript_repo=transcript_repo,
            patient_repo=patient_repo,
        )
        result = uc.execute(consultation_id="cons-001", clinic_id="clinic-001")

        self.assertEqual(result.status, PipelineStatus.FAILED)
        self.assertIn("LLM broke", result.error_message)
        self.assertIsNone(result.medical_history)
        self.assertIsNone(result.summary)
        self.assertIsNone(result.insights)


if __name__ == "__main__":
    unittest.main()
