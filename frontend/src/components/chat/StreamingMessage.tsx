import type { StreamingToolCall } from '@/types/tool'
import { ToolCallsGroup } from './ToolCallsGroup'
import { MarkdownRenderer } from './MarkdownRenderer'

interface StreamingMessageProps {
  content: string
  toolCalls?: StreamingToolCall[]
}

function LoadingDots() {
  return (
    <div className="flex gap-1">
      <span className="w-2 h-2 bg-slate-400 rounded-full animate-[loadingDot_1.4s_ease-in-out_infinite_-0.32s]" />
      <span className="w-2 h-2 bg-slate-400 rounded-full animate-[loadingDot_1.4s_ease-in-out_infinite_-0.16s]" />
      <span className="w-2 h-2 bg-slate-400 rounded-full animate-[loadingDot_1.4s_ease-in-out_infinite]" />
    </div>
  )
}

export function StreamingMessage({ content, toolCalls = [] }: StreamingMessageProps) {
  const hasToolCalls = toolCalls.length > 0
  const hasContent = content.length > 0

  // Show loading dots only when no tool calls and no content
  if (!hasToolCalls && !hasContent) {
    return (
      <div className="flex gap-4">
        <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold shrink-0 bg-success-500 text-white">
          AI
        </div>
        <div className="max-w-[80%] py-3 px-4 rounded-2xl rounded-bl-sm bg-white text-slate-800 shadow-sm leading-normal whitespace-pre-wrap break-words">
          <LoadingDots />
        </div>
      </div>
    )
  }

  return (
    <div className="flex gap-4">
      <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold shrink-0 bg-success-500 text-white">
        AI
      </div>
      <div className="max-w-[80%] py-3 px-4 rounded-2xl rounded-bl-sm bg-white text-slate-800 shadow-sm leading-normal whitespace-pre-wrap break-words">
        {hasToolCalls && (
          <div className="mb-3">
            <ToolCallsGroup toolCalls={toolCalls} />
          </div>
        )}
        {hasContent && (
          <>
            <MarkdownRenderer content={content} />
            <span className="inline-block w-0.5 h-[1em] bg-primary-500 ml-0.5 animate-[blink_1s_infinite]" />
          </>
        )}
        {!hasContent && hasToolCalls && <LoadingDots />}
      </div>
    </div>
  )
}
