import { useEffect, useRef } from 'react'
import type { Message } from '@/types/chat'
import { MessageItem } from './MessageItem'
import { StreamingMessage } from './StreamingMessage'

interface MessageListProps {
  messages: Message[]
  isStreaming: boolean
  streamingContent: string
  userName?: string
}

export function MessageList({
  messages,
  isStreaming,
  streamingContent,
  userName,
}: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent])

  return (
    <div className="message-list">
      {messages.map((message) => (
        <MessageItem key={message.id} message={message} userName={userName} />
      ))}
      {isStreaming && <StreamingMessage content={streamingContent} />}
      <div ref={bottomRef} />
    </div>
  )
}
