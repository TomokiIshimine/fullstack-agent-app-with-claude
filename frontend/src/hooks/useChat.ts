import { useCallback, useEffect, useState } from 'react'
import { fetchConversation, sendMessageStreaming } from '@/lib/api/conversations'
import { useErrorHandler } from './useErrorHandler'
import type { Conversation, Message, SendMessageRequest } from '@/types/chat'
import { toConversation, toMessage } from '@/types/chat'
import type { StreamingToolCall } from '@/types/tool'
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
  const [streamingToolCalls, setStreamingToolCalls] = useState<StreamingToolCall[]>([])
  const { error, handleError, clearError } = useErrorHandler()

  const loadConversation = useCallback(
    async (conversationUuid?: string) => {
      const targetUuid = conversationUuid ?? uuid

      if (!targetUuid) {
        return
      }

      setIsLoading(true)
      clearError()
      try {
        const data = await fetchConversation(targetUuid)
        setConversation(toConversation(data.conversation))
        setMessages(data.messages.map(toMessage))
        logger.info('Conversation loaded', { uuid: targetUuid, messageCount: data.messages.length })
      } catch (err) {
        handleError(err, 'Failed to load conversation')
      } finally {
        setIsLoading(false)
      }
    },
    [uuid, clearError, handleError]
  )

  const sendMessage = useCallback(
    async (content: string, conversationUuid?: string) => {
      const targetUuid = conversationUuid ?? uuid

      if (!targetUuid) {
        throw new Error('Conversation UUID is required to send a message')
      }

      if (isStreaming) return

      const request: SendMessageRequest = { content }

      // Add optimistic user message
      const tempUserMessage: Message = {
        id: Date.now(), // Temporary ID
        role: 'user',
        content,
        createdAt: new Date(),
      }
      setMessages(prev => [...prev, tempUserMessage])

      setIsStreaming(true)
      setStreamingContent('')
      setStreamingToolCalls([])
      clearError()

      let userMessagePersisted = false
      let realUserMessageId: number | undefined

      try {
        let finalContent = ''
        let assistantMessageId = 0

        await sendMessageStreaming(targetUuid, request, {
          onStart: userMessageId => {
            // Update the temp user message with real ID
            realUserMessageId = userMessageId
            userMessagePersisted = true
            setMessages(prev =>
              prev.map(m => (m.id === tempUserMessage.id ? { ...m, id: userMessageId } : m))
            )
            logger.debug('Streaming started', { userMessageId })
          },
          onToolCallStart: (toolCallId, toolName, input) => {
            const newToolCall: StreamingToolCall = {
              toolCallId,
              toolName,
              input,
              status: 'pending',
            }
            setStreamingToolCalls(prev => [...prev, newToolCall])
            logger.debug('Tool call started', { toolCallId, toolName })
          },
          onToolCallEnd: (toolCallId, output, error) => {
            setStreamingToolCalls(prev =>
              prev.map(tc =>
                tc.toolCallId === toolCallId
                  ? { ...tc, output, error, status: error ? 'error' : 'success' }
                  : tc
              )
            )
            logger.debug('Tool call ended', { toolCallId, hasError: !!error })
          },
          onDelta: delta => {
            finalContent += delta
            setStreamingContent(finalContent)
          },
          onEnd: (msgId, content) => {
            assistantMessageId = msgId
            if (content.length > 0) {
              finalContent = content
              setStreamingContent(content)
            }
            logger.debug('Streaming ended', { assistantMessageId, hasContent: content.length > 0 })
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
        setMessages(prev => [...prev, assistantMessage])
        setStreamingContent('')

        logger.info('Message sent successfully', { uuid: targetUuid })
      } catch (err) {
        if (userMessagePersisted) {
          // Message was saved on server - reload conversation to sync state
          logger.warn('Error after message persisted, reloading conversation', {
            uuid: targetUuid,
            realUserMessageId,
          })
          void loadConversation(targetUuid)
        } else {
          // Message was not saved - safe to remove optimistic message
          setMessages(prev => prev.filter(m => m.id !== tempUserMessage.id))
        }
        handleError(err, 'Failed to send message')
        throw err
      } finally {
        setIsStreaming(false)
        setStreamingContent('')
        setStreamingToolCalls([])
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
    streamingToolCalls,
    error,
    clearError,
    loadConversation,
    sendMessage,
  }
}
