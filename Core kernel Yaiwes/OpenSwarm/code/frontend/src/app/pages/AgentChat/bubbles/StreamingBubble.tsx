import React, { useEffect, useRef } from 'react';
import { useStreamingMessage } from '@/shared/state/streamingSlice';
import MessageBubble from './MessageBubble';
import ToolCallBubble from '../tool-bubbles/ToolCallBubble';
import { useSmoothText } from './useSmoothText';

interface Props {
  sessionId: string;
  activeBranchId: string;
  turnLabel?: string | null;
  onStreamGrew?: () => void;
}

/** Leaf subscriber for one session's streaming entry; isolates re-renders so AgentChat doesn't churn per character. */
const StreamingBubble: React.FC<Props> = ({ sessionId, activeBranchId, turnLabel, onStreamGrew }) => {
  const streamingMessage = useStreamingMessage(sessionId);
  const rawContent = streamingMessage?.content ?? '';
  // Smooth-reveal the assistant's generated text at a steady cadence so it reads like typing instead of bursty network chunks. Provider-agnostic by design: every model (Anthropic/OpenAI/Gemini/OpenRouter/custom) funnels through this same streaming slice, so smoothing here covers all of them at once. Tool-call input is left raw (it's args, not prose). Zero added TTFT (see useSmoothText).
  const isTextRole = streamingMessage?.role !== 'tool_call';
  const { text: smoothContent, revealRef } = useSmoothText(rawContent, isTextRole);
  const typedContent = isTextRole ? smoothContent : rawContent;
  // RAF-coalesce so onStreamGrew fires once per frame regardless of token rate.
  const onGrewRef = useRef(onStreamGrew);
  onGrewRef.current = onStreamGrew;
  const rafRef = useRef<number | null>(null);
  useEffect(() => {
    if (!streamingMessage) return;
    if (rafRef.current != null) return;
    rafRef.current = requestAnimationFrame(() => {
      rafRef.current = null;
      onGrewRef.current?.();
    });
    return () => {
      if (rafRef.current != null) {
        cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      }
    };
  });
  if (!streamingMessage) return null;

  if (streamingMessage.role === 'tool_call') {
    return (
      <ToolCallBubble
        key={`streaming-${streamingMessage.id}`}
        isStreaming
        isPending
        sessionId={sessionId}
        call={{
          id: streamingMessage.id,
          role: 'tool_call',
          content: { tool: streamingMessage.tool_name || '', input: typedContent },
          timestamp: new Date().toISOString(),
          branch_id: activeBranchId,
          parent_id: null,
        }}
      />
    );
  }

  return (
    <MessageBubble
      key={`streaming-${streamingMessage.id}`}
      isStreaming
      revealRef={revealRef}
      dynamicTurnLabel={turnLabel}
      message={{
        id: streamingMessage.id,
        role: streamingMessage.role,
        content: typedContent,
        timestamp: new Date().toISOString(),
        branch_id: activeBranchId,
        parent_id: null,
      }}
    />
  );
};

export default StreamingBubble;
