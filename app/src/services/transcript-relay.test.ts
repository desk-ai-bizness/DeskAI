import { describe, expect, it, vi } from 'vitest';
import {
  buildTranscriptCommitMessage,
  relayCommittedSegment,
  scribeEventToSegment,
} from './transcript-relay';
import type { ScribeCommittedEvent } from './elevenlabs-scribe';
import { CURRENT_EVENT_VERSION } from '../types/contracts';

function createCommittedEvent(overrides?: Partial<ScribeCommittedEvent>): ScribeCommittedEvent {
  return {
    type: 'committed_transcript',
    text: 'Sinto dor de cabeca',
    speaker: 'patient',
    start_time: 1.0,
    end_time: 3.5,
    confidence: 0.95,
    ...overrides,
  };
}

describe('transcript-relay', () => {
  describe('scribeEventToSegment', () => {
    it('converts a Scribe committed event to a CommittedSegment', () => {
      const event = createCommittedEvent();
      const segment = scribeEventToSegment(event);

      expect(segment).toEqual({
        speaker: 'patient',
        text: 'Sinto dor de cabeca',
        start_time: 1.0,
        end_time: 3.5,
        confidence: 0.95,
        is_final: true,
      });
    });

    it('handles null timestamps and confidence', () => {
      const event = createCommittedEvent({
        start_time: null,
        end_time: null,
        confidence: null,
      });
      const segment = scribeEventToSegment(event);

      expect(segment.start_time).toBeNull();
      expect(segment.end_time).toBeNull();
      expect(segment.confidence).toBeNull();
      expect(segment.is_final).toBe(true);
    });
  });

  describe('buildTranscriptCommitMessage', () => {
    it('builds a transcript.commit message with event_version', () => {
      const segments = [scribeEventToSegment(createCommittedEvent())];
      const message = buildTranscriptCommitMessage('cons-123', segments);

      expect(message.action).toBe('transcript.commit');
      expect(message.data).toEqual(expect.objectContaining({
        consultation_id: 'cons-123',
        segments: [expect.objectContaining({ speaker: 'patient', text: 'Sinto dor de cabeca' })],
        event_version: CURRENT_EVENT_VERSION,
      }));
      expect(typeof message.data.timestamp).toBe('string');
    });
  });

  describe('relayCommittedSegment', () => {
    it('sends segment to open WebSocket and returns true', () => {
      const sendMock = vi.fn();
      const mockSocket = {
        readyState: WebSocket.OPEN,
        send: sendMock,
      } as unknown as WebSocket;

      const result = relayCommittedSegment(mockSocket, 'cons-1', createCommittedEvent());

      expect(result).toBe(true);
      expect(sendMock).toHaveBeenCalledOnce();

      const sent = JSON.parse(sendMock.mock.calls[0][0]);
      expect(sent.action).toBe('transcript.commit');
      expect(sent.data.consultation_id).toBe('cons-1');
      expect(sent.data.segments).toHaveLength(1);
      expect(sent.data.event_version).toBe(CURRENT_EVENT_VERSION);
    });

    it('returns false when socket is null', () => {
      const result = relayCommittedSegment(null, 'cons-1', createCommittedEvent());
      expect(result).toBe(false);
    });

    it('returns false when socket is not open', () => {
      const mockSocket = {
        readyState: WebSocket.CLOSED,
        send: vi.fn(),
      } as unknown as WebSocket;

      const result = relayCommittedSegment(mockSocket, 'cons-1', createCommittedEvent());
      expect(result).toBe(false);
    });

    it('returns false when send throws', () => {
      const mockSocket = {
        readyState: WebSocket.OPEN,
        send: vi.fn().mockImplementation(() => { throw new Error('fail'); }),
      } as unknown as WebSocket;

      const result = relayCommittedSegment(mockSocket, 'cons-1', createCommittedEvent());
      expect(result).toBe(false);
    });
  });
});
