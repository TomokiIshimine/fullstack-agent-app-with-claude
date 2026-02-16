import { describe, it, expect, afterEach } from 'vitest'
import { isMac, getModifierKeyLabel } from './platform'

describe('platform', () => {
  const originalNavigator = global.navigator

  afterEach(() => {
    // Restore original navigator
    Object.defineProperty(global, 'navigator', {
      value: originalNavigator,
      writable: true,
      configurable: true,
    })
  })

  describe('isMac', () => {
    it('returns true when navigator.platform contains "Mac"', () => {
      Object.defineProperty(global, 'navigator', {
        value: { platform: 'MacIntel', userAgent: '' },
        writable: true,
        configurable: true,
      })

      expect(isMac()).toBe(true)
    })

    it('returns true when navigator.platform is "MacPPC"', () => {
      Object.defineProperty(global, 'navigator', {
        value: { platform: 'MacPPC', userAgent: '' },
        writable: true,
        configurable: true,
      })

      expect(isMac()).toBe(true)
    })

    it('returns false when navigator.platform is "Win32"', () => {
      Object.defineProperty(global, 'navigator', {
        value: { platform: 'Win32', userAgent: '' },
        writable: true,
        configurable: true,
      })

      expect(isMac()).toBe(false)
    })

    it('returns false when navigator.platform is "Linux x86_64"', () => {
      Object.defineProperty(global, 'navigator', {
        value: { platform: 'Linux x86_64', userAgent: '' },
        writable: true,
        configurable: true,
      })

      expect(isMac()).toBe(false)
    })

    it('falls back to userAgent when platform is empty', () => {
      Object.defineProperty(global, 'navigator', {
        value: {
          platform: '',
          userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        },
        writable: true,
        configurable: true,
      })

      expect(isMac()).toBe(true)
    })

    it('returns false when userAgent is Windows and platform is empty', () => {
      Object.defineProperty(global, 'navigator', {
        value: {
          platform: '',
          userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        },
        writable: true,
        configurable: true,
      })

      expect(isMac()).toBe(false)
    })

    it('returns false when navigator is undefined', () => {
      Object.defineProperty(global, 'navigator', {
        value: undefined,
        writable: true,
        configurable: true,
      })

      expect(isMac()).toBe(false)
    })
  })

  describe('getModifierKeyLabel', () => {
    it('returns "Cmd" on macOS', () => {
      Object.defineProperty(global, 'navigator', {
        value: { platform: 'MacIntel', userAgent: '' },
        writable: true,
        configurable: true,
      })

      expect(getModifierKeyLabel()).toBe('Cmd')
    })

    it('returns "Ctrl" on Windows', () => {
      Object.defineProperty(global, 'navigator', {
        value: { platform: 'Win32', userAgent: '' },
        writable: true,
        configurable: true,
      })

      expect(getModifierKeyLabel()).toBe('Ctrl')
    })

    it('returns "Ctrl" on Linux', () => {
      Object.defineProperty(global, 'navigator', {
        value: { platform: 'Linux x86_64', userAgent: '' },
        writable: true,
        configurable: true,
      })

      expect(getModifierKeyLabel()).toBe('Ctrl')
    })
  })
})
