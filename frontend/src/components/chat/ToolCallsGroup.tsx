import { useState } from 'react'

import type { ToolCall, StreamingToolCall, ToolCallStatus } from '@/types/tool'

import { ToolCallItem } from './ToolCallItem'

interface ToolCallsGroupProps {
  toolCalls: (ToolCall | StreamingToolCall)[]
}

function getGroupStatus(toolCalls: (ToolCall | StreamingToolCall)[]): ToolCallStatus {
  // Prioritize error status so users immediately see failures
  if (toolCalls.some(tc => tc.status === 'error')) {
    return 'error'
  }
  // If any tool is still pending, show pending
  if (toolCalls.some(tc => tc.status === 'pending')) {
    return 'pending'
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
    <div className="my-2 border border-slate-200 rounded-lg bg-slate-50 overflow-hidden">
      <button
        type="button"
        className="flex items-center gap-2 w-full py-2 px-3 bg-transparent border-none cursor-pointer text-sm text-slate-600 text-left transition-colors duration-200 hover:bg-slate-200"
        onClick={() => setIsExpanded(!isExpanded)}
        aria-expanded={isExpanded}
      >
        <span className="text-sm">{statusIcon}</span>
        <span className="flex-1 font-medium">{toolCalls.length}個のツールを使用</span>
        <span
          className={`text-[10px] text-slate-400 transition-transform duration-200 ${isExpanded ? 'rotate-90' : ''}`}
        >
          ▶
        </span>
      </button>
      {isExpanded && (
        <div className="p-2 border-t border-slate-200 bg-white space-y-1">
          {toolCalls.map(tc => (
            <ToolCallItem key={'id' in tc ? tc.id : tc.toolCallId} toolCall={tc} />
          ))}
        </div>
      )}
    </div>
  )
}
