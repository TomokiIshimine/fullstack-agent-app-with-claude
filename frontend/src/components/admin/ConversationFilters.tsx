import { useState, useEffect } from 'react'
import { Button } from '@/components/ui'
import type { AdminConversationFilters } from '@/types/adminConversation'
import type { UserResponse } from '@/types/user'

interface ConversationFiltersProps {
  users: UserResponse[]
  filters: AdminConversationFilters
  onApplyFilters: (filters: AdminConversationFilters) => void
  onClearFilters: () => void
}

export function ConversationFilters({
  users,
  filters,
  onApplyFilters,
  onClearFilters,
}: ConversationFiltersProps) {
  const [userId, setUserId] = useState<string>(filters.userId?.toString() || '')
  const [startDate, setStartDate] = useState(filters.startDate || '')
  const [endDate, setEndDate] = useState(filters.endDate || '')

  useEffect(() => {
    setUserId(filters.userId?.toString() || '')
    setStartDate(filters.startDate || '')
    setEndDate(filters.endDate || '')
  }, [filters])

  const handleApply = () => {
    const newFilters: AdminConversationFilters = {}
    if (userId) {
      newFilters.userId = parseInt(userId, 10)
    }
    if (startDate) {
      newFilters.startDate = startDate
    }
    if (endDate) {
      newFilters.endDate = endDate
    }
    onApplyFilters(newFilters)
  }

  const handleClear = () => {
    setUserId('')
    setStartDate('')
    setEndDate('')
    onClearFilters()
  }

  const hasFilters = userId || startDate || endDate

  return (
    <div className="bg-white rounded-xl shadow-md p-4 mb-6">
      <h3 className="text-sm font-semibold text-slate-700 mb-4">フィルター</h3>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div>
          <label htmlFor="user-filter" className="block text-sm font-medium text-slate-700 mb-1">
            ユーザー
          </label>
          <select
            id="user-filter"
            value={userId}
            onChange={e => setUserId(e.target.value)}
            className="block w-full px-3 py-2 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-500"
          >
            <option value="">全てのユーザー</option>
            {users.map(user => (
              <option key={user.id} value={user.id}>
                {user.name || user.email}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="start-date" className="block text-sm font-medium text-slate-700 mb-1">
            開始日
          </label>
          <input
            id="start-date"
            type="date"
            value={startDate}
            onChange={e => setStartDate(e.target.value)}
            className="block w-full px-3 py-2 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-500"
          />
        </div>
        <div>
          <label htmlFor="end-date" className="block text-sm font-medium text-slate-700 mb-1">
            終了日
          </label>
          <input
            id="end-date"
            type="date"
            value={endDate}
            onChange={e => setEndDate(e.target.value)}
            className="block w-full px-3 py-2 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-500"
          />
        </div>
        <div className="flex items-end gap-2">
          <Button onClick={handleApply}>適用</Button>
          {hasFilters && (
            <Button variant="secondary" onClick={handleClear}>
              クリア
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
