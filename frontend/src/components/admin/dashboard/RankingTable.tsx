import type { UserRankingItem, TrendMetric } from '@/types/adminDashboard'
import { Card } from '@/components/ui'
import { cn } from '@/lib/utils/cn'

interface RankingTableProps {
  rankings: UserRankingItem[]
  metric: TrendMetric
  title: string
  isLoading?: boolean
}

const metricLabels: Record<TrendMetric, string> = {
  conversations: '会話数',
  messages: 'メッセージ数',
  tokens: 'トークン数',
}

export function RankingTable({ rankings, metric, title, isLoading = false }: RankingTableProps) {
  if (isLoading) {
    return (
      <Card>
        <h3 className="text-lg font-semibold text-slate-800 mb-4">{title}</h3>
        <div className="h-64 flex items-center justify-center">
          <div className="animate-pulse text-slate-400">Loading...</div>
        </div>
      </Card>
    )
  }

  if (rankings.length === 0) {
    return (
      <Card>
        <h3 className="text-lg font-semibold text-slate-800 mb-4">{title}</h3>
        <p className="text-slate-500 text-center py-8">データがありません</p>
      </Card>
    )
  }

  return (
    <Card>
      <h3 className="text-lg font-semibold text-slate-800 mb-4">{title}</h3>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-200">
              <th className="pb-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                順位
              </th>
              <th className="pb-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                ユーザー
              </th>
              <th className="pb-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">
                {metricLabels[metric]}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rankings.map((item, index) => (
              <tr key={item.user_id} className="hover:bg-slate-50 transition-colors">
                <td className="py-3 text-sm">
                  <span
                    className={cn(
                      'inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-semibold',
                      index === 0 && 'bg-yellow-100 text-yellow-800',
                      index === 1 && 'bg-slate-200 text-slate-700',
                      index === 2 && 'bg-amber-100 text-amber-800',
                      index >= 3 && 'bg-slate-100 text-slate-600'
                    )}
                  >
                    {index + 1}
                  </span>
                </td>
                <td className="py-3">
                  <div className="text-sm font-medium text-slate-900">
                    {item.name || item.email}
                  </div>
                  {item.name && <div className="text-xs text-slate-500">{item.email}</div>}
                </td>
                <td className="py-3 text-right text-sm font-semibold text-slate-900">
                  {item.value.toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  )
}
