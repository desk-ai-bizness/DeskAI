import { runtimeConfig } from '../config/env';

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${runtimeConfig.apiBaseUrl}${path}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'X-Contract-Version': runtimeConfig.contractVersion,
    },
  });

  if (!response.ok) {
    throw new ApiError('Falha tecnica ao consultar o backend.', response.status);
  }

  return (await response.json()) as T;
}
