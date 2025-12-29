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
      className="tool-call-expander"
      onClick={onToggle}
      aria-expanded={isExpanded}
    >
      <span className="tool-call-expander__status">{getStatusIcon(status)}</span>
      <span className="tool-call-expander__name">{toolName}</span>
      <span
        className={`tool-call-expander__chevron ${isExpanded ? 'tool-call-expander__chevron--open' : ''}`}
      >
        ▶
      </span>
    </button>
  )
}
