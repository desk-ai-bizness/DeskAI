import { beforeEach, describe, expect, it } from 'vitest';
import {
  clearAuthSession,
  loadAuthSession,
  saveAuthSession,
} from './sessionStorage';

describe('sessionStorage', () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it('returns null when there is no stored session', () => {
    expect(loadAuthSession()).toBeNull();
  });

  it('persists and restores the auth session', () => {
    saveAuthSession({
      accessToken: 'token-123',
      refreshToken: 'refresh-123',
      expiresAt: '2026-04-11T20:00:00.000Z',
    });

    expect(loadAuthSession()).toEqual({
      accessToken: 'token-123',
      refreshToken: 'refresh-123',
      expiresAt: '2026-04-11T20:00:00.000Z',
    });
  });

  it('clears the stored session', () => {
    saveAuthSession({
      accessToken: 'token-123',
      refreshToken: 'refresh-123',
      expiresAt: '2026-04-11T20:00:00.000Z',
    });

    clearAuthSession();
    expect(loadAuthSession()).toBeNull();
  });
});

