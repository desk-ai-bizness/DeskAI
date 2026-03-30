import { useEffect, useState } from 'react';
import { apiGet } from '../api/client';
import type { UiConfigView } from '../types/contracts';

export function useUiConfig() {
  const [config, setConfig] = useState<UiConfigView | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function loadConfig() {
      try {
        const response = await apiGet<UiConfigView>('/v1/ui-config');
        if (mounted) {
          setConfig(response);
        }
      } catch {
        if (mounted) {
          setError('Falha tecnica ao carregar configuracoes de interface.');
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    void loadConfig();

    return () => {
      mounted = false;
    };
  }, []);

  return { config, loading, error };
}
