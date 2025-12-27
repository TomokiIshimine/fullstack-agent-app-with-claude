import { useCallback, useState } from 'react'
import { createConversationStreaming } from '@/lib/api/conversations'
import { useErrorHandler } from './useErrorHandler'
import type { Conversation, Message, CreateConversationRequest } from '@/types/chat'
import { toConversation } from '@/types/chat'
import type { StreamingToolCall } from '@/types/tool'
import { logger } from '@/lib/logger'

/**
 * Result of creating a new conversation
 */
export interface CreateConversationResult {
  /** UUID of the created conversation */
  uuid: string
  /** Whether the user message was persisted */
  userMessagePersisted: boolean
}

/**
 * Hook for managing new conversation creation with streaming
 *
 * Handles:
 * - Optimistic user message display
 * - Streaming AI response
 * - Error recovery with message persistence detection
 * - State management for all streaming lifecycle
 *
 * @example
 * const {
 *   conversation,
 *   messages,
 *   isStreaming,
 *   streamingContent,
 *   error,
 *   createConversation,
 *   reset
 * } = useNewConversation()
 *
 * const handleSend = async (content: string) => {
 *   try {
 *     const { uuid } = await createConversation(content)
 *     navigate(`/chat/${uuid}`)
 *   } catch {
 *     // Error already set in hook state
 *   }
 * }
 */
export function useNewConversation() {
  const [conversation, setConversation] = useState<Conversation | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const [streamingToolCalls, setStreamingToolCalls] = useState<StreamingToolCall[]>([])
  const { error, handleError, clearError } = useErrorHandler()

  /**
   * Reset all state to initial values
   */
  const reset = useCallback(() => {
    setConversation(null)
    setMessages([])
    setStreamingContent('')
    setStreamingToolCalls([])
    setIsStreaming(false)
    clearError()
  }, [clearError])

  /**
   * Create a new conversation with streaming AI response
   *
   * @param content - The initial message content
   * @returns Promise with conversation UUID and persistence status
   * @throws Error if streaming fails (also sets error state)
   */
  const createConversation = useCallback(
    async (content: string): Promise<CreateConversationResult> => {
      if (isStreaming) {
        throw new Error('Already streaming')
      }

      setIsStreaming(true)
      setStreamingContent('')
      setStreamingToolCalls([])
      clearError()

      // Add optimistic user message
      const tempUserMessage: Message = {
        id: Date.now(),
        role: 'user',
        content,
        createdAt: new Date(),
      }
      setMessages([tempUserMessage])

      let userMessagePersisted = false
      let createdUuid = ''

      try {
        let finalContent = ''
        let assistantMessageId = 0

        const request: CreateConversationRequest = { message: content }

        await createConversationStreaming(request, {
          onCreated: (conversationDto, userMessageId) => {
            createdUuid = conversationDto.uuid
            userMessagePersisted = true
            setConversation(toConversation(conversationDto))
            // Update temp message with real ID
            setMessages(prev =>
              prev.map(m => (m.id === tempUserMessage.id ? { ...m, id: userMessageId } : m))
            )
            logger.debug('Conversation created', { uuid: createdUuid, userMessageId })
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
          onEnd: (msgId, responseContent) => {
            assistantMessageId = msgId
            if (responseContent.length > 0) {
              finalContent = responseContent
              setStreamingContent(responseContent)
            }
            logger.debug('Streaming ended', { assistantMessageId, hasContent: responseContent.length > 0 })
          },
          onError: errorMsg => {
            throw new Error(errorMsg)
          },
        })

        // Add assistant message only if we got a valid response
        if (assistantMessageId > 0 && finalContent) {
          const assistantMessage: Message = {
            id: assistantMessageId,
            role: 'assistant',
            content: finalContent,
            createdAt: new Date(),
          }
          setMessages(prev => [...prev, assistantMessage])
        }
        setStreamingContent('')

        logger.info('New conversation created', { uuid: createdUuid })

        return { uuid: createdUuid, userMessagePersisted }
      } catch (err) {
        const error = err as Error
        logger.error('Failed to create conversation', error)
        handleError(error, 'Failed to create conversation')
        setStreamingContent('')

        if (!userMessagePersisted) {
          // Message was not saved - remove optimistic message
          setMessages([])
          setConversation(null)
        }
        // If userMessagePersisted is true, keep the messages for potential recovery

        // Re-throw with context for caller to handle navigation
        const enhancedError = new Error(error.message) as Error & {
          uuid?: string
          userMessagePersisted?: boolean
        }
        enhancedError.uuid = createdUuid
        enhancedError.userMessagePersisted = userMessagePersisted
        throw enhancedError
      } finally {
        setIsStreaming(false)
        setStreamingToolCalls([])
      }
    },
    [isStreaming, clearError, handleError]
  )

  return {
    // State
    conversation,
    messages,
    isStreaming,
    streamingContent,
    streamingToolCalls,
    error,
    // Actions
    createConversation,
    reset,
    clearError,
  }
}
