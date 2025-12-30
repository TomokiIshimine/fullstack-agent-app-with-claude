import { useEffect } from 'react'

// Reference counter to track how many components want scroll locked
let lockCount = 0

/**
 * Hook to lock body scroll when a component is open (e.g., modal, mobile menu).
 * Uses reference counting to handle multiple overlays - scroll is only restored
 * when all overlays are closed.
 *
 * @param isLocked - Whether this component wants scroll locked
 */
export function useScrollLock(isLocked: boolean): void {
  useEffect(() => {
    if (isLocked) {
      lockCount++
      document.body.style.overflow = 'hidden'
    }

    return () => {
      if (isLocked) {
        lockCount--
        if (lockCount === 0) {
          document.body.style.overflow = ''
        }
      }
    }
  }, [isLocked])
}

// Export for testing purposes
export function _resetLockCount(): void {
  lockCount = 0
  document.body.style.overflow = ''
}

export function _getLockCount(): number {
  return lockCount
}
