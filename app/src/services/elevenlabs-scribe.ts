import type { TranscriptionTokenView } from '../types/contracts';

export interface ScribeConfig {
  modelId?: string;
  languageCode?: string;
  commitStrategy?: string;
  includeTimestamps?: boolean;
  audioFormat?: string;
}

export interface ScribePartialEvent {
  type: 'partial_transcript';
  text: string;
}

export interface ScribeCommittedEvent {
  type: 'committed_transcript';
  text: string;
  speaker: string;
  start_time: number | null;
  end_time: number | null;
  confidence: number | null;
}

export interface ScribeErrorEvent {
  type: 'error';
  code: string;
  message: string;
}

export type ScribeEvent = ScribePartialEvent | ScribeCommittedEvent | ScribeErrorEvent;

export interface ScribeCallbacks {
  onPartial?: (event: ScribePartialEvent) => void;
  onCommitted?: (event: ScribeCommittedEvent) => void;
  onError?: (event: ScribeErrorEvent) => void;
  onClose?: () => void;
  onSessionStarted?: () => void;
  onTokenRefreshNeeded?: () => Promise<TranscriptionTokenView | null>;
}

const DEFAULT_CONFIG: Required<ScribeConfig> = {
  modelId: 'scribe_v2_realtime',
  languageCode: 'pt',
  commitStrategy: 'vad',
  includeTimestamps: true,
  audioFormat: 'pcm_16000',
};

const TOKEN_REFRESH_BUFFER_MS = 60_000;

function buildScribeUrl(token: string, config: Required<ScribeConfig>): string {
  const params = new URLSearchParams({
    token,
    model_id: config.modelId,
    language_code: config.languageCode,
    commit_strategy: config.commitStrategy,
    include_timestamps: String(config.includeTimestamps),
    audio_format: config.audioFormat,
  });

  return `wss://api.elevenlabs.io/v1/speech-to-text/realtime?${params.toString()}`;
}

interface ScribeMessage {
  message_type?: string;
  type?: string;
  text?: string;
  speaker?: string;
  start_time?: number;
  end_time?: number;
  confidence?: number;
  code?: string;
  message?: string;
  error_type?: string;
}

export class ElevenLabsScribe {
  private socket: WebSocket | null = null;
  private callbacks: ScribeCallbacks = {};
  private resolvedConfig: Required<ScribeConfig>;
  private refreshTimer: ReturnType<typeof setTimeout> | null = null;
  private closed = false;
  private expiresAt: string | null = null;

  constructor(config?: ScribeConfig) {
    this.resolvedConfig = { ...DEFAULT_CONFIG, ...config };
  }

  connect(tokenView: TranscriptionTokenView): void {
    this.closed = false;
    this.expiresAt = tokenView.expires_at;

    const url = buildScribeUrl(tokenView.token, this.resolvedConfig);
    this.socket = new WebSocket(url);

    this.socket.onopen = () => {
      this.scheduleTokenRefresh();
    };

    this.socket.onmessage = (event) => {
      this.handleMessage(event.data);
    };

    this.socket.onerror = () => {
      this.callbacks.onError?.({
        type: 'error',
        code: 'websocket_error',
        message: 'Erro na conexao com o servico de transcricao.',
      });
    };

    this.socket.onclose = () => {
      if (!this.closed) {
        this.callbacks.onClose?.();
      }
    };
  }

  onPartial(cb: ScribeCallbacks['onPartial']): void {
    this.callbacks.onPartial = cb;
  }

  onCommitted(cb: ScribeCallbacks['onCommitted']): void {
    this.callbacks.onCommitted = cb;
  }

  onError(cb: ScribeCallbacks['onError']): void {
    this.callbacks.onError = cb;
  }

  onClose(cb: ScribeCallbacks['onClose']): void {
    this.callbacks.onClose = cb;
  }

  onSessionStarted(cb: ScribeCallbacks['onSessionStarted']): void {
    this.callbacks.onSessionStarted = cb;
  }

  setTokenRefreshCallback(cb: ScribeCallbacks['onTokenRefreshNeeded']): void {
    this.callbacks.onTokenRefreshNeeded = cb;
  }

  sendAudio(base64Chunk: string): void {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      return;
    }

    const payload = JSON.stringify({
      message_type: 'input_audio_chunk',
      audio_base_64: base64Chunk,
      sample_rate: 16000,
    });

