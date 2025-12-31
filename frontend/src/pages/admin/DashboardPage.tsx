import { Alert } from '@/components/ui'
import { StatCard, TrendChart, PeriodFilter, RankingTable } from '@/components/admin/dashboard'
import { useAdminDashboard } from '@/hooks/useAdminDashboard'

export function DashboardPage() {
  const {
    summary,
    trends,
    rankings,
    isLoading,
    isLoadingTrends,
    isLoadingRankings,
    period,
    error,
    clearError,
    changePeriod,
    refresh,
  } = useAdminDashboard()

  const formatCost = (cost: number) => {
    return `$${cost.toFixed(2)}`
  }

  const formatTokens = (input: number, output: number) => {
    const total = input + output
    if (total >= 1000000) {
      return `${(total / 1000000).toFixed(1)}M`
    }
    if (total >= 1000) {
      return `${(total / 1000).toFixed(1)}K`
    }
    return total.toLocaleString()
  }

  return (
    <div className="bg-slate-100 min-h-screen">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-2xl font-bold text-slate-800">ダッシュボード</h1>
          <button
            onClick={() => void refresh()}
            className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-200 rounded-lg transition-colors"
          >
            更新
          </button>
        </div>

        {error && (
          <div className="mb-6">
            <Alert
              variant="error"
              onRetry={() => {
                clearError()
                void refresh()
              }}
              onDismiss={clearError}
            >
              {error}
            </Alert>
          </div>
        )}

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-slate-600 text-lg">読み込み中...</div>
          </div>
        ) : (
          <div className="space-y-8">
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <StatCard
                title="総ユーザー数"
                value={summary?.total_users ?? 0}
                subtitle={`アクティブ: ${summary?.active_users ?? 0}人`}
              />
              <StatCard
                title="総会話数"
                value={summary?.total_conversations ?? 0}
                subtitle={`今日: ${summary?.today_conversations ?? 0}件`}
              />
              <StatCard title="総メッセージ数" value={summary?.total_messages ?? 0} />
              <StatCard
                title="トークン消費量"
                value={
                  summary
                    ? formatTokens(summary.total_tokens.input, summary.total_tokens.output)
                    : '0'
                }
                subtitle={summary ? formatCost(summary.total_cost_usd) : '$0.00'}
              />
            </div>

            {/* Period Filter */}
            <div className="flex justify-end">
              <PeriodFilter value={period} onChange={changePeriod} disabled={isLoadingTrends} />
            </div>

            {/* Trend Chart */}
            <TrendChart
              data={trends?.data ?? []}
              title="会話数の推移"
              isLoading={isLoadingTrends}
              color="#3b82f6"
            />

            {/* Rankings */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <RankingTable
                rankings={rankings?.rankings ?? []}
                metric="conversations"
                title="会話数ランキング TOP10"
                isLoading={isLoadingRankings}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
