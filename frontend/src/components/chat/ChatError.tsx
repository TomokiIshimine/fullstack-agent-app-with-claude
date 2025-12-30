import { Alert } from '@/components/ui'
import { getDetailedErrorMessage } from '@/lib/constants/errorMessages'
import type { StreamError } from '@/types/errors'

interface ChatErrorProps {
  /** The stream error object containing error details */
  error: StreamError
  /** Callback to dismiss the error */
  onDismiss?: () => void
  /** Callback to retry the operation (only shown if error is retryable) */
  onRetry?: () => void
}

/**
 * Displays an error message above the chat input area.
 *
 * Wraps the Alert component with chat-specific error handling,
 * including error type mapping and retry_after countdown.
 *
 * @example
 * ```tsx
 * {streamError && (
 *   <ChatError
 *     error={streamError}
 *     onDismiss={clearStreamError}
 *     onRetry={isRetryable ? handleRetry : undefined}
 *   />
 * )}
 * ```
 */
export function ChatError({ error, onDismiss, onRetry }: ChatErrorProps) {
  const userMessage = getDetailedErrorMessage(error.error_type)

  return (
    <Alert variant="error" onDismiss={onDismiss} onRetry={error.is_retryable ? onRetry : undefined}>
      <p className="font-medium">{userMessage}</p>
      {error.retry_after && (
        <p className="text-xs mt-1 opacity-75">{error.retry_after}秒後に再試行できます。</p>
      )}
    </Alert>
  )
}

export default ChatError
