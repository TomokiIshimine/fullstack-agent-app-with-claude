import type { StreamingToolCall } from '@/types/tool'
import { ToolCallItem } from './ToolCallItem'

interface StreamingMessageProps {
  content: string
  toolCalls?: StreamingToolCall[]
}

export function StreamingMessage({ content, toolCalls = [] }: StreamingMessageProps) {
  const hasToolCalls = toolCalls.length > 0
  const hasContent = content.length > 0

  // Show loading dots only when no tool calls and no content
  if (!hasToolCalls && !hasContent) {
    return (
      <div className="streaming-message">
        <div className="message-item__avatar" style={{ backgroundColor: '#10b981' }}>
          AI
        </div>
        <div className="streaming-message__content">
          <div className="loading-dots">
            <span className="loading-dots__dot" />
            <span className="loading-dots__dot" />
            <span className="loading-dots__dot" />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="streaming-message">
      <div className="message-item__avatar" style={{ backgroundColor: '#10b981' }}>
        AI
      </div>
      <div className="streaming-message__content">
        {hasToolCalls && (
          <div className="streaming-message__tool-calls">
            {toolCalls.map(tc => (
              <ToolCallItem key={tc.toolCallId} toolCall={tc} />
            ))}
          </div>
        )}
        {hasContent && (
          <>
            {content}
            <span className="streaming-message__cursor" />
          </>
        )}
        {!hasContent && hasToolCalls && (
          <div className="loading-dots">
            <span className="loading-dots__dot" />
            <span className="loading-dots__dot" />
            <span className="loading-dots__dot" />
          </div>
        )}
      </div>
    </div>
  )
}
