import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError, createApiClient } from './client';

const fetchMock = vi.fn();

describe('createApiClient', () => {
  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal('fetch', fetchMock);
  });

  it('sends authorization and contract headers', async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ user: { doctor_id: 'doc-1' } }),
    } as Response);

    const client = createApiClient({
      apiBaseUrl: 'https://api.example.com',
      contractVersion: 'v1',
      getAccessToken: () => 'access-token',
    });

    await client.get('/v1/me');

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledWith(
      'https://api.example.com/v1/me',
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({
          Authorization: 'Bearer access-token',
          'X-Contract-Version': 'v1',
        }),
      }),
    );
  });

  it('throws ApiError with backend code and message', async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 403,
      json: async () => ({
        error: {
          code: 'plan_limit_exceeded',
          message: 'Voce atingiu o limite de consultas do seu plano este mes.',
        },
      }),
    } as Response);

    const client = createApiClient({
      apiBaseUrl: 'https://api.example.com',
      contractVersion: 'v1',
      getAccessToken: () => 'access-token',
    });

    await expect(client.post('/v1/consultations', {})).rejects.toEqual(
      new ApiError(
        'Voce atingiu o limite de consultas do seu plano este mes.',
        403,
        'plan_limit_exceeded',
      ),
    );
  });
});

