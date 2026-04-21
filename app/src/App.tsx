import { Navigate, Outlet, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './auth/auth-context';
import { useAuth } from './auth/use-auth';
import { AppLayout } from './components/AppLayout';
import { BrandLogo } from './components/BrandLogo';
import { RequireAuth } from './components/RequireAuth';
import { Card, Loader } from './components/ui';
import { ConsultationEntryPage } from './pages/ConsultationEntryPage';
import { ConsultationsPage } from './pages/ConsultationsPage';
import { LiveConsultationPage } from './pages/LiveConsultationPage';
import { LoginPage } from './pages/LoginPage';
import { PatientDetailPage } from './pages/PatientDetailPage';
import { ReviewPage } from './pages/ReviewPage';

function AppShell() {
  return (
    <AppLayout>
      <Outlet />
    </AppLayout>
  );
}

function AppRoutes() {
  const { isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="auth-shell">
        <Card className="auth-card">
          <BrandLogo size="compact" />
          <Loader label="Carregando configuração da sessão" />
        </Card>
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<RequireAuth />}>
        <Route element={<AppShell />}>
          <Route path="/" element={<Navigate to="/nova-consulta" replace />} />
          <Route path="/nova-consulta" element={<ConsultationEntryPage />} />
          <Route path="/patients/:patientId" element={<PatientDetailPage />} />
          <Route path="/consultations" element={<ConsultationsPage />} />
          <Route path="/consultations/:consultationId/live" element={<LiveConsultationPage />} />
          <Route path="/consultations/:consultationId/review" element={<ReviewPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}

export default App;