    this.socket.send(payload);
  }

  close(): void {
    this.closed = true;
    this.clearRefreshTimer();

    if (this.socket) {
      this.socket.onclose = null;
      this.socket.onerror = null;
      this.socket.onmessage = null;

      if (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING) {
        this.socket.close();
      }

      this.socket = null;
    }
  }

  isConnected(): boolean {
    return this.socket !== null && this.socket.readyState === WebSocket.OPEN;
  }

  private handleMessage(raw: string | unknown): void {
    if (typeof raw !== 'string') {
      return;
    }

    let parsed: ScribeMessage;
    try {
      parsed = JSON.parse(raw) as ScribeMessage;
    } catch {
      return;
    }

    const messageType = parsed.message_type ?? parsed.type;

    if (messageType === 'session_started') {
      this.callbacks.onSessionStarted?.();
      return;
    }

    if (messageType === 'partial_transcript') {
      this.callbacks.onPartial?.({
        type: 'partial_transcript',
        text: parsed.text ?? '',
      });
      return;
    }

    if (messageType === 'committed_transcript' || messageType === 'committed_transcript_with_timestamps') {
      this.callbacks.onCommitted?.({
        type: 'committed_transcript',
        text: parsed.text ?? '',
        speaker: parsed.speaker ?? 'unknown',
        start_time: parsed.start_time ?? null,
        end_time: parsed.end_time ?? null,
        confidence: parsed.confidence ?? null,
      });
      return;
    }

    if (parsed.error_type || messageType === 'error') {
      this.callbacks.onError?.({
        type: 'error',
        code: parsed.error_type ?? parsed.code ?? 'unknown_error',
        message: parsed.message ?? 'Erro desconhecido do servico de transcricao.',
      });
    }
  }

  private scheduleTokenRefresh(): void {
    this.clearRefreshTimer();

    if (!this.expiresAt || !this.callbacks.onTokenRefreshNeeded) {
      return;
    }

    const expiresAtMs = Date.parse(this.expiresAt);
    if (Number.isNaN(expiresAtMs)) {
      return;
    }

    const refreshAtMs = expiresAtMs - TOKEN_REFRESH_BUFFER_MS;
    const delayMs = refreshAtMs - Date.now();

    if (delayMs <= 0) {
      void this.performTokenRefresh();
      return;
    }

    this.refreshTimer = setTimeout(() => {
      void this.performTokenRefresh();
    }, delayMs);
  }

  private async performTokenRefresh(): Promise<void> {
    if (this.closed || !this.callbacks.onTokenRefreshNeeded) {
      return;
    }

    try {
      const newTokenView = await this.callbacks.onTokenRefreshNeeded();
      if (!newTokenView || this.closed) {
        return;
      }

      const oldSocket = this.socket;

      this.expiresAt = newTokenView.expires_at;
      const url = buildScribeUrl(newTokenView.token, this.resolvedConfig);
      const newSocket = new WebSocket(url);

      newSocket.onopen = () => {
        this.socket = newSocket;

        this.socket.onmessage = (event) => {
          this.handleMessage(event.data);
        };

        this.socket.onerror = () => {
          this.callbacks.onError?.({
            type: 'error',
            code: 'websocket_error',
            message: 'Erro na conexao com o servico de transcricao.',
          });
        };

        this.socket.onclose = () => {
          if (!this.closed) {
            this.callbacks.onClose?.();
          }
        };

        if (oldSocket) {
          oldSocket.onclose = null;
          oldSocket.onerror = null;
          oldSocket.onmessage = null;
          if (oldSocket.readyState === WebSocket.OPEN || oldSocket.readyState === WebSocket.CONNECTING) {
            oldSocket.close();
          }
        }

        this.scheduleTokenRefresh();
      };

      newSocket.onerror = () => {
        this.callbacks.onError?.({
          type: 'error',
          code: 'token_refresh_failed',
          message: 'Falha ao reconectar transcricao.',
        });
      };
    } catch {
      this.callbacks.onError?.({
        type: 'error',
        code: 'token_refresh_failed',
        message: 'Falha ao renovar token de transcricao.',
      });
    }
  }

  private clearRefreshTimer(): void {
    if (this.refreshTimer !== null) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = null;
    }
  }
}
