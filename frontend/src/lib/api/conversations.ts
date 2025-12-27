import type {
  ConversationDetailResponse,
  ConversationDto,
  ConversationListResponse,
  CreateConversationRequest,
  CreateConversationResponse,
  SendMessageRequest,
  SendMessageResponse,
} from '@/types/chat'
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
  onEnd?: (assistantMessageId: number, content: string) => void
  onError?: (error: string, userMessageId?: number) => void
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
      callbacks.onEnd?.(data.assistant_message_id as number, data.content as string)
      break
    case 'error':
      callbacks.onError?.(data.error as string, data.user_message_id as number | undefined)
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
  onEnd?: (assistantMessageId: number, content: string) => void
  /** Called on error. userMessageId is provided if message was persisted before error */
  onError?: (error: string, userMessageId?: number) => void
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
      callbacks.onEnd?.(data.assistant_message_id as number, data.content as string)
      break
    case 'error':
      // user_message_id is included if the message was persisted before the error
      callbacks.onError?.(data.error as string, data.user_message_id as number | undefined)
      break
  }
}
