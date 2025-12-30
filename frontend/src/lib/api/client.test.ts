import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { parseSSEStream, fetchSSE, ApiError, fetchWithLogging } from './client'
import { createMockResponse, restoreFetch } from '@/test/helpers/mockApi'
import * as authEvents from '@/lib/authEvents'

describe('SSE Utilities', () => {
  describe('parseSSEStream', () => {
    it('should parse a single SSE event correctly', async () => {
      const mockSSEData = 'event: test_event\ndata: {"key":"value"}\n\n'

      const encoder = new TextEncoder()
      const stream = new ReadableStream({
        start(controller) {
          controller.enqueue(encoder.encode(mockSSEData))
          controller.close()
        },
      })

      const onEvent = vi.fn()
      await parseSSEStream(stream, { onEvent })

      expect(onEvent).toHaveBeenCalledTimes(1)
      expect(onEvent).toHaveBeenCalledWith('test_event', { key: 'value' })
    })

    it('should parse multiple events in a single chunk', async () => {
      const mockSSEData = 'event: first\ndata: {"id":1}\n\n' + 'event: second\ndata: {"id":2}\n\n'

      const encoder = new TextEncoder()
      const stream = new ReadableStream({
        start(controller) {
          controller.enqueue(encoder.encode(mockSSEData))
          controller.close()
        },
      })

      const onEvent = vi.fn()
      await parseSSEStream(stream, { onEvent })

      expect(onEvent).toHaveBeenCalledTimes(2)
      expect(onEvent).toHaveBeenNthCalledWith(1, 'first', { id: 1 })
      expect(onEvent).toHaveBeenNthCalledWith(2, 'second', { id: 2 })
    })

    it('should handle multiple chunks with complete events', async () => {
      const encoder = new TextEncoder()
      let enqueueCount = 0
      const stream = new ReadableStream({
        pull(controller) {
          // Simulate multiple chunks, each containing complete events
          const chunks = ['event: first\ndata: {"id":1}\n\n', 'event: second\ndata: {"id":2}\n\n']
          if (enqueueCount < chunks.length) {
            controller.enqueue(encoder.encode(chunks[enqueueCount]))
            enqueueCount++
          } else {
            controller.close()
          }
        },
      })

      const onEvent = vi.fn()
      await parseSSEStream(stream, { onEvent })

      expect(onEvent).toHaveBeenCalledTimes(2)
      expect(onEvent).toHaveBeenNthCalledWith(1, 'first', { id: 1 })
      expect(onEvent).toHaveBeenNthCalledWith(2, 'second', { id: 2 })
    })

    it('should throw ApiError when body is null', async () => {
      const onEvent = vi.fn()

      await expect(parseSSEStream(null, { onEvent })).rejects.toThrow(ApiError)
      await expect(parseSSEStream(null, { onEvent })).rejects.toThrow(
        'No response body for streaming'
      )
    })

    it('should ignore malformed JSON in data', async () => {
      const mockSSEData =
        'event: test\ndata: {invalid json}\n\n' + 'event: valid\ndata: {"ok":true}\n\n'

      const encoder = new TextEncoder()
      const stream = new ReadableStream({
        start(controller) {
          controller.enqueue(encoder.encode(mockSSEData))
          controller.close()
        },
      })

      const onEvent = vi.fn()
      await parseSSEStream(stream, { onEvent })

      // Only valid event should be called
      expect(onEvent).toHaveBeenCalledTimes(1)
      expect(onEvent).toHaveBeenCalledWith('valid', { ok: true })
    })

    it('should ignore data lines without a preceding event', async () => {
      const mockSSEData = 'data: {"orphan":true}\n\nevent: proper\ndata: {"ok":true}\n\n'

      const encoder = new TextEncoder()
      const stream = new ReadableStream({
        start(controller) {
          controller.enqueue(encoder.encode(mockSSEData))
          controller.close()
        },
      })

      const onEvent = vi.fn()
      await parseSSEStream(stream, { onEvent })

      // Only the proper event should be called
      expect(onEvent).toHaveBeenCalledTimes(1)
      expect(onEvent).toHaveBeenCalledWith('proper', { ok: true })
    })

    it('should call onStreamError and re-throw on stream error', async () => {
      const testError = new Error('Stream failed')
      const stream = new ReadableStream({
        start(controller) {
          controller.error(testError)
        },
      })

      const onEvent = vi.fn()
      const onStreamError = vi.fn()

      await expect(parseSSEStream(stream, { onEvent, onStreamError })).rejects.toThrow(
        'Stream failed'
      )

      expect(onStreamError).toHaveBeenCalledWith(testError)
      expect(onEvent).not.toHaveBeenCalled()
    })
  })

  describe('fetchSSE', () => {
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

    it('should fetch and parse SSE stream', async () => {
      const mockSSEData =
        'event: message\ndata: {"text":"Hello"}\n\n' + 'event: message\ndata: {"text":"World"}\n\n'

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

      const onEvent = vi.fn()
      await fetchSSE('/api/stream', { method: 'POST' }, { onEvent })

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/stream',
        expect.objectContaining({
          method: 'POST',
          credentials: 'include',
        })
      )
      expect(onEvent).toHaveBeenCalledTimes(2)
      expect(onEvent).toHaveBeenNthCalledWith(1, 'message', { text: 'Hello' })
      expect(onEvent).toHaveBeenNthCalledWith(2, 'message', { text: 'World' })
    })

    it('should throw ApiError on HTTP error', async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({ error: 'Unauthorized' }, { status: 401, ok: false })
      )

      const onEvent = vi.fn()

      await expect(fetchSSE('/api/stream', { method: 'POST' }, { onEvent })).rejects.toThrow(
        ApiError
      )

      expect(onEvent).not.toHaveBeenCalled()
    })

    it('should include credentials in request', async () => {
      const stream = new ReadableStream({
        start(controller) {
          controller.close()
        },
      })

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        body: stream,
      } as Response)

      await fetchSSE('/api/stream', { method: 'GET' }, { onEvent: vi.fn() })

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/stream',
        expect.objectContaining({
          credentials: 'include',
        })
      )
    })

    it('should pass headers through to fetch', async () => {
      const stream = new ReadableStream({
        start(controller) {
          controller.close()
        },
      })

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        body: stream,
      } as Response)

      await fetchSSE(
        '/api/stream',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: 'test' }),
        },
        { onEvent: vi.fn() }
      )

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/stream',
        expect.objectContaining({
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: 'test' }),
        })
      )
    })
  })
})

