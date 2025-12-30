import { describe, it, expect, vi, afterEach } from 'vitest'
import { AUTH_EVENTS, emitSessionExpired, onSessionExpired } from './authEvents'

describe('authEvents', () => {
  describe('AUTH_EVENTS', () => {
    it('should have SESSION_EXPIRED event type', () => {
      expect(AUTH_EVENTS.SESSION_EXPIRED).toBe('auth:session-expired')
    })
  })

  describe('emitSessionExpired', () => {
    it('should dispatch a CustomEvent on window', () => {
      const dispatchSpy = vi.spyOn(window, 'dispatchEvent')

      emitSessionExpired()

      expect(dispatchSpy).toHaveBeenCalledTimes(1)
      expect(dispatchSpy).toHaveBeenCalledWith(expect.any(CustomEvent))

      const event = dispatchSpy.mock.calls[0][0] as CustomEvent
      expect(event.type).toBe(AUTH_EVENTS.SESSION_EXPIRED)

      dispatchSpy.mockRestore()
    })
  })

  describe('onSessionExpired', () => {
    let cleanup: (() => void) | null = null

    afterEach(() => {
      if (cleanup) {
        cleanup()
        cleanup = null
      }
    })

    it('should call callback when session expired event is emitted', () => {
      const callback = vi.fn()

      cleanup = onSessionExpired(callback)
      emitSessionExpired()

      expect(callback).toHaveBeenCalledTimes(1)
    })

    it('should call callback multiple times for multiple events', () => {
      const callback = vi.fn()

      cleanup = onSessionExpired(callback)
      emitSessionExpired()
      emitSessionExpired()
      emitSessionExpired()

      expect(callback).toHaveBeenCalledTimes(3)
    })

    it('should return a cleanup function that removes the listener', () => {
      const callback = vi.fn()

      cleanup = onSessionExpired(callback)
      emitSessionExpired()
      expect(callback).toHaveBeenCalledTimes(1)

      // Call cleanup to remove listener
      cleanup()
      cleanup = null

      // This event should not trigger the callback
      emitSessionExpired()
      expect(callback).toHaveBeenCalledTimes(1)
    })

    it('should support multiple independent subscribers', () => {
      const callback1 = vi.fn()
      const callback2 = vi.fn()

      const cleanup1 = onSessionExpired(callback1)
      const cleanup2 = onSessionExpired(callback2)

      emitSessionExpired()

      expect(callback1).toHaveBeenCalledTimes(1)
      expect(callback2).toHaveBeenCalledTimes(1)

      // Remove first subscriber
      cleanup1()

      emitSessionExpired()

      expect(callback1).toHaveBeenCalledTimes(1) // Not called again
      expect(callback2).toHaveBeenCalledTimes(2) // Called again

      cleanup2()
    })

    it('should not call callback for other events', () => {
      const callback = vi.fn()

      cleanup = onSessionExpired(callback)

      // Dispatch a different event
      window.dispatchEvent(new CustomEvent('other-event'))

      expect(callback).not.toHaveBeenCalled()
    })
  })
})
