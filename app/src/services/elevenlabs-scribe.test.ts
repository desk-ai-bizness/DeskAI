import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ElevenLabsScribe } from './elevenlabs-scribe';
import type { TranscriptionTokenView } from '../types/contracts';

function createMockTokenView(overrides?: Partial<TranscriptionTokenView>): TranscriptionTokenView {
  return {
    token: 'test-token-abc',
    websocket_url: 'wss://api.elevenlabs.io/v1/speech-to-text/realtime',
    model_id: 'scribe_v2_realtime',
    language_code: 'pt',
    expires_at: new Date(Date.now() + 15 * 60_000).toISOString(),
    expires_in_seconds: 900,
    ...overrides,
  };
}

class MockWebSocket {
  static readonly CONNECTING = 0;
  static readonly OPEN = 1;
  static readonly CLOSING = 2;
  static readonly CLOSED = 3;
  static instances: MockWebSocket[] = [];

  url: string;
  readyState: number = MockWebSocket.CONNECTING;
  onopen: ((ev: Event) => void) | null = null;
  onmessage: ((ev: MessageEvent) => void) | null = null;
  onerror: ((ev: Event) => void) | null = null;
  onclose: ((ev: CloseEvent) => void) | null = null;
  sentMessages: string[] = [];

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }

  send(data: string): void {
    this.sentMessages.push(data);
  }

  close(): void {
    this.readyState = MockWebSocket.CLOSED;
  }

  simulateOpen(): void {
    this.readyState = MockWebSocket.OPEN;
    this.onopen?.(new Event('open'));
  }

  simulateMessage(data: unknown): void {
    this.onmessage?.(new MessageEvent('message', { data: JSON.stringify(data) }));
  }

  simulateError(): void {
    this.onerror?.(new Event('error'));
  }

  simulateClose(): void {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.(new CloseEvent('close'));
  }
}

