import { FormEvent, useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { ApiError } from '../api/client';
import { useAuth } from '../auth/use-auth';
import { BrandLogo } from '../components/BrandLogo';
import {
  Alert,
  Button,
  Card,
  Heading,
  Text,
  TextField,
} from '../components/ui';

interface LocationState {
  from?: {
    pathname?: string;
  };
}

export function LoginPage() {
  const { isAuthenticated, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as LocationState | null;

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (isAuthenticated) {
    return <Navigate to="/consultations" replace />;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await login(email, password);
      navigate(state?.from?.pathname ?? '/consultations', { replace: true });
    } catch (requestError) {
      if (requestError instanceof ApiError) {
        setError(requestError.message);
      } else {
        setError('Nao foi possivel iniciar sessao. Tente novamente.');
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="auth-shell login-shell-wrap">
      <div className="login-ambient" aria-hidden="true" />

      <div className="login-shell two-column-layout">
        <section className="login-showcase" aria-label="Visao geral do produto">
          <div className="login-brand-lockup">
            <BrandLogo iconTestId="notter-login-logo-icon" />
          </div>
          <p className="login-chip">Notter para medicos</p>
          <h1>Documentacao clinica mais clara, com revisao humana em cada etapa.</h1>
          <p className="login-lead">
            Organize consultas com apoio de IA sem perder controle sobre o conteudo final.
          </p>

          <ul className="login-benefits">
            <li className="login-benefit">Transcricao da consulta para acompanhamento continuo.</li>
            <li className="login-benefit">Rascunho estruturado para revisar e editar com rapidez.</li>
            <li className="login-benefit">Fluxo seguro de finalizacao e exportacao para o prontuario.</li>
          </ul>
        </section>

        <Card className="auth-card login-card">
          <div className="login-header">
            <p className="login-eyebrow">Area autenticada</p>
            <Heading level={2}>Entrar</Heading>
            <Text tone="muted">Acesse sua conta para iniciar ou revisar consultas.</Text>
          </div>

          <form onSubmit={handleSubmit} className="auth-form">
            <TextField
              id="email"
              name="email"
              label="Email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />

            <TextField
              id="password"
              name="password"
              label="Senha"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />

            {error ? (
              <Alert tone="danger">
                {error}
              </Alert>
            ) : null}

            <Button type="submit" className="login-submit" isLoading={isSubmitting}>
              <span>{isSubmitting ? 'Entrando...' : 'Entrar'}</span>
            </Button>
          </form>

          <p className="auth-note">
            Acesso restrito a profissionais autorizados.
          </p>
        </Card>
      </div>
    </div>
  );
}
