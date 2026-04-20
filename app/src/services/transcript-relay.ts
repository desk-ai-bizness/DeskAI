import type { CommittedSegment, SessionClientMessage } from '../types/contracts';
import { CURRENT_EVENT_VERSION } from '../types/contracts';
import type { ScribeCommittedEvent } from './elevenlabs-scribe';

export function buildTranscriptCommitMessage(
  consultationId: string,
  segments: CommittedSegment[],
): SessionClientMessage {
  return {
    action: 'transcript.commit',
    data: {
      consultation_id: consultationId,
      segments,
      timestamp: new Date().toISOString(),
      event_version: CURRENT_EVENT_VERSION,
    },
  };
}

export function scribeEventToSegment(event: ScribeCommittedEvent): CommittedSegment {
  return {
    speaker: event.speaker,
    text: event.text,
    start_time: event.start_time,
    end_time: event.end_time,
    confidence: event.confidence,
    is_final: true,
  };
}

export function relayCommittedSegment(
  socket: WebSocket | null,
  consultationId: string,
  event: ScribeCommittedEvent,
): boolean {
  if (!socket || socket.readyState !== WebSocket.OPEN) {
    return false;
  }

  const segment = scribeEventToSegment(event);
  const message = buildTranscriptCommitMessage(consultationId, [segment]);

  try {
    socket.send(JSON.stringify(message));
    return true;
  } catch {
    return false;
  }
}
