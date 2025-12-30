import type {
  AdminConversationDetailResponse,
  AdminConversationFilters,
  AdminConversationListResponse,
} from '@/types/adminConversation'
import { buildApiError, fetchWithLogging, parseJson } from './client'

const API_BASE = '/api/admin/conversations'

/**
 * Fetch all conversations for admin with optional filters (Admin only)
 */
export async function fetchAdminConversations(
  page: number = 1,
  perPage: number = 20,
  filters?: AdminConversationFilters
): Promise<AdminConversationListResponse> {
  const params = new URLSearchParams({
    page: page.toString(),
    per_page: perPage.toString(),
  })

  if (filters?.userId) {
    params.set('user_id', filters.userId.toString())
  }
  if (filters?.startDate) {
    params.set('start_date', filters.startDate)
  }
  if (filters?.endDate) {
    params.set('end_date', filters.endDate)
  }

  const response = await fetchWithLogging(`${API_BASE}?${params}`)
  const json = await parseJson(response)

  if (!response.ok) {
    throw buildApiError(response, json)
  }

  return json as AdminConversationListResponse
}

/**
 * Fetch a single conversation detail for admin (Admin only)
 */
export async function fetchAdminConversationDetail(
  uuid: string
): Promise<AdminConversationDetailResponse> {
  const response = await fetchWithLogging(`${API_BASE}/${uuid}`)
  const json = await parseJson(response)

  if (!response.ok) {
    throw buildApiError(response, json)
  }

  return json as AdminConversationDetailResponse
}
