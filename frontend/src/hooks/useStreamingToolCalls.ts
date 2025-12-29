import { useCallback, useEffect, useRef, useState } from 'react'
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

  // Keep ref in sync with state to avoid stale closure issues
  useEffect(() => {
    toolCallsRef.current = streamingToolCalls
  }, [streamingToolCalls])

  /**
   * Add a new tool call with pending status
   */
  const addToolCall = useCallback(
    (toolCallId: string, toolName: string, input: Record<string, unknown>) => {
      const newToolCall: StreamingToolCall = {
        toolCallId,
        toolName,
        input,
        status: 'pending',
      }
      setStreamingToolCalls(prev => [...prev, newToolCall])
    },
    []
  )

  /**
   * Complete a tool call with output or error
   */
  const completeToolCall = useCallback((toolCallId: string, output?: string, error?: string) => {
    setStreamingToolCalls(prev =>
      prev.map(tc =>
        tc.toolCallId === toolCallId
          ? { ...tc, output, error, status: error ? 'error' : 'success' }
          : tc
      )
    )
  }, [])

  /**
   * Reset all tool calls
   */
  const resetToolCalls = useCallback(() => {
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
