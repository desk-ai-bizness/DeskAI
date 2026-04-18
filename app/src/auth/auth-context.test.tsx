import { QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { AuthProvider } from './auth-context';
import { useAuth } from './use-auth';
import { createAppQueryClient, queryKeys } from '../api/query-hooks';

const logoutMock = vi.fn();

vi.mock('../api/endpoints', () => ({
  getCurrentUser: vi.fn(),
  getUiConfig: vi.fn(),
  login: vi.fn(),
  logout: () => logoutMock(),
}));

vi.mock('./sessionStorage', () => ({
  clearAuthSession: vi.fn(),
  loadAuthSession: vi.fn(() => null),
  saveAuthSession: vi.fn(),
}));

function LogoutButton() {
  const { logout } = useAuth();

  return (
    <button type="button" onClick={() => void logout()}>
      Sair
    </button>
  );
}

describe('AuthProvider query cache handling', () => {
  it('clears sensitive query cache on logout', async () => {
    const queryClient = createAppQueryClient();
    queryClient.setQueryData(queryKeys.consultations.list(), {
      consultations: [{ consultation_id: 'cons-sensitive' }],
    });
    queryClient.setQueryData(queryKeys.currentUser(), {
      user: { name: 'Dra. Maria' },
    });
    logoutMock.mockResolvedValue(undefined);

    render(
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <LogoutButton />
        </AuthProvider>
      </QueryClientProvider>,
    );

    await userEvent.click(screen.getByRole('button', { name: 'Sair' }));

    await waitFor(() => {
      expect(queryClient.getQueryCache().getAll()).toHaveLength(0);
    });
  });
});
