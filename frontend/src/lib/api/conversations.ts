import type {
  ConversationDetailResponse,
  ConversationDto,
  ConversationListResponse,
  CreateConversationRequest,
  CreateConversationResponse,
  MessageMetadata,
  SendMessageRequest,
  SendMessageResponse,
} from '@/types/chat'
import type { RetryEvent, StreamError } from '@/types/errors'
import { buildApiError, buildJsonHeaders, fetchSSE, fetchWithLogging, parseJson } from './client'

const API_BASE = '/api/conversations'

/**
 * Fetch conversations list with pagination
 */
export async function fetchConversations(
  page: number = 1,
  perPage: number = 20
): Promise<ConversationListResponse> {
  const params = new URLSearchParams({
    page: page.toString(),
    per_page: perPage.toString(),
  })

  const response = await fetchWithLogging(`${API_BASE}?${params}`)
  const json = await parseJson(response)

  if (!response.ok) {
    throw buildApiError(response, json)
  }

  return json as ConversationListResponse
}

/**
 * Fetch a single conversation with all messages
 */
export async function fetchConversation(uuid: string): Promise<ConversationDetailResponse> {
  const response = await fetchWithLogging(`${API_BASE}/${uuid}`)
  const json = await parseJson(response)

  if (!response.ok) {
    throw buildApiError(response, json)
  }

  return json as ConversationDetailResponse
}

/**
 * Create a new conversation with initial message
 */
export async function createConversation(
  data: CreateConversationRequest
): Promise<CreateConversationResponse> {
  const response = await fetchWithLogging(API_BASE, {
    method: 'POST',
    headers: {
      ...buildJsonHeaders(),
      'X-Stream': 'false',
    },
    body: JSON.stringify(data),
  })
  const json = await parseJson(response)

  if (!response.ok) {
    throw buildApiError(response, json)
  }

  return json as CreateConversationResponse
}

/**
 * Delete a conversation
 */
export async function deleteConversation(uuid: string): Promise<void> {
  const response = await fetchWithLogging(`${API_BASE}/${uuid}`, {
    method: 'DELETE',
  })

  if (!response.ok) {
    const json = await parseJson(response)
    throw buildApiError(response, json)
  }
}

/**
 * SSE event callback types for create conversation streaming
 */
export interface CreateConversationStreamCallbacks {
  onCreated?: (conversation: ConversationDto, userMessageId: number) => void
  onToolCallStart?: (toolCallId: string, toolName: string, input: Record<string, unknown>) => void
  onToolCallEnd?: (toolCallId: string, output?: string, error?: string) => void
  onDelta?: (delta: string) => void
  onEnd?: (assistantMessageId: number, content: string, metadata?: MessageMetadata) => void
  /** Called when retry is attempted during streaming */
  onRetry?: (event: RetryEvent) => void
  /** Called on error with structured error details */
  onError?: (error: StreamError) => void
}

/**
 * Create a new conversation with streaming AI response
 */
export async function createConversationStreaming(
  data: CreateConversationRequest,
  callbacks: CreateConversationStreamCallbacks
): Promise<void> {
  await fetchSSE(
    API_BASE,
    {
      method: 'POST',
      headers: buildJsonHeaders(),
      body: JSON.stringify(data),
    },
    {
      onEvent: (event, eventData) => {
        handleCreateConversationStreamEvent(event, eventData, callbacks)
      },
    }
  )
}

/**
 * Extract metadata from SSE event data
 */
function extractMetadataFromEvent(data: Record<string, unknown>): MessageMetadata | undefined {
  const hasMetadata =
    data.input_tokens != null ||
    data.output_tokens != null ||
    data.model != null ||
    data.response_time_ms != null ||
    data.cost_usd != null

  if (!hasMetadata) {
    return undefined
  }

  return {
    inputTokens: (data.input_tokens as number | null) ?? undefined,
    outputTokens: (data.output_tokens as number | null) ?? undefined,
    model: (data.model as string | null) ?? undefined,
    responseTimeMs: (data.response_time_ms as number | null) ?? undefined,
    costUsd: (data.cost_usd as number | null) ?? undefined,
  }
}

/**
 * Handle a single SSE event for create conversation streaming
 */
