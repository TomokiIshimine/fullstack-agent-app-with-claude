import { useCallback, useEffect, useState } from 'react'
import { fetchConversation, sendMessageStreaming } from '@/lib/api/conversations'
import { useErrorHandler } from './useErrorHandler'
import type { Conversation, Message, SendMessageRequest } from '@/types/chat'
import { toConversation, toMessage } from '@/types/chat'
import { logger } from '@/lib/logger'

interface UseChatOptions {
  uuid: string
  autoLoad?: boolean
}

export function useChat(options: UseChatOptions) {
  const { uuid, autoLoad = true } = options

  const [conversation, setConversation] = useState<Conversation | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const { error, handleError, clearError } = useErrorHandler()

  const loadConversation = useCallback(async () => {
    setIsLoading(true)
    clearError()
    try {
      const data = await fetchConversation(uuid)
      setConversation(toConversation(data.conversation))
      setMessages(data.messages.map(toMessage))
      logger.info('Conversation loaded', { uuid, messageCount: data.messages.length })
    } catch (err) {
      handleError(err, 'Failed to load conversation')
    } finally {
      setIsLoading(false)
    }
  }, [uuid, clearError, handleError])

  const sendMessage = useCallback(
    async (content: string) => {
      if (isStreaming) return

      const request: SendMessageRequest = { content }

      // Add optimistic user message
      const tempUserMessage: Message = {
        id: Date.now(), // Temporary ID
        role: 'user',
        content,
        createdAt: new Date(),
      }
      setMessages((prev) => [...prev, tempUserMessage])

      setIsStreaming(true)
      setStreamingContent('')
      clearError()

      let userMessagePersisted = false
      let realUserMessageId: number | undefined

      try {
        let finalContent = ''
        let assistantMessageId = 0

        await sendMessageStreaming(uuid, request, {
          onStart: (userMessageId) => {
            // Update the temp user message with real ID
            realUserMessageId = userMessageId
            userMessagePersisted = true
            setMessages((prev) =>
              prev.map((m) =>
                m.id === tempUserMessage.id ? { ...m, id: userMessageId } : m
              )
            )
            logger.debug('Streaming started', { userMessageId })
          },
          onDelta: (delta) => {
            finalContent += delta
            setStreamingContent(finalContent)
          },
          onEnd: (msgId, content) => {
            assistantMessageId = msgId
            finalContent = content
            logger.debug('Streaming ended', { assistantMessageId })
          },
          onError: (errorMsg, persistedUserMessageId) => {
            // If user message was persisted (indicated by presence of ID), mark it
            if (persistedUserMessageId !== undefined) {
              userMessagePersisted = true
              realUserMessageId = persistedUserMessageId
            }
            throw new Error(errorMsg)
          },
        })

        // Add assistant message
        const assistantMessage: Message = {
          id: assistantMessageId,
          role: 'assistant',
          content: finalContent,
          createdAt: new Date(),
        }
        setMessages((prev) => [...prev, assistantMessage])
        setStreamingContent('')

        logger.info('Message sent successfully', { uuid })
      } catch (err) {
        if (userMessagePersisted) {
          // Message was saved on server - reload conversation to sync state
          logger.warn('Error after message persisted, reloading conversation', { uuid, realUserMessageId })
          void loadConversation()
        } else {
          // Message was not saved - safe to remove optimistic message
          setMessages((prev) => prev.filter((m) => m.id !== tempUserMessage.id))
        }
        handleError(err, 'Failed to send message')
        throw err
      } finally {
        setIsStreaming(false)
        setStreamingContent('')
      }
    },
    [uuid, isStreaming, clearError, handleError, loadConversation]
  )

  useEffect(() => {
    if (autoLoad && uuid) {
      void loadConversation()
    }
  }, [autoLoad, uuid, loadConversation])

  return {
    conversation,
    messages,
    isLoading,
    isStreaming,
    streamingContent,
    error,
    clearError,
    loadConversation,
    sendMessage,
  }
}
