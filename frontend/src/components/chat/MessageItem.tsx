import type { Message } from '@/types/chat'
import { ToolCallItem } from './ToolCallItem'

interface MessageItemProps {
  message: Message
  userName?: string
}

export function MessageItem({ message, userName }: MessageItemProps) {
  const isUser = message.role === 'user'
  const avatarText = isUser ? userName?.[0]?.toUpperCase() || 'U' : 'AI'
  const hasToolCalls = message.toolCalls && message.toolCalls.length > 0

  return (
    <div className={`message-item message-item--${message.role}`}>
      <div className="message-item__avatar">{avatarText}</div>
      <div className="message-item__content">
        {hasToolCalls && (
          <div className="message-item__tool-calls">
            {message.toolCalls!.map(tc => (
              <ToolCallItem key={tc.id} toolCall={tc} />
            ))}
          </div>
        )}
        {message.content}
      </div>
    </div>
  )
}