function handleCreateConversationStreamEvent(
  event: string,
  data: Record<string, unknown>,
  callbacks: CreateConversationStreamCallbacks
): void {
  switch (event) {
    case 'conversation_created':
      callbacks.onCreated?.(data.conversation as ConversationDto, data.user_message_id as number)
      break
    case 'tool_call_start':
      callbacks.onToolCallStart?.(
        data.tool_call_id as string,
        data.tool_name as string,
        data.input as Record<string, unknown>
      )
      break
    case 'tool_call_end':
      callbacks.onToolCallEnd?.(
        data.tool_call_id as string,
        (data.output as string | null) ?? undefined,
        (data.error as string | null) ?? undefined
      )
      break
    case 'content_delta':
      callbacks.onDelta?.(data.delta as string)
      break
    case 'message_end':
      callbacks.onEnd?.(
        data.assistant_message_id as number,
        data.content as string,
        extractMetadataFromEvent(data)
      )
      break
    case 'retry':
      callbacks.onRetry?.({
        attempt: data.attempt as number,
        max_attempts: data.max_attempts as number,
        error_type: data.error_type as string,
        delay: data.delay as number,
      })
      break
    case 'error':
      callbacks.onError?.({
        error: data.error as string,
        error_type: data.error_type as StreamError['error_type'],
        user_message_id: data.user_message_id as number | undefined,
        retry_after: data.retry_after as number | undefined,
        is_retryable: data.is_retryable as boolean | undefined,
      })
      break
  }
}

/**
 * Send a message (non-streaming)
 */
export async function sendMessage(
  uuid: string,
  data: SendMessageRequest
): Promise<SendMessageResponse> {
  const response = await fetchWithLogging(`${API_BASE}/${uuid}/messages`, {
    method: 'POST',
    headers: {
      ...buildJsonHeaders(),
      'X-Stream': 'false',
    },
    body: JSON.stringify(data),
  })
  const json = await parseJson(response)

  if (!response.ok) {
    throw buildApiError(response, json)
  }

  return json as SendMessageResponse
}

/**
 * SSE event callback types
 */
export interface StreamCallbacks {
  onStart?: (userMessageId: number) => void
  onToolCallStart?: (toolCallId: string, toolName: string, input: Record<string, unknown>) => void
  onToolCallEnd?: (toolCallId: string, output?: string, error?: string) => void
  onDelta?: (delta: string) => void
  onEnd?: (assistantMessageId: number, content: string, metadata?: MessageMetadata) => void
  /** Called when retry is attempted during streaming */
  onRetry?: (event: RetryEvent) => void
  /** Called on error with structured error details */
  onError?: (error: StreamError) => void
}

/**
 * Send a message with streaming response
 */
export async function sendMessageStreaming(
  uuid: string,
  data: SendMessageRequest,
  callbacks: StreamCallbacks
): Promise<void> {
  await fetchSSE(
    `${API_BASE}/${uuid}/messages`,
    {
      method: 'POST',
      headers: buildJsonHeaders(),
      body: JSON.stringify(data),
    },
    {
      onEvent: (event, eventData) => {
        handleStreamEvent(event, eventData, callbacks)
      },
    }
  )
}

/**
 * Handle a single SSE event
 */
function handleStreamEvent(
  event: string,
  data: Record<string, unknown>,
  callbacks: StreamCallbacks
): void {
  switch (event) {
    case 'message_start':
      callbacks.onStart?.(data.user_message_id as number)
      break
    case 'tool_call_start':
      callbacks.onToolCallStart?.(
        data.tool_call_id as string,
        data.tool_name as string,
        data.input as Record<string, unknown>
      )
      break
    case 'tool_call_end':
      callbacks.onToolCallEnd?.(
        data.tool_call_id as string,
        (data.output as string | null) ?? undefined,
        (data.error as string | null) ?? undefined
      )
      break
    case 'content_delta':
      callbacks.onDelta?.(data.delta as string)
      break
    case 'message_end':
      callbacks.onEnd?.(
        data.assistant_message_id as number,
        data.content as string,
        extractMetadataFromEvent(data)
      )
      break
    case 'retry':
      callbacks.onRetry?.({
        attempt: data.attempt as number,
        max_attempts: data.max_attempts as number,
        error_type: data.error_type as string,
        delay: data.delay as number,
      })
      break
    case 'error':
      callbacks.onError?.({
        error: data.error as string,
        error_type: data.error_type as StreamError['error_type'],
        user_message_id: data.user_message_id as number | undefined,
        retry_after: data.retry_after as number | undefined,
        is_retryable: data.is_retryable as boolean | undefined,
      })
      break
  }
}
