import { QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { useState } from 'react';
import { createAppQueryClient } from '../api/query-hooks';

export function QueryTestProvider({ children }: { children: ReactNode }) {
  const [queryClient] = useState(() => createAppQueryClient());

  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
