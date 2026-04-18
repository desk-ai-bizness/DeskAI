import type { ReactNode } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/use-auth';
import { BrandLogo } from './BrandLogo';
import { Button, Chip } from './ui';

interface AppLayoutProps {
  children: ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  const navigate = useNavigate();
  const { profile, logout } = useAuth();

  async function handleLogout() {
    await logout();
    navigate('/login');
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-brand">
          <BrandLogo iconTestId="notter-app-logo-icon" />
          <p>Documentação clínica assistida por IA</p>
        </div>

        <div className="header-actions">
          <div className="doctor-meta">
            <strong>{profile?.user.name ?? 'Médico'}</strong>
            <span>
              Plano: <Chip>{profile?.user.plan_type ?? 'indisponível'}</Chip>
            </span>
          </div>
          <Button type="button" variant="secondary" onClick={handleLogout}>
            Sair
          </Button>
        </div>
      </header>

      <nav className="app-nav" aria-label="Navegação principal">
        <NavLink
          to="/consultations"
          className={({ isActive }) => (isActive ? 'app-nav-link active' : 'app-nav-link')}
          end
        >
          Consultas
        </NavLink>
      </nav>

      <main className="app-content">{children}</main>
    </div>
  );
}
