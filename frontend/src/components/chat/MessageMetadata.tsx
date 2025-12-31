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
    <div className="message-metadata">
      {totalTokens > 0 && (
        <span
          className="message-metadata__item"
          title={`Input: ${formatTokens(inputTokens || 0)} / Output: ${formatTokens(outputTokens || 0)}`}
        >
          <TokenIcon className="message-metadata__icon" />
          {formatTokens(totalTokens)} tokens
        </span>
      )}
      {responseTimeMs != null && responseTimeMs > 0 && (
        <span className="message-metadata__item">
          <ClockIcon className="message-metadata__icon" />
          {formatResponseTime(responseTimeMs)}
        </span>
      )}
      {costUsd != null && costUsd > 0 && (
        <span className="message-metadata__item">
          <CostIcon className="message-metadata__icon" />
          {formatCost(costUsd)}
        </span>
      )}
      {model && (
        <span className="message-metadata__item message-metadata__item--model" title={model}>
          {formatModelName(model)}
        </span>
      )}
    </div>
  )
}
