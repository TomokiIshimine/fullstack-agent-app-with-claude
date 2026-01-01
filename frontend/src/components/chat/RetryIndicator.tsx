import { getBriefErrorMessage } from '@/lib/constants/errorMessages'
import type { RetryStatus } from '@/types/errors'

interface RetryIndicatorProps {
  status: RetryStatus
}

/**
 * Displays retry status with spinner and progress count.
 *
 * Shows a spinner animation with the current retry attempt count
 * and a Japanese message describing the error type.
 *
 * @example
 * ```tsx
 * {retryStatus && <RetryIndicator status={retryStatus} />}
 * ```
 */
export function RetryIndicator({ status }: RetryIndicatorProps) {
  const errorMessage = getBriefErrorMessage(status.errorType)

  return (
    <div className="flex items-center gap-2 px-4 py-2 bg-warning-50 border border-warning-100 rounded-lg text-warning-600">
      {/* Spinner */}
      <svg
        className="animate-spin h-4 w-4 text-warning-600"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
      {/* Message */}
      <span className="text-sm">
        {errorMessage}。再試行中... ({status.attempt}/{status.maxAttempts})
      </span>
    </div>
  )
}

export default RetryIndicator
