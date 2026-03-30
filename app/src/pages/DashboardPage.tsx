import { StatusCard } from '../components/StatusCard';

export function DashboardPage() {
  return (
    <section className="dashboard-grid">
      <StatusCard title="Status de conexao" value="Aguardando backend" />
      <StatusCard title="Sessao ativa" value="Nenhuma" />
      <StatusCard title="Contrato" value="v1" />
    </section>
  );
}
