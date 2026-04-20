import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createPatient, getPatientDetail, getTranscriptionToken, listPatients } from './endpoints';

const getMock = vi.fn();
const postMock = vi.fn();

vi.mock('./client', () => ({
  apiClient: {
    get: (...args: unknown[]) => getMock(...args),
    post: (...args: unknown[]) => postMock(...args),
  },
}));

describe('patient endpoints', () => {
  beforeEach(() => {
    getMock.mockReset();
    postMock.mockReset();
  });

  it('searches patients by encoded name or CPF term', async () => {
    getMock.mockResolvedValue({ patients: [] });

    await listPatients('529.982');

    expect(getMock).toHaveBeenCalledWith('/v1/patients?search=529.982');
  });

  it('creates a patient with required CPF and optional date of birth', async () => {
    postMock.mockResolvedValue({
      patient_id: 'pat-1',
      name: 'Joao Silva',
      cpf: '529.***.***-25',
      date_of_birth: null,
      clinic_id: 'clinic-1',
      created_at: '2026-04-18T10:00:00Z',
    });

    await createPatient({
      name: 'Joao Silva',
      cpf: '529.982.247-25',
      date_of_birth: null,
    });

    expect(postMock).toHaveBeenCalledWith('/v1/patients', {
      name: 'Joao Silva',
      cpf: '529.982.247-25',
      date_of_birth: null,
    });
  });

  it('loads patient detail by id', async () => {
    getMock.mockResolvedValue({ patient: {}, history: [] });

    await getPatientDetail('pat-1');

    expect(getMock).toHaveBeenCalledWith('/v1/patients/pat-1');
  });
});

describe('transcription token endpoint', () => {
  beforeEach(() => {
    postMock.mockReset();
  });

  it('requests a transcription token for a consultation', async () => {
    const tokenResponse = {
      token: 'el-token-abc',
      websocket_url: 'wss://api.elevenlabs.io/v1/speech-to-text/realtime',
      model_id: 'scribe_v2_realtime',
      language_code: 'pt',
      expires_at: '2026-04-19T12:15:00Z',
      expires_in_seconds: 900,
    };
    postMock.mockResolvedValue(tokenResponse);

    const result = await getTranscriptionToken('cons-1');

    expect(postMock).toHaveBeenCalledWith('/v1/consultations/cons-1/transcription-token');
    expect(result.token).toBe('el-token-abc');
    expect(result.expires_in_seconds).toBe(900);
  });
});
