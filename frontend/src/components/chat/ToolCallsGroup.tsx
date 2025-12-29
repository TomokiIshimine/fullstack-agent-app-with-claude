import { useState } from 'react'

import type { ToolCall, StreamingToolCall, ToolCallStatus } from '@/types/tool'

import { ToolCallItem } from './ToolCallItem'

interface ToolCallsGroupProps {
  toolCalls: (ToolCall | StreamingToolCall)[]
}

function getGroupStatus(toolCalls: (ToolCall | StreamingToolCall)[]): ToolCallStatus {
  // If any tool is pending, the group is pending
  if (toolCalls.some(tc => tc.status === 'pending')) {
    return 'pending'
  }
  // If any tool has an error, the group shows error
  if (toolCalls.some(tc => tc.status === 'error')) {
    return 'error'
  }
  // All tools succeeded
  return 'success'
}

function getGroupStatusIcon(status: ToolCallStatus): string {
  switch (status) {
    case 'pending':
      return '⏳'
    case 'success':
      return '✅'
    case 'error':
      return '❌'
  }
}

export function ToolCallsGroup({ toolCalls }: ToolCallsGroupProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  if (toolCalls.length === 0) {
    return null
  }

  // If only one tool, render it directly without grouping
  if (toolCalls.length === 1) {
    return <ToolCallItem toolCall={toolCalls[0]} />
  }

  const groupStatus = getGroupStatus(toolCalls)
  const statusIcon = getGroupStatusIcon(groupStatus)

  return (
    <div className="tool-calls-group">
      <button
        type="button"
        className="tool-calls-group__header"
        onClick={() => setIsExpanded(!isExpanded)}
        aria-expanded={isExpanded}
      >
        <span className="tool-calls-group__status">{statusIcon}</span>
        <span className="tool-calls-group__text">{toolCalls.length}個のツールを使用</span>
        <span
          className={`tool-calls-group__chevron ${isExpanded ? 'tool-calls-group__chevron--open' : ''}`}
        >
          ▶
        </span>
      </button>
      {isExpanded && (
        <div className="tool-calls-group__content">
          {toolCalls.map(tc => (
            <ToolCallItem key={'id' in tc ? tc.id : tc.toolCallId} toolCall={tc} />
          ))}
        </div>
      )}
    </div>
  )
}
