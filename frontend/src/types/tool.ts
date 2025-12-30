/**
 * Tool call status
 */
export type ToolCallStatus = 'pending' | 'success' | 'error'

/**
 * Tool call DTO from API
 */
export interface ToolCallDto {
  id: number
  tool_call_id: string
  tool_name: string
  input: Record<string, unknown>
  output?: string | null
  error?: string | null
  status: ToolCallStatus
  started_at: string
  completed_at?: string | null
}

/**
 * Tool call domain model
 */
export interface ToolCall {
  id: number
  toolCallId: string
  toolName: string
  input: Record<string, unknown>
  output?: string
  error?: string
  status: ToolCallStatus
  startedAt: Date
  completedAt?: Date
}

/**
 * Streaming tool call (used during SSE streaming)
 */
export interface StreamingToolCall {
  toolCallId: string
  toolName: string
  input: Record<string, unknown>
  output?: string
  error?: string
  status: ToolCallStatus
}

/**
 * Helper function to convert ToolCallDto to ToolCall
 */
export function toToolCall(dto: ToolCallDto): ToolCall {
  return {
    id: dto.id,
    toolCallId: dto.tool_call_id,
    toolName: dto.tool_name,
    input: dto.input,
    output: dto.output ?? undefined,
    error: dto.error ?? undefined,
    status: dto.status,
    startedAt: new Date(dto.started_at),
    completedAt: dto.completed_at ? new Date(dto.completed_at) : undefined,
  }
}

/**
 * Type guard to check if a tool call is a persisted ToolCall (has numeric id)
 *
 * Use this to safely access properties specific to persisted tool calls:
 * ```typescript
 * if (isPersistedToolCall(tc)) {
 *   console.log(tc.id)        // number - safe to access
 *   console.log(tc.startedAt) // Date - safe to access
 * }
 * ```
 */
export function isPersistedToolCall(tc: ToolCall | StreamingToolCall): tc is ToolCall {
  return 'id' in tc && typeof (tc as ToolCall).id === 'number'
}

/**
 * Type guard to check if a tool call is a streaming tool call
 */
export function isStreamingToolCall(tc: ToolCall | StreamingToolCall): tc is StreamingToolCall {
  return !isPersistedToolCall(tc)
}

/**
 * Get a unique key for any tool call type (for React list rendering)
 *
 * Usage:
 * ```typescript
 * {toolCalls.map(tc => (
 *   <ToolCallItem key={getToolCallKey(tc)} toolCall={tc} />
 * ))}
 * ```
 */
export function getToolCallKey(tc: ToolCall | StreamingToolCall): string | number {
  return isPersistedToolCall(tc) ? tc.id : tc.toolCallId
}
