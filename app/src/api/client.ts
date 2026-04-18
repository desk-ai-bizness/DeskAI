import { runtimeConfig } from '../config/env';
import { loadAuthSession } from '../auth/sessionStorage';
import type { ApiErrorEnvelope } from '../types/contracts';

interface ApiClientConfig {
  apiBaseUrl: string;
  contractVersion: string;
  getAccessToken?: () => string | null;
}

interface RequestOptions {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
  body?: unknown;
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details?: Record<string, unknown>;

  constructor(
    message: string,
    status: number,
    code = 'request_failed',
    details?: Record<string, unknown>,
  ) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export interface ApiClient {
  get<T>(path: string): Promise<T>;
  post<T>(path: string, body?: unknown): Promise<T>;
  put<T>(path: string, body?: unknown): Promise<T>;
  delete(path: string): Promise<void>;
}

function normalizePath(path: string): string {
  if (path.startsWith('/')) {
    return path;
  }
  return `/${path}`;
}

async function parseJsonSafe(response: Response): Promise<unknown> {
  if (typeof response.text === 'function') {
    const text = await response.text();
    if (!text) {
      return null;
    }

    try {
      return JSON.parse(text) as unknown;
    } catch {
      return null;
    }
  }

  if (typeof response.json === 'function') {
    try {
      return (await response.json()) as unknown;
    } catch {
      return null;
    }
  }

  return null;
}

function extractApiError(
  fallbackStatus: number,
  payload: unknown,
): ApiError {
  if (
    payload &&
    typeof payload === 'object' &&
    'error' in payload &&
    typeof (payload as ApiErrorEnvelope).error?.message === 'string'
  ) {
    const apiPayload = payload as ApiErrorEnvelope;
    return new ApiError(
      apiPayload.error.message,
      fallbackStatus,
      apiPayload.error.code,
      apiPayload.error.details,
    );
  }

  return new ApiError(
    'Falha tecnica ao comunicar com o backend.',
    fallbackStatus,
  );
}

export function createApiClient(config: ApiClientConfig): ApiClient {
  async function request<T>(path: string, options: RequestOptions): Promise<T> {
    const headers: Record<string, string> = {
      'X-Contract-Version': config.contractVersion,
    };

    if (options.body !== undefined) {
      headers['Content-Type'] = 'application/json';
    }

    const token = config.getAccessToken?.();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    let response: Response;
    try {
      response = await fetch(`${config.apiBaseUrl}${normalizePath(path)}`, {
        method: options.method,
        headers,
        body:
          options.body !== undefined
            ? JSON.stringify(options.body)
            : undefined,
      });
    } catch {
      throw new ApiError('Falha de conexão com o servidor.', 0, 'network_error');
    }

    const payload = await parseJsonSafe(response);

    if (!response.ok) {
      throw extractApiError(response.status, payload);
    }

    return payload as T;
  }

  return {
    get<T>(path: string) {
      return request<T>(path, { method: 'GET' });
    },
    post<T>(path: string, body?: unknown) {
      return request<T>(path, { method: 'POST', body });
    },
    put<T>(path: string, body?: unknown) {
      return request<T>(path, { method: 'PUT', body });
    },
    async delete(path: string) {
      await request<unknown>(path, { method: 'DELETE' });
    },
  };
}

export const apiClient = createApiClient({
  apiBaseUrl: runtimeConfig.apiBaseUrl,
  contractVersion: runtimeConfig.contractVersion,
  getAccessToken: () => loadAuthSession()?.accessToken ?? null,
});
