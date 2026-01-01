import { useState } from 'react'

import type { ToolCall, StreamingToolCall } from '@/types/tool'

import { ToolCallExpander } from './ToolCallExpander'

interface ToolCallItemProps {
  toolCall: ToolCall | StreamingToolCall
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
    <div className="my-2 border border-slate-200 rounded-lg bg-slate-50 overflow-hidden">
      <ToolCallExpander
        toolName={toolCall.toolName}
        status={toolCall.status}
        isExpanded={isExpanded}
        onToggle={() => setIsExpanded(!isExpanded)}
      />
      {isExpanded && (
        <div className="p-3 border-t border-slate-200 bg-white">
          <div className="mb-3">
            <div className="text-xs font-semibold text-slate-500 mb-1 uppercase tracking-wider">
              Input:
            </div>
            <pre className="m-0 p-2 bg-slate-100 rounded-md text-[13px] font-mono whitespace-pre-wrap break-words text-slate-700">
              {formatInput(toolCall.input)}
            </pre>
          </div>
          {toolCall.output && (
            <div className="mb-3">
              <div className="text-xs font-semibold text-slate-500 mb-1 uppercase tracking-wider">
                Output:
              </div>
              <pre className="m-0 p-2 bg-slate-100 rounded-md text-[13px] font-mono whitespace-pre-wrap break-words text-slate-700">
                {toolCall.output}
              </pre>
            </div>
          )}
          {toolCall.error && (
            <div className="mb-3 last:mb-0">
              <div className="text-xs font-semibold text-danger-600 mb-1 uppercase tracking-wider">
                Error:
              </div>
              <pre className="m-0 p-2 bg-danger-50 rounded-md text-[13px] font-mono whitespace-pre-wrap break-words text-danger-600">
                {toolCall.error}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
