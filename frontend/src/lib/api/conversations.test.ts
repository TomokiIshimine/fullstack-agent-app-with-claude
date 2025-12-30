import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import {
  fetchConversations,
  fetchConversation,
  createConversation,
  deleteConversation,
  createConversationStreaming,
} from './conversations'
import { ApiError } from './client'
import { createMockResponse, createMockEmptyResponse, restoreFetch } from '@/test/helpers/mockApi'

describe('API Client - conversations', () => {
  let originalFetch: typeof global.fetch
  let mockFetch: ReturnType<typeof vi.fn>

  beforeEach(() => {
    originalFetch = global.fetch
    mockFetch = vi.fn()
    global.fetch = mockFetch as unknown as typeof fetch
  })

  afterEach(() => {
    restoreFetch(originalFetch)
    vi.restoreAllMocks()
  })

  describe('fetchConversations', () => {
    it('fetches conversations list successfully', async () => {
      const mockResponse = {
        conversations: [
          {
            uuid: 'test-uuid',
            title: 'Test Conversation',
            message_count: 5,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
          },
        ],
        meta: {
          total: 1,
          page: 1,
          per_page: 20,
          total_pages: 1,
        },
      }

      mockFetch.mockResolvedValueOnce(createMockResponse(mockResponse))

      const result = await fetchConversations()

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/conversations?page=1&per_page=20',
        expect.objectContaining({
          credentials: 'include',
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('throws ApiError on failure', async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({ error: 'Unauthorized' }, { status: 401, ok: false })
      )

      await expect(fetchConversations()).rejects.toThrow(ApiError)
    })
  })

  describe('fetchConversation', () => {
    it('fetches a single conversation successfully', async () => {
      const mockResponse = {
        conversation: {
          uuid: 'test-uuid',
          title: 'Test Conversation',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
        messages: [
          {
            id: 1,
            role: 'user',
            content: 'Hello',
            created_at: '2024-01-01T00:00:00Z',
          },
        ],
      }

      mockFetch.mockResolvedValueOnce(createMockResponse(mockResponse))

      const result = await fetchConversation('test-uuid')

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/conversations/test-uuid',
        expect.objectContaining({
          credentials: 'include',
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('throws ApiError on not found', async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({ error: 'Conversation not found' }, { status: 404, ok: false })
      )

      await expect(fetchConversation('nonexistent')).rejects.toThrow(ApiError)
    })
  })

  describe('createConversation', () => {
    it('creates a conversation successfully', async () => {
      const mockResponse = {
        conversation: {
          uuid: 'new-uuid',
          title: 'New Conversation',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
        message: {
          id: 1,
          role: 'user',
          content: 'Hello',
          created_at: '2024-01-01T00:00:00Z',
        },
      }

      mockFetch.mockResolvedValueOnce(createMockResponse(mockResponse))

      const result = await createConversation({ message: 'Hello' })

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/conversations',
        expect.objectContaining({
          method: 'POST',
          credentials: 'include',
          body: JSON.stringify({ message: 'Hello' }),
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('throws ApiError on validation error', async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({ error: 'Message is required' }, { status: 400, ok: false })
      )

      await expect(createConversation({ message: '' })).rejects.toThrow(ApiError)
    })
  })

  describe('deleteConversation', () => {
    it('deletes a conversation successfully', async () => {
      mockFetch.mockResolvedValueOnce(createMockEmptyResponse())

      await deleteConversation('test-uuid')

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/conversations/test-uuid',
        expect.objectContaining({
          method: 'DELETE',
          credentials: 'include',
        })
      )
    })

    it('throws ApiError on not found', async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({ error: 'Conversation not found' }, { status: 404, ok: false })
      )

      await expect(deleteConversation('nonexistent')).rejects.toThrow(ApiError)
    })
  })

  describe('createConversationStreaming', () => {
    it('calls streaming endpoint with correct parameters', async () => {
      // Create a mock readable stream
      const mockSSEData =
        'event: conversation_created\ndata: {"conversation":{"uuid":"test-uuid","title":"Test"},"user_message_id":1}\n\n' +
        'event: content_delta\ndata: {"delta":"Hello"}\n\n' +
        'event: content_delta\ndata: {"delta":" World"}\n\n' +
        'event: message_end\ndata: {"assistant_message_id":2,"content":"Hello World"}\n\n'

      const encoder = new TextEncoder()
      const stream = new ReadableStream({
        start(controller) {
          controller.enqueue(encoder.encode(mockSSEData))
          controller.close()
        },
      })

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        body: stream,
      } as Response)

      const callbacks = {
        onCreated: vi.fn(),
        onDelta: vi.fn(),
        onEnd: vi.fn(),
        onError: vi.fn(),
      }

      await createConversationStreaming({ message: 'Hello' }, callbacks)

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/conversations',
        expect.objectContaining({
          method: 'POST',
          credentials: 'include',
          body: JSON.stringify({ message: 'Hello' }),
        })
      )

      expect(callbacks.onCreated).toHaveBeenCalledWith({ uuid: 'test-uuid', title: 'Test' }, 1)
      expect(callbacks.onDelta).toHaveBeenCalledTimes(2)
      expect(callbacks.onDelta).toHaveBeenCalledWith('Hello')
      expect(callbacks.onDelta).toHaveBeenCalledWith(' World')
      expect(callbacks.onEnd).toHaveBeenCalledWith(2, 'Hello World', undefined)
      expect(callbacks.onError).not.toHaveBeenCalled()
    })

    it('throws ApiError on HTTP error', async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({ error: 'Unauthorized' }, { status: 401, ok: false })
      )

      const callbacks = {
        onCreated: vi.fn(),
        onDelta: vi.fn(),
        onEnd: vi.fn(),
        onError: vi.fn(),
      }

      await expect(createConversationStreaming({ message: 'Hello' }, callbacks)).rejects.toThrow(
        ApiError
      )
    })

    it('throws ApiError when response body is missing', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        body: null,
      } as Response)

      const callbacks = {
        onCreated: vi.fn(),
        onDelta: vi.fn(),
        onEnd: vi.fn(),
        onError: vi.fn(),
      }

      await expect(createConversationStreaming({ message: 'Hello' }, callbacks)).rejects.toThrow(
        'No response body for streaming'
      )
    })

    it('handles error events from stream', async () => {
      const mockSSEData =
        'event: conversation_created\ndata: {"conversation":{"uuid":"test-uuid","title":"Test"},"user_message_id":1}\n\n' +
        'event: error\ndata: {"error":"AI service error","user_message_id":1}\n\n'

      const encoder = new TextEncoder()
      const stream = new ReadableStream({
        start(controller) {
          controller.enqueue(encoder.encode(mockSSEData))
          controller.close()
        },
      })

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        body: stream,
      } as Response)

      const callbacks = {
        onCreated: vi.fn(),
        onDelta: vi.fn(),
        onEnd: vi.fn(),
        onError: vi.fn(),
      }

      await createConversationStreaming({ message: 'Hello' }, callbacks)

      expect(callbacks.onCreated).toHaveBeenCalled()
      expect(callbacks.onError).toHaveBeenCalledWith({
        error: 'AI service error',
        error_type: undefined,
        user_message_id: 1,
        retry_after: undefined,
        is_retryable: undefined,
      })
    })
  })
})
