import { useEffect, useRef } from 'react'
import type { Message } from '@/types/chat'
import type { StreamingToolCall } from '@/types/tool'
import { MessageItem } from './MessageItem'
import { StreamingMessage } from './StreamingMessage'

interface MessageListProps {
  messages: Message[]
  isStreaming: boolean
  streamingContent: string
  streamingToolCalls?: StreamingToolCall[]
  userName?: string
}

export function MessageList({
  messages,
  isStreaming,
  streamingContent,
  streamingToolCalls = [],
  userName,
}: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent, streamingToolCalls])

  return (
    <div className="message-list">
      {messages.map(message => (
        <MessageItem key={message.id} message={message} userName={userName} />
      ))}
      {isStreaming && (
        <StreamingMessage content={streamingContent} toolCalls={streamingToolCalls} />
      )}
      <div ref={bottomRef} />
    </div>
  )
}
