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

  it('shows Notter branding with the new logo assets', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    expect(screen.getByText('Notter para médicos')).toBeInTheDocument();
    expect(screen.queryByText('Notter para medicos')).not.toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Entrar' })).toBeInTheDocument();
    expect(screen.queryByText(/DeskAI/i)).not.toBeInTheDocument();

    const brandLogo = screen.getByRole('img', { name: 'Notter' });
    expect(brandLogo).toHaveAttribute('src', '/logo-text.png');
    expect(brandLogo.closest('.brand-logo')).toHaveClass('brand-logo-light');

    const iconLogo = screen.getByTestId('notter-login-logo-icon');
    expect(iconLogo).toHaveAttribute('src', '/logo-icon.png');
    expect(iconLogo.closest('.brand-logo')).toHaveClass('brand-logo-light');
  });

  it('does not render the removed login ambient background treatment', () => {
    const { container } = render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    expect(container.querySelector('.login-ambient')).not.toBeInTheDocument();
  });

  it('uses design-system primitives for the sign-in form', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    expect(screen.getByRole('heading', { name: 'Entrar' }).closest('.ds-card')).toBeInTheDocument();
    expect(screen.getByLabelText('Email')).toHaveClass('ds-input');
    expect(screen.getByRole('button', { name: 'Entrar' })).toHaveClass('ds-button');
  });
});
