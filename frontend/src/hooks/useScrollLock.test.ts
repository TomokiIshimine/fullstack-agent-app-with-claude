import { describe, it, expect, beforeEach } from 'vitest'
import { renderHook } from '@testing-library/react'
import { useScrollLock, _resetLockCount, _getLockCount } from './useScrollLock'

describe('useScrollLock', () => {
  beforeEach(() => {
    // Reset state before each test
    _resetLockCount()
  })

  it('isLocked=true の場合、body の overflow を hidden に設定する', () => {
    renderHook(() => useScrollLock(true))

    expect(document.body.style.overflow).toBe('hidden')
    expect(_getLockCount()).toBe(1)
  })

  it('isLocked=false の場合、body の overflow を変更しない', () => {
    document.body.style.overflow = ''

    renderHook(() => useScrollLock(false))

    expect(document.body.style.overflow).toBe('')
    expect(_getLockCount()).toBe(0)
  })

  it('アンマウント時に lockCount をデクリメントする', () => {
    const { unmount } = renderHook(() => useScrollLock(true))

    expect(_getLockCount()).toBe(1)
    expect(document.body.style.overflow).toBe('hidden')

    unmount()

    expect(_getLockCount()).toBe(0)
    expect(document.body.style.overflow).toBe('')
  })

  it('複数のコンポーネントがロックしている場合、最後のコンポーネントがアンマウントされるまで overflow は hidden のまま', () => {
    // Simulate two components locking scroll
    const { unmount: unmount1 } = renderHook(() => useScrollLock(true))
    const { unmount: unmount2 } = renderHook(() => useScrollLock(true))

    expect(_getLockCount()).toBe(2)
    expect(document.body.style.overflow).toBe('hidden')

    // First component unmounts - scroll should still be locked
    unmount1()

    expect(_getLockCount()).toBe(1)
    expect(document.body.style.overflow).toBe('hidden')

    // Second component unmounts - scroll should be restored
    unmount2()

    expect(_getLockCount()).toBe(0)
    expect(document.body.style.overflow).toBe('')
  })

  it('isLocked が true から false に変わった場合、lockCount をデクリメントする', () => {
    const { rerender } = renderHook(({ isLocked }) => useScrollLock(isLocked), {
      initialProps: { isLocked: true },
    })

    expect(_getLockCount()).toBe(1)
    expect(document.body.style.overflow).toBe('hidden')

    // Change to false
    rerender({ isLocked: false })

    expect(_getLockCount()).toBe(0)
    expect(document.body.style.overflow).toBe('')
  })

  it('isLocked が false から true に変わった場合、lockCount をインクリメントする', () => {
    const { rerender } = renderHook(({ isLocked }) => useScrollLock(isLocked), {
      initialProps: { isLocked: false },
    })

    expect(_getLockCount()).toBe(0)
    expect(document.body.style.overflow).toBe('')

    // Change to true
    rerender({ isLocked: true })

    expect(_getLockCount()).toBe(1)
    expect(document.body.style.overflow).toBe('hidden')
  })

  it('Modal と MobileMenu が同時に開いている場合のシナリオ', () => {
    // Simulate Modal opening
    const { unmount: unmountModal } = renderHook(() => useScrollLock(true))

    expect(_getLockCount()).toBe(1)
    expect(document.body.style.overflow).toBe('hidden')

    // Simulate MobileMenu opening
    const { unmount: unmountMenu } = renderHook(() => useScrollLock(true))

    expect(_getLockCount()).toBe(2)
    expect(document.body.style.overflow).toBe('hidden')

    // MobileMenu closes - Modal still needs scroll lock
    unmountMenu()

    expect(_getLockCount()).toBe(1)
    expect(document.body.style.overflow).toBe('hidden')

    // Modal closes - now scroll should be restored
    unmountModal()

    expect(_getLockCount()).toBe(0)
    expect(document.body.style.overflow).toBe('')
  })

  it('3つ以上のコンポーネントがロックしている場合も正しく動作する', () => {
    const { unmount: unmount1 } = renderHook(() => useScrollLock(true))
    const { unmount: unmount2 } = renderHook(() => useScrollLock(true))
    const { unmount: unmount3 } = renderHook(() => useScrollLock(true))

    expect(_getLockCount()).toBe(3)
    expect(document.body.style.overflow).toBe('hidden')

    unmount2()
    expect(_getLockCount()).toBe(2)
    expect(document.body.style.overflow).toBe('hidden')

    unmount1()
    expect(_getLockCount()).toBe(1)
    expect(document.body.style.overflow).toBe('hidden')

    unmount3()
    expect(_getLockCount()).toBe(0)
    expect(document.body.style.overflow).toBe('')
  })
})
