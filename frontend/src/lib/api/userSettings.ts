import type {
  UserSettingsResponse,
  UserSettingsUpdateRequest,
  UserSettingsUpdateResponse,
} from '@/types/userSettings'
import { fetchWithLogging, buildJsonHeaders, parseJson, buildApiError } from './client'

const API_BASE_URL = '/api/users/me/settings'

/**
 * Get current user's settings
 */
export async function getUserSettings(): Promise<UserSettingsResponse> {
  const response = await fetchWithLogging(API_BASE_URL, {
    method: 'GET',
    headers: buildJsonHeaders(),
  })
  const json = await parseJson(response)
  if (!response.ok) {
    throw buildApiError(response, json)
  }
  return json as UserSettingsResponse
}

/**
 * Update current user's settings
 */
export async function updateUserSettings(
  payload: UserSettingsUpdateRequest
): Promise<UserSettingsUpdateResponse> {
  const response = await fetchWithLogging(API_BASE_URL, {
    method: 'PATCH',
    headers: buildJsonHeaders(),
    body: JSON.stringify(payload),
  })
  const json = await parseJson(response)
  if (!response.ok) {
    throw buildApiError(response, json)
  }
  return json as UserSettingsUpdateResponse
}
