import { AppLayout } from './components/AppLayout';
import { ConsultationPage } from './pages/ConsultationPage';
import { DashboardPage } from './pages/DashboardPage';
import { useUiConfig } from './hooks/useUiConfig';

function App() {
  const { config, loading, error } = useUiConfig();

  return (
    <AppLayout>
      {loading && <p className="panel">Carregando configuracoes...</p>}
      {error && <p className="panel error">{error}</p>}
      {!loading && !error && (
        <>
          <DashboardPage />
          <ConsultationPage />
          <section className="panel">
            <h2>Configuração ativa</h2>
            <p>Versao: {config?.version ?? 'indisponivel'}</p>
            <p>Locale: {config?.locale ?? 'indisponivel'}</p>
          </section>
        </>
      )}
    </AppLayout>
  );
}

export default App;
