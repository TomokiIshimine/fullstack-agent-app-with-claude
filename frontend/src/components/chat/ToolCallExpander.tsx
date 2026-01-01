import type { ToolCallStatus } from '@/types/tool'

interface ToolCallExpanderProps {
  toolName: string
  status: ToolCallStatus
  isExpanded: boolean
  onToggle: () => void
}

function getStatusIcon(status: ToolCallStatus): string {
  switch (status) {
    case 'pending':
      return '⏳'
    case 'success':
      return '✅'
    case 'error':
      return '❌'
  }
}

export function ToolCallExpander({
  toolName,
  status,
  isExpanded,
  onToggle,
}: ToolCallExpanderProps) {
  return (
    <button
      type="button"
      className="flex items-center gap-2 w-full py-2 px-3 bg-transparent border-none cursor-pointer text-sm text-slate-600 text-left transition-colors duration-200 hover:bg-slate-200"
      onClick={onToggle}
      aria-expanded={isExpanded}
    >
      <span className="text-sm">{getStatusIcon(status)}</span>
      <span className="flex-1 font-medium font-mono">{toolName}</span>
      <span
        className={`text-[10px] text-slate-400 transition-transform duration-200 ${isExpanded ? 'rotate-90' : ''}`}
      >
        ▶
      </span>
    </button>
  )
}
