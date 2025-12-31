import { useCallback, useEffect, useState } from 'react'
import { fetchConversation, sendMessageStreaming } from '@/lib/api/conversations'
import { useErrorHandler } from './useErrorHandler'
import { createOnRetryHandler } from './useStreamingCallbacks'
import { useStreamingToolCalls } from './useStreamingToolCalls'
import type { Conversation, Message, MessageMetadata, SendMessageRequest } from '@/types/chat'
import { toConversation, toMessage } from '@/types/chat'
import type { RetryStatus } from '@/types/errors'
import { fromStreamError } from '@/types/errors'
import { logger } from '@/lib/logger'

interface UseChatOptions {
  uuid: string
  autoLoad?: boolean
}

/**
 * @deprecated Use `useUnifiedChat` instead. This hook will be removed in a future version.
 *
 * Migration guide:
 * ```typescript
 * // Before
 * const { messages, isStreaming, sendMessage } = useChat({ uuid })
 *
 * // After
 * const { messages, isStreaming, sendMessage } = useUnifiedChat({ initialUuid: uuid })
 * ```
 *
 * @see useUnifiedChat for the new unified conversation hook
 */
export function useChat(options: UseChatOptions) {
  const { uuid, autoLoad = true } = options

  const [conversation, setConversation] = useState<Conversation | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const [retryStatus, setRetryStatus] = useState<RetryStatus | null>(null)
  const { streamingToolCalls, addToolCall, completeToolCall, resetToolCalls, getToolCalls } =
    useStreamingToolCalls()
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
      setRetryStatus(null)
      resetToolCalls()
      clearError()

      let userMessagePersisted = false
      let realUserMessageId: number | undefined

      try {
        let finalContent = ''
        let assistantMessageId = 0
        let messageMetadata: MessageMetadata | undefined

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
            addToolCall(toolCallId, toolName, input)
            logger.debug('Tool call started', { toolCallId, toolName })
          },
          onToolCallEnd: (toolCallId, output, toolError) => {
            completeToolCall(toolCallId, output, toolError)
            logger.debug('Tool call ended', { toolCallId, hasError: !!toolError })
          },
          onDelta: delta => {
            finalContent += delta
            setStreamingContent(finalContent)
          },
          onEnd: (msgId, content, metadata) => {
            assistantMessageId = msgId
            finalContent = content
            messageMetadata = metadata
            setRetryStatus(null)
            logger.debug('Streaming ended', { assistantMessageId })
          },
          onRetry: createOnRetryHandler(setRetryStatus, {
            onReset: () => {
              finalContent = ''
              setStreamingContent('')
              resetToolCalls()
            },
          }),
          onError: streamErr => {
            // If user message was persisted (indicated by presence of ID), mark it
            if (streamErr.user_message_id !== undefined) {
              userMessagePersisted = true
              realUserMessageId = streamErr.user_message_id
            }
            throw fromStreamError(streamErr, targetUuid)
          },
        })

        // Add assistant message with accumulated tool calls
        const toolCalls = getToolCalls()
        const assistantMessage: Message = {
          id: assistantMessageId,
          role: 'assistant',
          content: finalContent,
          toolCalls: toolCalls.length > 0 ? toolCalls : undefined,
          createdAt: new Date(),
          metadata: messageMetadata,
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
        setRetryStatus(null)
        resetToolCalls()
      }
    },
    [
      uuid,
      isStreaming,
      clearError,
      handleError,
      loadConversation,
      addToolCall,
      completeToolCall,
      resetToolCalls,
      getToolCalls,
    ]
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
    retryStatus,
    clearError,
    loadConversation,
    sendMessage,
  }
}
