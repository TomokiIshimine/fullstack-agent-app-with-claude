import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useAdminConversations } from './useAdminConversations'

// Mock the API modules
vi.mock('@/lib/api/adminConversations', () => ({
  fetchAdminConversations: vi.fn(),
  fetchAdminConversationDetail: vi.fn(),
}))

vi.mock('@/lib/api/users', () => ({
  fetchUsers: vi.fn(),
}))

// Mock logger
vi.mock('@/lib/logger', () => ({
  logger: {
    debug: vi.fn(),
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
  },
}))

import { fetchAdminConversations, fetchAdminConversationDetail } from '@/lib/api/adminConversations'
import { fetchUsers } from '@/lib/api/users'

const mockConversationsResponse = {
  conversations: [
    {
      uuid: 'conv-1',
      title: 'Test Conversation 1',
      message_count: 5,
      user: { id: 1, email: 'user1@example.com', name: 'User One' },
      created_at: '2025-01-01T10:00:00Z',
      updated_at: '2025-01-01T12:00:00Z',
    },
    {
      uuid: 'conv-2',
      title: 'Test Conversation 2',
      message_count: 3,
      user: { id: 2, email: 'user2@example.com', name: 'User Two' },
      created_at: '2025-01-02T10:00:00Z',
      updated_at: '2025-01-02T12:00:00Z',
    },
  ],
  meta: {
    total: 2,
    page: 1,
    per_page: 20,
    total_pages: 1,
  },
}

const mockUsers = [
  {
    id: 1,
    email: 'user1@example.com',
    name: 'User One',
    role: 'user' as const,
    created_at: '2025-01-01T00:00:00Z',
  },
  {
    id: 2,
    email: 'user2@example.com',
    name: 'User Two',
    role: 'user' as const,
    created_at: '2025-01-02T00:00:00Z',
  },
]

const mockConversationDetail = {
  uuid: 'conv-1',
  title: 'Test Conversation 1',
  user: { id: 1, email: 'user1@example.com', name: 'User One' },
  messages: [
    { id: 1, role: 'user' as const, content: 'Hello', created_at: '2025-01-01T10:00:00Z' },
    { id: 2, role: 'assistant' as const, content: 'Hi there!', created_at: '2025-01-01T10:00:01Z' },
  ],
  created_at: '2025-01-01T10:00:00Z',
  updated_at: '2025-01-01T12:00:00Z',
}

