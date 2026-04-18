import { createContext } from 'react';
import type { AuthSession, UiConfigView, UserProfileView } from '../types/contracts';

export interface AuthContextValue {
  session: AuthSession | null;
  profile: UserProfileView | null;
  uiConfig: UiConfigView | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined);
