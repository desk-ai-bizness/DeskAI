import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from 'react';
import type { ReactNode } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import {
  getCurrentUser,
  getUiConfig,
  login as loginRequest,
  logout as logoutRequest,
} from '../api/endpoints';
import { queryKeys } from '../api/query-hooks';
import { ApiError } from '../api/client';
import { clearAuthSession, loadAuthSession, saveAuthSession } from './sessionStorage';
import type { AuthSession, UiConfigView, UserProfileView } from '../types/contracts';
import { AuthContext } from './auth-context-store';
import type { AuthContextValue } from './auth-context-store';

function isSessionExpired(session: AuthSession): boolean {
  const expiresAt = Date.parse(session.expiresAt);
  if (Number.isNaN(expiresAt)) {
    return true;
  }

  return expiresAt <= Date.now();
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [session, setSession] = useState<AuthSession | null>(null);
  const [profile, setProfile] = useState<UserProfileView | null>(null);
  const [uiConfig, setUiConfig] = useState<UiConfigView | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const clearState = useCallback(() => {
    clearAuthSession();
    setSession(null);
    setProfile(null);
    setUiConfig(null);
    queryClient.clear();
  }, [queryClient]);

  const refresh = useCallback(async () => {
    const [user, config] = await Promise.all([
      queryClient.fetchQuery({
        queryKey: queryKeys.currentUser(),
        queryFn: getCurrentUser,
      }),
      queryClient.fetchQuery({
        queryKey: queryKeys.uiConfig(),
        queryFn: getUiConfig,
        staleTime: 60_000,
      }),
    ]);
    setProfile(user);
    setUiConfig(config);
  }, [queryClient]);

  const restoreSession = useCallback(async () => {
    const storedSession = loadAuthSession();
    if (!storedSession || isSessionExpired(storedSession)) {
      clearState();
      return;
    }

    setSession(storedSession);

    try {
      await refresh();
    } catch {
      clearState();
    }
  }, [clearState, refresh]);

  useEffect(() => {
    void (async () => {
      try {
        await restoreSession();
      } finally {
        setIsLoading(false);
      }
    })();
  }, [restoreSession]);

  const login = useCallback(
    async (email: string, password: string) => {
      const response = await loginRequest(email, password);
      const expiresAt = new Date(Date.now() + response.expires_in * 1000).toISOString();
      const nextSession: AuthSession = {
        accessToken: response.access_token,
        refreshToken: response.refresh_token,
        expiresAt,
      };

      saveAuthSession(nextSession);
      setSession(nextSession);

      try {
        await refresh();
      } catch (error) {
        clearState();
        if (error instanceof ApiError) {
          throw error;
        }

        throw new ApiError('Nao foi possivel carregar sua sessao.', 500, 'session_load_failed');
      }
    },
    [clearState, refresh],
  );

  const logout = useCallback(async () => {
    try {
      await logoutRequest();
    } catch {
      // Best-effort logout in the backend; local session is always cleared.
    } finally {
      clearState();
    }
  }, [clearState]);

  const value = useMemo<AuthContextValue>(
    () => ({
      session,
      profile,
      uiConfig,
      isLoading,
      isAuthenticated: Boolean(session && profile),
      login,
      logout,
      refresh,
    }),
    [isLoading, login, logout, profile, refresh, session, uiConfig],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
