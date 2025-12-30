import type { Dispatch, SetStateAction } from 'react'
import type { RetryEvent, RetryStatus } from '@/types/errors'
import { logger } from '@/lib/logger'

/**
 * Creates a standardized onRetry callback for streaming operations.
 *
 * This factory function eliminates code duplication across useChat and
 * useUnifiedChat hooks by providing a consistent retry event handler.
 *
 * @param setRetryStatus - React state setter for RetryStatus
 * @returns Callback function for handling retry events
 *
 * @example
 * ```typescript
 * const [retryStatus, setRetryStatus] = useState<RetryStatus | null>(null)
 * const onRetry = createOnRetryHandler(setRetryStatus)
 *
 * await sendMessageStreaming(uuid, request, {
 *   onRetry,
 *   // ...other callbacks
 * })
 * ```
 */
export function createOnRetryHandler(
  setRetryStatus: Dispatch<SetStateAction<RetryStatus | null>>
): (event: RetryEvent) => void {
  return (event: RetryEvent) => {
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
