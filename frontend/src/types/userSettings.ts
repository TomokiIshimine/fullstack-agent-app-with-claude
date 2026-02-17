/**
 * Send shortcut key setting values
 */
export type SendShortcut = 'enter' | 'ctrl_enter'

/**
 * User settings response from API
 */
export interface UserSettingsResponse {
  send_shortcut: SendShortcut
}

/**
 * User settings update request payload
 */
export interface UserSettingsUpdateRequest {
  send_shortcut: SendShortcut
}

/**
 * User settings update response
 */
export interface UserSettingsUpdateResponse {
  message: string
  send_shortcut: SendShortcut
}
