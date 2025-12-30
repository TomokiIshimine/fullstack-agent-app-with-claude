/**
 * Admin conversation management types
 */

import type { MessageDto, PaginationMeta } from './chat'

/**
 * User info in admin conversation list
 */
export interface AdminUserInfo {
  id: number
  email: string
  name: string | null
}

/**
 * Admin conversation DTO from API
 */
export interface AdminConversationDto {
  uuid: string
  title: string
  message_count: number
  user: AdminUserInfo
  created_at: string
  updated_at: string
}

/**
 * Admin conversation domain model
 */
export interface AdminConversation {
  uuid: string
  title: string
  messageCount: number
  user: AdminUserInfo
  createdAt: Date
  updatedAt: Date
}

/**
 * Admin conversation list response
 */
export interface AdminConversationListResponse {
  conversations: AdminConversationDto[]
  meta: PaginationMeta
}

/**
 * Admin conversation detail response
 */
export interface AdminConversationDetailResponse {
  uuid: string
  title: string
  user: AdminUserInfo
  messages: MessageDto[]
  created_at: string
  updated_at: string
}

/**
 * Admin conversation filter options
 */
export interface AdminConversationFilters {
  userId?: number
  startDate?: string
  endDate?: string
}

/**
 * Helper function to convert AdminConversationDto to AdminConversation
 */
export function toAdminConversation(dto: AdminConversationDto): AdminConversation {
  return {
    uuid: dto.uuid,
    title: dto.title,
    messageCount: dto.message_count,
    user: dto.user,
    createdAt: new Date(dto.created_at),
    updatedAt: new Date(dto.updated_at),
  }
}
