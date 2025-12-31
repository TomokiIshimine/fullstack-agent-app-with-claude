/**
 * Admin Dashboard types
 */

export interface TokenStats {
  input: number
  output: number
}

export interface DashboardSummary {
  total_users: number
  active_users: number
  total_conversations: number
  today_conversations: number
  total_messages: number
  total_tokens: TokenStats
  total_cost_usd: number
}

export interface TrendDataPoint {
  date: string
  value: number
}

export interface DashboardTrends {
  period: string
  metric: string
  data: TrendDataPoint[]
}

export interface UserRankingItem {
  user_id: number
  email: string
  name: string | null
  value: number
}

export interface DashboardRankings {
  metric: string
  rankings: UserRankingItem[]
}

export type TrendMetric = 'conversations' | 'messages' | 'tokens'
export type TrendPeriod = '7d' | '30d' | '90d' | 'custom'
export type RankingPeriod = '7d' | '30d' | '90d' | 'all'
