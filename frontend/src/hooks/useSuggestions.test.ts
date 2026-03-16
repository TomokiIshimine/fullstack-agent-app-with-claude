import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useSuggestions } from './useSuggestions'

// Mock the API module
vi.mock('@/lib/api/suggestions', () => ({
  fetchSuggestions: vi.fn(),
}))

// Mock logger
vi.mock('@/lib/logger', () => ({
  logger: {
    debug: vi.fn(),
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
  },
}))

import { fetchSuggestions } from '@/lib/api/suggestions'

describe('useSuggestions', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    vi.mocked(fetchSuggestions).mockResolvedValue({
      suggestions: ['選択肢1', '選択肢2', '選択肢3'],
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Initial state', () => {
    it('should have correct initial state', () => {
      const { result } = renderHook(() => useSuggestions({ conversationUuid: 'test-uuid' }))

      expect(result.current.suggestions).toEqual([])
      expect(result.current.isLoading).toBe(false)
    })
  })

  describe('fetchSuggestions', () => {
    it('should fetch suggestions and update state', async () => {
      const { result } = renderHook(() => useSuggestions({ conversationUuid: 'test-uuid' }))

      act(() => {
        result.current.fetchSuggestions()
      })

      expect(result.current.isLoading).toBe(true)

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.suggestions).toEqual(['選択肢1', '選択肢2', '選択肢3'])
      expect(fetchSuggestions).toHaveBeenCalledWith('test-uuid', expect.any(AbortSignal))
    })

    it('should not fetch when conversationUuid is undefined', () => {
      const { result } = renderHook(() => useSuggestions({ conversationUuid: undefined }))

      act(() => {
        result.current.fetchSuggestions()
      })

      expect(fetchSuggestions).not.toHaveBeenCalled()
      expect(result.current.isLoading).toBe(false)
    })

    it('should handle API errors silently', async () => {
      vi.mocked(fetchSuggestions).mockRejectedValue(new Error('Network error'))

      const { result } = renderHook(() => useSuggestions({ conversationUuid: 'test-uuid' }))

      act(() => {
        result.current.fetchSuggestions()
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.suggestions).toEqual([])
    })
  })

  describe('clearSuggestions', () => {
    it('should clear suggestions and loading state', async () => {
      const { result } = renderHook(() => useSuggestions({ conversationUuid: 'test-uuid' }))

      act(() => {
        result.current.fetchSuggestions()
      })

      await waitFor(() => {
        expect(result.current.suggestions).toEqual(['選択肢1', '選択肢2', '選択肢3'])
      })

      act(() => {
        result.current.clearSuggestions()
      })

      expect(result.current.suggestions).toEqual([])
      expect(result.current.isLoading).toBe(false)
    })
  })

  describe('conversationUuid change', () => {
    it('should clear suggestions when conversationUuid changes', async () => {
      const { result, rerender } = renderHook(
        ({ uuid }: { uuid: string | undefined }) => useSuggestions({ conversationUuid: uuid }),
        { initialProps: { uuid: 'uuid-1' } }
      )

      act(() => {
        result.current.fetchSuggestions()
      })

      await waitFor(() => {
        expect(result.current.suggestions).toEqual(['選択肢1', '選択肢2', '選択肢3'])
      })

      rerender({ uuid: 'uuid-2' })

      expect(result.current.suggestions).toEqual([])
      expect(result.current.isLoading).toBe(false)
    })
  })

  describe('AbortController management', () => {
    it('should abort previous request when fetchSuggestions is called again', async () => {
      let resolveSecond: (value: { suggestions: string[] }) => void

      vi.mocked(fetchSuggestions)
        .mockImplementationOnce(
          (_uuid, signal) =>
            new Promise((_resolve, reject) => {
              signal?.addEventListener('abort', () =>
                reject(new DOMException('Aborted', 'AbortError'))
              )
            })
        )
        .mockImplementationOnce(
          (_uuid, signal) =>
            new Promise((resolve, reject) => {
              resolveSecond = resolve
              signal?.addEventListener('abort', () =>
                reject(new DOMException('Aborted', 'AbortError'))
              )
            })
        )

      const { result } = renderHook(() => useSuggestions({ conversationUuid: 'test-uuid' }))

      // First call
      act(() => {
        result.current.fetchSuggestions()
      })

      // Second call should abort first
      act(() => {
        result.current.fetchSuggestions()
      })

      // Resolve second request
      await act(async () => {
        resolveSecond!({ suggestions: ['新しい選択肢'] })
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.suggestions).toEqual(['新しい選択肢'])
    })

    it('should abort pending request on clearSuggestions', async () => {
      let fetchResolve: (value: { suggestions: string[] }) => void

      vi.mocked(fetchSuggestions).mockImplementation(
        () =>
          new Promise(resolve => {
            fetchResolve = resolve
          })
      )

      const { result } = renderHook(() => useSuggestions({ conversationUuid: 'test-uuid' }))

      act(() => {
        result.current.fetchSuggestions()
      })

      expect(result.current.isLoading).toBe(true)

      act(() => {
        result.current.clearSuggestions()
      })

      expect(result.current.isLoading).toBe(false)
      expect(result.current.suggestions).toEqual([])

      // Resolve after clear - should not update state due to abort
      await act(async () => {
        fetchResolve!({ suggestions: ['遅延結果'] })
      })

      expect(result.current.suggestions).toEqual([])
    })
  })
})
