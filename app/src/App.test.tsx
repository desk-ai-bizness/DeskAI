import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App from './App';

const useAuthMock = vi.fn();

vi.mock('./auth/auth-context', () => ({
  AuthProvider: ({ children }: { children: ReactNode }) => <>{children}</>,
}));

vi.mock('./auth/use-auth', () => ({
  useAuth: () => useAuthMock(),
}));

vi.mock('./pages/ConsultationsPage', () => ({
  ConsultationsPage: () => <div>Consultas somente</div>,
}));

vi.mock('./pages/ConsultationEntryPage', () => ({
  ConsultationEntryPage: () => <div>Conteudo nova consulta</div>,
}));

vi.mock('./pages/PatientDetailPage', () => ({
  PatientDetailPage: () => <div>Paciente selecionado</div>,
}));

vi.mock('./pages/LiveConsultationPage', () => ({
  LiveConsultationPage: () => <div>Sessao ao vivo</div>,
}));

vi.mock('./pages/ReviewPage', () => ({
  ReviewPage: () => <div>Revisao</div>,
}));

describe('App routes', () => {
  beforeEach(() => {
    useAuthMock.mockReset();
    useAuthMock.mockReturnValue({
      isLoading: false,
      isAuthenticated: true,
      profile: {
        user: {
          name: 'Dra. Maria',
          plan_type: 'plus',
        },
      },
      logout: vi.fn(),
    });
  });

  it('routes authenticated home visits to the staged consultation entry flow', async () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByText('Conteudo nova consulta')).toBeInTheDocument();
  });

  it('keeps /consultations available as the consultation history screen', async () => {
    render(
      <MemoryRouter initialEntries={['/consultations']}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByText('Consultas somente')).toBeInTheDocument();
  });
});
