"""Comprehensive validation tests for all domain dataclasses."""

import unittest
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

# --- Audit domain ---
from deskai.domain.audit.entities import AuditAction, AuditEvent

# --- Auth domain ---
from deskai.domain.auth.entities import DoctorProfile
from deskai.domain.auth.value_objects import AuthContext, Entitlements, PlanType, Tokens

# --- Consultation domain ---
from deskai.domain.consultation.entities import Consultation, ConsultationStatus
from deskai.domain.consultation.events import ConsultationCreated, ConsultationStatusChanged
from deskai.domain.consultation.value_objects import ArtifactPointer, ArtifactType

# --- Patient domain ---
from deskai.domain.patient.entities import Patient

# --- Session domain ---
from deskai.domain.session.entities import Session, SessionState
from deskai.domain.session.value_objects import AudioChunk, ConnectionInfo

# --- Transcription domain ---
from deskai.domain.transcription.entities import NormalizedTranscript
from deskai.domain.transcription.value_objects import (
    FinalTranscript,
    PartialTranscript,
    SpeakerSegment,
    TranscriptionSessionInfo,
)
from deskai.shared.errors import DomainValidationError

# =========================================================================
# Consultation entity validation
# =========================================================================


class TestConsultationValidation(unittest.TestCase):
    def _make(self, **overrides):
        defaults = dict(
            consultation_id="c-1",
            clinic_id="cl-1",
            doctor_id="d-1",
            patient_id="p-1",
            specialty="general",
        )
        defaults.update(overrides)
        return Consultation(**defaults)

    def test_valid_creation(self):
        c = self._make()
        self.assertEqual(c.consultation_id, "c-1")

    def test_frozen(self):
        c = self._make()
        with self.assertRaises(FrozenInstanceError):
            c.status = ConsultationStatus.RECORDING  # type: ignore[misc]

    def test_empty_consultation_id(self):
        with self.assertRaises(DomainValidationError):
            self._make(consultation_id="")

    def test_whitespace_consultation_id(self):
        with self.assertRaises(DomainValidationError):
            self._make(consultation_id="   ")

    def test_empty_clinic_id(self):
        with self.assertRaises(DomainValidationError):
            self._make(clinic_id="")

    def test_empty_doctor_id(self):
        with self.assertRaises(DomainValidationError):
            self._make(doctor_id="")

    def test_empty_patient_id(self):
        with self.assertRaises(DomainValidationError):
            self._make(patient_id="")

    def test_empty_specialty(self):
        with self.assertRaises(DomainValidationError):
            self._make(specialty="")


# =========================================================================
# ArtifactPointer validation
# =========================================================================


class TestArtifactPointerValidation(unittest.TestCase):
    def test_valid_creation(self):
        ap = ArtifactPointer(
            artifact_type=ArtifactType.SUMMARY,
            storage_key="s3://bucket/key",
        )
        self.assertEqual(ap.storage_key, "s3://bucket/key")

    def test_empty_storage_key(self):
        with self.assertRaises(DomainValidationError):
            ArtifactPointer(artifact_type=ArtifactType.SUMMARY, storage_key="")

    def test_whitespace_storage_key(self):
        with self.assertRaises(DomainValidationError):
            ArtifactPointer(artifact_type=ArtifactType.SUMMARY, storage_key="   ")


# =========================================================================
# ConsultationCreated event validation
# =========================================================================


class TestConsultationCreatedValidation(unittest.TestCase):
    def test_valid_creation(self):
        e = ConsultationCreated(
            consultation_id="c-1",
            doctor_id="d-1",
            clinic_id="cl-1",
            patient_id="p-1",
            timestamp="2026-04-01T10:00:00+00:00",
        )
        self.assertEqual(e.consultation_id, "c-1")

    def test_empty_consultation_id(self):
        with self.assertRaises(DomainValidationError):
            ConsultationCreated(
                consultation_id="",
                doctor_id="d-1",
                clinic_id="cl-1",
                patient_id="p-1",
                timestamp="2026-04-01T10:00:00+00:00",
            )

    def test_empty_timestamp(self):
        with self.assertRaises(DomainValidationError):
            ConsultationCreated(
                consultation_id="c-1",
                doctor_id="d-1",
                clinic_id="cl-1",
                patient_id="p-1",
                timestamp="",
            )


