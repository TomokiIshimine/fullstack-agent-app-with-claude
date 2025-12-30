import { useState, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { useConversations } from '@/hooks/useConversations'
import { useUnifiedChat } from '@/hooks/useUnifiedChat'
import { ChatSidebar, ChatInput, MessageList, ChatError } from '@/components/chat'
import { Alert } from '@/components/ui'
import { isConversationError } from '@/types/errors'
import { logger } from '@/lib/logger'
import '@/styles/chat.css'

export function ChatPage() {
  const { uuid } = useParams<{ uuid?: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)

  const {
    conversations,
    isLoading: isLoadingConversations,
    error: conversationsError,
    loadConversations,
  } = useConversations()

  const chat = useUnifiedChat({ initialUuid: uuid })

  const handleNewChat = useCallback(() => {
    chat.reset()
    navigate('/chat')
    setIsSidebarOpen(false)
  }, [navigate, chat])

  const handleSelectConversation = useCallback(
    (selectedUuid: string) => {
      navigate(`/chat/${selectedUuid}`)
      setIsSidebarOpen(false)
    },
    [navigate]
  )

  const handleSendMessage = useCallback(
    async (content: string) => {
      if (chat.isStreaming) return

      try {
        const result = await chat.sendMessage(content)

        if (result.isNew) {
          void loadConversations()
          navigate(`/chat/${result.uuid}`, { replace: true })
        }
      } catch (err) {
        // Check if we should navigate despite error
        if (isConversationError(err) && err.userMessagePersisted && err.uuid) {
          logger.warn('Error after message persisted, navigating to conversation', {
            uuid: err.uuid,
          })
          void loadConversations()
          navigate(`/chat/${err.uuid}`, { replace: true })
        }
        // Error is already set in hook state
      }
    },
    [chat, loadConversations, navigate]
  )

  const error = conversationsError || chat.error
  const hasContent = chat.messages.length > 0 || chat.isStreaming

  return (
    <div className="chat-layout">
      <ChatSidebar
        conversations={conversations}
        currentUuid={uuid}
        isLoading={isLoadingConversations}
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
          <h1 className="chat-main__title">{chat.title}</h1>
        </header>

        {error && (
          <div className="p-4">
            <Alert variant="error">{error}</Alert>
          </div>
        )}

        {uuid && chat.isLoading ? (
          <div className="chat-main__empty">読み込み中...</div>
        ) : hasContent ? (
          <div className="chat-main__messages">
            <MessageList
              messages={chat.messages}
              isStreaming={chat.isStreaming}
              streamingContent={chat.streamingContent}
              streamingToolCalls={chat.streamingToolCalls}
              retryStatus={chat.retryStatus}
              userName={user?.name || undefined}
            />
          </div>
        ) : (
          <div className="chat-main__empty">メッセージを入力して新しい会話を始めましょう</div>
        )}

        <div className="chat-main__footer">
          {chat.streamError && (
            <div className="px-4 pb-2">
              <ChatError error={chat.streamError} onDismiss={chat.clearStreamError} />
            </div>
          )}
          <ChatInput onSend={handleSendMessage} disabled={chat.isStreaming || chat.isLoading} />
        </div>
      </main>
    </div>
  )
}
