import { useState, useCallback, useEffect, useRef } from 'react'
import { fetchSuggestions as fetchSuggestionsApi } from '@/lib/api/suggestions'
import { logger } from '@/lib/logger'

const RETRY_DELAY_MS = 1500
const MAX_RETRIES = 1

interface UseSuggestionsOptions {
  conversationUuid: string | undefined
}

interface UseSuggestionsReturn {
  suggestions: string[]
  isLoading: boolean
  fetchSuggestions: (overrideUuid?: string) => void
  clearSuggestions: () => void
}

export function useSuggestions({ conversationUuid }: UseSuggestionsOptions): UseSuggestionsReturn {
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const abortControllerRef = useRef<AbortController | null>(null)
  const prevUuidRef = useRef<string | undefined>(conversationUuid)

  const cancelPending = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
  }, [])

  const clearSuggestions = useCallback(() => {
    cancelPending()
    setSuggestions([])
    setIsLoading(false)
  }, [cancelPending])

  const fetchSuggestions = useCallback(
    (overrideUuid?: string) => {
      const uuid = overrideUuid || conversationUuid
      if (!uuid) return

      cancelPending()

      const controller = new AbortController()
      abortControllerRef.current = controller

      setIsLoading(true)
      setSuggestions([])

      const attemptFetch = (retriesLeft: number): void => {
        fetchSuggestionsApi(uuid, controller.signal)
          .then(data => {
            if (!controller.signal.aborted) {
              setSuggestions(data.suggestions)
              setIsLoading(false)
              logger.debug('Suggestions fetched', { count: data.suggestions.length })
            }
          })
          .catch(err => {
            if (controller.signal.aborted) return

            const status = err?.status ?? err?.response?.status
            if (status === 404 && retriesLeft > 0) {
              logger.debug('Suggestions 404, retrying after delay', { retriesLeft })
              setTimeout(() => {
                if (!controller.signal.aborted) {
                  attemptFetch(retriesLeft - 1)
                }
              }, RETRY_DELAY_MS)
              return
            }

            logger.warn('Failed to fetch suggestions', { error: String(err) })
            setSuggestions([])
            setIsLoading(false)
          })
      }

      attemptFetch(MAX_RETRIES)
    },
    [conversationUuid, cancelPending]
  )

  // Clear suggestions when switching between conversations (uuid→uuid change)
  // but NOT when uuid changes from undefined→uuid (new conversation creation)
  useEffect(() => {
    const prevUuid = prevUuidRef.current
    prevUuidRef.current = conversationUuid

    // Only clear when switching from one conversation to another
    if (prevUuid && conversationUuid && prevUuid !== conversationUuid) {
      clearSuggestions()
    }
    // Clear when navigating away from a conversation (uuid→undefined)
    if (prevUuid && !conversationUuid) {
      clearSuggestions()
    }
  }, [conversationUuid, clearSuggestions])

  // Cancel pending request on unmount
  useEffect(() => {
    return () => {
      cancelPending()
    }
  }, [cancelPending])

  return {
    suggestions,
    isLoading,
    fetchSuggestions,
    clearSuggestions,
  }
}
