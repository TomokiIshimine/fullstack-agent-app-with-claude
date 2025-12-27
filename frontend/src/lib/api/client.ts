import { logger } from '@/lib/logger'
/**
 * Custom error class for API errors
 */
export class ApiError extends Error {
  status: number
  data?: unknown

  constructor(status: number, message: string, data?: unknown) {
    super(message)
    this.status = status
    this.data = data
    this.name = 'ApiError'
  }
}

/**
 * Wrapper for fetch with automatic logging, timing, and credentials
 */
export async function fetchWithLogging(url: string, options?: RequestInit): Promise<Response> {
  const method = options?.method || 'GET'
  const startTime = performance.now()

  logger.logApiRequest(method, url)

  try {
    const response = await fetch(url, {
      ...options,
      credentials: 'include', // Always include cookies for authentication
    })
    const duration = performance.now() - startTime

    logger.logApiResponse(method, url, response.status, duration)

    return response
  } catch (error) {
    const duration = performance.now() - startTime
    logger.logApiError(method, url, error, { duration })
    throw error
  }
}

/**
 * Build standard JSON headers for API requests
 */
export function buildJsonHeaders(): HeadersInit {
  return {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  }
}

/**
 * Parse JSON response, returning null for empty responses
 */
export async function parseJson(response: Response): Promise<unknown> {
  const text = await response.text()
  if (!text) {
    return null
  }
  try {
    return JSON.parse(text)
  } catch {
    return null
  }
}

/**
 * Build ApiError from response and parsed JSON
 * Supports both error formats:
 * - { error: string }
 * - { error: { message: string } }
 */
export function buildApiError(response: Response, json: unknown): ApiError {
  if (isErrorResponseWithMessage(json)) {
    return new ApiError(response.status, json.error.message ?? 'Request failed', json)
  }
  if (isErrorResponse(json)) {
    return new ApiError(response.status, json.error ?? 'Request failed', json)
  }
  return new ApiError(response.status, response.statusText || 'Request failed', json)
}

/**
 * Type guard to check if response is an error response with string error
 */
export function isErrorResponse(json: unknown): json is { error: string } {
  return Boolean(
    json &&
      typeof json === 'object' &&
      'error' in (json as Record<string, unknown>) &&
      typeof (json as { error: unknown }).error === 'string'
  )
}

/**
 * Type guard to check if response is an error response with message object
 */
function isErrorResponseWithMessage(json: unknown): json is { error: { message?: string } } {
  return Boolean(
    json &&
      typeof json === 'object' &&
      'error' in (json as Record<string, unknown>) &&
      typeof (json as { error: unknown }).error === 'object' &&
      (json as { error: unknown }).error !== null
  )
}

/**
 * Options for SSE stream parsing
 */
export interface SSEStreamOptions<T extends Record<string, unknown> = Record<string, unknown>> {
  /** Called for each parsed SSE event */
  onEvent: (event: string, data: T) => void
  /** Called on stream error (optional) */
  onStreamError?: (error: Error) => void
}

/**
 * Parse SSE events from a ReadableStream response body.
 * Handles buffering for incomplete events and JSON parsing.
 *
 * @param body - The ReadableStream from response.body
 * @param options - Event handler callbacks
 * @throws ApiError if body is null
 *
 * @example
 * await parseSSEStream(response.body, {
 *   onEvent: (event, data) => {
 *     switch (event) {
 *       case 'content_delta':
 *         callbacks.onDelta?.(data.delta as string)
 *         break
 *     }
 *   }
 * })
 */
export async function parseSSEStream<T extends Record<string, unknown> = Record<string, unknown>>(
  body: ReadableStream<Uint8Array> | null,
  options: SSEStreamOptions<T>
): Promise<void> {
  if (!body) {
    throw new ApiError(500, 'No response body for streaming')
  }

  const reader = body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      // Parse SSE events from buffer
      const lines = buffer.split('\n')
      buffer = lines.pop() || '' // Keep incomplete line in buffer

      let currentEvent = ''
      for (const line of lines) {
        if (line.startsWith('event: ')) {
          currentEvent = line.slice(7)
        } else if (line.startsWith('data: ') && currentEvent) {
          const eventData = line.slice(6)
          try {
            const parsed = JSON.parse(eventData) as T
            options.onEvent(currentEvent, parsed)
          } catch {
            // Ignore JSON parse errors for malformed events
          }
          currentEvent = ''
        }
      }
    }
  } catch (error) {
    options.onStreamError?.(error as Error)
    throw error
  } finally {
    reader.releaseLock()
  }
}

/**
 * Perform a streaming fetch with SSE parsing.
 * Combines fetch, error handling, and SSE parsing into one operation.
 *
 * @param url - The URL to fetch
 * @param init - Fetch init options
 * @param sseOptions - SSE parsing options
 *
 * @example
 * await fetchSSE('/api/messages', {
 *   method: 'POST',
 *   body: JSON.stringify({ content: 'Hello' })
 * }, {
 *   onEvent: (event, data) => {
 *     if (event === 'content_delta') {
 *       setContent(prev => prev + data.delta)
 *     }
 *   }
 * })
 */
export async function fetchSSE<T extends Record<string, unknown> = Record<string, unknown>>(
  url: string,
  init: RequestInit,
  sseOptions: SSEStreamOptions<T>
): Promise<void> {
  const response = await fetch(url, {
    ...init,
    credentials: 'include',
  })

  if (!response.ok) {
    const json = await parseJson(response)
    throw buildApiError(response, json)
  }

  await parseSSEStream<T>(response.body, sseOptions)
}