# =========================================================================
# ConsultationStatusChanged event validation
# =========================================================================


class TestConsultationStatusChangedValidation(unittest.TestCase):
    def test_valid_creation(self):
        e = ConsultationStatusChanged(
            consultation_id="c-1",
            from_status="started",
            to_status="recording",
            actor_id="d-1",
            timestamp="2026-04-01T10:00:00+00:00",
        )
        self.assertEqual(e.from_status, "started")

    def test_empty_actor_id(self):
        with self.assertRaises(DomainValidationError):
            ConsultationStatusChanged(
                consultation_id="c-1",
                from_status="started",
                to_status="recording",
                actor_id="",
                timestamp="2026-04-01T10:00:00+00:00",
            )


# =========================================================================
# Session entity validation
# =========================================================================


class TestSessionValidation(unittest.TestCase):
    def _make(self, **overrides):
        defaults = dict(
            session_id="s-1",
            consultation_id="c-1",
            doctor_id="d-1",
            clinic_id="cl-1",
        )
        defaults.update(overrides)
        return Session(**defaults)

    def test_valid_creation(self):
        s = self._make()
        self.assertEqual(s.session_id, "s-1")

    def test_frozen(self):
        s = self._make()
        with self.assertRaises(FrozenInstanceError):
            s.state = SessionState.ACTIVE  # type: ignore[misc]

    def test_empty_session_id(self):
        with self.assertRaises(DomainValidationError):
            self._make(session_id="")

    def test_empty_consultation_id(self):
        with self.assertRaises(DomainValidationError):
            self._make(consultation_id="")

    def test_empty_doctor_id(self):
        with self.assertRaises(DomainValidationError):
            self._make(doctor_id="")

    def test_empty_clinic_id(self):
        with self.assertRaises(DomainValidationError):
            self._make(clinic_id="")

    def test_negative_duration_seconds(self):
        with self.assertRaises(DomainValidationError):
            self._make(duration_seconds=-1)

    def test_negative_audio_chunks_received(self):
        with self.assertRaises(DomainValidationError):
            self._make(audio_chunks_received=-1)


# =========================================================================
# AudioChunk validation
# =========================================================================


class TestAudioChunkValidation(unittest.TestCase):
    def test_negative_chunk_index(self):
        with self.assertRaises(DomainValidationError):
            AudioChunk(chunk_index=-1, audio_data=b"\x00", timestamp="t", session_id="s")

    def test_empty_timestamp(self):
        with self.assertRaises(DomainValidationError):
            AudioChunk(chunk_index=0, audio_data=b"\x00", timestamp="", session_id="s")

    def test_empty_session_id(self):
        with self.assertRaises(DomainValidationError):
            AudioChunk(chunk_index=0, audio_data=b"\x00", timestamp="t", session_id="")


# =========================================================================
# ConnectionInfo validation
# =========================================================================


class TestConnectionInfoValidation(unittest.TestCase):
    def test_empty_connection_id(self):
        with self.assertRaises(DomainValidationError):
            ConnectionInfo(
                connection_id="",
                session_id="s",
                doctor_id="d",
                clinic_id="c",
                connected_at="t",
            )

    def test_empty_connected_at(self):
        with self.assertRaises(DomainValidationError):
            ConnectionInfo(
                connection_id="c",
                session_id="s",
                doctor_id="d",
                clinic_id="c",
                connected_at="",
            )


# =========================================================================
# SpeakerSegment validation
# =========================================================================


