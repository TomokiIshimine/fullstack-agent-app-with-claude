import { useEffect, useRef } from 'react'
import type { Message } from '@/types/chat'
import type { StreamingToolCall } from '@/types/tool'
import type { RetryStatus } from '@/types/errors'
import { MessageItem } from './MessageItem'
import { StreamingMessage } from './StreamingMessage'
import { RetryIndicator } from './RetryIndicator'

interface MessageListProps {
  messages: Message[]
  isStreaming: boolean
  streamingContent: string
  streamingToolCalls?: StreamingToolCall[]
  retryStatus?: RetryStatus | null
  userName?: string
}

export function MessageList({
  messages,
  isStreaming,
  streamingContent,
  streamingToolCalls = [],
  retryStatus,
  userName,
}: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent, streamingToolCalls, retryStatus])

  return (
    <div className="max-w-3xl mx-auto flex flex-col gap-6">
      {messages.map(message => (
        <MessageItem key={message.id} message={message} userName={userName} />
      ))}
      {isStreaming && (
        <StreamingMessage content={streamingContent} toolCalls={streamingToolCalls} />
      )}
      {retryStatus?.isRetrying && (
        <div className="px-4 py-2">
          <RetryIndicator status={retryStatus} />
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  )
}
