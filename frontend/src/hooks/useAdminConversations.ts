import { useCallback, useEffect, useState } from 'react'
import { fetchAdminConversations, fetchAdminConversationDetail } from '@/lib/api/adminConversations'
import { fetchUsers } from '@/lib/api/users'
import { useErrorHandler } from './useErrorHandler'
import type { AdminConversation, AdminConversationFilters } from '@/types/adminConversation'
import type { PaginationMeta, MessageDto } from '@/types/chat'
import type { UserResponse } from '@/types/user'
import { logger } from '@/lib/logger'

interface ConversationDetail {
  uuid: string
  title: string
  user: {
    id: number
    email: string
    name: string | null
  }
  messages: MessageDto[]
  createdAt: Date
  updatedAt: Date
}

export function useAdminConversations() {
  const [conversations, setConversations] = useState<AdminConversation[]>([])
  const [users, setUsers] = useState<UserResponse[]>([])
  const [pagination, setPagination] = useState<PaginationMeta | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isLoadingDetail, setIsLoadingDetail] = useState(false)
  const [selectedConversation, setSelectedConversation] = useState<ConversationDetail | null>(null)
  const [filters, setFilters] = useState<AdminConversationFilters>({})
  const [currentPage, setCurrentPage] = useState(1)
  const { error, handleError, clearError } = useErrorHandler()

  const loadUsers = useCallback(async () => {
    try {
      const data = await fetchUsers()
      setUsers(data)
    } catch (err) {
      logger.error('Failed to load users for filter', { error: err })
    }
  }, [])

  const loadConversations = useCallback(
    async (page: number = 1, appliedFilters?: AdminConversationFilters) => {
      setIsLoading(true)
      clearError()
      try {
        const data = await fetchAdminConversations(page, 20, appliedFilters || filters)
        const converted: AdminConversation[] = data.conversations.map(dto => ({
          uuid: dto.uuid,
          title: dto.title,
          messageCount: dto.message_count,
          user: dto.user,
          createdAt: new Date(dto.created_at),
          updatedAt: new Date(dto.updated_at),
        }))
        setConversations(converted)
        setPagination(data.meta)
        setCurrentPage(page)
        logger.info('Admin conversations loaded', { count: converted.length, page })
      } catch (err) {
        handleError(err, 'Failed to load conversations')
      } finally {
        setIsLoading(false)
      }
    },
    [clearError, handleError, filters]
  )

  const loadConversationDetail = useCallback(
    async (uuid: string) => {
      setIsLoadingDetail(true)
      clearError()
      try {
        const data = await fetchAdminConversationDetail(uuid)
        setSelectedConversation({
          uuid: data.uuid,
          title: data.title,
          user: data.user,
          messages: data.messages,
          createdAt: new Date(data.created_at),
          updatedAt: new Date(data.updated_at),
        })
        logger.info('Admin conversation detail loaded', {
          uuid,
          messageCount: data.messages.length,
        })
      } catch (err) {
        handleError(err, 'Failed to load conversation detail')
      } finally {
        setIsLoadingDetail(false)
      }
    },
    [clearError, handleError]
  )

  const applyFilters = useCallback(
    (newFilters: AdminConversationFilters) => {
      setFilters(newFilters)
      setCurrentPage(1)
      void loadConversations(1, newFilters)
    },
    [loadConversations]
  )

  const clearFilters = useCallback(() => {
    setFilters({})
    setCurrentPage(1)
    void loadConversations(1, {})
  }, [loadConversations])

  const goToPage = useCallback(
    (page: number) => {
      void loadConversations(page)
    },
    [loadConversations]
  )

  const closeDetail = useCallback(() => {
    setSelectedConversation(null)
  }, [])

  useEffect(() => {
    void loadConversations()
    void loadUsers()
  }, [])

  return {
    conversations,
    users,
    pagination,
    isLoading,
    isLoadingDetail,
    selectedConversation,
    filters,
    currentPage,
    error,
    clearError,
    loadConversations,
    loadConversationDetail,
    applyFilters,
    clearFilters,
    goToPage,
    closeDetail,
  }
}
