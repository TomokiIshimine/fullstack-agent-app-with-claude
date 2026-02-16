/**
 * Detect if the current platform is macOS.
 * Uses navigator.platform (with userAgent fallback).
 */
export function isMac(): boolean {
  if (typeof navigator === 'undefined') return false

  // navigator.platform is deprecated but widely supported
  if (navigator.platform) {
    return navigator.platform.toUpperCase().includes('MAC')
  }

  // Fallback to userAgent
  return /macintosh|mac os x/i.test(navigator.userAgent)
}

/**
 * Get the modifier key label for the current platform.
 * Returns "Cmd" on macOS, "Ctrl" on other platforms.
 */
export function getModifierKeyLabel(): string {
  return isMac() ? 'Cmd' : 'Ctrl'
}
