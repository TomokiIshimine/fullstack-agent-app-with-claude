import { buildApiError, fetchWithLogging, parseJson } from './client'

const API_BASE = '/api/conversations'

export interface SuggestionsResponse {
  suggestions: string[]
}

/**
 * Fetch reply suggestions for a conversation
 */
export async function fetchSuggestions(
  uuid: string,
  signal?: AbortSignal
): Promise<SuggestionsResponse> {
  const response = await fetchWithLogging(`${API_BASE}/${uuid}/suggestions`, {
    method: 'POST',
    signal,
  })
  const json = await parseJson(response)

  if (!response.ok) {
    throw buildApiError(response, json)
  }

  return json as SuggestionsResponse
}
