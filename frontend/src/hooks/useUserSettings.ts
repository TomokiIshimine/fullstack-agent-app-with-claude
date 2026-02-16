import { useState, useEffect, useCallback } from 'react'
import { getUserSettings, updateUserSettings } from '@/lib/api/userSettings'
import { logger } from '@/lib/logger'
import type { SendShortcut } from '@/types/userSettings'

interface UseUserSettingsReturn {
  /** Current send shortcut setting */
  sendShortcut: SendShortcut
  /** Whether settings are being loaded */
  isLoading: boolean
  /** Update send shortcut setting */
  updateSendShortcut: (value: SendShortcut) => Promise<void>
  /** Error message (null if no error) */
  error: string | null
  /** Success message (null if no success) */
  successMessage: string | null
  /** Clear error state */
  clearError: () => void
  /** Clear success message */
  clearSuccessMessage: () => void
}

const DEFAULT_SEND_SHORTCUT: SendShortcut = 'enter'

export function useUserSettings(): UseUserSettingsReturn {
  const [sendShortcut, setSendShortcut] = useState<SendShortcut>(DEFAULT_SEND_SHORTCUT)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  // Fetch settings on mount
  useEffect(() => {
    let cancelled = false

    const fetchSettings = async () => {
      try {
        const settings = await getUserSettings()
        if (!cancelled) {
          setSendShortcut(settings.send_shortcut)
        }
      } catch (err) {
        // Fetch failure: use default silently (per requirement)
        logger.warn('Failed to fetch user settings, using defaults', {
          error: err instanceof Error ? err.message : 'Unknown error',
        })
        if (!cancelled) {
          setSendShortcut(DEFAULT_SEND_SHORTCUT)
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    void fetchSettings()

    return () => {
      cancelled = true
    }
  }, [])

  const updateSendShortcut = useCallback(
    async (value: SendShortcut) => {
      const previousValue = sendShortcut
      // Optimistic update
      setSendShortcut(value)
      setError(null)
      setSuccessMessage(null)

      try {
        await updateUserSettings({ send_shortcut: value })
        setSuccessMessage('チャット設定を更新しました')
        logger.info('User settings updated', { send_shortcut: value })
      } catch (err) {
        // Rollback on failure
        setSendShortcut(previousValue)
        setError('設定の更新に失敗しました')
        logger.error('Failed to update user settings', err as Error)
      }
    },
    [sendShortcut]
  )

  const clearError = useCallback(() => setError(null), [])
  const clearSuccessMessage = useCallback(() => setSuccessMessage(null), [])

  return {
    sendShortcut,
    isLoading,
    updateSendShortcut,
    error,
    successMessage,
    clearError,
    clearSuccessMessage,
  }
}
