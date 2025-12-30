/**
 * Typed error classes for the application
 */

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

  constructor(message: string, options?: { uuid?: string; userMessagePersisted?: boolean }) {
    super(message)
    this.name = 'ConversationError'
    this.uuid = options?.uuid
    this.userMessagePersisted = options?.userMessagePersisted ?? false

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
  context?: { uuid?: string; userMessagePersisted?: boolean }
): ConversationError {
  return new ConversationError(err.message, context)
}
