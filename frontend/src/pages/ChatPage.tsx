import { useState, useCallback, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { useConversations } from '@/hooks/useConversations'
import { useChat } from '@/hooks/useChat'
import { ChatSidebar, ChatInput, MessageList } from '@/components/chat'
import { Alert } from '@/components/ui'
import { logger } from '@/lib/logger'
import '@/styles/chat.css'

export function ChatPage() {
  const { uuid } = useParams<{ uuid?: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [isCreating, setIsCreating] = useState(false)

  const {
    conversations,
    isLoading: isLoadingConversations,
    error: conversationsError,
    createConversation,
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

  // Clear chat state when navigating to a new chat
  useEffect(() => {
    if (!uuid) {
      // When on /chat without uuid, we're ready for a new chat
      logger.debug('Ready for new chat')
    }
  }, [uuid])

  const handleNewChat = useCallback(() => {
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
      if (uuid) {
        // Existing conversation
        await sendMessage(content)
      } else {
        // New conversation - create it first
        setIsCreating(true)
        try {
          const newUuid = await createConversation({ content })
          navigate(`/chat/${newUuid}`, { replace: true })
        } finally {
          setIsCreating(false)
        }
      }
    },
    [uuid, sendMessage, createConversation, navigate]
  )

  // Reload conversations when a new one is created
  useEffect(() => {
    if (uuid && conversations.length > 0 && !conversations.find(c => c.uuid === uuid)) {
      void loadConversations()
    }
  }, [uuid, conversations, loadConversations])

  const error = conversationsError || chatError
  const isInputDisabled = isStreaming || isCreating

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
          <h1 className="chat-main__title">
            {uuid ? conversation?.title || '読み込み中...' : '新しいチャット'}
          </h1>
        </header>

        {error && (
          <div className="p-4">
            <Alert variant="error">{error.message}</Alert>
          </div>
        )}

        {uuid ? (
          isLoadingChat ? (
            <div className="chat-main__empty">読み込み中...</div>
          ) : (
            <div className="chat-main__messages">
              <MessageList
                messages={messages}
                isStreaming={isStreaming}
                streamingContent={streamingContent}
                userName={user?.name || undefined}
              />
            </div>
          )
        ) : (
          <div className="chat-main__empty">メッセージを入力して新しい会話を始めましょう</div>
        )}

        <ChatInput onSend={handleSendMessage} disabled={isInputDisabled} />
      </main>
    </div>
  )
}
