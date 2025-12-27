import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useNewConversation } from './useNewConversation'

// Mock the API module
vi.mock('@/lib/api/conversations', () => ({
  createConversationStreaming: vi.fn(),
}))

// Mock logger
vi.mock('@/lib/logger', () => ({
  logger: {
    debug: vi.fn(),
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
  },
}))

import { createConversationStreaming } from '@/lib/api/conversations'

describe('useNewConversation', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should have correct initial state', () => {
    const { result } = renderHook(() => useNewConversation())

    expect(result.current.conversation).toBeNull()
    expect(result.current.messages).toEqual([])
    expect(result.current.isStreaming).toBe(false)
    expect(result.current.streamingContent).toBe('')
    expect(result.current.error).toBeNull()
  })

  it('should add optimistic user message when creating conversation', async () => {
    const mockStreaming = vi.mocked(createConversationStreaming)
    mockStreaming.mockImplementation(async (_request, callbacks) => {
      callbacks.onCreated?.(
        { uuid: 'test-uuid', title: 'Test', created_at: '', updated_at: '' },
        1
      )
      callbacks.onEnd?.(2, 'Hello!')
    })

    const { result } = renderHook(() => useNewConversation())

    await act(async () => {
      await result.current.createConversation('Hello')
    })

    expect(result.current.messages).toHaveLength(2) // user + assistant
    expect(result.current.messages[0].role).toBe('user')
    expect(result.current.messages[0].content).toBe('Hello')
  })

  it('should update streaming content during delta events', async () => {
    const mockStreaming = vi.mocked(createConversationStreaming)
    mockStreaming.mockImplementation(async (_request, callbacks) => {
      callbacks.onCreated?.(
        { uuid: 'test-uuid', title: 'Test', created_at: '', updated_at: '' },
        1
      )
      callbacks.onDelta?.('Hello')
      callbacks.onDelta?.(' World')
      callbacks.onEnd?.(2, 'Hello World')
    })

    const { result } = renderHook(() => useNewConversation())

    await act(async () => {
      await result.current.createConversation('Hi')
    })

    expect(result.current.messages[1].content).toBe('Hello World')
  })

  it('should set conversation when onCreated is called', async () => {
    const mockStreaming = vi.mocked(createConversationStreaming)
    mockStreaming.mockImplementation(async (_request, callbacks) => {
      callbacks.onCreated?.(
        {
          uuid: 'test-uuid',
          title: 'Test Conversation',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
        1
      )
      callbacks.onEnd?.(2, 'Response')
    })

    const { result } = renderHook(() => useNewConversation())

    await act(async () => {
      await result.current.createConversation('Hello')
    })

    expect(result.current.conversation).not.toBeNull()
    expect(result.current.conversation?.uuid).toBe('test-uuid')
    expect(result.current.conversation?.title).toBe('Test Conversation')
  })

  it('should return uuid and userMessagePersisted on success', async () => {
    const mockStreaming = vi.mocked(createConversationStreaming)
    mockStreaming.mockImplementation(async (_request, callbacks) => {
      callbacks.onCreated?.(
        { uuid: 'created-uuid', title: 'Test', created_at: '', updated_at: '' },
        1
      )
      callbacks.onEnd?.(2, 'Response')
    })

    const { result } = renderHook(() => useNewConversation())

    let createResult: { uuid: string; userMessagePersisted: boolean } | undefined
    await act(async () => {
      createResult = await result.current.createConversation('Hello')
    })

    expect(createResult?.uuid).toBe('created-uuid')
    expect(createResult?.userMessagePersisted).toBe(true)
  })

  it('should reset state correctly', async () => {
    const mockStreaming = vi.mocked(createConversationStreaming)
    mockStreaming.mockImplementation(async (_request, callbacks) => {
      callbacks.onCreated?.(
        { uuid: 'test-uuid', title: 'Test', created_at: '', updated_at: '' },
        1
      )
      callbacks.onEnd?.(2, 'Response')
    })

    const { result } = renderHook(() => useNewConversation())

    await act(async () => {
      await result.current.createConversation('Hello')
    })

    expect(result.current.messages).toHaveLength(2)

    act(() => {
      result.current.reset()
    })

    expect(result.current.conversation).toBeNull()
    expect(result.current.messages).toEqual([])
    expect(result.current.isStreaming).toBe(false)
    expect(result.current.streamingContent).toBe('')
  })

  it('should handle error before message persisted', async () => {
    const mockStreaming = vi.mocked(createConversationStreaming)
    mockStreaming.mockRejectedValue(new Error('Network error'))

    const { result } = renderHook(() => useNewConversation())

    let caughtError: Error | undefined
    await act(async () => {
      try {
        await result.current.createConversation('Hello')
      } catch (err) {
        caughtError = err as Error
      }
    })

    expect(caughtError).toBeDefined()
    // Messages should be cleared when error before persist
    expect(result.current.messages).toEqual([])
    // error is a string from useErrorHandler
    expect(result.current.error).toBe('Network error')
    expect(result.current.isStreaming).toBe(false)
  })

  it('should keep messages when error after persist', async () => {
    const mockStreaming = vi.mocked(createConversationStreaming)

    mockStreaming.mockImplementation(async (_request, callbacks) => {
      callbacks.onCreated?.(
        { uuid: 'test-uuid', title: 'Test', created_at: '', updated_at: '' },
        1
      )
      // Simulate error during streaming by rejecting after onCreated
      throw new Error('AI error')
    })

    const { result } = renderHook(() => useNewConversation())

    let caughtError: Error | undefined
    await act(async () => {
      try {
        await result.current.createConversation('Hello')
      } catch (err) {
        caughtError = err as Error
      }
    })

    expect(caughtError).toBeDefined()
    // Messages should be kept for recovery since message was persisted
    // The user message was added optimistically, then onCreated updated it
    expect(result.current.messages).toHaveLength(1)
    expect(result.current.messages[0].role).toBe('user')
    expect(result.current.error).toBe('AI error')
  })

  it('should throw enhanced error with uuid and userMessagePersisted', async () => {
    const mockStreaming = vi.mocked(createConversationStreaming)
    mockStreaming.mockImplementation(async (_request, callbacks) => {
      callbacks.onCreated?.(
        { uuid: 'error-uuid', title: 'Test', created_at: '', updated_at: '' },
        1
      )
      callbacks.onError?.('AI error')
    })

    const { result } = renderHook(() => useNewConversation())

    let caughtError: Error & { uuid?: string; userMessagePersisted?: boolean } | undefined
    await act(async () => {
      try {
        await result.current.createConversation('Hello')
      } catch (err) {
        caughtError = err as Error & { uuid?: string; userMessagePersisted?: boolean }
      }
    })

    expect(caughtError).toBeDefined()
    expect(caughtError?.uuid).toBe('error-uuid')
    expect(caughtError?.userMessagePersisted).toBe(true)
  })

  it('should prevent double streaming by throwing when isStreaming is true', async () => {
    const mockStreaming = vi.mocked(createConversationStreaming)

    let resolveStreaming: () => void
    mockStreaming.mockImplementation(async (_request, callbacks) => {
      callbacks.onCreated?.(
        { uuid: 'test-uuid', title: 'Test', created_at: '', updated_at: '' },
        1
      )
      // Wait for external signal
      await new Promise<void>(resolve => {
        resolveStreaming = resolve
      })
      callbacks.onEnd?.(2, 'Response')
    })

    const { result } = renderHook(() => useNewConversation())

    // Start first call
    let firstCallPromise: Promise<unknown>
    await act(async () => {
      firstCallPromise = result.current.createConversation('First')
      // Wait a tick for state to update
      await Promise.resolve()
    })

    // isStreaming should be true now
    expect(result.current.isStreaming).toBe(true)

    // Try second call while first is running - should throw
    let secondCallError: Error | undefined
    await act(async () => {
      try {
        await result.current.createConversation('Second')
      } catch (err) {
        secondCallError = err as Error
      }
    })

    expect(secondCallError?.message).toBe('Already streaming')

    // Cleanup: resolve the first call
    resolveStreaming!()
    await act(async () => {
      await firstCallPromise
    })
  })

  it('should update user message ID when onCreated is called', async () => {
    const mockStreaming = vi.mocked(createConversationStreaming)
    mockStreaming.mockImplementation(async (_request, callbacks) => {
      callbacks.onCreated?.(
        { uuid: 'test-uuid', title: 'Test', created_at: '', updated_at: '' },
        42 // Real user message ID from server
      )
      callbacks.onEnd?.(2, 'Response')
    })

    const { result } = renderHook(() => useNewConversation())

    await act(async () => {
      await result.current.createConversation('Hello')
    })

    // User message should have the real ID, not the temp one
    expect(result.current.messages[0].id).toBe(42)
  })
})
