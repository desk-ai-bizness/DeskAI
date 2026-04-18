import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AppLayout } from './AppLayout';

const logoutMock = vi.fn();
const navigateMock = vi.fn();
const useAuthMock = vi.fn();

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

describe('AppLayout', () => {
  beforeEach(() => {
    logoutMock.mockReset();
    navigateMock.mockReset();

    useAuthMock.mockReturnValue({
      profile: {
        user: {
          name: 'Dra. Maria',
          plan_type: 'plus',
        },
      },
      logout: logoutMock,
    });
  });

  it('shows Notter branding with logo assets in the authenticated shell', () => {
    render(
      <MemoryRouter>
        <AppLayout>
          <p>Conteudo autenticado</p>
        </AppLayout>
      </MemoryRouter>,
    );

    const banner = screen.getByRole('banner');

    expect(within(banner).getByRole('img', { name: 'Notter' })).toHaveAttribute(
      'src',
      '/logo-text.png',
    );
    expect(screen.getByTestId('notter-app-logo-icon')).toHaveAttribute('src', '/logo-icon.png');
    expect(screen.queryByText(/DeskAI/i)).not.toBeInTheDocument();
    expect(screen.getByText('Documentacao clinica assistida por IA')).toBeInTheDocument();
  });

  it('keeps the existing sign-out behavior', async () => {
    logoutMock.mockResolvedValue(undefined);

    render(
      <MemoryRouter>
        <AppLayout>
          <p>Conteudo autenticado</p>
        </AppLayout>
      </MemoryRouter>,
    );

    await userEvent.click(screen.getByRole('button', { name: 'Sair' }));

    expect(logoutMock).toHaveBeenCalledTimes(1);
    expect(navigateMock).toHaveBeenCalledWith('/login');
  });
});
