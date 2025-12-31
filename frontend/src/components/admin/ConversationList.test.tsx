import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ConversationList } from './ConversationList'
import type { AdminConversation } from '@/types/adminConversation'

describe('ConversationList', () => {
  const mockOnViewDetail = vi.fn()

  const mockConversations: AdminConversation[] = [
    {
      uuid: 'conv-1',
      title: 'Test Conversation 1',
      messageCount: 5,
      user: { id: 1, email: 'user1@example.com', name: 'User One' },
      createdAt: new Date('2025-01-01T10:00:00Z'),
      updatedAt: new Date('2025-01-01T12:00:00Z'),
    },
    {
      uuid: 'conv-2',
      title: 'Test Conversation 2',
      messageCount: 3,
      user: { id: 2, email: 'user2@example.com', name: null },
      createdAt: new Date('2025-01-02T10:00:00Z'),
      updatedAt: new Date('2025-01-02T12:00:00Z'),
    },
  ]

  beforeEach(() => {
    mockOnViewDetail.mockReset()
  })

  describe('Rendering', () => {
    it('should display empty message when no conversations', () => {
      render(<ConversationList conversations={[]} onViewDetail={mockOnViewDetail} />)

      expect(screen.getByText('会話履歴がありません')).toBeInTheDocument()
    })

    it('should display conversation list with all conversations', () => {
      render(<ConversationList conversations={mockConversations} onViewDetail={mockOnViewDetail} />)

      expect(screen.getByText('Test Conversation 1')).toBeInTheDocument()
      expect(screen.getByText('Test Conversation 2')).toBeInTheDocument()
    })

    it('should display user name and email', () => {
      render(<ConversationList conversations={mockConversations} onViewDetail={mockOnViewDetail} />)

      expect(screen.getByText('User One')).toBeInTheDocument()
      expect(screen.getByText('user1@example.com')).toBeInTheDocument()
    })

    it('should display "-" for null name', () => {
      render(<ConversationList conversations={mockConversations} onViewDetail={mockOnViewDetail} />)

      const rows = screen.getAllByRole('row')
      const user2Row = rows.find(row => row.textContent?.includes('user2@example.com'))

      expect(user2Row?.textContent).toContain('-')
    })

    it('should display message count', () => {
      render(<ConversationList conversations={mockConversations} onViewDetail={mockOnViewDetail} />)

      expect(screen.getByText('5')).toBeInTheDocument()
      expect(screen.getByText('3')).toBeInTheDocument()
    })

    it('should format dates correctly', () => {
      render(<ConversationList conversations={mockConversations} onViewDetail={mockOnViewDetail} />)

      // Each date appears twice (created_at and updated_at)
      expect(screen.getAllByText('2025/1/1')).toHaveLength(2)
      expect(screen.getAllByText('2025/1/2')).toHaveLength(2)
    })
  })

  describe('Table Structure', () => {
    it('should have correct table headers', () => {
      render(<ConversationList conversations={mockConversations} onViewDetail={mockOnViewDetail} />)

      expect(screen.getByText('タイトル')).toBeInTheDocument()
      expect(screen.getByText('ユーザー')).toBeInTheDocument()
      expect(screen.getByText('メッセージ数')).toBeInTheDocument()
      expect(screen.getByText('作成日')).toBeInTheDocument()
      expect(screen.getByText('最終更新')).toBeInTheDocument()
      expect(screen.getByText('操作')).toBeInTheDocument()
    })

    it('should have correct number of rows', () => {
      render(<ConversationList conversations={mockConversations} onViewDetail={mockOnViewDetail} />)

      const rows = screen.getAllByRole('row')
      // 1 header row + 2 conversation rows
      expect(rows).toHaveLength(3)
    })
  })

  describe('Detail Button', () => {
    it('should call onViewDetail with uuid when detail button is clicked', () => {
      render(<ConversationList conversations={mockConversations} onViewDetail={mockOnViewDetail} />)

      const detailButtons = screen.getAllByRole('button', { name: '詳細' })
      fireEvent.click(detailButtons[0])

      expect(mockOnViewDetail).toHaveBeenCalledWith('conv-1')
    })

    it('should have detail button for each conversation', () => {
      render(<ConversationList conversations={mockConversations} onViewDetail={mockOnViewDetail} />)

      const detailButtons = screen.getAllByRole('button', { name: '詳細' })
      expect(detailButtons).toHaveLength(2)
    })
  })
})
