import { useState, useCallback } from 'react'
import { ApiError } from '@/lib/api/client'
import { logger } from '@/lib/logger'

/**
 * Check if error is a network connection error (fetch failed)
 */
function isNetworkError(err: unknown): boolean {
  return err instanceof TypeError && err.message.toLowerCase().includes('fetch')
}

/**
 * Check if error is a request timeout/abort error
 */
function isAbortError(err: unknown): boolean {
  return err instanceof DOMException && err.name === 'AbortError'
}

/**
 * Get user-friendly error message based on error type
 */
export function getErrorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    return err.message
  }

  if (isNetworkError(err)) {
    return 'ネットワーク接続に問題があります。インターネット接続を確認してください。'
  }

  if (isAbortError(err)) {
    return 'リクエストがタイムアウトしました。しばらく経ってから再試行してください。'
  }

  if (err instanceof Error) {
    return err.message
  }

  return 'エラーが発生しました'
}

export function useErrorHandler() {
  const [error, setError] = useState<string | null>(null)

  const handleError = useCallback((err: unknown, context?: string) => {
    const message = getErrorMessage(err)
    setError(message)
    logger.error(context || 'Error occurred', err as Error)
  }, [])

  const clearError = useCallback(() => {
    setError(null)
  }, [])

  return { error, handleError, clearError }
}