class TestSpeakerSegmentValidation(unittest.TestCase):
    def test_valid_creation(self):
        seg = SpeakerSegment(
            speaker="Dr",
            text="hello",
            start_time=0.0,
            end_time=1.0,
            confidence=0.9,
        )
        self.assertEqual(seg.speaker, "Dr")

    def test_empty_speaker(self):
        with self.assertRaises(DomainValidationError):
            SpeakerSegment(
                speaker="",
                text="hello",
                start_time=0.0,
                end_time=1.0,
                confidence=0.9,
            )

    def test_negative_start_time(self):
        with self.assertRaises(DomainValidationError):
            SpeakerSegment(
                speaker="Dr",
                text="hello",
                start_time=-1.0,
                end_time=1.0,
                confidence=0.9,
            )

    def test_end_before_start(self):
        with self.assertRaises(DomainValidationError):
            SpeakerSegment(
                speaker="Dr",
                text="hello",
                start_time=2.0,
                end_time=1.0,
                confidence=0.9,
            )

    def test_confidence_above_1(self):
        with self.assertRaises(DomainValidationError):
            SpeakerSegment(
                speaker="Dr",
                text="hello",
                start_time=0.0,
                end_time=1.0,
                confidence=1.1,
            )

    def test_confidence_below_0(self):
        with self.assertRaises(DomainValidationError):
            SpeakerSegment(
                speaker="Dr",
                text="hello",
                start_time=0.0,
                end_time=1.0,
                confidence=-0.1,
            )


# =========================================================================
# PartialTranscript validation
# =========================================================================


class TestPartialTranscriptValidation(unittest.TestCase):
    def test_empty_speaker(self):
        with self.assertRaises(DomainValidationError):
            PartialTranscript(text="hi", speaker="", is_final=False, timestamp="t", confidence=0.5)

    def test_empty_timestamp(self):
        with self.assertRaises(DomainValidationError):
            PartialTranscript(text="hi", speaker="Dr", is_final=False, timestamp="", confidence=0.5)

    def test_confidence_out_of_range(self):
        with self.assertRaises(DomainValidationError):
            PartialTranscript(
                text="hi",
                speaker="Dr",
                is_final=False,
                timestamp="t",
                confidence=2.0,
            )


# =========================================================================
# TranscriptionSessionInfo validation
# =========================================================================


class TestTranscriptionSessionInfoValidation(unittest.TestCase):
    def test_empty_session_id(self):
        with self.assertRaises(DomainValidationError):
            TranscriptionSessionInfo(session_id="", state="active", provider_name="aws")

    def test_empty_state(self):
        with self.assertRaises(DomainValidationError):
            TranscriptionSessionInfo(session_id="s", state="", provider_name="aws")

    def test_empty_provider_name(self):
        with self.assertRaises(DomainValidationError):
            TranscriptionSessionInfo(session_id="s", state="active", provider_name="")


# =========================================================================
# FinalTranscript validation
# =========================================================================


class TestFinalTranscriptValidation(unittest.TestCase):
    def test_empty_session_id(self):
        with self.assertRaises(DomainValidationError):
            FinalTranscript(
                session_id="",
                text="hello",
                speaker_segments=[],
                language="pt-BR",
                provider_name="aws",
            )

    def test_negative_duration(self):
        with self.assertRaises(DomainValidationError):
            FinalTranscript(
                session_id="s",
                text="hello",
                speaker_segments=[],
                language="pt-BR",
                provider_name="aws",
                duration_seconds=-1.0,
            )

    def test_confidence_out_of_range(self):
        with self.assertRaises(DomainValidationError):
            FinalTranscript(
                session_id="s",
                text="hello",
                speaker_segments=[],
                language="pt-BR",
                provider_name="aws",
                confidence=1.5,
            )


# =========================================================================
# NormalizedTranscript validation
# =========================================================================


