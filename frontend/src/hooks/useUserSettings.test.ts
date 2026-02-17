import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useUserSettings } from './useUserSettings'

// Mock the API module
vi.mock('@/lib/api/userSettings', () => ({
  getUserSettings: vi.fn(),
  updateUserSettings: vi.fn(),
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

import { getUserSettings, updateUserSettings } from '@/lib/api/userSettings'

describe('useUserSettings', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    vi.mocked(getUserSettings).mockResolvedValue({ send_shortcut: 'enter' })
    vi.mocked(updateUserSettings).mockResolvedValue({
      message: '設定を更新しました',
      send_shortcut: 'ctrl_enter',
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Initial state and fetch', () => {
    it('should have correct initial state', () => {
      const { result } = renderHook(() => useUserSettings())

      expect(result.current.sendShortcut).toBe('enter')
      expect(result.current.isLoading).toBe(true)
      expect(result.current.error).toBeNull()
      expect(result.current.successMessage).toBeNull()
    })

    it('should fetch settings on mount', async () => {
      vi.mocked(getUserSettings).mockResolvedValue({ send_shortcut: 'ctrl_enter' })

      const { result } = renderHook(() => useUserSettings())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(getUserSettings).toHaveBeenCalledTimes(1)
      expect(result.current.sendShortcut).toBe('ctrl_enter')
    })

    it('should use default value when fetch fails', async () => {
      vi.mocked(getUserSettings).mockRejectedValue(new Error('Network error'))

      const { result } = renderHook(() => useUserSettings())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.sendShortcut).toBe('enter')
      expect(result.current.error).toBeNull()
    })

    it('should set isLoading to false after fetch completes', async () => {
      const { result } = renderHook(() => useUserSettings())

      expect(result.current.isLoading).toBe(true)

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })
    })
  })

  describe('updateSendShortcut', () => {
    it('should update send shortcut successfully', async () => {
      const { result } = renderHook(() => useUserSettings())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      await act(async () => {
        await result.current.updateSendShortcut('ctrl_enter')
      })

      expect(updateUserSettings).toHaveBeenCalledWith({ send_shortcut: 'ctrl_enter' })
      expect(result.current.sendShortcut).toBe('ctrl_enter')
      expect(result.current.successMessage).toBe('チャット設定を更新しました')
      expect(result.current.error).toBeNull()
    })

    it('should perform optimistic update', async () => {
      let resolveUpdate: (value: { message: string; send_shortcut: 'ctrl_enter' }) => void
      vi.mocked(updateUserSettings).mockReturnValue(
        new Promise(resolve => {
          resolveUpdate = resolve
        })
      )

      const { result } = renderHook(() => useUserSettings())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Start the update but don't await it
      act(() => {
        void result.current.updateSendShortcut('ctrl_enter')
      })

      // Optimistic update should be immediate
      expect(result.current.sendShortcut).toBe('ctrl_enter')

      // Resolve the API call
      await act(async () => {
        resolveUpdate!({ message: '設定を更新しました', send_shortcut: 'ctrl_enter' })
      })
    })

    it('should rollback on update failure', async () => {
      vi.mocked(updateUserSettings).mockRejectedValue(new Error('Update failed'))

      const { result } = renderHook(() => useUserSettings())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.sendShortcut).toBe('enter')

      await act(async () => {
        await result.current.updateSendShortcut('ctrl_enter')
      })

      // Should rollback to previous value
      expect(result.current.sendShortcut).toBe('enter')
      expect(result.current.error).toBe('設定の更新に失敗しました')
    })

    it('should clear previous error on new update', async () => {
      vi.mocked(updateUserSettings)
        .mockRejectedValueOnce(new Error('First error'))
        .mockResolvedValueOnce({
          message: '設定を更新しました',
          send_shortcut: 'ctrl_enter',
        })

      const { result } = renderHook(() => useUserSettings())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // First update - fails
      await act(async () => {
        await result.current.updateSendShortcut('ctrl_enter')
      })

      expect(result.current.error).toBe('設定の更新に失敗しました')

      // Second update - succeeds
      await act(async () => {
        await result.current.updateSendShortcut('ctrl_enter')
      })

      expect(result.current.error).toBeNull()
      expect(result.current.successMessage).toBe('チャット設定を更新しました')
    })
  })

  describe('clearError', () => {
    it('should clear error state', async () => {
      vi.mocked(updateUserSettings).mockRejectedValue(new Error('Update failed'))

      const { result } = renderHook(() => useUserSettings())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      await act(async () => {
        await result.current.updateSendShortcut('ctrl_enter')
      })

      expect(result.current.error).toBe('設定の更新に失敗しました')

      act(() => {
        result.current.clearError()
      })

      expect(result.current.error).toBeNull()
    })
  })

  describe('clearSuccessMessage', () => {
    it('should clear success message', async () => {
      const { result } = renderHook(() => useUserSettings())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      await act(async () => {
        await result.current.updateSendShortcut('ctrl_enter')
      })

      expect(result.current.successMessage).toBe('チャット設定を更新しました')

      act(() => {
        result.current.clearSuccessMessage()
      })

      expect(result.current.successMessage).toBeNull()
    })
  })
})
