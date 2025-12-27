import { useCallback, useEffect, useState } from 'react'
import {
  createConversation as createConversationApi,
  createConversationStreaming as createConversationStreamingApi,
  deleteConversation as deleteConversationApi,
  fetchConversations,
  type CreateConversationStreamCallbacks,
} from '@/lib/api/conversations'
import { useErrorHandler } from './useErrorHandler'
import type { ConversationWithCount, CreateConversationRequest, PaginationMeta } from '@/types/chat'
import { toConversationWithCount } from '@/types/chat'
import { logger } from '@/lib/logger'

interface UseConversationsOptions {
  page?: number
  perPage?: number
  autoLoad?: boolean
}

export function useConversations(options: UseConversationsOptions = {}) {
  const { page = 1, perPage = 20, autoLoad = true } = options

  const [conversations, setConversations] = useState<ConversationWithCount[]>([])
  const [meta, setMeta] = useState<PaginationMeta | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const { error, handleError, clearError } = useErrorHandler()

  const loadConversations = useCallback(
    async (loadPage?: number) => {
      setIsLoading(true)
      clearError()
      try {
        const data = await fetchConversations(loadPage ?? page, perPage)
        setConversations(data.conversations.map(toConversationWithCount))
        setMeta(data.meta)
        logger.info('Conversations loaded', { count: data.conversations.length })
      } catch (err) {
        handleError(err, 'Failed to load conversations')
      } finally {
        setIsLoading(false)
      }
    },
    [page, perPage, clearError, handleError]
  )

  const createConversation = useCallback(
    async (payload: CreateConversationRequest): Promise<string> => {
      try {
        const response = await createConversationApi(payload)
        logger.info('Conversation created', { uuid: response.conversation.uuid })
        // Reload conversations to include the new one
        await loadConversations()
        return response.conversation.uuid
      } catch (err) {
        handleError(err, 'Failed to create conversation')
        throw err
      }
    },
    [handleError, loadConversations]
  )

  const createConversationStreaming = useCallback(
    async (
      payload: CreateConversationRequest,
      callbacks: CreateConversationStreamCallbacks
    ): Promise<void> => {
      try {
        await createConversationStreamingApi(payload, callbacks)
        logger.info('Conversation created with streaming')
        // Reload conversations to include the new one
        await loadConversations()
      } catch (err) {
        handleError(err, 'Failed to create conversation')
        throw err
      }
    },
    [handleError, loadConversations]
  )

  const deleteConversation = useCallback(
    async (uuid: string) => {
      try {
        await deleteConversationApi(uuid)
        logger.info('Conversation deleted', { uuid })
        // Remove from local state
        setConversations(prev => prev.filter(c => c.uuid !== uuid))
      } catch (err) {
        handleError(err, 'Failed to delete conversation')
        throw err
      }
    },
    [handleError]
  )

  useEffect(() => {
    if (autoLoad) {
      void loadConversations()
    }
  }, [autoLoad, loadConversations])

  return {
    conversations,
    meta,
    isLoading,
    error,
    clearError,
    loadConversations,
    createConversation,
    createConversationStreaming,
    deleteConversation,
  }
}
