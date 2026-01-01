import { useState, useEffect, useMemo } from 'react'
import { Button, Card, Select, Input } from '@/components/ui'
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

  const userOptions = useMemo(
    () => [
      { value: '', label: '全てのユーザー' },
      ...users.map(user => ({
        value: user.id.toString(),
        label: user.name || user.email,
      })),
    ],
    [users]
  )

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
    <Card padding="sm" className="mb-6">
      <h3 className="text-sm font-semibold text-slate-700 mb-4">フィルター</h3>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Select
          id="user-filter"
          label="ユーザー"
          value={userId}
          onChange={e => setUserId(e.target.value)}
          options={userOptions}
          fullWidth
        />
        <Input
          id="start-date"
          label="開始日"
          type="date"
          value={startDate}
          onChange={e => setStartDate(e.target.value)}
          fullWidth
        />
        <Input
          id="end-date"
          label="終了日"
          type="date"
          value={endDate}
          onChange={e => setEndDate(e.target.value)}
          fullWidth
        />
        <div className="flex items-end gap-2">
          <Button onClick={handleApply}>適用</Button>
          {hasFilters && (
            <Button variant="secondary" onClick={handleClear}>
              クリア
            </Button>
          )}
        </div>
      </div>
    </Card>
  )
}
