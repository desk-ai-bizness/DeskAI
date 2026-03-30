import type { ReactNode } from 'react';

interface AppLayoutProps {
  children: ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>DeskAI</h1>
        <p>Assistente de documentacao clinica</p>
      </header>
      <main>{children}</main>
    </div>
  );
}
