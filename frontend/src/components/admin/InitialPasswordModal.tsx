import { useState } from 'react'
import { logger } from '@/lib/logger'
import { Modal, Button } from '@/components/ui'

interface InitialPasswordModalProps {
  email: string
  password: string
  onClose: () => void
}

export function InitialPasswordModal({ email, password, onClose }: InitialPasswordModalProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(password)
      setCopied(true)
      logger.info('Initial password copied to clipboard')
      // Reset copied state after 2 seconds
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      logger.error('Failed to copy password', err as Error)
    }
  }

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title="ユーザーを作成しました"
      size="sm"
      showCloseButton={false}
    >
      <div className="space-y-4">
        <p className="text-sm text-slate-600">
          <span className="font-semibold">メールアドレス:</span> {email}
        </p>

        <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg">
          <label className="block text-sm font-medium text-slate-600 mb-2">初期パスワード:</label>
          <div className="font-mono text-xl font-semibold text-slate-900 p-3 bg-white border-2 border-primary-500 rounded-md text-center tracking-wider mb-3">
            {password}
          </div>
          <Button onClick={handleCopy} disabled={copied} variant="success" fullWidth>
            {copied ? 'コピーしました' : 'コピー'}
          </Button>
        </div>

        <div className="p-4 bg-warning-50 border border-warning-100 rounded-lg text-warning-600 text-sm">
          <p className="mb-2">
            <span className="font-semibold">重要:</span> このパスワードをユーザーに伝えてください。
          </p>
          <p className="m-0">この画面を閉じると再表示できません。</p>
        </div>

        <Button onClick={onClose} fullWidth>
          閉じる
        </Button>
      </div>
    </Modal>
  )
}
