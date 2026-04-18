import type { AuthSession } from '../types/contracts';

const AUTH_SESSION_STORAGE_KEY = 'deskai.auth.session';

function isString(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0;
}

export function loadAuthSession(): AuthSession | null {
  const raw = sessionStorage.getItem(AUTH_SESSION_STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    const parsed: unknown = JSON.parse(raw);
    if (
      typeof parsed === 'object' &&
      parsed !== null &&
      isString((parsed as Record<string, unknown>).accessToken) &&
      isString((parsed as Record<string, unknown>).refreshToken) &&
      isString((parsed as Record<string, unknown>).expiresAt)
    ) {
      return {
        accessToken: (parsed as Record<string, string>).accessToken,
        refreshToken: (parsed as Record<string, string>).refreshToken,
        expiresAt: (parsed as Record<string, string>).expiresAt,
      };
    }
  } catch {
    // Ignore malformed session payloads and force a fresh login.
  }

  return null;
}

export function saveAuthSession(session: AuthSession): void {
  sessionStorage.setItem(AUTH_SESSION_STORAGE_KEY, JSON.stringify(session));
}

export function clearAuthSession(): void {
  sessionStorage.removeItem(AUTH_SESSION_STORAGE_KEY);
}
