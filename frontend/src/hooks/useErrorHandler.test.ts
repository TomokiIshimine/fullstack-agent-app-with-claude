import { describe, it, expect, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useErrorHandler, getErrorMessage } from './useErrorHandler'
import { ApiError } from '@/lib/api/client'

// Mock logger to avoid console output in tests
vi.mock('@/lib/logger', () => ({
  logger: {
    error: vi.fn(),
  },
}))

describe('getErrorMessage', () => {
  it('should return ApiError message for ApiError', () => {
    const apiError = new ApiError(400, 'Bad request message')
    expect(getErrorMessage(apiError)).toBe('Bad request message')
  })

  it('should return network error message for fetch TypeError', () => {
    const fetchError = new TypeError('Failed to fetch')
    expect(getErrorMessage(fetchError)).toBe(
      'ネットワーク接続に問題があります。インターネット接続を確認してください。'
    )
  })

  it('should return network error message for fetch TypeError (lowercase)', () => {
    const fetchError = new TypeError('fetch failed')
    expect(getErrorMessage(fetchError)).toBe(
      'ネットワーク接続に問題があります。インターネット接続を確認してください。'
    )
  })

  it('should return timeout message for AbortError', () => {
    const abortError = new DOMException('The operation was aborted', 'AbortError')
    expect(getErrorMessage(abortError)).toBe(
      'リクエストがタイムアウトしました。しばらく経ってから再試行してください。'
    )
  })

  it('should return error message for generic Error', () => {
    const genericError = new Error('Something went wrong')
    expect(getErrorMessage(genericError)).toBe('Something went wrong')
  })

  it('should return default message for non-Error objects', () => {
    expect(getErrorMessage('string error')).toBe('エラーが発生しました')
    expect(getErrorMessage(null)).toBe('エラーが発生しました')
    expect(getErrorMessage(undefined)).toBe('エラーが発生しました')
    expect(getErrorMessage({ error: 'object' })).toBe('エラーが発生しました')
  })

  it('should not treat non-fetch TypeError as network error', () => {
    const typeError = new TypeError('Cannot read property of undefined')
    expect(getErrorMessage(typeError)).toBe('Cannot read property of undefined')
  })

  it('should not treat non-AbortError DOMException as timeout', () => {
    const domException = new DOMException('Invalid state', 'InvalidStateError')
    expect(getErrorMessage(domException)).toBe('Invalid state')
  })
})

describe('useErrorHandler', () => {
  it('should initialize with null error', () => {
    const { result } = renderHook(() => useErrorHandler())
    expect(result.current.error).toBeNull()
  })

  it('should set error message when handleError is called with ApiError', () => {
    const { result } = renderHook(() => useErrorHandler())

    act(() => {
      result.current.handleError(new ApiError(400, 'API error message'))
    })

    expect(result.current.error).toBe('API error message')
  })

  it('should set network error message for fetch errors', () => {
    const { result } = renderHook(() => useErrorHandler())

    act(() => {
      result.current.handleError(new TypeError('Failed to fetch'))
    })

    expect(result.current.error).toBe(
      'ネットワーク接続に問題があります。インターネット接続を確認してください。'
    )
  })

  it('should set timeout message for AbortError', () => {
    const { result } = renderHook(() => useErrorHandler())

    act(() => {
      result.current.handleError(new DOMException('Aborted', 'AbortError'))
    })

    expect(result.current.error).toBe(
      'リクエストがタイムアウトしました。しばらく経ってから再試行してください。'
    )
  })

  it('should clear error when clearError is called', () => {
    const { result } = renderHook(() => useErrorHandler())

    act(() => {
      result.current.handleError(new Error('Some error'))
    })

    expect(result.current.error).toBe('Some error')

    act(() => {
      result.current.clearError()
    })

    expect(result.current.error).toBeNull()
  })

  it('should use default message for unknown error types', () => {
    const { result } = renderHook(() => useErrorHandler())

    act(() => {
      result.current.handleError('just a string')
    })

    expect(result.current.error).toBe('エラーが発生しました')
  })
})
