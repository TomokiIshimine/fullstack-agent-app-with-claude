import { useCallback, useEffect, useState, useRef } from 'react'
import {
  fetchConversation,
  sendMessageStreaming,
  createConversationStreaming,
} from '@/lib/api/conversations'
import { useErrorHandler } from './useErrorHandler'
import { useStreamingToolCalls } from './useStreamingToolCalls'
import type {
  Conversation,
  Message,
  SendMessageRequest,
  CreateConversationRequest,
} from '@/types/chat'
import { toConversation, toMessage } from '@/types/chat'
import { ConversationError } from '@/types/errors'
import { logger } from '@/lib/logger'

/**
 * Chat mode indicating current state
 */
export type ChatMode = 'idle' | 'existing' | 'new'

/**
 * Result of sending a message
 */
export interface SendMessageResult {
  /** UUID of the conversation (new or existing) */
  uuid: string
  /** Whether this was a new conversation */
  isNew: boolean
  /** Whether user message was persisted before any error */
  userMessagePersisted: boolean
}

/**
 * Options for useUnifiedChat hook
 */
export interface UseUnifiedChatOptions {
  /** Initial conversation UUID (undefined for new chat) */
  initialUuid?: string
}

/**
 * Unified conversation hook that handles both new and existing conversations.
 *
 * This hook consolidates the functionality of useChat and useNewConversation
 * into a single hook that automatically handles the correct behavior based on
 * whether a UUID is provided.
 *
 * @example
 * ```typescript
 * // In ChatPage
 * const { uuid } = useParams()
 * const chat = useUnifiedChat({ initialUuid: uuid })
 *
 * const handleSend = async (content: string) => {
 *   try {
 *     const result = await chat.sendMessage(content)
 *     if (result.isNew) {
 *       navigate(`/chat/${result.uuid}`, { replace: true })
 *     }
 *   } catch (err) {
 *     // Error handling with persisted message navigation
 *     if (isConversationError(err) && err.userMessagePersisted && err.uuid) {
 *       navigate(`/chat/${err.uuid}`, { replace: true })
 *     }
 *   }
 * }
 *
 * return (
 *   <MessageList
 *     messages={chat.messages}
 *     isStreaming={chat.isStreaming}
 *     streamingContent={chat.streamingContent}
 *   />
 * )
 * ```
 */
