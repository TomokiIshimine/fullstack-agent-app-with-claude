import type { MessageMetadata as MessageMetadataType } from '@/types/chat'

interface MessageMetadataProps {
  metadata: MessageMetadataType
}

/**
 * Format cost in USD with appropriate precision
 */
function formatCost(cost: number): string {
  if (cost < 0.0001) {
    return `$${cost.toFixed(6)}`
  }
  if (cost < 0.01) {
    return `$${cost.toFixed(4)}`
  }
  return `$${cost.toFixed(2)}`
}

/**
 * Format response time in human-readable format
 */
function formatResponseTime(ms: number): string {
  if (ms < 1000) {
    return `${ms}ms`
  }
  return `${(ms / 1000).toFixed(1)}s`
}

/**
 * Format token count with commas for readability
 */
function formatTokens(count: number): string {
  return count.toLocaleString()
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
        <span className="message-metadata__item" title={`Input: ${formatTokens(inputTokens || 0)} / Output: ${formatTokens(outputTokens || 0)}`}>
          <svg className="message-metadata__icon" viewBox="0 0 16 16" fill="currentColor" width="12" height="12">
            <path d="M8 0a8 8 0 1 0 0 16A8 8 0 0 0 8 0zm3.5 7.5a.5.5 0 0 1 0 1H8a.5.5 0 0 1-.5-.5V4a.5.5 0 0 1 1 0v3h3z"/>
          </svg>
          {formatTokens(totalTokens)} tokens
        </span>
      )}
      {responseTimeMs != null && responseTimeMs > 0 && (
        <span className="message-metadata__item">
          <svg className="message-metadata__icon" viewBox="0 0 16 16" fill="currentColor" width="12" height="12">
            <path d="M8 3.5a.5.5 0 0 0-1 0V9a.5.5 0 0 0 .252.434l3.5 2a.5.5 0 0 0 .496-.868L8 8.71V3.5z"/>
            <path d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16zm7-8A7 7 0 1 1 1 8a7 7 0 0 1 14 0z"/>
          </svg>
          {formatResponseTime(responseTimeMs)}
        </span>
      )}
      {costUsd != null && costUsd > 0 && (
        <span className="message-metadata__item">
          <svg className="message-metadata__icon" viewBox="0 0 16 16" fill="currentColor" width="12" height="12">
            <path d="M4 10.781c.148 1.667 1.513 2.85 3.591 3.003V15h1.043v-1.216c2.27-.179 3.678-1.438 3.678-3.3 0-1.59-.947-2.51-2.956-3.028l-.722-.187V3.467c1.122.11 1.879.714 2.07 1.616h1.47c-.166-1.6-1.54-2.748-3.54-2.875V1H7.591v1.233c-1.939.23-3.27 1.472-3.27 3.156 0 1.454.966 2.483 2.661 2.917l.61.162v4.031c-1.149-.17-1.94-.8-2.131-1.718H4zm3.391-3.836c-1.043-.263-1.6-.825-1.6-1.616 0-.944.704-1.641 1.8-1.828v3.495l-.2-.05zm1.591 1.872c1.287.323 1.852.859 1.852 1.769 0 1.097-.826 1.828-2.2 1.939V8.73l.348.086z"/>
          </svg>
          {formatCost(costUsd)}
        </span>
      )}
      {model && (
        <span className="message-metadata__item message-metadata__item--model" title={model}>
          {model.split('/').pop()?.replace(/-\d{8}$/, '') || model}
        </span>
      )}
    </div>
  )
}
