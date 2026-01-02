import type { Message } from '@/types/chat'
import { ToolCallsGroup } from './ToolCallsGroup'
import { MarkdownRenderer } from './MarkdownRenderer'
import { MessageMetadata } from './MessageMetadata'

interface MessageItemProps {
  message: Message
  userName?: string
}

export function MessageItem({ message, userName }: MessageItemProps) {
  const isUser = message.role === 'user'
  const avatarText = isUser ? userName?.[0]?.toUpperCase() || 'U' : 'AI'
  const hasToolCalls = message.toolCalls && message.toolCalls.length > 0
  const hasMetadata = !isUser && message.metadata

  return (
    <div className={`flex gap-4 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold shrink-0 ${
          isUser ? 'bg-slate-800 text-white' : 'bg-success-500 text-white'
        }`}
      >
        {avatarText}
      </div>
      <div
        className={`max-w-[80%] py-3 px-4 rounded-2xl leading-normal whitespace-pre-wrap break-words ${
          isUser
            ? 'bg-slate-800 text-white rounded-br-sm'
            : 'bg-white text-slate-800 rounded-bl-sm shadow-sm'
        }`}
      >
        {hasToolCalls && (
          <div className="mt-3">
            <ToolCallsGroup toolCalls={message.toolCalls!} />
          </div>
        )}
        <MarkdownRenderer content={message.content} isUserMessage={isUser} />
        {hasMetadata && <MessageMetadata metadata={message.metadata!} />}
      </div>
    </div>
  )
}
