import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createPatient, getPatientDetail, listPatients } from './endpoints';

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
