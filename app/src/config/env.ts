export interface RuntimeConfig {
  apiBaseUrl: string;
  wsBaseUrl: string;
  contractVersion: string;
}

export const runtimeConfig: RuntimeConfig = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000',
  wsBaseUrl: import.meta.env.VITE_WS_BASE_URL ?? 'ws://localhost:9000',
  contractVersion: import.meta.env.VITE_CONTRACT_VERSION ?? 'v1',
};