class TestNormalizedTranscriptValidation(unittest.TestCase):
    def test_valid_creation(self):
        nt = NormalizedTranscript(
            consultation_id="c-1",
            provider_name="aws",
            provider_session_id="ps-1",
            language="pt-BR",
            transcript_text="hello",
            speaker_segments=[],
        )
        self.assertEqual(nt.consultation_id, "c-1")

    def test_frozen(self):
        nt = NormalizedTranscript(
            consultation_id="c-1",
            provider_name="aws",
            provider_session_id="ps-1",
            language="pt-BR",
            transcript_text="hello",
            speaker_segments=[],
        )
        with self.assertRaises(FrozenInstanceError):
            nt.consultation_id = "c-2"  # type: ignore[misc]

    def test_empty_consultation_id(self):
        with self.assertRaises(DomainValidationError):
            NormalizedTranscript(
                consultation_id="",
                provider_name="aws",
                provider_session_id="ps-1",
                language="pt-BR",
                transcript_text="hello",
                speaker_segments=[],
            )

    def test_empty_provider_name(self):
        with self.assertRaises(DomainValidationError):
            NormalizedTranscript(
                consultation_id="c-1",
                provider_name="",
                provider_session_id="ps-1",
                language="pt-BR",
                transcript_text="hello",
                speaker_segments=[],
            )

    def test_empty_language(self):
        with self.assertRaises(DomainValidationError):
            NormalizedTranscript(
                consultation_id="c-1",
                provider_name="aws",
                provider_session_id="ps-1",
                language="",
                transcript_text="hello",
                speaker_segments=[],
            )


# =========================================================================
# DoctorProfile validation
# =========================================================================


