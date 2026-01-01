import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import type { TrendDataPoint } from '@/types/adminDashboard'
import { Card } from '@/components/ui'

interface TrendChartProps {
  data: TrendDataPoint[]
  title: string
  isLoading?: boolean
  color?: string
}

export function TrendChart({ data, title, isLoading = false, color = '#3b82f6' }: TrendChartProps) {
  // Format date for display (MM/DD)
  const formattedData = data.map(item => ({
    ...item,
    displayDate: new Date(item.date).toLocaleDateString('ja-JP', {
      month: 'numeric',
      day: 'numeric',
    }),
  }))

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

  return (
    <Card>
      <h3 className="text-lg font-semibold text-slate-800 mb-4">{title}</h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={formattedData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200" />
            <XAxis
              dataKey="displayDate"
              tick={{ fontSize: 12 }}
              tickLine={false}
              axisLine={false}
              className="text-slate-500"
            />
            <YAxis
              tick={{ fontSize: 12 }}
              tickLine={false}
              axisLine={false}
              className="text-slate-500"
              tickFormatter={value => value.toLocaleString()}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'white',
                borderRadius: '8px',
              }}
              wrapperClassName="shadow-md border border-slate-200 rounded-lg"
              formatter={(value: number) => [value.toLocaleString(), '']}
              labelFormatter={(label: string) => label}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke={color}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: color }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  )
}
