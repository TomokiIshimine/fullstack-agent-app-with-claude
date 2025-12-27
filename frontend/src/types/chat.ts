/**
 * Message role type
 */
export type MessageRole = 'user' | 'assistant'

/**
 * Message DTO from API
 */
export interface MessageDto {
  id: number
  role: MessageRole
  content: string
  created_at: string
}

/**
 * Message domain model
 */
export interface Message {
  id: number
  role: MessageRole
  content: string
  createdAt: Date
}

/**
 * Conversation DTO from API (without messages)
 */
export interface ConversationDto {
  uuid: string
  title: string
  created_at: string
  updated_at: string
}

/**
 * Conversation with message count DTO
 */
export interface ConversationWithCountDto {
  uuid: string
  title: string
  message_count: number
  created_at: string
  updated_at: string
}

/**
 * Conversation domain model
 */
export interface Conversation {
  uuid: string
  title: string
  createdAt: Date
  updatedAt: Date
}

/**
 * Conversation with message count
 */
export interface ConversationWithCount extends Conversation {
  messageCount: number
}

/**
 * Pagination metadata
 */
export interface PaginationMeta {
  total: number
  page: number
  per_page: number
  total_pages: number
}

/**
 * Conversation list response
 */
export interface ConversationListResponse {
  conversations: ConversationWithCountDto[]
  meta: PaginationMeta
}

/**
 * Conversation detail response
 */
export interface ConversationDetailResponse {
  conversation: ConversationDto
  messages: MessageDto[]
}

/**
 * Create conversation request
 */
export interface CreateConversationRequest {
  message: string
}

/**
 * Create conversation response
 */
export interface CreateConversationResponse {
  conversation: ConversationDto
  message: MessageDto
  assistant_message?: MessageDto
}

/**
 * Send message request
 */
export interface SendMessageRequest {
  content: string
}

/**
 * Send message response (non-streaming)
 */
export interface SendMessageResponse {
  user_message: MessageDto
  assistant_message: MessageDto
}

/**
 * SSE event types for streaming
 */
export type StreamEventType = 'message_start' | 'content_delta' | 'message_end' | 'error'

/**
 * SSE event data for message_start
 */
export interface MessageStartEvent {
  user_message_id: number
}

/**
 * SSE event data for content_delta
 */
export interface ContentDeltaEvent {
  delta: string
}

/**
 * SSE event data for message_end
 */
export interface MessageEndEvent {
  assistant_message_id: number
  content: string
}

/**
 * SSE event data for error
 */
export interface StreamErrorEvent {
  error: string
}

/**
 * Helper function to convert MessageDto to Message
 */
export function toMessage(dto: MessageDto): Message {
  return {
    id: dto.id,
    role: dto.role,
    content: dto.content,
    createdAt: new Date(dto.created_at),
  }
}

/**
 * Helper function to convert ConversationDto to Conversation
 */
export function toConversation(dto: ConversationDto): Conversation {
  return {
    uuid: dto.uuid,
    title: dto.title,
    createdAt: new Date(dto.created_at),
    updatedAt: new Date(dto.updated_at),
  }
}

/**
 * Helper function to convert ConversationWithCountDto to ConversationWithCount
 */
export function toConversationWithCount(dto: ConversationWithCountDto): ConversationWithCount {
  return {
    uuid: dto.uuid,
    title: dto.title,
    messageCount: dto.message_count,
    createdAt: new Date(dto.created_at),
    updatedAt: new Date(dto.updated_at),
  }
}
