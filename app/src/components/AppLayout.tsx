import type { ReactNode } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/use-auth';
import { BrandLogo } from './BrandLogo';

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
          <p>Documentacao clinica assistida por IA</p>
        </div>

        <div className="header-actions">
          <div className="doctor-meta">
            <strong>{profile?.user.name ?? 'Medico'}</strong>
            <span>
              Plano: <code>{profile?.user.plan_type ?? 'indisponivel'}</code>
            </span>
          </div>
          <button type="button" className="secondary-button" onClick={handleLogout}>
            Sair
          </button>
        </div>
      </header>

      <nav className="app-nav" aria-label="Navegacao principal">
        <NavLink
          to="/consultations"
          className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
          end
        >
          Consultas
        </NavLink>
      </nav>

      <main className="app-content">{children}</main>
    </div>
  );
}