class TestDoctorProfileValidation(unittest.TestCase):
    def _make(self, **overrides):
        defaults = dict(
            doctor_id="d-1",
            identity_provider_id="sub-1",
            email="doc@clinic.com",
            name="Dr. Test",
            clinic_id="cl-1",
            clinic_name="Clinic One",
            plan_type=PlanType.FREE_TRIAL,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        defaults.update(overrides)
        return DoctorProfile(**defaults)

    def test_valid_creation(self):
        dp = self._make()
        self.assertEqual(dp.doctor_id, "d-1")

    def test_empty_doctor_id(self):
        with self.assertRaises(DomainValidationError):
            self._make(doctor_id="")

    def test_empty_identity_provider_id(self):
        with self.assertRaises(DomainValidationError):
            self._make(identity_provider_id="")

    def test_invalid_email(self):
        with self.assertRaises(DomainValidationError):
            self._make(email="not-an-email")

    def test_empty_email(self):
        with self.assertRaises(DomainValidationError):
            self._make(email="")

    def test_empty_name(self):
        with self.assertRaises(DomainValidationError):
            self._make(name="")

    def test_empty_clinic_id(self):
        with self.assertRaises(DomainValidationError):
            self._make(clinic_id="")

    def test_empty_clinic_name(self):
        with self.assertRaises(DomainValidationError):
            self._make(clinic_name="")

    def test_empty_created_at(self):
        with self.assertRaises(DomainValidationError):
            self._make(created_at="")


# =========================================================================
# AuthContext validation
# =========================================================================


class TestAuthContextValidation(unittest.TestCase):
    def test_valid_creation(self):
        ac = AuthContext(
            doctor_id="d-1",
            email="doc@clinic.com",
            clinic_id="cl-1",
            plan_type=PlanType.PLUS,
        )
        self.assertEqual(ac.doctor_id, "d-1")

    def test_empty_doctor_id(self):
        with self.assertRaises(DomainValidationError):
            AuthContext(
                doctor_id="",
                email="doc@clinic.com",
                clinic_id="cl-1",
                plan_type=PlanType.PLUS,
            )

    def test_invalid_email(self):
        with self.assertRaises(DomainValidationError):
            AuthContext(doctor_id="d-1", email="bad", clinic_id="cl-1", plan_type=PlanType.PLUS)


# =========================================================================
# Entitlements validation
# =========================================================================


class TestEntitlementsValidation(unittest.TestCase):
    def test_valid_creation(self):
        e = Entitlements(
            can_create_consultation=True,
            consultations_remaining=10,
            consultations_used_this_month=5,
            max_duration_minutes=60,
            export_enabled=True,
            trial_expired=False,
            trial_days_remaining=14,
        )
        self.assertEqual(e.consultations_remaining, 10)

    def test_negative_consultations_remaining(self):
        with self.assertRaises(DomainValidationError):
            Entitlements(
                can_create_consultation=True,
                consultations_remaining=-2,
                consultations_used_this_month=0,
                max_duration_minutes=60,
                export_enabled=True,
                trial_expired=False,
                trial_days_remaining=None,
            )

    def test_negative_max_duration_minutes(self):
        with self.assertRaises(DomainValidationError):
            Entitlements(
                can_create_consultation=True,
                consultations_remaining=10,
                consultations_used_this_month=0,
                max_duration_minutes=-1,
                export_enabled=True,
                trial_expired=False,
                trial_days_remaining=None,
            )

    def test_negative_trial_days_remaining(self):
        with self.assertRaises(DomainValidationError):
            Entitlements(
                can_create_consultation=True,
                consultations_remaining=10,
                consultations_used_this_month=0,
                max_duration_minutes=60,
                export_enabled=True,
                trial_expired=False,
                trial_days_remaining=-1,
            )


# =========================================================================
# Tokens validation
# =========================================================================


class TestTokensValidation(unittest.TestCase):
    def test_valid_creation(self):
        t = Tokens(access_token="abc", refresh_token="def", expires_in=3600)
        self.assertEqual(t.access_token, "abc")

    def test_empty_access_token(self):
        with self.assertRaises(DomainValidationError):
            Tokens(access_token="", refresh_token="def", expires_in=3600)

    def test_none_refresh_token(self):
        with self.assertRaises(DomainValidationError):
            Tokens(access_token="abc", refresh_token=None, expires_in=3600)

    def test_zero_expires_in(self):
        with self.assertRaises(DomainValidationError):
            Tokens(access_token="abc", refresh_token="def", expires_in=0)

    def test_negative_expires_in(self):
        with self.assertRaises(DomainValidationError):
            Tokens(access_token="abc", refresh_token="def", expires_in=-1)


# =========================================================================
# Patient validation
# =========================================================================


class TestPatientValidation(unittest.TestCase):
    def _make(self, **overrides):
        defaults = dict(
            patient_id="p-1",
            name="Maria",
            date_of_birth="1990-01-01",
            clinic_id="cl-1",
            created_at="2026-01-01T00:00:00+00:00",
        )
        defaults.update(overrides)
        return Patient(**defaults)

    def test_valid_creation(self):
        p = self._make()
        self.assertEqual(p.patient_id, "p-1")

    def test_empty_patient_id(self):
        with self.assertRaises(DomainValidationError):
            self._make(patient_id="")

    def test_empty_name(self):
        with self.assertRaises(DomainValidationError):
            self._make(name="")

    def test_empty_date_of_birth(self):
        with self.assertRaises(DomainValidationError):
            self._make(date_of_birth="")

    def test_empty_clinic_id(self):
        with self.assertRaises(DomainValidationError):
            self._make(clinic_id="")

    def test_empty_created_at(self):
        with self.assertRaises(DomainValidationError):
            self._make(created_at="")


# =========================================================================
# AuditEvent validation
# =========================================================================


class TestAuditEventValidation(unittest.TestCase):
    def _make(self, **overrides):
        defaults = dict(
            event_id="e-1",
            consultation_id="c-1",
            event_type=AuditAction.CONSULTATION_CREATED,
            actor_id="d-1",
            timestamp="2026-01-01T00:00:00+00:00",
        )
        defaults.update(overrides)
        return AuditEvent(**defaults)

    def test_valid_creation(self):
        e = self._make()
        self.assertEqual(e.event_id, "e-1")

    def test_empty_event_id(self):
        with self.assertRaises(DomainValidationError):
            self._make(event_id="")

    def test_empty_consultation_id(self):
        with self.assertRaises(DomainValidationError):
            self._make(consultation_id="")

    def test_empty_actor_id(self):
        with self.assertRaises(DomainValidationError):
            self._make(actor_id="")

    def test_empty_timestamp(self):
        with self.assertRaises(DomainValidationError):
            self._make(timestamp="")


if __name__ == "__main__":
    unittest.main()
