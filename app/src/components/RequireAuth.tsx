import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../auth/use-auth';
import { Card, Loader, Text } from './ui';

export function RequireAuth() {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <Card title="Carregando sessao">
        <Loader label="Validando sessao" />
        <Text tone="muted">Validando suas credenciais e configuracoes de interface.</Text>
      </Card>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
}
