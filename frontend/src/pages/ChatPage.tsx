import { useState, useCallback, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { useConversations } from '@/hooks/useConversations'
import { useChat } from '@/hooks/useChat'
import { useNewConversation } from '@/hooks/useNewConversation'
import { ChatSidebar, ChatInput, MessageList } from '@/components/chat'
import { Alert } from '@/components/ui'
import { logger } from '@/lib/logger'
import '@/styles/chat.css'

export function ChatPage() {
  const { uuid } = useParams<{ uuid?: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)

  // Existing conversation management
  const {
    conversations,
    isLoading: isLoadingConversations,
    error: conversationsError,
    loadConversations,
  } = useConversations()

  // Selected conversation (when uuid is present)
  const {
    conversation,
    messages,
    isLoading: isLoadingChat,
    isStreaming,
    streamingContent,
    streamingToolCalls,
    error: chatError,
    sendMessage,
  } = useChat({ uuid: uuid || '', autoLoad: !!uuid })

  // New conversation creation
  const {
    conversation: newConversation,
    messages: newMessages,
    isStreaming: newIsStreaming,
    streamingContent: newStreamingContent,
    streamingToolCalls: newStreamingToolCalls,
    error: newConversationError,
    createConversation: createNewConversation,
    reset: resetNewConversation,
  } = useNewConversation()

  // Reset new conversation state when navigating to a chat with uuid
  useEffect(() => {
    if (uuid) {
      resetNewConversation()
    } else {
      logger.debug('Ready for new chat')
    }
  }, [uuid, resetNewConversation])

  const handleNewChat = useCallback(() => {
    resetNewConversation()
    navigate('/chat')
    setIsSidebarOpen(false)
  }, [navigate, resetNewConversation])

  const handleSelectConversation = useCallback(
    (selectedUuid: string) => {
      navigate(`/chat/${selectedUuid}`)
      setIsSidebarOpen(false)
    },
    [navigate]
  )

  const handleSendMessage = useCallback(
    async (content: string) => {
      if (isStreaming || newIsStreaming) return

      if (uuid) {
        // Existing conversation
        await sendMessage(content)
      } else {
        // New conversation
        try {
          const { uuid: createdUuid } = await createNewConversation(content)
          // Reload sidebar to include new conversation
          void loadConversations()
          navigate(`/chat/${createdUuid}`, { replace: true })
        } catch (err) {
          // Check if we should navigate despite error
          const error = err as Error & { uuid?: string; userMessagePersisted?: boolean }
          if (error.userMessagePersisted && error.uuid) {
            logger.warn('Error after message persisted, navigating to conversation', {
              uuid: error.uuid,
            })
            // Reload sidebar even on error if conversation was created
            void loadConversations()
            navigate(`/chat/${error.uuid}`, { replace: true })
          }
          // Error is already set in hook state
        }
      }
    },
    [
      uuid,
      isStreaming,
      newIsStreaming,
      sendMessage,
      createNewConversation,
      loadConversations,
      navigate,
    ]
  )

  const error = conversationsError || chatError || newConversationError
  const isInputDisabled = isStreaming || newIsStreaming

  // Determine which messages and streaming content to show
  const displayMessages = uuid ? messages : newMessages
  const displayStreamingContent = uuid ? streamingContent : newStreamingContent
  const displayStreamingToolCalls = uuid ? streamingToolCalls : newStreamingToolCalls
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
            <Alert variant="error">{error}</Alert>
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
              streamingToolCalls={displayStreamingToolCalls}
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