export function useUnifiedChat(options: UseUnifiedChatOptions = {}) {
  const { initialUuid } = options

  // Determine initial mode
  const getInitialMode = (): ChatMode => (initialUuid ? 'existing' : 'idle')

  const [mode, setMode] = useState<ChatMode>(getInitialMode)
  const [conversation, setConversation] = useState<Conversation | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(!!initialUuid)
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')

  // Track current UUID to handle navigation during async operations
  const currentUuidRef = useRef<string | undefined>(initialUuid)

  const { streamingToolCalls, addToolCall, completeToolCall, resetToolCalls, getToolCalls } =
    useStreamingToolCalls()
  const { error, handleError, clearError } = useErrorHandler()

  // Derived state
  const title =
    conversation?.title ||
    (mode === 'idle' ? '新しいチャット' : mode === 'new' ? '' : '読み込み中...')

  /**
   * Load an existing conversation by UUID
   */
  const loadConversation = useCallback(
    async (uuid: string) => {
      currentUuidRef.current = uuid
      setMode('existing')
      setIsLoading(true)
      clearError()

      try {
        const data = await fetchConversation(uuid)

        // Check if still relevant (user might have navigated away)
        if (currentUuidRef.current !== uuid) return

        setConversation(toConversation(data.conversation))
        setMessages(data.messages.map(toMessage))
        logger.info('Conversation loaded', { uuid, messageCount: data.messages.length })
      } catch (err) {
        handleError(err, 'Failed to load conversation')
      } finally {
        setIsLoading(false)
      }
    },
    [clearError, handleError]
  )

  /**
   * Reset to idle state (for new chat button)
   */
  const reset = useCallback(() => {
    currentUuidRef.current = undefined
    setMode('idle')
    setConversation(null)
    setMessages([])
    setStreamingContent('')
    resetToolCalls()
    setIsStreaming(false)
    clearError()
    logger.debug('Chat reset to idle')
  }, [clearError, resetToolCalls])

  /**
   * Send a message (handles both new and existing conversations)
   */
  const sendMessage = useCallback(
    async (content: string): Promise<SendMessageResult> => {
      if (isStreaming) {
        throw new Error('Already streaming')
      }

      const isNew = mode === 'idle'
      let userMessagePersisted = false
      let resultUuid = currentUuidRef.current || ''

      // Add optimistic user message
      const tempUserMessage: Message = {
        id: Date.now(),
        role: 'user',
        content,
        createdAt: new Date(),
      }
      setMessages(prev => [...prev, tempUserMessage])

      if (isNew) {
        setMode('new')
      }

      setIsStreaming(true)
      setStreamingContent('')
      resetToolCalls()
      clearError()

      try {
        let finalContent = ''
        let assistantMessageId = 0

        if (isNew) {
          // Create new conversation
          const request: CreateConversationRequest = { message: content }

          await createConversationStreaming(request, {
            onCreated: (conversationDto, userMessageId) => {
              resultUuid = conversationDto.uuid
              currentUuidRef.current = resultUuid
              userMessagePersisted = true
              setConversation(toConversation(conversationDto))
              setMessages(prev =>
                prev.map(m => (m.id === tempUserMessage.id ? { ...m, id: userMessageId } : m))
              )
              setMode('existing')
              logger.debug('Conversation created', { uuid: resultUuid, userMessageId })
            },
            onToolCallStart: (toolCallId, toolName, input) => {
              addToolCall(toolCallId, toolName, input)
            },
            onToolCallEnd: (toolCallId, output, toolError) => {
              completeToolCall(toolCallId, output, toolError)
            },
            onDelta: delta => {
              finalContent += delta
              setStreamingContent(finalContent)
            },
            onEnd: (msgId, responseContent) => {
              assistantMessageId = msgId
              finalContent = responseContent
            },
            onError: errorMsg => {
              throw new Error(errorMsg)
            },
          })
        } else {
          // Send to existing conversation
          const request: SendMessageRequest = { content }

          await sendMessageStreaming(resultUuid, request, {
            onStart: userMessageId => {
              userMessagePersisted = true
              setMessages(prev =>
                prev.map(m => (m.id === tempUserMessage.id ? { ...m, id: userMessageId } : m))
              )
              logger.debug('Streaming started', { userMessageId })
            },
            onToolCallStart: (toolCallId, toolName, input) => {
              addToolCall(toolCallId, toolName, input)
            },
            onToolCallEnd: (toolCallId, output, toolError) => {
              completeToolCall(toolCallId, output, toolError)
            },
            onDelta: delta => {
              finalContent += delta
              setStreamingContent(finalContent)
            },
            onEnd: (msgId, responseContent) => {
              assistantMessageId = msgId
              finalContent = responseContent
            },
            onError: (errorMsg, persistedUserMessageId) => {
              if (persistedUserMessageId !== undefined) {
                userMessagePersisted = true
              }
              throw new Error(errorMsg)
            },
          })
        }

        // Add assistant message
        const toolCalls = getToolCalls()
        if (assistantMessageId > 0) {
          const assistantMessage: Message = {
            id: assistantMessageId,
            role: 'assistant',
            content: finalContent,
            toolCalls: toolCalls.length > 0 ? toolCalls : undefined,
            createdAt: new Date(),
          }
          setMessages(prev => [...prev, assistantMessage])
        }
        setStreamingContent('')

        logger.info('Message sent successfully', { uuid: resultUuid, isNew })

        return { uuid: resultUuid, isNew, userMessagePersisted: true }
      } catch (err) {
        const error = err as Error

        if (!userMessagePersisted) {
          // Remove optimistic message if not persisted
          setMessages(prev => prev.filter(m => m.id !== tempUserMessage.id))
          if (isNew) {
            setMode('idle')
            setConversation(null)
          }
        } else if (!isNew && resultUuid) {
          // Reload existing conversation to sync state
          void loadConversation(resultUuid)
        }

        handleError(error, 'Failed to send message')

        // Throw enhanced error with context
        throw new ConversationError(error.message, {
          uuid: resultUuid || undefined,
          userMessagePersisted,
        })
      } finally {
        setIsStreaming(false)
        setStreamingContent('')
        resetToolCalls()
      }
    },
    [
      mode,
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

  // Auto-load on initial UUID change
  useEffect(() => {
    if (initialUuid && initialUuid !== currentUuidRef.current) {
      void loadConversation(initialUuid)
    } else if (!initialUuid && currentUuidRef.current) {
      reset()
    }
  }, [initialUuid, loadConversation, reset])

  return {
    // State
    mode,
    conversation,
    messages,
    isLoading,
    isStreaming,
    streamingContent,
    streamingToolCalls,
    error,
    title,
    // Actions
    sendMessage,
    reset,
    clearError,
    loadConversation,
  }
}
