import type { Conversation } from '@/types/chat'

interface ChatSidebarProps {
  conversations: Conversation[]
  currentUuid?: string
  isLoading: boolean
  onNewChat: () => void
  onSelectConversation: (uuid: string) => void
  isOpen?: boolean
  onClose?: () => void
}

export function ChatSidebar({
  conversations,
  currentUuid,
  isLoading,
  onNewChat,
  onSelectConversation,
  isOpen = true,
  onClose,
}: ChatSidebarProps) {

  const formatDate = (date: Date) => {
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))

    if (days === 0) {
      return '今日'
    } else if (days === 1) {
      return '昨日'
    } else if (days < 7) {
      return `${days}日前`
    } else {
      return date.toLocaleDateString('ja-JP', { month: 'short', day: 'numeric' })
    }
  }

  const sidebarClasses = ['chat-sidebar', isOpen && 'chat-sidebar--open'].filter(Boolean).join(' ')

  return (
    <>
      {isOpen && onClose && <div className="chat-sidebar__overlay" onClick={onClose} />}
      <aside className={sidebarClasses}>
        <div className="chat-sidebar__header">
          <button
            type="button"
            className="chat-sidebar__new-chat-btn"
            onClick={onNewChat}
            disabled={isLoading}
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            新しいチャット
          </button>
        </div>

        <div className="chat-sidebar__list">
          {isLoading ? (
            <div className="chat-sidebar__loading">読み込み中...</div>
          ) : conversations.length === 0 ? (
            <div className="chat-sidebar__empty">会話履歴がありません</div>
          ) : (
            conversations.map(conv => (
              <div
                key={conv.uuid}
                className={`chat-sidebar__item ${conv.uuid === currentUuid ? 'chat-sidebar__item--active' : ''}`}
                onClick={() => onSelectConversation(conv.uuid)}
                role="button"
                tabIndex={0}
                onKeyDown={e => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    onSelectConversation(conv.uuid)
                  }
                }}
              >
                <div className="chat-sidebar__item-title">{conv.title}</div>
                <div className="chat-sidebar__item-date">{formatDate(conv.updatedAt)}</div>
              </div>
            ))
          )}
        </div>
      </aside>
    </>
  )
}
