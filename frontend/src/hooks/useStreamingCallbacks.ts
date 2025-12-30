import type { Dispatch, SetStateAction } from 'react'
import type { RetryEvent, RetryStatus } from '@/types/errors'
import { logger } from '@/lib/logger'

/**
 * Options for creating a retry handler
 */
export interface RetryHandlerOptions {
  /**
   * Callback to reset streaming content when a retry occurs.
   * This prevents duplicate/garbled responses by clearing partial content
   * before the next retry attempt starts fresh.
   *
   * @example
   * ```typescript
   * let finalContent = ''
   * const onRetry = createOnRetryHandler(setRetryStatus, {
   *   onReset: () => {
   *     finalContent = ''
   *     setStreamingContent('')
   *   }
   * })
   * ```
   */
  onReset?: () => void
}

/**
 * Creates a standardized onRetry callback for streaming operations.
 *
 * This factory function eliminates code duplication across useChat and
 * useUnifiedChat hooks by providing a consistent retry event handler.
 *
 * When a retry occurs after partial streaming content has been received,
 * this handler clears the streaming buffer via the optional onReset callback
 * to ensure each retry starts from a clean slate.
 *
 * @param setRetryStatus - React state setter for RetryStatus
 * @param options - Optional configuration including reset callback
 * @returns Callback function for handling retry events
 *
 * @example
 * ```typescript
 * const [retryStatus, setRetryStatus] = useState<RetryStatus | null>(null)
 * let finalContent = ''
 *
 * const onRetry = createOnRetryHandler(setRetryStatus, {
 *   onReset: () => {
 *     finalContent = ''
 *     setStreamingContent('')
 *   }
 * })
 *
 * await sendMessageStreaming(uuid, request, {
 *   onRetry,
 *   onDelta: delta => {
 *     finalContent += delta
 *     setStreamingContent(finalContent)
 *   },
 *   // ...other callbacks
 * })
 * ```
 */
export function createOnRetryHandler(
  setRetryStatus: Dispatch<SetStateAction<RetryStatus | null>>,
  options?: RetryHandlerOptions
): (event: RetryEvent) => void {
  return (event: RetryEvent) => {
    // Clear streaming content before retry to prevent duplicated/garbled output
    options?.onReset?.()

    setRetryStatus({
      isRetrying: true,
      attempt: event.attempt,
      maxAttempts: event.max_attempts,
      errorType: event.error_type,
    })
    logger.warn('Retry attempt', {
      attempt: event.attempt,
      maxAttempts: event.max_attempts,
      errorType: event.error_type,
    })
  }
}
