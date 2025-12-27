import { useState } from 'react'

import type { ToolCall } from '@/types/tool'

import { ToolCallExpander } from './ToolCallExpander'

interface ToolCallItemProps {
  toolCall: ToolCall | StreamingToolCallDisplay
}

/** Streaming tool call compatible interface */
interface StreamingToolCallDisplay {
  toolCallId: string
  toolName: string
  input: Record<string, unknown>
  output?: string
  error?: string
  status: 'pending' | 'success' | 'error'
}

export function ToolCallItem({ toolCall }: ToolCallItemProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const formatInput = (input: Record<string, unknown>): string => {
    try {
      return JSON.stringify(input, null, 2)
    } catch {
      return String(input)
    }
  }

  return (
    <div className="tool-call-item">
      <ToolCallExpander
        toolName={toolCall.toolName}
        status={toolCall.status}
        isExpanded={isExpanded}
        onToggle={() => setIsExpanded(!isExpanded)}
      />
      {isExpanded && (
        <div className="tool-call-item__details">
          <div className="tool-call-item__section">
            <div className="tool-call-item__label">Input:</div>
            <pre className="tool-call-item__code">{formatInput(toolCall.input)}</pre>
          </div>
          {toolCall.output && (
            <div className="tool-call-item__section">
              <div className="tool-call-item__label">Output:</div>
              <pre className="tool-call-item__code">{toolCall.output}</pre>
            </div>
          )}
          {toolCall.error && (
            <div className="tool-call-item__section tool-call-item__section--error">
              <div className="tool-call-item__label">Error:</div>
              <pre className="tool-call-item__code tool-call-item__code--error">
                {toolCall.error}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
