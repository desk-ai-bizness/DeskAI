import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../auth/use-auth';

export function RequireAuth() {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <section className="panel">
        <h2>Carregando sessao...</h2>
        <p>Validando suas credenciais e configuracoes de interface.</p>
      </section>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
}
