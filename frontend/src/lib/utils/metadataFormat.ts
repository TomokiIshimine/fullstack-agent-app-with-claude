/**
 * Formatting utilities for message metadata display
 */

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
