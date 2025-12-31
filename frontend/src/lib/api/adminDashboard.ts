import type {
  DashboardSummary,
  DashboardTrends,
  DashboardRankings,
  TrendMetric,
  TrendPeriod,
  RankingPeriod,
} from '@/types/adminDashboard'
import { fetchWithLogging, parseJson, buildApiError } from './client'

const API_BASE_URL = '/api/admin/dashboard'

/**
 * Fetch dashboard summary statistics
 */
export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  const response = await fetchWithLogging(`${API_BASE_URL}/summary`, {
    method: 'GET',
  })
  const json = await parseJson(response)
  if (!response.ok) {
    throw buildApiError(response, json)
  }
  return json as DashboardSummary
}

/**
 * Fetch dashboard trend data
 */
export async function fetchDashboardTrends(
  period: TrendPeriod = '30d',
  metric: TrendMetric = 'conversations',
  startDate?: string,
  endDate?: string
): Promise<DashboardTrends> {
  const params = new URLSearchParams({
    period,
    metric,
  })
  if (period === 'custom' && startDate && endDate) {
    params.set('start_date', startDate)
    params.set('end_date', endDate)
  }

  const response = await fetchWithLogging(`${API_BASE_URL}/trends?${params}`, {
    method: 'GET',
  })
  const json = await parseJson(response)
  if (!response.ok) {
    throw buildApiError(response, json)
  }
  return json as DashboardTrends
}

/**
 * Fetch user rankings
 */
export async function fetchDashboardRankings(
  metric: TrendMetric = 'conversations',
  limit: number = 10,
  period: RankingPeriod = 'all'
): Promise<DashboardRankings> {
  const params = new URLSearchParams({
    metric,
    limit: limit.toString(),
    period,
  })

  const response = await fetchWithLogging(`${API_BASE_URL}/rankings?${params}`, {
    method: 'GET',
  })
  const json = await parseJson(response)
  if (!response.ok) {
    throw buildApiError(response, json)
  }
  return json as DashboardRankings
}
