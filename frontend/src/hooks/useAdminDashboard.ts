import { useCallback, useEffect, useState } from 'react'
import {
  fetchDashboardSummary,
  fetchDashboardTrends,
  fetchDashboardRankings,
} from '@/lib/api/adminDashboard'
import { useErrorHandler } from './useErrorHandler'
import type {
  DashboardSummary,
  DashboardTrends,
  DashboardRankings,
  TrendMetric,
  TrendPeriod,
  RankingPeriod,
} from '@/types/adminDashboard'
import { logger } from '@/lib/logger'

interface UseAdminDashboardOptions {
  autoLoad?: boolean
}

export function useAdminDashboard(options: UseAdminDashboardOptions = {}) {
  const { autoLoad = true } = options

  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [trends, setTrends] = useState<DashboardTrends | null>(null)
  const [rankings, setRankings] = useState<DashboardRankings | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isLoadingTrends, setIsLoadingTrends] = useState(false)
  const [isLoadingRankings, setIsLoadingRankings] = useState(false)
  const [period, setPeriod] = useState<TrendPeriod>('30d')
  const [trendMetric, setTrendMetric] = useState<TrendMetric>('conversations')
  const [rankingMetric, setRankingMetric] = useState<TrendMetric>('conversations')
  const [rankingPeriod, setRankingPeriod] = useState<RankingPeriod>('all')
  const { error, handleError, clearError } = useErrorHandler()

  const loadSummary = useCallback(async () => {
    setIsLoading(true)
    clearError()
    try {
      const data = await fetchDashboardSummary()
      setSummary(data)
      logger.info('Dashboard summary loaded', { totalUsers: data.total_users })
    } catch (err) {
      handleError(err, 'Failed to load dashboard summary')
    } finally {
      setIsLoading(false)
    }
  }, [clearError, handleError])

  const loadTrends = useCallback(
    async (
      selectedPeriod: TrendPeriod = period,
      selectedMetric: TrendMetric = trendMetric,
      startDate?: string,
      endDate?: string
    ) => {
      setIsLoadingTrends(true)
      try {
        const data = await fetchDashboardTrends(selectedPeriod, selectedMetric, startDate, endDate)
        setTrends(data)
        setPeriod(selectedPeriod)
        setTrendMetric(selectedMetric)
        logger.info('Dashboard trends loaded', {
          period: selectedPeriod,
          metric: selectedMetric,
          dataPoints: data.data.length,
        })
      } catch (err) {
        handleError(err, 'Failed to load trends')
      } finally {
        setIsLoadingTrends(false)
      }
    },
    [period, trendMetric, handleError]
  )

  const loadRankings = useCallback(
    async (
      selectedMetric: TrendMetric = rankingMetric,
      limit: number = 10,
      selectedPeriod: RankingPeriod = rankingPeriod
    ) => {
      setIsLoadingRankings(true)
      try {
        const data = await fetchDashboardRankings(selectedMetric, limit, selectedPeriod)
        setRankings(data)
        setRankingMetric(selectedMetric)
        setRankingPeriod(selectedPeriod)
        logger.info('Dashboard rankings loaded', {
          metric: selectedMetric,
          count: data.rankings.length,
        })
      } catch (err) {
        handleError(err, 'Failed to load rankings')
      } finally {
        setIsLoadingRankings(false)
      }
    },
    [rankingMetric, rankingPeriod, handleError]
  )

  const changePeriod = useCallback(
    (newPeriod: TrendPeriod) => {
      void loadTrends(newPeriod, trendMetric)
    },
    [loadTrends, trendMetric]
  )

  const changeTrendMetric = useCallback(
    (newMetric: TrendMetric) => {
      void loadTrends(period, newMetric)
    },
    [loadTrends, period]
  )

  const changeRankingMetric = useCallback(
    (newMetric: TrendMetric) => {
      void loadRankings(newMetric, 10, rankingPeriod)
    },
    [loadRankings, rankingPeriod]
  )

  const refresh = useCallback(async () => {
    await Promise.all([loadSummary(), loadTrends(), loadRankings()])
  }, [loadSummary, loadTrends, loadRankings])

  useEffect(() => {
    if (autoLoad) {
      void loadSummary()
      void loadTrends()
      void loadRankings()
    }
  }, [autoLoad, loadSummary, loadTrends, loadRankings])

  return {
    summary,
    trends,
    rankings,
    isLoading,
    isLoadingTrends,
    isLoadingRankings,
    period,
    trendMetric,
    rankingMetric,
    rankingPeriod,
    error,
    clearError,
    loadSummary,
    loadTrends,
    loadRankings,
    changePeriod,
    changeTrendMetric,
    changeRankingMetric,
    refresh,
  }
}
