import type { TrendPeriod } from '@/types/adminDashboard'

interface PeriodFilterProps {
  value: TrendPeriod
  onChange: (period: TrendPeriod) => void
  disabled?: boolean
}

const periodOptions: { value: TrendPeriod; label: string }[] = [
  { value: '7d', label: '7日間' },
  { value: '30d', label: '30日間' },
  { value: '90d', label: '90日間' },
]

export function PeriodFilter({ value, onChange, disabled = false }: PeriodFilterProps) {
  return (
    <div className="flex gap-2">
      {periodOptions.map(option => (
        <button
          key={option.value}
          onClick={() => onChange(option.value)}
          disabled={disabled}
          className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
            value === option.value
              ? 'bg-blue-500 text-white'
              : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
          } disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {option.label}
        </button>
      ))}
    </div>
  )
}
