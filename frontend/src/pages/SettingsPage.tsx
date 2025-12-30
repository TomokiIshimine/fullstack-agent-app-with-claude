import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { PasswordChangeForm } from '@/components/settings/PasswordChangeForm'
import { ProfileUpdateForm } from '@/components/settings/ProfileUpdateForm'
import { Alert } from '@/components/ui'
import { logger } from '@/lib/logger'
import type { User } from '@/types/auth'

export function SettingsPage() {
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const { user, updateUser } = useAuth()

  const handleSuccess = (message: string) => {
    setSuccessMessage(message)
    logger.info('Settings success message displayed', { message })
    setTimeout(() => {
      setSuccessMessage(null)
    }, 5000)
  }

  const handleProfileUpdate = (updatedUser: User) => {
    updateUser(updatedUser)
    handleSuccess('プロフィールを更新しました')
  }

  return (
    <div className="min-h-screen bg-slate-100">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-slate-800 mb-8">設定</h1>

        {successMessage && (
          <div className="mb-6">
            <Alert variant="success" autoCloseMs={5000} onDismiss={() => setSuccessMessage(null)}>
              {successMessage}
            </Alert>
          </div>
        )}

        <div className="space-y-6">
          <ProfileUpdateForm user={user} onSuccess={handleProfileUpdate} />
          <PasswordChangeForm onSuccess={() => handleSuccess('パスワードを変更しました')} />
        </div>
      </div>
    </div>
  )
}
