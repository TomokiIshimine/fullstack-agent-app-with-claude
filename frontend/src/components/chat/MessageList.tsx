import { useEffect, useRef, useCallback } from 'react'
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
  const scrollRequestRef = useRef<number | null>(null)

  const scrollToBottom = useCallback((smooth: boolean) => {
    bottomRef.current?.scrollIntoView({ behavior: smooth ? 'smooth' : 'auto' })
  }, [])

  // Scroll on new messages (smooth scroll)
  useEffect(() => {
    scrollToBottom(true)
  }, [messages, scrollToBottom])

  // Scroll during streaming (throttled with requestAnimationFrame, instant scroll)
  useEffect(() => {
    if (!isStreaming) {
      return
    }

    // Cancel any pending scroll request
    if (scrollRequestRef.current !== null) {
      cancelAnimationFrame(scrollRequestRef.current)
    }

    // Schedule scroll on next animation frame to avoid excessive updates
    scrollRequestRef.current = requestAnimationFrame(() => {
      scrollToBottom(false)
      scrollRequestRef.current = null
    })

    return () => {
      if (scrollRequestRef.current !== null) {
        cancelAnimationFrame(scrollRequestRef.current)
        scrollRequestRef.current = null
      }
    }
  }, [isStreaming, streamingContent, streamingToolCalls, scrollToBottom])

  // Scroll when retry status changes
  useEffect(() => {
    if (retryStatus?.isRetrying) {
      scrollToBottom(true)
    }
  }, [retryStatus, scrollToBottom])

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
