/**
 * Formatting and transformation utilities for message metadata
 */

import type { MessageMetadata } from '@/types/chat'

/**
 * Raw metadata fields from API (snake_case)
 */
export interface RawMetadataFields {
  input_tokens?: number | null
  output_tokens?: number | null
  model?: string | null
  response_time_ms?: number | null
  cost_usd?: number | null
}

/**
 * Build MessageMetadata from raw API fields.
 * Returns undefined if no meaningful metadata is present.
 *
 * @param data - Raw metadata fields from API (snake_case)
 * @returns MessageMetadata object or undefined
 *
 * @example
 * const metadata = buildMetadata({
 *   input_tokens: 100,
 *   output_tokens: 200,
 *   model: 'claude-sonnet-4-5-20250929',
 *   response_time_ms: 1500,
 *   cost_usd: 0.002
 * })
 */
export function buildMetadata(data: RawMetadataFields): MessageMetadata | undefined {
  const hasMetadata =
    data.input_tokens != null ||
    data.output_tokens != null ||
    data.model != null ||
    data.response_time_ms != null ||
    data.cost_usd != null

  if (!hasMetadata) {
    return undefined
  }

  return {
    inputTokens: data.input_tokens ?? undefined,
    outputTokens: data.output_tokens ?? undefined,
    model: data.model ?? undefined,
    responseTimeMs: data.response_time_ms ?? undefined,
    costUsd: data.cost_usd ?? undefined,
  }
}

/**
 * Threshold constants for cost formatting precision
 */
const COST_THRESHOLD_HIGH_PRECISION = 0.0001
const COST_THRESHOLD_MEDIUM_PRECISION = 0.01

/**
 * Threshold constant for response time formatting
 */
const RESPONSE_TIME_THRESHOLD_MS = 1000

/**
 * Format cost in USD with appropriate precision based on amount
 *
 * @param cost - Cost in USD
 * @returns Formatted cost string (e.g., "$0.000001", "$0.0012", "$1.50")
 *
 * @example
 * formatCost(0.000001) // "$0.000001"
 * formatCost(0.0012)   // "$0.0012"
 * formatCost(1.5)      // "$1.50"
 */
export function formatCost(cost: number): string {
  if (cost < COST_THRESHOLD_HIGH_PRECISION) {
    return `$${cost.toFixed(6)}`
  }
  if (cost < COST_THRESHOLD_MEDIUM_PRECISION) {
    return `$${cost.toFixed(4)}`
  }
  return `$${cost.toFixed(2)}`
}

/**
 * Format response time in human-readable format
 *
 * @param ms - Response time in milliseconds
 * @returns Formatted time string (e.g., "500ms", "1.2s")
 *
 * @example
 * formatResponseTime(500)  // "500ms"
 * formatResponseTime(1500) // "1.5s"
 */
export function formatResponseTime(ms: number): string {
  if (ms < RESPONSE_TIME_THRESHOLD_MS) {
    return `${ms}ms`
  }
  return `${(ms / 1000).toFixed(1)}s`
}

/**
 * Format token count with locale-specific thousands separators
 *
 * @param count - Token count
 * @returns Formatted token count string (e.g., "1,234")
 *
 * @example
 * formatTokens(1234)    // "1,234" (in en-US locale)
 * formatTokens(1000000) // "1,000,000" (in en-US locale)
 */
export function formatTokens(count: number): string {
  return count.toLocaleString()
}

/**
 * Format model name for display by removing date suffix and extracting the last segment
 *
 * @param model - Full model name (e.g., "anthropic/claude-sonnet-4-5-20250929")
 * @returns Simplified model name (e.g., "claude-sonnet-4-5")
 *
 * @example
 * formatModelName("anthropic/claude-sonnet-4-5-20250929") // "claude-sonnet-4-5"
 * formatModelName("claude-sonnet-4-5-20250929")           // "claude-sonnet-4-5"
 * formatModelName("gpt-4")                              // "gpt-4"
 */
export function formatModelName(model: string): string {
  const lastSegment = model.split('/').pop() ?? model
  return lastSegment.replace(/-\d{8}$/, '')
}
