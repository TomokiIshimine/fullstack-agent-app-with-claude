import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ConversationFilters } from './ConversationFilters'
import type { UserResponse } from '@/types/user'

describe('ConversationFilters', () => {
  const mockOnApplyFilters = vi.fn()
  const mockOnClearFilters = vi.fn()

  const mockUsers: UserResponse[] = [
    {
      id: 1,
      email: 'user1@example.com',
      name: 'User One',
      role: 'user',
      created_at: '2025-01-01T00:00:00Z',
    },
    {
      id: 2,
      email: 'user2@example.com',
      name: null,
      role: 'user',
      created_at: '2025-01-02T00:00:00Z',
    },
  ]

  beforeEach(() => {
    mockOnApplyFilters.mockReset()
    mockOnClearFilters.mockReset()
  })

  describe('Rendering', () => {
    it('should render all filter inputs', () => {
      render(
        <ConversationFilters
          users={mockUsers}
          filters={{}}
          onApplyFilters={mockOnApplyFilters}
          onClearFilters={mockOnClearFilters}
        />
      )

      expect(screen.getByLabelText('ユーザー')).toBeInTheDocument()
      expect(screen.getByLabelText('開始日')).toBeInTheDocument()
      expect(screen.getByLabelText('終了日')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: '適用' })).toBeInTheDocument()
    })

    it('should render user options in select', () => {
      render(
        <ConversationFilters
          users={mockUsers}
          filters={{}}
          onApplyFilters={mockOnApplyFilters}
          onClearFilters={mockOnClearFilters}
        />
      )

      expect(screen.getByText('全てのユーザー')).toBeInTheDocument()
      expect(screen.getByText('User One')).toBeInTheDocument()
      // For null name, should show email
      expect(screen.getByText('user2@example.com')).toBeInTheDocument()
    })

    it('should not show clear button when no filters applied', () => {
      render(
        <ConversationFilters
          users={mockUsers}
          filters={{}}
          onApplyFilters={mockOnApplyFilters}
          onClearFilters={mockOnClearFilters}
        />
      )

      expect(screen.queryByRole('button', { name: 'クリア' })).not.toBeInTheDocument()
    })

    it('should show clear button when filters are applied', () => {
      render(
        <ConversationFilters
          users={mockUsers}
          filters={{ userId: 1 }}
          onApplyFilters={mockOnApplyFilters}
          onClearFilters={mockOnClearFilters}
        />
      )

      expect(screen.getByRole('button', { name: 'クリア' })).toBeInTheDocument()
    })
  })

  describe('Initial Values', () => {
    it('should set initial values from filters prop', () => {
      render(
        <ConversationFilters
          users={mockUsers}
          filters={{ userId: 1, startDate: '2025-01-01', endDate: '2025-12-31' }}
          onApplyFilters={mockOnApplyFilters}
          onClearFilters={mockOnClearFilters}
        />
      )

      expect(screen.getByLabelText('ユーザー')).toHaveValue('1')
      expect(screen.getByLabelText('開始日')).toHaveValue('2025-01-01')
      expect(screen.getByLabelText('終了日')).toHaveValue('2025-12-31')
    })
  })

  describe('Apply Filters', () => {
    it('should call onApplyFilters with user filter', async () => {
      const user = userEvent.setup()
      render(
        <ConversationFilters
          users={mockUsers}
          filters={{}}
          onApplyFilters={mockOnApplyFilters}
          onClearFilters={mockOnClearFilters}
        />
      )

      await user.selectOptions(screen.getByLabelText('ユーザー'), '1')
      fireEvent.click(screen.getByRole('button', { name: '適用' }))

      expect(mockOnApplyFilters).toHaveBeenCalledWith({ userId: 1 })
    })

    it('should call onApplyFilters with date filters', async () => {
      const user = userEvent.setup()
      render(
        <ConversationFilters
          users={mockUsers}
          filters={{}}
          onApplyFilters={mockOnApplyFilters}
          onClearFilters={mockOnClearFilters}
        />
      )

      await user.type(screen.getByLabelText('開始日'), '2025-01-01')
      await user.type(screen.getByLabelText('終了日'), '2025-12-31')
      fireEvent.click(screen.getByRole('button', { name: '適用' }))

      expect(mockOnApplyFilters).toHaveBeenCalledWith({
        startDate: '2025-01-01',
        endDate: '2025-12-31',
      })
    })

    it('should call onApplyFilters with all filters', async () => {
      const user = userEvent.setup()
      render(
        <ConversationFilters
          users={mockUsers}
          filters={{}}
          onApplyFilters={mockOnApplyFilters}
          onClearFilters={mockOnClearFilters}
        />
      )

      await user.selectOptions(screen.getByLabelText('ユーザー'), '2')
      await user.type(screen.getByLabelText('開始日'), '2025-06-01')
      await user.type(screen.getByLabelText('終了日'), '2025-06-30')
      fireEvent.click(screen.getByRole('button', { name: '適用' }))

      expect(mockOnApplyFilters).toHaveBeenCalledWith({
        userId: 2,
        startDate: '2025-06-01',
        endDate: '2025-06-30',
      })
    })

    it('should call onApplyFilters with empty object when no filters set', () => {
      render(
        <ConversationFilters
          users={mockUsers}
          filters={{}}
          onApplyFilters={mockOnApplyFilters}
          onClearFilters={mockOnClearFilters}
        />
      )

      fireEvent.click(screen.getByRole('button', { name: '適用' }))

      expect(mockOnApplyFilters).toHaveBeenCalledWith({})
    })
  })

  describe('Clear Filters', () => {
    it('should call onClearFilters and reset local state when clear button clicked', async () => {
      const user = userEvent.setup()
      render(
        <ConversationFilters
          users={mockUsers}
          filters={{ userId: 1, startDate: '2025-01-01' }}
          onApplyFilters={mockOnApplyFilters}
          onClearFilters={mockOnClearFilters}
        />
      )

      await user.click(screen.getByRole('button', { name: 'クリア' }))

      expect(mockOnClearFilters).toHaveBeenCalled()
      expect(screen.getByLabelText('ユーザー')).toHaveValue('')
      expect(screen.getByLabelText('開始日')).toHaveValue('')
      expect(screen.getByLabelText('終了日')).toHaveValue('')
    })
  })

  describe('Filter Updates', () => {
    it('should update local state when filters prop changes', () => {
      const { rerender } = render(
        <ConversationFilters
          users={mockUsers}
          filters={{}}
          onApplyFilters={mockOnApplyFilters}
          onClearFilters={mockOnClearFilters}
        />
      )

      expect(screen.getByLabelText('ユーザー')).toHaveValue('')

      rerender(
        <ConversationFilters
          users={mockUsers}
          filters={{ userId: 2 }}
          onApplyFilters={mockOnApplyFilters}
          onClearFilters={mockOnClearFilters}
        />
      )

      expect(screen.getByLabelText('ユーザー')).toHaveValue('2')
    })
  })
})
