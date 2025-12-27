import { useState, useCallback, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { useConversations } from '@/hooks/useConversations'
import { useChat } from '@/hooks/useChat'
import { ChatSidebar, ChatInput, MessageList } from '@/components/chat'
import { Alert } from '@/components/ui'
import { logger } from '@/lib/logger'
import type { Message, Conversation } from '@/types/chat'
import { toConversation } from '@/types/chat'
import '@/styles/chat.css'

export function ChatPage() {
  const { uuid } = useParams<{ uuid?: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [isCreating, setIsCreating] = useState(false)

  // State for new conversation creation with streaming
  const [newConversation, setNewConversation] = useState<Conversation | null>(null)
  const [newMessages, setNewMessages] = useState<Message[]>([])
  const [newStreamingContent, setNewStreamingContent] = useState('')
  const [newIsStreaming, setNewIsStreaming] = useState(false)
  const [newConversationError, setNewConversationError] = useState<Error | null>(null)

  const {
    conversations,
    isLoading: isLoadingConversations,
    error: conversationsError,
    createConversationStreaming,
    loadConversations,
  } = useConversations()

  const {
    conversation,
    messages,
    isLoading: isLoadingChat,
    isStreaming,
    streamingContent,
    error: chatError,
    sendMessage,
  } = useChat({ uuid: uuid || '', autoLoad: !!uuid })

  // Clear new conversation state when navigating to a chat with uuid
  useEffect(() => {
    if (uuid) {
      setNewConversation(null)
      setNewMessages([])
      setNewStreamingContent('')
      setNewIsStreaming(false)
      setNewConversationError(null)
    } else {
      logger.debug('Ready for new chat')
    }
  }, [uuid])

  const handleNewChat = useCallback(() => {
    setNewConversation(null)
    setNewMessages([])
    setNewStreamingContent('')
    setNewIsStreaming(false)
    setNewConversationError(null)
    navigate('/chat')
    setIsSidebarOpen(false)
  }, [navigate])

  const handleSelectConversation = useCallback(
    (selectedUuid: string) => {
      navigate(`/chat/${selectedUuid}`)
      setIsSidebarOpen(false)
    },
    [navigate]
  )

  const handleSendMessage = useCallback(
    async (content: string) => {
      if (isStreaming || isCreating || newIsStreaming) return

      if (uuid) {
        // Existing conversation
        await sendMessage(content)
      } else {
        // New conversation - create with streaming AI response
        setIsCreating(true)
        setNewIsStreaming(true)
        setNewConversationError(null)

        // Add optimistic user message
        const tempUserMessage: Message = {
          id: Date.now(),
          role: 'user',
          content,
          createdAt: new Date(),
        }
        setNewMessages([tempUserMessage])

        let userMessagePersisted = false
        let createdUuid = ''

        try {
          let finalContent = ''
          let assistantMessageId = 0

          await createConversationStreaming(
            { message: content },
            {
              onCreated: (conversationDto, userMessageId) => {
                createdUuid = conversationDto.uuid
                userMessagePersisted = true
                setNewConversation(toConversation(conversationDto))
                // Update temp message with real ID
                setNewMessages(prev =>
                  prev.map(m => (m.id === tempUserMessage.id ? { ...m, id: userMessageId } : m))
                )
                logger.debug('Conversation created', { uuid: createdUuid, userMessageId })
              },
              onDelta: delta => {
                finalContent += delta
                setNewStreamingContent(finalContent)
              },
              onEnd: (msgId, responseContent) => {
                assistantMessageId = msgId
                finalContent = responseContent
                logger.debug('Streaming ended', { assistantMessageId })
              },
              onError: errorMsg => {
                // Propagate error to be caught by try-catch
                throw new Error(errorMsg)
              },
            }
          )

          // Add assistant message only if we got a valid response
          if (assistantMessageId > 0 && finalContent) {
            const assistantMessage: Message = {
              id: assistantMessageId,
              role: 'assistant',
              content: finalContent,
              createdAt: new Date(),
            }
            setNewMessages(prev => [...prev, assistantMessage])
          }
          setNewStreamingContent('')

          // Navigate to the new conversation
          if (createdUuid) {
            navigate(`/chat/${createdUuid}`, { replace: true })
          }
        } catch (err) {
          const error = err as Error
          logger.error('Failed to create conversation', error)
          setNewConversationError(error)
          setNewStreamingContent('')

          if (userMessagePersisted && createdUuid) {
            // Message was saved on server - navigate to conversation to sync state
            logger.warn('Error after message persisted, navigating to conversation', {
              uuid: createdUuid,
            })
            navigate(`/chat/${createdUuid}`, { replace: true })
          } else {
            // Message was not saved - remove optimistic message
            setNewMessages([])
            setNewConversation(null)
          }
        } finally {
          setIsCreating(false)
          setNewIsStreaming(false)
        }
      }
    },
    [
      uuid,
      isStreaming,
      isCreating,
      newIsStreaming,
      sendMessage,
      createConversationStreaming,
      navigate,
    ]
  )

  // Reload conversations when a new one is created
  useEffect(() => {
    if (uuid && conversations.length > 0 && !conversations.find(c => c.uuid === uuid)) {
      void loadConversations()
    }
  }, [uuid, conversations, loadConversations])

  const error = conversationsError || chatError || newConversationError
  const isInputDisabled = isStreaming || isCreating || newIsStreaming

  // Determine which messages and streaming content to show
  const displayMessages = uuid ? messages : newMessages
  const displayStreamingContent = uuid ? streamingContent : newStreamingContent
  const displayIsStreaming = uuid ? isStreaming : newIsStreaming
  const displayTitle = uuid
    ? conversation?.title || '読み込み中...'
    : newConversation?.title || '新しいチャット'

  // Show message list if we have messages or are streaming (new or existing conversation)
  const hasContent = displayMessages.length > 0 || displayIsStreaming

  return (
    <div className="chat-layout">
      <ChatSidebar
        conversations={conversations}
        currentUuid={uuid}
        isLoading={isLoadingConversations}
        userName={user?.name || undefined}
        userEmail={user?.email}
        onNewChat={handleNewChat}
        onSelectConversation={handleSelectConversation}
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
      />

      <main className="chat-main">
        <header className="chat-main__header">
          <button
            type="button"
            className="chat-main__toggle-sidebar"
            onClick={() => setIsSidebarOpen(true)}
            aria-label="サイドバーを開く"
          >
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          </button>
          <h1 className="chat-main__title">{displayTitle}</h1>
        </header>

        {error && (
          <div className="p-4">
            <Alert variant="error">{error.message}</Alert>
          </div>
        )}

        {uuid && isLoadingChat ? (
          <div className="chat-main__empty">読み込み中...</div>
        ) : hasContent ? (
          <div className="chat-main__messages">
            <MessageList
              messages={displayMessages}
              isStreaming={displayIsStreaming}
              streamingContent={displayStreamingContent}
              userName={user?.name || undefined}
            />
          </div>
        ) : (
          <div className="chat-main__empty">メッセージを入力して新しい会話を始めましょう</div>
        )}

        <ChatInput onSend={handleSendMessage} disabled={isInputDisabled} />
      </main>
    </div>
  )
}
