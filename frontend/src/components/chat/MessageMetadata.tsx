import type { MessageMetadata as MessageMetadataType } from '@/types/chat'
import {
  formatCost,
  formatModelName,
  formatResponseTime,
  formatTokens,
} from '@/lib/utils/metadataFormat'
import { TokenIcon, ClockIcon, CostIcon } from '@/components/ui/Icons'

interface MessageMetadataProps {
  metadata: MessageMetadataType
}

/**
 * Display message metadata (tokens, cost, response time, model)
 */
export function MessageMetadata({ metadata }: MessageMetadataProps) {
  const { inputTokens, outputTokens, model, responseTimeMs, costUsd } = metadata

  // Don't render if no meaningful metadata
  if (!inputTokens && !outputTokens && !responseTimeMs && !costUsd) {
    return null
  }

  const totalTokens = (inputTokens || 0) + (outputTokens || 0)

  return (
    <div className="flex flex-wrap gap-3 mt-3 pt-2 border-t border-slate-200 text-xs text-slate-500">
      {totalTokens > 0 && (
        <span
          className="flex items-center gap-1"
          title={`Input: ${formatTokens(inputTokens || 0)} / Output: ${formatTokens(outputTokens || 0)}`}
        >
          <TokenIcon className="opacity-70" />
          {formatTokens(totalTokens)} tokens
        </span>
      )}
      {responseTimeMs != null && responseTimeMs > 0 && (
        <span className="flex items-center gap-1">
          <ClockIcon className="opacity-70" />
          {formatResponseTime(responseTimeMs)}
        </span>
      )}
      {costUsd != null && costUsd > 0 && (
        <span className="flex items-center gap-1">
          <CostIcon className="opacity-70" />
          {formatCost(costUsd)}
        </span>
      )}
      {model && (
        <span
          className="flex items-center gap-1 font-mono bg-slate-100 px-1.5 py-0.5 rounded max-w-48 truncate"
          title={model}
        >
          {formatModelName(model)}
        </span>
      )}
    </div>
  )
}
