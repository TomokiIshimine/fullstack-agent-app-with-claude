import { useEffect } from 'react'
import { Card, Alert } from '@/components/ui'
import { useUserSettings } from '@/hooks/useUserSettings'
import { getModifierKeyLabel } from '@/lib/utils/platform'
import type { SendShortcut } from '@/types/userSettings'

interface ChatSettingsFormProps {
  onSuccess?: (message: string) => void
}

const modifierKey = getModifierKeyLabel()

const options: { value: SendShortcut; label: string; description: string }[] = [
  {
    value: 'enter',
    label: 'Enter',
    description: 'Enterで送信、Shift+Enterで改行',
  },
  {
    value: 'ctrl_enter',
    label: `${modifierKey}+Enter`,
    description: `${modifierKey}+Enterで送信、Enterで改行`,
  },
]

export function ChatSettingsForm({ onSuccess }: ChatSettingsFormProps) {
  const {
    sendShortcut,
    isLoading,
    updateSendShortcut,
    error,
    successMessage,
    clearError,
    clearSuccessMessage,
  } = useUserSettings()

  // Notify parent of success
  useEffect(() => {
    if (successMessage && onSuccess) {
      onSuccess(successMessage)
      clearSuccessMessage()
    }
  }, [successMessage, onSuccess, clearSuccessMessage])

  const handleChange = (value: SendShortcut) => {
    if (value !== sendShortcut) {
      void updateSendShortcut(value)
    }
  }

  return (
    <Card>
      <h2 className="text-2xl font-semibold text-slate-900 mb-6">チャット設定</h2>

      {error && (
        <div className="mb-4">
          <Alert variant="error" onDismiss={clearError}>
            {error}
          </Alert>
        </div>
      )}

      <fieldset disabled={isLoading}>
        <legend className="text-sm font-medium text-slate-700 mb-3">メッセージ送信キー</legend>
        <div className="space-y-3" role="radiogroup" aria-label="メッセージ送信キー">
          {options.map(option => (
            <label
              key={option.value}
              className="flex items-start gap-3 cursor-pointer p-3 rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors has-[:checked]:border-primary-500 has-[:checked]:bg-primary-50"
            >
              <input
                type="radio"
                name="sendShortcut"
                value={option.value}
                checked={sendShortcut === option.value}
                onChange={() => handleChange(option.value)}
                className="mt-0.5 h-4 w-4 text-primary-600 focus:ring-primary-500 border-slate-300"
              />
              <div>
                <span className="text-sm font-medium text-slate-900">{option.label}</span>
                <p className="text-xs text-slate-500 mt-0.5">{option.description}</p>
              </div>
            </label>
          ))}
        </div>
      </fieldset>
    </Card>
  )
}
