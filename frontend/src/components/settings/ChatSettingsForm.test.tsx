import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ChatSettingsForm } from './ChatSettingsForm'
import * as userSettingsApi from '@/lib/api/userSettings'

// Mock logger
vi.mock('@/lib/logger', () => ({
  logger: {
    debug: vi.fn(),
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
  },
}))

// Mock platform utils to return consistent values in tests
vi.mock('@/lib/utils/platform', () => ({
  isMac: () => false,
  getModifierKeyLabel: () => 'Ctrl',
}))

describe('ChatSettingsForm', () => {
  const mockOnSuccess = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    // Default: settings fetch returns 'enter'
    vi.spyOn(userSettingsApi, 'getUserSettings').mockResolvedValue({
      send_shortcut: 'enter',
    })
    vi.spyOn(userSettingsApi, 'updateUserSettings').mockResolvedValue({
      message: '設定を更新しました',
      send_shortcut: 'ctrl_enter',
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Rendering', () => {
    it('should render the chat settings heading', async () => {
      render(<ChatSettingsForm />)

      await waitFor(() => {
        expect(screen.getByText('チャット設定')).toBeInTheDocument()
      })
    })

    it('should render the send key legend', async () => {
      render(<ChatSettingsForm />)

      await waitFor(() => {
        expect(screen.getByText('メッセージ送信キー')).toBeInTheDocument()
      })
    })

    it('should render Enter and Ctrl+Enter radio options', async () => {
      render(<ChatSettingsForm />)

      await waitFor(() => {
        expect(screen.getByLabelText(/^Enter/)).toBeInTheDocument()
        expect(screen.getByLabelText(/^Ctrl\+Enter/)).toBeInTheDocument()
      })
    })

    it('should render option descriptions', async () => {
      render(<ChatSettingsForm />)

      await waitFor(() => {
        expect(screen.getByText('Enterで送信、Shift+Enterで改行')).toBeInTheDocument()
        expect(screen.getByText('Ctrl+Enterで送信、Enterで改行')).toBeInTheDocument()
      })
    })

    it('should have Enter selected by default', async () => {
      render(<ChatSettingsForm />)

      await waitFor(() => {
        const enterRadio = screen.getByRole('radio', { name: /^Enter/ })
        expect(enterRadio).toBeChecked()
      })
    })

    it('should show ctrl_enter selected when fetched from API', async () => {
      vi.spyOn(userSettingsApi, 'getUserSettings').mockResolvedValue({
        send_shortcut: 'ctrl_enter',
      })

      render(<ChatSettingsForm />)

      await waitFor(() => {
        const ctrlEnterRadio = screen.getByRole('radio', { name: /^Ctrl\+Enter/ })
        expect(ctrlEnterRadio).toBeChecked()
      })
    })
  })

  describe('Interaction', () => {
    it('should call updateUserSettings when selecting Ctrl+Enter', async () => {
      const user = userEvent.setup()
      render(<ChatSettingsForm onSuccess={mockOnSuccess} />)

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByRole('radio', { name: /^Enter/ })).toBeChecked()
      })

      // Click Ctrl+Enter option
      const ctrlEnterRadio = screen.getByRole('radio', { name: /^Ctrl\+Enter/ })
      await user.click(ctrlEnterRadio)

      await waitFor(() => {
        expect(userSettingsApi.updateUserSettings).toHaveBeenCalledWith({
          send_shortcut: 'ctrl_enter',
        })
      })
    })

    it('should not call updateUserSettings when clicking already selected option', async () => {
      const user = userEvent.setup()
      render(<ChatSettingsForm />)

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByRole('radio', { name: /^Enter/ })).toBeChecked()
      })

      // Click the already-selected Enter option
      const enterRadio = screen.getByRole('radio', { name: /^Enter/ })
      await user.click(enterRadio)

      expect(userSettingsApi.updateUserSettings).not.toHaveBeenCalled()
    })

    it('should notify parent on success via onSuccess callback', async () => {
      const user = userEvent.setup()
      render(<ChatSettingsForm onSuccess={mockOnSuccess} />)

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByRole('radio', { name: /^Enter/ })).toBeChecked()
      })

      // Click Ctrl+Enter option
      const ctrlEnterRadio = screen.getByRole('radio', { name: /^Ctrl\+Enter/ })
      await user.click(ctrlEnterRadio)

      await waitFor(() => {
        expect(mockOnSuccess).toHaveBeenCalledWith('チャット設定を更新しました')
      })
    })
  })

  describe('Error handling', () => {
    it('should show error alert on update failure', async () => {
      vi.spyOn(userSettingsApi, 'updateUserSettings').mockRejectedValue(new Error('Update failed'))
      const user = userEvent.setup()
      render(<ChatSettingsForm />)

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByRole('radio', { name: /^Enter/ })).toBeChecked()
      })

      // Click Ctrl+Enter option
      const ctrlEnterRadio = screen.getByRole('radio', { name: /^Ctrl\+Enter/ })
      await user.click(ctrlEnterRadio)

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('設定の更新に失敗しました')
      })
    })

    it('should rollback selection on update failure', async () => {
      vi.spyOn(userSettingsApi, 'updateUserSettings').mockRejectedValue(new Error('Update failed'))
      const user = userEvent.setup()
      render(<ChatSettingsForm />)

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByRole('radio', { name: /^Enter/ })).toBeChecked()
      })

      // Click Ctrl+Enter option
      const ctrlEnterRadio = screen.getByRole('radio', { name: /^Ctrl\+Enter/ })
      await user.click(ctrlEnterRadio)

      // Should rollback to Enter
      await waitFor(() => {
        const enterRadio = screen.getByRole('radio', { name: /^Enter/ })
        expect(enterRadio).toBeChecked()
      })
    })

    it('should dismiss error when clicking dismiss button', async () => {
      vi.spyOn(userSettingsApi, 'updateUserSettings').mockRejectedValue(new Error('Update failed'))
      const user = userEvent.setup()
      render(<ChatSettingsForm />)

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByRole('radio', { name: /^Enter/ })).toBeChecked()
      })

      // Trigger error
      const ctrlEnterRadio = screen.getByRole('radio', { name: /^Ctrl\+Enter/ })
      await user.click(ctrlEnterRadio)

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument()
      })

      // Dismiss the error - Alert has both text and icon dismiss buttons
      const dismissButtons = screen.getAllByRole('button', { name: /閉じる/ })
      await user.click(dismissButtons[0])

      await waitFor(() => {
        expect(screen.queryByRole('alert')).not.toBeInTheDocument()
      })
    })
  })

  describe('Accessibility', () => {
    it('should have a radiogroup with proper aria-label', async () => {
      render(<ChatSettingsForm />)

      await waitFor(() => {
        expect(screen.getByRole('radiogroup', { name: 'メッセージ送信キー' })).toBeInTheDocument()
      })
    })

    it('should have radio inputs with proper names', async () => {
      render(<ChatSettingsForm />)

      await waitFor(() => {
        const radios = screen.getAllByRole('radio')
        expect(radios).toHaveLength(2)
        radios.forEach(radio => {
          expect(radio).toHaveAttribute('name', 'sendShortcut')
        })
      })
    })
  })
})
