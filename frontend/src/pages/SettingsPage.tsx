import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { useConversations } from '@/hooks/useConversations'
import { ChatSettingsForm } from '@/components/settings/ChatSettingsForm'
import { PasswordChangeForm } from '@/components/settings/PasswordChangeForm'
import { ProfileUpdateForm } from '@/components/settings/ProfileUpdateForm'
import { ChatSidebar } from '@/components/chat/ChatSidebar'
import { Alert } from '@/components/ui'
import { logger } from '@/lib/logger'
import type { User } from '@/types/auth'

export function SettingsPage() {
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const { user, updateUser } = useAuth()
  const navigate = useNavigate()

  const isAdmin = user?.role === 'admin'

  // Only load conversations for non-admin users
  const { conversations, isLoading: isLoadingConversations } = useConversations({
    autoLoad: !isAdmin,
  })

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

  const handleNewChat = () => {
    navigate('/chat')
  }

  const handleSelectConversation = (uuid: string) => {
    navigate(`/chat/${uuid}`)
  }

  // Admin layout (no sidebar)
  if (isAdmin) {
    return (
      <div className="bg-slate-100">
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
            <ChatSettingsForm onSuccess={handleSuccess} />
            <PasswordChangeForm onSuccess={() => handleSuccess('パスワードを変更しました')} />
          </div>
        </div>
      </div>
    )
  }

  // User layout (with sidebar)
  return (
    <div className="settings-layout">
      <ChatSidebar
        conversations={conversations}
        isLoading={isLoadingConversations}
        onNewChat={handleNewChat}
        onSelectConversation={handleSelectConversation}
      />
      <div className="settings-content">
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
            <ChatSettingsForm onSuccess={handleSuccess} />
            <PasswordChangeForm onSuccess={() => handleSuccess('パスワードを変更しました')} />
          </div>
        </div>
      </div>
    </div>
  )
}
