import type { Conversation } from '@/types/chat'
import { cn } from '@/lib/utils/cn'

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

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && onClose && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'w-[280px] bg-slate-800 text-white flex flex-col shrink-0',
          'max-md:fixed max-md:left-0 max-md:top-16 max-md:bottom-0 max-md:z-50 max-md:transition-transform max-md:duration-300',
          isOpen ? 'max-md:translate-x-0' : 'max-md:-translate-x-full'
        )}
      >
        <div className="p-4 border-b border-slate-700">
          <button
            type="button"
            className="w-full py-3 px-4 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm font-medium cursor-pointer transition-colors duration-200 flex items-center gap-2 hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed"
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

        <div className="flex-1 overflow-y-auto p-2">
          {isLoading ? (
            <div className="p-8 text-center text-slate-400">読み込み中...</div>
          ) : conversations.length === 0 ? (
            <div className="p-8 text-center text-slate-400 text-sm">会話履歴がありません</div>
          ) : (
            conversations.map(conv => (
              <button
                key={conv.uuid}
                type="button"
                className={cn(
                  'w-full text-left py-3 px-4 rounded-lg cursor-pointer transition-colors duration-200 mb-1',
                  'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 focus:ring-offset-slate-800',
                  conv.uuid === currentUuid ? 'bg-slate-600' : 'hover:bg-slate-700'
                )}
                onClick={() => onSelectConversation(conv.uuid)}
                aria-label={`会話: ${conv.title}、${formatDate(conv.updatedAt)}`}
                aria-current={conv.uuid === currentUuid ? 'true' : undefined}
              >
                <div className="text-sm font-medium truncate">{conv.title}</div>
                <div className="text-xs text-slate-400 mt-1">{formatDate(conv.updatedAt)}</div>
              </button>
            ))
          )}
        </div>
      </aside>
    </>
  )
}
