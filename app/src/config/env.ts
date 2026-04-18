export interface RuntimeConfig {
  apiBaseUrl: string;
  wsBaseUrl: string;
  contractVersion: string;
}

function stripTrailingSlash(value: string): string {
  return value.endsWith('/') ? value.slice(0, -1) : value;
}

export const runtimeConfig: RuntimeConfig = {
  apiBaseUrl: stripTrailingSlash(
    import.meta.env.VITE_API_BASE_URL ?? '/api',
  ),
  wsBaseUrl: stripTrailingSlash(
    import.meta.env.VITE_WS_BASE_URL ?? 'ws://localhost:9000',
  ),
  contractVersion: import.meta.env.VITE_CONTRACT_VERSION ?? 'v1',
};