describe('useAdminConversations', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    vi.mocked(fetchAdminConversations).mockResolvedValue(mockConversationsResponse)
    vi.mocked(fetchUsers).mockResolvedValue(mockUsers)
    vi.mocked(fetchAdminConversationDetail).mockResolvedValue(mockConversationDetail)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Initial state', () => {
    it('should have correct initial state with autoLoad=false', () => {
      const { result } = renderHook(() => useAdminConversations({ autoLoad: false }))

      expect(result.current.conversations).toEqual([])
      expect(result.current.users).toEqual([])
      expect(result.current.pagination).toBeNull()
      expect(result.current.isLoading).toBe(true)
      expect(result.current.isLoadingDetail).toBe(false)
      expect(result.current.selectedConversation).toBeNull()
      expect(result.current.filters).toEqual({})
      expect(result.current.currentPage).toBe(1)
      expect(result.current.error).toBeNull()
    })

    it('should auto-load conversations and users on mount by default', async () => {
      const { result } = renderHook(() => useAdminConversations())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(fetchAdminConversations).toHaveBeenCalledWith(1, 20, {})
      expect(fetchUsers).toHaveBeenCalled()
      expect(result.current.conversations).toHaveLength(2)
      expect(result.current.users).toHaveLength(2)
    })
  })

  describe('loadConversations', () => {
    it('should load conversations successfully', async () => {
      const { result } = renderHook(() => useAdminConversations({ autoLoad: false }))

      await act(async () => {
        await result.current.loadConversations()
      })

      expect(result.current.conversations).toHaveLength(2)
      expect(result.current.conversations[0].uuid).toBe('conv-1')
      expect(result.current.conversations[0].title).toBe('Test Conversation 1')
      expect(result.current.conversations[0].messageCount).toBe(5)
      expect(result.current.pagination).toEqual(mockConversationsResponse.meta)
      expect(result.current.isLoading).toBe(false)
    })

    it('should convert dates correctly', async () => {
      const { result } = renderHook(() => useAdminConversations({ autoLoad: false }))

      await act(async () => {
        await result.current.loadConversations()
      })

      expect(result.current.conversations[0].createdAt).toBeInstanceOf(Date)
      expect(result.current.conversations[0].updatedAt).toBeInstanceOf(Date)
    })

    it('should handle error when loading conversations', async () => {
      vi.mocked(fetchAdminConversations).mockRejectedValue(new Error('Network error'))

      const { result } = renderHook(() => useAdminConversations({ autoLoad: false }))

      await act(async () => {
        await result.current.loadConversations()
      })

      expect(result.current.error).toBe('Network error')
      expect(result.current.isLoading).toBe(false)
    })

    it('should pass page and filters to API', async () => {
      const { result } = renderHook(() => useAdminConversations({ autoLoad: false }))
      const filters = { user_id: 1, start_date: '2025-01-01' }

      await act(async () => {
        await result.current.loadConversations(2, filters)
      })

      expect(fetchAdminConversations).toHaveBeenCalledWith(2, 20, filters)
      expect(result.current.currentPage).toBe(2)
    })
  })

  describe('loadConversationDetail', () => {
    it('should load conversation detail successfully', async () => {
      const { result } = renderHook(() => useAdminConversations({ autoLoad: false }))

      await act(async () => {
        await result.current.loadConversationDetail('conv-1')
      })

      expect(result.current.selectedConversation).not.toBeNull()
      expect(result.current.selectedConversation?.uuid).toBe('conv-1')
      expect(result.current.selectedConversation?.messages).toHaveLength(2)
      expect(result.current.isLoadingDetail).toBe(false)
    })

    it('should handle error when loading detail', async () => {
      vi.mocked(fetchAdminConversationDetail).mockRejectedValue(new Error('Not found'))

      const { result } = renderHook(() => useAdminConversations({ autoLoad: false }))

      await act(async () => {
        await result.current.loadConversationDetail('invalid-uuid')
      })

      expect(result.current.error).toBe('Not found')
      expect(result.current.isLoadingDetail).toBe(false)
    })
  })

  describe('applyFilters', () => {
    it('should apply filters and reload conversations', async () => {
      const { result } = renderHook(() => useAdminConversations({ autoLoad: false }))
      const newFilters = { user_id: 1, start_date: '2025-01-01' }

      await act(async () => {
        result.current.applyFilters(newFilters)
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.filters).toEqual(newFilters)
      expect(result.current.currentPage).toBe(1)
      expect(fetchAdminConversations).toHaveBeenCalledWith(1, 20, newFilters)
    })
  })

  describe('clearFilters', () => {
    it('should clear filters and reload conversations', async () => {
      const { result } = renderHook(() => useAdminConversations({ autoLoad: false }))

      // First apply some filters
      await act(async () => {
        result.current.applyFilters({ user_id: 1 })
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then clear them
      await act(async () => {
        result.current.clearFilters()
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.filters).toEqual({})
      expect(result.current.currentPage).toBe(1)
    })
  })

  describe('goToPage', () => {
    it('should navigate to specified page with current filters', async () => {
      const { result } = renderHook(() => useAdminConversations({ autoLoad: false }))

      // First apply some filters
      await act(async () => {
        result.current.applyFilters({ user_id: 1 })
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      vi.mocked(fetchAdminConversations).mockClear()

      // Then go to page 2
      await act(async () => {
        result.current.goToPage(2)
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(fetchAdminConversations).toHaveBeenCalledWith(2, 20, { user_id: 1 })
    })
  })

  describe('closeDetail', () => {
    it('should close the detail modal', async () => {
      const { result } = renderHook(() => useAdminConversations({ autoLoad: false }))

      // First load a detail
      await act(async () => {
        await result.current.loadConversationDetail('conv-1')
      })

      expect(result.current.selectedConversation).not.toBeNull()

      // Then close it
      act(() => {
        result.current.closeDetail()
      })

      expect(result.current.selectedConversation).toBeNull()
    })
  })

  describe('clearError', () => {
    it('should clear error state', async () => {
      vi.mocked(fetchAdminConversations).mockRejectedValue(new Error('Error'))

      const { result } = renderHook(() => useAdminConversations({ autoLoad: false }))

      await act(async () => {
        await result.current.loadConversations()
      })

      expect(result.current.error).toBe('Error')

      act(() => {
        result.current.clearError()
      })

      expect(result.current.error).toBeNull()
    })
  })

  describe('loadUsers', () => {
    it('should silently handle errors when loading users', async () => {
      vi.mocked(fetchUsers).mockRejectedValue(new Error('Failed to load users'))

      const { result } = renderHook(() => useAdminConversations())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Error should not be set for user loading failure
      expect(result.current.error).toBeNull()
      expect(result.current.users).toEqual([])
    })
  })
})
