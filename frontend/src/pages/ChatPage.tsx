import { useState, useCallback, useRef } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { useConversations } from '@/hooks/useConversations'
import { useUnifiedChat } from '@/hooks/useUnifiedChat'
import { useUserSettings } from '@/hooks/useUserSettings'
import { useSuggestions } from '@/hooks/useSuggestions'
import { ChatSidebar, ChatInput, MessageList, ChatError } from '@/components/chat'
import { Alert } from '@/components/ui'
import { isConversationError } from '@/types/errors'
import { logger } from '@/lib/logger'

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

  const { sendShortcut, isLoading: isLoadingSettings } = useUserSettings()
  const chat = useUnifiedChat({ initialUuid: uuid })
  const suggestions = useSuggestions({ conversationUuid: uuid })

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

  // Track the current conversation uuid to detect stale async callbacks
  const currentUuidRef = useRef(uuid)
  currentUuidRef.current = uuid

  const handleSendMessage = useCallback(
    async (content: string) => {
      if (chat.isStreaming) return
      suggestions.clearSuggestions()

      try {
        const result = await chat.sendMessage(content)

        if (result.isNew) {
          void loadConversations()
          currentUuidRef.current = result.uuid
          navigate(`/chat/${result.uuid}`, { replace: true })
        }
        // Guard: skip if user navigated to a different conversation while streaming
        const expectedUuid = result.isNew ? result.uuid : uuid
        if (currentUuidRef.current !== expectedUuid) return
        suggestions.fetchSuggestions(result.isNew ? result.uuid : undefined)
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
    [chat, suggestions, loadConversations, navigate]
  )

  const error = conversationsError || chat.error
  const hasContent = chat.messages.length > 0 || chat.isStreaming

  return (
    <div className="flex h-[calc(100vh-4rem)] overflow-hidden bg-slate-50">
      <ChatSidebar
        conversations={conversations}
        currentUuid={uuid}
        isLoading={isLoadingConversations}
        onNewChat={handleNewChat}
        onSelectConversation={handleSelectConversation}
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
      />

      <main className="flex-1 flex flex-col min-w-0">
        <header className="px-4 md:px-6 py-4 border-b border-slate-200 bg-white flex items-center justify-between">
          <button
            type="button"
            className="mr-3 md:hidden text-slate-600 hover:text-slate-800"
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
          <h1 className="text-base font-semibold text-slate-800">{chat.title}</h1>
        </header>

        {error && (
          <div className="p-4">
            <Alert variant="error">{error}</Alert>
          </div>
        )}

        {uuid && chat.isLoading ? (
          <div className="flex-1 flex items-center justify-center text-slate-500">
            読み込み中...
          </div>
        ) : hasContent ? (
          <div className="flex-1 overflow-y-auto p-6">
            <MessageList
              messages={chat.messages}
              isStreaming={chat.isStreaming}
              streamingContent={chat.streamingContent}
              streamingToolCalls={chat.streamingToolCalls}
              retryStatus={chat.retryStatus}
              userName={user?.name || undefined}
              suggestions={suggestions.suggestions}
              isSuggestionsLoading={suggestions.isLoading}
              onSuggestionSelect={handleSendMessage}
            />
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center text-slate-500">
            メッセージを入力して新しい会話を始めましょう
          </div>
        )}

        <div>
          {chat.streamError && (
            <div className="px-4 pb-2">
              <ChatError error={chat.streamError} onDismiss={chat.clearStreamError} />
            </div>
          )}
          <ChatInput
            onSend={handleSendMessage}
            disabled={chat.isStreaming || chat.isLoading}
            sendShortcut={isLoadingSettings ? undefined : sendShortcut}
          />
        </div>
      </main>
    </div>
  )
}
