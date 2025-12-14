import type { Message } from '@/types/chat'

interface MessageItemProps {
  message: Message
  userName?: string
}

export function MessageItem({ message, userName }: MessageItemProps) {
  const isUser = message.role === 'user'
  const avatarText = isUser ? (userName?.[0]?.toUpperCase() || 'U') : 'AI'

  return (
    <div className={`message-item message-item--${message.role}`}>
      <div className="message-item__avatar">{avatarText}</div>
      <div className="message-item__content">{message.content}</div>
    </div>
  )
}