describe('ElevenLabsScribe', () => {
  beforeEach(() => {
    MockWebSocket.instances = [];
    vi.stubGlobal('WebSocket', MockWebSocket);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('connects to ElevenLabs with correct query params', () => {
    const scribe = new ElevenLabsScribe();
    scribe.connect(createMockTokenView());

    expect(MockWebSocket.instances).toHaveLength(1);
    const url = MockWebSocket.instances[0].url;
    expect(url).toContain('wss://api.elevenlabs.io/v1/speech-to-text/realtime');
    expect(url).toContain('token=test-token-abc');
    expect(url).toContain('model_id=scribe_v2_realtime');
    expect(url).toContain('language_code=pt');
    expect(url).toContain('commit_strategy=vad');
    expect(url).toContain('include_timestamps=true');
    expect(url).toContain('audio_format=pcm_16000');

    scribe.close();
  });

  it('fires onSessionStarted when session_started message received', () => {
    const scribe = new ElevenLabsScribe();
    const onSessionStarted = vi.fn();
    scribe.onSessionStarted(onSessionStarted);

    scribe.connect(createMockTokenView());
    const ws = MockWebSocket.instances[0];
    ws.simulateOpen();
    ws.simulateMessage({ message_type: 'session_started' });

    expect(onSessionStarted).toHaveBeenCalledOnce();

    scribe.close();
  });

  it('fires onPartial for partial_transcript events', () => {
    const scribe = new ElevenLabsScribe();
    const onPartial = vi.fn();
    scribe.onPartial(onPartial);

    scribe.connect(createMockTokenView());
    const ws = MockWebSocket.instances[0];
    ws.simulateOpen();
    ws.simulateMessage({ message_type: 'partial_transcript', text: 'Olá doutor' });

    expect(onPartial).toHaveBeenCalledWith({
      type: 'partial_transcript',
      text: 'Olá doutor',
    });

    scribe.close();
  });

  it('fires onCommitted for committed_transcript events', () => {
    const scribe = new ElevenLabsScribe();
    const onCommitted = vi.fn();
    scribe.onCommitted(onCommitted);

    scribe.connect(createMockTokenView());
    const ws = MockWebSocket.instances[0];
    ws.simulateOpen();
    ws.simulateMessage({
      message_type: 'committed_transcript',
      text: 'Sinto dor de cabeça',
      speaker: 'patient',
      start_time: 1.0,
      end_time: 3.5,
      confidence: 0.95,
    });

    expect(onCommitted).toHaveBeenCalledWith({
      type: 'committed_transcript',
      text: 'Sinto dor de cabeça',
      speaker: 'patient',
      start_time: 1.0,
      end_time: 3.5,
      confidence: 0.95,
    });

    scribe.close();
  });

  it('fires onCommitted for committed_transcript_with_timestamps events', () => {
    const scribe = new ElevenLabsScribe();
    const onCommitted = vi.fn();
    scribe.onCommitted(onCommitted);

    scribe.connect(createMockTokenView());
    const ws = MockWebSocket.instances[0];
    ws.simulateOpen();
    ws.simulateMessage({
      message_type: 'committed_transcript_with_timestamps',
      text: 'Desde ontem',
      speaker: 'patient',
      start_time: 4.0,
      end_time: 5.2,
    });

    expect(onCommitted).toHaveBeenCalledWith(expect.objectContaining({
      type: 'committed_transcript',
      text: 'Desde ontem',
    }));

    scribe.close();
  });

  it('fires onError for ElevenLabs error events', () => {
    const scribe = new ElevenLabsScribe();
    const onError = vi.fn();
    scribe.onError(onError);

    scribe.connect(createMockTokenView());
    const ws = MockWebSocket.instances[0];
    ws.simulateOpen();
    ws.simulateMessage({
      error_type: 'auth_error',
      message: 'Invalid token',
    });

    expect(onError).toHaveBeenCalledWith({
      type: 'error',
      code: 'auth_error',
      message: 'Invalid token',
    });

    scribe.close();
  });

  it('fires onClose when WebSocket closes unexpectedly', () => {
    const scribe = new ElevenLabsScribe();
    const onClose = vi.fn();
    scribe.onClose(onClose);

    scribe.connect(createMockTokenView());
    const ws = MockWebSocket.instances[0];
    ws.simulateOpen();
    ws.simulateClose();

    expect(onClose).toHaveBeenCalledOnce();
  });

  it('does not fire onClose after explicit close()', () => {
    const scribe = new ElevenLabsScribe();
    const onClose = vi.fn();
    scribe.onClose(onClose);

    scribe.connect(createMockTokenView());
    const ws = MockWebSocket.instances[0];
    ws.simulateOpen();

    scribe.close();

    expect(onClose).not.toHaveBeenCalled();
  });

  it('sends audio chunk in correct format', () => {
    const scribe = new ElevenLabsScribe();
    scribe.connect(createMockTokenView());
    const ws = MockWebSocket.instances[0];
    ws.simulateOpen();

    scribe.sendAudio('AAAA');

    expect(ws.sentMessages).toHaveLength(1);
    const parsed = JSON.parse(ws.sentMessages[0]);
    expect(parsed.message_type).toBe('input_audio_chunk');
    expect(parsed.audio_base_64).toBe('AAAA');
    expect(parsed.sample_rate).toBe(16000);

    scribe.close();
  });

  it('does not send audio when socket is not open', () => {
    const scribe = new ElevenLabsScribe();

    // sendAudio without connect should be a no-op
    scribe.sendAudio('AAAA');

    scribe.connect(createMockTokenView());
    // WebSocket is still CONNECTING (not yet open), so send should not go through
    const ws = MockWebSocket.instances[0];
    expect(ws.readyState).toBe(MockWebSocket.CONNECTING);

    scribe.sendAudio('BBBB');
    expect(ws.sentMessages).toHaveLength(0);

    scribe.close();
  });

  it('reports isConnected correctly', () => {
    const scribe = new ElevenLabsScribe();
    expect(scribe.isConnected()).toBe(false);

    scribe.connect(createMockTokenView());
    // Still CONNECTING, not yet OPEN
    expect(scribe.isConnected()).toBe(false);

    MockWebSocket.instances[0].simulateOpen();
    expect(scribe.isConnected()).toBe(true);

    scribe.close();
    expect(scribe.isConnected()).toBe(false);
  });

  it('handles non-JSON messages gracefully', () => {
    const scribe = new ElevenLabsScribe();
    const onError = vi.fn();
    scribe.onError(onError);

    scribe.connect(createMockTokenView());
    const ws = MockWebSocket.instances[0];
    ws.simulateOpen();

    ws.onmessage?.(new MessageEvent('message', { data: 'not json' }));

    expect(onError).not.toHaveBeenCalled();

    scribe.close();
  });

  describe('token auto-refresh', () => {
    it('schedules refresh before expiry and opens new connection', async () => {
      vi.useFakeTimers();

      const scribe = new ElevenLabsScribe();
      const newToken = createMockTokenView({
        token: 'new-token',
        expires_at: new Date(Date.now() + 30 * 60_000).toISOString(),
      });

      const refreshCallback = vi.fn().mockResolvedValue(newToken);
      scribe.setTokenRefreshCallback(refreshCallback);

      const tokenView = createMockTokenView({
        expires_at: new Date(Date.now() + 2 * 60_000).toISOString(),
      });

      scribe.connect(tokenView);
      MockWebSocket.instances[0].simulateOpen();

      await vi.advanceTimersByTimeAsync(1 * 60_000 + 1);

      expect(refreshCallback).toHaveBeenCalledOnce();

      expect(MockWebSocket.instances).toHaveLength(2);
      const newWs = MockWebSocket.instances[1];
      expect(newWs.url).toContain('token=new-token');

      scribe.close();
      vi.useRealTimers();
    });

    it('fires onError when refresh callback fails', async () => {
      vi.useFakeTimers();

      const scribe = new ElevenLabsScribe();
      const onError = vi.fn();
      scribe.onError(onError);

      const refreshCallback = vi.fn().mockRejectedValue(new Error('network'));
      scribe.setTokenRefreshCallback(refreshCallback);

      const tokenView = createMockTokenView({
        expires_at: new Date(Date.now() + 2 * 60_000).toISOString(),
      });

      scribe.connect(tokenView);
      MockWebSocket.instances[0].simulateOpen();

      await vi.advanceTimersByTimeAsync(1 * 60_000 + 1);

      expect(onError).toHaveBeenCalledWith(
        expect.objectContaining({ code: 'token_refresh_failed' }),
      );

      scribe.close();
      vi.useRealTimers();
    });
  });
});