describe('fetchWithLogging', () => {
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

  it('should emit session expired event on 401 response', async () => {
    const emitSpy = vi.spyOn(authEvents, 'emitSessionExpired')

    mockFetch.mockResolvedValueOnce(
      createMockResponse({ error: 'Unauthorized' }, { status: 401, ok: false })
    )

    await fetchWithLogging('/api/protected')

    expect(emitSpy).toHaveBeenCalledTimes(1)
  })

  it('should not emit session expired event on 200 response', async () => {
    const emitSpy = vi.spyOn(authEvents, 'emitSessionExpired')

    mockFetch.mockResolvedValueOnce(createMockResponse({ data: 'ok' }, { status: 200, ok: true }))

    await fetchWithLogging('/api/data')

    expect(emitSpy).not.toHaveBeenCalled()
  })

  it('should not emit session expired event on other error responses', async () => {
    const emitSpy = vi.spyOn(authEvents, 'emitSessionExpired')

    mockFetch.mockResolvedValueOnce(
      createMockResponse({ error: 'Forbidden' }, { status: 403, ok: false })
    )

    await fetchWithLogging('/api/forbidden')

    expect(emitSpy).not.toHaveBeenCalled()
  })

  it('should include credentials in request', async () => {
    mockFetch.mockResolvedValueOnce(createMockResponse({ data: 'ok' }, { status: 200, ok: true }))

    await fetchWithLogging('/api/data', { method: 'POST' })

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/data',
      expect.objectContaining({
        credentials: 'include',
        method: 'POST',
      })
    )
  })

  it('should return response even on 401', async () => {
    mockFetch.mockResolvedValueOnce(
      createMockResponse({ error: 'Unauthorized' }, { status: 401, ok: false })
    )

    const response = await fetchWithLogging('/api/protected')

    expect(response.status).toBe(401)
    expect(response.ok).toBe(false)
  })
})
