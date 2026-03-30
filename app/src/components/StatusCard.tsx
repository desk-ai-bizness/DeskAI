interface StatusCardProps {
  title: string;
  value: string;
}

export function StatusCard({ title, value }: StatusCardProps) {
  return (
    <article className="status-card">
      <h2>{title}</h2>
      <p>{value}</p>
    </article>
  );
}
