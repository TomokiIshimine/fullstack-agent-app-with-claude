/**
 * Typed error classes for the application
 */

/**
 * Error types from LLM provider
 */
export type LLMErrorType =
  | 'rate_limit'
  | 'connection'
  | 'server_error'
  | 'context_length'
  | 'stream_error'
  | 'provider_error'
  | 'conversation_error'
  | 'unknown'

/**
 * Structured error from SSE stream
 */
export interface StreamError {
  error: string
  error_type?: LLMErrorType
  user_message_id?: number
  retry_after?: number
  is_retryable?: boolean
}

/**
 * Retry event from SSE stream
 */
export interface RetryEvent {
  attempt: number
  max_attempts: number
  error_type: string
  delay: number
}

/**
 * Retry status for UI display
 */
export interface RetryStatus {
  isRetrying: boolean
  attempt: number
  maxAttempts: number
  errorType: string
}

/**
 * Error thrown when a conversation operation fails after partial success.
 * Contains context about whether the user message was persisted.
 *
 * @example
 * ```typescript
 * try {
 *   await createConversation(content)
 * } catch (err) {
 *   if (isConversationError(err)) {
 *     if (err.userMessagePersisted && err.uuid) {
 *       // Navigate to conversation even though there was an error
 *       navigate(`/chat/${err.uuid}`)
 *     }
 *   }
 * }
 * ```
 */
export class ConversationError extends Error {
  readonly uuid?: string
  readonly userMessagePersisted: boolean
  readonly errorType?: LLMErrorType
  readonly isRetryable?: boolean
  readonly retryAfter?: number

  constructor(
    message: string,
    options?: {
      uuid?: string
      userMessagePersisted?: boolean
      errorType?: LLMErrorType
      isRetryable?: boolean
      retryAfter?: number
    }
  ) {
    super(message)
    this.name = 'ConversationError'
    this.uuid = options?.uuid
    this.userMessagePersisted = options?.userMessagePersisted ?? false
    this.errorType = options?.errorType
    this.isRetryable = options?.isRetryable
    this.retryAfter = options?.retryAfter

    // Maintain proper stack trace for where error was thrown
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, ConversationError)
    }
  }
}

/**
 * Type guard for ConversationError
 */
export function isConversationError(err: unknown): err is ConversationError {
  return err instanceof ConversationError
}

/**
 * Error context for form submission failures
 */
export interface FormSubmissionError {
  /** Error message */
  message: string
  /** Field-level errors keyed by field name */
  fieldErrors?: Record<string, string>
  /** Whether this was an API error */
  isApiError: boolean
}

/**
 * Create a ConversationError from a generic error with context
 */
export function toConversationError(
  err: Error,
  context?: {
    uuid?: string
    userMessagePersisted?: boolean
    errorType?: LLMErrorType
    isRetryable?: boolean
    retryAfter?: number
  }
): ConversationError {
  return new ConversationError(err.message, context)
}

/**
 * Create a ConversationError from StreamError
 */
export function fromStreamError(streamError: StreamError, uuid?: string): ConversationError {
  return new ConversationError(streamError.error, {
    uuid,
    userMessagePersisted: streamError.user_message_id !== undefined,
    errorType: streamError.error_type,
    isRetryable: streamError.is_retryable,
    retryAfter: streamError.retry_after,
  })
}
