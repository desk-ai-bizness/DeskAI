import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError } from '../api/client';
import { LoginPage } from './LoginPage';

const loginMock = vi.fn();
const useAuthMock = vi.fn();
const navigateMock = vi.fn();

vi.mock('../auth/use-auth', () => ({
  useAuth: () => useAuthMock(),
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});

describe('LoginPage', () => {
  beforeEach(() => {
    loginMock.mockReset();
    navigateMock.mockReset();

    useAuthMock.mockReturnValue({
      isAuthenticated: false,
      login: loginMock,
    });
  });

  it('submits credentials and navigates to consultations', async () => {
    loginMock.mockResolvedValue(undefined);

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    await userEvent.type(screen.getByLabelText('Email'), 'medico@example.com');
    await userEvent.type(screen.getByLabelText('Senha'), 'senha-segura');
    await userEvent.click(screen.getByRole('button', { name: 'Entrar' }));

    expect(loginMock).toHaveBeenCalledWith('medico@example.com', 'senha-segura');
    expect(navigateMock).toHaveBeenCalledWith('/consultations', { replace: true });
  });

  it('shows backend error on failed sign-in', async () => {
    loginMock.mockRejectedValue(new ApiError('Email ou senha incorretos.', 401, 'unauthorized'));

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    await userEvent.type(screen.getByLabelText('Email'), 'medico@example.com');
    await userEvent.type(screen.getByLabelText('Senha'), 'senha-incorreta');
    await userEvent.click(screen.getByRole('button', { name: 'Entrar' }));

    expect(await screen.findByText('Email ou senha incorretos.')).toBeInTheDocument();
  });

  it('does not show developer-facing authentication notes', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    expect(
      screen.queryByText(/Login social e SSO nao estao disponiveis/i),
    ).not.toBeInTheDocument();
  });
});
