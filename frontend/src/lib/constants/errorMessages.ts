import type { LLMErrorType } from '@/types/errors'

/**
 * Detailed error messages with recovery instructions.
 * Used in ChatError component for user-facing error display.
 */
export const ERROR_MESSAGES_DETAILED: Record<LLMErrorType | string, string> = {
  rate_limit: 'リクエスト制限に達しました。しばらく待ってから再度お試しください。',
  connection: 'AIサービスへの接続に失敗しました。ネットワーク接続を確認してください。',
  server_error: 'サーバーエラーが発生しました。しばらく待ってから再度お試しください。',
  context_length: 'メッセージが長すぎます。会話履歴を削減するか、短いメッセージをお試しください。',
  stream_error: 'AI応答のストリーミング中にエラーが発生しました。再度お試しください。',
  provider_error: 'AIサービスの設定に問題があります。管理者にお問い合わせください。',
  conversation_error: '会話の処理中にエラーが発生しました。',
  unknown: '予期しないエラーが発生しました。再度お試しください。',
}

/**
 * Brief error messages for status indicators.
 * Used in RetryIndicator component for compact display.
 */
export const ERROR_MESSAGES_BRIEF: Record<string, string> = {
  rate_limit: 'リクエスト制限に達しました',
  connection: '接続エラーが発生しました',
  server_error: 'サーバーエラーが発生しました',
  stream_error: '応答が中断されました',
  context_length: 'メッセージが長すぎます',
  provider_error: 'AIサービスエラー',
  conversation_error: '会話処理エラー',
  unknown: 'エラーが発生しました',
}

/**
 * Get detailed error message for an error type.
 * Falls back to 'unknown' message if type is not found.
 */
export function getDetailedErrorMessage(errorType: LLMErrorType | string | undefined): string {
  return ERROR_MESSAGES_DETAILED[errorType || 'unknown'] || ERROR_MESSAGES_DETAILED.unknown
}

/**
 * Get brief error message for an error type.
 * Falls back to 'unknown' message if type is not found.
 */
export function getBriefErrorMessage(errorType: string | undefined): string {
  return ERROR_MESSAGES_BRIEF[errorType || 'unknown'] || ERROR_MESSAGES_BRIEF.unknown
}
