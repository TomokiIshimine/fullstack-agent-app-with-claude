import { useCallback, useRef, useState } from 'react'
import type { StreamingToolCall } from '@/types/tool'

/**
 * Hook for managing streaming tool call state
 *
 * Provides unified state management for tool calls during SSE streaming.
 * Used by both useChat and useNewConversation hooks.
 *
 * @example
 * const { streamingToolCalls, addToolCall, completeToolCall, resetToolCalls } = useStreamingToolCalls()
 *
 * // When tool call starts
 * addToolCall('tool-123', 'calculator', { a: 1, b: 2 })
 *
 * // When tool call completes
 * completeToolCall('tool-123', '3')  // success
 * completeToolCall('tool-123', undefined, 'Division by zero')  // error
 *
 * // Reset all tool calls
 * resetToolCalls()
 */
export function useStreamingToolCalls() {
  const [streamingToolCalls, setStreamingToolCalls] = useState<StreamingToolCall[]>([])
  const toolCallsRef = useRef<StreamingToolCall[]>([])

  /**
   * Add a new tool call with pending status
   * Note: Updates ref synchronously to avoid timing issues when SSE events
   * arrive in rapid succession (e.g., tool_call_* and message_end in same chunk)
   */
  const addToolCall = useCallback(
    (toolCallId: string, toolName: string, input: Record<string, unknown>) => {
      const newToolCall: StreamingToolCall = {
        toolCallId,
        toolName,
        input,
        status: 'pending',
      }
      setStreamingToolCalls(prev => {
        const updated = [...prev, newToolCall]
        toolCallsRef.current = updated
        return updated
      })
    },
    []
  )

  /**
   * Complete a tool call with output or error
   * Note: Updates ref synchronously to avoid timing issues when SSE events
   * arrive in rapid succession (e.g., tool_call_* and message_end in same chunk)
   */
  const completeToolCall = useCallback((toolCallId: string, output?: string, error?: string) => {
    setStreamingToolCalls(prev => {
      const updated = prev.map(tc =>
        tc.toolCallId === toolCallId
          ? { ...tc, output, error, status: error ? 'error' : 'success' }
          : tc
      )
      toolCallsRef.current = updated as StreamingToolCall[]
      return updated as StreamingToolCall[]
    })
  }, [])

  /**
   * Reset all tool calls
   * Note: Updates ref synchronously to ensure getToolCalls() returns empty array immediately
   */
  const resetToolCalls = useCallback(() => {
    toolCallsRef.current = []
    setStreamingToolCalls([])
  }, [])

  /**
   * Get current tool calls (avoids stale closure in async callbacks)
   */
  const getToolCalls = useCallback(() => toolCallsRef.current, [])

  return {
    streamingToolCalls,
    addToolCall,
    completeToolCall,
    resetToolCalls,
    getToolCalls,
  }
}
